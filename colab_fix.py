# ngrok URL 제대로 출력하는 수정된 코드

import nest_asyncio
from pyngrok import ngrok
import threading
import time

# Flask 서버를 별도 스레드에서 실행
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ngrok 터널 생성
print("🚀 서버 시작 중...")
print("")

# Flask 서버 먼저 시작
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# 서버가 시작될 때까지 대기
time.sleep(3)

# ngrok 터널 생성
tunnel = ngrok.connect(5000)
public_url = tunnel.public_url

print("=" * 70)
print("✅ 서버가 시작되었습니다!")
print("=" * 70)
print("")
print(f"🌐 접속 URL: {public_url}")
print("")
print("💡 위 URL을 클릭하거나 복사해서 브라우저에서 열어주세요!")
print("")
print("⚠️  주의: 이 셀이 실행 중일 때만 접속 가능합니다.")
print("")
print("=" * 70)
print("")

# 서버 유지
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n서버 종료")
    ngrok.disconnect(public_url)
    if crawler:
        crawler.close()
