#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 크롤러 v4.2 - SPA 구조 대응
iframe이 아닌 메인 페이지에서 직접 크롤링
"""

from playwright.sync_api import sync_playwright
import time
import re
from urllib.parse import quote
import json

class NaverPlaceCrawlerV42:
    """네이버 플레이스 크롤러 v4.2 - SPA 구조 대응"""
    
    def __init__(self, debug=True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.version = "v4.2"
        self.debug = debug
    
    def start(self):
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            print(f"✅ 브라우저 시작 ({self.version} - SPA 대응)")
            return True
        except Exception as e:
            print(f"❌ 브라우저 오류: {e}")
            return False
    
    def search_places(self, keyword, max_results=10):
        if not self.page:
            self.start()
        
        try:
            print(f"\n🔍 '{keyword}' 검색 중...")
            
            url = f"https://map.naver.com/p/search/{quote(keyword)}"
            self.page.goto(url, timeout=30000, wait_until="networkidle")
            time.sleep(5)  # SPA 로딩 대기
            
            print("📜 페이지 로딩 완료, 데이터 수집 중...")
            
            # 스크롤하여 더 많은 결과 로드
            for i in range(5):
                self.page.evaluate("window.scrollBy(0, 500)")
                time.sleep(0.5)
            
            # 메인 페이지에서 직접 리스트 아이템 찾기
            item_selectors = [
                'li._이름없음1',  # 네이버 최신 구조
                'a[class*="place"]',
                'li[class*="search"]',
                'div[class*="item"]',
                'li[role="listitem"]',
                'a[href*="/place/"]',  # place ID 링크
                '[data-place-id]',
                'li._3zNr6',
                'li > a',
                'div[class*="PlaceItem"]'
            ]
            
            items = []
            working_selector = ""
            
            for selector in item_selectors:
                items = self.page.query_selector_all(selector)
                if items and len(items) > 3:  # 최소 3개 이상
                    working_selector = selector
                    print(f"✅ {len(items)}개 발견 (셀렉터: {selector})")
                    break
            
            if not items:
                print("❌ 검색 결과를 찾을 수 없습니다")
                if self.debug:
                    print("\n🔍 페이지 HTML 구조 샘플 (2000자):")
                    content = self.page.content()
                    # class나 id가 있는 부분만 추출
                    lines = content.split('\n')
                    relevant_lines = [l for l in lines if 'class=' in l or 'id=' in l or 'data-' in l]
                    print('\n'.join(relevant_lines[:50]))
                return []
            
            print(f"\n📊 총 {min(len(items), max_results)}개 파싱 시작...\n")
            
            results = []
            addr_success = 0
            
            for idx, item in enumerate(items[:max_results]):
                try:
                    # item HTML 전체 가져오기
                    item_html = item.inner_html()
                    item_text = item.inner_text()
                    
                    # 업체명 추출 (여러 방법 시도)
                    name = ""
                    
                    # 방법 1: 텍스트에서 직접 추출 (첫 줄이 주로 업체명)
                    lines = [l.strip() for l in item_text.split('\n') if l.strip()]
                    if lines:
                        name = lines[0]
                    
                    # 방법 2: 셀렉터로 찾기
                    if not name:
                        name_selectors = [
                            '.place_bluelink', 
                            'span[class*="name"]',
                            'div[class*="name"]',
                            '.TYaxT'
                        ]
                        for sel in name_selectors:
                            el = item.query_selector(sel)
                            if el:
                                name = el.inner_text().strip()
                                if name:
                                    break
                    
                    if not name:
                        if self.debug and idx < 3:
                            print(f"  ⚠️ [{idx+1}] 업체명 찾기 실패")
                        continue
                    
                    # 주소 추출 (v4.2 강화)
                    addr = ""
                    
                    # 방법 1: 텍스트에서 주소 패턴 찾기
                    addr_patterns = [
                        r'([가-힣]+(?:특별시|광역시|시|도)\s+[가-힣]+(?:구|군|시)\s+[가-힣0-9\s\-]+)',
                        r'(서울[^<>\n]+?(?:동|로|가|길)[\s\d]*)',
                        r'(경기[^<>\n]+?(?:동|로|가|길)[\s\d]*)',
                        r'(부산[^<>\n]+?(?:동|로|가|길)[\s\d]*)',
                        r'(대구[^<>\n]+?(?:동|로|가|길)[\s\d]*)',
                        r'(인천[^<>\n]+?(?:동|로|가|길)[\s\d]*)',
                        r'([가-힣]+구\s+[가-힣]+동[\s\d]+)',
                        r'([가-힣]+로\s+\d+[\s가-힣]*)',
                        r'([가-힣]+길\s+\d+[\s가-힣]*)'
                    ]
                    
                    for pattern in addr_patterns:
                        match = re.search(pattern, item_text)
                        if match:
                            addr = match.group(1).strip()
                            # 너무 긴 경우 잘라내기 (100자 이상이면 이상함)
                            if len(addr) > 100:
                                addr = addr[:100]
                            if addr:
                                if self.debug and idx < 3:
                                    print(f"    ✅ [{idx+1}] '{name[:20]}' - 주소 발견!")
                                    print(f"        주소: {addr[:60]}...")
                                break
                    
                    # 방법 2: HTML에서 주소 셀렉터로 찾기
                    if not addr:
                        addr_selectors = [
                            '.LDgIH',
                            'span[class*="addr"]',
                            'div[class*="addr"]',
                            'span[class*="address"]',
                            'div[class*="address"]'
                        ]
                        for sel in addr_selectors:
                            el = item.query_selector(sel)
                            if el:
                                addr = el.inner_text().strip()
                                if addr:
                                    break
                    
                    # 디버깅: 주소 찾기 실패 시
                    if not addr and self.debug and idx < 2:
                        print(f"\n⚠️⚠️⚠️ [{idx+1}] '{name[:30]}' - 주소 찾기 실패 ⚠️⚠️⚠️")
                        print(f"\n=== 텍스트 내용 (500자) ===")
                        print(item_text[:500])
                        print("=== 끝 ===\n")
                    
                    if addr and addr != "주소 정보 없음":
                        addr_success += 1
                    
                    # 전화번호 추출
                    phone = ""
                    phone_patterns = [
                        r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})',
                        r'(070[-\s]?\d{3,4}[-\s]?\d{4})',
                        r'(1\d{3}[-\s]?\d{4})',
                        r'(\d{2,3}-\d{3,4}-\d{4})'
                    ]
                    for pattern in phone_patterns:
                        match = re.search(pattern, item_text)
                        if match:
                            phone = match.group(1)
                            break
                    
                    # 평점 추출
                    rating = ""
                    rating_match = re.search(r'(\d+\.\d+)', item_text)
                    if rating_match:
                        rating = rating_match.group(1)
                    
                    # 리뷰 수 추출
                    reviews = "0"
                    review_patterns = [r'리뷰\s*(\d+)', r'(\d+)개', r'방문자리뷰\s*(\d+)']
                    for pattern in review_patterns:
                        match = re.search(pattern, item_text)
                        if match:
                            reviews = match.group(1)
                            break
                    
                    # 타지역 판단
                    is_other = self._is_other_region(name, addr, phone, rating, keyword)
                    
                    result = {
                        'name': name,
                        'address': addr if addr else "주소 정보 없음",
                        'phone': phone if phone else "전화번호 없음",
                        'rating': rating if rating else "",
                        'reviews': reviews,
                        'is_other_region': is_other,
                        'place_type': "타지역업체" if is_other else "주업체"
                    }
                    
                    results.append(result)
                    
                    # 진행 상황
                    icon = "🟠" if is_other else "🟢"
                    addr_display = addr[:35] if addr else "❌주소없음"
                    print(f"  {icon} [{idx+1}] {name[:25]:25s} | {addr_display}...")
                    
                except Exception as e:
                    print(f"⚠️ [{idx+1}] 파싱 오류: {str(e)}")
                    if self.debug:
                        import traceback
                        traceback.print_exc()
                    continue
            
            total = len(results)
            addr_rate = (addr_success / total * 100) if total > 0 else 0
            
            print(f"\n{'='*70}")
            print(f"✅ 총 {total}개 수집 완료")
            print(f"   🟢 주업체: {len([r for r in results if not r['is_other_region']])}개")
            print(f"   🟠 타지역: {len([r for r in results if r['is_other_region']])}개")
            print(f"   📍 주소 수집: {addr_success}/{total} ({addr_rate:.1f}%)")
            print(f"{'='*70}\n")
            
            return results
            
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _is_other_region(self, name, addr, phone, rating, keyword):
        """타지역업체 판단"""
        score = 0
        
        if phone and "070" in phone:
            score += 3
        
        if addr and addr != "주소 정보 없음":
            if len(addr.split()) <= 3:
                score += 2
            if addr.endswith(("동", "구", "시")):
                score += 1
        
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


# 테스트 실행
if __name__ == "__main__":
    print("="*70)
    print("🚀 네이버 플레이스 크롤러 v4.2 테스트 (SPA 대응)")
    print("="*70)
    
    crawler = NaverPlaceCrawlerV42(debug=True)
    crawler.start()
    
    # 테스트 검색
    results = crawler.search_places("선불폰", max_results=10)
    
    # 결과 상세 출력
    print("\n📊 상세 결과:")
    print("="*70)
    for i, r in enumerate(results[:5], 1):
        print(f"\n[{i}] {r['name']}")
        print(f"    주소: {r['address']}")
        print(f"    전화: {r['phone']}")
        print(f"    평점: {r['rating']} ({r['reviews']}개)")
        print(f"    타입: {r['place_type']}")
    
    crawler.close()
    print("\n✅ 테스트 완료!")
