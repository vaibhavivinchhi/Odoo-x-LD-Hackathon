from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(name="Destination", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=120)), ("country", models.CharField(max_length=100)),
            ("region", models.CharField(blank=True, max_length=100)), ("description", models.TextField()),
            ("image_url", models.URLField(blank=True)), ("cost_index", models.PositiveSmallIntegerField(default=2)),
            ("popularity", models.PositiveIntegerField(default=0)), ("best_time", models.CharField(blank=True, max_length=120)),
            ("estimated_daily_cost", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="Profile", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("phone", models.CharField(blank=True, max_length=30)), ("country", models.CharField(blank=True, max_length=80)),
            ("city", models.CharField(blank=True, max_length=80)), ("bio", models.TextField(blank=True)),
            ("avatar", models.ImageField(blank=True, null=True, upload_to="avatars/")),
            ("interests", models.JSONField(blank=True, default=list)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="auth.user")),
        ]),
        migrations.CreateModel(name="Trip", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=180)), ("description", models.TextField(blank=True)),
            ("cover_image", models.ImageField(blank=True, null=True, upload_to="trip_covers/")),
            ("start_date", models.DateField()), ("end_date", models.DateField()), ("starting_location", models.CharField(blank=True, max_length=120)),
            ("budget", models.DecimalField(decimal_places=2, default=0, max_digits=12)), ("currency", models.CharField(choices=[("INR","₹ INR"),("USD","$ USD"),("EUR","€ EUR"),("GBP","£ GBP")], default="INR", max_length=3)),
            ("status", models.CharField(choices=[("draft","Draft"),("upcoming","Upcoming"),("ongoing","Ongoing"),("completed","Completed")], default="draft", max_length=20)),
            ("is_public", models.BooleanField(default=False)), ("share_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("views", models.PositiveIntegerField(default=0)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trips", to="auth.user")),
        ]),
        migrations.CreateModel(name="Activity", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=160)), ("category", models.CharField(choices=[("sightseeing","Sightseeing"),("food","Food"),("adventure","Adventure"),("culture","Culture"),("shopping","Shopping"),("nature","Nature"),("nightlife","Nightlife")], max_length=30)),
            ("description", models.TextField()), ("image_url", models.URLField(blank=True)), ("duration_hours", models.DecimalField(decimal_places=1, default=2, max_digits=4)),
            ("estimated_cost", models.DecimalField(decimal_places=2, default=0, max_digits=10)), ("rating", models.DecimalField(decimal_places=1, default=4.5, max_digits=3)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("destination", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="travel.destination")),
        ]),
        migrations.CreateModel(name="TripStop", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("arrival_date", models.DateField()), ("departure_date", models.DateField()),
            ("order", models.PositiveIntegerField(default=0)), ("notes", models.TextField(blank=True)), ("transport_to_next", models.CharField(blank=True, max_length=100)),
            ("accommodation_cost", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ("destination", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="trip_stops", to="travel.destination")),
            ("trip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stops", to="travel.trip")),
        ]),
        migrations.CreateModel(name="ItineraryDay", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("date", models.DateField()), ("title", models.CharField(blank=True, max_length=160)), ("notes", models.TextField(blank=True)),
            ("trip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="days", to="travel.trip")),
        ]),
        migrations.CreateModel(name="ItineraryActivity", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("start_time", models.TimeField(blank=True, null=True)), ("notes", models.TextField(blank=True)),
            ("custom_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)), ("order", models.PositiveIntegerField(default=0)),
            ("activity", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="scheduled_items", to="travel.activity")),
            ("day", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="travel.itineraryday")),
        ]),
        migrations.CreateModel(name="Expense", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("category", models.CharField(choices=[("transport","Transportation"),("stay","Accommodation"),("activity","Activities"),("food","Food"),("other","Other")], max_length=20)),
            ("description", models.CharField(max_length=180)), ("amount", models.DecimalField(decimal_places=2, max_digits=12)), ("date", models.DateField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("trip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expenses", to="travel.trip")),
        ]),
        migrations.CreateModel(name="SavedDestination", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("destination", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_by", to="travel.destination")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_destinations", to="auth.user")),
        ]),
        migrations.CreateModel(name="TripLike", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("trip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="travel.trip")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user")),
        ]),
        migrations.AddConstraint(model_name="tripstop", constraint=models.UniqueConstraint(fields=("trip","destination","arrival_date"), name="unique_trip_destination_arrival")),
        migrations.AddConstraint(model_name="itineraryday", constraint=models.UniqueConstraint(fields=("trip","date"), name="unique_trip_day")),
        migrations.AddConstraint(model_name="saveddestination", constraint=models.UniqueConstraint(fields=("user","destination"), name="unique_saved_destination")),
        migrations.AddConstraint(model_name="triplike", constraint=models.UniqueConstraint(fields=("user","trip"), name="unique_trip_like")),
        migrations.AddIndex(model_name="destination", index=models.Index(fields=["name"], name="travel_destin_name_4e8b91_idx")),
        migrations.AddIndex(model_name="destination", index=models.Index(fields=["country","region"], name="travel_destin_country_4d3c7f_idx")),
        migrations.AddIndex(model_name="activity", index=models.Index(fields=["category"], name="travel_activ_category_1e8c50_idx")),
        migrations.AddIndex(model_name="activity", index=models.Index(fields=["destination","category"], name="travel_activ_destina_5d5e4a_idx")),
        migrations.AddIndex(model_name="trip", index=models.Index(fields=["owner","start_date"], name="travel_trip_owner_i_5a2f9b_idx")),
        migrations.AddIndex(model_name="trip", index=models.Index(fields=["is_public","start_date"], name="travel_trip_is_publ_9e0c47_idx")),
    ]
