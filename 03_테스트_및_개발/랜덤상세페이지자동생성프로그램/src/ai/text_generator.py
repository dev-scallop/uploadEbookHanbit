"""
OpenAI API를 사용한 텍스트 생성 모듈
"""
from openai import OpenAI
from typing import List, Optional
import logging

import config

logger = logging.getLogger(__name__)


class TextGenerator:
    """OpenAI API를 사용하여 텍스트를 생성하는 클래스"""
    
    def __init__(self, api_key: str = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        
        if not self.api_key:
            logger.warning("OpenAI API 키가 설정되지 않았습니다.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI 클라이언트 초기화 완료")
    
    def _get_tone_instruction(self, tone: str) -> str:
        """
        톤에 따른 지시사항 반환
        
        Args:
            tone: 텍스트 톤 (formal, marketing, emotional)
            
        Returns:
            지시사항 문자열
        """
        tone_instructions = {
            'formal': '격식있고 전문적인 톤으로 작성해주세요. 객관적이고 신뢰감 있는 표현을 사용하세요.',
            'marketing': '마케팅 톤으로 흥미롭고 매력적으로 작성해주세요. 독자의 관심을 끌고 구매 욕구를 자극하세요.',
            'emotional': '감성적이고 공감을 이끌어내는 톤으로 작성해주세요. 독자의 감정에 호소하는 표현을 사용하세요.',
        }
        return tone_instructions.get(tone, tone_instructions['formal'])
    
    def generate_book_intro(
        self,
        title: str,
        author: str,
        description: str = "",
        keywords: List[str] = None,
        tone: str = 'formal',
        max_tokens: int = None
    ) -> Optional[str]:
        """
        책 소개 텍스트 생성
        
        Args:
            title: 책 제목
            author: 저자명
            description: 기존 설명 (참고용)
            keywords: 키워드 리스트
            tone: 텍스트 톤
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 책 소개 텍스트
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 프롬프트 작성
            tone_instruction = self._get_tone_instruction(tone)
            keywords_str = ', '.join(keywords) if keywords else ''
            
            prompt = f"""다음 도서에 대한 간단하고 핵심적인 책 소개를 작성해주세요.

제목: {title}
저자: {author}
키워드: {keywords_str}

{f"기존 설명: {description}" if description else ""}

요구사항:
- {tone_instruction}
- **1-2문장으로 간결하게** (최대 100자)
- 책의 핵심 내용만 명확히 전달
- 불필요한 수식어 제거
- 한국어로 작성
"""
            
            # API 호출
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문 북 에디터입니다. 독자의 관심을 끌고 책의 가치를 효과적으로 전달하는 책 소개를 작성합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or config.AI_SETTINGS['max_tokens'],
                temperature=config.AI_SETTINGS['temperature'],
            )
            
            intro = response.choices[0].message.content.strip()
            logger.info(f"책 소개 생성 완료: {title}")
            return intro
            
        except Exception as e:
            logger.error(f"책 소개 생성 실패: {e}")
            return None
    
    def generate_marketing_copy(
        self,
        title: str,
        author: str,
        description: str = "",
        keywords: List[str] = None,
        tone: str = 'marketing',
        max_tokens: int = None
    ) -> Optional[str]:
        """
        마케팅 카피 생성
        
        Args:
            title: 책 제목
            author: 저자명
            description: 기존 설명
            keywords: 키워드 리스트
            tone: 텍스트 톤
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 마케팅 카피
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            keywords_str = ', '.join(keywords) if keywords else ''
            
            prompt = f"""다음 도서에 대한 짧고 강력한 마케팅 카피를 작성해주세요.

제목: {title}
저자: {author}
키워드: {keywords_str}
{f"책 소개: {description}" if description else ""}

요구사항:
- **1-2문장으로 간결하게** (최대 80자)
- 핵심 가치만 강조
- 불필요한 수식어 제거
- 한국어로 작성
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 베스트셀러를 만드는 마케팅 전문가입니다. 독자의 마음을 움직이는 강력한 카피를 작성합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or 300,
                temperature=0.9,
            )
            
            copy = response.choices[0].message.content.strip()
            logger.info(f"마케팅 카피 생성 완료: {title}")
            return copy
            
        except Exception as e:
            logger.error(f"마케팅 카피 생성 실패: {e}")
            return None
    
    def generate_author_bio(
        self,
        author: str,
        book_title: str = "",
        additional_info: str = "",
        tone: str = 'formal',
        max_tokens: int = None
    ) -> Optional[str]:
        """
        저자 소개 텍스트 생성
        
        Args:
            author: 저자명
            book_title: 책 제목
            additional_info: 추가 정보
            tone: 텍스트 톤
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 저자 소개
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            tone_instruction = self._get_tone_instruction(tone)
            
            prompt = f"""저자 '{author}'에 대한 소개를 작성해주세요.

{f"대표 저서: {book_title}" if book_title else ""}
{f"추가 정보: {additional_info}" if additional_info else ""}

요구사항:
- {tone_instruction}
- 1-2 문단으로 구성
- 저자의 전문성과 권위를 드러내기
- 독자가 신뢰할 수 있는 저자임을 설득
- 한국어로 작성

주의: 실제 저자 정보를 모르는 경우, 일반적이고 전문적인 톤으로 작성하되 구체적인 허위 사실은 포함하지 마세요.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문 편집자입니다. 저자의 전문성과 신뢰도를 효과적으로 전달하는 저자 소개를 작성합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or 400,
                temperature=config.AI_SETTINGS['temperature'],
            )
            
            bio = response.choices[0].message.content.strip()
            logger.info(f"저자 소개 생성 완료: {author}")
            return bio
            
        except Exception as e:
            logger.error(f"저자 소개 생성 실패: {e}")
            return None
    
    def generate_multiple_variations(
        self,
        generate_func,
        variations: int = 3,
        **kwargs
    ) -> List[str]:
        """
        여러 버전의 텍스트 생성
        
        Args:
            generate_func: 생성 함수
            variations: 생성할 변형 수
            **kwargs: 생성 함수에 전달할 인자
            
        Returns:
            생성된 텍스트 리스트
        """
        results = []
        
        for i in range(variations):
            try:
                text = generate_func(**kwargs)
                if text:
                    results.append(text)
                    logger.info(f"변형 {i+1}/{variations} 생성 완료")
            except Exception as e:
                logger.error(f"변형 {i+1} 생성 실패: {e}")
                continue
        
        return results
