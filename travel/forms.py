from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Trip, TripStop, Expense


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    phone = forms.CharField(max_length=30, required=False)
    country = forms.CharField(max_length=80, required=False)
    city = forms.CharField(max_length=80, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone", "country", "city", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            Profile.objects.update_or_create(user=user, defaults={
                "phone": self.cleaned_data.get("phone", ""),
                "country": self.cleaned_data.get("country", ""),
                "city": self.cleaned_data.get("city", ""),
            })
        return user


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ["title", "description", "cover_image", "start_date", "end_date", "starting_location", "budget", "currency", "is_public"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        data = super().clean()
        if data.get("start_date") and data.get("end_date") and data["end_date"] < data["start_date"]:
            raise forms.ValidationError("End date must be on or after the start date.")
        if data.get("budget") is not None and data["budget"] < 0:
            raise forms.ValidationError("Budget cannot be negative.")
        return data


class TripStopForm(forms.ModelForm):
    class Meta:
        model = TripStop
        fields = ["destination", "arrival_date", "departure_date", "notes", "transport_to_next", "accommodation_cost"]
        widgets = {
            "arrival_date": forms.DateInput(attrs={"type": "date"}),
            "departure_date": forms.DateInput(attrs={"type": "date"}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "description", "amount", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "country", "city", "bio", "avatar"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class QuickProfileForm(forms.ModelForm):
    """Small profile editor used directly from the navbar avatar menu."""
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email address"}),
        }
