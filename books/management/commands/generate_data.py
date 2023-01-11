import logging
from typing import cast

from django.core.management.base import BaseCommand

from books.models import Person

from .generate_data_scripts import generate_books, generate_persons


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generates fake data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--persons",
            type=int,
            help="Count for persons to create",
            default=1_000_000,
        )
        parser.add_argument(
            "--books",
            type=int,
            help="Count of books to create",
            default=2_000,
        )
        parser.add_argument(
            "--readers",
            type=int,
            help="average count of readers",
            default=10_000,
        )

    def handle(self, *args, **options):

        logger.info("starting data generation...")

        logger.info(f"adding {options['persons']} persons...")
        persons = cast(
            list[Person], generate_persons(options["persons"], keep_results=True)
        )

        tolstoy = Person.objects.first()
        assert tolstoy is not None, "Person's table should not be empty"

        tolstoy.name = "tolstoy"
        tolstoy.save()

        logger.info(f"adding {options['books']} books...")

        generate_books(options["books"], options["readers"], persons)
