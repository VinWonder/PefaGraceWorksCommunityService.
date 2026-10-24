from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("blog/", views.post_list, name="list"),
    path("blog/category/<slug:slug>/", views.post_list, name="category"),
    path("blog/<slug:slug>/", views.post_detail, name="detail"),
    path("gallery/", views.gallery, name="gallery"),
    path("gallery/<slug:slug>/", views.album_detail, name="album"),
]
