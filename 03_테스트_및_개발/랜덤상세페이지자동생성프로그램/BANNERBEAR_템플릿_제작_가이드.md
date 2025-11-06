# Bannerbear 책 전용 템플릿 제작 가이드

참고 이미지와 같은 전문적인 책 상세페이지를 만들기 위한 단계별 가이드입니다.

---

## 📋 사전 준비

### 필요한 것:
1. ✅ Bannerbear 계정 (https://app.bannerbear.com)
2. ✅ 참고 디자인 이미지 (이미 제공받으신 강화학습 교과서 이미지)
3. ✅ 캔버스 크기 결정: **1000px × 1500px** (세로형) 권장

---

## 🎨 Step 1: 템플릿 생성 시작

### 1-1. Bannerbear 대시보드 접속
```
https://app.bannerbear.com/templates
```

### 1-2. 새 템플릿 만들기
1. **"Create New Template"** 버튼 클릭
2. 템플릿 이름 입력: **"Book Detail Page - Korean"**
3. 캔버스 크기 설정:
   - Width: **1000px**
   - Height: **1500px**
   - Background: **흰색** 또는 **그라디언트**

---

## 📐 Step 2: 레이아웃 구조 설계

참고 이미지를 보면 다음과 같은 구조입니다:

```
┌─────────────────────────────────────┐
│  [헤더 영역]                        │
│  "이론과 실습을 통해 배우는"        │
│  "강화 학습 교과서" (큰 제목)       │
├─────────────────────────────────────┤
│  [책 표지 이미지]                   │
│  (3D 목업 스타일)                   │
├─────────────────────────────────────┤
│  [섹션 1: 누구를 위한 책인가?]     │
│  ✓ 체크박스 리스트                  │
├─────────────────────────────────────┤
│  [섹션 2: 이 책의 특징]            │
│  01 - 내용                         │
├─────────────────────────────────────┤
│  [섹션 3: 학습 내용]               │
│  아이콘 + 텍스트 그리드            │
├─────────────────────────────────────┤
│  [섹션 4: 특별 혜택]               │
│  강조 박스                         │
└─────────────────────────────────────┘
```

---

## 🔧 Step 3: 레이어 추가하기 (핵심!)

Bannerbear는 **레이어 기반**으로 작동합니다. 각 레이어는 API로 동적으로 변경 가능합니다.

### 3-1. 배경 레이어 추가

**Layer Type: Rectangle**
- Name: `background`
- Position: (0, 0)
- Size: 1000 × 1500
- Color: `#F8F9FA` (연한 회색) 또는 그라디언트
- Border: None

---

### 3-2. 헤더 타이틀 레이어

**Layer Type: Text**
- **Name: `header_subtitle`** ⭐ (API에서 참조할 이름)
- Position: (50, 50)
- Font: **Noto Sans KR Bold**
- Size: **32px**
- Color: `#6C757D` (회색)
- Text: "이론과 실습을 통해 배우는" (기본값)
- Alignment: Left

**Layer Type: Text**
- **Name: `book_title`** ⭐
- Position: (50, 100)
- Font: **Noto Sans KR Black**
- Size: **56px**
- Color: `#2C3E50` (진한 남색)
- Text: "강화 학습 교과서" (기본값)
- Alignment: Left
- Line Height: 1.3

---

### 3-3. 책 표지 이미지 레이어

**Layer Type: Image Container**
- **Name: `book_cover_image`** ⭐
- Position: (300, 220) - 중앙 배치
- Size: 400 × 600
- Border Radius: 10px (둥근 모서리)
- Shadow: `0 10px 30px rgba(0,0,0,0.2)`
- Default Image: 플레이스홀더 이미지

**꿀팁:** 3D 목업 효과를 원하면
- Rotation: 약간 회전 (-5도)
- Perspective: 활성화

---

### 3-4. 섹션 1 - "누구를 위한 책인가?"

**Rectangle Layer (배경 박스)**
- Name: `section1_bg`
- Position: (50, 850)
- Size: 900 × 200
- Color: `#FFFFFF`
- Border Radius: 15px
- Shadow: `0 4px 10px rgba(0,0,0,0.1)`

**Text Layer (섹션 제목)**
- **Name: `section1_title`** ⭐
- Position: (80, 880)
- Font: **Noto Sans KR Bold**
- Size: **28px**
- Color: `#2C3E50`
- Text: "📖 누구를 위한 책인가?"

**Text Layer (섹션 내용)**
- **Name: `section1_content`** ⭐
- Position: (80, 930)
- Font: **Noto Sans KR Regular**
- Size: **18px**
- Color: `#495057`
- Text: 여러 줄 텍스트 (기본값)
- Max Lines: 5

---

### 3-5. 섹션 2 - "이 책의 특징"

**Rectangle Layer**
- Name: `section2_bg`
- Position: (50, 1080)
- Size: 900 × 180
- Color: `#E8F5F7` (연한 파란색)
- Border Radius: 15px

**Text Layer (번호)**
- **Name: `section2_number`** ⭐
- Position: (80, 1100)
- Font: **Noto Sans KR Black**
- Size: **48px**
- Color: `#17A2B8` (청록색)
- Text: "01"

**Text Layer (제목)**
- **Name: `section2_title`** ⭐
- Position: (160, 1110)
- Font: **Noto Sans KR Bold**
- Size: **24px**
- Color: `#2C3E50`
- Text: "기초 개념부터 실전까지 포괄"

**Text Layer (내용)**
- **Name: `section2_content`** ⭐
- Position: (160, 1150)
- Font: **Noto Sans KR Regular**
- Size: **16px**
- Color: `#6C757D`
- Text: 상세 설명 (기본값)

---

### 3-6. 섹션 3 - "학습 내용" (아이콘 그리드)

**Rectangle Layer (4개 박스를 각각 만들거나 반복)**

**Example - Box 1:**
- Name: `learning_box1_bg`
- Position: (50, 1290)
- Size: 430 × 120
- Color: `#FFFFFF`
- Border: 3px solid `#17A2B8`
- Border Radius: 10px

**Text Layer:**
- **Name: `learning_box1_text`** ⭐
- Position: (70, 1320)
- Font: **Noto Sans KR Medium**
- Size: **18px**
- Text: "• DQN, A2C, PPO, SAC 등"

(나머지 박스도 동일하게 반복: `learning_box2_text`, `learning_box3_text`, `learning_box4_text`)

---

### 3-7. 푸터 (저자 정보)

**Rectangle Layer**
- Name: `footer_bg`
- Position: (0, 1450)
- Size: 1000 × 50
- Color: `#2C3E50`

**Text Layer**
- **Name: `author_name`** ⭐
- Position: (50, 1460)
- Font: **Noto Sans KR Regular**
- Size: **16px**
- Color: `#FFFFFF`
- Text: "저자: 홍길동"

---

## 📝 Step 4: 레이어 이름 정리 (중요!)

API에서 사용할 레이어 이름들을 정리하세요:

```python
# API에서 참조 가능한 레이어 이름들
LAYER_NAMES = {
    "book_title": "책 제목",
    "header_subtitle": "헤더 부제목",
    "book_cover_image": "책 표지 이미지",
    "section1_title": "섹션1 제목",
    "section1_content": "섹션1 내용",
    "section2_number": "섹션2 번호",
    "section2_title": "섹션2 제목",
    "section2_content": "섹션2 내용",
    "learning_box1_text": "학습내용 1",
    "learning_box2_text": "학습내용 2",
    "learning_box3_text": "학습내용 3",
    "learning_box4_text": "학습내용 4",
    "author_name": "저자명"
}
```

---

## 🎨 Step 5: 색상 스킴 설정

참고 이미지 기반 색상:

```css
/* 주요 색상 */
Primary: #2C3E50 (진한 남색)
Secondary: #17A2B8 (청록색)
Accent: #F39C12 (주황색)
Background: #F8F9FA (연한 회색)
Text: #495057 (회색)
```

Bannerbear 에디터에서:
1. 각 레이어 선택
2. Color Picker로 위 색상 적용
3. Save

---

## 💾 Step 6: 템플릿 저장 및 ID 확인

### 6-1. 템플릿 저장
1. 우측 상단 **"Save Template"** 클릭
2. 템플릿 이름 확인

### 6-2. 템플릿 ID 복사
1. 템플릿 설정 페이지에서 **Template UID** 복사
   - 예: `ABcd1234EFgh5678`
2. `.env` 파일에 추가:
```properties
BANNERBEAR_TEMPLATE_ID=ABcd1234EFgh5678
```

---

## 🧪 Step 7: 테스트 이미지 생성

### 7-1. Bannerbear 대시보드에서 테스트
1. 템플릿 페이지에서 **"Create Image"** 클릭
2. 각 레이어에 샘플 데이터 입력:
   ```
   book_title: "파이썬 프로그래밍 입문"
   author_name: "저자: 홍길동"
   section1_content: "프로그래밍 초보자를 위한 완벽 가이드"
   ```
3. **"Generate"** 클릭
4. 결과 확인

### 7-2. Python 코드로 테스트
```python
python check_template.py
```

새 템플릿 ID로 수정 후:
```python
python main.py --source sheets --count 1 --use-bannerbear
```

---

## 🔄 Step 8: 코드 업데이트

생성한 템플릿에 맞게 `bannerbear_generator.py` 수정:

```python
# 새 템플릿 레이어 구조에 맞게 수정
modifications = [
    {
        "name": "book_title",  # 실제 레이어 이름
        "text": title
    },
    {
        "name": "header_subtitle",
        "text": "이론과 실습을 통해 배우는"
    },
    {
        "name": "book_cover_image",
        "image_url": cover_image_url
    },
    {
        "name": "section1_title",
        "text": "📖 이 책의 특징"
    },
    {
        "name": "section1_content",
        "text": description[:200]
    },
    {
        "name": "section2_number",
        "text": "01"
    },
    {
        "name": "section2_title",
        "text": "핵심 내용"
    },
    {
        "name": "section2_content",
        "text": f"키워드: {' · '.join(keywords[:5])}"
    },
    {
        "name": "author_name",
        "text": f"저자: {author}"
    }
]
```

---

## 🎯 Step 9: 고급 팁

### 9-1. 3D 책 목업 효과
- **Transform** 옵션 사용
- Rotation Y: -15도
- Shadow: 더 진하게

### 9-2. 그라디언트 배경
```
Linear Gradient:
- Start: #E8F5F7
- End: #FFFFFF
- Direction: Top to Bottom
```

### 9-3. 아이콘 추가
- **Image Layer** 사용
- 무료 아이콘: https://icons8.com
- SVG 형식 권장

### 9-4. 반응형 텍스트
- **Auto-resize** 옵션 활성화
- Max Width 설정으로 텍스트 길이 제어

---

## 📊 Step 10: 템플릿 최적화

### 10-1. 텍스트 길이 제한
```python
# 코드에서 텍스트 길이 제한
description = description[:300] if len(description) > 300 else description
```

### 10-2. 폰트 로딩
- Bannerbear는 Google Fonts 지원
- 한글 폰트: **Noto Sans KR**, **Nanum Gothic**, **Nanum Myeongjo**

### 10-3. 이미지 최적화
- 책 표지 이미지: 권장 크기 400×600
- 포맷: JPG 또는 PNG
- 파일 크기: 최대 5MB

---

## ✅ 완료 체크리스트

- [ ] Bannerbear 템플릿 생성 완료
- [ ] 모든 레이어 이름 정의
- [ ] 템플릿 ID `.env`에 추가
- [ ] 색상 스킴 적용
- [ ] 폰트 설정 (한글 지원)
- [ ] 테스트 이미지 생성 성공
- [ ] Python 코드 레이어 매핑 업데이트
- [ ] 실제 데이터로 테스트 완료

---

## 🆘 문제 해결

### "Layer not found" 에러
→ `check_template.py`로 레이어 이름 확인

### 한글이 깨짐
→ Google Fonts의 한글 폰트 사용 (Noto Sans KR)

### 이미지가 표시 안됨
→ 이미지 URL이 공개(public) 상태인지 확인

### 텍스트가 잘림
→ Layer의 Width/Height 늘리기 또는 Font Size 줄이기

---

## 📚 참고 자료

- Bannerbear 공식 문서: https://developers.bannerbear.com/
- 템플릿 갤러리: https://www.bannerbear.com/templates/
- Google Fonts 한글: https://fonts.google.com/?subset=korean
- 무료 아이콘: https://heroicons.com/

---

## 🎓 다음 단계

템플릿이 완성되면:
1. 여러 책으로 대량 생성 테스트
2. 디자인 미세 조정
3. 추가 템플릿 변형 만들기 (다크 모드, 미니멀 등)

**템플릿 만드실 때 막히는 부분 있으면 언제든 물어보세요!** 🚀
