import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests
import re
from openai import OpenAI


STATE_PATH = Path("state.json")
DEFAULT_INTERVAL = 60

WATCH_SPREADSHEET_ID = os.getenv("WATCH_SPREADSHEET_ID", "1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c")
WATCH_SHEET_NAME = os.getenv("WATCH_SHEET_NAME", "시트1")
TARGET_SPREADSHEET_ID = os.getenv("TARGET_SPREADSHEET_ID", WATCH_SPREADSHEET_ID)
TARGET_SHEET_NAME = os.getenv("TARGET_SHEET_NAME", "도서정리")


@dataclass
class Config:
    openai_api_key: str
    hcti_user_id: str
    hcti_api_key: str
    poll_interval: int = DEFAULT_INTERVAL



PROMPT_BODY = """너는 브랜드 마케팅 전문가다.
아래 신간안내서 원문에서 도서 정보를 추출하고, 독자가 바로 관심을 갖고 구매하고 싶게 만드는 매력적인 마케팅 콘텐츠를 생성해라.

## 브랜드 마케팅 전략
1. **타깃 독자 맞춤화**: 기획서 내용을 분석하여 대상 독자(교사, 학생, 일반인, 전문가 등)를 정확히 파악하고, 그들의 언어로 메시지를 전달해라.
2. **USP 강조**: 이 책만의 차별화된 강점(Unique Selling Proposition)을 명확히 드러내라.
3. **광고 카피 작성법**: 
   - 짧은 헤드라인으로 임팩트를 주고
   - 2-3줄의 설명으로 흥미를 유발하며
   - 핵심 특징 리스트로 구체적 가치를 제시해라

## 세부 가이드라인

### 1. promo_line (짧은 헤드라인)
**목적**: 3초 안에 시선을 사로잡는 강렬한 한 문장
**길이**: 15-25자
**작성법**:
- 독자의 감정을 건드리는 파워 워드 사용 ("혁신", "필수", "완벽한", "최고의" 등)
- 숫자나 구체적 표현 활용 ("단 7일", "500개 예제", "1위" 등)
- 의문문이나 단정문으로 강렬하게 마무리
**예시**:
- "STEM 교육의 새로운 기준"
- "7일 만에 정복하는 파이썬"
- "교사들이 가장 많이 선택한 교재"

### 2. intro_summary (2-3줄 설명)
**목적**: 흥미를 유발하고 계속 읽고 싶게 만들기
**길이**: 80-120자 (2-3문장)
**작성법**:
- 1문장: 독자의 고민이나 니즈 언급 ("~하고 싶으신가요?", "~이 어려우신가요?")
- 2문장: 이 책의 솔루션과 차별점 제시
- 3문장: 기대 효과나 변화 약속
**예시**:
- "경제학이 어렵게만 느껴지셨나요? 이 책은 실제 뉴스와 사례로 복잡한 개념을 쉽게 풀어냅니다. 읽고 나면 경제 뉴스가 저절로 이해됩니다."

### 3. recommendation (대상 독자별 맞춤 메시지)
**목적**: "이 책은 바로 나를 위한 책이다"라는 확신을 주기
**길이**: 각 40-60자
**작성법**:
- 독자 유형별로 구체적 상황 묘사
- "~하는 분", "~을 원하는 분", "~에 고민하는 분" 패턴 활용
- 책이 제공하는 구체적 해결책과 혜택 명시
**예시**:
- recommendation_1 (초보자): "처음 배우는 분도 따라하기 쉽게 단계별로 구성했습니다"
- recommendation_2 (실무자): "현장에서 바로 적용 가능한 200개 실전 예제를 담았습니다"
- recommendation_3 (교육자): "학생들이 흥미를 갖고 참여하는 수업 자료가 필요하다면 최적입니다"

### 4. feature (핵심 특징 리스트)
**목적**: 구체적 가치를 한눈에 보여주기
**구성**:
- title (10자 이내): 핵심 키워드, 카테고리화된 제목
- desc (50-80자): 그 특징이 주는 실질적 혜택 강조
**작성법**:
- title: 명사형으로 임팩트 있게 ("실전 예제", "단계별 학습", "풍부한 자료")
- desc: 독자가 얻을 수 있는 구체적 결과 중심 ("~할 수 있습니다", "~를 제공합니다")
**예시**:
- title: "실무 예제", desc: "업계 전문가가 검증한 200개 예제로 실무 감각을 키울 수 있습니다"
- title: "동영상 강의", desc: "QR코드로 바로 연결되는 50개 무료 강의로 이해를 돕습니다"

### 5. publisher_review (출판사 관점)
**목적**: 전문성과 신뢰도 부여
**길이**: 100-150자
**작성법**:
- 기획 의도와 시장 분석 언급
- 타깃 독자층 명확히 정의
- 경쟁 도서 대비 차별점 강조
**예시**:
- "현장 교사들의 목소리를 담아 기획했습니다. 이론과 실습이 균형잡힌 구성으로 대학 교재는 물론 독학용으로도 완벽합니다."

## 작성 원칙
✅ **DO (해야 할 것)**:
- 구체적 숫자와 데이터 활용 ("200개 예제", "50개 동영상")
- 독자의 감정과 니즈에 공감하는 표현
- 액션을 유도하는 능동적 문장 ("~할 수 있습니다", "~를 경험하세요")
- 짧고 강렬한 문장, 리듬감 있는 표현
- 차별화 포인트 명확히 부각

❌ **DON'T (하지 말아야 할 것)**:
- 과도한 수식어와 미사여구 ("매우", "정말", "엄청" 남발)
- 추상적이고 애매한 표현 ("좋은 책", "유익한 내용")
- 긴 문장, 복잡한 구조
- 전문 용어 과다 사용
- 다른 책과 비슷한 평범한 문구

## JSON 출력 규칙
- 불확실한 값은 null
- title에 "2판", "3판", "개정판" 등이 포함되면 changed_section에 개정 포인트 3가지 작성 (각 30-50자)
- 그 외에는 changed_section을 null로 설정
- 모든 문구는 광고 카피처럼 매력적이고 설득력 있게 작성

아래 구조로 JSON만 반환 (코드블록 마커 없이, minified 형태):

{
  "title": "",
  "authors": "",
  "publish_date": "",
  "price": 0,
  "category": "",
  "keywords": [],
  "difficulty": "",
  "isbn": "",
  "pages": "",
  "book_size": "",
  "intro_summary": "",
  "publisher_review": "",
  "authors_bio": "",
  "toc_highlight": "",
  "promo_line": "",
  "bookstore_position": "",
  "cover_image_url": null,
  "ai_confidence": 95,
  "recommendation_1": "",
  "recommendation_2": "",
  "recommendation_3": "",
  "feature_1_title": "",
  "feature_1_desc": "",
  "feature_2_title": "",
  "feature_2_desc": "",
  "feature_3_title": "",
  "feature_3_desc": "",
  "feature_4_title": "",
  "feature_4_desc": "",
  "update_1": "",
  "update_2": "",
  "update_3": "",
  "changed_section": {
    "update_1": "",
    "update_2": "",
    "update_3": ""
  }
}

신간안내서 원문:
"""

