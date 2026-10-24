from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("events/", views.event_list, name="list"),
    path("events/calendar/", views.calendar, name="calendar"),
    path("events/feed.json", views.calendar_feed, name="feed"),
    path("events/<slug:slug>/", views.event_detail, name="detail"),
    path("events/<slug:slug>/add-to-calendar.ics", views.event_ics, name="ics"),
]
