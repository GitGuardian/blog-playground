from contextlib import contextmanager

from django.conf import settings
from django.db import connection


def toggle_index(index_name: str, active: bool):
    sql_file = settings.BASE_DIR / "sql_utils" / "toggle_index.sql"
    sql_query = sql_file.read_text()
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [active, index_name])


def indexes_size(valid_only=True):
    filename = "valid_indexes_size.sql" if valid_only else "all_indexes_size.sql"
    sql_file = settings.BASE_DIR / "sql_utils" / filename
    sql_query = sql_file.read_text()
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        col_names = [desc[0] for desc in cursor.description]
        return (col_names, cursor.fetchall())


@contextmanager
def use_indexes(*index_names):
    for index_name in index_names:
        toggle_index(index_name, True)
    yield

    for index_name in index_names:
        toggle_index(index_name, False)


@contextmanager
def disable_indexes(*index_names):
    for index_name in index_names:
        toggle_index(index_name, False)
    yield

    for index_name in index_names:
        toggle_index(index_name, True)


def toggle_all_custom_indexes(active):
    sql_file = settings.BASE_DIR / "sql_utils" / "toggle_custom_indexes.sql"
    sql_query = sql_file.read_text()
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [active])
