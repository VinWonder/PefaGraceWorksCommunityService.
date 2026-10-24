from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    path("donate/", views.donate, name="donate"),
    path("donate/mpesa/callback/", views.mpesa_callback, name="mpesa_callback"),
    path("donate/<str:reference>/", views.status, name="status"),
    path("donate/<str:reference>/check/", views.status_json, name="status_json"),
    path("donate/<str:reference>/pay/", views.pay, name="pay"),
    path("donate/<str:reference>/paypal/order/", views.paypal_create, name="paypal_create"),
    path("donate/<str:reference>/paypal/capture/", views.paypal_capture, name="paypal_capture"),
]
