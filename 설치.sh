#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " 네이버 플레이스 크롤링 앱 - 맥/리눅스 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "[1/4] Python 버전 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다!"
    echo "👉 https://python.org 에서 Python을 다운로드하세요."
    exit 1
fi
python3 --version
echo "✅ Python 설치 확인 완료"
echo ""

echo "[2/4] Flask 설치 중..."
pip3 install flask
if [ $? -ne 0 ]; then
    echo "❌ Flask 설치 실패"
    exit 1
fi
echo "✅ Flask 설치 완료"
echo ""

echo "[3/4] Playwright 설치 중..."
pip3 install playwright
if [ $? -ne 0 ]; then
    echo "❌ Playwright 설치 실패"
    exit 1
fi
echo "✅ Playwright 설치 완료"
echo ""

echo "[4/4] Chromium 브라우저 설치 중... (약 1-2분 소요)"
playwright install chromium
if [ $? -ne 0 ]; then
    echo "❌ Chromium 설치 실패"
    echo ""
    echo "리눅스의 경우 다음 명령어를 먼저 실행해주세요:"
    echo "sudo apt-get update"
    echo "sudo apt-get install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2"
    exit 1
fi
echo "✅ Chromium 설치 완료"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " 🎉 설치 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "앱을 실행하려면:"
echo "  ./실행.sh"
echo ""
echo "또는:"
echo "  python3 naver_map_crawler.py"
echo ""
