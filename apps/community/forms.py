from django import forms

from apps.core.forms import BootstrapFormMixin
from apps.programs.models import FocusArea

from .models import ContactMessage, Feedback, HelpRequest, NewsletterSubscriber, PartnershipInquiry, VolunteerApplication


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}


class VolunteerForm(BootstrapFormMixin, forms.ModelForm):
    focus_areas = forms.ModelMultipleChoiceField(
        queryset=FocusArea.objects.filter(is_active=True), widget=forms.CheckboxSelectMultiple, required=False,
        label="Areas you'd like to serve in")

    class Meta:
        model = VolunteerApplication
        fields = ["full_name", "email", "phone", "location", "profession", "focus_areas", "skills", "availability", "motivation"]
        widgets = {"skills": forms.Textarea(attrs={"rows": 3}), "motivation": forms.Textarea(attrs={"rows": 3})}


class PartnershipForm(BootstrapFormMixin, forms.ModelForm):
    focus_areas = forms.ModelMultipleChoiceField(
        queryset=FocusArea.objects.filter(is_active=True), widget=forms.CheckboxSelectMultiple, required=False,
        label="Areas of interest")

    class Meta:
        model = PartnershipInquiry
        fields = ["organisation", "contact_person", "email", "phone", "partner_type", "focus_areas", "interest"]
        widgets = {"interest": forms.Textarea(attrs={"rows": 4})}


class FeedbackForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["kind", "name", "phone", "email", "focus_area", "message"]
        labels = {"kind": "Type of feedback"}
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["focus_area"].queryset = FocusArea.objects.filter(is_active=True)
        self.fields["focus_area"].empty_label = "General / not sure"


class HelpRequestForm(BootstrapFormMixin, forms.ModelForm):
    consent = forms.BooleanField(
        required=True,
        label="I agree that PEFA GraceWorks may store this information to assess and follow up my request. "
              "It will not be shared outside the organisation without my permission.")

    class Meta:
        model = HelpRequest
        fields = ["full_name", "phone", "location", "ward", "need_type", "urgency", "description",
                  "household_size", "children_under_18", "monthly_income", "is_single_parent", "has_disability",
                  "is_elderly_headed", "is_child_headed", "referred_by", "consent"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "household_size": forms.NumberInput(attrs={"min": 1, "max": 30}),
            "children_under_18": forms.NumberInput(attrs={"min": 0, "max": 20}),
        }

    def clean(self):
        data = super().clean()
        size, kids = data.get("household_size") or 0, data.get("children_under_18") or 0
        if kids > size:
            self.add_error("children_under_18", "Can't be more than the number of people in the household.")
        phone = data.get("phone")
        if phone and HelpRequest.objects.filter(phone=phone, status__in=["new", "under_review"]).exists():
            raise forms.ValidationError(
                "This phone number already has a request being reviewed. Use 'Track my request' to check on it.")
        return data


class TrackForm(BootstrapFormMixin, forms.Form):
    reference = forms.CharField(max_length=12, label="Reference number",
                                widget=forms.TextInput(attrs={"placeholder": "e.g. HR-7K2M9Q", "autocapitalize": "characters"}))
    phone = forms.CharField(max_length=20, label="Phone number used on the request")

    def clean_reference(self):
        return self.cleaned_data["reference"].strip().upper()


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
