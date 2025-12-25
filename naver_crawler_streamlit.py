"""
네이버 플레이스 크롤러 - Streamlit 버전
메인/타지역 업체 자동 판별 시스템
"""

from playwright.async_api import async_playwright
import asyncio
import time
import re
from typing import List, Dict, Optional


class NaverPlaceCrawler:
    """네이버 플레이스 크롤러"""
    
    def __init__(self):
        # 데스크톱 User-Agent로 변경 (더 안정적)
        self.user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 모바일 User-Agent (백업용)
        self.mobile_user_agent = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 '
            'Mobile/15E148 Safari/604.1'
        )
    
    async def crawl(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """
        네이버 플레이스 크롤링 실행
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수
            
        Returns:
            크롤링 결과 리스트
        """
        print(f"\n{'='*60}")
        print(f"🚀 크롤링 시작: '{keyword}'")
        print(f"{'='*60}")
        
        try:
            async with async_playwright() as p:
                print("✓ Playwright 초기화 성공")
                
                try:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--no-sandbox',
                        ]
                    )
                    print("✓ Chromium 브라우저 실행 성공")
                except Exception as launch_error:
                    print(f"❌ 브라우저 실행 실패: {launch_error}")
                    raise
            
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080},  # 데스크톱 해상도
                    locale='ko-KR',
                    timezone_id='Asia/Seoul'
                )
                print("✓ 브라우저 컨텍스트 생성 성공")
                
                # 봇 감지 우회 스크립트
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
                """)
                print("✓ 봇 우회 스크립트 추가 완료")
                
                page = await context.new_page()
                print("✓ 새 페이지 생성 성공")
                
                try:
                    # 네이버 플레이스 검색 - 데스크톱 URL 시도
                    import urllib.parse
                    encoded_keyword = urllib.parse.quote(keyword)
                    
                    # 모바일 대신 데스크톱 URL 사용
                    search_url = f"https://map.naver.com/p/search/{encoded_keyword}"
                    print(f"→ 검색 URL (데스크톱): {search_url}")
                    
                    # 페이지 로드 - networkidle 대기
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)
                    print("✓ 페이지 로드 완료 (networkidle)")
                    
                    # 추가 대기 (JavaScript 실행 대기)
                    await asyncio.sleep(5)
                    print("✓ JavaScript 실행 대기 완료")
                    
                    # iframe 확인
                    frames = page.frames
                    print(f"→ 발견된 iframe 수: {len(frames)}")
                    for i, frame in enumerate(frames):
                        print(f"  Frame {i}: {frame.url[:100]}")
                    
                    # searchIframe 찾기
                    search_frame = None
                    for frame in frames:
                        if 'searchIframe' in frame.url or 'search' in frame.url.lower():
                            search_frame = frame
                            print(f"✓ 검색 iframe 발견: {frame.url}")
                            break
                    
                    # iframe이 있으면 그 안에서 추출, 없으면 메인 페이지에서 추출
                    if search_frame:
                        results = await self._extract_results(search_frame, keyword, max_results)
                    else:
                        print("⚠️ 검색 iframe 없음, 메인 페이지에서 추출 시도")
                        results = await self._extract_results(page, keyword, max_results)
                    
                    print(f"✓ 최종 결과: {len(results)}개 추출")
                    return results
                    
                except Exception as e:
                    print(f"❌ 크롤링 오류: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return []
                
                finally:
                    await browser.close()
                    print("✓ 브라우저 종료")
                    
        except Exception as outer_error:
            print(f"❌ Playwright 실행 실패: {outer_error}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _extract_results(self, page, keyword: str, max_results: int) -> List[Dict]:
        """검색 결과 추출"""
        results = []
        
        try:
            print(f"\n🔍 '{keyword}' 검색 결과 추출 시작...")
            
            # 검색 결과 로드 대기
            await asyncio.sleep(3)
            
            # 페이지 HTML 확인 (디버깅용)
            html = await page.content()
            print(f"  → 페이지 HTML 길이: {len(html)} 문자")
            
            # HTML 샘플 출력 (처음 500자)
            print(f"  → HTML 샘플 (처음 500자):")
            print(f"     {html[:500]}")
            
            # 특정 키워드 검색
            if "플레이스" in html or "place" in html.lower():
                print("  ✓ HTML에 '플레이스' 관련 키워드 발견")
            else:
                print("  ❌ HTML에 '플레이스' 키워드 없음 (차단되었을 수 있음)")
            
            # 현재 URL 확인
            current_url = page.url
            print(f"  → 현재 URL: {current_url}")
            
            # 스크롤하여 더 많은 결과 로드
            print("  → 스크롤 중...")
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
            
            # 플레이스 아이템 찾기 - 여러 셀렉터 시도
            print("  → 셀렉터로 아이템 찾는 중...")
            
            # 시도할 모든 셀렉터 (iframe 내부용)
            selectors = [
                # iframe 모바일 검색 결과 (우선순위 높음)
                ('ul.place_section_content > li', 'ul.place_section_content > li (모바일)'),
                ('li._YwYLL', 'li._YwYLL (모바일 아이템)'),
                ('li._3cEhe', 'li._3cEhe (모바일 아이템)'),
                ('.place_section_content li', '.place_section_content li'),
                
                # 모바일 일반
                ('li[data-index]', 'li[data-index]'),
                ('.item_inner', '.item_inner'),
                ('.UEzoS', '.UEzoS'),
                
                # 데스크톱 셀렉터
                ('.Ryr1F', '.Ryr1F (데스크톱 아이템)'),
                ('.CHC5F', '.CHC5F (데스크톱 리스트)'),
                ('li.VLTHu', 'li.VLTHu'),
                
                # 일반 리스트 (최후 수단, UI 버튼 제외)
                ('ul > li:not([role="button"])', 'ul > li (버튼 제외)'),
            ]
            
            items = []
            for selector, name in selectors:
                found = await page.query_selector_all(selector)
                print(f"  → {name}: {len(found)}개")
                if found and not items:
                    items = found
                    print(f"  ✅ 사용할 셀렉터: {name}")
            
            print(f"  ✅ 최종 발견된 아이템 수: {len(items)}")
            
            # 각 아이템에서 정보 추출
            for idx, item in enumerate(items[:max_results]):
                try:
                    print(f"\n  [{idx+1}] 아이템 처리 중...")
                    
                    # 디버깅: 아이템 HTML 출력 (첫 번째만)
                    if idx == 0:
                        item_html = await item.inner_html()
                        print(f"    📄 첫 번째 아이템 HTML (처음 1000자):")
                        print(f"    {item_html[:1000]}")
                    
                    # 상호명 - 모바일 iframe 우선
                    name = await self._get_text(item, [
                        'a.YwYLL',          # 모바일 iframe
                        '.YwYLL',           # 모바일
                        'a[class*="place"]', # 모바일
                        '.place_bluelink',  # 데스크톱
                        '.TYaxT',           # 데스크톱
                        'a.place_bluelink', # 데스크톱
                        'a.BwZrK',          # 모바일
                        '[class*="name"]',
                        'a',                # 일반
                        'span',
                        'div.YwYLL'         # div로도 시도
                    ])
                    
                    if not name or name == '':
                        print(f"    ⚠️ 상호명 없음, 스킵")
                        continue
                    
                    print(f"    ✓ 상호명: {name}")
                    
                    # 카테고리
                    category = await self._get_text(item, [
                        '.KCMnt',           # 모바일 iframe
                        'span.KCMnt',       # 모바일
                        '.YzBgS',           # 데스크톱
                        '[class*="category"]',
                        'span'
                    ])
                    
                    # 주소
                    addr = await self._get_text(item, [
                        '.LDgIH',           # 모바일 iframe
                        'span.LDgIH',       # 모바일
                        '.IH4XH',           # 모바일 대체
                        '[class*="addr"]',
                        '[class*="address"]',
                        'span'
                    ])
                    
                    # 전화번호 - 여러 방법으로 시도
                    phone = await self._get_text(item, [
                        'a[href^="tel:"]',
                        '.dry6Z',
                        '[class*="phone"]',
                        '[class*="tel"]',
                        'span'
                    ])
                    
                    # tel: 링크에서 전화번호 추출
                    if not phone or phone == "전화":
                        tel_link = await item.query_selector('a[href^="tel:"]')
                        if tel_link:
                            href = await tel_link.get_attribute('href')
                            if href:
                                phone = href.replace('tel:', '').strip()
                    
                    # HTML에서 정규식으로 전화번호 찾기
                    if not phone or phone == "전화":
                        html = await item.inner_html()
                        phone_patterns = [
                            r'(070[-\s]?\d{3,4}[-\s]?\d{4})',
                            r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})',
                            r'(\d{4}[-\s]?\d{4})',
                        ]
                        for pattern in phone_patterns:
                            match = re.search(pattern, html)
                            if match:
                                phone = match.group(1)
                                break
                    
                    # 평점
                    rating = await self._get_text(item, ['.h69bs', '[class*="rating"]', '[class*="star"]'])
                    
                    # 리뷰 수
                    reviews = await self._get_text(item, ['.AQ85', '[class*="review"]'])
                    
                    # 이미지 URL
                    img_elem = await item.query_selector('img')
                    image_url = ""
                    if img_elem:
                        image_url = await img_elem.get_attribute('src') or ""
                    
                    # 타지역 판정
                    is_other = self._is_other_region(name, addr, phone, rating, keyword, image_url)
                    
                    results.append({
                        'name': name,
                        'category': category or "미분류",
                        'address': addr or "주소 정보 없음",
                        'phone': phone or "전화번호 없음",
                        'rating': rating or "",
                        'reviews': reviews or "",
                        'image_url': image_url,
                        'is_other_region': is_other,
                        'place_type': '타지역업체' if is_other else '주업체'
                    })
                    
                    print(f"  [{idx+1}] {name} - {phone} → {'타지역' if is_other else '메인'}")
                    
                except Exception as e:
                    print(f"  ⚠️ 아이템 추출 실패: {str(e)}")
                    continue
            
            if not results:
                print(f"  ❌ '{keyword}': 추출된 결과 없음 (아이템은 {len(items)}개 발견)")
            else:
                print(f"  ✅ '{keyword}': {len(results)}개 결과 추출 완료")
            
        except Exception as e:
            print(f"❌ 결과 추출 오류: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return results
    
    async def _get_text(self, element, selectors: List[str]) -> str:
        """여러 셀렉터로 텍스트 추출 시도"""
        for selector in selectors:
            try:
                elem = await element.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return ""
    
    def _is_other_region(self, name: str, addr: str, phone: str, rating: str, 
                        keyword: str, image_url: str = "") -> bool:
        """메인/타지역 판정 (상호명 → 전화번호 순서)"""
        
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
        
        # 3순위: 주소 기반 (번지수 있으면 메인)
        if addr and addr != "주소 정보 없음":
            # 강력한 번지수 패턴
            detailed_patterns = [
                r'\d+-\d+',              # 123-45
                r'\d+\s*-\s*\d+',        # 123 - 45
                r'[동가]\s+\d+-\d+',      # 신사동 638-2, 저동2가 35-4
                r'[로길]\s+\d+',          # 압구정로 306
                r'[로길]\s*\d+번길',      # 선릉로 428번길
            ]
            
            for pattern in detailed_patterns:
                if re.search(pattern, addr):
                    return False  # 메인 (번지수 있음)
        
        # 4순위: 이미지 없으면 타지역 의심
        if not image_url or image_url == "":
            return True  # 타지역 의심
        
        # 5순위: 평점 없으면 타지역 의심
        if not rating or rating == "":
            return True  # 타지역 의심
        
        # 기본값: 메인
        return False


# 테스트용 실행
if __name__ == "__main__":
    async def test():
        crawler = NaverPlaceCrawler()
        results = await crawler.crawl("안산선불폰", max_results=5)
        
        print(f"\n✅ 크롤링 완료: {len(results)}개 업체")
        for r in results:
            print(f"  - {r['name']}: {r['phone']} ({r['place_type']})")
    
    asyncio.run(test())
