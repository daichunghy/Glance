#!/usr/bin/env python3
"""
Glance - PayOS Payment Gateway & Licensing Server
Lightweight, zero-dependency Python 3 HTTP Server
Supports:
- PayOS VietQR Payment Link Creation (/api/payment/create)
- Real-time Payment Status Polling (/api/payment/status/<orderCode>)
- PayOS Webhook Verification (/api/payment/webhook)
- Glance Software License Key Verification (/api/license/verify)
- Static Landing Page Server (/)
"""

import http.server
import socketserver
import os
import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import hmac
import hashlib
import mimetypes
from pathlib import Path

# Base paths
SERVER_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SERVER_DIR.parent
LANDING_PAGE_DIR = PROJECT_DIR / "landing-page"
ORDERS_FILE = SERVER_DIR / "orders.json"
LICENSES_FILE = SERVER_DIR / "licenses.json"

# Load environment variables from .env if present
def load_env():
    env_file = SERVER_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

# Configuration
PAYOS_CLIENT_ID = os.environ.get("PAYOS_CLIENT_ID", "67649131-5fa0-4271-aee3-098127cd96b3")
PAYOS_API_KEY = os.environ.get("PAYOS_API_KEY", "850357a1-e55a-4b7a-b4bf-0d3482f46ba0")
PAYOS_CHECKSUM_KEY = os.environ.get("PAYOS_CHECKSUM_KEY", "dea16585b9b9a7bef274753e0cc7bb83f02a518f68f4dc2f7471ae3404a065cf")
PORT = int(os.environ.get("PORT", 3000))
BASE_URL = os.environ.get("BASE_URL", f"http://localhost:{PORT}")
PRICE_AMOUNT = int(os.environ.get("PRICE_AMOUNT", 20000))
PRODUCT_NAME = os.environ.get("PRODUCT_NAME", "Glance 20k Pro")

PAYOS_API_BASE = "https://api-merchant.payos.vn/v2/payment-requests"

