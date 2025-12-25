# 🚀 네이버 플레이스 크롤러 - Streamlit Cloud 배포 완료!

## ✅ 배포 준비 완료

모든 파일이 GitHub에 업로드되었습니다. 이제 Streamlit Cloud에서 배포만 하면 됩니다!

---

## 📋 1단계: Streamlit Cloud 가입

### 방법 1: 직접 가입
1. https://share.streamlit.io 방문
2. **"Sign up"** 클릭
3. **"Continue with GitHub"** 선택
4. GitHub 계정 연동 승인

### 방법 2: 빠른 링크
- 직접 배포 URL: https://share.streamlit.io/deploy

---

## 🎯 2단계: 앱 배포하기

### 필수 정보 입력:

```
Repository: masolshop/AINAVER
Branch: main
Main file path: app.py
```

### 상세 단계:

1. **"New app"** 버튼 클릭
2. **Repository** 입력창에 `masolshop/AINAVER` 입력
3. **Branch** 선택: `main`
4. **Main file path** 입력: `app.py`
5. **App URL** (선택사항):
   - 기본값 사용 또는
   - 원하는 이름으로 변경 (예: `naver-crawler`)

6. **"Deploy!"** 버튼 클릭

---

## ⏳ 3단계: 배포 완료 대기

### 예상 소요 시간: 3-5분

배포 과정에서 다음 작업이 자동으로 진행됩니다:

✅ **1분**: GitHub 저장소 클론  
✅ **2분**: Python 패키지 설치 (streamlit, pandas, playwright 등)  
✅ **2분**: Playwright Chromium 브라우저 설치  
✅ **완료**: 앱 시작 및 URL 생성

### 로그 확인:
- 배포 중 로그를 실시간으로 확인할 수 있습니다
- 오류 발생 시 로그에서 원인 파악 가능

---

## 🌐 4단계: 배포 완료 후 URL 확인

배포가 완료되면 다음과 같은 형식의 URL을 받게 됩니다:

```
https://[your-app-name].streamlit.app
```

**예시:**
```
https://naver-place-crawler-abc123.streamlit.app
```

---

## 🧪 5단계: 앱 테스트

### 기능 테스트 체크리스트:

- [ ] 앱이 정상적으로 로드되는가?
- [ ] 검색 키워드 입력이 작동하는가?
- [ ] 크롤링 버튼 클릭 시 정상 작동하는가?
- [ ] 결과가 테이블로 표시되는가?
- [ ] Excel 다운로드가 작동하는가?
- [ ] CSV 다운로드가 작동하는가?
- [ ] 타지역 필터링이 정확한가?

### 추천 테스트 키워드:
```
안산선불폰
인천흥신소
강남역맛집
```

---

## 📤 6단계: URL 공유

### 공유 메시지 템플릿:

```
🔍 네이버 플레이스 크롤러

📍 URL: https://your-app.streamlit.app

✨ 기능:
• 네이버 플레이스 자동 크롤링
• 메인/타지역 업체 자동 판별
• Excel/CSV 다운로드
• 다중 키워드 검색

📊 판정 기준:
• 타지역: 흥신소(3글자), 070 전화번호
• 메인: 기타 모든 전화번호 (031, 02, 0507, 1688 등)

💡 사용법:
1. 키워드 입력
2. 크롤링 시작 버튼 클릭
3. 결과 확인 및 다운로드
```

---

## 🔧 문제 해결

### 배포 실패 시:

#### 1. Playwright 설치 오류
```
해결: packages.txt와 setup.sh가 자동으로 처리함
대기: 5분 정도 더 기다려보기
```

#### 2. 메모리 부족 오류
```
해결: app.py에서 max_results 값 낮추기
수정: 기본값 20 → 10으로 변경
```

#### 3. 크롤링 속도 느림
```
원인: Streamlit Cloud는 1 CPU / 1GB RAM 제한
해결: 한 번에 5-10개 키워드만 검색
```

#### 4. 앱이 슬립 모드
```
원인: 7일간 사용 없으면 자동 슬립
해결: URL 방문 시 자동으로 깨어남 (30초 소요)
```

---

## ⚙️ 고급 설정

### 앱 업데이트 방법:

코드 수정 후:
```bash
git add .
git commit -m "업데이트 내용"
git push origin main
```

→ Streamlit Cloud가 자동으로 새 버전 배포 (약 3분)

### 환경 변수 설정:

1. Streamlit Cloud 대시보드 접속
2. 앱 선택 → **Settings** → **Secrets**
3. TOML 형식으로 추가

예시:
```toml
# 필요한 경우 API 키 등 추가
NAVER_API_KEY = "your-key-here"
```

---

## 📊 사용 제한 (무료 플랜)

| 항목 | 제한 |
|-----|-----|
| 앱 개수 | 무제한 |
| 메모리 | 1GB |
| CPU | 1 코어 |
| 동시 접속 | 제한 없음 |
| 휴면 | 7일 무사용 시 슬립 |
| 비용 | 100% 무료 |

---

## 🎉 배포 성공 체크리스트

- [ ] Streamlit Cloud 계정 생성
- [ ] 앱 배포 완료
- [ ] 공개 URL 생성 확인
- [ ] 기능 테스트 완료
- [ ] URL을 필요한 사람들에게 공유
- [ ] 피드백 수집 채널 준비

---

## 📞 지원

**문제 발생 시:**

1. GitHub Issues: https://github.com/masolshop/AINAVER/issues
2. 로그 확인: Streamlit Cloud 대시보드 → Logs
3. 재배포: Streamlit Cloud 대시보드 → Reboot app

---

## 🔗 유용한 링크

- **Streamlit Cloud**: https://share.streamlit.io
- **GitHub 저장소**: https://github.com/masolshop/AINAVER
- **Streamlit 문서**: https://docs.streamlit.io

---

**🎯 배포 완료 후 다음 단계:**

1. URL 즐겨찾기 추가
2. 팀원들에게 URL 공유
3. 사용 피드백 수집
4. 기능 개선 요청 정리
5. 업데이트 배포

**축하합니다! 이제 누구나 웹에서 크롤러를 사용할 수 있습니다!** 🎉
