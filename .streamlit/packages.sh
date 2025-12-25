#!/bin/bash

# Playwright 브라우저 설치 스크립트
echo "🔧 Installing Playwright browsers..."
python -m playwright install chromium
python -m playwright install-deps chromium
echo "✅ Playwright installation complete!"
