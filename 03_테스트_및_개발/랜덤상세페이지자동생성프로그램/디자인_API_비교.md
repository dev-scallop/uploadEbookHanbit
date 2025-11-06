# 디자인 자동화 API 비교 가이드

Bannerbear 외에 책 상세페이지 자동 생성에 사용할 수 있는 대안 API들을 비교합니다.

---

## 🏆 추천 순위

### 1위: **Canva API** ⭐⭐⭐⭐⭐
### 2위: **Placid.app** ⭐⭐⭐⭐⭐
### 3위: **Shotstack** ⭐⭐⭐⭐
### 4위: **Abyssale** ⭐⭐⭐⭐
### 5위: **Rocketium** ⭐⭐⭐

---

## 📊 상세 비교표

| 서비스 | 가격 | 한글 지원 | 템플릿 | API 품질 | 추천도 |
|--------|------|-----------|--------|----------|---------|
| **Canva API** | $119/월 | ✅ 완벽 | 수백만개 | ⭐⭐⭐⭐⭐ | 최고 |
| **Placid** | $49/월 | ✅ 가능 | 직접제작 | ⭐⭐⭐⭐⭐ | 최고 |
| **Bannerbear** | $29/월 | ✅ 가능 | 직접제작 | ⭐⭐⭐⭐ | 좋음 |
| **Shotstack** | $49/월 | ⚠️ 제한적 | JSON기반 | ⭐⭐⭐⭐ | 좋음 |
| **Abyssale** | $39/월 | ✅ 가능 | 직접제작 | ⭐⭐⭐⭐ | 좋음 |
| **Rocketium** | $99/월 | ⚠️ 제한적 | 직접제작 | ⭐⭐⭐ | 보통 |

---

## 🥇 1. Canva API (강력 추천!)

### 장점:
- ✅ **세계 최고 수준의 디자인 플랫폼**
- ✅ **수백만 개의 전문 템플릿** (무료 + 유료)
- ✅ **한글 폰트 완벽 지원** (수백 종류)
- ✅ **드래그앤드롭 에디터** (템플릿 제작 초간단)
- ✅ **AI 디자인 추천** 내장
- ✅ **팀 협업 기능**

### 단점:
- ❌ 가격이 비쌈 ($119/월)
- ❌ API 사용 제한 (월 1,000 콜)

### 가격:
```
Canva Pro API:
- $119/월
- 1,000 API 호출/월
- 초과 시 $0.10/콜
```

### 사용 예시:
```python
import requests

CANVA_API_KEY = "your_canva_api_key"

# 1. 템플릿 선택 (Canva에서 미리 만든 템플릿)
template_id = "DAFxxx..."  # Canva 템플릿 ID

# 2. 데이터 전달
payload = {
    "design_id": template_id,
    "data": {
        "title": "한 권으로 끝내는 회계원리",
        "author": "김선미",
        "description": "회계의 기초부터 실전까지...",
        "image_url": "https://example.com/cover.jpg"
    }
}

# 3. 이미지 생성
response = requests.post(
    "https://api.canva.com/v1/autofills",
    headers={"Authorization": f"Bearer {CANVA_API_KEY}"},
    json=payload
)

image_url = response.json()["url"]
```

### 추천 이유:
- **가장 쉽고 빠름**: 템플릿 수백만 개 중 선택만 하면 됨
- **디자인 품질 최고**: 전문 디자이너가 만든 템플릿
- **한글 완벽**: Noto Sans KR, 나눔고딕 등 기본 지원

### 공식 사이트:
https://www.canva.com/developers/

---

## 🥈 2. Placid.app (1등과 동급!)

### 장점:
- ✅ **Bannerbear와 비슷하지만 더 강력**
- ✅ **무제한 템플릿** 생성 가능
- ✅ **동적 QR 코드** 생성
- ✅ **비디오도 생성 가능**
- ✅ **Zapier/Make.com 통합**
- ✅ **한글 폰트 지원** (Google Fonts)

### 단점:
- ❌ 템플릿 직접 제작 필요