HTML_TEMPLATE = Template("""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.container {
  max-width: 900px;
  width: 100%;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
}

.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 40px;
  text-align: center;
  color: #ffffff;
  position: relative;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120"><path fill="%23ffffff" fill-opacity="0.1" d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" opacity=".25"/><path fill="%23ffffff" fill-opacity="0.1" d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z" opacity=".5"/><path fill="%23ffffff" fill-opacity="0.1" d="M0,0V5.63C149.93,59,314.09,71.32,475.83,42.57c43-7.64,84.23-20.12,127.61-26.46,59-8.63,112.48,12.24,165.56,35.4C827.93,77.22,886,95.24,951.2,90c86.53-7,172.46-45.71,248.8-84.81V0Z"/></svg>') center bottom / cover no-repeat;
}

.promo-badge {
  display: inline-block;
  background: rgba(255,255,255,0.25);
  backdrop-filter: blur(10px);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 20px;
  letter-spacing: 0.5px;
}

.book-title {
  font-size: 36px;
  font-weight: 900;
  line-height: 1.3;
  margin-bottom: 16px;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.book-intro {
  font-size: 16px;
  line-height: 1.6;
  opacity: 0.95;
  max-width: 600px;
  margin: 0 auto 30px;
}

.cover-wrapper {
  display: inline-block;
  padding: 8px;
  background: rgba(255,255,255,0.15);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.cover-image {
  width: 220px;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
  display: block;
}

.content {
  padding: 50px 40px;
}

.section {
  margin-bottom: 50px;
}

.section-header {
  text-align: center;
  margin-bottom: 30px;
}

.section-badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a1a;
}

.recommendation-list {
  list-style: none;
  display: grid;
  gap: 16px;
}

.recommendation-item {
  background: #f8f9ff;
  padding: 20px 24px 20px 48px;
  border-radius: 12px;
  border-left: 4px solid #667eea;
  font-size: 15px;
  line-height: 1.7;
  color: #333;
  position: relative;
}

.recommendation-item::before {
  content: '✓';
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.feature-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 30px;
  border-radius: 16px;
  position: relative;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}

.feature-number {
  position: absolute;
  top: -12px;
  left: 20px;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 16px;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
}

.feature-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 12px;
  padding-top: 8px;
}

.feature-desc {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
}

.footer {
  text-align: center;
  padding: 40px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
}

.publisher-logo {
  width: 160px;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.publisher-logo:hover {
  opacity: 1;
}

@media (max-width: 768px) {
  .hero {
    padding: 40px 24px;
  }
  
  .book-title {
    font-size: 28px;
  }
  
  .content {
    padding: 40px 24px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .cover-image {
    width: 180px;
  }
}
</style>
</head>
<body>
<div class="container">
  <section class="hero">
    <div class="promo-badge">$promo_line</div>
    <h1 class="book-title">$title</h1>
    <p class="book-intro">$intro_summary</p>
    <div class="cover-wrapper">
      <img class="cover-image" src="$cover_image_url" alt="$title 표지">
    </div>
  </section>

  <div class="content">
    <section class="section">
      <div class="section-header">
        <span class="section-badge">WHO IS THIS FOR?</span>
        <h2 class="section-title">이런 분들께 추천합니다</h2>
      </div>
      <ul class="recommendation-list">
        <li class="recommendation-item">$recommendation_1</li>
        <li class="recommendation-item">$recommendation_2</li>
        <li class="recommendation-item">$recommendation_3</li>
      </ul>
    </section>

    <section class="section">
      <div class="section-header">
        <span class="section-badge">KEY FEATURES</span>
        <h2 class="section-title">이 책의 핵심 특징</h2>
      </div>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-number">01</div>
          <h3 class="feature-title">$feature_1_title</h3>
          <p class="feature-desc">$feature_1_desc</p>
        </div>
        <div class="feature-card">
          <div class="feature-number">02</div>
          <h3 class="feature-title">$feature_2_title</h3>
          <p class="feature-desc">$feature_2_desc</p>
        </div>
        <div class="feature-card">
          <div class="feature-number">03</div>
          <h3 class="feature-title">$feature_3_title</h3>
          <p class="feature-desc">$feature_3_desc</p>
        </div>
        <div class="feature-card">
          <div class="feature-number">04</div>
          <h3 class="feature-title">$feature_4_title</h3>
          <p class="feature-desc">$feature_4_desc</p>
        </div>
      </div>
    </section>
  </div>

  <footer class="footer">
    <img class="publisher-logo" src="https://www.hanbit.co.kr/images/brand/brand_logo_academy.gif" alt="한빛아카데미">
  </footer>
</div>
</body>
</html>
""")


