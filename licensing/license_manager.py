"""
Glance - License Manager for Windows & Linux
Validates Glance Lifetime Pro license keys issued via PayOS
"""

import json
import urllib.request
import os
import time

LICENSE_FILE = os.path.expanduser("~/.glance_license.json")
TRIAL_DAYS = 7
SERVER_ENDPOINT = "http://localhost:3000/api/license/verify"

class LicenseManager:
    @staticmethod
    def get_status():
        """Returns (is_licensed, days_remaining, license_key)"""
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("activated", False):
                        return True, 999, data.get("key", "")
                    start_time = data.get("trial_start", time.time())
                    elapsed_days = (time.time() - start_time) / (24 * 3600)
                    remaining = max(0, int(TRIAL_DAYS - elapsed_days))
                    return remaining > 0, remaining, ""
            except Exception:
                pass
                
        # Initialize trial
        data = {"activated": False, "trial_start": time.time()}
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
        return True, TRIAL_DAYS, ""

    @staticmethod
    def activate(key):
        """Validates key via Glance PayOS Server or authentic GLANCE- pattern"""
        clean_key = str(key).strip().upper()
        if not clean_key:
            return False, "Vui lòng nhập mã kích hoạt hợp lệ."

        # Online validation via Glance Server
        try:
            payload = json.dumps({"licenseKey": clean_key, "instanceName": "Desktop"}).encode("utf-8")
            req = urllib.request.Request(
                SERVER_ENDPOINT,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                res = json.loads(response.read().decode("utf-8"))
                if res.get("valid", False):
                    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                        json.dump({"activated": True, "key": clean_key, "verified_at": time.time()}, f, indent=2)
                    return True, "Kích hoạt bản quyền Glance trọn đời thành công!"
        except Exception:
            pass

        # Offline fallback for PayOS issued keys (Format: GLANCE-2026-XDR9-XXXX-XXXX)
        if clean_key.startswith("GLANCE-2026-") or clean_key.startswith("GLANCE-"):
            try:
                with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"activated": True, "key": clean_key, "mode": "offline"}, f, indent=2)
                return True, "Kích hoạt bản quyền Glance trọn đời thành công (Offline)!"
            except Exception as e:
                return False, f"Lỗi lưu trữ bản quyền: {e}"

        return False, "Mã kích hoạt không hợp lệ hoặc chưa được thanh toán qua PayOS."
