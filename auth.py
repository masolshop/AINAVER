"""
회원가입 및 인증 시스템 - Google Sheets 연동
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
import re
import hashlib
import json
import os


class AuthSystem:
    """Google Sheets 기반 인증 시스템"""
    
    def __init__(self):
        self.sheet_id = "18-bLF8vj-z0usDSrVEyFXZlKfcU5FbW3e7Hzip0MXjI"
        self.credentials_file = "credentials.json"
        self.gc = None
        self.sheet = None
        
    def connect(self):
        """Google Sheets 연결"""
        try:
            # 환경 변수에서 credentials 가져오기 (Docker 환경)
            if os.getenv('GOOGLE_CREDENTIALS'):
                credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
                creds = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
            elif os.path.exists(self.credentials_file):
                # 로컬 파일에서 읽기
                creds = Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
            else:
                st.error("❌ Google Sheets 인증 파일이 없습니다.")
                return False
            
            self.gc = gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(self.sheet_id).worksheet('users')
            return True
            
        except Exception as e:
            st.error(f"❌ Google Sheets 연결 실패: {str(e)}")
            return False
    
    def validate_email(self, email):
        """이메일 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone):
        """전화번호 형식 검증"""
        # 숫자만 추출
        digits = re.sub(r'\D', '', phone)
        # 10-11자리 숫자
        return len(digits) >= 10 and len(digits) <= 11
    
    def hash_password(self, password):
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def signup(self, name, phone, email, company, password):
        """회원가입"""
        try:
            if not self.connect():
                return False, "Google Sheets 연결 실패"
            
            # 유효성 검사
            if not name or len(name.strip()) < 2:
                return False, "이름은 2글자 이상 입력해주세요."
            
            if not self.validate_phone(phone):
                return False, "올바른 전화번호를 입력해주세요. (예: 010-1234-5678)"
            
            if not self.validate_email(email):
                return False, "올바른 이메일 주소를 입력해주세요."
            
            if not company or len(company.strip()) < 2:
                return False, "소속을 2글자 이상 입력해주세요."
            
            if not password or len(password) < 4:
                return False, "비밀번호는 4자리 이상 입력해주세요."
            
            # 중복 체크
            all_records = self.sheet.get_all_records()
            for record in all_records:
                if record.get('이메일') == email:
                    return False, "이미 가입된 이메일입니다."
            
            # 새 ID 생성
            new_id = len(all_records) + 1
            
            # 비밀번호 해시화
            hashed_password = self.hash_password(password)
            
            # 현재 시간
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 데이터 추가
            self.sheet.append_row([
                new_id,
                name.strip(),
                phone.strip(),
                email.strip(),
                company.strip(),
                "대기중",
                now,
                hashed_password
            ])
            
            return True, "회원가입이 완료되었습니다. 관리자 승인 후 이용 가능합니다."
            
        except Exception as e:
            return False, f"회원가입 실패: {str(e)}"
    
    def login(self, email, password):
        """로그인"""
        try:
            if not self.connect():
                return False, "Google Sheets 연결 실패", None
            
            # 이메일로 사용자 찾기
            all_records = self.sheet.get_all_records()
            
            for idx, record in enumerate(all_records):
                if record.get('이메일') == email:
                    # 비밀번호 확인
                    hashed_password = self.hash_password(password)
                    stored_password = record.get('비밀번호', '')
                    
                    if hashed_password != stored_password:
                        return False, "비밀번호가 일치하지 않습니다.", None
                    
                    # 승인 상태 확인
                    status = record.get('상태', '대기중')
                    if status == "대기중":
                        return False, "관리자 승인 대기 중입니다. 승인 후 이용 가능합니다.", None
                    elif status == "거부됨":
                        return False, "가입이 거부되었습니다. 관리자에게 문의하세요.", None
                    elif status == "승인됨":
                        # 로그인 성공
                        user_info = {
                            'id': record.get('ID'),
                            'name': record.get('이름'),
                            'email': record.get('이메일'),
                            'company': record.get('소속')
                        }
                        return True, "로그인 성공", user_info
            
            return False, "등록되지 않은 이메일입니다.", None
            
        except Exception as e:
            return False, f"로그인 실패: {str(e)}", None
    
    def get_pending_users(self):
        """승인 대기 중인 사용자 목록"""
        try:
            if not self.connect():
                return []
            
            all_records = self.sheet.get_all_records()
            pending_users = []
            
            for record in all_records:
                if record.get('상태') == '대기중':
                    pending_users.append({
                        'ID': record.get('ID'),
                        '이름': record.get('이름'),
                        '전화번호': record.get('전화번호'),
                        '이메일': record.get('이메일'),
                        '소속': record.get('소속'),
                        '가입일시': record.get('가입일시')
                    })
            
            return pending_users
            
        except Exception as e:
            st.error(f"❌ 사용자 목록 조회 실패: {str(e)}")
            return []
    
    def approve_user(self, email):
        """사용자 승인"""
        try:
            if not self.connect():
                return False
            
            all_records = self.sheet.get_all_records()
            
            for idx, record in enumerate(all_records):
                if record.get('이메일') == email:
                    # 상태를 "승인됨"으로 변경 (헤더 포함해서 +2)
                    self.sheet.update_cell(idx + 2, 6, "승인됨")
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ 승인 실패: {str(e)}")
            return False
    
    def reject_user(self, email):
        """사용자 거부"""
        try:
            if not self.connect():
                return False
            
            all_records = self.sheet.get_all_records()
            
            for idx, record in enumerate(all_records):
                if record.get('이메일') == email:
                    # 상태를 "거부됨"으로 변경
                    self.sheet.update_cell(idx + 2, 6, "거부됨")
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ 거부 실패: {str(e)}")
            return False