def load_state() -> int:
    if not STATE_PATH.exists():
        return 1
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return int(data.get("last_processed_row", 1))
    except (json.JSONDecodeError, ValueError):
        return 1


def save_state(row_number: int) -> None:
    payload = {"last_processed_row": row_number}
    STATE_PATH.write_text(json.dumps(payload), encoding="utf-8")


def load_config(poll_interval: int) -> Config:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    hcti_user_id = os.getenv("HCTI_USER_ID")
    hcti_api_key = os.getenv("HCTI_API_KEY")

    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is missing")
    if not hcti_user_id or not hcti_api_key:
        raise RuntimeError("HCTI_USER_ID and HCTI_API_KEY environment variables are required")

    return Config(
        openai_api_key=openai_api_key,
        hcti_user_id=hcti_user_id,
        hcti_api_key=hcti_api_key,
        poll_interval=poll_interval,
    )


def column_index_to_letter(index: int) -> str:
    letters = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def fetch_rows(spreadsheet_id: str, sheet_name: str) -> List[List[str]]:
    """
    공개 스프레드시트에서 A2:Z 범위 행들을 읽어옵니다.
    CSV export를 사용해 더 안정적으로 데이터를 가져옵니다.
    """
    # Google Sheets CSV export URL (gid는 시트 ID, 기본값 0)
    # 시트명으로 직접 접근이 안되므로 gid를 얻거나 첫 시트(gid=0) 사용
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # CSV 파싱
        import csv
        from io import StringIO
        
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        
        # 헤더 스킵 (1행)
        next(reader, None)
        
        rows = []
        for row in reader:
            # 최대 26개 컬럼(A-Z)만 읽기, 부족하면 빈 문자열로 채움
            padded_row = (row + [""] * 26)[:26]
            rows.append(padded_row)
        
        return rows
    except Exception as exc:
        raise RuntimeError(f"Failed to read rows from public sheet: {exc}") from exc


