from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Feedback, HelpRequest, add_working_days


class HelpRequestScoringTest(TestCase):
    def make(self, **kw):
        data = dict(full_name="Test Person", phone="0712345678", location="Kolwa", need_type="school_fees",
                    urgency="medium", description="x", household_size=4, children_under_18=2, monthly_income="lt5k",
                    consent=True)
        data.update(kw)
        return HelpRequest.objects.create(**data)

    def test_more_vulnerable_scores_higher(self):
        low = self.make(phone="0711111111", monthly_income="gt20k", urgency="low", household_size=1, children_under_18=0)
        high = self.make(phone="0722222222", monthly_income="none", urgency="critical", is_child_headed=True, has_disability=True)
        self.assertGreater(high.priority_score, low.priority_score)
        self.assertEqual(high.priority_band, "High")
        self.assertTrue(low.reference.startswith("HR-"))

    def test_recently_assisted_moves_down(self):
        first = self.make(phone="0733333333")
        first.status = "assisted"
        first.save()
        again = self.make(phone="0733333333")
        self.assertLess(again.priority_score, first.priority_score)

    def test_public_form_and_tracking(self):
        resp = self.client.post(reverse("community:help_request"), {
            "full_name": "Jane", "phone": "0798765432", "location": "Kolwa", "ward": "Kolwa Central",
            "need_type": "sanitary", "urgency": "high", "description": "Need pads for school",
            "household_size": 5, "children_under_18": 3, "monthly_income": "none", "consent": "on"})
        self.assertRedirects(resp, reverse("community:submitted"))
        hr = HelpRequest.objects.get(full_name="Jane")
        resp = self.client.post(reverse("community:help_track"), {"reference": hr.reference.lower(), "phone": "+254798765432"})
        self.assertContains(resp, hr.reference)

    def test_honeypot_blocks_bots(self):
        self.client.post(reverse("community:help_request"), {
            "full_name": "Bot", "phone": "0798765400", "location": "x", "ward": "x", "need_type": "food",
            "urgency": "low", "description": "x", "household_size": 1, "children_under_18": 0,
            "monthly_income": "none", "consent": "on", "website_url": "http://spam"})
        self.assertFalse(HelpRequest.objects.filter(full_name="Bot").exists())


class FeedbackCharterTest(TestCase):
    def test_deadlines_set(self):
        fb = Feedback.objects.create(phone="0712345678", message="Slow response")
        self.assertIsNotNone(fb.acknowledge_by)
        self.assertIsNotNone(fb.resolve_by)
        self.assertTrue(fb.reference.startswith("FB-"))

    def test_working_days_skip_weekends(self):
        # Friday 7 Nov 2025 + 1 working day = Monday 10 Nov 2025
        self.assertEqual(add_working_days(date(2025, 11, 7), 1), date(2025, 11, 10))
