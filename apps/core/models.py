from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models

from .storage import video_storage
from .utils import OptimizedImagesMixin

phone_validator = RegexValidator(
    r"^(\+?254|0)[17]\d{8}$", "Enter a Kenyan phone number, e.g. 0712 345 678 or +254712345678."
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, db_index=True, help_text="Lower numbers show first.")

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class SiteSettings(OptimizedImagesMixin, models.Model):
    """One editable record holding the organisation's identity and contact details."""

    org_name = models.CharField(max_length=150, default="PEFA GraceWorks Community Services")
    short_name = models.CharField(max_length=20, default="PGCS")
    tagline = models.CharField(max_length=150, default="Empowered by Faith, Serving with Grace")
    closing_statement = models.CharField(max_length=200, default="Together, we build thriving, holistic communities.")
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    about_short = models.TextField("Short about text (home page)", blank=True)
    about_long = models.TextField("Full about text", blank=True, help_text="Separate paragraphs with a blank line.")
    legal_status = models.TextField(blank=True, help_text="Separate paragraphs with a blank line.")
    church_block_title = models.CharField(max_length=120, default="Rooted in the PEFA Church")
    church_block_text = models.TextField(blank=True)
    church_block_image = models.ImageField(upload_to="site/", blank=True)

    registration_number = models.CharField(max_length=60, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    registered_under = models.CharField(max_length=200, blank=True)
    affiliation = models.CharField(max_length=200, blank=True)

    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True, help_text="Number in international format, e.g. 254728565413")
    email = models.EmailField(blank=True)
    po_box = models.CharField("P.O. Box", max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    physical_location = models.CharField(max_length=255, blank=True)
    map_embed_url = models.URLField(blank=True, max_length=600, help_text="Google Maps → Share → Embed a map → copy the src URL")
    office_hours = models.CharField(max_length=120, blank=True, default="Mon – Fri, 8:00am – 5:00pm")

    facebook = models.URLField(blank=True)
    x_twitter = models.URLField("X / Twitter", blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)

    mpesa_paybill = models.CharField("M-Pesa Paybill / Till", max_length=20, blank=True)
    mpesa_account = models.CharField("M-Pesa account name", max_length=40, blank=True)
    bank_details = models.TextField(blank=True, help_text="Bank name, branch, account name and number.")

    feedback_ack_hours = models.PositiveIntegerField(default=48, help_text="Service charter: acknowledge within N hours")
    feedback_resolve_working_days = models.PositiveIntegerField(default=14, help_text="Service charter: resolve within N working days")

    optimized_image_fields = ("church_block_image",)

    class Meta:
        verbose_name = verbose_name_plural = "Site settings"

    def __str__(self):
        return self.org_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("site_settings")

    @classmethod
    def load(cls):
        obj = cache.get("site_settings")
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set("site_settings", obj, 300)
        return obj

    @property
    def whatsapp_link(self):
        return f"https://wa.me/{self.whatsapp}" if self.whatsapp else ""


class HeroSlide(OptimizedImagesMixin, OrderedModel):
    """Home page slider (replaces WordPress Slider Revolution)."""

    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="slides/", blank=True, help_text="Landscape photo, at least 1600px wide.")
    image_credit = models.CharField(max_length=255, blank=True, help_text="Photographer and licence, if the photo isn't ours.")
    video = models.FileField(
        upload_to="slides/video/", storage=video_storage, blank=True,
        help_text="Optional short, silent MP4 loop played behind the text (the photo shows while it loads).")
    button_text = models.CharField(max_length=40, blank=True)
    button_url = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    optimized_image_fields = ("image",)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title


class CoreValue(OrderedModel):
    title = models.CharField(max_length=80)
    description = models.TextField()
    icon = models.CharField(max_length=40, default="heart", help_text="Bootstrap icon name, e.g. heart, shield-check")

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title


class Person(OptimizedImagesMixin, OrderedModel):
    GROUP_CHOICES = [("board", "Executive Board"), ("management", "Management Team"), ("patron", "Patron / Church leadership")]
    name = models.CharField(max_length=120, blank=True, help_text="Leave blank to show the role only (position vacant / not yet published).")
    role = models.CharField(max_length=120)
    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default="board")
    role_description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="people/", blank=True)
    is_active = models.BooleanField(default=True)

    optimized_image_fields = ("photo",)

    class Meta(OrderedModel.Meta):
        verbose_name_plural = "People (board & team)"

    def __str__(self):
        return f"{self.role}: {self.name or '—'}"


class Partner(OptimizedImagesMixin, OrderedModel):
    CATEGORY_CHOICES = [
        ("faith", "Faith-based"),
        ("government", "Government"),
        ("development", "Development partner / donor"),
        ("community", "Community & private sector"),
    ]
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="partners/", blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    optimized_image_fields = ("logo",)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.name


class Milestone(OrderedModel):
    """Key achievements & institutional milestones."""

    title = models.CharField(max_length=150)
    description = models.TextField()
    date = models.DateField(null=True, blank=True)
    icon = models.CharField(max_length=40, default="check2-circle")
    focus_area = models.ForeignKey("programs.FocusArea", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title


class ImpactStat(OrderedModel):
    """Home page counters. Either typed in manually or calculated live from the database."""

    SOURCE_CHOICES = [
        ("manual", "Manual value"),
        ("learners", "Live: active learners supported (beneficiary registry)"),
        ("beneficiaries", "Live: all beneficiaries"),
        ("households_helped", "Live: help requests assisted"),
        ("volunteers", "Live: approved volunteers"),
        ("events", "Live: events held"),
        ("donors", "Live: completed donations"),
    ]
    label = models.CharField(max_length=80)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default="manual")
    manual_value = models.PositiveIntegerField(default=0)
    minimum_value = models.PositiveIntegerField(default=0, help_text="Live values never show below this (e.g. records not yet digitised).")
    suffix = models.CharField(max_length=10, blank=True, help_text="e.g. + or %")
    is_active = models.BooleanField(default=True)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.label

    @property
    def value(self):
        from .services import live_stat

        if self.source == "manual":
            return self.manual_value
        return max(live_stat(self.source), self.minimum_value)


class FAQ(OrderedModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
