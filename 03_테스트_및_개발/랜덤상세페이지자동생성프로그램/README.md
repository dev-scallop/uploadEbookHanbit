# 랜덤 레이아웃 상세페이지 자동 생성 시스템

도서 상세페이지를 자동으로 생성하고, 레이아웃·스타일·카피라이팅을 랜덤화하여 사용자 경험을 다양화하는 자동화 시스템입니다.

## 🎯 주요 기능

- **데이터 기반 자동화**: 도서 메타데이터를 기반으로 상세페이지 자동 생성
- **랜덤화 시스템**: 레이아웃, 폰트, 컬러, 이미지 배치, 텍스트 톤 랜덤화
- **AI 연동**: OpenAI API를 활용한 텍스트 및 이미지 생성
- **JPG 출력**: HTML을 고품질 JPG 이미지로 자동 변환

## 📋 요구사항

- Python 3.8 이상
- OpenAI API 키
- Google Sheets API 인증 정보 (선택)

## 🚀 설치 방법

1. **저장소 클론**
```bash
git clone <repository-url>
cd 랜덤상세페이지자동생성프로그램
```

2. **가상환경 생성 및 활성화**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. **패키지 설치**
```bash
pip install -r requirements.txt
```

4. **환경 변수 설정**
```bash
# .env.example을 .env로 복사
copy .env.example .env

# .env 파일을 편집하여 API 키 등을 입력
```

5. **Google Sheets API 설정 (선택)**
- Google Cloud Console에서 프로젝트 생성
- Google Sheets API 활성화
- 서비스 계정 생성 및 credentials.json 다운로드
- credentials.json을 프로젝트 루트에 저장

## 📖 사용 방법

### 1. 기본 실행

```bash
python main.py
```

### 2. Google Sheets에서 데이터 가져오기

```bash
python main.py --source sheets --sheet-id YOUR_SHEET_ID
```

### 3. 특정 도서만 생성

```bash
python main.py --isbn 9788901234567
```

### 4. JPG 변환 없이 HTML만 생성

```bash
python main.py --source test --no-jpg
```

## 📂 프로젝트 구조

```
랜덤상세페이지자동생성프로그램/
├── config.py                 # 설정 파일
├── main.py                   # 메인 실행 파일
├── requirements.txt          # 패키지 의존성
├── .env.example             # 환경 변수 예시
├── README.md                # 프로젝트 문서
│
├── src/                     # 소스 코드
│   ├── data/               # 데이터 처리
│   │   ├── __init__.py
│   │   ├── book_model.py   # 도서 데이터 모델
│   │   └── sheets_connector.py  # Google Sheets 연동
│   │
│   ├── ai/                 # AI 연동
│   │   ├── __init__.py
│   │   ├── text_generator.py    # 텍스트 생성
│   │   └── image_generator.py   # 이미지 생성
│   │
│   ├── template/           # 템플릿 처리
│   │   ├── __init__.py
│   │   ├── renderer.py     # Jinja2 렌더러
│   │   └── randomizer.py   # 랜덤화 엔진
│   │
│   ├── cms/                # CMS 연동
│   │   ├── __init__.py
│   │   ├── wordpress_uploader.py
│   │   └── shopify_uploader.py
│   │
│   └── utils/              # 유틸리티
│       ├── __init__.py
│       └── logger.py
│
├── templates/              # Jinja2 템플릿
│   ├── layout_hero_left.html
│   ├── layout_hero_right.html
│   ├── layout_card_grid.html
│   ├── layout_banner_top.html
│   ├── layout_magazine.html
│   ├── layout_minimal.html
│   ├── layout_classic.html
│   ├── layout_modern.html
│   └── css/
│       └── styles.css
│
├── output/                 # 생성된 파일
│   ├── html/              # HTML 페이지
│   └── images/            # 생성된 이미지
│
└── tests/                 # 테스트
    ├── sample_data.xlsx
    └── test_generation.py
```

## 🎨 커스터마이징

### 브랜드 가이드라인 수정

`config.py` 파일에서 브랜드 컬러, 폰트, 레이아웃 옵션을 수정할 수 있습니다.

```python
BRAND_COLORS = {
    'primary': ['#YOUR_COLOR', ...],
    ...
}

BRAND_FONTS = {
    'heading': ['Your Font', ...],
    ...
}
```

### 새 템플릿 추가

1. `templates/` 폴더에 새 HTML 파일 생성
2. `config.py`의 `LAYOUT_TEMPLATES` 리스트에 추가

## 🔧 주요 모듈 설명

### 1. 데이터 모듈 (`src/data/`)
- 도서 메타데이터 관리
- Google Sheets, Excel, DB 연동

### 2. AI 모듈 (`src/ai/`)
- OpenAI API를 통한 텍스트 생성
- DALL-E를 통한 이미지 생성

### 3. 템플릿 모듈 (`src/template/`)
- Jinja2 템플릿 렌더링
- 랜덤화 로직 적용

### 4. CMS 모듈 (`src/cms/`)
- WordPress/Shopify 자동 업로드

## 📊 워크플로우

1. **데이터 수집**: Google Sheets 또는 DB에서 도서 정보 가져오기
2. **AI 생성**: 책 소개, 마케팅 카피 생성
3. **랜덤화**: 레이아웃, 컬러, 폰트 랜덤 선택
4. **렌더링**: Jinja2로 HTML 생성
5. **JPG 변환**: HTML을 고품질 JPG 이미지로 변환

## 🧪 테스트

```bash
# 샘플 데이터로 테스트
python tests/test_generation.py

# 단일 도서 테스트
python main.py --test --isbn 9788901234567
```

## 📈 성공 지표 (KPI)

- ✅ 상세페이지 제작 시간 70% 이상 단축
- ✅ 레이아웃 다양성 (중복률 < 20%)
- ✅ 자동 업로드 성공률 95% 이상

## ⚠️ 주의사항

- OpenAI API 사용량에 따른 비용 발생
- 브랜드 가이드라인 준수를 위한 랜덤화 범위 제한
- AI 생성물은 반드시 검수 후 사용 권장

## 📝 라이선스

MIT License

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

## 📧 문의

프로젝트 관련 문의사항은 이슈로 등록해주세요.
