from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel, phone_validator
from apps.core.utils import make_reference

# Fixed-date Kenyan public holidays (month, day). Movable feasts are not counted.
KENYA_FIXED_HOLIDAYS = {(1, 1), (5, 1), (6, 1), (10, 10), (10, 20), (12, 12), (12, 25), (12, 26)}


def add_working_days(start, days):
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5 and (current.month, current.day) not in KENYA_FIXED_HOLIDAYS:
            added += 1
    return current


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"


class VolunteerApplication(TimeStampedModel):
    STATUS_CHOICES = [("new", "New"), ("contacted", "Contacted"), ("approved", "Approved"), ("declined", "Declined")]
    AVAILABILITY_CHOICES = [("weekdays", "Weekdays"), ("weekends", "Weekends"), ("both", "Weekdays & weekends"),
                            ("events", "Specific events only"), ("remote", "Remote / online")]
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, validators=[phone_validator])
    location = models.CharField(max_length=120)
    profession = models.CharField(max_length=120, blank=True)
    focus_areas = models.ManyToManyField("programs.FocusArea", blank=True, verbose_name="Areas you'd like to serve in")
    skills = models.TextField(help_text="Skills and experience you'd bring")
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    motivation = models.TextField("Why do you want to volunteer?")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="new", db_index=True)
    staff_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name


class PartnershipInquiry(TimeStampedModel):
    TYPE_CHOICES = [("church", "Church / faith-based"), ("government", "Government"), ("ngo", "NGO / CBO"),
                    ("donor", "Donor / foundation"), ("corporate", "Corporate / CSR"), ("school", "School / institution"),
                    ("individual", "Individual sponsor")]
    STATUS_CHOICES = [("new", "New"), ("in_discussion", "In discussion"), ("active", "Active partner"), ("closed", "Closed")]
    organisation = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    partner_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    focus_areas = models.ManyToManyField("programs.FocusArea", blank=True)
    interest = models.TextField("How would you like to partner?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Partnership inquiries"

    def __str__(self):
        return self.organisation


class NewsletterSubscriber(TimeStampedModel):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class Feedback(TimeStampedModel):
    """Service charter feedback & complaints with acknowledgement/resolution deadlines."""

    KIND_CHOICES = [("complaint", "Complaint"), ("suggestion", "Suggestion"), ("compliment", "Compliment"), ("enquiry", "Enquiry")]
    STATUS_CHOICES = [("received", "Received"), ("acknowledged", "Acknowledged"), ("in_progress", "In progress"), ("resolved", "Resolved")]
    reference = models.CharField(max_length=12, unique=True, editable=False)
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default="complaint")
    name = models.CharField(max_length=120, blank=True, help_text="Optional — you may stay anonymous")
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)
    focus_area = models.ForeignKey("programs.FocusArea", null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name="Related service")
    message = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="received", db_index=True)
    response = models.TextField("Response to the person", blank=True, help_text="Shown on the public tracking page")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    acknowledge_by = models.DateTimeField(editable=False, null=True)
    resolve_by = models.DateField(editable=False, null=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Feedback & complaints"

    def __str__(self):
        return f"{self.reference} ({self.get_kind_display()})"

    def save(self, *args, **kwargs):
        from apps.core.models import SiteSettings

        if not self.reference:
            self.reference = make_reference("FB")
        now = timezone.now()
        if not self.acknowledge_by:
            s = SiteSettings.load()
            self.acknowledge_by = now + timedelta(hours=s.feedback_ack_hours)
            self.resolve_by = add_working_days(timezone.localdate(), s.feedback_resolve_working_days)
        if self.status != "received" and not self.acknowledged_at:
            self.acknowledged_at = now
        if self.status == "resolved" and not self.resolved_at:
            self.resolved_at = now
        super().save(*args, **kwargs)

    @property
    def ack_overdue(self):
        return self.acknowledged_at is None and self.acknowledge_by and timezone.now() > self.acknowledge_by

    @property
    def resolution_overdue(self):
        return self.resolved_at is None and self.resolve_by and timezone.localdate() > self.resolve_by

    @property
    def met_charter(self):
        if not self.resolved_at:
            return None
        ack_ok = self.acknowledged_at and self.acknowledged_at <= self.acknowledge_by
        return bool(ack_ok and timezone.localdate(self.resolved_at) <= self.resolve_by)


class HelpRequest(TimeStampedModel):
    """A household asking for support. Scored automatically so the most vulnerable are seen first."""

    NEED_CHOICES = [
        ("school_fees", "School fees / bursary"),
        ("sanitary", "Sanitary towels"),
        ("food", "Food support"),
        ("medical", "Medical support"),
        ("water", "Clean water / sanitation"),
        ("skills", "Skills training / start-up support"),
        ("counseling", "Counselling / spiritual support"),
        ("other", "Other"),
    ]
    URGENCY_CHOICES = [("low", "Can wait a few weeks"), ("medium", "Needed this month"),
                       ("high", "Needed this week"), ("critical", "Emergency — needed now")]
    INCOME_CHOICES = [("none", "No regular income"), ("lt5k", "Below KES 5,000 a month"),
                      ("5to10k", "KES 5,000 – 10,000"), ("10to20k", "KES 10,000 – 20,000"), ("gt20k", "Above KES 20,000")]
    STATUS_CHOICES = [("new", "New"), ("under_review", "Under review"), ("approved", "Approved"),
                      ("assisted", "Assisted"), ("referred", "Referred to partner"), ("declined", "Not eligible")]

    reference = models.CharField(max_length=12, unique=True, editable=False)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, validators=[phone_validator], db_index=True)
    location = models.CharField("Village / estate", max_length=120)
    ward = models.CharField(max_length=80, default="Kolwa Central")
    need_type = models.CharField(max_length=20, choices=NEED_CHOICES, db_index=True)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="medium")
    description = models.TextField("Tell us about your situation")
    household_size = models.PositiveSmallIntegerField(default=1)
    children_under_18 = models.PositiveSmallIntegerField(default=0)
    monthly_income = models.CharField(max_length=10, choices=INCOME_CHOICES)
    is_single_parent = models.BooleanField("Single parent / guardian", default=False)
    has_disability = models.BooleanField("Someone in the household lives with a disability", default=False)
    is_elderly_headed = models.BooleanField("Household head is 60 or older", default=False)
    is_child_headed = models.BooleanField("Household is headed by a child (under 18)", default=False)
    referred_by = models.CharField(max_length=120, blank=True, help_text="Pastor, chief, teacher, CHV…")
    consent = models.BooleanField(default=False)

    priority_score = models.PositiveSmallIntegerField(default=0, db_index=True, editable=False)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="new", db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    staff_notes = models.TextField(blank=True)
    public_update = models.CharField(max_length=255, blank=True, help_text="Short update shown when the person tracks their request")
    assisted_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-priority_score", "created_at"]

    def __str__(self):
        return f"{self.reference} · {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = make_reference("HR")
        self.priority_score = self.compute_priority()
        if self.status == "assisted" and not self.assisted_on:
            self.assisted_on = timezone.localdate()
        super().save(*args, **kwargs)

    def compute_priority(self):
        """Transparent 0–100 vulnerability score. Adjust the weights here to match your policy."""
        score = 0
        score += {"none": 25, "lt5k": 18, "5to10k": 10, "10to20k": 4, "gt20k": 0}.get(self.monthly_income, 0)
        score += {"low": 0, "medium": 5, "high": 12, "critical": 20}.get(self.urgency, 0)
        score += min(self.household_size or 0, 10)
        score += min((self.children_under_18 or 0) * 2, 10)
        score += 8 if self.is_single_parent else 0
        score += 10 if self.has_disability else 0
        score += 7 if self.is_elderly_headed else 0
        score += 15 if self.is_child_headed else 0
        # Spread help fairly: households assisted in the last 6 months drop in the queue.
        recent = HelpRequest.objects.filter(phone=self.phone, status="assisted",
                                            assisted_on__gte=date.today() - timedelta(days=182))
        if self.pk:
            recent = recent.exclude(pk=self.pk)
        if recent.exists():
            score -= 15
        return max(0, min(100, score))

    @property
    def priority_band(self):
        if self.priority_score >= 60:
            return "High"
        if self.priority_score >= 35:
            return "Medium"
        return "Low"


