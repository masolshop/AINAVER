#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 크롤링 v4.3 - Google Colab 올인원 버전
이 파일을 Colab의 한 셀에 전체 복사해서 실행하세요!
"""

# ==================== 패키지 설치 ====================
print("📦 패키지 설치 중...")
import subprocess
import sys

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "playwright", "pyngrok", "nest-asyncio"], check=True)
subprocess.run(["playwright", "install", "chromium"], check=True)
subprocess.run(["playwright", "install-deps", "chromium"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("✅ 설치 완료!\n")

# ==================== 크롤러 클래스 ====================
from playwright.sync_api import sync_playwright
import time
import re
from urllib.parse import quote

class NaverPlaceCrawler:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    def start(self):
        print("🌐 브라우저 시작 중...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        self.page = self.browser.new_page()
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        print("✅ 브라우저 준비 완료\n")
        return True
    
    def search_places(self, keyword, max_results=20):
        if not self.page:
            self.start()
        
        try:
            print(f"🔍 '{keyword}' 검색 중...")
            url = f"https://map.naver.com/p/search/{quote(keyword)}"
            self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
            time.sleep(3)
            
            iframe = self.page.frame(name="searchIframe")
            if not iframe:
                print("❌ searchIframe을 찾을 수 없습니다")
                return []
            
            time.sleep(2)
            
            # 스크롤
            for i in range(5):
                iframe.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.8)
            
            # 아이템 찾기
            items = []
            for selector in ['li[role="listitem"]', 'li.UEzoS', 'ul._2py9K li']:
                items = iframe.query_selector_all(selector)
                if items:
                    print(f"✅ {len(items)}개 발견\n")
                    break
            
            if not items:
                print("❌ 검색 결과 없음")
                return []
            
            results = []
            addr_count = 0
            
            for idx, item in enumerate(items[:max_results]):
                try:
                    # 업체명
                    name = self._get_text(item, ['.TYaxT', '.place_bluelink', '.YwYLL'])
                    if not name:
                        continue
                    
                    # 주소 (15개 셀렉터)
                    addr = self._get_text(item, [
                        '.LDgIH', '.addr', 'span.place_addr', '.Osdwn',
                        'div.addr', '.v7Sqg', '[class*="addr"]',
                        'span[class*="addr"]', 'div[class*="addr"]',
                        '.place_address', 'span.address', 'div.address',
                        'div[class*="address"]', 'span[class*="location"]',
                        'div[class*="location"]'
                    ])
                    
                    # 정규식 매칭
                    if not addr:
                        html = item.inner_html()
                        for pattern in [
                            r'([가-힣]+(?:특별시|광역시|시|도)\s+[가-힣]+(?:구|군|시)\s+[가-힣0-9\s\-]+)',
                            r'(서울[^<>]+?(?:동|로|가|길)\s*\d*)',
                            r'(경기[^<>]+?(?:동|로|가|길)\s*\d*)',
                            r'(부산[^<>]+?(?:동|로|가|길)\s*\d*)',
                            r'([가-힣]+구\s+[가-힣]+동\s+\d+)',
                        ]:
                            match = re.search(pattern, html)
                            if match:
                                addr = match.group(1).strip()
                                break
                    
                    if addr and addr != "주소 정보 없음":
                        addr_count += 1
                    
                    # 나머지 정보
                    phone = self._get_text(item, ['.dry6Z', '.tel', '[class*="tel"]'])
                    rating = self._get_text(item, ['.h69bs', '.score'])
                    reviews = self._get_text(item, ['.Tvqnp', '.cnt'])
                    reviews = re.sub(r'[^0-9]', '', reviews) if reviews else "0"
                    category = self._get_text(item, ['.YzBgS', '.category'])
                    
                    is_other = self._is_other_region(name, addr, phone, rating, keyword)
                    
                    results.append({
                        'name': name,
                        'category': category if category else "미분류",
                        'address': addr if addr else "주소 정보 없음",
                        'phone': phone if phone else "전화번호 없음",
                        'rating': rating if rating else "",
                        'reviews': reviews,
                        'is_other_region': is_other,
                        'place_type': '타지역업체' if is_other else '주업체'
                    })
                    
                    # 진행 상황
                    icon = "🟠" if is_other else "🟢"
                    addr_display = (addr[:30] + "...") if addr else "❌없음"
                    print(f"  {icon} [{idx+1:2d}] {name[:20]:20s} | {addr_display}")
                    
                except Exception as e:
                    continue
            
            total = len(results)
            addr_rate = (addr_count / total * 100) if total > 0 else 0
            
            print(f"\n{'='*60}")
            print(f"✅ {total}개 수집 | 주소: {addr_count}/{total} ({addr_rate:.0f}%)")
            print(f"{'='*60}\n")
            
            return results
            
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            return []
    
    def _get_text(self, parent, selectors):
        for sel in selectors:
            try:
                el = parent.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if text:
                        return text
            except:
                pass
        return ""
    
    def _is_other_region(self, name, addr, phone, rating, keyword):
        score = 0
        if phone and '070' in phone:
            score += 3
        if addr and addr != "주소 정보 없음":
            if len(addr.split()) <= 3 or addr.endswith(('동', '구', '시')):
                score += 2
        if not addr or addr == "주소 정보 없음":
            score += 2
        if not rating:
            score += 1
        if name and keyword:
            words = [w for w in keyword.split() if len(w) > 1]
            if any(w in name for w in words):
                score += 2
        return score >= 4
    
    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass

# ==================== Flask 웹 서버 ====================
import nest_asyncio
from flask import Flask, request, jsonify, Response
import threading
import io
import csv
from datetime import datetime

nest_asyncio.apply()

app = Flask(__name__)
crawler = None

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>네이버 플레이스 v4.3</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white;
            border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 40px; text-align: center;
        }
        h1 { font-size: 2em; }
        .content { padding: 40px; }
        .search-box { display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 15px; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; }
        button { padding: 15px 30px; background: #667eea; color: white; border: none; border-radius: 10px; cursor: pointer; }
        button:hover { background: #5568d3; }
        .results { margin-top: 30px; }
        .place-card { border: 2px solid #e0e0e0; padding: 20px; margin: 15px 0; border-radius: 12px; }
        .place-card.other { border-color: #ff9800; background: #fff3e0; }
        .badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 0.85em; margin-left: 10px; }
        .badge.main { background: #4caf50; color: white; }
        .badge.other { background: #ff9800; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ 네이버 플레이스 v4.3</h1>
            <p>주소 수집 강화 | CSV 다운로드</p>
        </div>
        <div class="content">
            <div class="search-box">
                <input type="text" id="keyword" placeholder="검색어 입력 (예: 강남역 맛집)">
                <button onclick="search()">🔍 검색</button>
                <button onclick="downloadCSV()" id="btnDownload" style="display:none; background:#11998e">📥 CSV</button>
            </div>
            <div id="results" class="results"></div>
        </div>
    </div>
    <script>
        let currentResults = [];
        let currentKeyword = '';
        
        async function search() {
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) { alert('검색어를 입력하세요'); return; }
            
            document.getElementById('results').innerHTML = '⏳ 검색 중...';
            document.getElementById('btnDownload').style.display = 'none';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword, max_results: 20 })
                });
                const data = await response.json();
                
                if (data.success) {
                    currentResults = data.results;
                    currentKeyword = keyword;
                    
                    const html = data.results.map((p, i) => {
                        const cls = p.is_other_region ? 'place-card other' : 'place-card';
                        const badge = p.is_other_region ? '<span class="badge other">🟠 타지역</span>' : '<span class="badge main">🟢 주업체</span>';
                        return `
                            <div class="${cls}">
                                <strong>[${i+1}] ${p.name}</strong>${badge}<br><br>
                                📍 ${p.address}<br>
                                📞 ${p.phone}<br>
                                ${p.rating ? '⭐ ' + p.rating + ' (' + p.reviews + '개)' : ''}
                            </div>
                        `;
                    }).join('');
                    
                    document.getElementById('results').innerHTML = html;
                    document.getElementById('btnDownload').style.display = 'inline-block';
                } else {
                    document.getElementById('results').innerHTML = '❌ ' + data.error;
                }
            } catch (error) {
                document.getElementById('results').innerHTML = '❌ ' + error.message;
            }
        }
        
        async function downloadCSV() {
            const response = await fetch('/api/download-csv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ results: currentResults, keyword: currentKeyword })
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `naver_${currentKeyword}_${Date.now()}.csv`;
            a.click();
        }
        
        document.getElementById('keyword').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') search();
        });
    </script>
</body>
</html>'''

@app.route('/api/search', methods=['POST'])
def api_search():
    global crawler
    data = request.json
    keyword = data.get('keyword', '')
    
    if not crawler:
        crawler = NaverPlaceCrawler()
        crawler.start()
    
    results = crawler.search_places(keyword, data.get('max_results', 20))
    return jsonify({'success': True, 'results': results})

@app.route('/api/download-csv', methods=['POST'])
def download_csv():
    data = request.json
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['name', 'category', 'address', 'phone', 'rating', 'reviews', 'place_type'])
    writer.writeheader()
    writer.writerows(data.get('results', []))
    return Response(output.getvalue().encode('utf-8-sig'), mimetype='text/csv')

# ==================== 서버 시작 ====================
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

print("🚀 Flask 서버 시작 중...\n")
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

time.sleep(2)

# ==================== ngrok 터널 ====================
print("🌐 ngrok 터널 생성 중...\n")

try:
    from pyngrok import ngrok
    
    # 기존 터널 종료
    ngrok.kill()
    time.sleep(1)
    
    # 새 터널 생성
    public_url = ngrok.connect(5000, bind_tls=True)
    
    # URL 추출
    if isinstance(public_url, str):
        url = public_url
    else:
        url = str(public_url)
    
    print("="*70)
    print("✅ v4.3 서버 시작 완료!")
    print("="*70)
    print()
    print(f"🌐 접속 URL: {url}")
    print()
    print("💡 위 URL을 클릭하세요!")
    print()
    print("🧪 테스트 검색어: 강남역 맛집, 홍대 카페, 스타벅스")
    print()
    print("="*70)
    print()
    
except Exception as e:
    print(f"❌ ngrok 오류: {e}")
    print("\n💡 해결 방법:")
    print("1. ngrok.com에서 무료 토큰 받기")
    print("2. 코드 상단에 추가:")
    print("   from pyngrok import ngrok")
    print("   ngrok.set_auth_token('여기에_토큰_붙여넣기')")

# ==================== 서버 유지 ====================
print("\n⚠️  Colab 셀을 중지하면 서버도 종료됩니다")
print("⚠️  이 셀을 계속 실행 상태로 유지하세요\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    if crawler:
        crawler.close()
    print("\n✅ 서버 종료")
