# 🚀 빠른 시작 가이드

이 문서는 랜덤 레이아웃 상세페이지 자동 생성 시스템을 빠르게 시작하는 방법을 안내합니다.

## 📦 1단계: 설치

### 가상환경 생성 및 활성화
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\activate
```

### 필수 패키지 설치
```powershell
pip install -r requirements.txt
```

## ⚙️ 2단계: 환경 설정

### .env 파일 생성
```powershell
copy .env.example .env
```

### API 키 설정 (.env 파일 편집)
```
# 최소 필수 설정
OPENAI_API_KEY=your_openai_api_key_here

# 선택사항
GOOGLE_SHEET_ID=your_google_sheet_id
WORDPRESS_URL=https://your-site.com
```

## 🎨 3단계: 첫 페이지 생성

### 테스트 모드로 페이지 생성
```powershell
python main.py --source test --count 3
```

생성된 페이지는 `output/html/` 폴더에 저장됩니다.
JPG 이미지는 `output/images/` 폴더에 저장됩니다.

### AI 기능 사용하여 생성
```powershell
python main.py --source test --count 1 --use-ai
```

### AI 이미지까지 생성 (시간 소요)
```powershell
python main.py --source test --count 1 --use-ai --generate-images
```

## 🧪 4단계: 테스트 실행

### 기본 테스트
```powershell
python tests/test_generation.py --test basic
```

### 모든 템플릿 테스트
```powershell
python tests/test_generation.py --test templates
```

### 다양성 보장 테스트
```powershell
python tests/test_generation.py --test diversity
```

### 전체 테스트
```powershell
python tests/test_generation.py --test all
```

## 📊 5단계: Google Sheets 연동 (선택)

### 1. Google Cloud Console 설정
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성
3. Google Sheets API 활성화
4. 서비스 계정 생성
5. 서비스 계정 키 (JSON) 다운로드

### 2. 인증 파일 설정
```powershell
# credentials.json을 프로젝트 루트에 저장
```

### 3. Google Sheets에서 데이터 가져오기
```powershell
python main.py --source sheets --use-ai
```

## 📁 출력 파일 위치

- **HTML 페이지**: `output/html/`
- **JPG 이미지**: `output/images/`
- **로그 파일**: `logs/automation.log`

## 💡 활용 예시

### 예시 1: 빠른 프로토타입
```powershell
python main.py --source test --count 5
```

### 예시 2: AI 콘텐츠 생성
```powershell
python main.py --source test --count 3 --use-ai
```

### 예시 3: 완전 자동화 (AI + 이미지 + JPG)
```powershell
python main.py --source sheets --use-ai --generate-images
```

### 예시 4: 특정 도서만 생성
```powershell
python main.py --source sheets --isbn 9788901234567 --use-ai
```

### 예시 5: HTML만 생성 (JPG 변환 생략)
```powershell
python main.py --source test --no-jpg
```

## ❓ 문제 해결

### ImportError 발생 시
```powershell
pip install -r requirements.txt --upgrade
```

### OpenAI API 에러
- `.env` 파일에서 `OPENAI_API_KEY` 확인
- API 키 유효성 확인
- `--use-ai` 옵션 없이 실행

### 템플릿을 찾을 수 없음
```powershell
# templates/ 폴더 존재 확인
dir templates
```

## 🎉 다음 단계

1. ✅ 기본 페이지 생성 테스트 완료
2. ✅ 템플릿 커스터마이징 (`templates/` 폴더)
3. ✅ 브랜드 컬러/폰트 수정 (`config.py`)
4. ✅ Google Sheets 연동
5. ✅ WordPress 자동 업로드
6. ✅ 스케줄링 설정 (cron/작업 스케줄러)

## 📚 추가 문서

- [전체 문서](README.md)
- [PRD](docs/PRD.md)
- [API 문서](docs/API.md)

---

문제가 발생하면 `logs/automation.log` 파일을 확인하세요!
