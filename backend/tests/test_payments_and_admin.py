import asyncio
import hashlib
import hmac
import json
from http.cookies import SimpleCookie

import httpx
import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request
from sqlalchemy import select

from app.core.auth import hash_password, verify_password
from app.core.config import Settings, settings
from app.main import admin_login, admin_orders, checkout, order_status, razorpay_webhook
from app.models import AdminSession, Order
from app.schemas import AdminLoginIn, CheckoutIn
from app.services.payments import PaymentUnavailable, RazorpayProvider


def make_request(headers=(), body=b""):
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    return Request({"type": "http", "method": "POST", "path": "/", "headers": list(headers), "client": ("127.0.0.1", 12345), "query_string": b""}, receive)


def test_password_hash_and_admin_login_is_session_based(db, monkeypatch):
    encoded = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)
    monkeypatch.setattr(settings, "admin_username", "store-operator")
    monkeypatch.setattr(settings, "admin_password_hash", encoded)
    response = Response()
    result = admin_login(AdminLoginIn(username="store-operator", password="correct horse battery staple"), make_request(), response, db)
    assert result["authenticated"] is True
    cookies = SimpleCookie(); cookies.load("; ".join(response.headers.getlist("set-cookie")))
    session_token = cookies["ks_admin_session"].value
    csrf = cookies["ks_admin_csrf"].value
    assert cookies["ks_admin_session"]["httponly"]
    assert db.scalar(select(AdminSession).where(AdminSession.token_sha256 == hashlib.sha256(session_token.encode()).hexdigest()))
    cookie_header = f"ks_admin_session={session_token}; ks_admin_csrf={csrf}".encode()
    admin_request = make_request([(b"cookie", cookie_header)])
    assert admin_orders(admin_request, None, None, 50, 0, db)["items"] == []


def test_razorpay_order_signature_and_webhook_verification(db, monkeypatch):
    config = Settings(payment_provider="razorpay", payment_mode="test", razorpay_key_id="rzp_test_demo", razorpay_key_secret="api_secret", razorpay_webhook_secret="hook_secret")
    def responder(request):
        assert request.url.path == "/v1/orders"
        assert json.loads(request.content)["amount"] == 12300
        return httpx.Response(200, json={"id": "order_demo123", "amount": 12300, "currency": "INR"})
    provider = RazorpayProvider(config, httpx.Client(transport=httpx.MockTransport(responder)))
    created = provider.create_order(order_reference="A" * 32, amount_minor=12300, currency="INR")
    assert created["id"] == "order_demo123"
    signature = hmac.new(b"api_secret", b"order_demo123|pay_demo123", hashlib.sha256).hexdigest()
    assert provider.verify_checkout_signature(provider_order_id="order_demo123", payment_id="pay_demo123", signature=signature)
    raw = b'{"event":"payment.failed"}'
    webhook_sig = hmac.new(b"hook_secret", raw, hashlib.sha256).hexdigest()
    assert provider.verify_webhook(raw_body=raw, signature=webhook_sig)["event"] == "payment.failed"
    with pytest.raises(ValueError):
        provider.verify_webhook(raw_body=raw, signature="0" * 64)


def test_razorpay_network_errors_are_sanitized():
    config = Settings(payment_provider="razorpay", payment_mode="test", razorpay_key_id="rzp_test_demo", razorpay_key_secret="api_secret")
    def fail(_request):
        raise httpx.ConnectError("connection failed with sensitive provider details")
    provider = RazorpayProvider(config, httpx.Client(transport=httpx.MockTransport(fail)))
    with pytest.raises(PaymentUnavailable, match="Razorpay could not create a payment order") as exc:
        provider.create_order(order_reference="A" * 32, amount_minor=1000, currency="INR")
    assert "sensitive provider details" not in str(exc.value)


def test_webhook_is_idempotent_and_failure_cannot_downgrade_captured(db, monkeypatch):
    monkeypatch.setattr(settings, "inventory_mode", "unlimited")
    monkeypatch.setattr(settings, "payment_provider", "disabled")
    monkeypatch.setattr(settings, "payment_mode", "test")
    monkeypatch.setattr(settings, "allow_live_payments", False)
    monkeypatch.setattr(settings, "razorpay_key_id", "rzp_test_demo")
    monkeypatch.setattr(settings, "razorpay_key_secret", "api_secret")
    monkeypatch.setattr(settings, "razorpay_webhook_secret", "hook_secret")
    from app.main import products
    variant_id = products(db)[0]["variants"][0]["id"]
    data = CheckoutIn(items=[{"variant_id": variant_id, "quantity": 1}], name="Test Buyer", email="buyer@example.com", address="12 Example Street, Mumbai")
    order_result = checkout(data, make_request(), db, None, "payment-test-idempotency-key")
    order = db.scalar(select(Order).where(Order.public_reference == order_result.reference))
    order.provider_order_id = "order_demo123"
    db.commit()
    monkeypatch.setattr(settings, "payment_provider", "razorpay")
    def send_event(event_id, event_name, payment_status, captured):
        payload = {"event": event_name, "payload": {"payment": {"entity": {"id": "pay_demo123", "order_id": "order_demo123", "amount": order.total_minor, "currency": "INR", "status": payment_status, "captured": captured}}}}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(b"hook_secret", raw, hashlib.sha256).hexdigest()
        request = make_request([(b"content-type", b"application/json")], raw)
        return asyncio.run(razorpay_webhook(request, signature, event_id, db))
    assert send_event("evt-captured", "payment.captured", "captured", True)["duplicate"] is False
    assert send_event("evt-captured", "payment.captured", "captured", True)["duplicate"] is True
    assert send_event("evt-failed-late", "payment.failed", "failed", False)["accepted"] is True
    db.refresh(order)
    assert order.status == "paid"
    assert order.provider_payment_id == "pay_demo123"
