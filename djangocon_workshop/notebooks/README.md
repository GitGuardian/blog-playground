## Goals and non-goals

This workshop aims at explainging a few methods to:

- Resolve SQL-related performance issues
- Detect them early

We won't discuss other performance problems, such as HTTP requests, nor question whether our models and URL endpoints make sense, from a business point of view (even though we tried to use relevant examples)

# What does this repo contain

This repo is a working demo django app, called `books`, along with multiple jupyter notebooks demonstrating multiple SQL-related perfomances issues

## The books Django app

### Models

`books` contains the following models:

- `Library`, either public or private, depending on the number of books it contains.
- `Book`
- `BookTag` for books also available on a specific media, or specific language, in a given library
- `Person`
- `Review`, written by a `Person` on a `Book` from a given `Library`

![Alt text](../../model_graph.png)

It also defines some views, most of them being rather slow, or even completely broken.
Each notebook will focus on a specific endpoint, and how to improve it.

### App structure

In addition to models, the app also defines some views, most of them being rather slow, or even completely broken.
Each notebook will focus on a specific endpoint, and how to improve it.

We'll also use a middle layer between views and models, called `selectors`, to write non-trivial queries.

### The data generation command

[This django command](../../books/management/commands/generate_data.py) helps to generate a large ammount of data, required to demonstrate performance issuees

## The notebooks

- [Generate data](generate_data.ipynb) gives a quick example on how to use the `generate_data` command
- [first_orm_tips](first_orm_tips.ipynb) explains basic ORM errors, and explain how to fix [the reader_per_book view](../../books/views/book/reader_per_book.py)
- [How to detect issues](how_to_detect_issues.ipynb) (WIP) lists several tools and methods to detect perf issues before they become critical
- [About Indexing](about_indexing.ipynb) explains how to properly use Postgres indexes, when basic fixes are not enough, as demonstrated in [review list endpoints](../../books/views/review/__init__.py)
- [aggregation](aggregation.ipynb) tries to show several methods to return a list of annotated objects, as in [the book list endpoint](../../books/views/book/list_books_aggregate.py)
