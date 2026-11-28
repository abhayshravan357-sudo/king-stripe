import hashlib
import hmac
import json
import logging
import secrets
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.catalog_seed import COLLECTIONS, PRODUCTS, SIZES
from app.core.config import settings
from app.db import Base, engine, get_db
from app.core.auth import hash_token, verify_password
from app.core.rate_limit import limit_request
from app.models import (AdminAudit, AdminSession, Collection, InventoryMovement,
                        InventoryRecord, InventoryReservation, Order, OrderItem,
                        PaymentEvent, Product, ProductVariant)
from app.schemas import (AdminLoginIn, CheckoutIn, CheckoutOut, FulfillmentUpdate,
                         InventoryUpdate, PaymentVerifyIn, VariantUpdate)
from app.services.payments import PaymentUnavailable, RazorpayProvider, configured_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("kingstripe")


def seed_catalog(db: Session):
    if db.scalar(select(Collection.id).limit(1)) is not None:
        return
    collections = {c["slug"]: Collection(**c) for c in COLLECTIONS}
    db.add_all(collections.values())
    db.flush()
    for slug, name, kind, price, colours in PRODUCTS:
        product = Product(slug=slug, name=name, garment_type=kind, collection_id=collections["tiger-black"].id)
        for colour in colours:
            for size in SIZES:
                product.variants.append(ProductVariant(sku=f"KS-{slug.upper()}-{colour.upper()}-{size}", colour=colour, size=size, price_minor=price * 100, currency="INR"))
        db.add(product)
    db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Local convenience only. Production schema changes must use Alembic migrations.
    if settings.environment == "development" and settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            seed_catalog(db)
    sweeper = asyncio.create_task(reservation_sweeper()) if settings.environment != "test" else None
    try:
        yield
    finally:
        if sweeper:
            sweeper.cancel()
            try:
                await sweeper
            except asyncio.CancelledError:
                pass


app = FastAPI(title="King Stripe API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"], allow_headers=["Content-Type", "X-Order-Token", "Idempotency-Key", "X-CSRF-Token", "X-Razorpay-Signature", "X-Razorpay-Event-Id"])


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@app.get("/api/v1/collections")
def collections(db: Session = Depends(get_db)):
    return [dict(id=c.id, slug=c.slug, title=c.title, animal=c.animal, colour=c.colour, tagline=c.tagline, description=c.description, status=c.status, artwork=c.artwork, accent=c.accent, featured=c.featured) for c in db.scalars(select(Collection).order_by(Collection.id)).all()]


@app.get("/api/v1/products")
def products(db: Session = Depends(get_db)):
    rows = db.scalars(select(Product).where(Product.active.is_(True)).options(selectinload(Product.variants), selectinload(Product.collection)).order_by(Product.id)).all()
    return [dict(id=p.id, slug=p.slug, name=p.name, type=p.garment_type, collection=p.collection.slug, variants=[dict(id=v.id, sku=v.sku, colour=v.colour, size=v.size, price_minor=v.price_minor, currency=v.currency) for v in p.variants if v.active]) for p in rows]


def checkout_response(order: Order, access_token: str, payment_ready: bool = False, key_id: str | None = None) -> CheckoutOut:
    return CheckoutOut(reference=order.public_reference, access_token=access_token, status=order.status,
                       subtotal_minor=order.subtotal_minor, currency=order.currency, payment_ready=payment_ready,
                       message="Payment order created." if payment_ready else "Order saved as pending. Online payment is not configured.",
                       provider_order_id=order.provider_order_id, razorpay_key_id=key_id)