### 가격:
```
Starter: $49/월
- 10,000 이미지/월
- 무제한 템플릿
- REST API

Pro: $99/월
- 30,000 이미지/월
- 우선 지원
```

### 사용 예시:
```python
import requests

PLACID_API_KEY = "your_placid_token"

payload = {
    "layers": {
        "title": {
            "text": "파이썬 프로그래밍 입문",
            "color": "#2C3E50"
        },
        "author": {
            "text": "저자: 홍길동"
        },
        "cover": {
            "image": "https://example.com/cover.jpg"
        }
    }
}

response = requests.post(
    f"https://api.placid.app/api/rest/templates/TEMPLATE_ID/create",
    headers={
        "Authorization": f"Bearer {PLACID_API_KEY}",
        "Content-Type": "application/json"
    },
    json=payload
)

image_url = response.json()["image_url"]
```

### 추천 이유:
- **Bannerbear보다 저렴**하고 기능 많음
- **무제한 템플릿** 생성 가능
- **비디오도 생성** 가능 (책 소개 영상)

### 공식 사이트:
https://placid.app/

---

## 🥉 3. Shotstack (개발자 친화적)

### 장점:
- ✅ **JSON으로 모든 것 제어** (코드로 디자인)
- ✅ **비디오 + 이미지** 모두 생성
- ✅ **AWS 기반** (빠르고 안정적)
- ✅ **무료 플랜** 있음 (월 20개)
- ✅ **오픈소스 SDK** (Python, Node.js)

### 단점:
- ❌ 비주얼 에디터 없음 (JSON만)
- ❌ 한글 폰트 제한적
- ❌ 학습 곡선 높음

### 가격:
```
Free: $0/월
- 20 렌더링/월
- 480p 해상도

Starter: $49/월
- 500 렌더링/월
- 1080p 해상도
```

### 사용 예시:
```python
import shotstack_sdk as shotstack

# JSON으로 디자인 정의
timeline = shotstack.Timeline(
    tracks=[
        shotstack.Track(
            clips=[
                shotstack.TitleClip(
                    asset=shotstack.TitleAsset(
                        text="한 권으로 끝내는 회계원리",
                        style="blockbuster"
                    ),
                    start=0,
                    length=5
                ),
                shotstack.ImageClip(
                    asset=shotstack.ImageAsset(
                        src="https://example.com/cover.jpg"
                    ),
                    start=0,
                    length=5
                )
            ]
        )
    ]
)

# 렌더링
response = api.post_render(timeline)
```

### 추천 이유:
- **개발자가 선호**: 모든 것을 코드로 제어
- **비디오도 생성**: 책 소개 영상 자동화 가능
- **무료 플랜**: 테스트하기 좋음

### 공식 사이트:
https://shotstack.io/

---

## 4. Abyssale

### 장점:
- ✅ **간단한 UI**
- ✅ **빠른 렌더링** (1-2초)
- ✅ **다양한 포맷** (PNG, JPG, PDF, GIF)
- ✅ **Figma 플러그인** 있음

### 단점:
- ❌ 템플릿 제한
- ❌ 고급 기능 부족

### 가격:
```
Starter: $39/월
- 3,000 이미지/월
- 10 템플릿
```

### 공식 사이트:
https://www.abyssale.com/

---

## 5. Rocketium

### 장점:
- ✅ **비디오 특화**
- ✅ **소셜 미디어 최적화**

### 단점:
- ❌ 비쌈
- ❌ 책 상세페이지에는 과함

### 가격:
```
$99/월 ~
```

### 공식 사이트:
https://rocketium.com/

---

## 🆓 무료 대안

### 1. **Puppeteer + HTML/CSS** (완전 무료!)

```python
from playwright.sync_api import sync_playwright

def generate_image_from_html(html_content: str) -> bytes:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        screenshot = page.screenshot(full_page=True)
        browser.close()
        return screenshot

# 사용 예시
html = """
<html>
<head>
    <style>
        body { font-family: 'Noto Sans KR'; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { width: 1000px; padding: 50px; }
        .title { font-size: 56px; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">한 권으로 끝내는 회계원리</h1>
    </div>
</body>
</html>
"""

image_bytes = generate_image_from_html(html)
```

