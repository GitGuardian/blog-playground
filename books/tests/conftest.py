import pytest
from django.core.management import call_command

from books.models.library import Library
from utils.assert_queries import assert_django_queries_manager


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_createdb, django_db_blocker):
    with django_db_blocker.unblock():
        if not Library.objects.count():
            call_command(
                "generate_data",
                libraries=3,
                books=100,
                avg_readers=3,
                max_readers=10,
                persons=20,
            )


@pytest.fixture
def assert_django_queries():
    """
    A fixture to check for actual database queries being run.


    To specify the query you can should use this format: {model_path}:{operation}
        model_path or operation could be omitted.
        operation is one of the following: INSERT, UPDATE, DELETE, SELECT,
                                       SAVEPOINT, RELEASE SAVEPOINT, ROLLBACK TO SAVEPOINT

    Usage:

        # unordered
        ```
        with assert_django_queries({
            "api.Account": 2,  # 2 queries on this model, any type
            "data.Occurrence:DELETE": 1,  # 1 DELETE query on this model
        }):
            # do stuff
        ```
        - In this mode you can use ASSERT_DJANGO_QUERIES_ANY or ASSERT_DJANGO_QUERIES_MULTIPLE_ANY
        - In this mode you can deduplicate same query by specifing the number of repetition.
                ex: [
                    "ggdjango_tests.A:INSERT",
                    "ggdjango_tests.A:INSERT",
                    "ggdjango_tests.A:INSERT",
                ] => ["ggdjango_tests.A:INSERT:3",]
        - In this mode you can specify an id to `savepoint` operations to precise the order.
                ex: [
                    "1:SAVEPOINT", # creation of a first savepoint
                    "ggdjango_tests.A:SELECT",
                    "2:SAVEPOINT", # creation of a second savepoint
                    "ggdjango_tests.A:INSERT",
                    "1:RELEASE SAVEPOINT", # first we close the first savepoint
                    "2:RELEASE SAVEPOINT", # then the second
                ]

        # ordered
        ```
        with assert_django_queries([
            "api.Account:SELECT",
            "api.Account:INSERT",
            ":SAVEPOINT",
            "data.Occurrence:DELETE",
            ":RELEASE SAVEPOINT"
        ]):
            # do more stuff
        ```
        - In this mode you can set the kwargs `extra` if you want to allow extra queries.

    Edge cases not handled:
    - union queries
    - queries that use a subquery in their FROM clause
    """
    return assert_django_queries_manager
