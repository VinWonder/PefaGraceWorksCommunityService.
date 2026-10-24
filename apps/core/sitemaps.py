from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.events.models import Event
from apps.news.models import Album, Post
from apps.programs.models import FocusArea, Project


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return ["core:home", "core:about", "core:governance", "core:charter", "core:partners", "core:impact",
                "core:get_involved", "programs:list", "programs:projects", "programs:approach", "news:list",
                "news:gallery", "events:list", "donations:donate", "community:contact", "community:volunteer",
                "community:partner", "community:help_request", "community:feedback"]

    def location(self, item):
        return reverse(item)


class ModelSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def __init__(self, queryset):
        self.queryset = queryset

    def items(self):
        return self.queryset

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)


sitemaps = {
    "static": StaticSitemap,
    "focus": ModelSitemap(FocusArea.objects.filter(is_active=True)),
    "projects": ModelSitemap(Project.objects.all()),
    "posts": ModelSitemap(Post.objects.filter(status="published")),
    "albums": ModelSitemap(Album.objects.filter(is_published=True)),
    "events": ModelSitemap(Event.objects.filter(is_published=True)),
}
