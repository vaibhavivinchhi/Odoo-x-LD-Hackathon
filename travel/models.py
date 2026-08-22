import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

class Profile(models.Model):
    INTERESTS = [
        ("culture", "Culture"), ("food", "Food"), ("nature", "Nature"),
        ("adventure", "Adventure"), ("shopping", "Shopping"), ("nightlife", "Nightlife"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    interests = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} Profile"

class Destination(models.Model):
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    image_url = models.URLField(blank=True)
    cost_index = models.PositiveSmallIntegerField(default=2, help_text="1=budget, 5=luxury")
    popularity = models.PositiveIntegerField(default=0)
    best_time = models.CharField(max_length=120, blank=True)
    estimated_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-popularity", "name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["country", "region"])]

    def __str__(self):
        return f"{self.name}, {self.country}"

class Activity(models.Model):
    CATEGORIES = [
        ("sightseeing", "Sightseeing"), ("food", "Food"), ("adventure", "Adventure"),
        ("culture", "Culture"), ("shopping", "Shopping"), ("nature", "Nature"),
        ("nightlife", "Nightlife"),
    ]
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="activities")
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    description = models.TextField()
    image_url = models.URLField(blank=True)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, default=2)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-rating", "name"]
        indexes = [models.Index(fields=["category"]), models.Index(fields=["destination", "category"])]

    def __str__(self):
        return self.name

class Trip(models.Model):
    STATUS_CHOICES = [("draft","Draft"),("upcoming","Upcoming"),("ongoing","Ongoing"),("completed","Completed")]
    CURRENCY_CHOICES = [("INR","₹ INR"),("USD","$ USD"),("EUR","€ EUR"),("GBP","£ GBP")]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="trip_covers/", blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    starting_location = models.CharField(max_length=120, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="INR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_public = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [models.Index(fields=["owner", "start_date"]), models.Index(fields=["is_public", "start_date"])]

    @property
    def duration(self):
        return max((self.end_date - self.start_date).days + 1, 1)

    @property
    def total_estimated_cost(self):
        return self.expenses.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")

    @property
    def remaining_budget(self):
        return self.budget - self.total_estimated_cost

    @property
    def budget_percentage(self):
        if self.budget <= 0:
            return 0
        return min(float(self.total_estimated_cost / self.budget * 100), 999)

    @property
    def destination_count(self):
        return self.stops.values("destination").distinct().count()

    def get_absolute_url(self):
        return reverse("trip_detail", args=[self.pk])

    def __str__(self):
        return self.title

class TripStop(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="stops")
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name="trip_stops")
    arrival_date = models.DateField()
    departure_date = models.DateField()
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    transport_to_next = models.CharField(max_length=100, blank=True)
    accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["order", "arrival_date"]
        constraints = [models.UniqueConstraint(fields=["trip", "destination", "arrival_date"], name="unique_trip_destination_arrival")]

    def __str__(self):
        return f"{self.trip} — {self.destination}"

class ItineraryDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="days")
    date = models.DateField()
    title = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]
        constraints = [models.UniqueConstraint(fields=["trip", "date"], name="unique_trip_day")]

class ItineraryActivity(models.Model):
    day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name="activities")
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, related_name="scheduled_items")
    start_time = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    custom_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "start_time"]

    @property
    def cost(self):
        return self.custom_cost if self.custom_cost is not None else self.activity.estimated_cost

class Expense(models.Model):
    CATEGORIES = [("transport", "Transportation"), ("stay", "Accommodation"), ("activity", "Activities"), ("food", "Food"), ("other", "Other")]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.CharField(max_length=180)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "created_at"]

class SavedDestination(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_destinations")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "destination"], name="unique_saved_destination")]

class TripLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "trip"], name="unique_trip_like")]
