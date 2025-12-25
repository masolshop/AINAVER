import streamlit as st
import pandas as pd
import sys
import os
from io import BytesIO
from datetime import datetime
import asyncio
import subprocess

# Playwright 브라우저 자동 설치 (최초 1회)
@st.cache_resource
def install_playwright_browsers():
    """Playwright Chromium 브라우저 설치"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Playwright 브라우저 설치 완료")
        print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ Playwright 설치 실패: {e}")
        return False

# 브라우저 설치 실행
install_status = install_playwright_browsers()
if not install_status:
    st.warning("⚠️ Playwright 브라우저 설치 중 문제가 발생했을 수 있습니다.")

# 페이지 설정
st.set_page_config(
    page_title="네이버 플레이스 크롤러",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #03C75A;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #03C75A;
        color: white;
        font-size: 1.2rem;
        padding: 0.8rem;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #02A84A;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown('<div class="main-header">🔍 네이버 플레이스 크롤러</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">메인/타지역 업체 자동 판별 시스템</div>', unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    st.markdown("### 📋 판정 기준")
    st.info("""
    **타지역 업체:**
    1. 상호명 = "흥신소" (3글자)
    2. 전화번호 = "070" (인터넷 전화)
    
    **메인 업체:**
    - 그 외 모든 전화번호
    - 0507, 031, 02, 1688 등
    """)
    
    st.markdown("### 🎯 크롤링 옵션")
    max_results = st.slider("최대 결과 수", 5, 100, 20, 5)
    
    st.markdown("### 📊 통계")
    if 'stats' in st.session_state:
        stats = st.session_state.stats
        st.metric("총 검색 횟수", stats.get('total_searches', 0))
        st.metric("총 추출 업체", stats.get('total_results', 0))

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🔎 검색 키워드 입력")
    
    # 입력 방식 선택
    input_mode = st.radio(
        "입력 방식 선택:",
        ["단일 키워드", "다중 키워드 (줄바꿈)", "다중 키워드 (쉼표)"],
        horizontal=True
    )
    
    if input_mode == "단일 키워드":
        keyword = st.text_input(
            "검색할 키워드를 입력하세요",
            placeholder="예: 안산선불폰, 인천흥신소, 강남맛집"
        )
        keywords = [keyword] if keyword else []
        
    elif input_mode == "다중 키워드 (줄바꿈)":
        keyword_text = st.text_area(
            "한 줄에 하나씩 키워드를 입력하세요",
            placeholder="안산선불폰\n인천흥신소\n강남맛집",
            height=150
        )
        keywords = [k.strip() for k in keyword_text.split('\n') if k.strip()]
        
    else:  # 쉼표 구분
        keyword_text = st.text_input(
            "쉼표로 구분하여 키워드를 입력하세요",
            placeholder="안산선불폰, 인천흥신소, 강남맛집"
        )
        keywords = [k.strip() for k in keyword_text.split(',') if k.strip()]
    
    if keywords:
        st.success(f"✅ {len(keywords)}개의 키워드 입력됨: {', '.join(keywords[:5])}" + 
                  (f" 외 {len(keywords)-5}개" if len(keywords) > 5 else ""))

with col2:
    st.markdown("### 💡 사용 팁")
    st.markdown("""
    <div class="info-box">
    <b>🎯 검색 키워드 예시:</b><br>
    • 안산선불폰<br>
    • 인천흥신소<br>
    • 강남역맛집<br>
    • 서울포장이사<br>
    <br>
    <b>⚡ 빠른 사용법:</b><br>
    1. 키워드 입력<br>
    2. 크롤링 시작 버튼 클릭<br>
    3. 결과 확인 및 다운로드<br>
    </div>
    """, unsafe_allow_html=True)

# 크롤링 버튼
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    start_button = st.button("🚀 크롤링 시작", use_container_width=True)

# 크롤링 실행
if start_button and keywords:
    
    # 프로그레스 바
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.markdown("### ⏳ 크롤링 중...")
        
        # Import the crawler
        from naver_crawler_streamlit import NaverPlaceCrawler
        
        all_results = []
        
        # 각 키워드별로 크롤링
        for idx, keyword in enumerate(keywords):
            status_text.markdown(f"### 🔍 검색 중: **{keyword}** ({idx+1}/{len(keywords)})")
            progress_bar.progress((idx) / len(keywords))
            
            # 크롤러 실행
            try:
                crawler = NaverPlaceCrawler()
                results = asyncio.run(crawler.crawl(keyword, max_results=max_results))
                
                if results:
                    all_results.extend(results)
                    st.info(f"✅ '{keyword}': {len(results)}개 업체 추출")
                else:
                    st.warning(f"⚠️ '{keyword}': 결과 없음")
            except Exception as e:
                st.error(f"❌ '{keyword}' 크롤링 실패: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        progress_bar.progress(1.0)
        
        # 결과 표시
        if all_results:
            status_text.markdown("### ✅ 크롤링 완료!")
            
            # DataFrame 생성
            df = pd.DataFrame(all_results)
            
            # 통계
            total = len(df)
            main_count = len(df[df['place_type'] == '주업체'])
            other_count = len(df[df['place_type'] == '타지역업체'])
            
            # 통계 표시
            st.markdown("---")
            st.markdown("### 📊 크롤링 결과 통계")
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("총 업체 수", f"{total}개")
            with col_stat2:
                st.metric("메인 업체", f"{main_count}개", f"{main_count/total*100:.1f}%")
            with col_stat3:
                st.metric("타지역 업체", f"{other_count}개", f"{other_count/total*100:.1f}%")
            
            # 필터링
            st.markdown("---")
            st.markdown("### 🔍 결과 필터링")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                filter_type = st.selectbox(
                    "업체 유형",
                    ["전체", "메인 업체만", "타지역 업체만"]
                )
            
            with filter_col2:
                search_name = st.text_input("업체명 검색", placeholder="검색할 업체명")
            
            # 필터 적용
            filtered_df = df.copy()
            
            if filter_type == "메인 업체만":
                filtered_df = filtered_df[filtered_df['place_type'] == '주업체']
            elif filter_type == "타지역 업체만":
                filtered_df = filtered_df[filtered_df['place_type'] == '타지역업체']
            
            if search_name:
                filtered_df = filtered_df[filtered_df['name'].str.contains(search_name, na=False)]
            
            # 결과 테이블
            st.markdown("---")
            st.markdown(f"### 📋 검색 결과 ({len(filtered_df)}개)")
            
            # 데이터프레임 스타일링
            def highlight_other_region(row):
                if row['place_type'] == '타지역업체':
                    return ['background-color: #fff3cd'] * len(row)
                else:
                    return ['background-color: #d4edda'] * len(row)
            
            styled_df = filtered_df.style.apply(highlight_other_region, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # 다운로드 버튼
            st.markdown("---")
            st.markdown("### 💾 결과 다운로드")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            # Excel 다운로드
            with col_dl1:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    filtered_df.to_excel(writer, index=False, sheet_name='크롤링결과')
                output.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"네이버플레이스_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Excel 다운로드",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # CSV 다운로드
            with col_dl2:
                csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_csv = f"네이버플레이스_{timestamp}.csv"
                
                st.download_button(
                    label="📥 CSV 다운로드",
                    data=csv,
                    file_name=filename_csv,
                    mime="text/csv",
                    use_container_width=True
                )
            
            # 타지역만 다운로드
            with col_dl3:
                other_df = df[df['place_type'] == '타지역업체']
                if len(other_df) > 0:
                    output_other = BytesIO()
                    with pd.ExcelWriter(output_other, engine='openpyxl') as writer:
                        other_df.to_excel(writer, index=False, sheet_name='타지역업체')
                    output_other.seek(0)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename_other = f"타지역업체_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📥 타지역만 다운로드",
                        data=output_other,
                        file_name=filename_other,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            # 세션 통계 업데이트
            if 'stats' not in st.session_state:
                st.session_state.stats = {'total_searches': 0, 'total_results': 0}
            
            st.session_state.stats['total_searches'] += len(keywords)
            st.session_state.stats['total_results'] += total
            
        else:
            st.error("❌ 검색 결과가 없습니다. 다른 키워드로 시도해보세요.")
            
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.exception(e)
    
    finally:
        status_text.empty()
        progress_bar.empty()

elif start_button and not keywords:
    st.warning("⚠️ 검색할 키워드를 입력해주세요!")

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <b>네이버 플레이스 크롤러 v4.9.9</b><br>
    GitHub: <a href="https://github.com/masolshop/AINAVER" target="_blank">masolshop/AINAVER</a><br>
    © 2024 All Rights Reserved
</div>
""", unsafe_allow_html=True)
