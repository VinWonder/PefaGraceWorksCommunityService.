"""
M-Pesa Daraja integration (Lipa na M-Pesa Online / STK Push).

1. Create an app on https://developer.safaricom.co.ke to get a consumer key & secret.
2. Sandbox shortcode is 174379 and the sandbox passkey is shown on the Daraja portal.
3. MPESA_CALLBACK_URL must be a public HTTPS URL that ends with /donate/mpesa/callback/
   (use ngrok while developing, your real domain in production).
"""
import base64
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MpesaError(Exception):
    pass


def _base_url():
    return "https://api.safaricom.co.ke" if settings.MPESA["ENV"] == "production" else "https://sandbox.safaricom.co.ke"


def is_configured():
    cfg = settings.MPESA
    return all([cfg["CONSUMER_KEY"], cfg["CONSUMER_SECRET"], cfg["SHORTCODE"], cfg["PASSKEY"], cfg["CALLBACK_URL"]])


def normalize_phone(phone):
    """0712345678 / +254712345678 / 712345678 → 254712345678"""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    elif len(digits) == 9:
        digits = "254" + digits
    if not (digits.startswith("2547") or digits.startswith("2541")) or len(digits) != 12:
        raise MpesaError("Enter a valid Safaricom number, e.g. 0712 345 678.")
    return digits


def get_access_token():
    token = cache.get("mpesa_token")
    if token:
        return token
    cfg = settings.MPESA
    try:
        resp = requests.get(
            f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials",
            auth=(cfg["CONSUMER_KEY"], cfg["CONSUMER_SECRET"]), timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.exception("M-Pesa token request failed")
        raise MpesaError("M-Pesa is not reachable right now. Try again in a few minutes.") from exc
    token = data["access_token"]
    cache.set("mpesa_token", token, int(data.get("expires_in", 3599)) - 60)
    return token


def _password(timestamp):
    cfg = settings.MPESA
    return base64.b64encode(f"{cfg['SHORTCODE']}{cfg['PASSKEY']}{timestamp}".encode()).decode()


def stk_push(phone, amount, account_reference, description="Donation"):
    cfg = settings.MPESA
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = {
        "BusinessShortCode": cfg["SHORTCODE"],
        "Password": _password(timestamp),
        "Timestamp": timestamp,
        "TransactionType": cfg["TRANSACTION_TYPE"],
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": cfg["SHORTCODE"],
        "PhoneNumber": phone,
        "CallBackURL": cfg["CALLBACK_URL"],
        "AccountReference": account_reference[:12],
        "TransactionDesc": description[:13],
    }
    try:
        resp = requests.post(f"{_base_url()}/mpesa/stkpush/v1/processrequest", json=payload,
                             headers={"Authorization": f"Bearer {get_access_token()}"}, timeout=30)
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.exception("STK push failed")
        raise MpesaError("We couldn't reach M-Pesa. Try again in a few minutes.") from exc
    if data.get("ResponseCode") != "0":
        logger.warning("STK push rejected: %s", data)
        raise MpesaError(data.get("errorMessage") or data.get("ResponseDescription") or "M-Pesa rejected the request.")
    return data


def stk_query(checkout_request_id):
    """Ask Safaricom for the result directly (backup for when the callback can't reach us)."""
    cfg = settings.MPESA
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = {"BusinessShortCode": cfg["SHORTCODE"], "Password": _password(timestamp),
               "Timestamp": timestamp, "CheckoutRequestID": checkout_request_id}
    try:
        resp = requests.post(f"{_base_url()}/mpesa/stkpushquery/v1/query", json=payload,
                             headers={"Authorization": f"Bearer {get_access_token()}"}, timeout=30)
        return resp.json()
    except (requests.RequestException, ValueError, MpesaError):
        logger.exception("STK query failed")
        return {}


def parse_callback(body):
    """Return (checkout_request_id, result_code, description, metadata_dict)."""
    cb = body.get("Body", {}).get("stkCallback", {})
    items = cb.get("CallbackMetadata", {}).get("Item", [])
    meta = {i.get("Name"): i.get("Value") for i in items}
    return cb.get("CheckoutRequestID"), cb.get("ResultCode"), cb.get("ResultDesc", ""), meta
