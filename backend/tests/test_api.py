import pytest
from fastapi import HTTPException
from starlette.requests import Request
from pydantic import ValidationError
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.main import checkout, collections as list_collections, expire_reservations, health, mark_order_paid, order_status, products as list_products
from app.core.config import settings
from app.models import InventoryRecord, InventoryReservation, Order
from app.schemas import CheckoutIn


def test_health_and_catalog_handlers(db):
    assert health() == {"status": "ok"}
    assert len(list_collections(db)) == 4
    products = list_products(db)
    assert len(products) == 6
    assert products[0]["variants"][0]["price_minor"] == 349900


def test_checkout_server_price_and_scoped_access(db, monkeypatch):
    monkeypatch.setattr(settings, "inventory_mode", "unlimited")
    variant_id = list_products(db)[0]["variants"][0]["id"]
    payload = CheckoutIn(items=[{"variant_id": variant_id, "quantity": 2}], name="Test Buyer", email="buyer@example.com", address="12 Example Street, Mumbai")
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 12345)})
    result = checkout(payload, request, db, None, "unique-test-idempotency-key-1")
    assert result.subtotal_minor == 699800
    assert result.payment_ready is False
    assert order_status(result.reference, result.access_token, db)["status"] == "pending_payment"
    with pytest.raises(HTTPException) as error:
        order_status(result.reference, "wrong", db)
    assert error.value.status_code == 404

    repeated = checkout(payload, request, db, None, "unique-test-idempotency-key-1")
    assert repeated.reference == result.reference
    assert repeated.access_token != result.access_token
    with pytest.raises(HTTPException) as invalid_reuse:
        checkout(payload.model_copy(update={"name": "Different Buyer"}), request, db, None, "unique-test-idempotency-key-1")
    assert invalid_reuse.value.status_code == 409


def test_checkout_rejects_unavailable_variant_and_invalid_quantity(db, monkeypatch):
    monkeypatch.setattr(settings, "inventory_mode", "unlimited")
    payload = CheckoutIn(items=[{"variant_id": 9999, "quantity": 1}], name="Test Buyer", email="buyer@example.com", address="12 Example Street, Mumbai")
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 12345)})
    with pytest.raises(HTTPException) as error:
        checkout(payload, request, db, None, "unique-test-idempotency-key-2")
    assert error.value.status_code == 422
    with pytest.raises(ValidationError):
        CheckoutIn(items=[{"variant_id": 1, "quantity": 11}], name="Test Buyer", email="buyer@example.com", address="12 Example Street, Mumbai")


def test_stock_reservation_expiry_and_late_capture_review(db, monkeypatch):
    monkeypatch.setattr(settings, "inventory_mode", "disabled")
    variant_id = list_products(db)[0]["variants"][0]["id"]
    payload = CheckoutIn(items=[{"variant_id": variant_id, "quantity": 2}], name="Test Buyer", email="buyer@example.com", address="12 Example Street, Mumbai")
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 12345)})
    with pytest.raises(HTTPException) as unconfigured:
        checkout(payload, request, db, None, "inventory-test-key-unconfigured")
    assert unconfigured.value.status_code == 503
    record = InventoryRecord(variant_id=variant_id, mode="limited", quantity_on_hand=2, quantity_reserved=0)
    db.add(record); db.commit()
    order_result = checkout(payload, request, db, None, "inventory-test-key-limited")
    db.refresh(record)
    assert record.quantity_reserved == 2
    order = db.scalar(select(Order).where(Order.public_reference == order_result.reference))
    reservation = db.scalar(select(InventoryReservation).where(InventoryReservation.order_id == order.id))
    reservation.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    expire_reservations(db)
    db.refresh(record); db.refresh(order)
    assert record.quantity_reserved == 0 and order.status == "cancelled"
    mark_order_paid(db, order, "pay-late-capture")
    db.commit()
    db.refresh(record); db.refresh(order)
    assert order.status == "paid" and record.quantity_on_hand == 0

    record.quantity_on_hand = 1
    db.commit()
    another = checkout(CheckoutIn(items=[{"variant_id": variant_id, "quantity": 1}], name="Another Buyer", email="another@example.com", address="34 Example Street, Mumbai"), request, db, None, "inventory-test-key-shortage")
    another_order = db.scalar(select(Order).where(Order.public_reference == another.reference))
    another_reservation = db.scalar(select(InventoryReservation).where(InventoryReservation.order_id == another_order.id))
    another_reservation.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit(); expire_reservations(db)
    record.quantity_on_hand = 0; db.commit()
    mark_order_paid(db, another_order, "pay-late-shortage")
    db.commit(); db.refresh(another_order)
    assert another_order.status == "paid" and another_order.fulfillment_status == "inventory_review"
