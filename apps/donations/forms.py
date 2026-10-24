from decimal import Decimal

from django import forms

from apps.core.forms import BootstrapFormMixin
from apps.programs.models import FocusArea, Project

from .models import Donation

PRESET_AMOUNTS = [500, 1000, 2500, 5000, 10000]
# (amount, what it does) for the gift picker; USD is used for PayPal and card gifts.
IMPACT_KES = [
    (500, "A term of sanitary towels for a schoolgirl"),
    (1000, "Medicine for a family at a medical camp"),
    (2500, "Uniform and stationery for a learner"),
    (5000, "Food parcels for two vulnerable households"),
    (10000, "A term's school fees for a secondary student"),
]
IMPACT_USD = [
    (10, "A term of sanitary towels for two schoolgirls"),
    (25, "Uniform and stationery for a learner"),
    (50, "Food parcels for three vulnerable households"),
    (100, "A term's school fees for a secondary student"),
    (250, "Medicine for a whole medical camp morning"),
]
CARD_METHODS = ("paypal", "card")


class DonationForm(BootstrapFormMixin, forms.ModelForm):
    project = forms.ModelChoiceField(
        queryset=Project.objects.exclude(status="completed"), required=False, empty_label="Where it's most needed",
        label="Support a project")
    focus_area = forms.ModelChoiceField(
        queryset=FocusArea.objects.filter(is_active=True), required=False, empty_label="Any focus area",
        label="Or a focus area")

    class Meta:
        model = Donation
        fields = ["amount", "method", "frequency", "donor_name", "phone", "email", "project", "focus_area",
                  "in_kind_description", "message", "is_anonymous"]
        labels = {"donor_name": "Your name", "phone": "Phone (M-Pesa number)", "message": "Message (optional)",
                  "in_kind_description": "Describe the item(s) you'd like to give"}
        widgets = {
            "amount": forms.NumberInput(attrs={"min": 10, "step": 1, "inputmode": "numeric"}),
            "method": forms.RadioSelect,
            "frequency": forms.RadioSelect,
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["method"].choices = [c for c in Donation.METHOD_CHOICES if c[0] in ("mpesa", "card", "paypal", "bank", "in_kind")]
        self.fields["amount"].required = False

    def clean(self):
        data = super().clean()
        method = data.get("method")
        amount = data.get("amount")
        if method == "mpesa":
            if not data.get("phone"):
                self.add_error("phone", "Enter the M-Pesa number that will receive the payment prompt.")
            if not amount or amount < Decimal("10"):
                self.add_error("amount", "The minimum M-Pesa gift is KES 10.")
            elif amount > Decimal("250000"):
                self.add_error("amount", "M-Pesa allows up to KES 250,000 per transaction. Use bank transfer for larger gifts.")
        elif method in CARD_METHODS:
            if not amount or amount < Decimal("1"):
                self.add_error("amount", "The minimum card or PayPal gift is USD 1.")
            elif amount > Decimal("10000"):
                self.add_error("amount", "For gifts above USD 10,000 please use bank transfer.")
            if not data.get("email"):
                self.add_error("email", "Enter your email so we can send your receipt.")
        elif method == "bank" and (not amount or amount <= 0):
            self.add_error("amount", "Enter the amount you plan to transfer.")
        elif method == "in_kind" and not data.get("in_kind_description"):
            self.add_error("in_kind_description", "Tell us what you'd like to give.")
        if method == "in_kind" and not amount:
            data["amount"] = Decimal("0")
        if not data.get("phone") and not data.get("email"):
            self.add_error("email", "Give us a phone number or email so we can send your receipt.")
        return data
