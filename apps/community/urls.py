from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("contact/", views.contact, name="contact"),
    path("volunteer/", views.volunteer, name="volunteer"),
    path("partner-with-us/", views.partner, name="partner"),
    path("feedback/", views.feedback, name="feedback"),
    path("feedback/track/", views.feedback_track, name="feedback_track"),
    path("request-help/", views.help_request, name="help_request"),
    path("request-help/track/", views.help_track, name="help_track"),
    path("newsletter/subscribe/", views.subscribe, name="subscribe"),
    path("thank-you/", views.submitted, name="submitted"),
]
