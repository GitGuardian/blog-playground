from datetime import timedelta

import pytest
from django.db import transaction
from rest_framework.test import APIClient

from books.models import Book, BookTag, Library


pytestmark = pytest.mark.django_db


def test_lib_count():
    assert Library.objects.count() == 3


def test_book_per_reader(django_assert_num_queries):
    client = APIClient()
    library = Library.objects.first()
    with django_assert_num_queries(2):
        result = client.get(f"/books/{library.id}/readers-per-book")
    data = result.json()
    assert len(data) > 10


def test_queries(assert_django_queries):
    with assert_django_queries(["books.Library:SELECT"]):
        book = Book.objects.first()


def test_queries_2(assert_django_queries):
    with assert_django_queries(
        [
            "books.Library:SELECT",
            ":SAVEPOINT:1",
            "books.Book:SELECT:1",
            "books.Book:UPDATE:1",
            ":RELEASE SAVEPOINT:1",
            "books.BookTag:DELETE:1",
            "books.BookTag:INSERT:1",
        ]
    ):
        library = Library.objects.first()
        with transaction.atomic():
            book = Book.objects.filter(library=library).first()
            book.release_date = book.release_date + timedelta(days=1)
            book.save()

        BookTag.objects.filter(book=book).delete()
        BookTag.objects.create(name="braille", book=book, library=library)
