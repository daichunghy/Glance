#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=== Building Glance for Linux ==="
python3 -m pip install -r requirements.txt

python3 -m PyInstaller --collect-data cv2 --onefile --name Glance glance_linux.py

echo "Build complete! Binary at: dist/Glance"
