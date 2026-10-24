from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("stats.json", views.stats_json, name="stats"),
    path("export/<slug:name>.csv", views.export, name="export"),
]
