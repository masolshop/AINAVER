"""
Playwright 브라우저 자동 설치 스크립트
Streamlit Cloud 시작 시 자동 실행
"""
import subprocess
import sys
import os

def install_playwright_browsers():
    """Playwright Chromium 브라우저 설치"""
    try:
        print("🔧 Playwright 브라우저 설치 중...")
        
        # Playwright install
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Playwright Chromium 설치 완료!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 설치 실패: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    install_playwright_browsers()