def iter_new_rows(rows: List[List[str]], start_row_number: int) -> Iterable[Tuple[int, List[str]]]:
    for idx, row in enumerate(rows, start=2):
        if idx <= start_row_number:
            continue
        yield idx, row


def build_prompt(source_text: str) -> str:
    return f'"prompt": "{PROMPT_BODY}신간안내서 원문:\n{source_text.strip()}"'


def call_openai(client: OpenAI, prompt: str) -> Dict[str, Any]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        top_p=1,
        max_tokens=2048,
        n=1,
    )
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Model response is not valid JSON") from exc


def ensure_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "title": "",
        "authors": "",
        "publish_date": "",
        "price": 0,
        "category": "",
        "keywords": [],
        "difficulty": "",
        "isbn": "",
        "pages": "",
        "book_size": "",
        "intro_summary": "",
        "publisher_review": "",
        "authors_bio": "",
        "toc_highlight": "",
        "promo_line": "",
        "bookstore_position": "",
        "cover_image_url": None,
        "ai_confidence": 95,
        "recommendation_1": "",
        "recommendation_2": "",
        "recommendation_3": "",
        "feature_1_title": "",
        "feature_1_desc": "",
        "feature_2_title": "",
        "feature_2_desc": "",
        "feature_3_title": "",
        "feature_3_desc": "",
        "feature_4_title": "",
        "feature_4_desc": "",
        "update_1": "",
        "update_2": "",
        "update_3": "",
        "changed_section": None,
    }
    result = defaults.copy()
    result.update(payload)
    if result["keywords"] is None:
        result["keywords"] = []
    if result.get("changed_section") in (None, "null"):
        result["changed_section"] = {"update_1": "", "update_2": "", "update_3": ""}
    else:
        changed = result["changed_section"]
        result["changed_section"] = {
            "update_1": changed.get("update_1", ""),
            "update_2": changed.get("update_2", ""),
            "update_3": changed.get("update_3", ""),
        }
    return result


