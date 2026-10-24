"""Clear cached numbers / menus whenever the underlying data changes."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save

LIVE_KEYS = ["learners", "beneficiaries", "households_helped", "volunteers", "events", "donors"]


def _clear_stats(**kwargs):
    cache.delete_many([f"live_stat:{k}" for k in LIVE_KEYS] + ["dashboard_stats"])


def _clear_nav(**kwargs):
    cache.delete("nav_focus_areas")


def connect():
    from apps.community.models import Beneficiary, HelpRequest, VolunteerApplication
    from apps.donations.models import Donation
    from apps.events.models import Event
    from apps.programs.models import FocusArea

    for model in (Beneficiary, HelpRequest, VolunteerApplication, Donation, Event):
        post_save.connect(_clear_stats, sender=model, dispatch_uid=f"stats-save-{model.__name__}")
        post_delete.connect(_clear_stats, sender=model, dispatch_uid=f"stats-del-{model.__name__}")
    post_save.connect(_clear_nav, sender=FocusArea, dispatch_uid="nav-save")
    post_delete.connect(_clear_nav, sender=FocusArea, dispatch_uid="nav-del")


connect()
