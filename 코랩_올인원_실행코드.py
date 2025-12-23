# ============================================================
# 🗺️ 네이버 플레이스 크롤링 v3 - 구글 코랩 올인원 코드
# ============================================================
# 이 코드를 구글 코랩의 한 셀에 복사-붙여넣기하여 실행하세요
# ============================================================

# 1️⃣ 패키지 설치 (첫 실행 시에만 필요)
print("📦 패키지 설치 중...")
import subprocess
import sys

def install_packages():
    packages = [
        "flask",
        "playwright",
        "pyngrok",
        "nest-asyncio"
    ]
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
    
    # Playwright 브라우저 설치
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install-deps", "chromium"])
    print("✅ 모든 패키지 설치 완료!\n")

# 패키지 설치 (주석 해제하여 사용)
install_packages()

# 2️⃣ 크롤링 모듈 작성
print("🤖 크롤링 모듈 생성 중...")

crawler_code = '''
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
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            print("✅ 브라우저 시작")
            return True
        except Exception as e:
            print(f"❌ 브라우저 오류: {e}")
            return False
    
    def search_places(self, keyword, max_results=20):
        if not self.page:
            self.start()
        
        try:
            print(f"🔍 '{keyword}' 검색 중...")
            
            url = f"https://map.naver.com/p/search/{quote(keyword)}"
            self.page.goto(url, timeout=15000, wait_until="domcontentloaded")
            time.sleep(3)
            
            iframe = self.page.frame(name="searchIframe")
            if not iframe:
                print("❌ searchIframe을 찾을 수 없습니다")
                return []
            
            time.sleep(2)
            
            # 스크롤로 더 많은 결과 로드
            for _ in range(3):
                iframe.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            
            results = []
            
            # 다양한 리스트 아이템 셀렉터 시도
            item_selectors = [
                'li[role="listitem"]',
                'li.UEzoS',
                'li.place_item',
                'ul._2py9K li',
                'div.CHC5F'
            ]
            
            items = []
            for selector in item_selectors:
                items = iframe.query_selector_all(selector)
                if items:
                    print(f"✅ 셀렉터 '{selector}'로 {len(items)}개 발견")
                    break
            
            if not items:
                print("❌ 검색 결과를 찾을 수 없습니다")
                return []
            
            for idx, item in enumerate(items[:max_results]):
                try:
                    # 업체명
                    name_selectors = ['.TYaxT', '.place_bluelink', '.YwYLL', 'a.place_bluelink']
                    name_text = self._get_text_by_selectors(item, name_selectors)
                    if not name_text:
                        continue
                    
                    # 주소 - 여러 셀렉터 + 패턴 매칭
                    addr_selectors = [
                        '.LDgIH', '.addr', 'span.place_addr', '.Osdwn', 
                        'div.addr', '.v7Sqg', '[class*="addr"]',
                        'span[class*="addr"]', 'div[class*="addr"]'
                    ]
                    addr_text = self._get_text_by_selectors(item, addr_selectors)
                    
                    # 주소를 못 찾으면 HTML 패턴 검색
                    if not addr_text:
                        item_html = item.inner_html()
                        addr_patterns = [
                            r'([가-힣]+(?:시|도)\\s+[가-힣]+(?:구|군|시)\\s+[가-힣\\s]+)',
                            r'(서울[^<>]+?동)', r'(경기[^<>]+?동)', r'(부산[^<>]+?동)'
                        ]
                        for pattern in addr_patterns:
                            match = re.search(pattern, item_html)
                            if match:
                                addr_text = match.group(1).strip()
                                break
                    
                    # 전화번호
                    phone_selectors = [
                        '.dry6Z', '.tel', 'span.place_tel', 
                        '.xlx7Q', '[class*="tel"]', 'span[class*="tel"]'
                    ]
                    phone_text = self._get_text_by_selectors(item, phone_selectors)
                    
                    # 전화번호 패턴 검색
                    if not phone_text:
                        item_html = item.inner_html()
                        phone_match = re.search(r'(0\\d{1,2}[-\\s]?\\d{3,4}[-\\s]?\\d{4}|070[-\\s]?\\d{3,4}[-\\s]?\\d{4})', item_html)
                        if phone_match:
                            phone_text = phone_match.group(1)
                    
                    # 평점
                    rating_selectors = ['.h69bs', '.score', 'span.place_score', '.PXMot', '[class*="score"]']
                    rating_text = self._get_text_by_selectors(item, rating_selectors)
                    
                    # 리뷰 수
                    reviews_selectors = ['.Tvqnp', '.cnt', 'span.place_review', '.YrbVX', '[class*="review"]']
                    reviews_el = self._get_element_by_selectors(item, reviews_selectors)
                    reviews_text = "0"
                    if reviews_el:
                        reviews_raw = reviews_el.inner_text()
                        reviews_text = re.sub(r'[^0-9]', '', reviews_raw) if reviews_raw else "0"
                    
                    # 타지역업체 판단
                    is_other = self._is_other_region(name_text, addr_text, phone_text, rating_text, keyword)
                    
                    results.append({
                        'name': name_text,
                        'address': addr_text if addr_text else "주소 정보 없음",
                        'phone': phone_text if phone_text else "전화번호 없음",
                        'rating': rating_text if rating_text else "",
                        'reviews': reviews_text,
                        'is_other_region': is_other,
                        'place_type': '타지역업체' if is_other else '주업체'
                    })
                    
                    print(f"  [{idx+1}] {name_text[:20]}... | 주소: {(addr_text if addr_text else '없음')[:30]}...")
                    
                except Exception as e:
                    print(f"⚠️ 항목 [{idx+1}] 파싱 오류: {e}")
                    continue
            
            print(f"✅ 총 {len(results)}개 수집 완료")
            return results
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_element_by_selectors(self, parent, selectors):
        for selector in selectors:
            try:
                el = parent.query_selector(selector)
                if el:
                    return el
            except:
                continue
        return None
    
    def _get_text_by_selectors(self, parent, selectors):
        el = self._get_element_by_selectors(parent, selectors)
        if el:
            try:
                text = el.inner_text().strip()
                return text if text else ""
            except:
                return ""
        return ""
    
    def _is_other_region(self, name, address, phone, rating, keyword):
        score = 0
        if phone and phone.startswith('070'): score += 3
        if address and len(address.split()) <= 3: score += 2
        if not rating: score += 1
        if name and keyword:
            keyword_words = [w for w in keyword.split() if len(w) > 1]
            if any(w in name for w in keyword_words): score += 2
        return score >= 4
    
    def close(self):
        try:
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()
        except:
            pass
'''

