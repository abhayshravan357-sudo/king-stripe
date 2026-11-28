"""Run a local Chromium storefront-to-pending-order smoke journey.

Usage: python tests/browser_checkout.py (requires Playwright and Chromium).
The script binds only to loopback and uses a disposable SQLite file in /tmp.
"""
import os
import re
import threading
import time
import urllib.request
import tempfile
import uuid
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def free_loopback_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


API_PORT = free_loopback_port()
STATIC_PORT = free_loopback_port()
while STATIC_PORT == API_PORT:
    STATIC_PORT = free_loopback_port()
BROWSER_DB = Path(tempfile.gettempdir()) / f"kingstripe-browser-test-{uuid.uuid4().hex}.sqlite"
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = f"sqlite:///{BROWSER_DB}"
os.environ["API_CORS_ORIGINS"] = f"http://localhost:{STATIC_PORT}"
os.environ["INVENTORY_MODE"] = "unlimited"
os.environ["PAYMENT_PROVIDER"] = "disabled"
os.environ["PAYMENT_MODE"] = "test"
os.environ["ALLOW_LIVE_PAYMENTS"] = "false"
os.environ["RAZORPAY_KEY_ID"] = ""
os.environ["RAZORPAY_KEY_SECRET"] = ""
os.environ["RAZORPAY_WEBHOOK_SECRET"] = ""
import sys
sys.path.insert(0, str(BACKEND))

import uvicorn
from app.core.auth import hash_password
from playwright.sync_api import sync_playwright

os.environ["ADMIN_USERNAME"] = "browser-operator"
os.environ["ADMIN_PASSWORD_HASH"] = hash_password("synthetic-browser-password")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True


def wait_for(url):
    for _ in range(50):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"Local service did not become ready: {url}")


