#!/usr/bin/env bash
# Quick start script for Glance PayOS Server
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🚀 Starting Glance PayOS Server..."
if command -v python3 &>/dev/null; then
    python3 server.py
elif command -v node &>/dev/null; then
    node server.js
else
    echo "❌ Neither python3 nor node found on PATH!"
    exit 1
fi
