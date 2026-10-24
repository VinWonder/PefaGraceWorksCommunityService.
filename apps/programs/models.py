from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.urls import reverse
from tinymce.models import HTMLField

from apps.core.models import OrderedModel, TimeStampedModel
from apps.core.utils import OptimizedImagesMixin


class FocusArea(OptimizedImagesMixin, OrderedModel, TimeStampedModel):
    """The five strategic pillars (Faith & Outreach, Health, WASH, Education, Economic Empowerment)."""

    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=40, default="stars", help_text="Bootstrap icon name")
    summary = models.CharField(max_length=300)
    description = HTMLField(blank=True)
    goal = models.TextField(blank=True)
    image = models.ImageField(upload_to="focus-areas/", blank=True)
    image_credit = models.CharField(max_length=255, blank=True, help_text="Photographer and licence, if the photo isn't ours.")
    is_active = models.BooleanField(default=True)

    optimized_image_fields = ("image",)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("programs:detail", args=[self.slug])

    @property
    def activities(self):
        return self.items.filter(kind="activity")

    @property
    def outcomes(self):
        return self.items.filter(kind="outcome")


class FocusAreaItem(OrderedModel):
    KIND_CHOICES = [("activity", "Key activity"), ("outcome", "Expected outcome")]
    focus_area = models.ForeignKey(FocusArea, related_name="items", on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    text = models.CharField(max_length=300)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.text


class ServiceStandard(models.Model):
    """Service charter row for a focus area."""

    focus_area = models.OneToOneField(FocusArea, related_name="charter", on_delete=models.CASCADE)
    services_offered = models.TextField()
    commitment = models.TextField()
    standard = models.TextField()

    def __str__(self):
        return f"Charter: {self.focus_area}"


class Project(OptimizedImagesMixin, TimeStampedModel):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("fundraising", "Fundraising"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
    ]
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    focus_area = models.ForeignKey(FocusArea, related_name="projects", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned", db_index=True)
    summary = models.CharField(max_length=300)
    description = HTMLField(blank=True)
    target_outcome = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="projects/", blank=True)
    image_credit = models.CharField(max_length=255, blank=True, help_text="Photographer and licence, if the photo isn't ours.")
    funding_goal = models.DecimalField("Funding goal (KES)", max_digits=14, decimal_places=2, default=0)
    offline_amount_raised = models.DecimalField(
        "Raised outside the website (KES)", max_digits=14, decimal_places=2, default=0,
        help_text="Cash, cheques and pledges already received that are not recorded as online donations.")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=150, blank=True)
    is_featured = models.BooleanField(default=False, help_text="Show on the home page")
    order = models.PositiveIntegerField(default=0)

    optimized_image_fields = ("image",)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("programs:project_detail", args=[self.slug])

    @property
    def amount_raised(self):
        online = self.donations.filter(status="completed").aggregate(t=Sum("amount_kes"))["t"] or Decimal("0")
        return online + self.offline_amount_raised

    @property
    def progress_percent(self):
        if not self.funding_goal:
            return 0
        return min(100, int(self.amount_raised / self.funding_goal * 100))


class ProjectUpdate(TimeStampedModel):
    project = models.ForeignKey(Project, related_name="updates", on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    body = models.TextField()
    date = models.DateField()

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title


class ImplementationStage(OrderedModel):
    """Program Implementation Model (needs assessment → … → scale-up)."""

    title = models.CharField(max_length=100)
    description = models.TextField()

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title


class Indicator(OrderedModel):
    """Monitoring, Evaluation & Learning indicator with a baseline and a target."""

    focus_area = models.ForeignKey(FocusArea, related_name="indicators", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="indicators", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=40, default="people")
    baseline = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target = models.DecimalField(max_digits=12, decimal_places=2)
    target_year = models.PositiveIntegerField(default=2028)
    is_cumulative = models.BooleanField(default=True, help_text="Ticked: latest value is the running total. Unticked: values are added together.")
    is_public = models.BooleanField(default=True, help_text="Show on the public Impact page")

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.name

    @property
    def current_value(self):
        measurements = list(self.measurements.all())  # uses prefetch when available
        if not measurements:
            return self.baseline
        if self.is_cumulative:
            return max(measurements, key=lambda m: m.period_end).value
        return sum((m.value for m in measurements), Decimal("0"))

    @property
    def progress_percent(self):
        span = self.target - self.baseline
        if span <= 0:
            return 100
        return max(0, min(100, int((self.current_value - self.baseline) / span * 100)))


class IndicatorMeasurement(TimeStampedModel):
    indicator = models.ForeignKey(Indicator, related_name="measurements", on_delete=models.CASCADE)
    period_end = models.DateField(help_text="Last day of the reporting period")
    value = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=150, blank=True, help_text="e.g. bursary register, attendance sheet")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-period_end"]
        unique_together = [("indicator", "period_end")]

    def __str__(self):
        return f"{self.indicator}: {self.value} ({self.period_end})"
