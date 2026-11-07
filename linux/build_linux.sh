#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=== Building Glance for Linux ==="

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "[Lỗi] Không tìm thấy python3 trên hệ thống."
    exit 1
fi

# Use virtual environment to prevent PEP 668 externally-managed-environment errors
if [ ! -d ".venv" ]; then
    echo "[Glance] Đang tạo môi trường ảo .venv..."
    python3 -m venv .venv
fi

echo "[Glance] Đang cài đặt thư viện phụ thuộc..."
.venv/bin/pip install -r requirements.txt

echo "[Glance] Đang đóng gói binary độc lập..."
.venv/bin/python -m PyInstaller --noconfirm --clean --collect-data cv2 --onefile --name Glance glance_linux.py

echo "Build complete! Binary at: dist/Glance"
