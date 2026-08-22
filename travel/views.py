from datetime import timedelta
from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import RegisterForm, TripForm, TripStopForm, ExpenseForm, ProfileForm, UserInfoForm, QuickProfileForm
from .models import Destination, Activity, Trip, TripStop, ItineraryDay, ItineraryActivity, Expense, SavedDestination, TripLike


def landing(request):
    # The application opens on authentication, not the marketing site.
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to GlobeTrotter! Let's plan something unforgettable.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})

def _refresh_status(trip):
    today = timezone.localdate()
    if trip.status != "draft":
        if today < trip.start_date:
            trip.status = "upcoming"
        elif today > trip.end_date:
            trip.status = "completed"
        else:
            trip.status = "ongoing"
        trip.save(update_fields=["status", "updated_at"])

def _ensure_days(trip):
    """Keep itinerary days exactly inside the trip date range.

    This also fixes the old 400+ day issue when a trip was shortened after
    its itinerary days had already been generated.
    """
    trip.days.filter(Q(date__lt=trip.start_date) | Q(date__gt=trip.end_date)).delete()
    existing = set(trip.days.values_list("date", flat=True))
    cur = trip.start_date
    while cur <= trip.end_date:
        if cur not in existing:
            ItineraryDay.objects.create(trip=trip, date=cur)
        cur += timedelta(days=1)


def logout_view(request):
    """Show a branded logout confirmation page and log out on POST."""
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully. See you on your next adventure!")
        return redirect("landing")
    return render(request, "registration/logged_out.html")

@login_required
def dashboard(request):
    trips = list(request.user.trips.all()[:8])
    for trip in trips:
        _refresh_status(trip)
    upcoming = request.user.trips.filter(start_date__gte=timezone.localdate()).order_by("start_date")[:4]
    recent = request.user.trips.order_by("-updated_at")[:4]
    destinations = Destination.objects.all()[:6]
    stats = {
        "total": request.user.trips.count(),
        "upcoming": request.user.trips.filter(start_date__gte=timezone.localdate()).count(),
        "ongoing": request.user.trips.filter(start_date__lte=timezone.localdate(), end_date__gte=timezone.localdate()).count(),
        "completed": request.user.trips.filter(end_date__lt=timezone.localdate()).count(),
    }
    return render(request, "travel/dashboard.html", {"upcoming": upcoming, "recent": recent, "destinations": destinations, "stats": stats})

@login_required
def trip_list(request):
    qs = request.user.trips.all()
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if status:
        qs = qs.filter(status=status)
    for trip in qs[:50]:
        _refresh_status(trip)
    return render(request, "travel/trip_list.html", {"trips": qs, "q": q, "status": status})

@login_required
def trip_create(request):
    form = TripForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        trip = form.save(commit=False)
        trip.owner = request.user
        trip.status = "upcoming"
        trip.save()
        _ensure_days(trip)
        messages.success(request, "Trip created. Now build your itinerary.")
        return redirect("trip_detail", trip.pk)
    return render(request, "travel/trip_form.html", {"form": form, "title": "Plan a new trip"})

@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if trip.owner != request.user and not trip.is_public:
        raise Http404
    if trip.owner == request.user:
        _refresh_status(trip)
    _ensure_days(trip)
    days = trip.days.prefetch_related("activities__activity__destination").all()
    stops = trip.stops.select_related("destination").all()
    expenses = trip.expenses.all()
    categories = {k: 0 for k, _ in Expense.CATEGORIES}
    for e in expenses:
        categories[e.category] += float(e.amount)
    activities = Activity.objects.select_related("destination").all()
    average_daily_cost = (trip.total_estimated_cost / trip.duration) if trip.duration else 0
    return render(request, "travel/trip_detail.html", {"trip": trip, "days": days, "stops": stops, "expenses": expenses, "categories": categories, "activities": activities, "average_daily_cost": average_daily_cost})

@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    form = TripForm(request.POST or None, request.FILES or None, instance=trip)
    if request.method == "POST" and form.is_valid():
        trip = form.save()
        _ensure_days(trip)
        messages.success(request, "Trip updated.")
        return redirect("trip_detail", trip.pk)
    return render(request, "travel/trip_form.html", {"form": form, "title": "Edit trip", "trip": trip})

