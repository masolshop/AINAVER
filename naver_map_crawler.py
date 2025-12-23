#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 지도 크롤링 앱
간단한 웹 인터페이스로 네이버 지도에서 장소 정보를 검색합니다.
"""

from flask import Flask, render_template, request, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import csv
import json
from datetime import datetime
import os

app = Flask(__name__)

class NaverMapCrawler:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def search_places(self, keyword, max_results=20):
        """네이버 지도에서 장소 검색"""
        if not self.driver:
            self.setup_driver()
            
        results = []
        
        try:
            # 네이버 지도 접속
            url = f"https://map.naver.com/v5/search/{keyword}"
            self.driver.get(url)
            time.sleep(3)
            
            # iframe으로 전환
            try:
                iframe = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
                )
                self.driver.switch_to.frame(iframe)
            except:
                pass
            
            # 검색 결과 대기
            time.sleep(2)
            
            # 스크롤하면서 데이터 수집
            scroll_container = self.driver.find_element(By.CSS_SELECTOR, "div.Ryr1F")
            last_height = 0
            collected = 0
            
            while collected < max_results:
                # 현재 보이는 장소들 가져오기
                place_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.UEzoS.rTjJo")
                
                for place in place_elements[collected:]:
                    if collected >= max_results:
                        break
                        
                    try:
                        place_data = {}
                        
                        # 장소명
                        try:
                            name = place.find_element(By.CSS_SELECTOR, "span.TYaxT").text
                            place_data['name'] = name
                        except:
                            place_data['name'] = ''
                        
                        # 카테고리
                        try:
                            category = place.find_element(By.CSS_SELECTOR, "span.KCMnt").text
                            place_data['category'] = category
                        except:
                            place_data['category'] = ''
                        
                        # 주소
                        try:
                            address = place.find_element(By.CSS_SELECTOR, "span.LDgIH").text
                            place_data['address'] = address
                        except:
                            place_data['address'] = ''
                        
                        # 전화번호
                        try:
                            phone = place.find_element(By.CSS_SELECTOR, "span.dry8d").text
                            place_data['phone'] = phone
                        except:
                            place_data['phone'] = ''
                            
                        # 평점
                        try:
                            rating = place.find_element(By.CSS_SELECTOR, "span.orXYY").text
                            place_data['rating'] = rating
                        except:
                            place_data['rating'] = ''
                        
                        # 리뷰 수
                        try:
                            reviews = place.find_element(By.CSS_SELECTOR, "span.MVx6e").text
                            place_data['reviews'] = reviews
                        except:
                            place_data['reviews'] = ''
                        
                        if place_data['name']:
                            results.append(place_data)
                            collected += 1
                            
                    except Exception as e:
                        continue
                
                # 스크롤
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
                time.sleep(1)
                
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_container)
                if new_height == last_height:
                    break
                last_height = new_height
                
        except Exception as e:
            print(f"Error during crawling: {e}")
            
        return results
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()

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
    
    app.run(host='0.0.0.0', port=5000, debug=False)