# 크롤러 모듈을 파일로 저장
with open('naver_crawler.py', 'w', encoding='utf-8') as f:
    f.write(crawler_code)

print("✅ 크롤링 모듈 생성 완료!\n")

# 3️⃣ Flask 웹 앱 실행
print("🚀 Flask 웹 앱 시작 중...\n")

import nest_asyncio
from pyngrok import ngrok
from flask import Flask, request, jsonify
import threading
import time
from naver_crawler import NaverPlaceCrawler

nest_asyncio.apply()

app = Flask(__name__)
crawler = None

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>네이버 플레이스 크롤링 v3</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .badge-version { 
            display: inline-block;
            background: rgba(255,255,255,0.3);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.6em;
            margin-left: 10px;
        }
        .content { padding: 40px; }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        input {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
        }
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102,126,234,0.4); }
        .loading { display: none; text-align: center; padding: 20px; font-size: 18px; color: #667eea; }
        .loading.active { display: block; }
        .results { margin-top: 30px; }
        .place-card {
            border: 2px solid #e0e0e0;
            padding: 20px;
            margin: 15px 0;
            border-radius: 12px;
            transition: all 0.3s;
        }
        .place-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        .place-card.other { border-color: #ff9800; background: #fff3e0; }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }
        .badge.main { background: #4caf50; color: white; }
        .badge.other { background: #ff9800; color: white; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 { font-size: 2em; margin-bottom: 5px; }
        .stat-card.warning { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .info-section {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .info-section h3 { margin-bottom: 10px; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ 네이버 플레이스 크롤링<span class="badge-version">v3 개선됨</span></h1>
            <p>실제 네이버 데이터 크롤링 + 타지역업체 자동 감지 + 주소 수집 강화</p>
        </div>
        <div class="content">
            <div class="info-section">
                <h3>🎯 v3 개선 사항</h3>
                <p>✅ 여러 CSS 셀렉터 시도로 주소 수집률 향상<br>
                ✅ 정규표현식 패턴 매칭으로 주소 추가 탐지<br>
                ✅ 전화번호도 패턴 매칭으로 추가 수집</p>
            </div>
            <div class="search-box">
                <input type="text" id="keyword" placeholder="검색어 입력 (예: 강남역 맛집, 선불폰, 하수구역빌)">
                <button onclick="search()">🔍 검색</button>
            </div>
            <div class="loading" id="loading">⏳ 검색 중... 잠시만 기다려주세요</div>
            <div id="stats"></div>
            <div id="results" class="results"></div>
        </div>
    </div>
    <script>
        async function search() {
            const keyword = document.getElementById('keyword').value.trim();
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const stats = document.getElementById('stats');
            
            if (!keyword) {
                alert('검색어를 입력하세요');
                return;
            }
            
            loading.classList.add('active');
            results.innerHTML = '';
            stats.innerHTML = '';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword, max_results: 20 })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const total = data.results.length;
                    const other = data.results.filter(p => p.is_other_region).length;
                    const main = total - other;
                    const withAddr = data.results.filter(p => p.address && p.address !== '주소 정보 없음').length;
                    
                    stats.innerHTML = `
                        <div class="stats">
                            <div class="stat-card"><h3>${total}</h3><p>총 결과</p></div>
                            <div class="stat-card"><h3>${main}</h3><p>주업체</p></div>
                            <div class="stat-card warning"><h3>${other}</h3><p>타지역업체</p></div>
                            <div class="stat-card"><h3>${withAddr}</h3><p>주소 수집</p></div>
                        </div>
                    `;
                    
                    results.innerHTML = data.results.map((place, idx) => {
                        const className = place.is_other_region ? 'place-card other' : 'place-card';
                        const badgeClass = place.is_other_region ? 'badge other' : 'badge main';
                        const badgeText = place.is_other_region ? '🟠 타지역업체' : '🟢 주업체';
                        
                        return `
                            <div class="${className}">
                                <strong style="font-size: 1.2em;">[${idx+1}] ${place.name}</strong>
                                <span class="${badgeClass}">${badgeText}</span><br><br>
                                📍 <strong>주소:</strong> ${place.address}<br>
                                📞 <strong>전화:</strong> ${place.phone}<br>
                                ${place.rating ? `⭐ ${place.rating} (리뷰 ${place.reviews}개)` : '평점 없음'}
                            </div>
                        `;
                    }).join('');
                } else {
                    results.innerHTML = `<p style="color: red;">오류: ${data.error}</p>`;
                }
            } catch (error) {
                results.innerHTML = `<p style="color: red;">오류: ${error.message}</p>`;
            } finally {
                loading.classList.remove('active');
            }
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
    try:
        data = request.json
        keyword = data.get('keyword', '')
        max_results = int(data.get('max_results', 20))
        
        if not keyword:
            return jsonify({'success': False, 'error': '검색어를 입력하세요'})
        
        if crawler is None:
            crawler = NaverPlaceCrawler()
            crawler.start()
        
        results = crawler.search_places(keyword, max_results)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# Flask 서버 시작
print("🚀 서버 시작 중...\n")
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# 서버 시작 대기
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
print("📝 v3 개선 사항:")
print("  - 여러 CSS 셀렉터로 주소 수집 시도")
print("  - 정규식 패턴 매칭으로 주소 추가 검색")
print("  - 전화번호도 패턴 매칭으로 추가 수집")
print("")
print("⚠️  이 셀이 실행 중일 때만 접속 가능합니다.")
print("⚠️  중지하려면 '중지' 버튼을 클릭하세요.")
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
