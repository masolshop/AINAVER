#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 지도 크롤링 앱
간단한 웹 인터페이스로 네이버 지도에서 장소 정보를 검색합니다.
"""

from flask import Flask, render_template, request, jsonify, send_file
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import csv
import json
from datetime import datetime
import os
import re

app = Flask(__name__)

class NaverMapCrawler:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
    def setup_browser(self):
        """Playwright 브라우저 설정"""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
        
    def search_places(self, keyword, max_results=20):
        """네이버 지도에서 장소 검색"""
        self.setup_browser()
        results = []
        
        page = self.context.new_page()
        
        try:
            # 네이버 지도 접속
            url = f"https://map.naver.com/v5/search/{keyword}"
            print(f"Accessing: {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(3)
            
            # iframe으로 전환
            try:
                iframe_element = page.wait_for_selector("iframe#searchIframe", timeout=10000)
                iframe = iframe_element.content_frame()
                print("Switched to iframe")
            except:
                print("No iframe found, using main page")
                iframe = page
            
            time.sleep(2)
            
            # 검색 결과 컨테이너 찾기
            try:
                iframe.wait_for_selector("div.Ryr1F", timeout=10000)
                print("Found results container")
            except:
                print("Results container not found")
                return results
            
            collected = 0
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 20
            
            while collected < max_results and scroll_attempts < max_scroll_attempts:
                # 현재 보이는 장소들 가져오기
                place_elements = iframe.query_selector_all("li.UEzoS")
                
                for i, place in enumerate(place_elements[collected:]):
                    if collected >= max_results:
                        break
                        
                    try:
                        place_data = {}
                        
                        # 장소명
                        try:
                            name_el = place.query_selector("span.TYaxT")
                            place_data['name'] = name_el.inner_text() if name_el else ''
                        except:
                            place_data['name'] = ''
                        
                        # 카테고리
                        try:
                            category_el = place.query_selector("span.KCMnt")
                            place_data['category'] = category_el.inner_text() if category_el else ''
                        except:
                            place_data['category'] = ''
                        
                        # 주소
                        try:
                            address_el = place.query_selector("span.LDgIH")
                            place_data['address'] = address_el.inner_text() if address_el else ''
                        except:
                            place_data['address'] = ''
                        
                        # 전화번호
                        try:
                            phone_el = place.query_selector("span.dry8d")
                            place_data['phone'] = phone_el.inner_text() if phone_el else ''
                        except:
                            place_data['phone'] = ''
                            
                        # 평점
                        try:
                            rating_el = place.query_selector("span.orXYY")
                            place_data['rating'] = rating_el.inner_text() if rating_el else ''
                        except:
                            place_data['rating'] = ''
                        
                        # 리뷰 수
                        try:
                            reviews_el = place.query_selector("span.MVx6e")
                            place_data['reviews'] = reviews_el.inner_text() if reviews_el else ''
                        except:
                            place_data['reviews'] = ''
                        
                        if place_data['name']:
                            results.append(place_data)
                            collected += 1
                            print(f"Collected: {collected}/{max_results} - {place_data['name']}")
                            
                    except Exception as e:
                        print(f"Error parsing place: {e}")
                        continue
                
                # 새로운 결과가 없으면 스크롤
                if collected == last_count:
                    scroll_attempts += 1
                    try:
                        iframe.evaluate("""
                            const container = document.querySelector('div.Ryr1F');
                            if (container) {
                                container.scrollTop = container.scrollHeight;
                            }
                        """)
                        time.sleep(1.5)
                    except:
                        break
                else:
                    scroll_attempts = 0
                    
                last_count = collected
                
        except Exception as e:
            print(f"Error during crawling: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            page.close()
            
        return results
    
    def close(self):
        """브라우저 종료"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

# 전역 crawler 인스턴스
crawler = None

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

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
        
        # 검색 실행
        results = crawler.search_places(keyword, max_results)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
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
            writer = csv.DictWriter(f, fieldnames=['name', 'category', 'address', 'phone', 'rating', 'reviews'])
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
    
    print("=" * 60)
    print("네이버 지도 크롤링 앱이 시작됩니다!")
    print("=" * 60)
    print("")
    print("사용 방법:")
    print("1. 웹 브라우저에서 아래 주소로 접속하세요")
    print("2. 검색어를 입력하고 '검색' 버튼을 클릭하세요")
    print("3. 결과를 확인하고 'CSV로 저장' 버튼으로 저장하세요")
    print("")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
