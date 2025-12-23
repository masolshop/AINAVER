#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 지도 크롤링 앱 (데모 버전)
간단한 웹 인터페이스로 네이버 지도에서 장소 정보를 검색합니다.

*** 이 버전은 데모/시뮬레이션 모드입니다 ***
실제 크롤링 기능을 사용하려면 로컬 컴퓨터에서 실행해주세요!
"""

from flask import Flask, render_template, request, jsonify, send_file
import time
import csv
import json
from datetime import datetime
import os
import random
import re

app = Flask(__name__)

# 데모 데이터 템플릿
DEMO_DATA_TEMPLATES = {
    '카페': {
        'names': ['스타벅스', '투썸플레이스', '이디야커피', '커피빈', '할리스', '탐앤탐스', '메가커피', '컴포즈커피', '폴바셋', '엔제리너스'],
        'categories': ['카페', '커피전문점', '디저트카페'],
        'phone_prefix': ['02', '010'],
        'ratings': ['4.2', '4.5', '4.7', '4.3', '4.6', '4.8', '4.1', '4.4'],
        'review_counts': ['120', '450', '89', '320', '780', '156', '520', '290']
    },
    '맛집': {
        'names': ['맛있는집', '행복한밥상', '진미식당', '황금손칼국수', '엄마손맛', '전통한정식', '퓨전레스토랑', '별미식당', '정성한끼', '요리조리'],
        'categories': ['한식', '일식', '중식', '양식', '분식', '고기집', '회/초밥'],
        'phone_prefix': ['02', '010', '031', '032'],
        'ratings': ['4.3', '4.6', '4.4', '4.7', '4.2', '4.5', '4.8'],
        'review_counts': ['230', '560', '178', '420', '890', '345', '610']
    },
    '병원': {
        'names': ['연세의원', '서울병원', '건강한의원', '튼튼정형외과', '밝은안과', '행복치과', '아름다운피부과', '희망내과'],
        'categories': ['병원', '의원', '내과', '외과', '피부과', '정형외과', '안과', '치과'],
        'phone_prefix': ['02', '031', '032'],
        'ratings': ['4.5', '4.7', '4.6', '4.8', '4.4'],
        'review_counts': ['67', '142', '89', '213', '156']
    },
    '편의점': {
        'names': ['GS25', 'CU', '세븐일레븐', '이마트24', '미니스톱'],
        'categories': ['편의점'],
        'phone_prefix': ['02', '031', '032'],
        'ratings': ['4.0', '4.1', '4.2', '3.9', '4.3'],
        'review_counts': ['45', '89', '123', '67', '91']
    }
}

class NaverMapCrawler:
    """데모 모드 크롤러 - 시뮬레이션 데이터 생성"""
    
    def __init__(self):
        self.demo_mode = True
        self.place_tab_keywords = [
            '맛집', '카페', '병원', '약국', '편의점', '음식점', '레스토랑',
            '미용실', '네일샵', '학원', '헬스장', '피트니스', '정형외과',
            '치과', '피부과', '안과', 'PC방', '노래방', '찜질방', '숙박',
            '호텔', '모텔', '게스트하우스', '빵집', '제과점', '분식',
            '술집', '바', '주점', '클럽', '마사지', '스파', '사우나',
            '세탁소', '부동산', '공인중개사', '동물병원', '애견샵'
        ]
        
    def check_place_tab(self, keyword):
        """플레이스 탭 표시 여부 확인 (시뮬레이션)"""
        keyword_lower = keyword.lower()
        has_place_tab = any(kw in keyword_lower for kw in self.place_tab_keywords)
        
        confidence = 'high' if has_place_tab else 'low'
        
        return {
            'has_place_tab': has_place_tab,
            'confidence': confidence,
            'keyword': keyword,
            'message': f"✅ 플레이스 탭 표시됨 (신뢰도: {confidence})" if has_place_tab else "❌ 플레이스 탭 없음"
        }
    
    def search_places(self, keyword, max_results=20):
        """시뮬레이션 데이터 생성"""
        print(f"🎭 데모 모드: '{keyword}' 검색 시뮬레이션")
        results = []
        
        # 키워드에서 카테고리 추출
        category_key = self._extract_category(keyword)
        template = DEMO_DATA_TEMPLATES.get(category_key, DEMO_DATA_TEMPLATES['맛집'])
        
        # 지역 추출 (예: "강남역", "홍대", "명동")
        locations = ['강남', '홍대', '신촌', '명동', '이태원', '여의도', '잠실', '건대', '신림', '수원']
        location = self._extract_location(keyword) or random.choice(locations)
        
        # 데이터 생성
        for i in range(min(max_results, len(template['names']) * 3)):
            place_data = self._generate_place_data(template, location, i)
            results.append(place_data)
            time.sleep(0.1)  # 실제 크롤링처럼 보이게
        
        print(f"✅ {len(results)}개의 시뮬레이션 데이터 생성 완료")
        return results
    
    def _extract_category(self, keyword):
        """키워드에서 카테고리 추출"""
        keyword_lower = keyword.lower()
        if '카페' in keyword or 'cafe' in keyword_lower or '커피' in keyword:
            return '카페'
        elif '병원' in keyword or '의원' in keyword or '클리닉' in keyword:
            return '병원'
        elif '편의점' in keyword:
            return '편의점'
        else:
            return '맛집'
    
    def _extract_location(self, keyword):
        """키워드에서 지역 추출"""
        locations = ['강남', '홍대', '신촌', '명동', '이태원', '여의도', '잠실', '건대', '신림', '수원', '판교', '분당']
        for loc in locations:
            if loc in keyword:
                return loc
        return None
    
    def _generate_place_data(self, template, location, index):
        """개별 장소 데이터 생성 (타지역업체 포함)"""
        name_base = template['names'][index % len(template['names'])]
        category = random.choice(template['categories'])
        
        # 20% 확률로 타지역업체 생성
        is_other_region = random.random() < 0.2
        
        # 지역별 상세 주소
        dong_list = ['동', '1가', '2가', '3가']
        street_list = ['중앙로', '역삼로', '테헤란로', '강남대로', '왕십리로', '성수길']
        
        if is_other_region:
            # 타지역업체: 동/구 단위 주소, 070번호, 짧은 상호명
            short_name = name_base[:10] if len(name_base) > 10 else name_base
            place_data = {
                'name': f"{short_name}",
                'category': category,
                'address': f"서울특별시 {location}{random.choice(dong_list)}",  # 동까지만
                'phone': f"070-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                'rating': '',  # 타지역업체는 평점 없음
                'reviews': '0',
                'is_other_region': True,
                'place_type': '타지역업체'
            }
        else:
            # 주업체: 상세주소, 일반번호, 평점/리뷰 있음
            place_data = {
                'name': f"{location} {name_base}" if index % 3 == 0 else f"{name_base} {location}점",
                'category': category,
                'address': f"서울특별시 {location}{random.choice(dong_list)} {random.choice(street_list)} {random.randint(1, 500)}",
                'phone': f"{random.choice(template['phone_prefix'])}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                'rating': random.choice(template['ratings']),
                'reviews': random.choice(template['review_counts']),
                'is_other_region': False,
                'place_type': '주업체'
            }
        
        return place_data
    
    def close(self):
        """데모 모드에서는 아무것도 하지 않음"""
        pass

# 전역 crawler 인스턴스
crawler = None

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/check-place-tab', methods=['POST'])
def check_place_tab():
    """플레이스 탭 확인 API"""
    global crawler
    
    try:
        data = request.json
        keyword = data.get('keyword', '')
        
        if not keyword:
            return jsonify({'error': '검색어를 입력해주세요.'}), 400
        
        # Crawler 초기화
        if crawler is None:
            crawler = NaverMapCrawler()
        
        # 플레이스 탭 확인
        result = crawler.check_place_tab(keyword)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/batch-check', methods=['POST'])
def batch_check():
    """일괄 키워드 검증 API"""
    global crawler
    
    try:
        data = request.json
        keywords = data.get('keywords', [])
        
        if not keywords:
            return jsonify({'error': '키워드를 입력해주세요.'}), 400
        
        # Crawler 초기화
        if crawler is None:
            crawler = NaverMapCrawler()
        
        # 일괄 검증
        results = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword:
                result = crawler.check_place_tab(keyword)
                results.append(result)
                time.sleep(0.1)  # 속도 제한
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'has_place_tab_count': sum(1 for r in results if r['has_place_tab'])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    """검색 API"""
    global crawler
    
    try:
        data = request.json
        keyword = data.get('keyword', '')
        max_results = int(data.get('max_results', 20))
        
        if not keyword:
            return jsonify({'error': '검색어를 입력해주세요.'}), 400
        
        # Crawler 초기화
        if crawler is None:
            crawler = NaverMapCrawler()
        
        # 플레이스 탭 확인
        place_tab_info = crawler.check_place_tab(keyword)
        
        # 검색 실행
        results = crawler.search_places(keyword, max_results)
        
        # 통계 계산
        total_count = len(results)
        other_region_count = sum(1 for r in results if r.get('is_other_region', False))
        main_places_count = total_count - other_region_count
        
        return jsonify({
            'success': True,
            'place_tab_info': place_tab_info,
            'results': results,
            'count': total_count,
            'statistics': {
                'total': total_count,
                'main_places': main_places_count,
                'other_region_places': other_region_count,
                'other_region_ratio': f"{(other_region_count/total_count*100):.1f}%" if total_count > 0 else "0%"
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST'])
def export_csv():
    """CSV 파일로 내보내기"""
    try:
        data = request.json
        results = data.get('results', [])
        keyword = data.get('keyword', 'search')
        
        if not results:
            return jsonify({'error': '저장할 데이터가 없습니다.'}), 400
        
        # CSV 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'naver_map_{keyword}_{timestamp}.csv'
        filepath = os.path.join('/home/user/webapp', filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'category', 'address', 'phone', 'rating', 'reviews', 'place_type'])
            writer.writeheader()
            writer.writerows(results)
        
        return jsonify({
            'success': True,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    """파일 다운로드"""
    filepath = os.path.join('/home/user/webapp', filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    # templates 디렉토리 생성
    os.makedirs('templates', exist_ok=True)
    
    print("=" * 70)
    print("🎭 네이버 지도 크롤링 앱 (데모 버전) 시작!")
    print("=" * 70)
    print("")
    print("⚠️  현재 데모/시뮬레이션 모드로 실행 중입니다!")
    print("    실제 네이버 지도 데이터 대신 시뮬레이션 데이터를 보여줍니다.")
    print("")
    print("💡 실제 크롤링 기능을 사용하려면:")
    print("    1. 이 코드를 로컬 컴퓨터에 다운로드")
    print("    2. pip install -r requirements.txt 실행")
    print("    3. playwright install chromium 실행")
    print("    4. 로컬에서 python naver_map_crawler.py 실행")
    print("")
    print("=" * 70)
    print("")
    print("📖 사용 방법:")
    print("    1. 웹 브라우저에서 아래 주소로 접속")
    print("    2. 검색어를 입력하고 '검색' 버튼 클릭")
    print("    3. 결과를 확인하고 'CSV로 저장' 버튼으로 저장")
    print("")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5003, debug=False)
