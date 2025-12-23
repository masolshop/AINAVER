@echo off
chcp 65001 > nul
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  네이버 플레이스 크롤링 앱 - 윈도우 설치
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo [1/4] Python 버전 확인 중...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다!
    echo 👉 https://python.org 에서 Python을 다운로드하세요.
    pause
    exit /b 1
)
echo ✅ Python 설치 확인 완료
echo.

echo [2/4] Flask 설치 중...
pip install flask
if %errorlevel% neq 0 (
    echo ❌ Flask 설치 실패
    pause
    exit /b 1
)
echo ✅ Flask 설치 완료
echo.

echo [3/4] Playwright 설치 중...
pip install playwright
if %errorlevel% neq 0 (
    echo ❌ Playwright 설치 실패
    pause
    exit /b 1
)
echo ✅ Playwright 설치 완료
echo.

echo [4/4] Chromium 브라우저 설치 중... (약 1-2분 소요)
playwright install chromium
if %errorlevel% neq 0 (
    echo ❌ Chromium 설치 실패
    pause
    exit /b 1
)
echo ✅ Chromium 설치 완료
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  🎉 설치 완료!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 앱을 실행하려면:
echo   실행.bat 파일을 더블클릭하세요
echo.
echo 또는 명령 프롬프트에서:
echo   python naver_map_crawler.py
echo.
pause
