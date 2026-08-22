from django.contrib import admin
from .models import Profile, Destination, Activity, Trip, TripStop, ItineraryDay, ItineraryActivity, Expense, SavedDestination, TripLike

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "region", "cost_index", "popularity", "estimated_daily_cost")
    search_fields = ("name", "country", "region")
    list_filter = ("country", "cost_index")

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "destination", "category", "estimated_cost", "rating")
    search_fields = ("name", "destination__name")
    list_filter = ("category",)

class StopInline(admin.TabularInline):
    model = TripStop
    extra = 0

class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "start_date", "end_date", "status", "is_public", "budget", "views")
    search_fields = ("title", "owner__username")
    list_filter = ("status", "is_public", "currency")
    inlines = [StopInline, ExpenseInline]

admin.site.register(Profile)
admin.site.register(TripStop)
admin.site.register(ItineraryDay)
admin.site.register(ItineraryActivity)
admin.site.register(Expense)
admin.site.register(SavedDestination)
admin.site.register(TripLike)
