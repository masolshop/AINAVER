"""
관리자 페이지 - 사용자 승인/거부
"""

import streamlit as st
import pandas as pd
from auth import AuthSystem

# 페이지 설정
st.set_page_config(
    page_title="관리자 페이지",
    page_icon="👨‍💼",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #03C75A;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 간단한 관리자 인증
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.markdown('<div class="main-header">👨‍💼 관리자 로그인</div>', unsafe_allow_html=True)
    
    admin_password = st.text_input("관리자 비밀번호", type="password")
    
    # 관리자 비밀번호 (변경 가능)
    ADMIN_PASSWORD = "admin1234"  # TODO: 환경 변수로 변경
    
    if st.button("로그인"):
        if admin_password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("✅ 관리자 로그인 성공")
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    
    st.info("💡 관리자 비밀번호는 환경 변수로 설정하세요.")
    st.stop()

# 관리자 페이지
st.markdown('<div class="main-header">👨‍💼 사용자 관리</div>', unsafe_allow_html=True)

# 로그아웃
if st.button("🚪 로그아웃"):
    st.session_state.admin_logged_in = False
    st.rerun()

st.markdown("---")

# AuthSystem 초기화
auth = AuthSystem()

# 승인 대기 중인 사용자 가져오기
st.markdown("### 📋 승인 대기 중인 사용자")

with st.spinner("사용자 목록 불러오는 중..."):
    pending_users = auth.get_pending_users()

if not pending_users:
    st.info("✅ 승인 대기 중인 사용자가 없습니다.")
else:
    st.success(f"📊 총 {len(pending_users)}명의 사용자가 승인 대기 중입니다.")
    
    # 데이터프레임으로 표시
    df = pd.DataFrame(pending_users)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🔧 사용자 승인/거부")
    
    # 사용자 선택
    if len(pending_users) > 0:
        user_emails = [user['이메일'] for user in pending_users]
        selected_email = st.selectbox(
            "사용자 선택",
            options=user_emails,
            format_func=lambda x: f"{x} ({[u for u in pending_users if u['이메일'] == x][0]['이름']})"
        )
        
        # 선택된 사용자 정보 표시
        selected_user = [u for u in pending_users if u['이메일'] == selected_email][0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 사용자 정보")
            st.write(f"**이름**: {selected_user['이름']}")
            st.write(f"**전화번호**: {selected_user['전화번호']}")
            st.write(f"**이메일**: {selected_user['이메일']}")
            st.write(f"**소속**: {selected_user['소속']}")
            st.write(f"**가입일시**: {selected_user['가입일시']}")
        
        with col2:
            st.markdown("#### 🔧 액션")
            
            col_approve, col_reject = st.columns(2)
            
            with col_approve:
                if st.button("✅ 승인", use_container_width=True, type="primary"):
                    with st.spinner("승인 처리 중..."):
                        if auth.approve_user(selected_email):
                            st.success(f"✅ {selected_user['이름']}님을 승인했습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 승인 실패")
            
            with col_reject:
                if st.button("❌ 거부", use_container_width=True):
                    with st.spinner("거부 처리 중..."):
                        if auth.reject_user(selected_email):
                            st.warning(f"⚠️ {selected_user['이름']}님을 거부했습니다.")
                            st.rerun()
                        else:
                            st.error("❌ 거부 실패")

st.markdown("---")

# Google Sheets 링크
st.markdown("### 📊 Google Sheets 바로가기")
st.markdown(f"[📄 사용자 관리 시트 열기](https://docs.google.com/spreadsheets/d/18-bLF8vj-z0usDSrVEyFXZlKfcU5FbW3e7Hzip0MXjI/edit)")
