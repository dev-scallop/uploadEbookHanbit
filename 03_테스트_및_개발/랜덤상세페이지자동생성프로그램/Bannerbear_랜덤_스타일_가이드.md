# Bannerbear 랜덤 스타일 적용 가이드

## 🎨 개요

Bannerbear 템플릿에서 **색상, 배경, 폰트 등을 랜덤으로 자동 변경**할 수 있습니다!

---

## ✅ 이미 구현된 기능

### 1. **랜덤 색상 적용**

현재 코드는 자동으로 랜덤 색상을 Bannerbear에 전달합니다:

```python
# main.py에서 자동 생성
style = {
    'primary_color': '#2C3E50',    # 랜덤
    'secondary_color': '#E74C3C',   # 랜덤
    'accent_color': '#F39C12',      # 랜덤
    'neutral_color': '#ECF0F1'      # 랜덤
}

# Bannerbear 레이어에 적용
modifications = [
    {
        "name": "title",
        "text": "책 제목",
        "color": primary_color  # 랜덤 색상 자동 적용
    },
    {
        "name": "footer",
        "background": primary_color  # 배경색도 랜덤
    }
]
```

---

## 🎯 Bannerbear에서 랜덤으로 변경 가능한 요소

### 1. **텍스트 색상 (Text Color)**
```python
{
    "name": "title",
    "text": "책 제목",
    "color": "#FF5733"  # HEX 색상 코드
}
```

### 2. **배경색 (Background Color)**
```python
{
    "name": "section_box",
    "background": "#ECF0F1"
}
```

### 3. **그라디언트 배경**
```python
{
    "name": "background",
    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
}
```

### 4. **투명도 (Opacity)**
```python
{
    "name": "overlay",
    "background": "rgba(0, 0, 0, 0.5)"  # 반투명 검은색
}
```

### 5. **이미지 URL 변경**
```python
{
    "name": "background_image",
    "image_url": "https://unsplash.com/random/1000x1500"  # 랜덤 이미지
}
```

---

## 🚀 고급 랜덤화 옵션

### Option 1: AI가 색상 조합 추천

OpenAI GPT-4에게 색상 조합을 물어보기:

```python
# src/ai/text_generator.py에 추가
def generate_color_scheme(self, keywords: List[str]) -> Dict[str, str]:
    """키워드 기반 색상 조합 생성"""
    prompt = f"""
    다음 키워드에 어울리는 색상 조합을 추천해주세요:
    키워드: {', '.join(keywords)}
    
    응답 형식 (HEX 코드):
    Primary: #XXXXXX
    Secondary: #XXXXXX
    Accent: #XXXXXX
    Background: #XXXXXX
    """
    
    response = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 전문 컬러리스트입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # 응답 파싱하여 색상 딕셔너리 반환
    return parse_colors(response.choices[0].message.content)
```

### Option 2: DALL-E로 배경 이미지 생성

```python
# 책 키워드 기반으로 추상 배경 생성
background_url = image_generator.generate_abstract_background(
    keywords=book.keywords,
    style="modern, minimalist, abstract"
)

modifications.append({
    "name": "background_image",
    "image_url": background_url
})
```

### Option 3: 무료 배경 이미지 API 사용

```python
import requests

def get_random_background(keywords: str) -> str:
    """Unsplash API로 랜덤 배경 이미지"""
    query = '+'.join(keywords)
    url = f"https://source.unsplash.com/1000x1500/?{query}"
    return url

# 사용 예
background_url = get_random_background(['책', '교육', '학습'])
```

---

## 📝 템플릿 제작 시 랜덤 지원 설정

### 1. 색상 변경 가능하게 만들기

Bannerbear 템플릿에서 **"Allow API modifications"** 체크:

```
레이어 선택 → Properties 패널
☑ Allow color changes
☑ Allow background changes
☑ Allow text changes
```

### 2. 기본 색상 설정

템플릿에 기본 색상을 설정해두면, API로 덮어쓰기 가능:

```
Title Layer:
- Default Color: #2C3E50
- API로 #FF5733 전달하면 → 빨간색으로 변경됨
```

---

## 🎨 실전 예제: 완전 랜덤 디자인

### 예제 1: 색상 팔레트 자동 선택

