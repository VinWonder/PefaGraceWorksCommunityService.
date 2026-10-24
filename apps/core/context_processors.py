import random

from django.core.cache import cache

from .models import SiteSettings


def site_context(request):
    nav = cache.get("nav_focus_areas")
    if nav is None:
        from apps.programs.models import FocusArea

        nav = list(FocusArea.objects.filter(is_active=True).values("title", "slug", "icon"))
        cache.set("nav_focus_areas", nav, 300)
    # A gallery photo behind every inner page header, rotating between visits.
    header_photos = cache.get("header_photos")
    if header_photos is None:
        from apps.news.models import Photo

        header_photos = [p.image.url for p in Photo.objects.filter(album__is_published=True, order__lt=6).exclude(image="")]
        cache.set("header_photos", header_photos, 300)
    return {
        "site": SiteSettings.load(),
        "nav_focus_areas": nav,
        "header_photo": random.choice(header_photos) if header_photos else "",
    }
