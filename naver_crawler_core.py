# ==================== 네이버 플레이스 크롤링 v4.9.6 봇 우회 ====================

print("="*70)
print("🎉 네이버 플레이스 크롤링 v4.9.9 최적화판 다중키워드 - 2페이지 + 테이블 UI")
print("   (봇 감지 우회 + Playwright + 검색 개선)" )
print("="*70)
print()

# ========== 패키지 설치 ==========
print("📦 패키지 설치 중...")
import subprocess
import sys
import time

# Playwright 재도입 - 실제 크롤링 위해
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "pyngrok", "playwright"], check=True)
subprocess.run(["playwright", "install", "chromium"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["playwright", "install-deps", "chromium"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("✅ 설치 완료 (Playwright 포함 - 실제 크롤링)\n")

# ========== ngrok 초기화 (ERROR 108 대응 강화) ==========
print("🔧 ngrok 초기화 중 (ERROR 108 방지)...")
from pyngrok import ngrok
import os

NGROK_TOKEN = "37GQIwqF1nLoRtC2vAVvnjKdbGD_62KXs32yxjhiQTUDVVCM9"

try:
    print("  [1/5] pyngrok 터널 강제 종료...")
    try:
        ngrok.kill()
        time.sleep(1.5)
        print("    ✓ pyngrok 터널 종료 완료")
    except Exception as e:
        print(f"    ⚠️ pyngrok 터널 없음")
    
    print("  [2/5] ngrok 프로세스 강제 종료...")
    try:
        subprocess.run(["pkill", "-9", "-f", "ngrok"], stderr=subprocess.DEVNULL)
        time.sleep(0.7)
        print("    ✓ ngrok 프로세스 종료 완료")
    except:
        print("    ⚠️ ngrok 프로세스 없음")
    
    print("  [3/5] ngrok 캐시 정리...")
    try:
        import shutil
        ngrok_dir = os.path.expanduser("~/.ngrok2")
        if os.path.exists(ngrok_dir):
            try:
                tunnel_file = os.path.join(ngrok_dir, ".ngrok")
                if os.path.exists(tunnel_file):
                    os.remove(tunnel_file)
                print("    ✓ 캐시 정리 완료")
            except:
                pass
        else:
            print("    ✓ 캐시 없음")
    except:
        print("    ⚠️ 캐시 정리 실패 (무시)")
    
    print("  [4/5] 추가 대기 (ERROR 108 방지)...")
    time.sleep(1.5)
    print("    ✓ 대기 완료")
    
    print("  [5/5] 토큰 설정 중...")
    ngrok.set_auth_token(NGROK_TOKEN)
    print("    ✓ 토큰 설정 완료")
    
    print("\n✅ ngrok 초기화 성공 (ERROR 108 방지 완료)!\n")
    
except Exception as e:
    print(f"\n⚠️ 경고: {e}")
    print("💡 해결: 런타임 재시작 후 다시 실행하세요\n")

# ========== 크롤러 클래스 (Playwright 실제 크롤링) ==========
from playwright.sync_api import sync_playwright
import re
from urllib.parse import quote

class NaverPlaceCrawlerReal:
    """v4.9.9 - Playwright로 실제 네이버 크롤링"""
    
    def search_places(self, keyword, max_results=20):
        """Playwright로 실제 네이버 플레이스 크롤링 (봇 우회)"""
        playwright = None
        browser = None
        context = None
        
        try:
            print(f"\n🔍 '{keyword}' 실제 크롤링 시작...")
            
            playwright = sync_playwright().start()
            
            # 🔒 봇 감지 우회 설정
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',  # 자동화 감지 차단
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # 모바일 디바이스 시뮬레이션 (iPhone 13)
            iphone_device = {
                'viewport': {'width': 390, 'height': 844},
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'device_scale_factor': 3,
                'is_mobile': True,
                'has_touch': True,
                'locale': 'ko-KR',
                'timezone_id': 'Asia/Seoul'
            }
            context = browser.new_context(**iphone_device)
            
            page = context.new_page()
            
            # JavaScript 스크립트로 봇 판별 방지
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
                window.chrome = {runtime: {}};
            """)
            
            print("  ✓ 봇 우회 + 모바일 시뮬레이션 완료")
            
            # 네이버 모바일 검색 접근
            url = f"https://m.search.naver.com/search.naver?where=m&sm=mtb_jum&query={quote(keyword)}"
            print(f"  → 모바일 검색 접속: {url[:60]}...")
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(1.5)
            
            print("  ✓ 페이지 로드 완료 (플레이스 섹션 확인 중...)")
            
            # 플레이스 섹션 대기 (최대 10초)
            try:
                page.wait_for_selector('.place_section', timeout=10000)
                print("  ✓ 플레이스 섹션 발견")
            except:
                print("  ⚠ 플레이스 섹션 대기 시간 초과 (계속 진행)")
            
            time.sleep(0.7)
            
            # 🔄 강화된 스크롤 로직 (더 많은 아이템 로드)
            print("  → 페이지 스크롤 중...")
            
            # 여러 번 스크롤하여 더 많은 아이템 로드
            for scroll_attempt in range(3):
                # 현재 아이템 수 확인
                current_items = len(page.query_selector_all('li.UEzoS, li[class*="place"], ul li'))
                
                # 스크롤
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)
                
                # 새로운 아이템 수 확인
                new_items = len(page.query_selector_all('li.UEzoS, li[class*="place"], ul li'))
                
                print(f"    스크롤 {scroll_attempt+1}/3: {new_items}개 아이템")
                
                # 더 이상 아이템이 증가하지 않으면 중단
                if new_items == current_items and scroll_attempt > 2:
                    break
            
            # 더보기 버튼 찾기 및 클릭 (2페이지 로드)
            print("  → 2페이지 로드 시도...")
            more_button_selectors = [
                'button:has-text(\"더보기\")',
                'a:has-text(\"더보기\")',
                '.place_more',
                '[class*=\"more\"]',
                'button[class*=\"More\"]'
            ]
            
            page_2_loaded = False
            for selector in more_button_selectors:
                try:
                    more_btn = page.query_selector(selector)
                    if more_btn and more_btn.is_visible():
                        more_btn.click()
                        time.sleep(0.7)
                        print(f"  ✓ 2페이지 로드 성공 (버튼: {selector})")
                        page_2_loaded = True
                        
                        # 2페이지 스크롤
                        for i in range(2):
                            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            time.sleep(0.7)
                        break
                except:
                    continue
            
            if not page_2_loaded:
                print("  ⚠ 2페이지 로드 실패 (더보기 버튼 없음 또는 1페이지만 존재)")
            
            # 플레이스 섹션 내 아이템 찾기 (모바일 셀렉터)
            items = []
            
            # 플레이스 아이템 찾기 (강화)
            items = []
            
            # 다양한 셀렉터 시도
            selectors = [
                ".place_section ul li",  # 플레이스 섹션 내부
                "li.UEzoS",  # 모바일 추천
                "ul li",  # 모든 리스트
                "li.place_item",
                "li[class]"  # 클래스 있는 li
            ]
            
            for selector in selectors:
                items = page.query_selector_all(selector)
                if items and len(items) > 0:
                    print(f"  ✓ {len(items)}개 발견 ({selector})")
                    break

            if not items:
                print("❌ 검색 결과를 찾을 수 없습니다")
                print("⚠️  플레이스 섹션 없음 - 검색 결과 없음")
                return [{
                    "name": "플레이스섹션없음",
                    "category": "-",
                    "address": "-",
                    "phone": "-",
                    "rating": "-",
                    "reviews": "0",
                    "place_type": "검색결과없음"
                }]
            
            # 데이터 추출
            results = []
            
            print(f"\n📊 총 {len(items)}개 아이템 발견")
            print(f"  → 최대 {min(len(items), max_results)}개 처리 예정\n")
            addr_count = 0
            
            print(f"  → 데이터 추출 중 (최대 {max_results}개)...")
            
            for idx, item in enumerate(items[:max_results]):
                try:
                    # 업체명 (모바일 셀렉터)
                    name = self._get_text(item, [
                        '.YwYLL',  # 모바일 플레이스 섹션
                        '.TYaxT',  # 모바일 추천 (맛집 등)
                        'a.BwZrK',
                        '.place_bluelink',
                        'span.place_name',
                        'a[href*="place"]',
                        'h2',
                        'strong'
                    ])
                    
                    if not name:
                        continue
                    
                    # === 디버깅: HTML 구조 확인 ===
                    if idx == 0:  # 첫 번째 아이템만 상세히 출력
                        try:
                            item_html = item.inner_html()
                            print(f"\n{'='*60}")
                            print(f"📋 첫 번째 아이템 HTML 구조 분석 (처음 2000자)")
                            print(f"{'='*60}")
                            print(item_html[:2000])
                            print(f"\n{'='*60}")
                            print(f"📋 전화번호 관련 텍스트 검색:")
                            print(f"{'='*60}")
                            # 전화번호 패턴 찾기
                            import re
                            phones_found = re.findall(r'(070[-\s]?\d{3,4}[-\s]?\d{4}|0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})', item_html)
                            if phones_found:
                                print(f"✓ 발견된 전화번호: {phones_found}")
                            else:
                                print(f"❌ 전화번호 패턴 없음")
                            
                            # 주소 패턴 찾기
                            addrs_found = re.findall(r'([가-힣]+[시도]\s+[가-힣]+[구군]\s+[가-힣]+[동읍면로길].*?(?:<|\n|$))', item_html)
                            if addrs_found:
                                print(f"✓ 발견된 주소 패턴: {addrs_found[:3]}")
                            else:
                                print(f"❌ 주소 패턴 없음")
                            print(f"{'='*60}\n")
                        except Exception as e:
                            print(f"⚠️ 디버깅 오류: {e}")
                    
                    # 플레이스 상세 링크 찾기
                    place_link = ""
                    try:
                        link_elem = item.query_selector('a[href*="place"]')
                        if link_elem:
                            place_link = link_elem.get_attribute('href') or ""
                            if place_link and not place_link.startswith('http'):
                                if place_link.startswith('/'):
                                    place_link = 'https://m.place.naver.com' + place_link
                    except: pass
                    
                    # 주소 추출 (다양한 방법 시도) + 디버깅
                    addr = ""
                    
                    # 방법 1: 텍스트 셀렉터 (모든 가능한 셀렉터)
                    addr_selectors = [".Pb4bU", ".LDgIH", "span.LDgIH", ".addr", "span.place_addr", ".Osdwn", "[class*='addr']", "[class*='address']", "div[class*='Addr']", "span[class*='place']"]
                    for sel in addr_selectors:
                        try:
                            el = item.query_selector(sel)
                            if el:
                                text = el.inner_text().strip()
                                if text and text != "-" and len(text) > 5:
                                    addr = text
                                    if idx == 0:
                                        print(f"  ✓ 주소 발견 (셀렉터: {sel}): {addr[:50]}")
                                    break
                        except: pass
                    
                    # 방법 2: HTML에서 정규식 추출
                    if not addr:
                        try:
                            html = item.inner_html()
                            import re
                            patterns = [
                                r"([가-힣]+시\s+[가-힣]+구\s+[가-힣]+동[^<]*)",  # 시 구 동
                                r"([가-힣]+[로길]\s+\d+[^<]*)",  # XX로 123
                                r"([가-힣]+동\s+\d+-\d+)",  # XX동 123-45
                            ]
                            for p in patterns:
                                m = re.search(p, html)
                                if m:
                                    addr = m.group(1).strip()
                                    break
                        except: pass
                    
                    if not addr:
                        addr = "주소 정보 없음"

                    # 전화번호 추출 (적극적으로) + 디버깅
                    phone = ""
                    
                    # 방법 1: 텍스트 셀렉터 (모든 가능한 셀렉터 시도)
                    phone_selectors = [
                        'a[href^="tel:"]',  # 전화 링크
                        '.dry6Z',           # 네이버 모바일 전화
                        'span.xlx7Q',       # 상세 전화
                        '.tel',
                        'span.place_tel',
                        '[class*="tel"]',
                        '[class*="phone"]',
                        'span[class*="Tel"]',
                        'div[class*="tel"]',
                        'a[class*="tel"]'
                    ]
                    
                    for sel in phone_selectors:
                        try:
                            el = item.query_selector(sel)
                            if el:
                                text = el.inner_text().strip()
                                if text and text != "-":
                                    phone = text
                                    if idx == 0:
                                        print(f"  ✓ 전화번호 발견 (셀렉터: {sel}): {phone}")
                                    break
                        except: pass
                    
                    if not phone:
                        phone = self._get_text(item, phone_selectors)
                    
                    # 방법 2: HTML에서 전화번호 추출 (더 강력한 패턴)
                    if not phone:
                        try:
                            html = item.inner_html()
                            phone_patterns = [
                                r'tel:([0-9\-]+)',                           # tel: 링크
                                r'(070[-\s]?\d{3,4}[-\s]?\d{4})',         # 070 번호
                                r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})',   # 지역번호
                                r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})',    # 일반 패턴
                            ]
                            for p in phone_patterns:
                                m = re.search(p, html)
                                if m:
                                    phone = m.group(1).replace('tel:', '').strip()
                                    # 전화번호 정규화
                                    phone = re.sub(r'\s+', '-', phone)
                                    break
                        except: pass
                    
                    # 전화번호 유효성 검사 - "전화"나 짧은 텍스트는 무효 처리
                    if phone and (phone == "전화" or phone == "tel" or len(phone) < 8 or not re.search(r'\d', phone)):
                        if idx == 0:
                            print(f"  ⚠️ 무효한 전화번호 발견: '{phone}' → 상세 페이지에서 재시도")
                        phone = ""  # 무효 처리
                    
                    # 상세 페이지에서 전화번호 우선 추출 (메인 판정의 핵심!)
                    import re
                    # 전화번호가 없거나 무효하면 무조건 상세 페이지 열기
                    if (not phone or phone == "-" or phone == "전화") and place_link:
                        try:
                            print(f"    → {name[:20]} 상세 페이지 확인 중...")
                            detail_page = context.new_page()
                            detail_page.goto(place_link, timeout=10000, wait_until="domcontentloaded")
                            time.sleep(0.5)
                            
                            # 전화번호 셀렉터 (상세 페이지) - 강화
                            if not phone or phone == "-" or phone == "전화":
                                phone_detail = self._get_text_from_page(detail_page, [
                                    'a[href^="tel:"]',
                                    '.dry6Z',
                                    'span.xlx7Q',
                                    'span[class*="phone"]',
                                    'span[class*="tel"]',
                                    'div[class*="phone"]',
                                    'div[class*="tel"]',
                                    '.phone_number',
                                    '.tel_number'
                                ])
                                
                                # HTML에서도 추출 시도 (tel: 링크에서 우선 추출)
                                if not phone_detail or phone_detail == "전화":
                                    try:
                                        html = detail_page.content()
                                        
                                        # 1. tel: 링크에서 먼저 추출 - 모든 번호 찾아서 070 우선
                                        tel_matches = re.findall(r'href="tel:([0-9\-]+)"', html)
                                        if tel_matches:
                                            print(f"    → 발견된 모든 tel: 링크: {tel_matches}")
                                            # 070 번호 우선 선택
                                            phone_detail = None
                                            for tel_num in tel_matches:
                                                if '070' in tel_num:
                                                    phone_detail = tel_num
                                                    print(f"    ✓ 070 번호 우선 선택: {phone_detail}")
                                                    break
                                            # 070이 없으면 첫 번째 번호 사용
                                            if not phone_detail:
                                                phone_detail = tel_matches[0]
                                                print(f"    ✓ 첫 번째 번호 사용: {phone_detail}").strip()
                                            print(f"      ✓ tel: 링크에서 발견: {phone_detail}")
                                        else:
                                            # 2. 전화번호 패턴 검색 (070 우선)
                                            phone_patterns = [
                                                r'(070[-\s]?\d{3,4}[-\s]?\d{4})',      # 070 최우선
                                                r'(0507[-\s]?\d{4}[-\s]?\d{4})',      # 0507
                                                r'(1[5-9]\d{2}[-\s]?\d{4})',           # 1509, 1688 등
                                                r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})'  # 일반 지역번호
                                            ]
                                            for p in phone_patterns:
                                                m = re.search(p, html)
                                                if m:
                                                    phone_detail = m.group(1).strip()
                                                    print(f"      ✓ 패턴 매칭: {phone_detail}")
                                                    break
                                    except Exception as e:
                                        print(f"      ⚠ HTML 추출 오류: {str(e)[:30]}")
                                
                                if phone_detail and phone_detail != "전화":
                                    phone = phone_detail
                                    print(f"      ✓ 전화: {phone}")
                                else:
                                    print(f"      ⚠️ 상세 페이지에서도 전화번호 없음")
                            
                            # 주소 셀렉터 (상세 페이지) - 상세 주소 가져오기
                            if not addr or addr == "주소 정보 없음":
                                addr_detail = self._get_text_from_page(detail_page, [
                                    'span.LDgIH',
                                    '.Pb4bU',
                                    'div.O8qbU span',
                                    '[class*="addr"]',
                                    '[class*="address"]'
                                ])
                                
                                if addr_detail and len(addr_detail) > len(addr):
                                    addr = addr_detail
                                    print(f"      ✓ 주소: {addr[:50]}")
                            
                            detail_page.close()
                        except Exception as e:
                            print(f"      ⚠ 상세 페이지 오류: {str(e)[:30]}")
                            pass
                    
                    if not phone:
                        phone = "-"

                    # 평점 (모바일 셀렉터)
                    rating = self._get_text(item, [
                        '.h69bs',  # 모바일 최신
                        'em.score',
                        '.score',
                        'span.rating',
                        '.star_score',
                        '[class*="rating"]'
                    ])
                    
                    # 리뷰 수 (모바일 셀렉터)
                    reviews = self._get_text(item, [
                        '.Tvqnp',  # 모바일 최신
                        'em.Tvqnp',
                        '.cnt',
                        'span.review_cnt',
                        '.review_count',
                        '[class*="review"]'
                    ])
                    reviews = re.sub(r'[^0-9]', '', reviews) if reviews else "0"
                    
                    # 카테고리 (모바일 셀렉터)
                    category = self._get_text(item, [
                        '.YzBgS',  # 모바일 최신
                        'span.YzBgS',
                        '.category',
                        'span.place_category',
                        '.type',
                        '[class*="category"]'
                    ])
                    
                    # 이미지 URL (썸네일) - 다양한 셀렉터 시도
                    image_url = ""
                    try:
                        # 1. img 태그 찾기
                        img_elem = item.query_selector('img')
                        if img_elem:
                            image_url = img_elem.get_attribute('src') or ""
                            if not image_url:
                                image_url = img_elem.get_attribute('data-src') or ""
                            if not image_url:
                                image_url = img_elem.get_attribute('data-lazy-src') or ""
                        
                        # 2. 배경 이미지는 체크하지 않음 (정규식 에러 방지)
                    except Exception as e:
                        pass
                    
                    # 디버깅: 이미지 URL 상태 로그
                    has_img = "📸" if image_url else "❌"
                    
                    # 타지역업체 판단 (사진 유무 최우선 체크)
                    is_other = self._is_other_region(name, addr, phone, rating, keyword, image_url)
                    
                    results.append({
                        'name': name,
                        'category': category or "미분류",
                        'address': addr or "주소 정보 없음",
                        'phone': phone or "전화번호 없음",
                        'rating': rating or "",
                        'reviews': reviews,
                        'image_url': image_url,
                        'is_other_region': is_other,
                        'place_type': '타지역업체' if is_other else '주업체'
                    })
                    
                    icon = "🟠" if is_other else "🟢"
                    print(f"  {icon} [{idx+1}] {name[:30]} {has_img}")
                    
                except Exception as e:
                    print(f"  ⚠️ [{idx+1}] 추출 실패: {str(e)[:50]}")
                    continue
            
            total = len(results)
            addr_rate = (addr_count / total * 100) if total > 0 else 0
            
            print(f"\n✅ 완료: {total}개 | 주소: {addr_count}/{total} ({addr_rate:.0f}%)\n")
            
            return results
            
        except Exception as e:
            print(f"❌ 크롤링 오류: {e}")
            return []
        
        finally:
            # 리소스 정리
            try:
                if context:
                    context.close()
                if browser:
                    browser.close()
                if playwright:
                    playwright.stop()
            except:
                pass
    
    def _get_text(self, parent, selectors):
        """Playwright 요소에서 텍스트 추출"""
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
    
    def _get_text_from_page(self, page, selectors):
        """Playwright 페이지에서 텍스트 추출"""
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if text:
                        return text
            except:
                pass
        return ""
    
    def _is_other_region(self, name, addr, phone, rating, keyword, image_url=""):
        """타지역 업체 판단 - 상호명 → 전화번호 순서"""
        import re
        
        # 1순위: 상호명 기반 필터링 (법적 사업자 등록 불가 업종)
        if name and name.strip() == "흥신소":
            return True  # 흥신소(3글자) = 무조건 타지역
        
        # 2순위: 전화번호 기반 판정 - 070만 타지역, 나머지는 모두 메인!
        if phone and phone != "-":
            # 070 번호 = 인터넷 전화 = 타지역 (유일한 타지역 기준!)
            if '070' in phone or phone.startswith('070'):
                return True  # 타지역
            
            # 그 외 모든 전화번호 = 메인
            # 0507 (네이버 메인플레이스)
            # 1509, 1688, 1588, 1577 (대표전화/고객센터)
            # 02, 031 등 (지역번호)
            # → 모두 메인으로 처리
            if re.search(r'\d', phone):  # 숫자가 하나라도 있으면
                return False  # 메인
        
        # 1. 주소에 번지수가 있는지 체크 (메인 판별)
        if addr and addr != "주소 정보 없음":
            # 강력한 번지수 패턴
            detailed_patterns = [
                r'\d+-\d+',              # 123-45
                r'\d+\s*-\s*\d+',        # 123 - 45
                r'[동가]\s+\d+-\d+',      # 신사동 638-2, 저동2가 35-4
                r'[로길]\s+\d+',          # 압구정로 306
                r'\d+\s*[층호]',          # 165호, 1층
                r'[가]\s+\d+',           # 저동2가 35
            ]
            
            for pattern in detailed_patterns:
                if re.search(pattern, addr):
                    return False  # 번지수 있음 = 메인
            
            # "~동/가"로만 끝나면 타지역
            if re.search(r'[동가로길]$', addr):
                return True
        
        # 2. "서울 XX구 XX동" 형태만 있으면 타지역
        if addr and re.match(r'^[가-힣]+\s+[가-힣]+구\s+[가-힣]+[동가로길]$', addr):
            return True
        
        # 3. 추가 점수 기반 판단
        score = 0
        if not rating:
            score += 1
        if name and keyword:
            words = [w for w in keyword.split() if len(w) > 1]
            if any(w in name for w in words):
                score += 2
        
        return score >= 3

# ========== Flask 웹 서버 ==========
from flask import Flask, request, jsonify, Response
import threading
import io
import csv

app = Flask(__name__)
crawler = NaverPlaceCrawlerReal()

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>네이버 플레이스 v4.9.9 최적화판 다중키워드</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white;
            border-radius: 25px; box-shadow: 0 25px 80px rgba(0,0,0,0.35);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 50px; text-align: center;
        }
        h1 { font-size: 3em; margin-bottom: 15px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
        .version { 
            color: #ffd700; font-size: 1.3em; font-weight: bold;
            background: rgba(255,255,255,0.2); 
            display: inline-block; padding: 10px 25px; 
            border-radius: 20px; margin-top: 10px;
        }
        .badge-new {
            background: #00ff88; color: #000; 
            padding: 8px 18px; border-radius: 15px;
            font-size: 0.9em; margin-left: 15px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .content { padding: 50px; }
        .info-box {
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 25px; border-radius: 15px; margin: 30px 0;
            border-left: 5px solid #667eea;
        }
        .info-box h3 {
            color: #667eea; margin-bottom: 15px; font-size: 1.4em;
        }
        .info-list {
            list-style: none; padding: 0;
        }
        .info-list li {
            padding: 10px 0; font-size: 1.1em; color: #333;
        }
        .info-list li::before {
            content: '✅ '; color: #667eea; font-weight: bold;
        }
        .search-box { display: flex; gap: 12px; margin-bottom: 40px; }
        input { 
            flex: 1; padding: 20px; border: 3px solid #667eea; 
            border-radius: 15px; font-size: 18px; transition: all 0.3s;
        }
        input:focus { 
            border-color: #764ba2; outline: none; 
            box-shadow: 0 0 0 3px rgba(118,75,162,0.1);
        }
        button { 
            padding: 20px 40px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border: none; border-radius: 15px; 
            cursor: pointer; font-weight: bold; font-size: 17px; 
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(102,126,234,0.4);
        }
        button:hover { 
            transform: translateY(-3px); 
            box-shadow: 0 6px 20px rgba(102,126,234,0.6);
        }
        button:disabled { 
            background: linear-gradient(135deg, #ccc 0%, #999 100%); 
            cursor: not-allowed; transform: none; box-shadow: none;
        }
        .results { margin-top: 30px; }
        .place-card { 
            border: 3px solid #e0e0e0; padding: 30px; margin: 20px 0; 
            border-radius: 20px; transition: all 0.4s;
            background: white; position: relative; overflow: hidden;
        }
        .place-card::before {
            content: ''; position: absolute; top: 0; left: 0;
            width: 5px; height: 100%; background: #667eea;
            transition: width 0.3s;
        }
        .place-card:hover::before { width: 10px; }
        .place-card:hover { 
            box-shadow: 0 10px 30px rgba(0,0,0,0.15); 
            transform: translateY(-5px); border-color: #667eea;
        }
        .place-card.other { border-color: #ff9800; }
        .place-card.other::before { background: #ff9800; }
        .badge { 
            display: inline-block; padding: 8px 18px; 
            border-radius: 25px; font-size: 0.9em; margin-left: 15px;
            font-weight: bold;
        }
        .badge.main { background: #4caf50; color: white; }
        .badge.other { background: #ff9800; color: white; }
        .info { color: #555; margin-top: 15px; line-height: 2.2; font-size: 1.05em; }
        .loading { 
            text-align: center; padding: 80px; font-size: 1.8em; 
            color: #667eea; font-weight: bold;
        }
        .spinner {
            border: 5px solid #f3f3f3; border-top: 5px solid #667eea;
            border-radius: 50%; width: 50px; height: 50px;
            animation: spin 1s linear infinite; margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 네이버 플레이스 크롤링</h1>
            <p class="version">v4.9.9 최적화판 <span class="badge-new">다중키워드</span></p>
            <p style="margin-top: 20px; font-size: 1.1em; opacity: 0.95;">봇 감지 우회 + 실제 크롤링 + 검색 개선</p>
        </div>
        <div class="content">
            <div class="info-box">
                <h3>✨ v4.9.9 실제 크롤링 보장</h3>
                <ul class="info-list">
                    <li>Playwright로 실제 네이버 플레이스 접근</li>
                    <li>샘플 데이터 완전 제거 - 실제 데이터만</li>
                    <li>주소, 전화번호, 평점 실시간 수집</li>
                    <li>ERROR 108 자동 복구 시스템</li>
                </ul>
            </div>
            
            <div class="search-box">
                <textarea id="keyword" rows="3" placeholder="검색어를 입력하세요 (여러 개는 쉼표 또는 줄바꿈으로 구분)\n예시: 하수구막힘, 포장이사, 강남역맛집" autocomplete="off" spellcheck="false" style="width:100%; padding:15px; border:2px solid #e0e0e0; border-radius:15px; font-size:1.1em; font-family:inherit; resize:vertical;"></textarea>
                <div style="margin-top:10px;">
                    <button onclick="search()" id="btnSearch" style="padding:15px 40px; font-size:1.2em;">🔍 검색</button>
                    <button onclick="downloadCSV()" id="btnDownload" style="display:none; background:linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding:15px 40px; font-size:1.2em;">📥 CSV 다운로드</button>
                </div>
            </div>
            <div id="results" class="results">
                <div style="text-align:center; padding:80px; color:#666;">
                    <h2 style="font-size:2.5em; margin-bottom:25px; color:#667eea;">🎉 v4.9.9 실제 크롤링 준비 완료!</h2>
                    <p style="font-size:1.3em; margin-bottom:15px;">검색어를 입력하고 Enter를 누르세요</p>
                    <p style="color:#999; font-size:1em;">예시: 강남역 맛집, 홍대 카페, 이태원 술집</p>
                    <div style="margin-top: 40px; padding: 30px; background: #d1ecf1; border-radius: 15px; display: inline-block;">
                        <p style="color: #0c5460; font-size: 1.1em; font-weight: bold;">✅ 실제 네이버에서 크롤링합니다!</p>
                        <p style="color: #0c5460; font-size: 0.9em; margin-top: 10px;">샘플 데이터가 아닌 실제 데이터를 수집합니다</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        let currentResults = [];
        let currentKeyword = '';
        let isSearching = false;
        
        async function search() {
            // 중복 검색 방지
            if (isSearching) {
                console.log('이미 검색 중입니다...');
                return;
            }
            
            const inputEl = document.getElementById('keyword');
            const keyword = inputEl.value.trim();
            
            if (!keyword) {
                alert('검색어를 입력하세요');
                inputEl.focus();
                return;
            }
            
            isSearching = true;
            const btnSearch = document.getElementById('btnSearch');
            
            // 입력창과 버튼 모두 비활성화
            inputEl.disabled = true;
            btnSearch.disabled = true;
            btnSearch.textContent = '⏳ 크롤링 중...';
            
            document.getElementById('results').innerHTML = '<div class="loading"><div class="spinner"></div>🔍 실제 네이버 크롤링 중...<br><small style="font-size:0.5em; color:#999; font-weight:normal;">약 30초 소요</small></div>';
            document.getElementById('btnDownload').style.display = 'none';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword, max_results: 20 })
                });
                const data = await response.json();
                
                if (data.success && data.results.length > 0) {
                    currentResults = data.results;
                    currentKeyword = keyword;
                    
                    // 키워드별 그룹화
                    const grouped = {};
                    data.results.forEach(p => {
                        const kw = p.keyword || '전체';
                        if (!grouped[kw]) grouped[kw] = [];
                        grouped[kw].push(p);
                    });
                    
                    let html = `<div style="padding:30px;"><h2 style="margin-bottom:20px; color:#667eea;">📊 검색 결과 (총 ${data.total_count}개, ${data.keywords_count}개 키워드)</h2>`;
                    
                    Object.keys(grouped).forEach(kw => {
                        const items = grouped[kw];
                        const mainCount = items.filter(p => !p.is_other_region).length;
                        const otherCount = items.length - mainCount;
                        
                        html += `
                            <div style="margin-bottom:40px;">
                                <h3 style="background:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:15px;">
                                    🔍 ${kw} <span style="color:#666; font-size:0.85em;">(${items.length}개 | 메인: ${mainCount}, 타지역: ${otherCount})</span>
                                </h3>
                                <table style="width:100%; border-collapse:collapse; box-shadow:0 2px 10px rgba(0,0,0,0.1);">
                                    <thead>
                                        <tr style="background:#667eea; color:white;">
                                            <th style="padding:12px; text-align:left; width:5%;">No</th>
                                            <th style="padding:12px; text-align:center; width:8%;">사진</th>
                                            <th style="padding:12px; text-align:left; width:18%;">업체명</th>
                                            <th style="padding:12px; text-align:left; width:12%;">카테고리</th>
                                            <th style="padding:12px; text-align:left; width:22%;">주소</th>
                                            <th style="padding:12px; text-align:left; width:13%;">전화번호</th>
                                            <th style="padding:12px; text-align:center; width:10%;">평점/리뷰</th>
                                            <th style="padding:12px; text-align:center; width:7%;">구분</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                        `;
                        
                        items.forEach((p, i) => {
                            const badge = p.is_other_region ? '<span style="background:#ff9800; color:white; padding:4px 10px; border-radius:5px; font-size:0.85em;">🟠타지역</span>' : '<span style="background:#4caf50; color:white; padding:4px 10px; border-radius:5px; font-size:0.85em;">🟢메인</span>';
                            const rowBg = p.is_other_region ? '#fff3e0' : 'white';
                            html += `
                                <tr style="background:${rowBg}; border-bottom:1px solid #e0e0e0;">
                                    <td style="padding:12px;">${i+1}</td>
                                    <td style="padding:8px; text-align:center;">${p.image_url ? '<img src="' + p.image_url + '" style="width:50px; height:50px; object-fit:cover; border-radius:5px;" />' : '<span style="color:#999;">-</span>'}</td>
                                    <td style="padding:12px;"><strong>${p.name}</strong></td>
                                    <td style="padding:12px; font-size:0.85em; color:#666;">${p.category || '-'}</td>
                                    <td style="padding:12px; font-size:0.9em;">${p.address}</td>
                                    <td style="padding:12px; font-size:0.9em;">${p.phone}</td>
                                    <td style="padding:12px; text-align:center; font-size:0.9em;">${p.rating ? '⭐ ' + p.rating + ' (' + p.reviews + ')' : '-'}</td>
                                    <td style="padding:12px; text-align:center;">${badge}</td>
                                </tr>
                            `;
                        });
                        
                        html += `
                                    </tbody>
                                </table>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    
                    document.getElementById('results').innerHTML = html;
                    document.getElementById('btnDownload').style.display = 'inline-block';
                } else {
                    document.getElementById('results').innerHTML = '<div style="text-align:center; padding:80px; color:#999; font-size:1.5em;">❌ 검색 결과가 없습니다<br><small style="font-size:0.6em; margin-top:15px; display:block;">다른 검색어를 시도해보세요</small></div>';
                }
            } catch (error) {
                console.error('검색 오류:', error);
                document.getElementById('results').innerHTML = '<div style="text-align:center; padding:80px; color:red; font-size:1.3em;">❌ 오류: ' + error.message + '<br><small style="font-size:0.6em; margin-top:15px; display:block; color:#666;">다시 시도해주세요</small></div>';
            } finally {
                // 입력창과 버튼 복구
                const inputEl = document.getElementById('keyword');
                inputEl.disabled = false;
                inputEl.focus();
                
                btnSearch.disabled = false;
                btnSearch.textContent = '🔍 검색';
                
                isSearching = false;
            }
        }
        
        async function downloadCSV() {
            const response = await fetch('/api/download-csv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ results: currentResults })
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `naver_${currentKeyword}_${Date.now()}.csv`;
            a.click();
            alert('✅ CSV 다운로드 완료!');
        }
        
        // 한글 입력 지원 (IME 완료 후 Enter)
        const keywordInput = document.getElementById('keyword');
        
        // Ctrl+Enter로 검색 (textarea는 Enter가 줄바꿈)
        keywordInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                // IME 입력 중이 아닐 때만 검색
                if (!e.isComposing && e.keyCode !== 229) {
                    e.preventDefault();
                    search();
                }
            }
        });
        
        // IME 입력 완료 이벤트
        keywordInput.addEventListener('compositionend', (e) => {
            console.log('한글 입력 완료:', e.data);
        });
        
        // 페이지 로드 시 입력창 자동 포커스
        window.addEventListener('load', () => {
            setTimeout(() => {
                keywordInput.focus();
            }, 300);
        });
    </script>
</body>
</html>'''

@app.route('/api/search-stream', methods=['POST'])
def api_search_stream():
    """실시간 스트리밍 검색 API"""
    def generate():
        try:
            data = request.json
            keywords_input = data.get('keyword', '')
            max_results = data.get('max_results', 20)
            
            import re
            keywords = [k.strip() for k in re.split(r'[,\n]', keywords_input) if k.strip()]
            
            MAX_KEYWORDS = 10
            if len(keywords) > MAX_KEYWORDS:
                yield "data: " + json.dumps({'error': f'키워드 {len(keywords)}개는 너무 많습니다. 최대 {MAX_KEYWORDS}개까지 가능합니다.'}) + "\n\n",
                return
            
            if not keywords:
                yield "data: " + json.dumps({'error': '키워드를 입력해주세요.'}) + "\n\n",
                return
            
            all_results = []
            
            for idx, keyword in enumerate(keywords, 1):
                try:
                    # 진행 상황 전송
                    yield "data: " + json.dumps({'status': 'processing', 'keyword': keyword, 'index': idx, 'total': len(keywords)}) + "\n\n",
                    
                    results = crawler.search_places(keyword, max_results)
                    
                    for r in results:
                        r['keyword'] = keyword
                    
                    all_results.extend(results)
                    
                    # 키워드별 결과 전송
                    yield "data: " + json.dumps({'status': 'completed', 'keyword': keyword, 'results': results, 'count': len(results)}) + "\n\n",
                    
                    if idx < len(keywords):
                        time.sleep(0.3)
                    
                except Exception as e:
                    yield "data: " + json.dumps({'status': 'error', 'keyword': keyword, 'error': str(e)}) + "\n\n",
                    continue
            
            # 전체 완료
            yield "data: " + json.dumps({'status': 'done', 'total_count': len(all_results), 'keywords_count': len(keywords)}) + "\n\n",
            
        except Exception as e:
            yield "data: " + json.dumps({'status': 'fatal_error', 'error': str(e)}) + "\n\n",
    
    return Response(generate(), mimetype='text/event-stream')



@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.json
        keywords_input = data.get('keyword', '')
        max_results = data.get('max_results', 20)
        
        # 다중 키워드 파싱
        import re
        keywords = [k.strip() for k in re.split(r'[,\n]', keywords_input) if k.strip()]
        
        # 키워드 개수 제한
        MAX_KEYWORDS = 10
        if len(keywords) > MAX_KEYWORDS:
            return jsonify({
                'success': False,
                'error': f'키워드가 너무 많습니다. ({len(keywords)}개) 최대 {MAX_KEYWORDS}개까지 가능합니다.',
                'results': []
            }), 400
        
        if not keywords:
            return jsonify({
                'success': False,
                'error': '키워드를 입력해주세요.',
                'results': []
            }), 400
        
        all_results = []
        
        for idx, keyword in enumerate(keywords, 1):
            try:
                print(f"\n{'='*70}")
                print(f"🔍 키워드 [{idx}/{len(keywords)}]: {keyword}")
                print(f"{'='*70}")
                
                results = crawler.search_places(keyword, max_results)
                
                for r in results:
                    r['keyword'] = keyword
                
                all_results.extend(results)
                print(f"✅ '{keyword}' 완료: {len(results)}개 수집")
                
                if idx < len(keywords):
                    time.sleep(0.3)
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ '{keyword}' 실패: {error_msg}")
                continue
        
        print(f"\n{'='*70}")
        print(f"🎉 전체 완료: 총 {len(all_results)}개 수집")
        print(f"{'='*70}")
        
        return jsonify({
            'success': True, 
            'results': all_results,
            'keywords_count': len(keywords),
            'total_count': len(all_results)
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 전체 오류: {error_msg}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'검색 중 오류 발생: {error_msg}',
            'results': []
        }), 500

@app.route('/api/download-csv', methods=['POST'])
def download_csv():
    data = request.json
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['keyword', 'name', 'category', 'address', 'phone', 'rating', 'reviews', 'place_type'])
    writer.writeheader()
    writer.writerows(data.get('results', []))
    return Response(output.getvalue().encode('utf-8-sig'), mimetype='text/csv')

# ========== Flask 서버 시작 ==========
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

print("🚀 Flask 서버 시작 중...")
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
time.sleep(0.7)
print("✅ Flask 서버 준비 완료!\n")

# ========== ngrok 터널 생성 (ERROR 108 강력 대응) ==========
print("🌐 ngrok 터널 생성 중 (ERROR 108 자동 복구)...")
print("="*70)

max_retries = 5
public_url = None

for attempt in range(1, max_retries + 1):
    try:
        print(f"\n[시도 {attempt}/{max_retries}] ngrok 연결 중...")
        
        if attempt > 1:
            print("  → 기존 터널 재정리 중...")
            try:
                ngrok.kill()
                time.sleep(1.5)
            except:
                pass
            
            try:
                subprocess.run(["pkill", "-9", "-f", "ngrok"], stderr=subprocess.DEVNULL)
                time.sleep(0.7)
            except:
                pass
        
        tunnel = ngrok.connect(5000, bind_tls=True)
        public_url = str(tunnel) if not hasattr(tunnel, 'public_url') else tunnel.public_url
        
        print(f"✅ 연결 성공!\n")
        break
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 실패: {error_msg[:150]}")
        
        if '108' in error_msg or 'failed to start tunnel' in error_msg:
            print("  ⚠️ ERROR 108 감지: 기존 터널 중복 문제")
            if attempt < max_retries:
                wait_time = 5 + (attempt * 2)
                print(f"  💡 해결: {wait_time}초 대기 후 강제 재시도...")
                time.sleep(wait_time)
            else:
                print("\n❌ ERROR 108 지속: 런타임 재시작 필요")
                print("💡 해결: 런타임 → 런타임 다시 시작")
        else:
            if attempt < max_retries:
                wait_time = attempt * 3
                print(f"⏳ {wait_time}초 대기 후 재시도...")
                time.sleep(wait_time)

print("="*70)

if public_url:
    print()
    print("🎉" * 35)
    print()
    print("🚀 v4.9.9 최적화판 다중키워드 (2페이지 + 테이블 UI) 시작 완료!")
    print()
    print("="*70)
    print()
    print(f"🌐 접속 URL: {public_url}")
    print()
    print("="*70)
    print()
    print("⚡ v4.9.9의 핵심 변화:")
    print("   • Playwright 재도입 → 실제 네이버 크롤링")
    print("   • 샘플 데이터 완전 제거")
    print("   • 실제 주소, 전화번호, 평점 수집")
    print("   • ERROR 108 자동 복구 유지")
    print()
    print("💡 사용 방법:")
    print("   1. 위 URL 클릭")
    print("   2. 검색어 입력 (예: 강남역 맛집)")
    print("   3. 실제 네이버 데이터 수집 (약 30초)")
    print()
    print("="*70)
    print()
else:
    print()
    print("❌ ngrok 연결 실패")
    print("💡 해결: 런타임 재시작 후 다시 실행")
    print()

# ========== 서버 유지 ==========
print("⚠️  셀을 실행 상태로 유지하세요")
print("⚠️  중지하면 서버가 종료됩니다\n")

try:
    while True:
        time.sleep(0.7)
except KeyboardInterrupt:
    print("\n✅ 서버 종료")





