def stringify(value: Optional[Any]) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def build_row_values(data: Dict[str, Any], source_row_id: int) -> List[str]:
    changed = data.get("changed_section", {}) or {"update_1": "", "update_2": "", "update_3": ""}
    values = [
        stringify(data.get("title")),
        stringify(data.get("authors")),
        stringify(data.get("publish_date")),
        stringify(data.get("price")),
        stringify(data.get("category")),
        stringify(data.get("keywords")),
        stringify(data.get("difficulty")),
        stringify(data.get("isbn")),
        stringify(data.get("pages")),
        stringify(data.get("book_size")),
        stringify(data.get("intro_summary")),
        stringify(data.get("publisher_review")),
        stringify(data.get("authors_bio")),
        stringify(data.get("toc_highlight")),
        stringify(data.get("promo_line")),
        stringify(data.get("bookstore_position")),
        stringify(data.get("cover_image_url")),
        stringify(data.get("ai_confidence")),
        stringify(data.get("recommendation_1")),
        stringify(data.get("recommendation_2")),
        stringify(data.get("recommendation_3")),
        stringify(data.get("feature_1_title")),
        stringify(data.get("feature_1_desc")),
        stringify(data.get("feature_2_title")),
        stringify(data.get("feature_2_desc")),
        stringify(data.get("feature_3_title")),
        stringify(data.get("feature_3_desc")),
        stringify(data.get("feature_4_title")),
        stringify(data.get("feature_4_desc")),
        stringify(data.get("update_1")),
        stringify(data.get("update_2")),
        stringify(data.get("update_3")),
        stringify(changed.get("update_1")),
        stringify(changed.get("update_2")),
        stringify(changed.get("update_3")),
        "",
        "",
        stringify(source_row_id),
    ]
    return values