@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    if request.method == "POST":
        trip.delete()
        messages.success(request, "Trip deleted.")
        return redirect("trip_list")
    return render(request, "travel/confirm_delete.html", {"trip": trip})

@login_required
def trip_duplicate(request, pk):
    original = get_object_or_404(Trip, pk=pk, owner=request.user)
    new = Trip.objects.create(owner=request.user, title=f"{original.title} — Copy", description=original.description,
                              start_date=original.start_date, end_date=original.end_date, starting_location=original.starting_location,
                              budget=original.budget, currency=original.currency, is_public=False, status="draft")
    for stop in original.stops.all():
        TripStop.objects.create(trip=new, destination=stop.destination, arrival_date=stop.arrival_date, departure_date=stop.departure_date,
                                order=stop.order, notes=stop.notes, transport_to_next=stop.transport_to_next, accommodation_cost=stop.accommodation_cost)
    _ensure_days(new)
    for day in original.days.prefetch_related("activities").all():
        nd = new.days.get(date=day.date)
        nd.title, nd.notes = day.title, day.notes
        nd.save()
        for item in day.activities.all():
            ItineraryActivity.objects.create(day=nd, activity=item.activity, start_time=item.start_time, notes=item.notes, custom_cost=item.custom_cost, order=item.order)
    for expense in original.expenses.all():
        Expense.objects.create(trip=new, category=expense.category, description=expense.description, amount=expense.amount, date=expense.date)
    messages.success(request, "Trip duplicated as a draft.")
    return redirect("trip_detail", new.pk)

