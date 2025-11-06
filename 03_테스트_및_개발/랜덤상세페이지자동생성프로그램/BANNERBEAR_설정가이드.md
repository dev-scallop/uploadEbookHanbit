# Bannerbear 설정 가이드

## 1. API 키 설정

`.env` 파일에 Bannerbear API 키를 추가하세요:

```properties
BANNERBEAR_API_KEY=your_actual_api_key_here
BANNERBEAR_TEMPLATE_ID=your_template_id_here
```

**API 키는 Bannerbear 대시보드에서 확인할 수 있습니다:**
- https://app.bannerbear.com/account/settings

## 2. 템플릿 생성

Bannerbear에서 책 상세페이지 템플릿을 생성해야 합니다.

### 템플릿에 필요한 레이어:

1. **텍스트 레이어:**
   - `book_title` - 책 제목
   - `author_name` - 저자명
   - `description` - 책 소개
   - `keywords` - 키워드
   - `section_1_title` ~ `section_4_title` - 섹션 제목들
   - `section_1_content` ~ `section_4_content` - 섹션 내용들

2. **이미지 레이어:**
   - `book_cover` - 책 표지 이미지

### 템플릿 만드는 방법:

1. https://app.bannerbear.com/templates 접속
2. "Create New Template" 클릭
3. 참고 이미지처럼 디자인 구성:
   - 상단: 3D 책 표지 영역
   - 중간: 번호가 있는 섹션들 (01, 02, 03, 04)
   - 하단: CTA 버튼 영역
4. 각 레이어에 위에서 언급한 이름 지정
5. 템플릿 ID 복사 → `.env`에 추가

## 3. 패키지 설치

**별도 패키지 설치 불필요!** 

Bannerbear는 REST API를 직접 호출하므로 기본 `requests` 라이브러리만 있으면 됩니다.

## 4. 사용 방법

### Python 코드에서 사용:

```python
from src.ai.bannerbear_generator import BannerbearGenerator

# 초기화
generator = BannerbearGenerator()

# 책 상세페이지 생성
sections = [
    {"title": "이 책의 특징", "content": "기초 개념부터..."},
    {"title": "학습 내용", "content": "Python 기초, 데이터 분석..."},
    {"title": "추천 대상", "content": "프로그래밍 입문자..."},
    {"title": "특별 혜택", "content": "무료 동영상 강의..."}
]

image_path = generator.create_book_detail_page(
    title="파이썬 프로그래밍 입문",
    author="홍길동",
    description="초보자를 위한 파이썬 완벽 가이드...",
    keywords=["Python", "프로그래밍", "입문", "데이터분석"],
    cover_image_url="https://example.com/cover.jpg",
    sections=sections
)

print(f"생성된 이미지: {image_path}")
```

### main.py에 통합하기:

기존 `image_generator.py` 대신 `bannerbear_generator.py`를 사용하도록 수정하면 됩니다.

## 5. 템플릿 정보 확인

템플릿이 제대로 설정되었는지 확인:

```python
from src.ai.bannerbear_generator import BannerbearGenerator

generator = BannerbearGenerator()
template_info = generator.get_template_info()
print(template_info)
```

## 6. 비용 안내

- **Free Plan:** 월 30개 이미지 무료
- **Starter Plan:** $29/월, 300개 이미지
- **Pro Plan:** $99/월, 1,500개 이미지

## 7. 참고 자료

- Bannerbear 공식 문서: https://www.bannerbear.com/documentation/
- Python SDK: https://github.com/yongfook/bannerbear-python
- 템플릿 예시: https://www.bannerbear.com/templates/

## 8. 문제 해결

### API 키 오류
```
Error: Invalid API key
```
→ `.env` 파일의 `BANNERBEAR_API_KEY`를 확인하세요.

### 템플릿 ID 오류
```
Error: Template not found
```
→ `.env` 파일의 `BANNERBEAR_TEMPLATE_ID`를 확인하세요.

### 레이어 이름 오류
```
Error: Layer 'book_title' not found
```
→ 템플릿에 해당 레이어가 있는지 확인하세요.

## 9. 다음 단계

1. ✅ `.env` 파일에 API 키 추가
2. ✅ `bannerbear` 패키지 설치
3. ⬜ Bannerbear에서 템플릿 생성
4. ⬜ 템플릿 ID를 `.env`에 추가
5. ⬜ 테스트 실행: `python main.py --source test --count 1`

## 10. 예상 결과

참고 이미지와 같은 전문적인 책 상세페이지:
- 3D 책 표지 목업
- 깔끔한 레이아웃
- 번호가 있는 섹션
- 아이콘과 그래픽 요소
- 브랜드 컬러 적용

템플릿 생성이 완료되면 알려주세요. 다음 단계를 도와드리겠습니다!
