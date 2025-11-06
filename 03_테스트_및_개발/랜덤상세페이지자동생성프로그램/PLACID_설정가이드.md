# Placid.app 설정 가이드

## 1. 계정 생성 및 API 토큰

### 1-1. 계정 생성
1. https://placid.app 접속
2. **"Start Free Trial"** 클릭 (14일 무료 체험)
3. 이메일로 가입

### 1-2. API 토큰 발급
1. 로그인 후 https://placid.app/settings/api 접속
2. **"API Tokens"** 섹션에서 **"Create Token"** 클릭
3. 토큰 이름 입력: "Book Page Generator"
4. **복사한 토큰을 `.env` 파일에 추가:**

```properties
PLACID_API_TOKEN=plcd_xxx실제_토큰_여기에
```

---

## 2. 템플릿 생성

### 2-1. 새 템플릿 만들기
1. https://placid.app/templates 접속
2. **"Create Template"** 클릭
3. 템플릿 이름: **"Book Detail Page - Korean"**
4. 캔버스 크기:
   - Width: **1000px**
   - Height: **1500px**

### 2-2. 레이어 추가

Placid 에디터에서 다음 레이어들을 추가하세요:

#### 배경 레이어
- **이름:** `background`
- **타입:** Rectangle
- 크기: 1000 × 1500
- 색상: `#F8F9FA`

#### 제목 레이어
- **이름:** `book_title`
- **타입:** Text
- 폰트: **Noto Sans KR Bold**
- 크기: **56px**
- 위치: (50, 100)
- 색상: `#2C3E50`
- 샘플 텍스트: "책 제목"

#### 헤더 부제목
- **이름:** `header_subtitle`
- **타입:** Text
- 폰트: **Noto Sans KR Regular**
- 크기: **28px**
- 위치: (50, 50)
- 색상: `#6C757D`
- 샘플 텍스트: "이론과 실습을 통해 배우는"

#### 책 표지 이미지
- **이름:** `book_cover_image`
- **타입:** Image
- 크기: 400 × 600
- 위치: (300, 220)
- Border Radius: 10px
- Shadow: Medium

#### 섹션 1 제목
- **이름:** `section1_title`
- **타입:** Text
- 폰트: **Noto Sans KR Bold**
- 크기: **32px**
- 위치: (50, 850)
- 색상: `#2C3E50`

#### 섹션 1 내용
- **이름:** `section1_content`
- **타입:** Text
- 폰트: **Noto Sans KR Regular**
- 크기: **18px**
- 위치: (50, 900)
- 색상: `#495057`
- Max Width: 900px

#### 섹션 2 제목
- **이름:** `section2_title`
- **타입:** Text
- 폰트: **Noto Sans KR Bold**
- 크기: **32px**
- 위치: (50, 1100)

#### 섹션 2 내용
- **이름:** `section2_content`
- **타입:** Text
- 폰트: **Noto Sans KR Regular**
- 크기: **18px**
- 위치: (50, 1150)

#### 저자명
- **이름:** `author_name`
- **타입:** Text
- 폰트: **Noto Sans KR Medium**
- 크기: **20px**
- 위치: (50, 1450)
- 색상: `#FFFFFF`
- Background: `#2C3E50`

---

## 3. 템플릿 ID 확인

1. 템플릿 저장 후 **"Settings"** 탭 클릭
2. **Template ID** 복사 (예: `xyzabc123`)
3. `.env` 파일에 추가:

```properties
PLACID_TEMPLATE_ID=xyzabc123
```

---

## 4. 템플릿 테스트

### 4-1. Placid 대시보드에서 테스트
1. 템플릿 페이지에서 **"Test"** 버튼 클릭
2. 각 레이어에 샘플 데이터 입력:
   ```json
   {
     "book_title": "파이썬 프로그래밍 입문",
     "author_name": "저자: 홍길동",
     "section1_content": "초보자를 위한 완벽 가이드"
   }
   ```
3. **"Generate Image"** 클릭
4. 결과 확인

### 4-2. Python 코드로 테스트
```bash
python check_placid_template.py
```

실제 데이터로 테스트:
```bash
python main.py --source sheets --count 1 --use-placid
```

---

## 5. 사용 방법

### 기본 사용
```bash
# Placid로 1개 생성
python main.py --source sheets --count 1 --use-placid

# Placid로 5개 생성 (랜덤 색상 적용)
python main.py --source sheets --count 5 --use-placid

# 테스트 데이터로 생성
python main.py --source test --count 1 --use-placid
```

### 옵션 비교
```bash
# HTML 템플릿 (무료)
python main.py --source sheets --count 1

# Bannerbear ($29/월)
python main.py --source sheets --count 1 --use-bannerbear

# Placid ($49/월, 추천!)
python main.py --source sheets --count 1 --use-placid
```

---

## 6. 장점

### Bannerbear 대비 장점:
- ✅ **더 저렴**: $49/월 (10,000개) vs $29/월 (300개)
- ✅ **무제한 템플릿** 생성 가능
- ✅ **더 빠른 렌더링** (1-2초)
- ✅ **비디오 생성** 기능 (추가 비용 없음)
- ✅ **더 많은 통합** (Zapier, Make.com 등)
- ✅ **QR 코드** 자동 생성
- ✅ **더 나은 문서**

---

## 7. 가격 플랜

```
Free Trial: 14일 무료
- 모든 기능 사용 가능
- 50개 이미지 생성

Starter: $49/월
- 10,000 이미지/월
- 무제한 템플릿
- REST API
- 비디오 생성 (30초)

Pro: $99/월
- 30,000 이미지/월
- 우선 지원
- 비디오 생성 (60초)
- 팀 협업

Enterprise: 맞춤 가격
- 무제한 이미지
- 전담 지원
- SLA 보장
```

---

## 8. 문제 해결

### "Invalid token" 에러
→ `.env` 파일의 `PLACID_API_TOKEN` 확인

### "Template not found" 에러
→ `.env` 파일의 `PLACID_TEMPLATE_ID` 확인

### 한글이 깨짐
→ 템플릿에서 **Noto Sans KR** 폰트 사용

### 이미지가 생성 안됨
→ `check_placid_template.py`로 템플릿 구조 확인

---

## 9. 추가 기능

### 9-1. 동적 QR 코드
```python
layers = {
    "qr_code": {
        "qr_code": "https://example.com/book/123"
    }
}
```

### 9-2. 비디오 생성
Placid는 **정적 이미지뿐만 아니라 비디오**도 생성 가능:
- 책 소개 영상 자동 생성
- 추가 비용 없음
- 템플릿 한 번만 수정

---

## 10. 다음 단계

1. ✅ 계정 생성 및 API 토큰 발급
2. ✅ Python 코드 통합 완료
3. ⬜ Placid에서 템플릿 생성
4. ⬜ 템플릿 ID를 `.env`에 추가
5. ⬜ 테스트 실행: `python main.py --source sheets --count 1 --use-placid`

---

## 📚 참고 자료

- Placid 공식 문서: https://placid.app/docs
- API 레퍼런스: https://placid.app/docs/2.0/rest/introduction
- 템플릿 갤러리: https://placid.app/templates
- 무료 체험: https://placid.app/pricing

**템플릿 만드실 때 도움 필요하시면 언제든 말씀해주세요!** 🚀
