import time
from contextlib import contextmanager

from django.db import connection, reset_queries
from rich import print


def format_duration(duration):
    return f"[cyan]{duration:.2f}[/cyan]"


@contextmanager
def perf_counter(message="Duration", time_sql=False, print_sql=False):
    if time_sql:
        reset_queries()

    start_time = time.perf_counter()
    yield
    msg = message
    msg += f"\n  Total: {format_duration(time.perf_counter() - start_time)}"
    if time_sql:
        msg += f"\n  SQL: {total_sql_duration(connection.queries)}"
        if print_sql:
            for query in connection.queries:
                msg += (
                    f" \n\n{' '*6}(duration: {query['time']})   {query['sql'][:1000]}"
                )
    print(msg)


def total_sql_duration(queries):
    return format_duration(sum(float(query["time"]) for query in queries))
