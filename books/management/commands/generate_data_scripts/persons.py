import logging
import random

from faker import Faker

from books.models import Person

from .bulk_creator import BulkCreator


fake: Faker = Faker()

logger = logging.getLogger(__name__)


def person_gen() -> Person:
    return Person(
        email=f"{random.randint(1,1_000_000)}_{fake.company_email()}",
        name=f"{fake.first_name()} {fake.last_name()}",
        bio=fake.paragraph(nb_sentences=20),
    )


def generate_persons(count: int, keep_results: bool = False) -> None | list[Person]:
    with BulkCreator(
        Person, total=count, keep_results=keep_results, ignore_conflicts=True
    ) as bulk_creator:
        bulk_creator.add_many(person_gen() for _ in range(count))

    if keep_results:
        return bulk_creator.results