**장점:**
- ✅ 완전 무료
- ✅ 무제한 생성
- ✅ 완전한 커스터마이징
- ✅ 이미 구현되어 있음!

**단점:**
- ❌ 디자인을 직접 코딩해야 함
- ❌ 템플릿 제작 시간 필요

---

### 2. **PIL/Pillow** (완전 무료!)

```python
from PIL import Image, ImageDraw, ImageFont

# 이미지 생성
img = Image.new('RGB', (1000, 1500), color='#F8F9FA')
draw = ImageDraw.Draw(img)

# 폰트 로드
font_title = ImageFont.truetype("NotoSansKR-Bold.ttf", 56)

# 텍스트 그리기
draw.text((50, 100), "한 권으로 끝내는 회계원리", fill='#2C3E50', font=font_title)

# 저장
img.save("output.jpg")
```

**장점:**
- ✅ 완전 무료
- ✅ 빠름
- ✅ 오프라인 작동

**단점:**
- ❌ 복잡한 디자인 어려움
- ❌ 그라디언트/그림자 제한적

---

## 🎯 결론 및 추천

### 상황별 추천:

#### 1. **최고 품질 + 빠른 개발 원하면**
→ **Canva API** ($119/월)
- 가장 쉽고 결과물 최고
- 템플릿 골라서 데이터만 넣으면 끝

#### 2. **가성비 최고 + 전문적인 결과**
→ **Placid.app** ($49/월)
- Bannerbear보다 기능 많음
- 무제한 템플릿
- 비디오도 생성 가능

#### 3. **완전 무료로 하고 싶다면**
→ **현재 시스템 (Playwright + HTML/CSS)**
- 이미 구현되어 있음
- 무제한 무료
- 디자인만 개선하면 됨

#### 4. **개발자 친화적 + 비디오도 필요**
→ **Shotstack** ($49/월)
- JSON으로 완전 제어
- 무료 플랜으로 테스트 가능

#### 5. **저렴하게 시작**
→ **Bannerbear** ($29/월) - 현재 사용 중
- 가장 저렴
- 간단한 기능

---

## 💰 비용 비교 (월 1,000개 이미지 생성 기준)

```
Canva API:      $119 (1,000개 포함)
Placid:         $49  (10,000개 포함) ✅ 최고 가성비
Bannerbear:     $29  (300개) + 추가 비용 = 약 $50
Shotstack:      $49  (500개) + 추가 비용 = 약 $80
Abyssale:       $39  (3,000개 포함) ✅ 좋은 가성비
HTML/CSS:       $0   (무제한) ✅ 완전 무료
```

---

## 🔧 통합 난이도

```
쉬움 → 어려움

Canva API ━━━━━━━━━━━━━━━━━━━━ (가장 쉬움)
Placid ━━━━━━━━━━━━━━━━━━━━━━━
Bannerbear ━━━━━━━━━━━━━━━━━━━━━━━━
Abyssale ━━━━━━━━━━━━━━━━━━━━━━━━━━
Shotstack ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Puppeteer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ (가장 어려움)
```

---

## 📌 최종 추천

### 🥇 1순위: **Placid.app**
- 가성비 최고 ($49/월, 10,000개)
- Bannerbear보다 기능 많음
- 한글 완벽 지원

### 🥈 2순위: **Canva API**
- 품질 최고
- 가장 쉬움
- 비용 감당 가능하다면 최고 선택

### 🥉 3순위: **현재 시스템 개선 (무료)**
- 이미 작동 중
- HTML/CSS 템플릿만 개선
- 완전 무료

---

## 🚀 다음 단계

1. **Placid 무료 체험** 해보기 (14일)
2. 템플릿 하나 만들어서 테스트
3. 결과 비교 후 결정

**무료 체험 링크:**
- Placid: https://placid.app/pricing
- Canva: https://www.canva.com/developers/
- Shotstack: https://shotstack.io/

원하시는 API 있으면 통합 코드 작성해드릴게요! 🎨
