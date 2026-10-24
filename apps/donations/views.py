import json
import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.utils import notify_person, notify_staff, rate_limit
from apps.programs.models import Project

from . import mpesa, paypal
from .forms import CARD_METHODS, IMPACT_KES, IMPACT_USD, PRESET_AMOUNTS, DonationForm
from .models import Donation

logger = logging.getLogger(__name__)


@rate_limit("donate", limit=6)
def donate(request):
    initial = {"method": "mpesa", "frequency": "once"}
    project_slug = request.GET.get("project")
    if project_slug:
        initial["project"] = Project.objects.filter(slug=project_slug).first()
    if request.GET.get("amount", "").isdigit():
        initial["amount"] = int(request.GET["amount"])

    if request.GET.get("method") in dict(Donation.METHOD_CHOICES):
        initial["method"] = request.GET["method"]

    form = DonationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        donation = form.save(commit=False)
        if donation.method in CARD_METHODS:
            donation.currency = settings.PAYPAL["CURRENCY"]
            donation.save()
            return redirect("donations:pay", donation.reference)
        if donation.method == "mpesa":
            try:
                donation.phone = mpesa.normalize_phone(donation.phone)
            except mpesa.MpesaError as exc:
                form.add_error("phone", str(exc))
                return render(request, "donations/donate.html", _ctx(form))
            if not mpesa.is_configured():
                messages.warning(request, "Online M-Pesa payments are being set up. Use the Paybill details below for now.")
                donation.method = "bank"
                donation.save()
                return redirect(donation.get_absolute_url())
            donation.save()
            try:
                resp = mpesa.stk_push(donation.phone, donation.amount, donation.reference, "PGCS donation")
            except mpesa.MpesaError as exc:
                donation.status = "failed"
                donation.result_description = str(exc)[:255]
                donation.save()
                messages.error(request, str(exc))
                return render(request, "donations/donate.html", _ctx(form))
            donation.merchant_request_id = resp.get("MerchantRequestID", "")
            donation.checkout_request_id = resp.get("CheckoutRequestID", "")
            donation.save()
        else:
            donation.save()
            notify_staff(f"New {donation.get_method_display()} pledge {donation.reference}",
                         f"{donation.donor_name} pledged KES {donation.amount:,.0f} via {donation.get_method_display()}.\n"
                         f"Phone: {donation.phone}\nEmail: {donation.email}\n{donation.in_kind_description}")
        return redirect(donation.get_absolute_url())
    return render(request, "donations/donate.html", _ctx(form))


def _ctx(form):
    return {
        "form": form, "presets": PRESET_AMOUNTS, "impact_kes": IMPACT_KES, "impact_usd": IMPACT_USD,
        "card_currency": settings.PAYPAL["CURRENCY"], "kes_per_usd": settings.PAYPAL_KES_PER_USD,
        "featured_projects": Project.objects.filter(status__in=["fundraising", "ongoing"]).select_related("focus_area")[:3],
        "supporters": Donation.objects.filter(status="completed").select_related("project").order_by("-completed_at")[:6],
        "methods": [
            ("mpesa", "M-Pesa", "phone", "Instant prompt on your phone"),
            ("card", "Debit / credit card", "credit-card-2-front", "Visa, Mastercard, Amex"),
            ("paypal", "PayPal", "paypal", "Pay with your PayPal account"),
            ("bank", "Bank transfer", "bank", "Get our account details"),
            ("in_kind", "In-kind gift", "box2-heart", "Food, books, supplies"),
        ],
    }


def status(request, reference):
    donation = get_object_or_404(Donation, reference=reference)
    return render(request, "donations/status.html", {"donation": donation})


def pay(request, reference):
    """Second step for card / PayPal gifts: PayPal's buttons for this exact donation."""
    donation = get_object_or_404(Donation, reference=reference)
    if not donation.is_online_card or donation.status != "pending":
        return redirect(donation.get_absolute_url())
    return render(request, "donations/pay.html", {
        "donation": donation, "paypal_ready": paypal.is_configured(), "paypal_client_id": settings.PAYPAL["CLIENT_ID"],
    })


@require_POST
def paypal_create(request, reference):
    donation = get_object_or_404(Donation, reference=reference, status="pending", method__in=CARD_METHODS)
    try:
        order_id = paypal.create_order(donation)
    except paypal.PayPalError as exc:
        return JsonResponse({"error": str(exc)}, status=502)
    donation.paypal_order_id = order_id
    donation.save(update_fields=["paypal_order_id", "updated_at"])
    return JsonResponse({"id": order_id})


