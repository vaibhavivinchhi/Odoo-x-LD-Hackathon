from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required

from .models import Trip
from .models import TripStop


def destinations(request):

    return render(
        request,
        "destinations/destinations.html"
    )


@login_required
def dashboard(request):

    user_trips = Trip.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "dashboard.html",
        {
            "trips": user_trips
        }
    )


@login_required
def trips(request):

    user_trips = Trip.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "trips.html",
        {
            "trips": user_trips
        }
    )


@login_required
def create_trip(request):

    if request.method == "POST":

        name = request.POST.get("name")

        description = request.POST.get("description")

        start_date = request.POST.get("start_date")

        end_date = request.POST.get("end_date")

        budget = request.POST.get("budget")

        trip = Trip.objects.create(

            user=request.user,

            name=name,

            description=description,

            start_date=start_date,

            end_date=end_date,

            budget=budget
        )

        return redirect(
            "itinerary",
            trip_id=trip.id
        )

    return render(
        request,
        "create_trip.html"
    )


@login_required
def itinerary(request, trip_id):

    trip = get_object_or_404(
        Trip,
        id=trip_id,
        user=request.user
    )

    stops = TripStop.objects.filter(
        trip=trip
    ).order_by(
        "order",
        "start_date"
    )

    return render(
        request,
        "itinerary.html",
        {
            "trip": trip,
            "stops": stops
        }
    )


@login_required
def add_stop(request, trip_id):

    trip = get_object_or_404(
        Trip,
        id=trip_id,
        user=request.user
    )

    if request.method == "POST":

        city = request.POST.get("city")

        country = request.POST.get("country")

        start_date = request.POST.get("start_date")

        end_date = request.POST.get("end_date")

        activity = request.POST.get("activity")

        cost = request.POST.get("cost")

        TripStop.objects.create(

            trip=trip,

            city=city,

            country=country,

            start_date=start_date,

            end_date=end_date,

            activity=activity,

            cost=cost
        )

        return redirect(
            "itinerary",
            trip_id=trip.id
        )

    return render(
        request,
        "destinations/add_stop.html",
        {
            "trip": trip
        }
    )