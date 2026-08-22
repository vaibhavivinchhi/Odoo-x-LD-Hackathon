from django.db import models
from django.contrib.auth.models import User


class Destination(models.Model):

    name = models.CharField(
        max_length=150
    )

    country = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    image = models.URLField(
        blank=True
    )

    cost_index = models.CharField(
        max_length=50,
        default="Moderate"
    )

    popularity = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):

        return self.name


class Trip(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="travel_trips"
    )

    name = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    start_date = models.DateField()

    end_date = models.DateField()

    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name


class TripStop(models.Model):

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="stops"
    )

    city = models.CharField(
        max_length=150
    )

    country = models.CharField(
        max_length=150,
        default="India"
    )

    start_date = models.DateField()

    end_date = models.DateField()

    activity = models.CharField(
        max_length=200,
        blank=True
    )

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    order = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):

        return self.city