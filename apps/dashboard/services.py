"""All dashboard numbers in one place. Every query runs in PostgreSQL (aggregations), not in Python loops."""
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.community.models import Beneficiary, Feedback, HelpRequest, VolunteerApplication
from apps.donations.models import Donation
from apps.events.models import Event, EventRegistration
from apps.programs.models import Indicator


def _months(start, end):
    months, cur = [], start.replace(day=1)
    while cur <= end:
        months.append(cur)
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return months


def build_stats(date_from, date_to):
    rng = Q(created_at__date__gte=date_from, created_at__date__lte=date_to)
    done = Donation.objects.filter(status="completed", completed_at__date__gte=date_from, completed_at__date__lte=date_to)

    # Donations by month (zero-filled)
    per_month = {r["m"].date(): float(r["t"] or 0) for r in done.annotate(m=TruncMonth("completed_at")).values("m").annotate(t=Sum("amount"))}
    months = _months(date_from, date_to)
    donations_monthly = {"labels": [m.strftime("%b %Y") for m in months], "values": [per_month.get(m, 0) for m in months]}

    by_method = list(done.values("method").annotate(total=Sum("amount"), n=Count("id")).order_by("-total"))
    method_labels = dict(Donation.METHOD_CHOICES)

    hr = HelpRequest.objects.filter(rng)
    hr_status = dict(HelpRequest.STATUS_CHOICES)
    hr_need = dict(HelpRequest.NEED_CHOICES)

    ben = Beneficiary.objects.all()
    fb = Feedback.objects.filter(rng)
    resolved = list(fb.filter(status="resolved"))
    met = sum(1 for f in resolved if f.met_charter)

    return {
        "kpis": {
            "donations_total": float(done.aggregate(t=Sum("amount"))["t"] or 0),
            "donations_count": done.count(),
            "pending_mpesa": Donation.objects.filter(status="pending", method="mpesa").count(),
            "help_requests": hr.count(),
            "help_open": HelpRequest.objects.filter(status__in=["new", "under_review"]).count(),
            "help_high_priority_open": HelpRequest.objects.filter(status__in=["new", "under_review"], priority_score__gte=60).count(),
            "beneficiaries_active": ben.filter(is_active=True).count(),
            "learners_active": ben.filter(is_active=True).exclude(level="na").count(),
            "girls_supported": ben.filter(is_active=True, gender="female").exclude(level="na").count(),
            "support_value": float(ben.filter(start_date__gte=date_from, start_date__lte=date_to).aggregate(t=Sum("amount_supported"))["t"] or 0),
            "volunteers_new": VolunteerApplication.objects.filter(rng, status="new").count(),
            "volunteers_approved": VolunteerApplication.objects.filter(status="approved").count(),
            "events_held": Event.objects.filter(start__date__gte=date_from, start__date__lte=date_to, start__lte=timezone.now()).count(),
            "event_attendance": EventRegistration.objects.filter(event__start__date__gte=date_from, event__start__date__lte=date_to, attended=True).aggregate(t=Sum("attendees"))["t"] or 0,
            "feedback_open": Feedback.objects.exclude(status="resolved").count(),
            "feedback_overdue": sum(1 for f in Feedback.objects.exclude(status="resolved") if f.ack_overdue or f.resolution_overdue),
            "charter_compliance": round(met / len(resolved) * 100) if resolved else None,
        },
        "donations_monthly": donations_monthly,
        "donations_by_method": {"labels": [method_labels.get(r["method"], r["method"]) for r in by_method],
                                "values": [float(r["total"]) for r in by_method]},
        "help_by_status": {"labels": [hr_status[k] for k, _ in HelpRequest.STATUS_CHOICES],
                           "values": [hr.filter(status=k).count() for k, _ in HelpRequest.STATUS_CHOICES]},
        "help_by_need": _pairs(hr.values("need_type").annotate(n=Count("id")).order_by("-n"), "need_type", hr_need),
        "beneficiaries_by_area": _pairs(ben.filter(is_active=True).values("focus_area__title").annotate(n=Count("id")).order_by("-n"), "focus_area__title"),
        "beneficiaries_by_gender": _pairs(ben.filter(is_active=True).values("gender").annotate(n=Count("id")), "gender", dict(Beneficiary.GENDER_CHOICES)),
        "beneficiaries_by_level": _pairs(ben.filter(is_active=True).exclude(level="na").values("level").annotate(n=Count("id")), "level", dict(Beneficiary.LEVEL_CHOICES)),
        "indicators": [{"name": i.name, "area": i.focus_area.title, "current": float(i.current_value), "target": float(i.target),
                        "unit": i.unit, "progress": i.progress_percent, "year": i.target_year}
                       for i in Indicator.objects.select_related("focus_area").prefetch_related("measurements")],
    }


def _pairs(rows, key, labels=None):
    labels = labels or {}
    return {"labels": [labels.get(r[key], r[key] or "—") for r in rows], "values": [r["n"] for r in rows]}
