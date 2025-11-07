# 상세페이지 제작 도구 🎨

Google Sheets + OpenAI + HTML-to-Image를 활용한 도서 상세페이지 자동 생성 도구입니다.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-00A67E?style=for-the-badge&logo=openai" />
  <img src="https://img.shields.io/badge/Tkinter-GUI-orange?style=for-the-badge" />
</p>

## ✨ 주요 기능

- 🔄 **Google Sheets 자동 감시**: 신간안내서가 추가되면 자동으로 감지
- 🤖 **AI 콘텐츠 생성**: OpenAI GPT-4o-mini로 마케팅 최적화된 콘텐츠 추출
- 🎨 **모던 디자인**: Toss 스타일의 그라디언트 HTML 템플릿
- 📸 **이미지 자동 렌더링**: HTML을 PNG 이미지로 변환 (hcti.io)
- 💾 **환경변수 관리**: .env 파일로 안전한 API 키 저장
- 🖥️ **단순하고 빠른 UI**: 한 화면에서 모든 작업, 백그라운드 실행으로 응답 없음 문제 해결
- ✅ **빈 값 자동 처리**: 이미지에 빈 항목이 나오지 않도록 기본값 자동 입력

## 📦 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
git clone <repository-url>
cd 상세페이지제작툴
```

### 2. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

설치되는 패키지:
- `openai>=1.52.0` - OpenAI API 클라이언트
- `requests>=2.32.3` - HTTP 요청 처리
- `python-dotenv>=1.0.0` - 환경변수 관리

### 3. 환경변수 설정

`.env.example` 파일을 복사하여 `.env` 파일 생성:

```bash
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux
```

`.env` 파일을 열어 실제 값으로 수정:

```env
# API 설정
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
HCTI_USER_ID=your_user_id
HCTI_API_KEY=your_api_key

# Google Apps Script 웹앱 URL
SHEETS_WEB_APP_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec

# Google Sheets 설정
WATCH_SPREADSHEET_ID=1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c
WATCH_SHEET_NAME=시트1
TARGET_SPREADSHEET_ID=1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c
TARGET_SHEET_NAME=도서정리

# 실행 설정
POLL_INTERVAL=60
OUTPUT_DIR=./output
```

## 🚀 사용 방법

### GUI 모드 (권장)

```bash
python gui.py
```

#### GUI 주요 기능:

1. **설정 저장** 💾
   - UI에서 API 키와 설정을 입력
   - "설정 저장" 버튼으로 `.env` 파일에 저장
   - 다음 실행 시 자동으로 로드됨

2. **한 번 실행** ▶
   - 현재 시트에서 새로운 행을 한 번만 처리
   - 테스트나 수동 실행에 적합

3. **시작 (연속)** 🔄
   - 백그라운드에서 지속적으로 새 행 감시
   - `POLL_INTERVAL` 주기마다 자동 체크

4. **중지** ⏸
   - 연속 실행 중지

5. **실시간 로그** 📋
   - 처리 과정을 실시간으로 확인
   - 오류 발생 시 상세 내용 표시

### CLI 모드

```bash
# 한 번만 실행
python main.py

# 연속 실행 (60초마다 체크)
python main.py --loop --interval 60
```

## 📊 Google Apps Script 설정

공개 Google Sheets에 데이터를 쓰기 위해 Apps Script 웹앱이 필요합니다.

### 1. Apps Script 코드 작성

Google Sheets에서 **확장 프로그램 > Apps Script** 열기:

```javascript
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    
    if (data.action === "updateMetadata") {
      // 이미지 URL 업데이트
      var ss = SpreadsheetApp.openById(data.spreadsheetId);
      var sheet = ss.getSheetByName(data.sheetName);
      var row = data.rowNumber;
      
      sheet.getRange(row, 36).setValue(data.imageUrl);  // AJ열
      sheet.getRange(row, 37).setValue(data.timestamp); // AK열
      
      return ContentService.createTextOutput(JSON.stringify({success: true}))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      // 새 행 추가
      var ss = SpreadsheetApp.openById(data.spreadsheetId);
      var sheet = ss.getSheetByName(data.sheetName);
      
      sheet.appendRow(data.values);
      var lastRow = sheet.getLastRow();
      
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        rowNumber: lastRow
      })).setMimeType(ContentService.MimeType.JSON);
    }
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

### 2. 웹앱 배포