@login_required
def stop_add(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    form = TripStopForm(request.POST or None)
    # The visual destination picker below replaces the very long native select.
    form.fields["destination"].widget = forms.HiddenInput()
    form.fields["destination"].required = False
    if request.method == "POST" and not request.POST.get("destination"):
        form.add_error("destination", "Choose a destination from the list.")
    if request.method == "POST" and form.is_valid():
        stop = form.save(commit=False)
        stop.trip = trip
        if stop.arrival_date < trip.start_date or stop.departure_date > trip.end_date or stop.departure_date < stop.arrival_date:
            form.add_error(None, "Stop dates must fall inside the trip and departure cannot be before arrival.")
        else:
            stop.order = trip.stops.count()
            stop.save()
            messages.success(request, f"{stop.destination.name} added to your trip.")
            return redirect("trip_detail", trip.pk)
    destinations = form.fields["destination"].queryset.order_by("country", "name")
    return render(request, "travel/stop_add.html", {"form": form, "title": "Add destination stop", "back_url": trip.get_absolute_url(), "trip": trip, "destinations": destinations})

@login_required
def stop_move(request, pk, direction):
    stop = get_object_or_404(TripStop, pk=pk, trip__owner=request.user)
    stops = list(stop.trip.stops.order_by("order", "arrival_date"))
    index = stops.index(stop)
    target = index - 1 if direction == "up" else index + 1
    if 0 <= target < len(stops):
        stops[index], stops[target] = stops[target], stops[index]
        for position, item in enumerate(stops):
            if item.order != position:
                TripStop.objects.filter(pk=item.pk).update(order=position)
        messages.success(request, "Route order updated.")
    return redirect("trip_detail", stop.trip.pk)

@login_required
def stop_delete(request, pk):
    stop = get_object_or_404(TripStop, pk=pk, trip__owner=request.user)
    trip_pk = stop.trip.pk
    if request.method == "POST":
        stop.delete()
        messages.success(request, "Destination removed from the trip.")
    return redirect("trip_detail", trip_pk)

@login_required
def expense_add(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        e = form.save(commit=False)
        e.trip = trip
        e.save()
        messages.success(request, "Expense added.")
        return redirect("trip_detail", trip.pk)
    return render(request, "travel/modal_form.html", {"form": form, "title": "Add expense", "back_url": trip.get_absolute_url()})

@login_required
def trip_share(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    trip.is_public = True
    trip.save(update_fields=["is_public", "updated_at"])
    return render(request, "travel/share.html", {"trip": trip, "share_url": request.build_absolute_uri(f"/shared/{trip.share_token}/")})

def shared_trip(request, token):
    trip = get_object_or_404(Trip.objects.select_related("owner"), share_token=token, is_public=True)
    trip.views += 1
    trip.save(update_fields=["views"])
    _ensure_days(trip)
    days = trip.days.prefetch_related("activities__activity__destination").all()
    return render(request, "travel/shared_trip.html", {"trip": trip, "days": days, "likes": trip.likes.count()})

@login_required
def toggle_public(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    trip.is_public = not trip.is_public
    trip.save(update_fields=["is_public", "updated_at"])
    messages.success(request, "Trip is now " + ("public." if trip.is_public else "private."))
    return redirect("trip_detail", pk)

@login_required
def like_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk, is_public=True)
    like, created = TripLike.objects.get_or_create(user=request.user, trip=trip)
    if not created:
        like.delete()
    return JsonResponse({"liked": created, "likes": trip.likes.count()})

@login_required
def copy_public_trip(request, pk):
    original = get_object_or_404(Trip, pk=pk, is_public=True)
    new = Trip.objects.create(owner=request.user, title=f"{original.title} — Inspired Trip", description=original.description,
                              start_date=original.start_date, end_date=original.end_date, starting_location=original.starting_location,
                              budget=original.budget, currency=original.currency, status="draft")
    for stop in original.stops.all():
        TripStop.objects.create(trip=new, destination=stop.destination, arrival_date=stop.arrival_date, departure_date=stop.departure_date,
                                order=stop.order, notes=stop.notes, transport_to_next=stop.transport_to_next, accommodation_cost=stop.accommodation_cost)
    _ensure_days(new)
    for day in original.days.prefetch_related("activities").all():
        nd = new.days.get(date=day.date)
        nd.title, nd.notes = day.title, day.notes
        nd.save()
        for item in day.activities.all():
            ItineraryActivity.objects.create(day=nd, activity=item.activity, start_time=item.start_time, notes=item.notes, custom_cost=item.custom_cost, order=item.order)
    messages.success(request, "A copy has been added to My Trips.")
    return redirect("trip_detail", new.pk)

@login_required
def activity_add(request, trip_pk, day_pk):
    trip = get_object_or_404(Trip, pk=trip_pk, owner=request.user)
    day = get_object_or_404(ItineraryDay, pk=day_pk, trip=trip)
    if request.method == "POST":
        activity_id = request.POST.get("activity")
        activity = get_object_or_404(Activity, pk=activity_id)
        custom_cost = request.POST.get("custom_cost") or None
        start_time = request.POST.get("start_time") or None
        ItineraryActivity.objects.create(
            day=day, activity=activity, custom_cost=custom_cost, start_time=start_time, order=day.activities.count()
        )
        messages.success(request, f"{activity.name} added to Day {day.date.strftime('%b %d')}.")
    return redirect("trip_detail", trip.pk)

@login_required
def activity_move(request, pk, direction):
    item = get_object_or_404(ItineraryActivity, pk=pk, day__trip__owner=request.user)
    items = list(item.day.activities.order_by("order", "start_time"))
    index = items.index(item)
    target = index - 1 if direction == "up" else index + 1
    if 0 <= target < len(items):
        items[index], items[target] = items[target], items[index]
        for position, obj in enumerate(items):
            ItineraryActivity.objects.filter(pk=obj.pk).update(order=position)
        messages.success(request, "Activity order updated.")
    return redirect("trip_detail", item.day.trip.pk)

@login_required
def activity_remove(request, pk):
    item = get_object_or_404(ItineraryActivity, pk=pk, day__trip__owner=request.user)
    trip_pk = item.day.trip.pk
    if request.method == "POST":
        item.delete()
        messages.success(request, "Activity removed from your itinerary.")
    return redirect("trip_detail", trip_pk)

@login_required
def delete_account(request):
    if request.method == "POST":
        request.user.delete()
        logout(request)
        messages.success(request, "Your GlobeTrotter account has been deleted.")
        return redirect("landing")
    return redirect("profile")

@login_required
def quick_profile_update(request):
    if request.method != "POST":
        return redirect("profile")
    form = QuickProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
    else:
        messages.error(request, "Please check your profile details.")
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))

def explore(request):
    q = request.GET.get("q", "").strip()
    country = request.GET.get("country", "")
    category = request.GET.get("category", "")
    destinations = Destination.objects.all()
    activities = Activity.objects.select_related("destination").all()
    if q:
        destinations = destinations.filter(Q(name__icontains=q) | Q(country__icontains=q) | Q(description__icontains=q))
        activities = activities.filter(Q(name__icontains=q) | Q(destination__name__icontains=q))
    if country:
        destinations = destinations.filter(country__iexact=country)
    if category:
        activities = activities.filter(category=category)
    countries = Destination.objects.values_list("country", flat=True).distinct().order_by("country")
    user_trips = request.user.trips.order_by("start_date")[:20] if request.user.is_authenticated else []
    user_days = ItineraryDay.objects.filter(trip__owner=request.user).select_related("trip").order_by("date")[:120] if request.user.is_authenticated else []
    saved_ids = set(request.user.saved_destinations.values_list("destination_id", flat=True)) if request.user.is_authenticated else set()
    return render(request, "travel/explore.html", {"destinations": destinations[:30], "activities": activities[:30], "countries": countries, "q": q, "country": country, "category": category, "user_trips": user_trips, "user_days": user_days, "saved_ids": saved_ids})

@login_required
def add_destination_to_trip(request, destination_pk):
    destination = get_object_or_404(Destination, pk=destination_pk)
    trip = get_object_or_404(Trip, pk=request.POST.get("trip"), owner=request.user)
    arrival = request.POST.get("arrival_date") or trip.start_date
    departure = request.POST.get("departure_date") or arrival
    form = TripStopForm({
        "destination": destination.pk,
        "arrival_date": arrival,
        "departure_date": departure,
        "notes": request.POST.get("notes", ""),
        "transport_to_next": request.POST.get("transport_to_next", ""),
        "accommodation_cost": request.POST.get("accommodation_cost") or 0,
    })
    if form.is_valid():
        stop = form.save(commit=False)
        stop.trip = trip
        if stop.arrival_date < trip.start_date or stop.departure_date > trip.end_date or stop.departure_date < stop.arrival_date:
            messages.error(request, "Choose dates that fall inside the trip dates.")
        else:
            stop.order = trip.stops.count()
            stop.save()
            messages.success(request, f"{destination.name} added to {trip.title}.")
    else:
        messages.error(request, "Could not add this destination. Check the selected dates.")
    return redirect(request.META.get("HTTP_REFERER", "explore"))

@login_required
def save_destination(request, pk):
    destination = get_object_or_404(Destination, pk=pk)
    obj, created = SavedDestination.objects.get_or_create(user=request.user, destination=destination)
    if not created:
        obj.delete()
    messages.success(request, f"{destination.name} " + ("saved." if created else "removed from saved places."))
    return redirect(request.META.get("HTTP_REFERER", "explore"))

@login_required
def calendar_view(request):
    trips = request.user.trips.filter(end_date__gte=timezone.localdate()).prefetch_related("days__activities__activity")
    events = []
    for trip in trips:
        _ensure_days(trip)
        for day in trip.days.all():
            events.append({"date": day.date.isoformat(), "title": f"{trip.title} · {day.title or 'Travel day'}", "url": trip.get_absolute_url()})
    return render(request, "travel/calendar.html", {"events": events})

def community(request):
    trips = Trip.objects.filter(is_public=True).select_related("owner").prefetch_related("stops").order_by("-views", "-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        trips = trips.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(stops__destination__name__icontains=q)).distinct()
    return render(request, "travel/community.html", {"trips": trips[:40], "q": q})

@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    user_form = UserInfoForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=profile_obj)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")
    saved = SavedDestination.objects.filter(user=request.user).select_related("destination")
    return render(request, "travel/profile.html", {"user_form": user_form, "profile_form": profile_form, "saved": saved})

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    context = {
        "users": User.objects.count(),
        "trips": Trip.objects.count(),
        "public_trips": Trip.objects.filter(is_public=True).count(),
        "destinations": Destination.objects.count(),
        "activities": Activity.objects.count(),
        "top_destinations": Destination.objects.annotate(uses=Count("trip_stops")).order_by("-uses", "-popularity")[:8],
        "top_activities": Activity.objects.annotate(uses=Count("scheduled_items")).order_by("-uses", "-rating")[:8],
        "recent_users": User.objects.order_by("-date_joined")[:8],
        "recent_trips": Trip.objects.select_related("owner").order_by("-created_at")[:8],
    }
    return render(request, "travel/admin_dashboard.html", context)