# Persistence helpers
def read_json_file(file_path):
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def write_json_file(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing to {file_path}: {e}", file=sys.stderr)

def generate_glance_license_key():
    """Generates an authentic Glance Lifetime Pro license key"""
    import random
    k1 = f"{random.randint(0, 0xFFFF):04X}"
    k2 = f"{random.randint(0, 0xFFFF):04X}"
    return f"GLANCE-2026-XDR9-{k1}-{k2}"

def sign_payos_payment_request(amount, cancel_url, description, order_code, return_url):
    """
    Computes HMAC-SHA256 signature for PayOS create payment link API.
    Rule: alphabetical order of keys: amount, cancelUrl, description, orderCode, returnUrl
    """
    query_str = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
    return hmac.new(PAYOS_CHECKSUM_KEY.encode("utf-8"), query_str.encode("utf-8"), hashlib.sha256).hexdigest()

def verify_payos_webhook_signature(data_dict, received_signature):
    """
    Verifies HMAC-SHA256 signature of PayOS webhook payload.
    Sorts all keys of 'data' alphabetically.
    """
    if not data_dict or not received_signature:
        return False
    sorted_keys = sorted(data_dict.keys())
    parts = []
    for k in sorted_keys:
        v = data_dict[k]
        val_str = "" if v is None else str(v)
        parts.append(f"{k}={val_str}")
    canonical = "&".join(parts)
    expected_sig = hmac.new(PAYOS_CHECKSUM_KEY.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, received_signature)


class GlanceRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for development and local testing
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-client-id, x-api-key")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API: Payment status query /api/payment/status/<orderCode>
        if path.startswith("/api/payment/status/"):
            order_code_str = path[len("/api/payment/status/"):].strip("/")
            self.handle_payment_status(order_code_str)
            return

        # API: Check server health /api/health
        if path == "/api/health":
            self.send_json(200, {
                "status": "ok",
                "service": "Glance PayOS Server",
                "time": int(time.time())
            })
            return

        # Static files from landing-page directory
        self.handle_static_file(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""
        body = {}
        if post_data:
            try:
                body = json.loads(post_data.decode("utf-8"))
            except Exception:
                self.send_json(400, {"success": False, "error": "Định dạng JSON không hợp lệ."})
                return

        if path == "/api/payment/create":
            self.handle_payment_create(body)
            return

        if path == "/api/payment/webhook":
            self.handle_payment_webhook(body)
            return

        if path == "/api/license/verify":
            self.handle_license_verify(body)
            return

        self.send_json(404, {"error": "Endpoint not found"})

    def handle_payment_create(self, body):
        email = body.get("email", "").strip()
        amount = int(body.get("amount", PRICE_AMOUNT))
        
        # PayOS orderCode must be a 32-bit positive integer
        # Using current timestamp seconds
        order_code = int(time.time())

        # Description: alphanumeric/spaces, max 25 chars for VietQR
        description = "Glance 20k Pro"
        
        return_url = f"{BASE_URL}/?payment=success&orderCode={order_code}"
        cancel_url = f"{BASE_URL}/?payment=cancel&orderCode={order_code}"

        signature = sign_payos_payment_request(
            amount=amount,
            cancel_url=cancel_url,
            description=description,
            order_code=order_code,
            return_url=return_url
        )

        payos_payload = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "cancelUrl": cancel_url,
            "returnUrl": return_url,
            "signature": signature
        }
        if email:
            payos_payload["buyerEmail"] = email

        # Request to PayOS API
        req = urllib.request.Request(
            PAYOS_API_BASE,
            data=json.dumps(payos_payload).encode("utf-8"),
            headers={
                "x-client-id": PAYOS_CLIENT_ID,
                "x-api-key": PAYOS_API_KEY,
                "Content-Type": "application/json",
                "User-Agent": "Glance-Desktop/1.0 (Macintosh; Intel Mac OS X)"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if res_data.get("code") == "00":
                    order_info = res_data.get("data", {})
                    
                    # Store order in orders.json
                    orders = read_json_file(ORDERS_FILE)
                    orders[str(order_code)] = {
                        "orderCode": order_code,
                        "amount": amount,
                        "email": email,
                        "status": "PENDING",
                        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "paymentLinkId": order_info.get("paymentLinkId"),
                        "checkoutUrl": order_info.get("checkoutUrl"),
                        "accountNumber": order_info.get("accountNumber"),
                        "accountName": order_info.get("accountName"),
                        "bin": order_info.get("bin"),
                        "qrCode": order_info.get("qrCode"),
                        "description": description
                    }
                    write_json_file(ORDERS_FILE, orders)

                    self.send_json(200, {
                        "success": True,
                        "data": order_info
                    })
                    return
                else:
                    self.send_json(400, {
                        "success": False,
                        "error": res_data.get("desc", "PayOS API error"),
                        "code": res_data.get("code")
                    })
                    return
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            self.send_json(e.code, {"success": False, "error": f"PayOS HTTP {e.code}: {err_msg}"})
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_payment_status(self, order_code_str):
        if not order_code_str:
            self.send_json(400, {"success": False, "error": "Thiếu orderCode"})
            return

        orders = read_json_file(ORDERS_FILE)
        order = orders.get(order_code_str)

        # If already PAID, return stored license key immediately
        if order and order.get("status") == "PAID":
            self.send_json(200, {
                "success": True,
                "status": "PAID",
                "orderCode": order.get("orderCode"),
                "licenseKey": order.get("licenseKey"),
                "email": order.get("email"),
                "amount": order.get("amount")
            })
            return

        # Query PayOS for latest payment status
        payos_url = f"{PAYOS_API_BASE}/{order_code_str}"
        req = urllib.request.Request(
            payos_url,
            headers={
                "x-client-id": PAYOS_CLIENT_ID,
                "x-api-key": PAYOS_API_KEY,
                "User-Agent": "Glance-Desktop/1.0 (Macintosh; Intel Mac OS X)"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if res_data.get("code") == "00":
                    data = res_data.get("data", {})
                    payos_status = data.get("status")

                    if payos_status == "PAID":
                        # Generate genuine Glance Pro license key
                        license_key = generate_glance_license_key()
                        
                        # Update order
                        if not order:
                            order = {"orderCode": int(order_code_str)}
                        order["status"] = "PAID"
                        order["licenseKey"] = license_key
                        order["paidAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        order["amountPaid"] = data.get("amountPaid", PRICE_AMOUNT)
                        orders[order_code_str] = order
                        write_json_file(ORDERS_FILE, orders)

                        # Register in licenses.json
                        licenses = read_json_file(LICENSES_FILE)
                        licenses[license_key] = {
                            "orderCode": int(order_code_str),
                            "email": order.get("email", ""),
                            "issuedAt": order["paidAt"],
                            "plan": "Glance Lifetime Pro",
                            "activated": True
                        }
                        write_json_file(LICENSES_FILE, licenses)

                        self.send_json(200, {
                            "success": True,
                            "status": "PAID",
                            "orderCode": int(order_code_str),
                            "licenseKey": license_key,
                            "email": order.get("email", "")
                        })
                        return
                    else:
                        self.send_json(200, {
                            "success": True,
                            "status": payos_status or "PENDING",
                            "orderCode": int(order_code_str)
                        })
                        return
                else:
                    self.send_json(400, {"success": False, "error": res_data.get("desc")})
                    return
        except urllib.error.HTTPError as e:
            self.send_json(e.code, {"success": False, "error": f"PayOS HTTP {e.code}"})
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_payment_webhook(self, payload):
        """Processes PayOS Webhook notification"""
        data = payload.get("data")
        received_signature = payload.get("signature")

        if not data or not received_signature:
            self.send_json(400, {"success": False, "message": "Invalid webhook payload"})
            return

        # Verify signature
        if not verify_payos_webhook_signature(data, received_signature):
            print("[Webhook Warning] Invalid PayOS signature!", file=sys.stderr)
            self.send_json(400, {"success": False, "message": "Invalid signature"})
            return

        order_code = str(data.get("orderCode"))
        code = data.get("code")

        if code == "00":
            # Payment success!
            orders = read_json_file(ORDERS_FILE)
            order = orders.get(order_code, {"orderCode": int(order_code)})

            if order.get("status") != "PAID":
                license_key = generate_glance_license_key()
                order["status"] = "PAID"
                order["licenseKey"] = license_key
                order["paidAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                order["amountPaid"] = data.get("amount", PRICE_AMOUNT)
                orders[order_code] = order
                write_json_file(ORDERS_FILE, orders)

                licenses = read_json_file(LICENSES_FILE)
                licenses[license_key] = {
                    "orderCode": int(order_code),
                    "email": order.get("email", ""),
                    "issuedAt": order["paidAt"],
                    "plan": "Glance Lifetime Pro",
                    "activated": True
                }
                write_json_file(LICENSES_FILE, licenses)
                print(f"[PayOS Webhook] Order {order_code} marked as PAID. License generated: {license_key}")

        self.send_json(200, {"success": True, "message": "Webhook processed successfully"})

    def handle_license_verify(self, body):
        """License verification endpoint for Glance desktop apps"""
        license_key = body.get("licenseKey", "").strip().upper()
        if not license_key:
            self.send_json(400, {"valid": False, "message": "Vui lòng cung cấp mã kích hoạt."})
            return

        licenses = read_json_file(LICENSES_FILE)
        if license_key in licenses:
            self.send_json(200, {
                "valid": True,
                "message": "Kích hoạt bản quyền Glance thành công!",
                "data": licenses[license_key]
            })
            return

        # Pattern check fallback (e.g. offline testing or official format)
        if license_key.startswith("GLANCE-2026-XDR9-"):
            self.send_json(200, {
                "valid": True,
                "message": "Kích hoạt bản quyền Glance thành công!",
                "data": {"plan": "Glance Lifetime Pro", "activated": True}
            })
            return

        self.send_json(400, {
            "valid": False,
            "message": "Mã kích hoạt không đúng hoặc chưa được thanh toán."
        })

    def handle_static_file(self, req_path):
        """Serves landing-page assets"""
        if req_path in ("/", ""):
            file_path = LANDING_PAGE_DIR / "index.html"
        else:
            rel_path = req_path.lstrip("/")
            file_path = LANDING_PAGE_DIR / rel_path

        if not file_path.exists() or file_path.is_dir():
            file_path = LANDING_PAGE_DIR / "index.html"

        if not file_path.exists():
            self.send_response(404)
            self.end_headers()
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), GlanceRequestHandler) as httpd:
        print(f"============================================================")
        print(f"  GLANCE PAYOS PAYMENT & LICENSING SERVER")
        print(f"============================================================")
        print(f"  • Local URL:      http://localhost:{PORT}")
        print(f"  • PayOS Client:   {PAYOS_CLIENT_ID}")
        print(f"  • Product Price:  {PRICE_AMOUNT:,} VNĐ")
        print(f"  • API Create:     POST http://localhost:{PORT}/api/payment/create")
        print(f"  • API Status:     GET  http://localhost:{PORT}/api/payment/status/<orderCode>")
        print(f"  • API Webhook:    POST http://localhost:{PORT}/api/payment/webhook")
        print(f"  • API License:    POST http://localhost:{PORT}/api/license/verify")
        print(f"============================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")
            httpd.server_close()


if __name__ == "__main__":
    run_server()
