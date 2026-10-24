"""Live numbers for counters (cached for 10 minutes so the home page stays fast)."""
from django.core.cache import cache


def live_stat(source):
    key = f"live_stat:{source}"
    value = cache.get(key)
    if value is not None:
        return value

    from apps.community.models import Beneficiary, HelpRequest, VolunteerApplication
    from apps.donations.models import Donation
    from apps.events.models import Event
    from django.utils import timezone

    if source == "learners":
        value = Beneficiary.objects.filter(is_active=True, support_type__in=["bursary", "school_fees", "sanitary"]).count()
    elif source == "beneficiaries":
        value = Beneficiary.objects.count()
    elif source == "households_helped":
        value = HelpRequest.objects.filter(status="assisted").count()
    elif source == "volunteers":
        value = VolunteerApplication.objects.filter(status="approved").count()
    elif source == "events":
        value = Event.objects.filter(is_published=True, start__lt=timezone.now()).count()
    elif source == "donors":
        value = Donation.objects.filter(status="completed").count()
    else:
        value = 0
    cache.set(key, value, 600)
    return value
