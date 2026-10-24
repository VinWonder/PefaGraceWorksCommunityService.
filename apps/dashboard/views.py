from datetime import date, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.community.models import Beneficiary, Feedback, HelpRequest, NewsletterSubscriber, VolunteerApplication
from apps.core.utils import queryset_to_csv
from apps.donations.models import Donation
from apps.events.models import EventRegistration

from .services import build_stats

EXPORTS = {
    "donations": (Donation, ["reference", "created_at", "completed_at", "donor_name", "phone", "email", "amount", "method",
                             "status", "project", "focus_area", "mpesa_receipt"]),
    "beneficiaries": (Beneficiary, None),
    "help-requests": (HelpRequest, None),
    "feedback": (Feedback, None),
    "volunteers": (VolunteerApplication, None),
    "subscribers": (NewsletterSubscriber, None),
    "event-registrations": (EventRegistration, None),
}


def _range(request):
    today = timezone.localdate()
    try:
        date_to = date.fromisoformat(request.GET.get("to", ""))
    except ValueError:
        date_to = today
    try:
        date_from = date.fromisoformat(request.GET.get("from", ""))
    except ValueError:
        date_from = (date_to - timedelta(days=365)).replace(day=1)
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    return date_from, date_to


@staff_member_required
def index(request):
    date_from, date_to = _range(request)
    stats = build_stats(date_from, date_to)
    return render(request, "dashboard/index.html", {
        "stats": stats, "date_from": date_from, "date_to": date_to, "exports": EXPORTS.keys(),
        "urgent_requests": HelpRequest.objects.filter(status__in=["new", "under_review"]).order_by("-priority_score")[:8],
        "overdue_feedback": [f for f in Feedback.objects.exclude(status="resolved") if f.ack_overdue or f.resolution_overdue][:8],
        "recent_donations": Donation.objects.filter(status="completed").order_by("-completed_at")[:8],
    })


@staff_member_required
def stats_json(request):
    date_from, date_to = _range(request)
    return JsonResponse(build_stats(date_from, date_to))


@staff_member_required
def export(request, name):
    if name not in EXPORTS:
        raise Http404
    model, fields = EXPORTS[name]
    return queryset_to_csv(model.objects.all(), name, fields)
