import streamlit as st
import pandas as pd
import sys
import os
from io import BytesIO
from datetime import datetime
import asyncio
import subprocess
from auth import AuthSystem

# Playwright 브라우저 자동 설치 (최초 1회)
@st.cache_resource
def install_playwright_browsers():
    """Playwright Chromium 브라우저 설치"""
    try:
        # 1. playwright install chromium
        print("🔧 Step 1: Installing Playwright Chromium...")
        result1 = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        print("✅ Chromium installed")
        print(result1.stdout)
        
        # 2. playwright install-deps (시스템 의존성)
        print("🔧 Step 2: Installing system dependencies...")
        result2 = subprocess.run(
            [sys.executable, "-m", "playwright", "install-deps", "chromium"],
            capture_output=True,
            text=True,
            timeout=300
        )
        print("✅ Dependencies installed")
        print(result2.stdout)
        
        # 3. 설치 확인
        print("🔧 Step 3: Verifying installation...")
        import os
        home_dir = os.path.expanduser("~")
        playwright_dir = os.path.join(home_dir, ".cache", "ms-playwright")
        if os.path.exists(playwright_dir):
            print(f"✅ Playwright directory exists: {playwright_dir}")
            for item in os.listdir(playwright_dir):
                print(f"  - {item}")
        else:
            print(f"❌ Playwright directory not found: {playwright_dir}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Installation timeout (5분 초과)")
        return False
    except Exception as e:
        print(f"❌ Playwright 설치 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

# 브라우저 설치 실행
with st.spinner("🔧 Playwright 브라우저 설치 중... (최초 1회, 약 2분 소요)"):
    install_status = install_playwright_browsers()

if not install_status:
    st.error("❌ Playwright 브라우저 설치 실패")
    st.info("💡 사이드바에서 '데모 모드'를 활성화하여 앱 기능을 테스트하세요.")
else:
    st.success("✅ Playwright 설치 완료!")

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

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# 인증 시스템
auth = AuthSystem()

# 로그인하지 않은 경우
if not st.session_state.logged_in:
    st.markdown('<div class="main-header">🔍 네이버 플레이스 크롤러</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">로그인이 필요합니다</div>', unsafe_allow_html=True)
    
    # 탭으로 로그인/회원가입 구분
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    
    with tab1:
        st.markdown("### 로그인")
        
        with st.form("login_form"):
            login_email = st.text_input("이메일", placeholder="your@email.com")
            login_password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_button = st.form_submit_button("🔓 로그인", use_container_width=True)
            
            if login_button:
                if not login_email or not login_password:
                    st.error("이메일과 비밀번호를 모두 입력해주세요.")
                else:
                    with st.spinner("로그인 중..."):
                        success, message, user_info = auth.login(login_email, login_password)
                        
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_info = user_info
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            
                            # 디버그 정보 (임시)
                            import hashlib
                            with st.expander("🔧 디버그 정보 (관리자용)"):
                                st.code(f"입력한 비밀번호 해시:\n{hashlib.sha256(login_password.encode()).hexdigest()}")
                                st.caption("Google Sheets의 H열과 비교해보세요.")
    
    with tab2:
        st.markdown("### 회원가입")
        st.info("📋 가입 후 관리자 승인 시 이용 가능합니다.")
        
        with st.form("signup_form"):
            signup_name = st.text_input("이름 *", placeholder="홍길동")
            signup_phone = st.text_input("전화번호 *", placeholder="010-1234-5678")
            signup_email = st.text_input("이메일 *", placeholder="your@email.com")
            signup_company = st.text_input("소속 *", placeholder="회사명 또는 단체명")
            signup_password = st.text_input("비밀번호 *", type="password", placeholder="4자리 이상")
            signup_password_confirm = st.text_input("비밀번호 확인 *", type="password", placeholder="비밀번호 재입력")
            
            st.caption("* 필수 입력 항목")
            
            signup_button = st.form_submit_button("📝 회원가입", use_container_width=True)
            
            if signup_button:
                if not all([signup_name, signup_phone, signup_email, signup_company, signup_password, signup_password_confirm]):
                    st.error("모든 필수 항목을 입력해주세요.")
                elif signup_password != signup_password_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    with st.spinner("회원가입 처리 중..."):
                        success, message = auth.signup(
                            signup_name,
                            signup_phone,
                            signup_email,
                            signup_company,
                            signup_password
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("💡 승인 완료 후 이메일로 알림을 받으실 수 있습니다.")
                        else:
                            st.error(f"❌ {message}")
    
    st.stop()  # 로그인하지 않으면 여기서 중단

# 로그인 상태 - 메인 앱 표시
st.markdown('<div class="main-header">🔍 네이버 플레이스 크롤러</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">메인/타지역 업체 자동 판별 시스템</div>', unsafe_allow_html=True)

# 사용자 정보 표시
with st.sidebar:
    st.success(f"👤 {st.session_state.user_info['name']}님 환영합니다!")
    st.caption(f"📧 {st.session_state.user_info['email']}")
    st.caption(f"🏢 {st.session_state.user_info['company']}")
    
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()
    
    st.markdown("---")
    
    # 관리자 페이지 링크
    st.markdown("### 👨‍💼 관리")
    if st.button("🔐 관리자 페이지", use_container_width=True):
        st.switch_page("pages/admin.py")
    
    st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    st.markdown("### 📋 판정 기준")
    st.info("""
    **타지역 업체:**
    1. 상호명 = "흥신소" (3글자)
    2. 전화번호 = "070" (인터넷 전화)
    
    **메인 업체:**
    - 0507 (네이버 대표번호) ✅
    - 031, 02, 1688 등 일반 전화번호 ✅
    """)
    
    st.markdown("### 🎯 크롤링 옵션")
    max_results = st.slider("최대 결과 수", 5, 100, 20, 5)
    
    st.markdown("### 🧪 테스트 모드")
    demo_mode = st.checkbox("데모 모드 (Playwright 문제 시)", value=False)
    if demo_mode:
        st.warning("⚠️ 데모 데이터를 사용합니다 (실제 크롤링 아님)")
    
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
    
    # 진행 중 표시
    st.markdown("---")
    progress_placeholder = st.empty()
    progress_placeholder.markdown("### 🔄 크롤링 진행 중...")
    
    # 프로그레스 바
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.markdown("### ⏳ 준비 중...")
        
        # Import the crawler
        from naver_crawler_streamlit import NaverPlaceCrawler
        
        all_results = []
        
        # 각 키워드별로 크롤링
        for idx, keyword in enumerate(keywords):
            status_text.markdown(f"### 🔍 검색 중: **{keyword}** ({idx+1}/{len(keywords)})")
            progress_bar.progress((idx) / len(keywords))
            
            # 크롤러 실행
            try:
                # 데모 모드 체크
                if demo_mode:
                    # 데모 데이터 생성
                    results = [
                        {
                            'search_keyword': keyword,
                            'name': f'{keyword} 업체{i+1}',
                            'category': '테스트카테고리',
                            'address': f'경기도 안산시 테스트동 {10+i}-{20+i}',
                            'phone': '070-8086-2784' if i % 3 == 0 else f'031-{800+i}-{2000+i}',
                            'rating': '4.5',
                            'reviews': f'{i*10}',
                            'is_other_region': i % 3 == 0,
                            'place_type': '타지역업체' if i % 3 == 0 else '주업체'
                        }
                        for i in range(min(10, max_results))
                    ]
                    st.info(f"🧪 '{keyword}': {len(results)}개 데모 데이터 생성 (실제 크롤링 아님)")
                else:
                    # 실제 크롤링 with 로그 캡처
                    import io
                    import sys
                    
                    # 표준 출력 캡처
                    old_stdout = sys.stdout
                    sys.stdout = log_buffer = io.StringIO()
                    
                    try:
                        crawler = NaverPlaceCrawler()
                        results = asyncio.run(crawler.crawl(keyword, max_results=max_results))
                    finally:
                        # 로그 복원
                        sys.stdout = old_stdout
                        log_output = log_buffer.getvalue()
                    
                    # 로그 표시
                    if log_output:
                        with st.expander(f"🔍 '{keyword}' 크롤링 로그 (클릭하여 보기)"):
                            st.code(log_output, language="text")
                    
                    if not results:
                        st.warning(f"⚠️ '{keyword}': 결과 없음")
                        st.info("💡 위의 로그를 확인하거나, 사이드바에서 '데모 모드'를 활성화해보세요.")
                    else:
                        st.success(f"✅ '{keyword}': {len(results)}개 업체 추출")
                
                if results:
                    # 각 결과에 검색 키워드 추가
                    for result in results:
                        result['search_keyword'] = keyword
                    all_results.extend(results)
                    
            except Exception as e:
                st.error(f"❌ '{keyword}' 크롤링 실패")
                with st.expander("🔍 오류 상세 정보"):
                    st.code(str(e))
                    import traceback
                    st.code(traceback.format_exc())
                st.info("💡 사이드바에서 '데모 모드'를 활성화하면 앱 기능을 테스트할 수 있습니다.")
        
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
            no_place_count = len(df[df['place_type'] == '플레이스 없음'])
            
            # 전체 통계 표시
            st.markdown("---")
            st.markdown("### 📊 크롤링 결과 통계")
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("총 키워드 수", f"{len(keywords)}개")
            with col_stat2:
                st.metric("메인 업체", f"{main_count}개")
            with col_stat3:
                st.metric("타지역 업체", f"{other_count}개")
            with col_stat4:
                st.metric("플레이스 없음", f"{no_place_count}개")
            
            # 키워드별 통계 표시
            if len(keywords) > 1:
                st.markdown("---")
                st.markdown("### 🔑 키워드별 통계")
                
                keyword_stats = []
                for kw in keywords:
                    kw_df = df[df['search_keyword'] == kw]
                    if len(kw_df) > 0:
                        kw_main = len(kw_df[kw_df['place_type'] == '주업체'])
                        kw_other = len(kw_df[kw_df['place_type'] == '타지역업체'])
                        kw_no_place = len(kw_df[kw_df['place_type'] == '플레이스 없음'])
                        keyword_stats.append({
                            '검색 키워드': kw,
                            '총 개수': len(kw_df),
                            '메인': kw_main,
                            '타지역': kw_other,
                            '플레이스 없음': kw_no_place
                        })
                
                if keyword_stats:
                    kw_stats_df = pd.DataFrame(keyword_stats)
                    st.dataframe(kw_stats_df, use_container_width=True, hide_index=True)
            
            # 필터링
            st.markdown("---")
            st.markdown("### 🔍 결과 필터링")
            
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                filter_type = st.selectbox(
                    "업체 유형",
                    ["전체", "메인 업체만", "타지역 업체만"]
                )
            
            with filter_col2:
                # 키워드 필터 (다중 키워드 검색인 경우만)
                if len(keywords) > 1:
                    filter_keyword = st.selectbox(
                        "검색 키워드",
                        ["전체"] + keywords
                    )
                else:
                    filter_keyword = "전체"
            
            with filter_col3:
                search_name = st.text_input("업체명 검색", placeholder="검색할 업체명")
            
            # 필터 적용
            filtered_df = df.copy()
            
            if filter_type == "메인 업체만":
                filtered_df = filtered_df[filtered_df['place_type'] == '주업체']
            elif filter_type == "타지역 업체만":
                filtered_df = filtered_df[filtered_df['place_type'] == '타지역업체']
            
            if len(keywords) > 1 and filter_keyword != "전체":
                filtered_df = filtered_df[filtered_df['search_keyword'] == filter_keyword]
            
            if search_name:
                filtered_df = filtered_df[filtered_df['name'].str.contains(search_name, na=False)]
            
            # 결과 테이블
            st.markdown("---")
            st.markdown(f"### 📋 검색 결과 ({len(filtered_df)}개)")
            
            # place_type 컬럼을 더 명확하게 표시
            display_df = filtered_df.copy()
            display_df['place_type'] = display_df['place_type'].apply(
                lambda x: '🟢 메인' if x == '주업체' else ('⚪ 플레이스 없음' if x == '플레이스 없음' else '🔴 타지역')
            )
            
            # 컬럼 순서 재정렬 (검색 키워드를 맨 앞으로)
            if 'search_keyword' in display_df.columns:
                columns_order = ['search_keyword', 'name', 'category', 'address', 'phone', 'rating', 'reviews', 'place_type']
                # 존재하는 컬럼만 선택
                columns_order = [col for col in columns_order if col in display_df.columns]
                display_df = display_df[columns_order]
                
                # 컬럼명 한글화
                display_df = display_df.rename(columns={
                    'search_keyword': '🔍 검색 키워드',
                    'name': '상호명',
                    'category': '카테고리',
                    'address': '주소',
                    'phone': '전화번호',
                    'rating': '평점',
                    'reviews': '리뷰수',
                    'place_type': '구분'
                })
            
            # 데이터프레임 스타일링 - 메인/타지역/플레이스없음 구분
            def highlight_place_type(row):
                place_val = str(row.get('구분', row.get('place_type', '')))
                if '플레이스 없음' in place_val:
                    # 플레이스 없음 - 회색 배경
                    return ['background-color: #e9ecef'] * len(row)
                elif '타지역' in place_val:
                    # 타지역 - 주황색 배경
                    return ['background-color: #fff3cd'] * len(row)
                else:
                    # 메인 - 초록색 배경
                    return ['background-color: #d4edda'] * len(row)
            
            styled_df = display_df.style.apply(highlight_place_type, axis=1)
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
