"""Payment provider contract and Razorpay Standard Checkout implementation."""
import hashlib
import hmac
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import Settings, settings


class PaymentUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class PaymentSession:
    provider_reference: str
    checkout_url: str


class PaymentProvider(Protocol):
    def create_order(self, *, order_reference: str, amount_minor: int, currency: str) -> dict: ...
    def fetch_payment(self, payment_id: str) -> dict: ...
    def verify_checkout_signature(self, *, provider_order_id: str, payment_id: str, signature: str) -> bool: ...
    def verify_webhook(self, *, raw_body: bytes, signature: str) -> dict: ...


class DisabledPaymentProvider:
    def create_order(self, *, order_reference: str, amount_minor: int, currency: str) -> dict:
        raise PaymentUnavailable("Online payments are not configured")

    def fetch_payment(self, payment_id: str) -> dict:
        raise PaymentUnavailable("Online payments are not configured")

    def verify_checkout_signature(self, *, provider_order_id: str, payment_id: str, signature: str) -> bool:
        raise PaymentUnavailable("Online payments are not configured")

    def verify_webhook(self, *, raw_body: bytes, signature: str) -> dict:
        raise PaymentUnavailable("Online payments are not configured")


class RazorpayProvider:
    """Uses Razorpay's documented server Orders API and signature schemes."""
    API = "https://api.razorpay.com/v1"

    def __init__(self, config: Settings = settings, client: httpx.Client | None = None):
        if not config.razorpay_key_id or not config.razorpay_key_secret:
            raise PaymentUnavailable("Razorpay API keys are not configured")
        if config.payment_mode == "test" and not config.razorpay_key_id.startswith("rzp_test_"):
            raise PaymentUnavailable("Test mode requires a Razorpay test key")
        if config.payment_mode == "live" and not config.allow_live_payments:
            raise PaymentUnavailable("Live payment activation is disabled")
        self.config = config
        self.client = client or httpx.Client(auth=(config.razorpay_key_id, config.razorpay_key_secret), timeout=httpx.Timeout(8.0, connect=3.0))

    def create_order(self, *, order_reference: str, amount_minor: int, currency: str) -> dict:
        try:
            response = self.client.post(f"{self.API}/orders", json={"amount": amount_minor, "currency": currency, "receipt": order_reference})
        except httpx.HTTPError as exc:
            raise PaymentUnavailable("Razorpay could not create a payment order") from exc
        if response.is_error:
            raise PaymentUnavailable("Razorpay could not create a payment order")
        try:
            result = response.json()
        except ValueError as exc:
            raise PaymentUnavailable("Razorpay returned an invalid payment order response") from exc
        if result.get("amount") != amount_minor or result.get("currency") != currency or not result.get("id"):
            raise PaymentUnavailable("Razorpay returned an unexpected payment order")
        return result

    def fetch_payment(self, payment_id: str) -> dict:
        try:
            response = self.client.get(f"{self.API}/payments/{payment_id}")
        except httpx.HTTPError as exc:
            raise PaymentUnavailable("Razorpay payment status could not be verified") from exc
        if response.is_error:
            raise PaymentUnavailable("Razorpay payment status could not be verified")
        try:
            return response.json()
        except ValueError as exc:
            raise PaymentUnavailable("Razorpay returned an invalid payment status response") from exc

    def verify_checkout_signature(self, *, provider_order_id: str, payment_id: str, signature: str) -> bool:
        digest = hmac.new(self.config.razorpay_key_secret.encode(), f"{provider_order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    def verify_webhook(self, *, raw_body: bytes, signature: str) -> dict:
        secret = self.config.razorpay_webhook_secret
        if not secret:
            raise PaymentUnavailable("Razorpay webhook secret is not configured")
        digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid webhook signature")
        import json
        return json.loads(raw_body)


def configured_provider(config: Settings = settings) -> PaymentProvider:
    if config.payment_provider == "razorpay":
        return RazorpayProvider(config)
    return DisabledPaymentProvider()
