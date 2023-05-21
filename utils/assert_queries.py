import difflib
import re
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Type, Union

from django.apps import apps
from django.db import connection as conn
from django.db.models import Model
from django.test.utils import CaptureQueriesContext


REGEX_INSERT = re.compile(r"INSERT\s+INTO\s+(?P<table_name>.+?)(\s|$)", re.IGNORECASE)
REGEX_FROM = re.compile(r"FROM\s+(?P<table_name>.+?)(\s|$)", re.IGNORECASE)
REGEX_UPDATE = re.compile(r"UPDATE\s+(?P<table_name>.+?)(\s|$)", re.IGNORECASE)


class SQLOperationTypes(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SELECT = "SELECT"
    SAVEPOINT = "SAVEPOINT"
    RELEASE_SAVEPOINT = "RELEASE SAVEPOINT"
    ROLLBACK_TO_SAVEPOINT = "ROLLBACK TO SAVEPOINT"
    MISSING = ""


savepoint_operations = {
    SQLOperationTypes.SAVEPOINT,
    SQLOperationTypes.RELEASE_SAVEPOINT,
    SQLOperationTypes.ROLLBACK_TO_SAVEPOINT,
}


@dataclass(slots=True, frozen=True)
class SQLQuery:
    model_name: str  # or savepoint name
    operation: SQLOperationTypes = SQLOperationTypes.MISSING
    n: int = 1

    @classmethod
    def from_str(cls, value):
        model_name, operation, n = (value + "::").split(":")[:3]
        n = int(n) if n else 1
        assert n > 0
        return cls(model_name=model_name, operation=SQLOperationTypes(operation), n=n)

    def __str__(self):
        # as the savepoint name is random, and change on each execution,
        # it should not appear in the str representation
        model_name = "" if self.operation in savepoint_operations else self.model_name
        return f"{model_name}:{self.operation}:{self.n}"

    @property
    def is_precise(self):
        return (
            bool(self.model_name) and bool(self.operation)
        ) or self.operation in savepoint_operations


class AssertDjangoQueriesException(Exception):
    def __init__(
        self,
        message: str,
        captured_queries: Sequence[Dict[str, str]],
        expected_queries: Optional[List] = None,
    ):
        """
        Exception raised when the SQL queries doesn't match the expected django queries.

        If provided `queries_extra` must be a list of the sme size as captured_queries, containing strings that will be
        displayed for each SQL queries in the error message.
        """
        super().__init__(message)
        self.error_message = message
        self.captured_queries = captured_queries
        self.expected_queries = expected_queries

    def __str__(self):
        if not self.expected_queries or not all(
            SQLQuery.from_str(expected_query).is_precise
            for expected_query in self.expected_queries
        ):
            error_message = f"{self.error_message}\n\nActual queries:\n"
            for ind, query in enumerate(self.captured_queries):
                error_message += f"\t{query['sql']}\n"
        else:
            # Display a more explicit error
            error_message = self.error_message
            standardized_expected_queries = [
                str(SQLQuery.from_str(expected_query))
                for expected_query in self.expected_queries
            ]

            standardized_captured_queries = [
                str(SQLQuery(model_name, operation=SQLOperationTypes(operation), n=1))
                for model_name, operation in (
                    parse_query(query["sql"]) for query in self.captured_queries
                )
            ]
            error_message += "\n" + "\n".join(
                map(
                    str,
                    difflib.ndiff(
                        standardized_expected_queries,
                        standardized_captured_queries,
                    ),
                )
            )
        return error_message


@lru_cache(maxsize=1)
def get_table_name_to_model() -> Dict[str, Type["Model"]]:
    """
    Map table names to django models.
    """
    return {
        model._meta.db_table: model
        for app_name in apps.all_models
        for model in apps.all_models[app_name].values()
        if not model._meta.proxy
        # proxy don't have a table name and could override their base model
    }


def get_model_name_from_table_name(table_name: str) -> str:
    """
    Return the name of the django model under the form "app_name.model_name"
    associated with the given table name.
    """
    try:
        model = get_table_name_to_model()[table_name]
    except KeyError:
        return ""
    return f"{model._meta.app_label}.{model.__name__}"


def _remove_parenthesis_blocks(query: str) -> str:
    """
    Search for every block of parenthesis in the string and remove them. This is used
    to remove sub-queries and then figure out which table the main query is referring to.
    """
    parenthesis_regex = re.compile(r"\([^(]*?\)")
    while True:
        updated_query = parenthesis_regex.sub("", query)
        if updated_query == query:
            break
        query = updated_query
    return query


def _get_model_name_for_query_with_from_clause(query: str) -> str:
    """
    Return the model name associated with the table of a SELECT or DELETE query.
    """
    query = _remove_parenthesis_blocks(query)
    match = REGEX_FROM.search(query)
    if not match:
        return ""
    return get_model_name_from_table_name(match.group("table_name").replace('"', ""))


def _get_model_name_for_insert_query(query: str) -> str:
    """
    Return the model name associated with the table of an INSERT query.
    """
    match = re.match(REGEX_INSERT, query)
    if not match:
        return ""
    return get_model_name_from_table_name(match.group("table_name").replace('"', ""))


def _get_model_name_for_update_query(query: str) -> str:
    """
    Return the model name associated with the table of an UPDATE query.
    """
    match = REGEX_UPDATE.match(query)
    if not match:
        return ""
    return get_model_name_from_table_name(match.group("table_name").replace('"', ""))


def _get_savepoint_identifier(query: str) -> str:
    """
    Return the identifier a any SAVEPOINT statement.
    """
    return query[query.index('"') + 1 : -1]


SQL_OPERATIONS = {
    SQLOperationTypes.INSERT: _get_model_name_for_insert_query,
    SQLOperationTypes.UPDATE: _get_model_name_for_update_query,
    SQLOperationTypes.DELETE: _get_model_name_for_query_with_from_clause,
    SQLOperationTypes.SELECT: _get_model_name_for_query_with_from_clause,
    SQLOperationTypes.SAVEPOINT: _get_savepoint_identifier,
    SQLOperationTypes.RELEASE_SAVEPOINT: _get_savepoint_identifier,
    SQLOperationTypes.ROLLBACK_TO_SAVEPOINT: _get_savepoint_identifier,
}


def parse_query(query: str) -> Tuple[str, str]:
    """
    Parse a SQL query and return its target (model name or savepoint identifier)
    and operation (INSERT, UPDATE, RELEASE SAVEPOINT, ...).
    """
    for operation in SQL_OPERATIONS:
        if not query.startswith(operation):
            continue
        return SQL_OPERATIONS[operation](query), operation
    raise NotImplementedError(f"Unsupported SQL operation: {query}")


def check_unordered_queries(
    expected_queries: Dict[str, int], captured_queries: Sequence, extra: bool = False
) -> None:
    """
    Compare the expected queries with the captured queries, without taking
    order into account.

    Set extra to True if you want to allow some extra queries
    """
    parsed_queries = [parse_query(query["sql"]) for query in captured_queries]

    for query_identifier, nb_expected in expected_queries.items():
        count = 0
        expected_target, _, expected_sql_operator = query_identifier.partition(":")

        query_index = 0
        while query_index < len(parsed_queries):
            query_target, query_operator = parsed_queries[query_index]

            if (not expected_target or expected_target == query_target) and (
                not expected_sql_operator or expected_sql_operator == query_operator
            ):
                count += 1
                parsed_queries.pop(query_index)
            else:
                query_index += 1

        if count != nb_expected:
            raise AssertDjangoQueriesException(
                f"Expected {nb_expected} quer{'y' if nb_expected == 1 else 'ies'} "
                f"{query_identifier} but found {count}.",
                captured_queries,
            )

    if parsed_queries and not extra:
        nb_unexpected = len(parsed_queries)
        raise AssertDjangoQueriesException(
            f"Found {nb_unexpected} unexpected quer{'y' if nb_unexpected == 1 else 'ies'}: {parsed_queries}",
            captured_queries,
        )


def flatten_expected_queries(expected_queries: Sequence[str]) -> List[str]:
    """
    Computes the full list of expected queries.
    Ex:
    flatten_expected_queries([
                "ggdjango_tests.A:INSERT:2",
                "ggdjango_tests.A:SELECT",
            ])
        returns: [
                "ggdjango_tests.A:INSERT",
                "ggdjango_tests.A:INSERT",
                "ggdjango_tests.A:SELECT",
            ]
    """
    results = []
    for query in expected_queries:
        expected_target, _, expected_sql_operator = query.partition(":")
        (
            partitioned_expected_sql_operator,
            _,
            nb_of_duplicate,
        ) = expected_sql_operator.partition(":")
        try:
            results.extend(
                [":".join([expected_target, partitioned_expected_sql_operator])]
                * int(nb_of_duplicate)
            )
        except (ValueError, TypeError):
            results.append(query)
    return results


def expected_queries_to_regex(expected_queries: Sequence[str]) -> str:
    """
    Computes the regex to match captured queries.

    Ex:
    expected_queries_to_regex([
                "ggdjango_tests.A:INSERT",
                "ggdjango_tests.A:INSERT",
                ASSERT_DJANGO_QUERIES_ANY,
                "ggdjango_tests.A:UPDATE",
                "ggdjango_tests.A:SELECT",
                ASSERT_DJANGO_QUERIES_MULTIPLE_ANY
                "ggdjango_tests.A:DELETE",
            ])
        returns: "^ggdjango_tests\\.A:INSERT&
                   ggdjango_tests\\.A:INSERT&
                   [^&]*&
                   ggdjango_tests\\.A:UPDATE&
                   ggdjango_tests\\.A:SELECT&
                   .*
                   &ggdjango_tests\\.A:DELETE$"
    """
    results = []
    index = 0
    for query in expected_queries:
        expected_target, _, expected_sql_operator = query.partition(":")

        expected_target = re.escape(expected_target)
        if "SAVEPOINT" in expected_sql_operator and expected_target:
            # Each expected target is matched as group for savepoints in order to verify that targets match.
            # Since named groups can not have the same name, index is used to distinguish them.
            expected_target = f"(?P<savepoint_{expected_target}_{index}>.*)"
            index += 1

        if not expected_target:
            expected_line = f"[^&]*:{expected_sql_operator}"
        elif not expected_sql_operator:
            expected_line = f"{expected_target}:?[^&]*"
        else:
            expected_line = f"{expected_target}:{expected_sql_operator}"

        results.append(expected_line)

    expected_regex = f'^{"&".join(results)}$'
    return expected_regex


def format_order_queries_extra(parsed_queries: Sequence) -> List[str]:
    return [
        f"parsed: {parsed_query[0]}:{parsed_query[1]}\t"
        for parsed_query in parsed_queries
    ]


def _check_queries_syntax(expected_queries: Sequence[str]):
    # assert that all expected queries have correct format
    query_regex = re.compile(rf"^[^:]*(:({'|'.join(SQL_OPERATIONS)})(:\d+)?)?$")
    for query in expected_queries:
        if not query_regex.match(query):
            raise ValueError(f"Expected query {query} does not have a correct format.")


def check_ordered_queries(
    expected_queries: Sequence[str], captured_queries: Sequence[Dict[str, str]]
) -> None:
    """
    Compare the expected queries with the captured queries and assert the order
    of execution.
    """

    _check_queries_syntax(expected_queries)

    # Serialize captured queries to string separated by &: e.g. table_1:SELECT&table_2:INSERT
    parsed_queries = (":".join(parse_query(query["sql"])) for query in captured_queries)
    captured_queries_string = "&".join(parsed_queries)

    # handle query duplicate number
    expected_queries = flatten_expected_queries(expected_queries)

    # verify that number of queries is the same, if there are no special queries
    if len(expected_queries) != len(captured_queries):
        raise AssertDjangoQueriesException(
            f"Expected {len(expected_queries)} queries but got {len(captured_queries)}.",
            captured_queries=captured_queries,
            expected_queries=expected_queries,
        )

    # We are going to compare expected and actual queries with regex
    expected_queries_regex = expected_queries_to_regex(expected_queries)
    result = re.match(expected_queries_regex, captured_queries_string)

    if not result:
        raise AssertDjangoQueriesException(
            "Expected queries and captured queries do not match.",
            captured_queries=captured_queries,
            expected_queries=expected_queries,
        )

    # Verify that targets of expected savepoints correspond to the targets of captured savepoints.
    # The targets of the regex groups of the same prefix must be same. E.g. groups with names savepoint_1_1,
    # savepoint_1_2, savepoint_1_3 (with the common prefix savepoint_1) should match to the same savepoint targets
    # in the captured query.
    savepoint_prefix_dict = {}
    for savepoint_group_name, savepoint_target in result.groupdict().items():
        savepoint_prefix = savepoint_group_name.rsplit("_", 1)[0]
        if (
            savepoint_prefix in savepoint_prefix_dict
            and savepoint_prefix_dict[savepoint_prefix] != savepoint_target
        ):
            raise AssertDjangoQueriesException(
                "Savepoints targets do not match.",
                captured_queries=captured_queries,
                expected_queries=expected_queries,
            )
        else:
            savepoint_prefix_dict[savepoint_prefix] = savepoint_target


@contextmanager
def assert_django_queries_manager(
    expected: Union[Sequence[str], Dict[str, int]], extra: bool = False
) -> Iterator[CaptureQueriesContext]:
    """
    Context manager to assert specifically the db queries.
    """

    with CaptureQueriesContext(conn) as context:
        yield context

        if isinstance(expected, dict):
            check_unordered_queries(expected, context.captured_queries, extra=extra)

        elif isinstance(expected, Sequence):
            check_ordered_queries(expected, context.captured_queries)

        else:
            raise TypeError("Unsupported type for expected queries.")

    return None
