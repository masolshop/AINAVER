#!/bin/bash

echo "🚀 네이버 크롤러 배포 시작..."

# 최신 코드 가져오기
echo "📥 Git Pull..."
git pull origin main

# 기존 컨테이너 중지 및 제거
echo "🛑 기존 컨테이너 중지..."
docker-compose down

# 이미지 빌드
echo "🔨 Docker 이미지 빌드..."
docker-compose build --no-cache

# 컨테이너 실행
echo "▶️  컨테이너 실행..."
docker-compose up -d

# 로그 확인
echo "📋 컨테이너 로그 (Ctrl+C로 종료)..."
sleep 5
docker-compose logs -f --tail=50
