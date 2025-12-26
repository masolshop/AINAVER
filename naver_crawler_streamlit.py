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
                    
                    # searchIframe 찾기 - 실제 검색 결과가 있는 iframe
                    search_frame = None
                    for frame in frames:
                        # pcmap.place.naver.com 또는 m.place.naver.com의 list URL
                        if 'place.naver.com/place/list' in frame.url or 'searchIframe' in frame.name:
                            search_frame = frame
                            print(f"✓ 검색 결과 iframe 발견: {frame.url[:100]}...")
                            break
                    
                    # 못 찾았으면 URL에 'place'가 포함된 iframe 찾기
                    if not search_frame:
                        for frame in frames:
                            if 'place.naver.com' in frame.url and frame.url != page.url:
                                search_frame = frame
                                print(f"✓ 플레이스 iframe 발견: {frame.url[:100]}...")
                                break
                    
                    # iframe이 있으면 그 안에서 추출, 없으면 메인 페이지에서 추출
                    if search_frame:
                        results = await self._extract_results(search_frame, keyword, max_results, main_page=page)
                    else:
                        print("⚠️ 검색 iframe 없음, 메인 페이지에서 추출 시도")
                        results = await self._extract_results(page, keyword, max_results, main_page=page)
                    
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
    
    async def _extract_results(self, page, keyword: str, max_results: int, main_page=None) -> List[Dict]:
        """검색 결과 추출"""
        results = []
        
        # main_page가 없으면 page를 사용 (하위 호환성)
        if main_page is None:
            main_page = page
        
        try:
            print(f"\n🔍 '{keyword}' 검색 결과 추출 시작... (v2.0 - 자동 셀렉터)")
            
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
            
            # HTML 전체 저장 (디버깅용)
            full_html = await page.content()
            import os
            debug_file = "/tmp/naver_place_debug.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            print(f"  📝 전체 HTML 저장됨: {debug_file} ({len(full_html)} 문자)")
            
            # 플레이스 아이템 찾기 - 여러 셀렉터 시도
            print("  → 셀렉터로 아이템 찾는 중...")
            
            # 시도할 모든 셀렉터 (iframe 내부용)
            selectors = [
                # PC 데스크톱 검색 결과 (pcmap.place.naver.com/place/list)
                # 각 검색 결과는 ul 안의 li.VLTHu 내부의 개별 div
                ('ul > li.VLTHu > div.qbGlu', 'ul > li > div.qbGlu (개별 검색 결과)'),  # 최우선
                ('div.qbGlu', 'div.qbGlu (검색 결과 카드)'),
                ('li.VLTHu', 'li.VLTHu (PC 검색 결과 리스트)'),
                ('li.UEzoS', 'li.UEzoS (PC 검색 결과)'),
                ('ul.place_section_content > li', 'ul.place_section_content > li'),
                ('.place_list li', '.place_list li'),
                
                # 모바일 검색 결과
                ('li._YwYLL', 'li._YwYLL (모바일)'),
                ('li[data-index]', 'li[data-index]'),
                ('.item_inner', '.item_inner'),
                
                # 일반 (UI 요소 제외)
                ('ul.place_list > li', 'ul.place_list > li'),
                ('div[role="list"] > div', 'div[role="list"] > div'),
            ]
            
            items = []
            max_found = 0
            selected_selector_name = ""
            
            print("  → 모든 셀렉터 시도 중...")
            
            # 모든 셀렉터를 시도하고 가장 많은 아이템을 찾은 것 선택
            for selector, name in selectors:
                found = await page.query_selector_all(selector)
                count = len(found)
                print(f"    • {name}: {count}개")
                
                # 최소 3개 이상이고, 이전보다 많으면 업데이트
                if count >= 3 and count > max_found:
                    items = found
                    max_found = count
                    selected_selector_name = name
                    print(f"      → 현재 최적: {name} ({count}개)")
            
            # 3개 미만이면 첫 번째로 발견한 것 사용
            if not items:
                print("  ⚠️ 3개 이상 찾지 못함, 첫 번째 셀렉터 사용")
                for selector, name in selectors:
                    found = await page.query_selector_all(selector)
                    if found:
                        items = found
                        selected_selector_name = name
                        break
            
            print(f"\n  ✅ 최종 선택된 셀렉터: {selected_selector_name}")
            print(f"  ✅ 최종 발견된 아이템 수: {len(items)}")
            
            # ========== 1단계: 리스트에서 기본 정보만 수집 (iframe detach 방지) ==========
            print(f"\n📋 1단계: 리스트에서 기본 정보 수집 중...")
            temp_items = []
            
            for idx, item in enumerate(items[:max_results]):
                try:
                    print(f"  [{idx+1}] 아이템 처리 중...")
                    
                    # 상호명 - YwYLL만 사용
                    name = ""
                    ywyll_elem = await item.query_selector('.YwYLL')
                    if ywyll_elem:
                        name = await ywyll_elem.inner_text()
                        name = name.strip() if name else ""
                    
                    if not name:
                        place_link = await item.query_selector('a.place_bluelink')
                        if place_link:
                            name = await place_link.inner_text()
                            name = name.strip() if name else ""
                    
                    if not name:
                        print(f"    ⚠️ 상호명 없음, 스킵")
                        continue
                    
                    # 주소
                    addr = ""
                    addr_elem = await item.query_selector('.Pb4bU')
                    if addr_elem:
                        addr = await addr_elem.inner_text()
                        addr = addr.strip() if addr else ""
                    
                    # 카테고리
                    category = await self._get_text(item, ['.YzBgS', 'span.YzBgS'])
                    
                    # 평점
                    rating = await self._get_text(item, ['.h69bs', '[class*="rating"]'])
                    
                    # 리뷰 수
                    reviews = await self._get_text(item, ['.AQ85', '[class*="review"]'])
                    
                    # 이미지
                    img_elem = await item.query_selector('img')
                    image_url = ""
                    if img_elem:
                        image_url = await img_elem.get_attribute('src') or ""
                    
                    # 상세 페이지 href 저장 (나중에 방문)
                    detail_href = ""
                    place_link = await item.query_selector('a.place_bluelink')
                    if place_link:
                        detail_href = await place_link.get_attribute('href')
                        if detail_href and not detail_href.startswith('http'):
                            detail_href = f"https://map.naver.com{detail_href}"
                    
                    if idx < 3:
                        print(f"    → detail_href: {detail_href[:80] if detail_href else '없음'}")
                    
                    temp_items.append({
                        'name': name,
                        'category': category or "미분류",
                        'address': addr or "주소 정보 없음",
                        'rating': rating or "",
                        'reviews': reviews or "",
                        'image_url': image_url,
                        'detail_href': detail_href
                    })
                    
                    print(f"    ✓ {name} - 기본 정보 수집 완료 (href: {'있음' if detail_href else '없음'})")
                    
                except Exception as e:
                    print(f"    ⚠️ 아이템 추출 실패: {str(e)}")
                    continue
            
            print(f"\n✅ 1단계 완료: {len(temp_items)}개 업체 기본 정보 수집")
            
            # ========== 2단계: 상세 페이지에서 전화번호 수집 ==========
            print(f"\n📞 2단계: 상세 페이지에서 전화번호 수집 중...")
            print(f"  → 수집할 업체 수: {len(temp_items)}개")
            
            for idx, temp_item in enumerate(temp_items):
                try:
                    print(f"\n  [{idx+1}/{len(temp_items)}] {temp_item['name']} 전화번호 수집 중...")
                    
                    phone = ""
                    
                    # detail_href 확인
                    if not temp_item['detail_href']:
                        print(f"    ⚠️ detail_href 없음, 스킵")
                        # 전화번호 없이 결과 추가
                        is_other = self._is_other_region(
                            temp_item['name'], 
                            temp_item['address'], 
                            "", 
                            temp_item['rating'], 
                            keyword, 
                            temp_item['image_url']
                        )
                        
                        results.append({
                            'name': temp_item['name'],
                            'category': temp_item['category'],
                            'address': temp_item['address'],
                            'phone': "전화번호 없음",
                            'rating': temp_item['rating'],
                            'reviews': temp_item['reviews'],
                            'image_url': temp_item['image_url'],
                            'is_other_region': is_other,
                            'place_type': '타지역업체' if is_other else '주업체'
                        })
                        continue
                    
                    print(f"    → href: {temp_item['detail_href'][:80]}...")
                    
                    # 상세 페이지 방문
                    if temp_item['detail_href']:
                        try:
                            print(f"    → 페이지 이동 중...")
                            await main_page.goto(temp_item['detail_href'], wait_until='networkidle', timeout=30000)
                            await asyncio.sleep(2)
                            
                            # place iframe 찾기
                            print(f"    → iframe 수: {len(main_page.frames)}")
                            place_frame_found = False
                            
                            for frame_idx, frame in enumerate(main_page.frames):
                                if 'place' in frame.url.lower():
                                    place_frame_found = True
                                    print(f"    → place iframe 발견: Frame {frame_idx}")
                                    await asyncio.sleep(1)
                                    detail_html = await frame.content()
                                    print(f"    → HTML 길이: {len(detail_html)}")
                                    
                                    # tel: 링크 찾기
                                    tel_elem = await frame.query_selector('a[href^="tel:"]')
                                    if tel_elem:
                                        tel_href = await tel_elem.get_attribute('href')
                                        if tel_href:
                                            phone = tel_href.replace('tel:', '').strip()
                                            print(f"    ✅ tel: 링크에서 전화번호: {phone}")
                                            break
                                    else:
                                        print(f"    → tel: 링크 없음")
                                    
                                    # HTML에서 직접 찾기
                                    if not phone:
                                        tel_match = re.search(r'href=["\']tel:([0-9\-]+)["\']', detail_html)
                                        if tel_match:
                                            phone = tel_match.group(1).strip()
                                            print(f"    ✅ HTML에서 전화번호: {phone}")
                                            break
                                        else:
                                            print(f"    → HTML에서 tel: 패턴 없음")
                                    
                                    # 정규식으로 찾기
                                    if not phone:
                                        phone_patterns = [
                                            r'(070[-]\d{3,4}[-]\d{4})',
                                            r'(0\d{1,2}[-]\d{3,4}[-]\d{4})',
                                            r'(1\d{3}[-]\d{4})',
                                        ]
                                        for pattern in phone_patterns:
                                            match = re.search(pattern, detail_html)
                                            if match:
                                                temp_phone = match.group(1)
                                                if not re.match(r'^\d{8}$', temp_phone.replace('-', '')):
                                                    phone = temp_phone
                                                    print(f"    ✅ 정규식으로 전화번호: {phone}")
                                                    break
                                        
                                        if not phone:
                                            print(f"    → 정규식으로도 전화번호 없음")
                                    
                                    if phone:
                                        break
                            
                            if not place_frame_found:
                                print(f"    ⚠️ place iframe을 찾지 못함")
                        
                        except Exception as e:
                            print(f"    ⚠️ 상세 페이지 열기 실패: {str(e)[:100]}")
                    
                    # 최종 결과 추가
                    is_other = self._is_other_region(
                        temp_item['name'], 
                        temp_item['address'], 
                        phone, 
                        temp_item['rating'], 
                        keyword, 
                        temp_item['image_url']
                    )
                    
                    results.append({
                        'name': temp_item['name'],
                        'category': temp_item['category'],
                        'address': temp_item['address'],
                        'phone': phone or "전화번호 없음",
                        'rating': temp_item['rating'],
                        'reviews': temp_item['reviews'],
                        'image_url': temp_item['image_url'],
                        'is_other_region': is_other,
                        'place_type': '타지역업체' if is_other else '주업체'
                    })
                    
                    print(f"  [{idx+1}] {temp_item['name']} - {phone or '전화번호 없음'} → {'타지역' if is_other else '메인'}")
                    
                except Exception as e:
                    print(f"  ⚠️ 전화번호 수집 실패: {str(e)[:100]}")
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
    
    async def _get_text(self, element, selectors: List[str], debug_name: str = "") -> str:
        """여러 셀렉터로 텍스트 추출 시도"""
        for idx, selector in enumerate(selectors):
            try:
                elem = await element.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if text and text.strip():
                        if debug_name:
                            print(f"      → {debug_name} 추출 성공: '{selector}' = '{text.strip()[:50]}'")
                        return text.strip()
            except:
                continue
        return ""
    
    def _is_other_region(self, name: str, addr: str, phone: str, rating: str, 
                        keyword: str, image_url: str = "") -> bool:
        """메인/타지역 판정 (상호명 → 전화번호 순서)"""
        
        # 1순위: 상호명 "흥신소" 정확히 3글자 = 무조건 타지역
        if name and name.strip() == "흥신소":
            return True  # 흥신소(3글자만) = 무조건 타지역
        
        # 2순위: 전화번호 070 = 무조건 타지역
        if phone and phone != "-" and phone != "전화번호 없음":
            # 070 번호 = 인터넷 전화 = 타지역
            if '070' in phone or phone.startswith('070'):
                return True  # 타지역
            
            # 유효한 전화번호가 있고 070이 아니면 메인
            if re.search(r'\d', phone):
                return False  # 메인
        
        # 전화번호 없으면 타지역 (의심)
        
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
