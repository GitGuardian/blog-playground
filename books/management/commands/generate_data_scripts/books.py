import random

from faker import Faker
from tqdm import tqdm

from books.models import Book, Person

from .bulk_creator import BulkCreator


fake = Faker()


def book_gen(persons: list[Person]) -> Book:
    return Book(
        title=fake.sentence(nb_words=10, variable_nb_words=True),
        author=random.choice(persons),
    )


def generate_books(
    total_books: int,
    avg_readers: int,
    persons: list[Person],
) -> None:

    with BulkCreator(Book, total=total_books, keep_results=True) as bulk_creator:
        bulk_creator.add_many(book_gen(persons) for _ in range(total_books))
    generate_readings(avg_readers, bulk_creator.results, persons)


def generate_readings(avg_readers: int, books: list[Book], persons: list[Person]):
    min_readers = int(avg_readers - avg_readers / 1.1)
    max_readers = int(avg_readers + avg_readers / 1.1)
    with tqdm(
        total=len(books),
        unit="books",
    ) as progress_bar:
        for book in books:
            book.readers.set(
                random.sample(persons, random.randint(min_readers, max_readers))
            )
            progress_bar.update(1)
