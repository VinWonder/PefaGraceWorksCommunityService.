from django.db import models
from django.urls import reverse
from django.utils import timezone
from tinymce.models import HTMLField

from apps.core.models import TimeStampedModel, phone_validator
from apps.core.utils import OptimizedImagesMixin


class EventQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(is_published=True, end__gte=timezone.now()).order_by("start")

    def past(self):
        return self.filter(is_published=True, end__lt=timezone.now()).order_by("-start")


class Event(OptimizedImagesMixin, TimeStampedModel):
    KIND_CHOICES = [
        ("outreach", "Outreach / mission"),
        ("medical_camp", "Medical camp"),
        ("training", "Training / workshop"),
        ("forum", "Community forum"),
        ("fundraiser", "Fundraiser"),
        ("fellowship", "Fellowship / prayer"),
        ("other", "Other"),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="other")
    focus_area = models.ForeignKey("programs.FocusArea", related_name="events", null=True, blank=True, on_delete=models.SET_NULL)
    summary = models.CharField(max_length=300, blank=True)
    description = HTMLField(blank=True)
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField()
    venue = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="events/", blank=True)
    registration_open = models.BooleanField(default=False)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    is_published = models.BooleanField(default=True)

    objects = EventQuerySet.as_manager()
    optimized_image_fields = ("image",)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.slug])

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start and self.end and self.end < self.start:
            raise ValidationError({"end": "The event must end after it starts."})

    @property
    def cover_url(self):
        """The event's own photo, else its focus area's, so cards are never blank."""
        if self.image:
            return self.image.url
        if self.focus_area_id and self.focus_area.image:
            return self.focus_area.image.url
        return ""

    @property
    def is_upcoming(self):
        return self.end >= timezone.now()

    @property
    def spots_left(self):
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.registrations.count())

    @property
    def fill_percent(self):
        if not self.capacity:
            return 0
        return min(100, int((self.capacity - self.spots_left) / self.capacity * 100))

    @property
    def can_register(self):
        return self.registration_open and self.is_upcoming and (self.spots_left is None or self.spots_left > 0)


class EventRegistration(TimeStampedModel):
    event = models.ForeignKey(Event, related_name="registrations", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)
    attendees = models.PositiveSmallIntegerField(default=1)
    attended = models.BooleanField(default=False)

    class Meta:
        unique_together = [("event", "phone")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} → {self.event}"
