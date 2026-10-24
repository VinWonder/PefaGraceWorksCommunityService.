from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.core.models import ImpactStat
from apps.events.models import Event
from apps.news.models import Post
from apps.programs.models import FocusArea, Project

from .serializers import EventSerializer, FocusAreaSerializer, PostSerializer, ProjectSerializer


class FocusAreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FocusArea.objects.filter(is_active=True).prefetch_related("items")
    serializer_class = FocusAreaSerializer
    lookup_field = "slug"


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.select_related("focus_area")
    serializer_class = ProjectSerializer
    lookup_field = "slug"


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.filter(is_published=True)
    serializer_class = EventSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Event.objects.upcoming()  # evaluated per request so "now" is always current


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.filter(status="published")
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Post.objects.published().select_related("category")


@api_view(["GET"])
def impact(request):
    return Response([{"label": s.label, "value": s.value, "suffix": s.suffix} for s in ImpactStat.objects.filter(is_active=True)])
