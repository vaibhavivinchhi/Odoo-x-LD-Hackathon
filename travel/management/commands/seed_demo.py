from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from travel.models import Profile, Destination, Activity, Trip, TripStop, ItineraryDay, ItineraryActivity, Expense
from datetime import date, timedelta
from decimal import Decimal

DESTS = [
("Ahmedabad","India","Gujarat","A vibrant heritage city known for food, architecture and the Sabarmati riverfront.",5,4,"Oct–Feb",2500),
("Mumbai","India","Maharashtra","India's energetic coastal metropolis with iconic landmarks, food and nightlife.",5,5,"Nov–Feb",3500),
("Goa","India","Goa","A relaxed coastal escape blending beaches, Portuguese heritage, food and nightlife.",5,5,"Nov–Feb",3000),
("Jaipur","India","Rajasthan","The Pink City, filled with forts, palaces, crafts and royal history.",5,5,"Oct–Mar",2200),
("Udaipur","India","Rajasthan","Lakes, palaces and romantic old-city streets surrounded by the Aravallis.",4,4,"Sep–Mar",2400),
("Manali","India","Himachal Pradesh","A Himalayan base for mountain views, adventure and slow travel.",4,4,"Mar–Jun",2600),
("Dubai","UAE","Dubai","A futuristic city of skyline experiences, desert adventures and global cuisine.",5,5,"Nov–Mar",8500),
("Paris","France","Île-de-France","Art, architecture, cafés and iconic experiences along the Seine.",5,5,"Apr–Jun",12000),
("London","UK","England","A cultural capital with museums, theatre, parks and historic neighborhoods.",5,5,"May–Sep",14000),
("Tokyo","Japan","Kanto","A high-energy blend of tradition, technology, food and design.",5,5,"Mar–May",11000),
("New York","USA","New York","A global city of neighborhoods, museums, food, Broadway and iconic views.",5,5,"Apr–Jun",15000),
]
ACTS = {
"Ahmedabad":[("Sabarmati Riverfront","nature",2,0),("Adalaj Stepwell","culture",2,100),("Heritage Walk","culture",3,250),("Gujarati Food Trail","food",3,700)],
"Mumbai":[("Gateway of India","sightseeing",2,0),("Colaba Food Walk","food",3,800),("Marine Drive Sunset","nature",2,0),("Elephanta Caves","culture",5,500)],
"Goa":[("Baga Beach Day","nature",5,0),("Old Goa Heritage Tour","culture",3,500),("Dudhsagar Adventure","adventure",8,1800),("Sunset Cruise","nightlife",2,1200)],
"Jaipur":[("Amber Fort","culture",3,500),("City Palace","culture",2,500),("Hawa Mahal","sightseeing",2,200),("Rajasthani Dinner","food",2,900)],
"Udaipur":[("City Palace","culture",3,600),("Lake Pichola Boat Ride","nature",2,800),("Sajjangarh Sunset","sightseeing",3,300)],
"Manali":[("Solang Valley","adventure",6,1200),("Old Manali Walk","culture",2,0),("River Rafting","adventure",4,1600)],
"Dubai":[("Burj Khalifa","sightseeing",3,3500),("Desert Safari","adventure",6,4500),("Dubai Mall Food Tour","food",3,1800)],
"Paris":[("Eiffel Tower","sightseeing",3,3000),("Louvre Museum","culture",4,2500),("Seine Cruise","nature",2,1800),("French Food Tour","food",3,3500)],
"London":[("British Museum","culture",4,0),("London Eye","sightseeing",2,3500),("West End Show","nightlife",3,5000)],
"Tokyo":[("Shibuya Experience","sightseeing",3,1200),("Senso-ji Temple","culture",2,0),("Tsukiji Food Tour","food",3,2500)],
"New York":[("Central Park","nature",3,0),("Statue of Liberty","sightseeing",4,3000),("Broadway Show","nightlife",3,8000)],
}

class Command(BaseCommand):
    help = "Populate realistic GlobeTrotter demo data"

    def handle(self, *args, **kwargs):
        for d in DESTS:
            name,country,region,desc,pop,costidx,best,daily = d
            obj,_ = Destination.objects.update_or_create(name=name,country=country,defaults={
                "region":region,"description":desc,"popularity":pop*20,"cost_index":costidx,"best_time":best,"estimated_daily_cost":daily,
                "image_url": f"https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"
            })
            for aname,cat,dur,cost in ACTS.get(name,[]):
                Activity.objects.update_or_create(destination=obj,name=aname,defaults={
                    "category":cat,"duration_hours":dur,"estimated_cost":cost,"rating":4.6,
                    "description":f"Plan a memorable {aname.lower()} experience in {name}."
                })

        user,created = User.objects.get_or_create(username="demo",defaults={"email":"demo@globetrotter.local","first_name":"Aarav","last_name":"Traveler"})
        if created:
            user.set_password("Demo@12345")
            user.save()
        Profile.objects.get_or_create(user=user,defaults={"country":"India","city":"Ahmedabad","bio":"Always planning the next adventure."})

        if not user.trips.exists():
            ahm=Destination.objects.get(name="Ahmedabad")
            goa=Destination.objects.get(name="Goa")
            trip=Trip.objects.create(owner=user,title="West Coast Escape",description="A relaxed multi-city journey from heritage streets to the beach.",start_date=date.today()+timedelta(days=20),end_date=date.today()+timedelta(days=24),budget=Decimal("30000"),currency="INR",status="upcoming",is_public=True)
            for i,(dest,arr,dep) in enumerate([(ahm,trip.start_date,trip.start_date+timedelta(days=1)),(goa,trip.start_date+timedelta(days=2),trip.end_date)]):
                TripStop.objects.create(trip=trip,destination=dest,arrival_date=arr,departure_date=dep,order=i,accommodation_cost=Decimal("2500"))
            cur=trip.start_date
            while cur<=trip.end_date:
                day=ItineraryDay.objects.create(trip=trip,date=cur,title="Explore & enjoy")
                acts=list(Activity.objects.filter(destination=ahm if cur<=trip.start_date+timedelta(days=1) else goa)[:2])
                for j,a in enumerate(acts):
                    ItineraryActivity.objects.create(day=day,activity=a,order=j)
                cur += timedelta(days=1)
            Expense.objects.create(trip=trip,category="stay",description="Hotels",amount=Decimal("10000"))
            Expense.objects.create(trip=trip,category="activity",description="Experiences",amount=Decimal("3500"))
            Expense.objects.create(trip=trip,category="food",description="Food budget",amount=Decimal("5000"))
            Expense.objects.create(trip=trip,category="transport",description="Intercity transport",amount=Decimal("4500"))
        self.stdout.write(self.style.SUCCESS("Demo data ready. Login: demo / Demo@12345"))
