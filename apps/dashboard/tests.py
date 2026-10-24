from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardTest(TestCase):
    def test_staff_only(self):
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 302)

    def test_staff_can_view_and_export(self):
        user = get_user_model().objects.create_user("staff", password="x-strong-pass-123", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard:stats")).status_code, 200)
        resp = self.client.get(reverse("dashboard:export", args=["donations"]))
        self.assertEqual(resp["Content-Type"], "text/csv; charset=utf-8")