```python
# config.py에 추가
COLOR_PALETTES = [
    {
        'name': 'Ocean Blue',
        'primary': '#2C3E50',
        'secondary': '#3498DB',
        'accent': '#1ABC9C',
        'neutral': '#ECF0F1'
    },
    {
        'name': 'Sunset Orange',
        'primary': '#E67E22',
        'secondary': '#F39C12',
        'accent': '#E74C3C',
        'neutral': '#FDF2E9'
    },
    {
        'name': 'Forest Green',
        'primary': '#27AE60',
        'secondary': '#16A085',
        'accent': '#F1C40F',
        'neutral': '#D5F4E6'
    }
]

# StyleRandomizer에서 사용
import random
selected_palette = random.choice(COLOR_PALETTES)
```

### 예제 2: 카테고리별 색상

```python
def get_category_colors(keywords: List[str]) -> Dict[str, str]:
    """키워드 기반 카테고리별 색상"""
    
    if any(k in ['프로그래밍', '코딩'] for k in keywords):
        return {'primary': '#2C3E50', 'accent': '#3498DB'}  # 블루 계열
    
    elif any(k in ['디자인', '예술'] for k in keywords):
        return {'primary': '#E74C3C', 'accent': '#F39C12'}  # 따뜻한 계열
    
    elif any(k in ['비즈니스', '경영'] for k in keywords):
        return {'primary': '#34495E', 'accent': '#16A085'}  # 차분한 계열
    
    else:
        return {'primary': '#7F8C8D', 'accent': '#95A5A6'}  # 중립 계열
```

---

## 🔄 현재 구현된 랜덤 시스템

### 자동으로 적용되는 것:
- ✅ **색상 (Color)**: Primary, Secondary, Accent, Neutral 4가지 랜덤
- ✅ **레이아웃**: 9가지 템플릿 중 랜덤 선택
- ✅ **폰트**: 헤딩/본문 폰트 랜덤 조합
- ✅ **텍스트 톤**: Formal / Marketing / Emotional 랜덤

### 추가 가능한 것:
- ⬜ **배경 이미지**: DALL-E 또는 Unsplash
- ⬜ **그라디언트 방향**: 45도, 90도, 135도 등
- ⬜ **섀도우 강도**: 작게/중간/크게
- ⬜ **테두리 스타일**: 둥근 모서리 반경

---

## 🎬 실행 방법

### 기본 (색상만 랜덤)
```bash
python main.py --source sheets --count 5 --use-bannerbear
```

### 배경 이미지도 랜덤 (구현 필요)
```bash
python main.py --source sheets --count 5 --use-bannerbear --random-background
```

---

## 📊 랜덤 결과 예시

**책 1: 파이썬 프로그래밍**
```
Primary: #2C3E50 (남색)
Secondary: #3498DB (파란색)
Accent: #1ABC9C (청록색)
→ 프로그래밍 느낌의 차가운 톤
```

**책 2: 감성 에세이**
```
Primary: #E74C3C (빨간색)
Secondary: #F39C12 (주황색)
Accent: #F1C40F (노란색)
→ 따뜻하고 감성적인 톤
```

**책 3: 비즈니스 실무**
```
Primary: #34495E (회색)
Secondary: #7F8C8D (진한 회색)
Accent: #16A085 (청록색)
→ 전문적이고 차분한 톤
```

---

## 🛠 추가 개선 아이디어

### 1. 시간대별 색상
```python
import datetime

hour = datetime.now().hour
if 6 <= hour < 12:
    colors = MORNING_PALETTE  # 밝은 색
elif 12 <= hour < 18:
    colors = AFTERNOON_PALETTE  # 생동감 있는 색
else:
    colors = EVENING_PALETTE  # 차분한 색
```

### 2. 계절별 색상
```python
month = datetime.now().month
if month in [3, 4, 5]:
    colors = SPRING_PALETTE  # 파스텔톤
elif month in [6, 7, 8]:
    colors = SUMMER_PALETTE  # 비비드
```

### 3. A/B 테스트
```python
# 두 가지 스타일 생성하여 비교
style_a = randomizer.get_style()
style_b = randomizer.get_style()

# 각각 이미지 생성
image_a = bannerbear.create(style=style_a)
image_b = bannerbear.create(style=style_b)
```

---

## ✅ 체크리스트

- [x] 랜덤 색상 자동 적용
- [x] Bannerbear API에 색상 전달
- [ ] AI 기반 색상 조합 추천 (옵션)
- [ ] 배경 이미지 랜덤 생성 (옵션)
- [ ] 카테고리별 색상 자동 선택 (옵션)

---

**현재 코드로도 이미 랜덤 색상이 자동 적용됩니다!** 

더 고급 기능(AI 추천, 배경 이미지)이 필요하면 말씀해주세요! 🎨
