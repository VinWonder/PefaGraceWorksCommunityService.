from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("focus-areas", views.FocusAreaViewSet)
router.register("projects", views.ProjectViewSet)
router.register("events", views.EventViewSet)
router.register("posts", views.PostViewSet)

urlpatterns = [
    path("impact/", views.impact, name="api-impact"),
    path("", include(router.urls)),
]
