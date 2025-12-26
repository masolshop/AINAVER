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
                    
                    # 디버깅: 처음 3개 아이템 HTML 출력
                    if idx < 3:
                        item_html = await item.inner_html()
                        print(f"    → 아이템 HTML 길이: {len(item_html)}")
                        # YwYLL 클래스 찾기
                        ywyll_test = await item.query_selector_all('.YwYLL')
                        print(f"    → YwYLL 요소 수: {len(ywyll_test)}")
                        for yw_idx, yw in enumerate(ywyll_test[:3]):
                            yw_text = await yw.inner_text()
                            print(f"      YwYLL[{yw_idx}]: {yw_text[:50]}")
                    
                    # 상호명 - place_bluelink 안의 YwYLL만 사용 (정확도 향상)
                    name = ""
                    place_link_for_name = await item.query_selector('a.place_bluelink')
                    if place_link_for_name:
                        ywyll_elem = await place_link_for_name.query_selector('.YwYLL')
                        if ywyll_elem:
                            name = await ywyll_elem.inner_text()
                            name = name.strip() if name else ""
                    
                    # 실패하면 전체에서 첫 번째 YwYLL 찾기
                    if not name:
                        ywyll_elem = await item.query_selector('.YwYLL')
                        if ywyll_elem:
                            name = await ywyll_elem.inner_text()
                            name = name.strip() if name else ""
                    
                    if not name:
                        print(f"    ⚠️ 상호명 없음, 스킵")
                        continue
                    
                    if idx < 3:
                        print(f"    → 상호명: {name}")
                    
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
                    
                    # 상세 페이지 링크 요소만 저장 (나중에 클릭)
                    # href는 '#'이므로 사용 불가, 클릭 이벤트 필요
                    place_link = await item.query_selector('a.place_bluelink')
                    
                    if idx < 3:
                        if place_link:
                            href_attr = await place_link.get_attribute('href')
                            print(f"    → place_link 있음 (href: {href_attr})")
                        else:
                            print(f"    → place_link 없음")
                    
                    temp_items.append({
                        'name': name,
                        'category': category or "미분류",
                        'address': addr or "주소 정보 없음",
                        'rating': rating or "",
                        'reviews': reviews or "",
                        'item_element': item  # 아이템 요소 자체를 저장
                    })
                    
                    print(f"    ✓ {name} - 기본 정보 수집 완료 (link: {'있음' if place_link else '없음'})")
                    
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
                    
                    # 아이템 요소에서 링크 찾기
                    try:
                        item_elem = temp_item['item_element']
                        place_link = await item_elem.query_selector('a.place_bluelink')
                        
                        if not place_link:
                            print(f"    ⚠️ place_link 없음, 스킵")
                            # 전화번호 없이 결과 추가
                            is_other = self._is_other_region(
                                temp_item['name'], 
                                temp_item['address'], 
                                "", 
                                temp_item['rating'], 
                                keyword
                            )
                            
                            results.append({
                                'name': temp_item['name'],
                                'category': temp_item['category'],
                                'address': temp_item['address'],
                                'phone': "전화번호 없음",
                                'rating': temp_item['rating'],
                                'reviews': temp_item['reviews'],
                                'is_other_region': is_other,
                                'place_type': '타지역업체' if is_other else '주업체'
                            })
                            continue
                        
                        print(f"    → 링크 클릭 시도...")
                        
                        # 현재 URL 저장
                        old_url = main_page.url
                        
                        # 링크 클릭 (JavaScript 이벤트 실행)
                        await place_link.click()
                        
                        # URL 변경 대기 (최대 5초)
                        try:
                            await main_page.wait_for_url(lambda url: url != old_url, timeout=5000)
                            print(f"    → 상세 페이지로 이동 완료")
                        except:
                            print(f"    ⚠️ URL 변경 없음 (타임아웃)")
                        
                        await asyncio.sleep(3)  # 추가 로딩 대기 (3초로 증가)
                        
                        # 현재 메인 페이지 URL 확인
                        current_main_url = main_page.url
                        if idx < 3:
                            print(f"    → 현재 메인 페이지 URL: {current_main_url[:100]}")
                        
                        # place iframe 찾기
                        print(f"    → iframe 수: {len(main_page.frames)}")
                        place_frame_found = False
                        
                        # 모든 프레임 URL 출력 (처음 3개 아이템만)
                        if idx < 3:
                            for frame_idx, frame in enumerate(main_page.frames):
                                print(f"      Frame {frame_idx}: {frame.url}")
                        
                        for frame_idx, frame in enumerate(main_page.frames):
                            frame_url = frame.url.lower()
                            
                            # pcmap.place.naver.com/place/XXX/home 또는 /entry 형태만 매칭
                            # (placePath=/home 파라미터는 제외)
                            is_detail_page = (
                                'pcmap.place.naver.com/place/' in frame_url and
                                ('/home' in frame_url or '/entry' in frame_url) and
                                'placepath=' not in frame_url  # URL 파라미터 제외
                            )
                            
                            if is_detail_page:
                                place_frame_found = True
                                print(f"    → place 상세 iframe 발견: Frame {frame_idx}")
                                await asyncio.sleep(2)  # 대기 시간 증가
                                detail_html = await frame.content()
                                print(f"    → HTML 길이: {len(detail_html)}")
                                
                                # 1. tel: 링크 찾기 (가장 확실한 방법)
                                tel_elem = await frame.query_selector('a[href^="tel:"]')
                                if tel_elem:
                                    tel_href = await tel_elem.get_attribute('href')
                                    if tel_href:
                                        phone = tel_href.replace('tel:', '').strip()
                                        print(f"    ✅ tel: 링크에서 전화번호: {phone}")
                                        break
                                else:
                                    if idx < 3:
                                        print(f"    → tel: 링크 없음, 다른 방법 시도...")
                                
                                # 2. 다양한 셀렉터로 전화번호 요소 직접 찾기
                                if not phone:
                                    phone_selectors = [
                                        'span.xlx7Q',  # PC 상세 페이지 전화번호
                                        'span[class*="phone"]',
                                        'div[class*="phone"]',
                                        'a.phone',
                                        '.contact_number',
                                        '[data-phone]',
                                    ]
                                    
                                    for selector in phone_selectors:
                                        try:
                                            phone_elem = await frame.query_selector(selector)
                                            if phone_elem:
                                                phone_text = await phone_elem.inner_text()
                                                if phone_text and re.search(r'\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}', phone_text):
                                                    phone = phone_text.strip()
                                                    print(f"    ✅ 셀렉터({selector})에서 전화번호: {phone}")
                                                    break
                                        except:
                                            continue
                                
                                # 3. HTML에서 직접 찾기
                                if not phone:
                                    tel_match = re.search(r'href=["\']tel:([0-9\-]+)["\']', detail_html)
                                    if tel_match:
                                        phone = tel_match.group(1).strip()
                                        print(f"    ✅ HTML에서 전화번호: {phone}")
                                        break
                                    else:
                                        if idx < 3:
                                            print(f"    → HTML에서 tel: 패턴 없음")
                                
                                # 4. 정규식으로 찾기 (다양한 패턴 지원)
                                if not phone:
                                    phone_patterns = [
                                        r'(0507[-\s]?\d{4}[-\s]?\d{4})',     # 0507-xxxx-xxxx (네이버 대표)
                                        r'(070[-\s]?\d{3,4}[-\s]?\d{4})',    # 070-xxx-xxxx
                                        r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})',  # 02-xxx-xxxx, 031-xxx-xxxx
                                        r'(1\d{3}[-\s]?\d{4})',           # 1588-xxxx
                                    ]
                                    for pattern in phone_patterns:
                                        match = re.search(pattern, detail_html)
                                        if match:
                                            temp_phone = match.group(1).strip()
                                            # 하이픈 정규화
                                            temp_phone = re.sub(r'\s+', '-', temp_phone)
                                            # 날짜 제외 (8자리 연속 숫자)
                                            if not re.match(r'^\d{8}$', temp_phone.replace('-', '')):
                                                phone = temp_phone
                                                print(f"    ✅ 정규식으로 전화번호: {phone}")
                                                break
                                    
                                    if not phone and idx < 3:
                                        print(f"    → 정규식으로도 전화번호 없음")
                                        # HTML 일부 출력 (디버깅용)
                                        print(f"    → HTML 샘플 (1000-1500자): {detail_html[1000:1500]}")
                                
                                if phone:
                                    break
                        
                        if not place_frame_found:
                            print(f"    ⚠️ place 상세 iframe을 찾지 못함")
                            if idx < 3:
                                print(f"    ⚠️ 상세 페이지로 이동하지 않았을 가능성 - 메인 URL: {main_page.url[:100]}")
                        
                        # 뒤로 가기 (리스트로 돌아가기)
                        await main_page.go_back()
                        await asyncio.sleep(1)
                    
                    except Exception as e:
                        print(f"    ⚠️ 상세 페이지 열기 실패: {str(e)[:100]}")
                    
                    # 최종 결과 추가
                    is_other = self._is_other_region(
                        temp_item['name'], 
                        temp_item['address'], 
                        phone, 
                        temp_item['rating'], 
                        keyword
                    )
                    
                    results.append({
                        'name': temp_item['name'],
                        'category': temp_item['category'],
                        'address': temp_item['address'],
                        'phone': phone or "전화번호 없음",
                        'rating': temp_item['rating'],
                        'reviews': temp_item['reviews'],
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
                        keyword: str) -> bool:
        """메인/타지역 판정"""
        
        # 1순위: 상호명 "흥신소" 정확히 3글자 = 무조건 타지역
        if name and name.strip() == "흥신소":
            return True  # 흥신소(3글자만) = 무조건 타지역
        
        # 2순위: 전화번호 기반 판정
        if phone and phone != "-" and phone != "전화번호 없음":
            # 0507 = 네이버 플레이스 대표번호 = 100% 메인
            if '0507' in phone or phone.startswith('0507'):
                return False  # 메인 (네이버 대표번호)
            
            # 070 = 인터넷 전화 = 타지역
            if '070' in phone or phone.startswith('070'):
                return True  # 타지역
            
            # 유효한 전화번호가 있고 070이 아니면 메인
            if re.search(r'\d', phone):
                return False  # 메인 (031, 02, 1588 등 일반 전화번호)
        
        # 3순위: 전화번호 없으면 메인 (기본값)
        return False  # 메인 (전화번호 없음도 메인으로 처리)


# 테스트용 실행
if __name__ == "__main__":
    async def test():
        crawler = NaverPlaceCrawler()
        results = await crawler.crawl("안산선불폰", max_results=5)
        
        print(f"\n✅ 크롤링 완료: {len(results)}개 업체")
        for r in results:
            print(f"  - {r['name']}: {r['phone']} ({r['place_type']})")
    
    asyncio.run(test())