def main():
    os.chdir(ROOT)
    api = uvicorn.Server(uvicorn.Config("app.main:app", host="127.0.0.1", port=API_PORT, log_level="warning"))
    api_thread = threading.Thread(target=api.run, daemon=True)
    api_thread.start()
    static = ReusableServer(("127.0.0.1", STATIC_PORT), lambda *a, **kw: QuietHandler(*a, directory=str(ROOT), **kw))
    static_thread = threading.Thread(target=static.serve_forever, daemon=True)
    static_thread.start()
    try:
        wait_for(f"http://127.0.0.1:{API_PORT}/health")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.add_init_script(f"window.KING_STRIPE_API = 'http://localhost:{API_PORT}'")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(f"console {message.type}: {message.text}") if message.type == "error" else None)
            page.on("requestfailed", lambda request: errors.append(f"request failed: {request.url} {request.failure}"))
            page.on("response", lambda response: errors.append(f"HTTP {response.status} {response.request.method} {response.url}") if response.request.method == "OPTIONS" or response.status >= 400 else None)
            page.goto(f"http://localhost:{STATIC_PORT}/", wait_until="networkidle")
            page.wait_for_selector('.product-card[data-product="1"]')
            page.goto(f"http://localhost:{STATIC_PORT}/collections/tiger-black/index.html", wait_until="networkidle")
            page.wait_for_selector("#collection-products .product-card")
            assert page.locator("#collection-products .product-card").count() == 6, "Live collection route did not show its products"
            page.goto(f"http://localhost:{STATIC_PORT}/", wait_until="networkidle")
            page.wait_for_selector('.product-card[data-product="1"]')
            page.locator('.filter[data-filter="Zip"]').click()
            assert page.locator(".product-card").count() == 2, "Product type filter did not update the catalog"
            page.locator("#product-sort").select_option("high")
            page.locator('.filter[data-filter="all"]').click()
            page.locator('.product-card[data-product="1"] [data-wish="1"]').click()
            assert page.locator("[data-wish-count]").first.inner_text() == "1"
            page.locator(".wishlist-trigger").click()
            assert page.locator("#wish-content .wish-row").count() == 1
            page.locator('#wish-dialog [data-close="wish-dialog"]').click()
            page.locator('.product-card[data-product="1"] [data-wish="1"]').click()
            assert page.locator("[data-wish-count]").first.inner_text() == "0"
            page.locator('.product-card[data-product="1"] .quick-view-btn').click()
            page.locator('#product-dialog [data-colour="Bone"]').click()
            page.locator('#product-dialog [data-size="M"]').click()
            page.locator('#product-dialog [data-add]').click()
            assert page.locator("[data-bag-count]").first.inner_text() == "1"
            page.reload(wait_until="networkidle")
            assert page.locator("[data-bag-count]").first.inner_text() == "1", "Bag did not persist after reload"
            page.locator(".bag-trigger").click()
            page.locator('[data-quantity][data-step="1"]').click()
            assert page.locator("[data-bag-count]").first.inner_text() == "2", "Bag quantity did not increase"
            page.locator('[data-quantity][data-step="-1"]').click()
            assert page.locator("[data-bag-count]").first.inner_text() == "1", "Bag quantity did not decrease"
            page.locator("[data-remove]").click()
            assert page.locator("[data-bag-count]").first.inner_text() == "0", "Bag item was not removed"
            page.locator('[data-close="bag-dialog"]').click()
            page.locator('.product-card[data-product="1"] .quick-view-btn').click()
            page.locator('#product-dialog [data-colour="Bone"]').click()
            page.locator('#product-dialog [data-size="M"]').click()
            page.locator('#product-dialog [data-add]').click()
            page.locator(".bag-trigger").click()
            page.locator("[data-checkout]").click()
            page.locator('#checkout-form [type="submit"]').click()
            assert not page.locator("#checkout-form").evaluate("form => form.checkValidity()"), "Empty checkout form unexpectedly passed validation"
            page.locator('#checkout-form [name="name"]').fill("Synthetic Browser Test")
            page.locator('#checkout-form [name="email"]').fill("browser-test@example.com")
            page.locator('#checkout-form [name="address"]').fill("12 Synthetic Test Road, Mumbai")
            page.locator('#checkout-form [type="submit"]').click()
            page.wait_for_function("document.querySelector('#toast').classList.contains('show') && document.querySelector('#toast').textContent.startsWith('Order ')")
            toast = page.locator("#toast").inner_text()
            match = re.search(r"Order ([A-F0-9]{32}) saved", toast)
            assert match, f"Unexpected checkout result: {toast}; browser diagnostics: {errors}"
            reference = match.group(1)
            token = page.evaluate(f"sessionStorage.getItem('ks-order:{reference}')")
            assert token, "Order token was not retained for this browser session"
            response = page.request.get(f"http://127.0.0.1:{API_PORT}/api/v1/orders/{reference}", headers={"X-Order-Token": token})
            assert response.status == 200 and response.json()["status"] == "pending_payment"
            unauthenticated_admin = page.request.get(f"http://127.0.0.1:{API_PORT}/api/v1/admin/orders")
            assert unauthenticated_admin.status == 401, "Admin orders were accessible without a session"
            assert not errors, f"Browser errors: {errors}"
            page.evaluate("document.querySelector('#toast').classList.remove('show')")
            page.screenshot(path="/tmp/kingstripe-desktop.png", full_page=True)
            for width in (320, 375, 390, 430, 768, 1366, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(100)
                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                offenders = page.evaluate("Array.from(document.querySelectorAll('*')).filter(e => { const r=e.getBoundingClientRect(); return r.right > innerWidth + 1 || r.left < -1; }).slice(0,12).map(e => ({tag:e.tagName, cls:typeof e.className==='string'?e.className:'', id:e.id, left:Math.round(e.getBoundingClientRect().left), right:Math.round(e.getBoundingClientRect().right), width:Math.round(e.getBoundingClientRect().width)}))") if overflow else []
                assert not overflow, f"Horizontal overflow at {width}px viewport: {offenders}"
            page.set_viewport_size({"width": 390, "height": 844})
            page.locator(".menu-trigger").click()
            assert page.locator(".menu-trigger").get_attribute("aria-expanded") == "true"
            assert not page.locator("#mobile-nav").is_hidden()
            page.locator('#mobile-nav a[href="#shop"]').click()
            assert page.locator(".menu-trigger").get_attribute("aria-expanded") == "false"
            page.screenshot(path="/tmp/kingstripe-mobile.png", full_page=True)
            page.goto(f"http://localhost:{STATIC_PORT}/admin.html", wait_until="networkidle")
            page.locator('#admin-login [name="username"]').fill("browser-operator")
            page.locator('#admin-login [name="password"]').fill("synthetic-browser-password")
            page.locator('#admin-login [type="submit"]').click()
            try:
                page.wait_for_function("!document.querySelector('#admin-panel').hidden", timeout=5000)
            except Exception as error:
                from app.core.config import settings
                raise AssertionError(f"Admin login failed: {page.locator('#admin-message').inner_text()}; configured origins: {settings.cors_origins}; browser diagnostics: {errors}") from error
            admin_list = page.locator("#orders-list")
            page.wait_for_selector(f'#orders-list button[data-order="{reference}"]', timeout=5000)
            assert admin_list.locator(f'button[data-order="{reference}"]').count() == 1, f"Authorized admin did not see the created order: message={page.locator('#admin-message').inner_text()} list={admin_list.inner_text()} reference={reference}"
            page.locator(f'#orders-list [data-order="{reference}"]').click()
            page.wait_for_function("document.querySelector('#order-detail').textContent.includes('Synthetic Browser Test')")
            assert "Synthetic Browser Test" in page.locator("#order-detail").inner_text()
            assert "12 Synthetic Test Road, Mumbai" in page.locator("#order-detail").inner_text()
            page.locator("#fulfillment").select_option("processing")
            page.locator("#save-fulfillment").click()
            page.wait_for_function("document.querySelector('#admin-message').textContent.includes('cannot move')")
            page.locator('[data-tab="variants"]').click()
            page.locator('.admin-inventory-form select[name="mode"]').first.select_option("limited")
            page.locator('.admin-inventory-form input[name="quantity"]').first.fill("5")
            page.locator('.admin-inventory-form button[type="submit"]').first.click()
            page.wait_for_timeout(1000)
            assert "Inventory policy saved" in page.locator("#admin-message").inner_text(), f"Inventory update failed: {page.locator('#admin-message').inner_text()}"
            for width in (320, 375, 390, 430, 768, 1366, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(100)
                assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), f"Admin page has horizontal overflow at {width}px"
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.screenshot(path="/tmp/kingstripe-admin.png", full_page=True)
            page.goto(f"http://localhost:{STATIC_PORT}/profile.html", wait_until="networkidle")
            page.locator('#profile-form [name="firstName"]').fill("Synthetic")
            page.locator('#profile-form [name="usualSize"]').select_option("M")
            page.locator('#profile-form [type="submit"]').click()
            assert "Saved on this device" in page.locator("#profile-status").inner_text()
            page.reload(wait_until="networkidle")
            assert page.locator('#profile-form [name="firstName"]').input_value() == "Synthetic"
            page.locator("#clear-profile").click()
            assert page.locator('#profile-form [name="firstName"]').input_value() == ""
            assert "cleared from this device" in page.locator("#profile-status").inner_text()
            browser.close()
        print("PASS: Chromium filters, sorting, wishlist, variants, bag persistence/quantity/removal, pending checkout, order lookup, and profile save/clear")
        print("PASS: unauthenticated admin denied; authenticated admin can view order and set variant stock policy")
        print("PASS: order fulfillment cannot advance before payment; storefront and admin have no mobile/tablet horizontal overflow")
        print("Screenshots: /tmp/kingstripe-desktop.png, /tmp/kingstripe-mobile.png, /tmp/kingstripe-admin.png")
    finally:
        static.shutdown()
        api.should_exit = True
        static.server_close()
        api_thread.join(timeout=3)
        BROWSER_DB.unlink(missing_ok=True)
        Path(f"{BROWSER_DB}-wal").unlink(missing_ok=True)
        Path(f"{BROWSER_DB}-shm").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
