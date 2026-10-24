from django.shortcuts import get_object_or_404, render

from apps.news.models import Photo, Video

from .models import FocusArea, ImplementationStage, Indicator, Project


def focus_area_list(request):
    return render(request, "programs/list.html", {"focus_areas": FocusArea.objects.filter(is_active=True)})


def focus_area_detail(request, slug):
    area = get_object_or_404(FocusArea.objects.prefetch_related("items"), slug=slug, is_active=True)
    return render(request, "programs/detail.html", {
        "area": area,
        "projects": area.projects.all(),
        "posts": area.posts.filter(status="published")[:3],
        "indicators": area.indicators.filter(is_public=True).prefetch_related("measurements"),
        "others": FocusArea.objects.filter(is_active=True).exclude(pk=area.pk),
        "field_photos": Photo.objects.filter(album__focus_area=area, album__is_published=True)[:16],
        "field_videos": Video.objects.filter(album__focus_area=area).exclude(file="")[:6],
    })


def project_list(request):
    status = request.GET.get("status", "")
    projects = Project.objects.select_related("focus_area")
    if status in dict(Project.STATUS_CHOICES):
        projects = projects.filter(status=status)
    return render(request, "programs/projects.html", {
        "projects": projects, "status": status, "status_choices": Project.STATUS_CHOICES,
    })


def project_detail(request, slug):
    project = get_object_or_404(Project.objects.select_related("focus_area"), slug=slug)
    return render(request, "programs/project_detail.html", {
        "project": project,
        "updates": project.updates.all(),
        "recent_donations": project.donations.filter(status="completed").order_by("-completed_at")[:6],
    })


def approach(request):
    return render(request, "programs/approach.html", {
        "stages": ImplementationStage.objects.all(),
        "indicators": Indicator.objects.filter(is_public=True).select_related("focus_area").prefetch_related("measurements"),
        "photos": _field_photos(),
    })


def _field_photos(limit=8):
    """Strong photos (the first few of each album) for decorating overview pages."""
    return list(Photo.objects.filter(album__is_published=True, order__lt=3).select_related("album").order_by("order", "album_id")[:limit])
