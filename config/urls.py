from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core.sitemaps import sitemaps
from apps.core.views import robots_txt

admin.site.site_header = "PEFA GraceWorks — Site Management"
admin.site.site_title = "PGCS Admin"
admin.site.index_title = "Manage website content and community data"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("api/v1/", include("apps.api.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("", include("apps.programs.urls")),
    path("", include("apps.news.urls")),
    path("", include("apps.events.urls")),
    path("", include("apps.donations.urls")),
    path("", include("apps.community.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
