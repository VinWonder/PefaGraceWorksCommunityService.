from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.core.utils import notify_person, notify_staff, rate_limit

from .forms import (ContactForm, FeedbackForm, HelpRequestForm, NewsletterForm, PartnershipForm, TrackForm,
                    VolunteerForm)
from .models import Feedback, HelpRequest, NewsletterSubscriber


def _same_phone(a, b):
    digits = lambda x: "".join(c for c in (x or "") if c.isdigit())[-9:]
    return bool(digits(a)) and digits(a) == digits(b)


def _find(model, form):
    obj = model.objects.filter(reference=form.cleaned_data["reference"]).first()
    return obj if obj and _same_phone(obj.phone, form.cleaned_data["phone"]) else None


def _submitted(request, title, body, reference=None, track_url=None):
    request.session["submitted"] = {"title": title, "body": body, "reference": reference, "track_url": track_url}
    return redirect("community:submitted")


def submitted(request):
    data = request.session.pop("submitted", None)
    if not data:
        return redirect("core:home")
    return render(request, "community/submitted.html", data)


@rate_limit("contact", limit=4)
def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        notify_staff(f"Contact: {msg.subject}", f"From {msg.name} <{msg.email}> {msg.phone}\n\n{msg.message}")
        return _submitted(request, "Message sent", "Thank you for reaching out. We reply within two working days.")
    return render(request, "community/contact.html", {"form": form})


@rate_limit("volunteer", limit=3)
def volunteer(request):
    form = VolunteerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        app = form.save()
        notify_staff("New volunteer application", f"{app.full_name} ({app.phone}, {app.email}) — {app.location}\n\n{app.skills}")
        notify_person(app.email, "We received your volunteer application",
                      f"Dear {app.full_name},\n\nThank you for offering to serve with PEFA GraceWorks. "
                      "Our team will call you within a week.\n\nGod bless.")
        return _submitted(request, "Application received", "Thank you for offering your time and skills. We'll call you within a week.")
    return render(request, "community/volunteer.html", {"form": form})


@rate_limit("partner", limit=3)
def partner(request):
    form = PartnershipForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save()
        notify_staff("New partnership inquiry", f"{inquiry.organisation} — {inquiry.contact_person} <{inquiry.email}>\n\n{inquiry.interest}")
        return _submitted(request, "Inquiry received", "Thank you for wanting to partner with us. Our Program Coordinator will be in touch.")
    return render(request, "community/partner.html", {"form": form})


@rate_limit("feedback", limit=4)
def feedback(request):
    form = FeedbackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        fb = form.save()
        notify_staff(f"{fb.get_kind_display()} {fb.reference}", f"Phone {fb.phone}\nAcknowledge by {fb.acknowledge_by:%d %b %H:%M}\n\n{fb.message}")
        notify_person(fb.email, f"We received your feedback ({fb.reference})",
                      f"Your reference is {fb.reference}. We will acknowledge it within 48 hours and resolve it by "
                      f"{fb.resolve_by:%d %B %Y}.")
        return _submitted(request, "Feedback received",
                          f"We will acknowledge it within 48 hours and aim to resolve it by {fb.resolve_by:%d %B %Y}.",
                          fb.reference, reverse("community:feedback_track"))
    return render(request, "community/feedback.html", {"form": form})


@rate_limit("track", limit=10)
def feedback_track(request):
    form = TrackForm(request.POST or None)
    item = None
    if request.method == "POST" and form.is_valid():
        item = _find(Feedback, form)
        if not item:
            messages.error(request, "No feedback matches that reference and phone number. Check both and try again.")
    return render(request, "community/track.html", {"form": form, "item": item, "kind": "feedback"})


@rate_limit("help", limit=3, period=300)
def help_request(request):
    form = HelpRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        hr = form.save()
        notify_staff(f"Help request {hr.reference} ({hr.priority_band} priority)",
                     f"{hr.full_name}, {hr.phone}, {hr.location}\nNeed: {hr.get_need_type_display()} — {hr.get_urgency_display()}\n"
                     f"Score {hr.priority_score}/100\n\n{hr.description}")
        return _submitted(request, "Request received",
                          "A member of our team will review your request and call you. Keep your reference number safe.",
                          hr.reference, reverse("community:help_track"))
    return render(request, "community/help_request.html", {"form": form})


@rate_limit("track", limit=10)
def help_track(request):
    form = TrackForm(request.POST or None)
    item = None
    if request.method == "POST" and form.is_valid():
        item = _find(HelpRequest, form)
        if not item:
            messages.error(request, "No request matches that reference and phone number. Check both and try again.")
    return render(request, "community/track.html", {"form": form, "item": item, "kind": "help"})


@require_POST
@rate_limit("newsletter", limit=5)
def subscribe(request):
    form = NewsletterForm(request.POST)
    ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if form.is_valid() or NewsletterSubscriber.objects.filter(email=request.POST.get("email", "")).exists():
        email = request.POST.get("email", "").strip().lower()
        NewsletterSubscriber.objects.update_or_create(email=email, defaults={"is_active": True})
        text = "You're subscribed. Look out for our next update."
        ok = True
    else:
        text = "Enter a valid email address."
        ok = False
    if ajax:
        return JsonResponse({"ok": ok, "message": text}, status=200 if ok else 400)
    (messages.success if ok else messages.error)(request, text)
    return redirect(request.META.get("HTTP_REFERER") or "core:home")
