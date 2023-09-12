import statistics
import timeit
from datetime import date

from django.urls import reverse
from rest_framework.test import APIClient
from rich.console import Console
from rich.table import Table

from books.models import Library


client = APIClient()


filters = [
    {},
    {"written_at__gte": date(2022, 1, 1)},
    {"rating__gte": 6},
    {"written_at__gte": date(2022, 1, 1), "rating__gte": 6},
]

orderings = [
    "id",
    "written_at",
    "rating",
    "-id",
    "-written_at",
    "-rating",
    "-written_at,rating",
]


data_by_url = {
    "simple-list-reviews": [{}],
    "filtered-list-reviews": filters,
    "ordered-list-reviews": [{"ordering": ordering} for ordering in orderings],
    "complete-list-reviews": [
        {**filter_, "ordering": ordering}
        for filter_ in filters
        for ordering in orderings
    ],
}


def setup_table(has_multiple_runs):
    table = Table(show_lines=True)
    table.add_column("Query params")
    table.add_column("Library")
    if has_multiple_runs:
        table.add_column("Mean duration")
        table.add_column("Max duration")
        table.add_column("Runs")
    else:
        table.add_column("duration")
    return table


def format_query_params(data):
    return "\n".join(map(lambda item: f"{item[0]}={item[1]}", data.items()))


def get_color(value: float) -> str:
    if value < 1:
        color = "green"
    elif value < 3:
        color = "yellow"
    elif value < 7:
        color = "orange_red1"
    else:
        color = "bright_red"

    return f"[bold {color}] {value:.3f}"


def add_row(table, url, data, library, results, repeat):
    mean = get_color(statistics.mean(results))

    if repeat > 1:
        table.add_row(
            format_query_params(data),
            str(library),
            f"{mean} s",
            f"{get_color(max(results))} s",
            str(repeat),
        )
    else:
        table.add_row(format_query_params(data), str(library), f"{mean} s")


def benchmark_list_reviews(url_names, library_ids, repeat=1):
    table = setup_table(has_multiple_runs=repeat > 1)

    libraries = dict(
        Library.objects.filter(id__in=library_ids).values_list("id", "name")
    )
    for url_name in url_names:
        for data in data_by_url[url_name]:
            for library_id in library_ids:
                url = reverse(url_name, args=[library_id])

                results = timeit.repeat(
                    lambda: client.get(url, data or {}), number=1, repeat=repeat
                )
                add_row(table, url, data, libraries.get(library_id), results, repeat)

    console = Console()
    console.print(table)