def payload_fingerprint(payload: CheckoutIn) -> str:
    canonical = {"items": sorted((line.variant_id, line.quantity) for line in payload.items),
                 "name": payload.name.strip(), "email": str(payload.email).lower(), "address": payload.address.strip()}
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reserve_inventory(db: Session, order: Order, requested: dict[int, int], variants: list[ProductVariant]):
    now = datetime.now(timezone.utc)
    for variant in variants:
        record = db.scalar(select(InventoryRecord).where(InventoryRecord.variant_id == variant.id).with_for_update())
        mode = record.mode if record else settings.inventory_mode
        if mode not in {"limited", "preorder", "made_to_order", "unlimited"}:
            raise HTTPException(503, "Store availability is not configured")
        quantity = requested[variant.id]
        if mode == "limited":
            if not record or record.quantity_on_hand is None or record.quantity_on_hand - record.quantity_reserved < quantity:
                raise HTTPException(409, "One or more selected variants are out of stock")
            record.quantity_reserved += quantity
            db.add(InventoryMovement(variant_id=variant.id, order_id=order.id, quantity_delta=quantity, movement_type="reserved", actor="checkout"))
        db.add(InventoryReservation(order_id=order.id, variant_id=variant.id, quantity=quantity, expires_at=now + timedelta(minutes=settings.reservation_minutes)))


def release_reservations(db: Session, order: Order, *, consume: bool):
    for reservation in db.scalars(select(InventoryReservation).where(InventoryReservation.order_id == order.id, InventoryReservation.status == "reserved").with_for_update()).all():
        record = db.scalar(select(InventoryRecord).where(InventoryRecord.variant_id == reservation.variant_id).with_for_update())
        if record and record.mode == "limited":
            record.quantity_reserved = max(0, record.quantity_reserved - reservation.quantity)
            if consume:
                record.quantity_on_hand = max(0, (record.quantity_on_hand or 0) - reservation.quantity)
            db.add(InventoryMovement(variant_id=reservation.variant_id, order_id=order.id, quantity_delta=-reservation.quantity if consume else 0, movement_type="sold" if consume else "released", actor="payment"))
        reservation.status = "consumed" if consume else "released"


def expire_reservations(db: Session):
    now = datetime.now(timezone.utc)
    reservations = db.scalars(select(InventoryReservation).where(InventoryReservation.status == "reserved", InventoryReservation.expires_at <= now).with_for_update()).all()
    for reservation in reservations:
        record = db.scalar(select(InventoryRecord).where(InventoryRecord.variant_id == reservation.variant_id).with_for_update())
        if record and record.mode == "limited":
            record.quantity_reserved = max(0, record.quantity_reserved - reservation.quantity)
            db.add(InventoryMovement(variant_id=reservation.variant_id, order_id=reservation.order_id, quantity_delta=0, movement_type="expired", actor="system"))
        reservation.status = "expired"
        order = db.get(Order, reservation.order_id)
        if order and order.status == "pending_payment":
            order.status = "cancelled"
    db.commit()


async def reservation_sweeper():
    while True:
        await asyncio.sleep(30)
        try:
            with Session(engine) as db:
                expire_reservations(db)
        except Exception:
            log.exception("Inventory reservation expiry pass failed")


def mark_order_paid(db: Session, order: Order, payment_id: str):
    if order.status == "refunded":
        return
    if order.provider_payment_id and order.provider_payment_id != payment_id:
        raise HTTPException(409, "Order already has a different captured payment")
    if order.status == "paid":
        return
    active_reservations = db.scalar(select(func.count(InventoryReservation.id)).where(InventoryReservation.order_id == order.id, InventoryReservation.status == "reserved")) or 0
    if not active_reservations:
        items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        records = {record.variant_id: record for record in db.scalars(select(InventoryRecord).where(InventoryRecord.variant_id.in_([item.variant_id for item in items])).with_for_update()).all()}
        shortage = False
        for item in items:
            record = records.get(item.variant_id)
            if record and record.mode == "limited" and (record.quantity_on_hand or 0) - record.quantity_reserved < item.quantity:
                shortage = True
        if shortage:
            order.status = "paid"
            order.provider_payment_id = payment_id
            order.fulfillment_status = "inventory_review"
            log.error("Captured order %s requires inventory review", order.public_reference)
            return
        now = datetime.now(timezone.utc)
        for item in items:
            record = records.get(item.variant_id)
            if record and record.mode == "limited":
                record.quantity_reserved += item.quantity
                db.add(InventoryMovement(variant_id=item.variant_id, order_id=order.id, quantity_delta=item.quantity, movement_type="late_capture_reserved", actor="payment"))
            reservation = db.scalar(select(InventoryReservation).where(InventoryReservation.order_id == order.id, InventoryReservation.variant_id == item.variant_id).with_for_update())
            if reservation:
                reservation.quantity = item.quantity
                reservation.status = "reserved"
                reservation.expires_at = now + timedelta(minutes=settings.reservation_minutes)
            else:
                db.add(InventoryReservation(order_id=order.id, variant_id=item.variant_id, quantity=item.quantity, status="reserved", expires_at=now + timedelta(minutes=settings.reservation_minutes)))
    order.status = "paid"
    order.provider_payment_id = payment_id
    release_reservations(db, order, consume=True)


