# GlobeTrotter — Django Travel Planner

GlobeTrotter is a responsive travel-planning application built with **Django + Python + SQL (SQLite by default)**. It follows the supplied hackathon brief: multi-city itineraries, dates, activities, budgets, search/discovery, calendar/timeline, public sharing, community inspiration, profiles and admin analytics.

## Final UI / UX updates
- App root opens directly on the themed Login screen. No public navbar is shown on Login/Register/Password Reset/Logout screens.
- Aurora travel UI: deep navy background, violet/cyan/pink gradients, glass cards and responsive layouts.
- Centered footer on application pages; removed the old “Built with Django · Hackathon edition” text.
- Navbar avatar opens an editable quick-profile panel; Full Profile remains available for detailed editing.
- Explore is a functional dropdown with destination discovery, activities, saved places and community links.
- Explore search supports city/country/activity/category filtering.
- Destinations can be saved and added directly to an existing trip.
- Activities can be added directly to an itinerary day, with optional start time and custom cost, then reordered or removed.
- Add Stop uses a searchable, scrollable destination picker instead of an oversized native select.
- Trip actions use one consistent premium button style: Edit, Add Stop, Add Expense, Share and Duplicate.
- Trip itinerary day generation is synchronized to the actual trip date range. Shortening a trip removes stale itinerary days, fixing the old 400+ day issue.
- Destination stops can be reordered or removed.
- Calendar is generated from the real trip date range.
- Profile includes editable personal details, saved destinations and account deletion.
- Public itinerary sharing, likes and Copy Trip are supported.
- Budget breakdown chart and average daily spend are shown on trip details.

## Run locally

```bash
python -m venv venv
venv\\Scripts\\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

### Demo account
- Username: `demo`
- Password: `Demo@12345`

### Admin
```bash
python manage.py createsuperuser
```
Then open `http://127.0.0.1:8000/admin/`.

## Database
SQLite is the default and requires no separate database server. The project uses Django ORM relational models for users, profiles, destinations, activities, trips, stops, itinerary days, itinerary activities, expenses, saved destinations and public-trip likes.

For a different SQL database, change `DATABASES` in `config/settings.py` and install the corresponding Django database driver.
