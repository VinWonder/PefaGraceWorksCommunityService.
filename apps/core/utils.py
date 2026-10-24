"""Shared helpers: image optimisation, reference codes, rate limiting, CSV export, notifications."""
import csv
import logging
import secrets
from functools import wraps
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Images: shrink big phone photos on upload so pages stay fast on mobile data
# --------------------------------------------------------------------------
def optimize_image(field_file, max_size=(1920, 1920), quality=82):
    """Resize + recompress a freshly uploaded ImageField file in place."""
    if not field_file or getattr(field_file, "_committed", True):
        return  # nothing new uploaded
    try:
        from PIL import Image, ImageOps

        img = Image.open(field_file)
        img = ImageOps.exif_transpose(img)
        img.thumbnail(max_size, Image.LANCZOS)
        buffer = BytesIO()
        stem = Path(field_file.name).stem
        if img.mode in ("RGBA", "LA", "P"):
            img.save(buffer, format="PNG", optimize=True)
            name = f"{stem}.png"
        else:
            img = img.convert("RGB")
            img.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
            name = f"{stem}.jpg"
        field_file.save(name, ContentFile(buffer.getvalue()), save=False)
    except Exception:  # never block a save because of an image problem
        logger.exception("Image optimisation failed for %s", field_file)


class OptimizedImagesMixin:
    """Add to a model and list its image fields in `optimized_image_fields`."""

    optimized_image_fields: tuple = ()

    def save(self, *args, **kwargs):
        for name in self.optimized_image_fields:
            optimize_image(getattr(self, name))
        super().save(*args, **kwargs)


# --------------------------------------------------------------------------
# Human-friendly reference codes, e.g. FB-7K2M9Q
# --------------------------------------------------------------------------
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I confusion


def make_reference(prefix, length=6):
    return f"{prefix}-" + "".join(secrets.choice(ALPHABET) for _ in range(length))


# --------------------------------------------------------------------------
# Simple per-IP rate limit for public forms (spam protection)
# --------------------------------------------------------------------------
def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")


def rate_limit(key, limit=5, period=60):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method == "POST":
                cache_key = f"rl:{key}:{client_ip(request)}"
                count = cache.get(cache_key, 0)
                if count >= limit:
                    messages.error(request, "Too many submissions from your connection. Wait a minute and try again.")
                    return redirect(request.path)
                cache.set(cache_key, count + 1, period)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


# --------------------------------------------------------------------------
# CSV export (used by admin actions and the dashboard)
# --------------------------------------------------------------------------
def queryset_to_csv(queryset, filename, fields=None):
    model = queryset.model
    fields = fields or [f.name for f in model._meta.fields]
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M")
    response["Content-Disposition"] = f'attachment; filename="{filename}-{stamp}.csv"'
    response.write("\ufeff")  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(response)
    writer.writerow([model._meta.get_field(f).verbose_name.title() for f in fields])
    for obj in queryset.iterator():
        row = []
        for f in fields:
            value = getattr(obj, f)
            display = getattr(obj, f"get_{f}_display", None)
            row.append(display() if callable(display) else ("" if value is None else value))
        writer.writerow(row)
    return response


def export_as_csv_action(description="Export selected to CSV"):
    def action(modeladmin, request, queryset):
        return queryset_to_csv(queryset, modeladmin.model._meta.model_name)

    action.short_description = description
    return action


# --------------------------------------------------------------------------
# Email notifications
# --------------------------------------------------------------------------
def notify_staff(subject, body):
    recipients = list(settings.STAFF_NOTIFICATION_EMAILS)
    if not recipients:
        from apps.core.models import SiteSettings

        site_email = SiteSettings.load().email
        if site_email:
            recipients = [site_email]
    if recipients:
        send_mail(f"[PGCS website] {subject}", body, None, recipients, fail_silently=True)


def notify_person(email, subject, body):
    if email:
        send_mail(subject, body, None, [email], fail_silently=True)