class Beneficiary(TimeStampedModel):
    """Registry of everyone PGCS supports — the source for impact numbers and donor reports."""

    GENDER_CHOICES = [("female", "Female"), ("male", "Male"), ("other", "Prefer not to say")]
    LEVEL_CHOICES = [("na", "Not a learner"), ("ecde", "ECDE"), ("primary", "Primary / Junior School"),
                     ("secondary", "Secondary / Senior School"), ("tertiary", "College / University"), ("tvet", "TVET")]
    SUPPORT_CHOICES = [
        ("bursary", "Bursary"), ("school_fees", "School fees"), ("sanitary", "Sanitary towels"),
        ("uniform", "Uniform / learning materials"), ("medical", "Medical support"), ("food", "Food support"),
        ("water", "Water / sanitation"), ("skills", "Skills training"), ("startup", "Start-up kit / tools"),
        ("counseling", "Counselling / mentorship"), ("other", "Other"),
    ]
    full_name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    year_of_birth = models.PositiveSmallIntegerField(null=True, blank=True)
    phone = models.CharField("Phone (self or guardian)", max_length=20, blank=True)
    guardian_name = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120)
    ward = models.CharField(max_length=80, default="Kolwa Central")
    focus_area = models.ForeignKey("programs.FocusArea", related_name="beneficiaries", on_delete=models.PROTECT)
    project = models.ForeignKey("programs.Project", related_name="beneficiaries", null=True, blank=True, on_delete=models.SET_NULL)
    support_type = models.CharField(max_length=15, choices=SUPPORT_CHOICES, db_index=True)
    school = models.CharField(max_length=150, blank=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="na")
    amount_supported = models.DecimalField("Value of support (KES)", max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)
    has_disability = models.BooleanField(default=False)
    help_request = models.ForeignKey(HelpRequest, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name_plural = "Beneficiaries"

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        return timezone.localdate().year - self.year_of_birth if self.year_of_birth else None
