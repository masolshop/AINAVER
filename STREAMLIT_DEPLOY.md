# 🚀 Streamlit Cloud 배포 가이드

## 📋 준비물

1. GitHub 계정
2. Streamlit Cloud 계정 (무료)
3. 이 저장소

## 🎯 배포 단계

### 1단계: Streamlit Cloud 계정 만들기

1. https://streamlit.io/cloud 방문
2. "Sign up" 클릭
3. GitHub 계정으로 로그인

### 2단계: 앱 배포하기

1. Streamlit Cloud 대시보드에서 **"New app"** 클릭
2. 다음 정보 입력:
   - **Repository**: `masolshop/AINAVER`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. **"Deploy!"** 버튼 클릭

### 3단계: 배포 완료 대기

- 약 3-5분 소요
- Playwright 브라우저 자동 설치
- 완료되면 공개 URL 생성

## 🌐 URL 형식

배포 완료 후 다음과 같은 URL을 받게 됩니다:

```
https://[app-name]-[random-string].streamlit.app
```

예시:
```
https://naver-place-crawler-abc123.streamlit.app
```

## 🔧 고급 설정

### Playwright 브라우저 설치

Streamlit Cloud에서 자동으로 처리되지만, 문제가 있다면:

1. `packages.txt` 파일 확인:
```
chromium
chromium-driver
```

2. `setup.sh` 실행 (자동):
```bash
playwright install chromium
```

### 환경 변수 설정

필요한 경우 Streamlit Cloud 대시보드에서:
1. 앱 설정 → **"Secrets"** 탭
2. TOML 형식으로 추가

## 📊 사용 제한

**Streamlit Cloud 무료 플랜:**
- ✅ 무제한 공개 앱
- ✅ 1GB 메모리
- ✅ 1 CPU 코어
- ✅ 커뮤니티 지원
- ⚠️ 앱 휴면: 7일간 사용 없으면 자동 슬립 (첫 방문 시 재시작)

## 🎉 배포 후 확인사항

1. ✅ 앱이 정상적으로 로드되는지 확인
2. ✅ 검색 기능 테스트
3. ✅ Excel 다운로드 테스트
4. ✅ 여러 키워드 동시 검색 테스트

## 🔗 URL 공유

배포 완료 후 URL을 다음과 같이 공유:

```
📍 네이버 플레이스 크롤러
🔗 https://your-app.streamlit.app

✨ 기능:
- 네이버 플레이스 자동 크롤링
- 메인/타지역 업체 자동 판별
- Excel/CSV 다운로드
- 다중 키워드 검색
```

## ⚡ 문제 해결

### 앱이 시작되지 않는 경우

1. Streamlit Cloud 로그 확인
2. `requirements_streamlit.txt` 버전 확인
3. Playwright 설치 로그 확인

### 크롤링이 느린 경우

- Streamlit Cloud는 1 CPU/1GB RAM 제한
- 한 번에 많은 키워드 검색 시 느려질 수 있음
- 키워드 수를 5-10개로 제한 권장

### 메모리 부족

- `max_results` 값을 20-30으로 제한
- 한 번에 크롤링할 키워드 수 제한

## 📞 지원

문제가 있으면 GitHub Issues에 등록해주세요:
https://github.com/masolshop/AINAVER/issues

---

**🎯 배포 성공 후 할 일:**

1. URL을 즐겨찾기에 추가
2. 필요한 사람들에게 URL 공유
3. 피드백 수집
4. 기능 개선 제안
