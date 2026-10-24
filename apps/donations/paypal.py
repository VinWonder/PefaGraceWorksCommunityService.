"""
PayPal Checkout (Orders v2): PayPal balance and debit / credit cards through one integration.

1. Create an app on https://developer.paypal.com → Apps & Credentials (Sandbox first, then Live).
2. Put its Client ID and Secret in .env as PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET, PAYPAL_ENV=sandbox|live.
3. The donate page shows PayPal's own buttons; the "Debit or Credit Card" button lets donors pay by card
   without a PayPal account. The order is created and captured on our server so amounts can't be tampered with.
"""
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PayPalError(Exception):
    pass


def _base_url():
    return "https://api-m.paypal.com" if settings.PAYPAL["ENV"] == "live" else "https://api-m.sandbox.paypal.com"


def is_configured():
    return bool(settings.PAYPAL["CLIENT_ID"] and settings.PAYPAL["CLIENT_SECRET"])


def get_access_token():
    token = cache.get("paypal_token")
    if token:
        return token
    cfg = settings.PAYPAL
    try:
        resp = requests.post(f"{_base_url()}/v1/oauth2/token", data={"grant_type": "client_credentials"},
                             auth=(cfg["CLIENT_ID"], cfg["CLIENT_SECRET"]), timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.exception("PayPal token request failed")
        raise PayPalError("PayPal is not reachable right now. Try again in a few minutes.") from exc
    cache.set("paypal_token", data["access_token"], int(data.get("expires_in", 3600)) - 120)
    return data["access_token"]


def _post(path, payload=None, request_id=None):
    headers = {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}
    if request_id:
        headers["PayPal-Request-Id"] = request_id  # makes retries idempotent
    try:
        resp = requests.post(f"{_base_url()}{path}", json=payload or {}, headers=headers, timeout=30)
    except requests.RequestException as exc:
        logger.exception("PayPal request to %s failed", path)
        raise PayPalError("PayPal is not reachable right now. Try again in a few minutes.") from exc
    data = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        logger.warning("PayPal %s returned %s: %s", path, resp.status_code, data)
        detail = (data.get("details") or [{}])[0].get("description") or data.get("message") or "PayPal declined the request."
        raise PayPalError(detail)
    return data


def create_order(donation):
    """Create an order for exactly this donation's amount and return PayPal's order id."""
    data = _post("/v2/checkout/orders", {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": donation.reference,
            "custom_id": donation.reference,
            "description": f"Gift to PEFA GraceWorks: {donation.designation}"[:127],
            "amount": {"currency_code": donation.currency, "value": f"{donation.amount:.2f}"},
        }],
        # application_context (not payment_source.paypal) so the same order works for the card button too
        "application_context": {"brand_name": "PEFA GraceWorks", "shipping_preference": "NO_SHIPPING", "user_action": "PAY_NOW"},
    }, request_id=f"{donation.reference}-create")
    return data["id"]


def capture_order(order_id):
    """Capture an approved order. Returns (capture_id, amount, currency) or raises PayPalError."""
    data = _post(f"/v2/checkout/orders/{order_id}/capture", request_id=f"{order_id}-capture")
    if data.get("status") != "COMPLETED":
        raise PayPalError("The payment was not completed.")
    capture = data["purchase_units"][0]["payments"]["captures"][0]
    if capture.get("status") not in ("COMPLETED", "PENDING"):
        raise PayPalError("The card or PayPal account was declined.")
    return capture["id"], Decimal(capture["amount"]["value"]), capture["amount"]["currency_code"]