@app.post("/api/v1/checkout-sessions", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
def checkout(payload: CheckoutIn, request: Request, db: Session = Depends(get_db), origin: str | None = Header(default=None), idempotency_key: str = Header(alias="Idempotency-Key", min_length=16, max_length=100)):
    if origin and origin not in settings.cors_origins:
        raise HTTPException(403, "Origin is not allowed")
    limit_request(request, bucket="checkout", count=8, seconds=60)
    try:
        provider = configured_provider()
    except PaymentUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    requested = {line.variant_id: line.quantity for line in payload.items}
    if len(requested) != len(payload.items):
        raise HTTPException(422, "Duplicate variants must be combined")
    key_hash = hash_token(idempotency_key)
    fingerprint = payload_fingerprint(payload)
    existing = db.scalar(select(Order).where(Order.idempotency_key_hash == key_hash))
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise HTTPException(409, "Idempotency key was used with different checkout details")
        token = secrets.token_urlsafe(32)
        existing.access_token_hash = hash_token(token)
        db.commit()
        if isinstance(provider, RazorpayProvider) and not existing.provider_order_id:
            try:
                payment_order = provider.create_order(order_reference=existing.public_reference, amount_minor=existing.total_minor, currency=existing.currency)
                existing.provider_order_id = payment_order["id"]
                db.commit()
            except PaymentUnavailable as exc:
                raise HTTPException(502, str(exc)) from exc
        return checkout_response(existing, token, isinstance(provider, RazorpayProvider), settings.razorpay_key_id if isinstance(provider, RazorpayProvider) else None)
    variants = db.scalars(select(ProductVariant).where(ProductVariant.id.in_(requested), ProductVariant.active.is_(True)).options(selectinload(ProductVariant.product))).all()
    if len(variants) != len(requested) or any(not v.product.active for v in variants):
        raise HTTPException(422, "One or more selected items are unavailable")
    subtotal = sum(v.price_minor * requested[v.id] for v in variants)
    token = secrets.token_urlsafe(32)
    order = Order(public_reference=uuid4().hex.upper(), access_token_hash=hash_token(token), idempotency_key_hash=key_hash, request_fingerprint=fingerprint, customer_name=payload.name.strip(), customer_email=str(payload.email), shipping_address=payload.address.strip(), subtotal_minor=subtotal, total_minor=subtotal, currency="INR")
    for v in variants:
        q = requested[v.id]
        order.items.append(OrderItem(product_id=v.product_id, variant_id=v.id, product_name=v.product.name, sku=v.sku, colour=v.colour, size=v.size, unit_price_minor=v.price_minor, quantity=q, line_total_minor=v.price_minor*q))
    db.add(order)
    try:
        db.flush()
        reserve_inventory(db, order, requested, variants)
        db.commit()
    except Exception:
        db.rollback()
        raise
    if isinstance(provider, RazorpayProvider):
        try:
            payment_order = provider.create_order(order_reference=order.public_reference, amount_minor=order.total_minor, currency=order.currency)
            order.provider_order_id = payment_order["id"]
            db.commit()
        except PaymentUnavailable as exc:
            raise HTTPException(502, str(exc)) from exc
    return checkout_response(order, token, isinstance(provider, RazorpayProvider), settings.razorpay_key_id if isinstance(provider, RazorpayProvider) else None)


@app.get("/api/v1/orders/{reference}")
def order_status(reference: str, x_order_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not x_order_token:
        raise HTTPException(401, "Order access token required")
    order = db.scalar(select(Order).where(Order.public_reference == reference))
    digest = hash_token(x_order_token)
    if not order or not secrets.compare_digest(digest, order.access_token_hash):
        raise HTTPException(404, "Order not found")
    return {"reference": order.public_reference, "status": order.status, "fulfillment_status": order.fulfillment_status, "total_minor": order.total_minor, "refunded_minor": order.refunded_minor, "currency": order.currency}


@app.post("/api/v1/payments/verify")
def verify_payment(payload: PaymentVerifyIn, request: Request, x_order_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    limit_request(request, bucket="payment_verify", count=12, seconds=60)
    if not x_order_token:
        raise HTTPException(401, "Order access token required")
    order = db.scalar(select(Order).where(Order.public_reference == payload.order_reference))
    if not order or not hmac.compare_digest(hash_token(x_order_token), order.access_token_hash):
        raise HTTPException(404, "Order not found")
    if not order.provider_order_id or order.provider_order_id != payload.razorpay_order_id:
        raise HTTPException(400, "Payment order does not match this checkout")
    try:
        provider = configured_provider()
        if not isinstance(provider, RazorpayProvider):
            raise PaymentUnavailable("Razorpay is not configured")
        if not provider.verify_checkout_signature(provider_order_id=order.provider_order_id, payment_id=payload.razorpay_payment_id, signature=payload.razorpay_signature):
            raise HTTPException(400, "Payment signature is invalid")
        payment = provider.fetch_payment(payload.razorpay_payment_id)
    except PaymentUnavailable as exc:
        raise HTTPException(502, str(exc)) from exc
    if payment.get("order_id") != order.provider_order_id or payment.get("amount") != order.total_minor or payment.get("currency") != order.currency:
        raise HTTPException(400, "Payment details do not match this order")
    if payment.get("status") == "captured" and payment.get("captured") is True:
        mark_order_paid(db, order, payload.razorpay_payment_id)
        db.commit()
        return {"reference": order.public_reference, "status": order.status}
    return {"reference": order.public_reference, "status": order.status, "message": "Payment is not captured yet; waiting for verified provider confirmation."}


@app.post("/api/v1/webhooks/razorpay")
async def razorpay_webhook(request: Request, x_razorpay_signature: str | None = Header(default=None), x_razorpay_event_id: str | None = Header(default=None), db: Session = Depends(get_db)):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > 1_000_000:
        raise HTTPException(413, "Webhook payload is too large")
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 1_000_000:
            raise HTTPException(413, "Webhook payload is too large")
        chunks.append(chunk)
    raw_body = b"".join(chunks)
    if not x_razorpay_signature or not x_razorpay_event_id or len(x_razorpay_event_id) > 120:
        raise HTTPException(400, "Webhook signature and event ID are required")
    try:
        provider = configured_provider()
        if not isinstance(provider, RazorpayProvider):
            raise PaymentUnavailable("Razorpay is not configured")
        payload = provider.verify_webhook(raw_body=raw_body, signature=x_razorpay_signature)
    except PaymentUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(400, "Webhook signature or JSON is invalid") from exc
    event_type = payload.get("event")
    if not isinstance(event_type, str):
        raise HTTPException(400, "Webhook event is invalid")
    duplicate = db.scalar(select(PaymentEvent.id).where(PaymentEvent.provider_event_id == x_razorpay_event_id))
    if duplicate:
        return {"accepted": True, "duplicate": True}
    event = PaymentEvent(provider_event_id=x_razorpay_event_id, event_type=event_type, payload_sha256=hashlib.sha256(raw_body).hexdigest(), processed_at=datetime.now(timezone.utc))
    db.add(event)
    try:
        payment_entity = (payload.get("payload", {}).get("payment", {}).get("entity") or {})
        order = db.scalar(select(Order).where(Order.provider_order_id == payment_entity.get("order_id"))) if payment_entity.get("order_id") else None
        if event_type in {"payment.captured", "order.paid"}:
            captured = payment_entity.get("status") == "captured" or payment_entity.get("captured") is True
            if order and captured:
                if payment_entity.get("amount") != order.total_minor or payment_entity.get("currency") != order.currency:
                    raise HTTPException(400, "Captured payment does not match local order")
                mark_order_paid(db, order, payment_entity["id"])
        elif event_type == "payment.failed" and order and order.status not in {"paid", "refunded", "partially_refunded", "cancelled"}:
            order.status = "payment_failed"
            release_reservations(db, order, consume=False)
        elif event_type == "refund.processed":
            refund = payload.get("payload", {}).get("refund", {}).get("entity") or {}
            refunded_order = db.scalar(select(Order).where(Order.provider_payment_id == refund.get("payment_id"))) if refund.get("payment_id") else None
            if refunded_order:
                refunded_order.refunded_minor = min(refunded_order.total_minor, refunded_order.refunded_minor + int(refund.get("amount", 0)))
                refunded_order.status = "refunded" if refunded_order.refunded_minor >= refunded_order.total_minor else "partially_refunded"
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(PaymentEvent.id).where(PaymentEvent.provider_event_id == x_razorpay_event_id)):
            return {"accepted": True, "duplicate": True}
        raise HTTPException(503, "Webhook could not be durably recorded")
    except Exception:
        db.rollback()
        raise
    return {"accepted": True, "duplicate": False}


def require_admin(request: Request, db: Session) -> AdminSession:
    raw = request.cookies.get("ks_admin_session")
    if not raw:
        raise HTTPException(401, "Administrator sign-in required")
    session = db.scalar(select(AdminSession).where(AdminSession.token_sha256 == hash_token(raw), AdminSession.revoked_at.is_(None)))
    if not session:
        raise HTTPException(401, "Administrator sign-in required")
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= datetime.now(timezone.utc):
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(401, "Administrator session expired")
    return session


def require_csrf(request: Request, admin: AdminSession, csrf_header: str | None):
    csrf_cookie = request.cookies.get("ks_admin_csrf")
    if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header) or not hmac.compare_digest(hash_token(csrf_header), admin.csrf_sha256):
        raise HTTPException(403, "CSRF validation failed")


def audit(db: Session, username: str, action: str, resource_type: str, resource_id: str, details: dict):
    # Only operational metadata is recorded here; never include customer addresses or passwords.
    db.add(AdminAudit(username=username, action=action, resource_type=resource_type, resource_id=resource_id, details=json.dumps(details, sort_keys=True, separators=(",", ":"))))


@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    limit_request(request, bucket="admin_login", count=5, seconds=300)
    if not settings.admin_username or not settings.admin_password_hash:
        raise HTTPException(503, "Administrator provisioning is not configured")
    valid_user = hmac.compare_digest(payload.username, settings.admin_username)
    valid_password = verify_password(payload.password, settings.admin_password_hash)
    if not (valid_user and valid_password):
        raise HTTPException(401, "Invalid username or password")
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session = AdminSession(token_sha256=hash_token(token), csrf_sha256=hash_token(csrf), username=settings.admin_username, expires_at=now + timedelta(hours=settings.admin_session_hours))
    db.add(session)
    audit(db, settings.admin_username, "admin.login", "session", session.token_sha256[:12], {})
    db.commit()
    secure = settings.environment != "development"
    response.set_cookie("ks_admin_session", token, httponly=True, secure=secure, samesite="strict", max_age=settings.admin_session_hours * 3600, path="/api/v1/admin")
    response.set_cookie("ks_admin_csrf", csrf, httponly=False, secure=secure, samesite="strict", max_age=settings.admin_session_hours * 3600, path="/api/v1/admin")
    return {"authenticated": True, "username": settings.admin_username, "csrf_token": csrf}


@app.post("/api/v1/admin/logout")
def admin_logout(request: Request, response: Response, x_csrf_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    require_csrf(request, admin, x_csrf_token)
    admin.revoked_at = datetime.now(timezone.utc)
    audit(db, admin.username, "admin.logout", "session", str(admin.id), {})
    db.commit()
    response.delete_cookie("ks_admin_session", path="/api/v1/admin", secure=settings.environment != "development", httponly=True, samesite="strict")
    response.delete_cookie("ks_admin_csrf", path="/api/v1/admin", secure=settings.environment != "development", samesite="strict")
    return {"authenticated": False}


@app.get("/api/v1/admin/orders")
def admin_orders(request: Request, status_filter: str | None = None, search: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    require_admin(request, db)
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(422, "Invalid pagination")
    query = select(Order)
    if status_filter:
        query = query.where(Order.status == status_filter)
    if search:
        term = f"%{search[:100]}%"
        query = query.where(or_(Order.public_reference.ilike(term), Order.customer_email.ilike(term)))
    rows = db.scalars(query.order_by(Order.created_at.desc()).limit(limit).offset(offset)).all()
    return {"items": [{"reference": o.public_reference, "status": o.status, "fulfillment_status": o.fulfillment_status, "total_minor": o.total_minor, "currency": o.currency, "created_at": o.created_at} for o in rows], "limit": limit, "offset": offset}


@app.get("/api/v1/admin/orders/{reference}")
def admin_order_detail(reference: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    order = db.scalar(select(Order).where(Order.public_reference == reference).options(selectinload(Order.items)))
    if not order:
        raise HTTPException(404, "Order not found")
    return {"reference": order.public_reference, "status": order.status, "fulfillment_status": order.fulfillment_status,
            "name": order.customer_name, "email": order.customer_email, "shipping_address": order.shipping_address,
            "total_minor": order.total_minor, "refunded_minor": order.refunded_minor, "provider_payment_id": order.provider_payment_id, "currency": order.currency,
            "items": [{"product": item.product_name, "sku": item.sku, "colour": item.colour, "size": item.size, "quantity": item.quantity, "unit_price_minor": item.unit_price_minor, "line_total_minor": item.line_total_minor} for item in order.items]}


@app.patch("/api/v1/admin/orders/{reference}/fulfillment")
def admin_update_fulfillment(reference: str, payload: FulfillmentUpdate, request: Request, x_csrf_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    require_csrf(request, admin, x_csrf_token)
    order = db.scalar(select(Order).where(Order.public_reference == reference).with_for_update())
    if not order:
        raise HTTPException(404, "Order not found")
    if payload.status != order.fulfillment_status:
        allowed = {"unfulfilled": {"processing"}, "processing": {"fulfilled"}, "fulfilled": set(), "inventory_review": {"processing"}}
        if order.status != "paid" or payload.status not in allowed.get(order.fulfillment_status, set()):
            raise HTTPException(409, "Order cannot move to that fulfillment state")
        before = order.fulfillment_status
        order.fulfillment_status = payload.status
        audit(db, admin.username, "order.fulfillment.update", "order", reference, {"from": before, "to": payload.status})
        db.commit()
    return {"reference": order.public_reference, "fulfillment_status": order.fulfillment_status}


@app.get("/api/v1/admin/variants")
def admin_variants(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    variants = db.scalars(select(ProductVariant).options(selectinload(ProductVariant.product)).order_by(ProductVariant.id)).all()
    stock = {row.variant_id: row for row in db.scalars(select(InventoryRecord)).all()}
    return [{"id": v.id, "sku": v.sku, "product": v.product.name, "colour": v.colour, "size": v.size, "price_minor": v.price_minor, "active": v.active,
             "inventory_mode": stock[v.id].mode if v.id in stock else settings.inventory_mode,
             "quantity_on_hand": stock[v.id].quantity_on_hand if v.id in stock else None,
             "quantity_reserved": stock[v.id].quantity_reserved if v.id in stock else 0} for v in variants]


@app.patch("/api/v1/admin/variants/{variant_id}")
def admin_update_variant(variant_id: int, payload: VariantUpdate, request: Request, x_csrf_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    require_csrf(request, admin, x_csrf_token)
    variant = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id).with_for_update())
    if not variant:
        raise HTTPException(404, "Variant not found")
    changes = {}
    if "price_minor" in payload.model_fields_set:
        if payload.price_minor is None:
            raise HTTPException(422, "price_minor cannot be null")
        changes["price_minor"] = {"from": variant.price_minor, "to": payload.price_minor}
        variant.price_minor = payload.price_minor
    if "active" in payload.model_fields_set:
        if payload.active is None:
            raise HTTPException(422, "active cannot be null")
        changes["active"] = {"from": variant.active, "to": payload.active}
        variant.active = payload.active
    if not changes:
        raise HTTPException(422, "No variant changes supplied")
    audit(db, admin.username, "variant.update", "variant", str(variant.id), changes)
    db.commit()
    return {"id": variant.id, "price_minor": variant.price_minor, "active": variant.active}


@app.put("/api/v1/admin/variants/{variant_id}/inventory")
def admin_set_inventory(variant_id: int, payload: InventoryUpdate, request: Request, x_csrf_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    require_csrf(request, admin, x_csrf_token)
    variant = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id).with_for_update())
    if not variant:
        raise HTTPException(404, "Variant not found")
    if payload.mode == "limited" and payload.quantity_on_hand is None:
        raise HTTPException(422, "Limited inventory requires a stock quantity")
    record = db.scalar(select(InventoryRecord).where(InventoryRecord.variant_id == variant_id).with_for_update())
    old_mode = record.mode if record else settings.inventory_mode
    old_qty = record.quantity_on_hand if record else None
    if record and old_mode != payload.mode and record.quantity_reserved:
        raise HTTPException(409, "Inventory mode cannot change while quantities are reserved")
    if record and record.mode == "limited" and record.quantity_reserved > (payload.quantity_on_hand or 0) and payload.mode == "limited":
        raise HTTPException(409, "Stock cannot be set below current reservations")
    if record is None:
        record = InventoryRecord(variant_id=variant_id, mode=payload.mode, quantity_on_hand=payload.quantity_on_hand)
        db.add(record)
    else:
        record.mode = payload.mode
        record.quantity_on_hand = payload.quantity_on_hand if payload.mode == "limited" else None
    if payload.mode == "limited" and payload.quantity_on_hand != old_qty:
        delta = payload.quantity_on_hand - (old_qty or 0)
        db.add(InventoryMovement(variant_id=variant_id, quantity_delta=delta, movement_type="adjustment", actor=admin.username))
    audit(db, admin.username, "inventory.policy.update", "variant", str(variant_id), {"mode": {"from": old_mode, "to": payload.mode}, "quantity_on_hand": {"from": old_qty, "to": payload.quantity_on_hand}})
    db.commit()
    return {"variant_id": variant_id, "mode": payload.mode, "quantity_on_hand": payload.quantity_on_hand}


@app.get("/api/v1/admin/audit")
def admin_audit(request: Request, limit: int = 100, db: Session = Depends(get_db)):
    require_admin(request, db)
    if limit < 1 or limit > 500:
        raise HTTPException(422, "Invalid limit")
    rows = db.scalars(select(AdminAudit).order_by(AdminAudit.id.desc()).limit(limit)).all()
    return [{"username": row.username, "action": row.action, "resource_type": row.resource_type, "resource_id": row.resource_id, "details": json.loads(row.details), "created_at": row.created_at} for row in rows]