@require_POST
def paypal_capture(request, reference):
    with transaction.atomic():
        donation = get_object_or_404(Donation.objects.select_for_update(), reference=reference, method__in=CARD_METHODS)
        if donation.status == "completed":
            return JsonResponse({"status": "completed", "redirect": donation.get_absolute_url()})
        if not donation.paypal_order_id:
            return JsonResponse({"error": "No payment was started for this gift."}, status=400)
        try:
            capture_id, paid, currency = paypal.capture_order(donation.paypal_order_id)
        except paypal.PayPalError as exc:
            donation.result_description = str(exc)[:255]
            donation.save(update_fields=["result_description", "updated_at"])
            return JsonResponse({"error": str(exc)}, status=402)
        if currency != donation.currency or paid != donation.amount:
            logger.warning("PayPal amount mismatch on %s: expected %s %s got %s %s",
                           donation.reference, donation.currency, donation.amount, currency, paid)
            donation.currency, donation.amount, donation.amount_kes = currency, paid, 0
        donation.paypal_capture_id = capture_id
        _complete(donation, description="Paid by " + donation.get_method_display())
    return JsonResponse({"status": "completed", "redirect": donation.get_absolute_url()})


def status_json(request, reference):
    """Polled by the status page every few seconds while the donor completes the M-Pesa prompt."""
    donation = get_object_or_404(Donation, reference=reference)
    age = (timezone.now() - donation.created_at).total_seconds()
    if donation.status == "pending" and donation.method == "mpesa" and donation.checkout_request_id and age > 25:
        result = mpesa.stk_query(donation.checkout_request_id)
        code = str(result.get("ResultCode", ""))
        if code == "0":
            _complete(donation, receipt=donation.mpesa_receipt, description=result.get("ResultDesc", ""))
        elif code and code not in ("", "4999"):  # 4999 = still processing
            donation.status = "cancelled" if code == "1032" else "failed"
            donation.result_description = result.get("ResultDesc", "")[:255]
            donation.save()
    if donation.status == "pending" and age > 180:
        donation.status = "failed"
        donation.result_description = "No confirmation received from M-Pesa within 3 minutes."
        donation.save()
    return JsonResponse({"status": donation.status, "message": donation.result_description,
                         "receipt": donation.mpesa_receipt})


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Safaricom posts the payment result here."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)
    checkout_id, code, desc, meta = mpesa.parse_callback(body)
    with transaction.atomic():
        donation = Donation.objects.select_for_update().filter(checkout_request_id=checkout_id).first()
        if not donation:
            logger.warning("M-Pesa callback for unknown CheckoutRequestID %s", checkout_id)
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
        donation.raw_callback = body
        if donation.status == "pending":
            if code == 0:
                paid = meta.get("Amount")
                if paid is not None and int(float(paid)) != int(donation.amount):
                    logger.warning("Amount mismatch on %s: expected %s got %s", donation.reference, donation.amount, paid)
                    donation.amount = paid
                _complete(donation, receipt=str(meta.get("MpesaReceiptNumber", "")), description=desc)
            else:
                donation.status = "cancelled" if code == 1032 else "failed"
                donation.result_description = desc[:255]
                donation.save()
        else:
            donation.save(update_fields=["raw_callback"])
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


def _complete(donation, receipt="", description=""):
    donation.status = "completed"
    donation.mpesa_receipt = receipt or donation.mpesa_receipt
    donation.result_description = description[:255]
    donation.completed_at = timezone.now()
    donation.save()
    if not donation.receipt_sent:
        via = "M-Pesa" if donation.method == "mpesa" else donation.get_method_display()
        notify_person(donation.email, f"Thank you for your gift ({donation.reference})",
                      f"Dear {donation.donor_name},\n\nWe received {donation.currency} {donation.amount:,.2f} "
                      f"by {via} (receipt {donation.receipt_number or 'n/a'}) towards {donation.designation}.\n\n"
                      "Thank you for serving with us.\n\nPEFA GraceWorks Community Services")
        notify_staff(f"Donation received {donation.reference}",
                     f"{donation.currency} {donation.amount:,.2f} by {via} from {donation.donor_name} "
                     f"({donation.phone or donation.email}). Receipt {donation.receipt_number}.")
        Donation.objects.filter(pk=donation.pk).update(receipt_sent=True)
