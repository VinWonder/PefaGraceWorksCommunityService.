from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

from apps.events.models import Event
from apps.news.models import Album, Photo, Post, Video
from apps.programs.models import FocusArea, Project, ServiceStandard

from .models import FAQ, CoreValue, HeroSlide, ImpactStat, Milestone, Partner, Person


def home(request):
    photos = list(Photo.objects.filter(album__is_published=True).select_related("album").order_by("album__id", "order"))
    # The first few of every album make the coverflow; everything feeds the scrolling ribbon.
    showcase = [p for p in photos if p.order < 4]
    mixed = sorted(photos, key=lambda p: (p.order, p.album_id))  # round-robin across albums
    ribbon = [mixed[0::2][:12], mixed[1::2][:12]] if len(mixed) > 1 else []
    context = {
        "slides": HeroSlide.objects.filter(is_active=True),
        "focus_areas": FocusArea.objects.filter(is_active=True),
        "featured_project": Project.objects.filter(is_featured=True).select_related("focus_area").first(),
        "stats": [s for s in ImpactStat.objects.filter(is_active=True)],
        "events": Event.objects.upcoming()[:3],
        "posts": Post.objects.published().select_related("category")[:3],
        "partners": Partner.objects.filter(is_active=True).exclude(logo=""),
        "partner_names": Partner.objects.filter(is_active=True)[:8],
        "albums": Album.objects.filter(is_published=True).order_by("-date", "id"),
        "videos": Video.objects.filter(is_featured=True).exclude(file="", youtube_id="")[:8],
        "showcase": showcase,
        "ribbon": ribbon,
        "impact_photo": showcase[3] if len(showcase) > 3 else None,
        "quote_photo": showcase[1] if len(showcase) > 1 else None,
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html", {
        "values": CoreValue.objects.all(),
        "milestones": Milestone.objects.all()[:4],
    })


def governance(request):
    return render(request, "core/governance.html", {
        "board": Person.objects.filter(group="board", is_active=True),
        "management": Person.objects.filter(group="management", is_active=True),
    })


def service_charter(request):
    return render(request, "core/charter.html", {
        "standards": ServiceStandard.objects.select_related("focus_area").order_by("focus_area__order"),
    })


def _field_photos(limit=8):
    from apps.programs.views import _field_photos as photos

    return photos(limit)


def partners(request):
    groups = []
    qs = Partner.objects.filter(is_active=True)
    for key, label in Partner.CATEGORY_CHOICES:
        items = [p for p in qs if p.category == key]
        if items:
            groups.append((label, items))
    return render(request, "core/partners.html", {
        "groups": groups, "count": qs.count(), "photos": _field_photos(4),
        "projects": Project.objects.exclude(status="completed").select_related("focus_area")[:6],
    })


def impact(request):
    from apps.programs.models import Indicator

    return render(request, "core/impact.html", {
        "stats": ImpactStat.objects.filter(is_active=True),
        "milestones": Milestone.objects.select_related("focus_area"),
        "indicators": Indicator.objects.filter(is_public=True).select_related("focus_area").prefetch_related("measurements"),
        "photos": _field_photos(10),
        "albums": Album.objects.filter(is_published=True).order_by("-date", "id"),
    })


def get_involved(request):
    return render(request, "core/get_involved.html", {"faqs": FAQ.objects.filter(is_active=True)})


def privacy(request):
    return render(request, "core/privacy.html")


def search(request):
    q = (request.GET.get("q") or "").strip()[:100]
    results = {}
    if len(q) >= 2:
        results = {
            "Focus areas": FocusArea.objects.filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(description__icontains=q)),
            "Projects": Project.objects.filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(description__icontains=q)),
            "Stories": Post.objects.published().filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q)),
            "Events": Event.objects.filter(is_published=True).filter(Q(title__icontains=q) | Q(description__icontains=q)),
        }
    total = sum(r.count() for r in results.values()) if results else 0
    return render(request, "core/search.html", {"q": q, "results": results, "total": total})


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /request-help/track/",
        "Disallow: /feedback/track/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
