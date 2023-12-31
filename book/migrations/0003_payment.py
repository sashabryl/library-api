# Generated by Django 4.2.7 on 2023-11-28 08:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("book", "0002_alter_book_cover"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("PAID", "Paid"), ("PENDING", "Pending")],
                        max_length=7,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("PAYMENT", "Payment"), ("FINE", "Fine")],
                        max_length=7,
                    ),
                ),
                ("session_url", models.URLField()),
                ("session_id", models.CharField(max_length=16)),
                (
                    "money_to_pay",
                    models.DecimalField(decimal_places=2, max_digits=6),
                ),
                (
                    "borrowing",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="book.borrowing",
                    ),
                ),
            ],
        ),
    ]
