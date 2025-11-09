#!/bin/bash
set -e

echo "🔧 Installing system dependencies..."
apt-get update
apt-get install -y nmap

echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "✅ Build complete!"
