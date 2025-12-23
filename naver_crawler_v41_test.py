#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 크롤러 v4.1 테스트 버전
주소 수집 문제 디버깅 및 해결
"""

from playwright.sync_api import sync_playwright
import time
import re
from urllib.parse import quote

class NaverPlaceCrawlerV41:
    """네이버 플레이스 크롤러 v4.1 - 주소 수집 디버깅 강화"""
    
    def __init__(self, debug=True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.version = "v4.1"
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
            print(f"✅ 브라우저 시작 ({self.version})")
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
            self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
            time.sleep(3)
            
            iframe = self.page.frame(name="searchIframe")
            if not iframe:
                print("❌ searchIframe을 찾을 수 없습니다")
                return []
            
            time.sleep(2)
            
            # 스크롤
            print("📜 결과 로딩 중...")
            for i in range(5):
                iframe.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.8)
            
            # 리스트 아이템 찾기
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
                    print(f"✅ {len(items)}개 발견 (셀렉터: {selector})")
                    break
            
            if not items:
                print("❌ 검색 결과를 찾을 수 없습니다")
                if self.debug:
                    print("\n🔍 iframe HTML 구조 샘플:")
                    content = iframe.content()
                    print(content[:2000])
                return []
            
            print(f"\n📊 총 {min(len(items), max_results)}개 파싱 시작...\n")
            
            results = []
            addr_success = 0
            
            for idx, item in enumerate(items[:max_results]):
                try:
                    # 업체명
                    name = self._get_text(item, [
                        '.TYaxT', '.place_bluelink', '.YwYLL',
                        'a.place_bluelink', 'span.place_name'
                    ])
                    if not name:
                        print(f"  ⚠️ [{idx+1}] 업체명 찾기 실패")
                        continue
                    
                    # 주소 - 강화된 셀렉터 (15개)
                    addr_selectors = [
                        '.LDgIH',  # 2024 메인
                        '.addr',
                        'span.place_addr',
                        '.Osdwn',
                        'div.addr',
                        '.v7Sqg',
                        '[class*="addr"]',
                        'span[class*="addr"]',
                        'div[class*="addr"]',
                        '.place_address',
                        'span.address',
                        'div.address',
                        'div[class*="address"]',
                        'span[class*="location"]',
                        'div[class*="location"]',
                        'p[class*="addr"]'
                    ]
                    
                    addr = ""
                    working_selector = ""
                    for sel in addr_selectors:
                        el = item.query_selector(sel)
                        if el:
                            addr = el.inner_text().strip()
                            if addr:
                                working_selector = sel
                                if self.debug and idx < 3:
                                    print(f"    ✅ [{idx+1}] '{name[:20]}' - 주소 발견!")
                                    print(f"        셀렉터: {sel}")
                                    print(f"        주소: {addr[:50]}...")
                                break
                    
                    # 정규식 패턴 매칭 (더 강화)
                    if not addr:
                        html = item.inner_html()
                        patterns = [
                            (r'([가-힣]+(?:특별시|광역시|시|도)\s+[가-힣]+(?:구|군|시)\s+[가-힣0-9\s\-]+)', '전체주소'),
                            (r'(서울[^<>]+?(?:동|로|가|길)\s*\d*)', '서울'),
                            (r'(경기[^<>]+?(?:동|로|가|길)\s*\d*)', '경기'),
                            (r'(부산[^<>]+?(?:동|로|가|길)\s*\d*)', '부산'),
                            (r'(대구[^<>]+?(?:동|로|가|길)\s*\d*)', '대구'),
                            (r'(인천[^<>]+?(?:동|로|가|길)\s*\d*)', '인천'),
                            (r'([가-힣]+구\s+[가-힣]+동\s+\d+)', '구동'),
                            (r'([가-힣]+로\s+\d+[가-힣\s]*)', '~로'),
                            (r'([가-힣]+길\s+\d+[가-힣\s]*)', '~길')
                        ]
                        for pat, pat_name in patterns:
                            match = re.search(pat, html)
                            if match:
                                addr = match.group(1).strip()
                                if self.debug and idx < 3:
                                    print(f"    🔍 [{idx+1}] '{name[:20]}' - 정규식 매칭!")
                                    print(f"        패턴: {pat_name}")
                                    print(f"        주소: {addr[:50]}...")
                                break
                    
                    # 여전히 주소 없으면 HTML 샘플 출력
                    if not addr and self.debug and idx < 2:
                        print(f"\n⚠️⚠️⚠️ [{idx+1}] '{name[:30]}' - 주소 찾기 완전 실패 ⚠️⚠️⚠️")
                        print(f"\n=== HTML 구조 샘플 (처음 600자) ===")
                        html_sample = item.inner_html()
                        # 가독성을 위해 일부 정리
                        html_sample = html_sample.replace('><', '>\n<')
                        print(html_sample[:600])
                        print("=== 끝 ===\n")
                    
                    if addr and addr != "주소 정보 없음":
                        addr_success += 1
                    
                    # 전화번호
                    phone = self._get_text(item, [
                        '.dry6Z', '.tel', 'span.place_tel',
                        '[class*="tel"]', 'span.phone'
                    ])
                    
                    # 평점
                    rating = self._get_text(item, [
                        '.h69bs', '.score', 'span.place_score'
                    ])
                    
                    # 리뷰 수
                    reviews = self._get_text(item, [
                        '.Tvqnp', '.cnt', 'span.place_review'
                    ])
                    reviews = re.sub(r'[^0-9]', '', reviews) if reviews else "0"
                    
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
    print("🚀 네이버 플레이스 크롤러 v4.1 테스트")
    print("="*70)
    
    crawler = NaverPlaceCrawlerV41(debug=True)
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
