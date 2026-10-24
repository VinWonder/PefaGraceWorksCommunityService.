from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.programs.models import FocusArea, Project


class PublicPagesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_pgcs", "--demo", verbosity=0)

    def test_seed_loaded_profile(self):
        self.assertEqual(FocusArea.objects.count(), 5)
        self.assertTrue(Project.objects.filter(slug="community-health-clinic").exists())

    def test_pages_render(self):
        names = ["core:home", "core:about", "core:governance", "core:charter", "core:partners", "core:impact",
                 "core:get_involved", "core:privacy", "programs:list", "programs:projects", "programs:approach",
                 "news:list", "news:gallery", "events:list", "events:calendar", "donations:donate",
                 "community:contact", "community:volunteer", "community:partner", "community:feedback",
                 "community:feedback_track", "community:help_request", "community:help_track"]
        for name in names:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_detail_pages(self):
        for area in FocusArea.objects.all():
            self.assertEqual(self.client.get(area.get_absolute_url()).status_code, 200)
        for project in Project.objects.all():
            self.assertEqual(self.client.get(project.get_absolute_url()).status_code, 200)

    def test_search_and_seo(self):
        self.assertContains(self.client.get(reverse("core:search"), {"q": "clinic"}), "Community Health Clinic")
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
        self.assertContains(self.client.get("/robots.txt"), "Sitemap")
        self.assertEqual(self.client.get(reverse("events:feed")).status_code, 200)
        self.assertEqual(self.client.get("/api/v1/focus-areas/").status_code, 200)

    def test_404(self):
        self.assertEqual(self.client.get("/no-such-page/").status_code, 404)