1. **배포 > 새 배포** 클릭
2. **유형 선택**: 웹 앱
3. **다음 사용자로 실행**: 나
4. **액세스 권한**: **모든 사용자** (중요!)
5. **배포** 클릭
6. 생성된 **웹 앱 URL**을 복사하여 `.env` 파일의 `SHEETS_WEB_APP_URL`에 입력

## 🎨 출력 형식

각 처리된 행에 대해 다음 파일들이 생성됩니다:

```
output/
├── 20250106_143022_src2_dst14_경제학개론.html  # 렌더링된 HTML
├── 20250106_143022_src2_dst14_경제학개론.json  # 추출된 JSON 데이터
└── 20250106_143022_src2_dst14_경제학개론.png   # 최종 이미지
```

### HTML 템플릿 특징

- **모던 그라디언트 히어로**: 보라색 계열 (#667eea → #764ba2)
- **카드 기반 레이아웃**: 특징 항목별 카드 UI
- **호버 효과**: 인터랙티브한 UX
- **반응형 디자인**: 모바일/태블릿 대응
- **글라스모피즘**: backdrop-filter blur 효과

## 🤖 AI 프롬프트 설정

### 마케팅 최적화된 콘텐츠 생성 가이드

- **recommendation**: 40-60자 (독자 니즈 → 해결책)
- **feature_title**: 10자 이내 (핵심 가치)
- **feature_desc**: 50-80자 (구체적 혜택)
- **promo_line**: 15-25자 (임팩트 문구)
- **intro_summary**: 80-120자 (핵심 요약)

자세한 프롬프트는 `main.py`의 `PROMPT_BODY` 참조.

## 📁 프로젝트 구조

```
상세페이지제작툴/
├── main.py              # 핵심 파이프라인 로직
├── gui.py               # Toss 스타일 GUI (신규)
├── gui_old.py           # 기존 GUI 백업
├── requirements.txt     # 필수 패키지
├── .env                 # 환경변수 (git에 추적 안 됨)
├── .env.example         # 환경변수 템플릿
├── state.json           # 마지막 처리 행 번호
├── main_backup.py       # main.py 백업
└── output/              # 결과물 저장 폴더
```

## 🔐 보안 주의사항

- ⚠️ `.env` 파일을 절대 Git에 커밋하지 마세요!
- `.gitignore`에 `.env` 추가 권장
- API 키는 읽기 전용 권한만 부여하세요

## 🐛 문제 해결

### ImportError: No module named 'dotenv'
```bash
pip install python-dotenv
```

### 401 Unauthorized (Apps Script)
- 웹앱 배포 시 **액세스 권한**을 "모든 사용자"로 설정했는지 확인
- 웹앱 URL이 `.env`에 정확히 입력되었는지 확인

### OpenAI API 오류
- `OPENAI_API_KEY`가 올바른지 확인
- API 잔액이 충분한지 확인

### Google Sheets 읽기 실패
- 스프레드시트 공유 설정: "링크가 있는 모든 사용자"
- `WATCH_SPREADSHEET_ID`가 정확한지 확인

## 📝 변경 이력

### v2.1.0 (2025-01-06) - 🚀 성능 및 UX 개선
- ⚡ **응답 없음 문제 해결**: 백그라운드 스레드로 실행, UI 즉시 반응
- 📏 **스크롤 제거**: 필수 필드만 표시, 1000x700 창에 모두 표시
- ✅ **빈 항목 자동 처리**: 이미지에 빈 값이 나오지 않도록 기본값 자동 입력
- 🎨 **UI 단순화**: 복잡한 설정 제거, 더 깔끔한 인터페이스
- 📊 **실시간 상태 업데이트**: 색상으로 구분되는 상태 표시

### v2.0.0 (2025-01-06)
- ✨ Toss 스타일 모던 UI 적용
- 💾 .env 파일 기반 환경변수 관리
- 📊 실시간 상태 카드 추가
- 🎨 한 화면에서 모든 기능 접근 가능
- 🔄 스크롤 가능한 설정 패널

### v1.0.0 (2025-01-05)
- 🎉 초기 릴리즈
- 🤖 OpenAI GPT-4o-mini 통합
- 📸 HTML-to-Image 렌더링
- 🖥️ 기본 Tkinter GUI

## 📄 라이선스

MIT License

## 🙋 문의

문제가 발생하거나 기능 제안이 있으시면 Issue를 열어주세요!

---

<p align="center">
  Made with ❤️ for 한빛아카데미
</p>
