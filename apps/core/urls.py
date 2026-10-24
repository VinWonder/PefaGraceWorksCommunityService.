from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("governance/", views.governance, name="governance"),
    path("service-charter/", views.service_charter, name="charter"),
    path("partners/", views.partners, name="partners"),
    path("impact/", views.impact, name="impact"),
    path("get-involved/", views.get_involved, name="get_involved"),
    path("privacy/", views.privacy, name="privacy"),
    path("search/", views.search, name="search"),
]
