#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 맵 구조 분석 스크립트
"""

from playwright.sync_api import sync_playwright
import time
from urllib.parse import quote

def analyze_naver_map_structure(keyword="선불폰"):
    """네이버 맵 HTML 구조 분석"""
    
    with sync_playwright() as p:
        print("="*70)
        print("🔍 네이버 맵 HTML 구조 분석")
        print("="*70)
        
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        url = f"https://map.naver.com/p/search/{quote(keyword)}"
        print(f"\n📍 URL: {url}")
        print(f"🔍 검색어: {keyword}\n")
        
        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        time.sleep(5)
        
        # 1. 모든 iframe 찾기
        print("="*70)
        print("1️⃣ iframe 목록:")
        print("="*70)
        
        frames = page.frames
        print(f"총 {len(frames)}개 프레임 발견:\n")
        
        for i, frame in enumerate(frames):
            name = frame.name if frame.name else "(이름없음)"
            url_frame = frame.url
            print(f"  [{i}] Name: {name}")
            print(f"      URL: {url_frame[:80]}...")
            print()
        
        # 2. searchIframe 찾기
        print("="*70)
        print("2️⃣ searchIframe 확인:")
        print("="*70)
        
        search_iframe = page.frame(name="searchIframe")
        if search_iframe:
            print("✅ searchIframe 찾음!")
            print(f"   URL: {search_iframe.url[:100]}...")
        else:
            print("❌ searchIframe을 찾을 수 없습니다")
            print("   → 다른 이름의 iframe을 사용 중일 수 있습니다\n")
            
            # 대체 iframe 찾기
            for frame in frames:
                if "search" in frame.url.lower() or "list" in frame.url.lower():
                    print(f"   💡 후보 iframe 발견:")
                    print(f"      Name: {frame.name if frame.name else '(없음)'}")
                    print(f"      URL: {frame.url}")
        
        # 3. 메인 페이지 HTML 샘플
        print("\n" + "="*70)
        print("3️⃣ 메인 페이지 HTML 샘플 (처음 1500자):")
        print("="*70)
        
        content = page.content()
        print(content[:1500])
        print("\n...")
        
        # 4. searchIframe이 있다면 내부 HTML 샘플
        if search_iframe:
            print("\n" + "="*70)
            print("4️⃣ searchIframe 내부 HTML 샘플 (처음 2000자):")
            print("="*70)
            
            iframe_content = search_iframe.content()
            print(iframe_content[:2000])
            print("\n...")
            
            # 5. 리스트 아이템 찾기 시도
            print("\n" + "="*70)
            print("5️⃣ 리스트 아이템 찾기 시도:")
            print("="*70)
            
            selectors_to_try = [
                'li[role="listitem"]',
                'li.UEzoS',
                'li.place_item',
                'ul._2py9K li',
                'div.CHC5F',
                'ul li',
                'div[class*="item"]',
                '[data-naver-map]',
                '[class*="place"]',
                '[class*="list"]'
            ]
            
            for sel in selectors_to_try:
                items = search_iframe.query_selector_all(sel)
                if items:
                    print(f"✅ '{sel}' → {len(items)}개 발견!")
                    
                    # 첫 번째 아이템 HTML 샘플
                    if items:
                        print(f"\n   첫 번째 아이템 HTML (500자):")
                        first_html = items[0].inner_html()
                        print(f"   {first_html[:500]}...")
                        print()
                else:
                    print(f"❌ '{sel}' → 없음")
        
        browser.close()
        
        print("\n" + "="*70)
        print("✅ 분석 완료!")
        print("="*70)

if __name__ == "__main__":
    analyze_naver_map_structure("선불폰")