def append_row(spreadsheet_id: str, sheet_name: str, values: List[str]) -> int:
    """
    공개 스프레드시트에 행을 추가합니다.
    참고: 공개 시트는 HTTP로 직접 append가 불가능하므로, 
    사용자가 미리 빈 행을 준비해두고 Apps Script 웹앱 URL을 제공해야 합니다.
    """
    # Apps Script 웹앱 엔드포인트 (환경변수로 설정)
    web_app_url = os.getenv("SHEETS_WEB_APP_URL")
    if not web_app_url:
        raise RuntimeError(
            "공개 시트에 쓰기 위해서는 SHEETS_WEB_APP_URL 환경변수가 필요합니다.\n"
            "Google Apps Script로 웹앱을 만들고 URL을 설정하세요."
        )
    
    payload = {
        "spreadsheetId": spreadsheet_id,
        "sheetName": sheet_name,
        "values": values
    }
    try:
        response = requests.post(web_app_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        row_number = result.get("rowNumber")
        if not row_number:
            raise RuntimeError(f"Web app did not return rowNumber: {result}")
        return row_number
    except Exception as exc:
        raise RuntimeError(f"Failed to append row via web app: {exc}") from exc


def generate_html(data: Dict[str, Any]) -> str:
    html_data = {key: stringify(value) for key, value in data.items()}
    
    # 빈 값을 기본값으로 대체
    defaults = {
        "title": "제목 없음",
        "intro_summary": "책 소개 내용이 없습니다.",
        "promo_line": "신간 도서",
        "cover_image_url": "https://via.placeholder.com/240x360?text=No+Image",
        "recommendation_1": "이 책을 추천합니다.",
        "recommendation_2": "유용한 내용이 담겨 있습니다.",
        "recommendation_3": "학습에 도움이 됩니다.",
        "feature_1_title": "특징 1",
        "feature_1_desc": "책의 특징을 설명합니다.",
        "feature_2_title": "특징 2",
        "feature_2_desc": "책의 특징을 설명합니다.",
        "feature_3_title": "특징 3",
        "feature_3_desc": "책의 특징을 설명합니다.",
        "feature_4_title": "특징 4",
        "feature_4_desc": "책의 특징을 설명합니다.",
    }
    
    # 빈 값이면 기본값 사용
    for key, default_value in defaults.items():
        value = html_data.get(key, "")
        if not value or (isinstance(value, str) and value.strip() == ""):
            html_data[key] = default_value
    
    return HTML_TEMPLATE.substitute(html_data)


def render_image(html: str, config: Config) -> str:
    payload = {
        "html": html,
        "google_fonts": "Noto+Sans+KR",
        "device_scale": 2,
        "viewport_width": 700,
        "viewport_height": 1800,
        "ms_delay": 1000,
        "full_screen": True,
    }
    response = requests.post(
        "https://hcti.io/v1/image",
        data=payload,
        auth=(config.hcti_user_id, config.hcti_api_key),
        timeout=120,
    )
    if response.status_code != 200:
        raise RuntimeError(f"HTML to image service failed: {response.text}")
    data = response.json()
    url = data.get("url")
    if not url:
        raise RuntimeError("HTML to image response missing URL")
    return url


def update_image_metadata(spreadsheet_id: str, sheet_name: str, row_number: int, image_url: str) -> None:
    """공개 시트의 AJ/AK 열에 이미지 URL과 타임스탬프를 기록합니다."""
    timestamp = datetime.now(timezone.utc).isoformat()
    web_app_url = os.getenv("SHEETS_WEB_APP_URL")
    if not web_app_url:
        logging.warning("SHEETS_WEB_APP_URL 없음, 이미지 메타데이터 업데이트 건너뜀")
        return
    
    payload = {
        "action": "updateMetadata",
        "spreadsheetId": spreadsheet_id,
        "sheetName": sheet_name,
        "rowNumber": row_number,
        "imageUrl": image_url,
        "timestamp": timestamp
    }
    try:
        response = requests.post(web_app_url, json=payload, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Failed to update image metadata via web app: {exc}") from exc


def process_row(
    client: OpenAI,
    config: Config,
    row_number: int,
    row_values: List[str],
    on_artifacts: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> int:
    if not row_values:
        raise RuntimeError("Empty row data")
    source_text = row_values[0]
    prompt = build_prompt(source_text)
    logging.info("Asking OpenAI to enrich row %s", row_number)
    response = call_openai(client, prompt)
    data = ensure_fields(response)
    enriched_row = build_row_values(data, source_row_id=row_number)
    appended_row = append_row(TARGET_SPREADSHEET_ID, TARGET_SHEET_NAME, enriched_row)
    html = generate_html(data)
    image_url = render_image(html, config)
    update_image_metadata(TARGET_SPREADSHEET_ID, TARGET_SHEET_NAME, appended_row, image_url)
    if on_artifacts is not None:
        try:
            on_artifacts(
                {
                    "html": html,
                    "image_url": image_url,
                    "data": data,
                    "target_row": appended_row,
                    "source_row": row_number,
                }
            )
        except Exception as cb_exc:  # noqa: BLE001
            logging.exception("on_artifacts callback failed: %s", cb_exc)
    logging.info("Processed source row %s into target row %s", row_number, appended_row)
    return row_number


def run_once(client: OpenAI, config: Config) -> Optional[int]:
    rows = fetch_rows(WATCH_SPREADSHEET_ID, WATCH_SHEET_NAME)
    last_processed = load_state()
    processed_any = None
    for row_number, row_values in iter_new_rows(rows, last_processed):
        try:
            processed_any = process_row(client, config, row_number, row_values)
            save_state(row_number)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to process row %s: %s", row_number, exc)
    return processed_any


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Google Sheets + OpenAI automation pipeline")
    parser.add_argument("--loop", action="store_true", help="Continuously poll for new rows")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Polling interval in seconds")
    args = parser.parse_args()

    config = load_config(poll_interval=args.interval)
    client = OpenAI(api_key=config.openai_api_key)

    if args.loop:
        while True:
            processed = run_once(client, config)
            if processed is None:
                logging.info("No new rows found; sleeping %s seconds", config.poll_interval)
            time.sleep(config.poll_interval)
    else:
        processed = run_once(client, config)
        if processed is None:
            logging.info("No new rows found")


if __name__ == "__main__":
    main()
