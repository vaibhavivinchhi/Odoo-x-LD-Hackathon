from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.destinations,
        name="destinations"
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "trips/",
        views.trips,
        name="trips"
    ),

    path(
        "trips/create/",
        views.create_trip,
        name="create_trip"
    ),

    path(
        "trips/<int:trip_id>/itinerary/",
        views.itinerary,
        name="itinerary"
    ),

    path(
        "trips/<int:trip_id>/add-stop/",
        views.add_stop,
        name="add_stop"
    ),
]