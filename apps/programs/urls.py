from django.urls import path

from . import views

app_name = "programs"

urlpatterns = [
    path("focus-areas/", views.focus_area_list, name="list"),
    path("focus-areas/<slug:slug>/", views.focus_area_detail, name="detail"),
    path("projects/", views.project_list, name="projects"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("how-we-work/", views.approach, name="approach"),
]
