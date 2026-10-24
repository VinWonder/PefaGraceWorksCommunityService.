from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.core.utils import make_reference


class Donation(TimeStampedModel):
    METHOD_CHOICES = [
        ("mpesa", "M-Pesa (STK push)"),
        ("paypal", "PayPal"),
        ("card", "Debit / credit card"),
        ("bank", "Bank transfer"),
        ("cash", "Cash / cheque (recorded by staff)"),
        ("in_kind", "In-kind gift"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    FREQUENCY_CHOICES = [("once", "One-off"), ("monthly", "Monthly pledge")]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    donor_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField("Amount", max_digits=12, decimal_places=2, help_text="In the donation's currency.")
    currency = models.CharField(max_length=3, default="KES")
    amount_kes = models.DecimalField(
        "Amount in KES", max_digits=14, decimal_places=2, default=0,
        help_text="Shilling value used for project totals. Card and PayPal gifts are converted at PAYPAL_KES_PER_USD.")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default="mpesa", db_index=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default="once")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending", db_index=True)
    project = models.ForeignKey("programs.Project", related_name="donations", null=True, blank=True, on_delete=models.SET_NULL)
    focus_area = models.ForeignKey("programs.FocusArea", related_name="donations", null=True, blank=True, on_delete=models.SET_NULL)
    in_kind_description = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    is_anonymous = models.BooleanField("Hide my name publicly", default=False)

    # M-Pesa tracking
    merchant_request_id = models.CharField(max_length=60, blank=True)
    checkout_request_id = models.CharField(max_length=60, blank=True, db_index=True)
    mpesa_receipt = models.CharField(max_length=30, blank=True, db_index=True)
    result_description = models.CharField(max_length=255, blank=True)
    raw_callback = models.JSONField(null=True, blank=True)

    # PayPal / card tracking
    paypal_order_id = models.CharField(max_length=40, blank=True, db_index=True)
    paypal_capture_id = models.CharField(max_length=40, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    receipt_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "completed_at"])]

    def __str__(self):
        return f"{self.reference} · {self.currency} {self.amount:,.0f} · {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = make_reference("DN")
        if self.currency == "KES":
            self.amount_kes = self.amount or 0
        elif not self.amount_kes and self.amount:  # keep a rate staff corrected by hand
            self.amount_kes = (Decimal(self.amount) * Decimal(str(settings.PAYPAL_KES_PER_USD))).quantize(Decimal("0.01"))
        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("donations:status", args=[self.reference])

    @property
    def public_name(self):
        return "Anonymous friend" if self.is_anonymous else self.donor_name.split(" ")[0]

    @property
    def designation(self):
        return self.project or self.focus_area or "Where most needed"

    @property
    def is_online_card(self):
        return self.method in ("paypal", "card")

    @property
    def receipt_number(self):
        return self.mpesa_receipt or self.paypal_capture_id
