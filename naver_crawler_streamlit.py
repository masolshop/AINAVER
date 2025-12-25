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
        self.user_agent = (
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
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 375, 'height': 667},
                device_scale_factor=2,
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )
            
            # 봇 감지 우회 스크립트
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
            """)
            
            page = await context.new_page()
            
            try:
                # 네이버 플레이스 검색
                search_url = f"https://m.place.naver.com/search?query={keyword}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                # 검색 결과 추출
                results = await self._extract_results(page, keyword, max_results)
                
                return results
                
            except Exception as e:
                print(f"❌ 크롤링 오류: {str(e)}")
                return []
            
            finally:
                await browser.close()
    
    async def _extract_results(self, page, keyword: str, max_results: int) -> List[Dict]:
        """검색 결과 추출"""
        results = []
        
        try:
            # 검색 결과 로드 대기
            await asyncio.sleep(2)
            
            # 스크롤하여 더 많은 결과 로드
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
            
            # 플레이스 아이템 찾기
            items = await page.query_selector_all('li[data-index]')
            
            if not items:
                # 대체 셀렉터 시도
                items = await page.query_selector_all('.item_inner')
            
            if not items:
                items = await page.query_selector_all('[class*="place"]')
            
            print(f"  → 발견된 아이템 수: {len(items)}")
            
            # 각 아이템에서 정보 추출
            for idx, item in enumerate(items[:max_results]):
                try:
                    # 상호명
                    name = await self._get_text(item, ['.YwYLL', '.TYaxT', 'a.BwZrK', '[class*="name"]'])
                    if not name:
                        continue
                    
                    # 카테고리
                    category = await self._get_text(item, ['.KCMnt', '[class*="category"]'])
                    
                    # 주소
                    addr = await self._get_text(item, ['.LDgIH', '[class*="addr"]', '[class*="address"]'])
                    
                    # 전화번호 - 여러 방법으로 시도
                    phone = await self._get_text(item, [
                        'a[href^="tel:"]',
                        '.dry6Z',
                        '[class*="phone"]',
                        '[class*="tel"]'
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
            
        except Exception as e:
            print(f"❌ 결과 추출 오류: {str(e)}")
        
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
