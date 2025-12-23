#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 실제 크롤링 모듈
타지역업체 자동 감지 기능 포함
"""

from playwright.sync_api import sync_playwright
import time
import re
from urllib.parse import quote

class RealNaverPlaceCrawler:
    """실제 네이버 플레이스 크롤러"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        
        # 플레이스 탭을 표시하는 키워드 패턴
        self.place_keywords = [
            '맛집', '카페', '병원', '약국', '편의점', '음식점', '레스토랑',
            '미용실', '네일샵', '학원', '헬스장', '피트니스', '정형외과',
            '치과', '피부과', '안과', 'PC방', '노래방', '찜질방', '숙박',
            '호텔', '모텔', '게스트하우스', '빵집', '제과점', '분식',
            '술집', '바', '주점', '클럽', '마사지', '스파', '사우나',
            '세탁소', '부동산', '공인중개사', '동물병원', '애견샵'
        ]
    
    def start(self):
        """브라우저 시작"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            print("✅ 브라우저 시작 완료")
            return True
        except Exception as e:
            print(f"❌ 브라우저 시작 실패: {e}")
            return False
    
    def check_place_tab(self, keyword):
        """플레이스 탭 표시 여부 확인"""
        try:
            if not self.page:
                self.start()
            
            # 네이버 검색
            search_url = f"https://search.naver.com/search.naver?query={quote(keyword)}"
            self.page.goto(search_url, wait_until="domcontentloaded", timeout=10000)
            time.sleep(2)
            
            # 플레이스 탭 확인
            place_tab_selectors = [
                'a[data-tab="place"]',
                'a.tab[href*="place"]',
                '.api_subject_bx a[href*="place"]',
                'a:has-text("플레이스")'
            ]
            
            has_place_tab = False
            for selector in place_tab_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        has_place_tab = True
                        break
                except:
                    continue
            
            # 키워드 기반 추가 확인
            keyword_match = any(kw in keyword.lower() for kw in self.place_keywords)
            
            confidence = 'high' if has_place_tab else ('medium' if keyword_match else 'low')
            
            return {
                'has_place_tab': has_place_tab,
                'confidence': confidence,
                'keyword': keyword,
                'message': f"✅ 플레이스 탭 표시됨 (신뢰도: {confidence})" if has_place_tab else "❌ 플레이스 탭 없음"
            }
        except Exception as e:
            print(f"❌ 플레이스 탭 확인 오류: {e}")
            return {
                'has_place_tab': False,
                'confidence': 'error',
                'keyword': keyword,
                'message': f"오류 발생: {str(e)}"
            }
    
    def search_places(self, keyword, max_results=20):
        """네이버 플레이스 검색 및 타지역업체 감지"""
        try:
            if not self.page:
                self.start()
            
            print(f"🔍 '{keyword}' 검색 시작...")
            
            # 네이버 지도로 이동
            map_url = f"https://map.naver.com/p/search/{quote(keyword)}"
            self.page.goto(map_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            # iframe으로 전환
            try:
                iframe = self.page.frame(name="searchIframe")
                if not iframe:
                    print("❌ searchIframe을 찾을 수 없습니다")
                    return []
            except Exception as e:
                print(f"❌ iframe 오류: {e}")
                return []
            
            results = []
            
            # 스크롤하면서 데이터 수집
            for scroll_count in range(5):  # 최대 5번 스크롤
                # 장소 목록 가져오기
                place_items = iframe.query_selector_all('li[role="listitem"]')
                
                print(f"📍 현재 {len(place_items)}개 항목 발견")
                
                for item in place_items:
                    if len(results) >= max_results:
                        break
                    
                    try:
                        place_data = self._extract_place_data(iframe, item, keyword)
                        if place_data and not self._is_duplicate(results, place_data):
                            results.append(place_data)
                            print(f"  ✅ {place_data['name']} - {place_data['place_type']}")
                    except Exception as e:
                        print(f"  ⚠️ 항목 추출 오류: {e}")
                        continue
                
                if len(results) >= max_results:
                    break
                
                # 스크롤
                try:
                    scroll_area = iframe.query_selector('.Ryr1F')  # 스크롤 영역
                    if scroll_area:
                        iframe.evaluate('(element) => element.scrollTop += 1000', scroll_area)
                        time.sleep(1)
                except:
                    pass
            
            print(f"✅ 총 {len(results)}개 결과 수집 완료")
            return results
            
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_place_data(self, iframe, item, keyword):
        """개별 장소 데이터 추출 및 타지역업체 판단"""
        try:
            # 상호명
            name_elem = item.query_selector('.TYaxT, .place_bluelink, span.YwYLL')
            name = name_elem.inner_text().strip() if name_elem else ""
            
            if not name:
                return None
            
            # 카테고리
            category_elem = item.query_selector('.KCMnt, span.nQ2b9')
            category = category_elem.inner_text().strip() if category_elem else ""
            
            # 주소
            address_elem = item.query_selector('.LDgIH, .addr')
            address = address_elem.inner_text().strip() if address_elem else ""
            
            # 전화번호
            phone_elem = item.query_selector('.dry6Z, .tel')
            phone = phone_elem.inner_text().strip() if phone_elem else ""
            
            # 평점
            rating_elem = item.query_selector('.h69bs, .score')
            rating = rating_elem.inner_text().strip() if rating_elem else ""
            
            # 리뷰 수
            review_elem = item.query_selector('.Tvqnp, .cnt')
            reviews = review_elem.inner_text().strip() if review_elem else "0"
            reviews = re.sub(r'[^0-9]', '', reviews)
            
            # 타지역업체 판단
            is_other_region = self._detect_other_region_place(
                name, address, phone, rating, reviews, keyword
            )
            
            place_data = {
                'name': name,
                'category': category,
                'address': address,
                'phone': phone,
                'rating': rating,
                'reviews': reviews,
                'is_other_region': is_other_region,
                'place_type': '타지역업체' if is_other_region else '주업체'
            }
            
            return place_data
            
        except Exception as e:
            print(f"⚠️ 데이터 추출 오류: {e}")
            return None
    
    def _detect_other_region_place(self, name, address, phone, rating, reviews, keyword):
        """타지역업체 감지 알고리즘"""
        indicators = 0
        
        # 1. 070 가상번호 사용
        if phone.startswith('070'):
            indicators += 3  # 가중치 높음
        
        # 2. 주소가 동/구 단위만 (상세주소 없음)
        if address:
            # "서울 강남구 역삼동" 형태인지 확인
            address_parts = address.split()
            if len(address_parts) <= 3 or not any(char.isdigit() for char in address):
                # 번지수나 상세주소 없음
                indicators += 2
        
        # 3. 평점 없음
        if not rating or rating == "":
            indicators += 1
        
        # 4. 리뷰 수 0 또는 매우 적음
        if reviews == "0" or (reviews and int(reviews) < 3):
            indicators += 1
        
        # 5. 상호명에 검색 키워드 포함 (타지역업체 특징)
        # 예: "홍대치킨" 검색 시 "홍대치킨배달", "홍대치킨전문점" 등
        if keyword:
            # 키워드를 단어로 분리
            keyword_clean = re.sub(r'[^\w\s]', '', keyword)
            keyword_words = keyword_clean.split()
            
            # 상호명에 키워드가 포함되어 있는지
            if any(word in name for word in keyword_words if len(word) > 1):
                indicators += 2
        
        # 6. 상호명 길이 짧음 (30자 이하 - 타지역업체 제약)
        if len(name) <= 30:
            indicators += 0.5
        
        # 판단: 4점 이상이면 타지역업체
        return indicators >= 4
    
    def _is_duplicate(self, results, new_place):
        """중복 확인"""
        for place in results:
            if place['name'] == new_place['name'] and place['address'] == new_place['address']:
                return True
        return False
    
    def close(self):
        """브라우저 종료"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("✅ 브라우저 종료")
        except Exception as e:
            print(f"⚠️ 종료 오류: {e}")


# 테스트 코드
if __name__ == "__main__":
    crawler = RealNaverPlaceCrawler(headless=True)
    
    # 플레이스 탭 확인 테스트
    print("\n=== 플레이스 탭 확인 테스트 ===")
    result = crawler.check_place_tab("강남역 맛집")
    print(result)
    
    # 장소 검색 테스트
    print("\n=== 장소 검색 테스트 ===")
    places = crawler.search_places("강남역 맛집", max_results=10)
    
    print(f"\n총 {len(places)}개 결과:")
    for i, place in enumerate(places, 1):
        print(f"{i}. {place['name']} - {place['place_type']}")
        print(f"   주소: {place['address']}")
        print(f"   전화: {place['phone']}")
    
    crawler.close()
