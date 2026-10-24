from django import forms

from apps.core.forms import BootstrapFormMixin

from .models import EventRegistration


class RegistrationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ["full_name", "phone", "email", "attendees"]
        labels = {"full_name": "Your full name", "phone": "Phone number", "email": "Email (optional)",
                  "attendees": "Number of people coming"}
        help_texts = {"phone": "We'll text you a reminder the day before.", "email": "For your confirmation."}
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "e.g. Grace Achieng"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "0712 345 678"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
            "attendees": forms.NumberInput(attrs={"min": 1, "max": 10}),
        }

    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if self.event and self.event.registrations.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already registered for this event.")
        return phone
