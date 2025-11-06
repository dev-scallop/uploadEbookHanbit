"""
참조 이미지로부터 HTML 템플릿을 자동 생성하는 모듈
 - OpenAI 멀티모달(비전) 모델을 사용해 레이아웃 분석 후 Jinja 템플릿(Inline CSS) 생성
 - 결과 템플릿은 templates/ai_generated/ 아래에 저장되고, 렌더러에서 template_name으로 사용 가능
"""
from __future__ import annotations

from typing import Optional, Dict
from pathlib import Path
import base64
import json
import logging
import datetime

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


class AutoTemplateGenerator:
    """참조 이미지 기반 AI 템플릿 생성기"""

    def __init__(self, api_key: str | None = None, templates_root: Path | None = None) -> None:
        self.api_key = api_key or config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.templates_root = templates_root or (config.TEMPLATES_DIR / 'ai_generated')
        self.templates_root.mkdir(parents=True, exist_ok=True)
        if not self.client:
            logger.warning("OpenAI API 키가 없어 AI 템플릿 자동 생성이 비활성화됩니다.")

    def _image_to_data_url(self, path: Path) -> str:
        mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        return f"data:{mime};base64,{b64}"

    def generate_from_reference(
        self,
        reference_image: str,
        template_basename: Optional[str] = None,
    ) -> Optional[str]:
        """
        참조 이미지를 분석해 유사한 HTML(Jinja) 템플릿을 생성합니다.

        Args:
            reference_image: 로컬 경로 또는 URL(https/http/data URL)
            template_basename: 저장할 템플릿 기본 파일명(확장자 제외)

        Returns:
            템플릿 로더 기준의 상대 경로 (예: 'ai_generated/ai_20251029_120000.html') 또는 None
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None

        # 이미지 입력 준비
        image_url: str
        ref_path = Path(reference_image)
        if reference_image.startswith('http://') or reference_image.startswith('https://') or reference_image.startswith('data:'):
            image_url = reference_image
        elif ref_path.exists():
            image_url = self._image_to_data_url(ref_path)
        else:
            logger.error(f"참조 이미지를 찾을 수 없습니다: {reference_image}")
            return None

        # 파일명 구성
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        name = template_basename or f"ai_{ts}"
        filename = f"{name}.html"
        out_path = self.templates_root / filename

        # 시스템/사용자 프롬프트 구성
        system_prompt = (
            "당신은 시니어 프론트엔드/퍼블리셔입니다. 주어진 참조 이미지를 보고 유사한 레이아웃의 단일 HTML 템플릿을 생성합니다.\n"
            "- 출력은 하나의 완전한 HTML 문서여야 합니다.\n"
            "- <style> 내에 CSS를 인라인으로 포함하세요 (외부 CSS 불필요).\n"
            "- 폰트는 한국어 가독성을 위해 'Pretendard', 'Noto Sans KR', system-ui를 우선 지정하세요.\n"
            "- 색상은 스타일 변수에 연동되도록 Jinja 변수를 사용하세요. 예: {{ style.primary_color }} 등.\n"
            "- 텍스트/이미지 콘텐츠에는 다음 Jinja 변수를 사용하세요: \n"
            "  {{ book.title }}, {{ book.author }}, {{ book.generated_intro }}, {{ book.generated_marketing_copy }}, {{ book.keywords }}, {{ book.cover_image_url }}.\n"
            "- 키워드는 ' · '로 join 해서 표시하거나, 최대 5개만 출력하세요.\n"
            "- 레이아웃은 Hero(제목/부제) + 커버 이미지 + 2~3개의 섹션(제목/본문) 구성으로 간결하게 만드세요.\n"
            "- 전체 폭 1000~1200px 기준, 여백과 라인하이트를 넉넉하게 설정하세요.\n"
            "- 접근성(대비, 폰트 크기)을 고려하세요.\n"
        )

        user_instruction = (
            "아래 참조 이미지를 분석하여 비슷한 구조와 분위기의 HTML 템플릿을 만들어 주세요.\n"
            "출력은 반드시 코드만 포함한 순수 HTML이어야 합니다. 불필요한 설명 텍스트를 넣지 마세요.\n"
        )

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_instruction},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    },
                ],
                temperature=0.6,
                max_tokens=2000,
            )

            html = resp.choices[0].message.content or ""
            html = html.strip()

            # 가끔 모델이 코드펜스 등을 넣는 경우 제거
            if html.startswith("```"):
                # ```html 또는 ``` 제거
                html = html.strip('`')
                # 첫 줄에 html 표기가 있을 수 있음
                if html.lower().startswith('html'):
                    html = html[4:]
                html = html.strip()

            out_path.write_text(html, encoding='utf-8')
            rel_path = out_path.relative_to(config.TEMPLATES_DIR).as_posix()
            logger.info(f"AI 템플릿 생성 완료: {out_path}")
            return rel_path

        except Exception as e:
            logger.error(f"AI 템플릿 생성 실패: {e}")
            return None
