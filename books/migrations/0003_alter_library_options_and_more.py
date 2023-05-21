# Generated by Django 4.2.1 on 2023-05-23 18:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0002_book_book_library_release_date_idx_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="library",
            options={"verbose_name_plural": "libraries"},
        ),
        migrations.RenameField(
            model_name="review",
            old_name="wrote_at",
            new_name="written_at",
        ),
        migrations.AlterField(
            model_name="book",
            name="library",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="books",
                to="books.library",
            ),
        ),
        migrations.AlterField(
            model_name="booktag",
            name="book",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tags",
                to="books.book",
            ),
        ),
        migrations.AlterField(
            model_name="booktag",
            name="library",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="book_tags",
                to="books.library",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="book",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to="books.book",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="library",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to="books.library",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="reader",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to="books.person",
            ),
        ),
    ]
