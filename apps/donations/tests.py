import json
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from . import mpesa
from .models import Donation

MPESA_TEST = {"ENV": "sandbox", "CONSUMER_KEY": "k", "CONSUMER_SECRET": "s", "SHORTCODE": "174379",
              "PASSKEY": "p", "CALLBACK_URL": "https://example.com/donate/mpesa/callback/", "TRANSACTION_TYPE": "CustomerPayBillOnline"}


class MpesaTest(TestCase):
    def test_phone_normalisation(self):
        self.assertEqual(mpesa.normalize_phone("0712 345 678"), "254712345678")
        self.assertEqual(mpesa.normalize_phone("+254712345678"), "254712345678")
        with self.assertRaises(mpesa.MpesaError):
            mpesa.normalize_phone("12345")

    @override_settings(MPESA=MPESA_TEST)
    @mock.patch("apps.donations.mpesa.stk_push", return_value={"ResponseCode": "0", "CheckoutRequestID": "ws_CO_1", "MerchantRequestID": "m1"})
    def test_full_flow_with_callback(self, _push):
        resp = self.client.post(reverse("donations:donate"), {
            "amount": "1000", "method": "mpesa", "frequency": "once", "donor_name": "Mary", "phone": "0712345678"})
        d = Donation.objects.get(donor_name="Mary")
        self.assertRedirects(resp, d.get_absolute_url())
        self.assertEqual(d.status, "pending")
        callback = {"Body": {"stkCallback": {"MerchantRequestID": "m1", "CheckoutRequestID": "ws_CO_1", "ResultCode": 0,
                     "ResultDesc": "ok", "CallbackMetadata": {"Item": [{"Name": "Amount", "Value": 1000},
                     {"Name": "MpesaReceiptNumber", "Value": "QWE123"}]}}}}
        self.client.post(reverse("donations:mpesa_callback"), json.dumps(callback), content_type="application/json")
        d.refresh_from_db()
        self.assertEqual(d.status, "completed")
        self.assertEqual(d.mpesa_receipt, "QWE123")

    def test_bank_pledge(self):
        resp = self.client.post(reverse("donations:donate"), {
            "amount": "5000", "method": "bank", "frequency": "once", "donor_name": "John", "email": "j@example.com"})
        d = Donation.objects.get(donor_name="John")
        self.assertRedirects(resp, d.get_absolute_url())
        self.assertEqual(d.method, "bank")


PAYPAL_TEST = {"ENV": "sandbox", "CLIENT_ID": "cid", "CLIENT_SECRET": "sec", "CURRENCY": "USD"}


@override_settings(PAYPAL=PAYPAL_TEST, PAYPAL_KES_PER_USD=130)
class PayPalTest(TestCase):
    def _start(self, method="card", amount="25"):
        resp = self.client.post(reverse("donations:donate"), {
            "amount": amount, "method": method, "frequency": "once", "donor_name": "Ann", "email": "ann@example.com"})
        d = Donation.objects.get(donor_name="Ann")
        self.assertRedirects(resp, reverse("donations:pay", args=[d.reference]))
        return d

    def test_card_gift_is_taken_in_usd_and_counted_in_kes(self):
        d = self._start()
        self.assertEqual((d.currency, d.method, d.status), ("USD", "card", "pending"))
        self.assertEqual(d.amount_kes, 3250)
        self.assertContains(self.client.get(reverse("donations:pay", args=[d.reference])), "paypal.com/sdk/js")

    @mock.patch("apps.donations.paypal.capture_order")
    @mock.patch("apps.donations.paypal.create_order", return_value="ORDER-1")
    def test_create_and_capture(self, _create, capture):
        from decimal import Decimal

        d = self._start("paypal")
        self.assertEqual(self.client.post(reverse("donations:paypal_create", args=[d.reference])).json(), {"id": "ORDER-1"})
        capture.return_value = ("CAP-9", Decimal("25.00"), "USD")
        data = self.client.post(reverse("donations:paypal_capture", args=[d.reference])).json()
        self.assertEqual(data["status"], "completed")
        d.refresh_from_db()
        self.assertEqual((d.status, d.paypal_capture_id, d.receipt_number), ("completed", "CAP-9", "CAP-9"))
        capture.assert_called_once_with("ORDER-1")

    @mock.patch("apps.donations.paypal.capture_order")
    @mock.patch("apps.donations.paypal.create_order", return_value="ORDER-2")
    def test_capture_records_what_was_actually_paid(self, _create, capture):
        from decimal import Decimal

        d = self._start()
        self.client.post(reverse("donations:paypal_create", args=[d.reference]))
        capture.return_value = ("CAP-1", Decimal("5.00"), "USD")
        self.client.post(reverse("donations:paypal_capture", args=[d.reference]))
        d.refresh_from_db()
        self.assertEqual((d.amount, d.amount_kes), (Decimal("5.00"), Decimal("650.00")))

    def test_card_needs_email(self):
        resp = self.client.post(reverse("donations:donate"), {
            "amount": "25", "method": "card", "frequency": "once", "donor_name": "Bo", "phone": "0712345678"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Donation.objects.filter(donor_name="Bo").exists())
