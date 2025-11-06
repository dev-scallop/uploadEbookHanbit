"""
DALL-E를 사용한 이미지 생성 모듈
"""
from openai import OpenAI
from typing import List, Optional
import logging
from pathlib import Path
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

import config

logger = logging.getLogger(__name__)


class ImageGenerator:
    """DALL-E를 사용하여 이미지를 생성하는 클래스"""
    
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
            logger.info("OpenAI 이미지 생성 클라이언트 초기화 완료")
    
    def generate_book_cover_image(
        self,
        title: str,
        keywords: List[str] = None,
        style: str = "professional",
        size: str = "1024x1024"
    ) -> Optional[str]:
        """
        책 표지 이미지 생성 (배경만, 텍스트 제외)
        
        Args:
            title: 책 제목
            keywords: 키워드 리스트
            style: 이미지 스타일
            size: 이미지 크기 (1024x1024, 1024x1792, 1792x1024)
            
        Returns:
            생성된 이미지 URL
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            keywords_str = ', '.join(keywords) if keywords else ''
            
            # 개선된 프롬프트: 텍스트 없이 배경 디자인만
            prompt = f"""Create a professional book cover background design.
Theme and style: {keywords_str}, {style}, modern, elegant
Requirements:
- Abstract background with visual interest
- Leave top 40% empty for title text overlay
- Professional color scheme
- High quality, artistic
- NO TEXT, NO WORDS, NO LETTERS at all
- Just beautiful background design and graphics
"""
            
            # DALL-E 3로 이미지 생성
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            logger.info(f"책 표지 배경 이미지 생성 완료: {title}")
            return image_url
            
        except Exception as e:
            logger.error(f"이미지 생성 실패: {e}")
            return None
    
    def generate_book_cover_with_text(
        self,
        title: str,
        author: str,
        keywords: List[str] = None,
        style: str = "professional",
        primary_color: str = "#FFFFFF",
        save_path: Path = None
    ) -> Optional[Path]:
        """
        책 표지 이미지 생성 + 텍스트 오버레이 (신규 기능!)
        
        Args:
            title: 책 제목
            author: 저자명
            keywords: 키워드 리스트
            style: 이미지 스타일
            primary_color: 텍스트 색상
            save_path: 저장 경로
            
        Returns:
            완성된 이미지 파일 경로
        """
        try:
            # 1단계: DALL-E로 배경 생성
            logger.info(f"책 표지 배경 생성 중: {title}")
            background_url = self.generate_book_cover_image(
                title=title,
                keywords=keywords,
                style=style,
                size="1024x1792"  # 세로형 책 표지
            )
            
            if not background_url:
                return None
            
            # 2단계: 배경 이미지 다운로드
            response = requests.get(background_url, timeout=30)
            background_img = Image.open(io.BytesIO(response.content))
            
            # 3단계: 텍스트 오버레이 준비
            draw = ImageDraw.Draw(background_img)
            width, height = background_img.size
            
            # 4단계: 폰트 로드 (시스템 폰트 사용)
            try:
                # Windows 기본 폰트 시도
                font_title = ImageFont.truetype("malgun.ttf", 80)  # 맑은 고딕
                font_author = ImageFont.truetype("malgun.ttf", 50)
            except:
                # 폰트 로드 실패시 기본 폰트
                font_title = ImageFont.load_default()
                font_author = ImageFont.load_default()
            
            # 5단계: 텍스트 위치 계산 (중앙 정렬)
            # 제목 배경 박스
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            title_x = (width - title_width) // 2
            title_y = height // 4  # 상단 1/4 지점
            
            # 반투명 배경 박스 그리기 (가독성 향상)
            padding = 30
            overlay = Image.new('RGBA', background_img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # 제목 배경
            overlay_draw.rectangle(
                [title_x - padding, title_y - padding, 
                 title_x + title_width + padding, title_y + title_height + padding],
                fill=(0, 0, 0, 180)  # 검은색 반투명
            )
            
            # 배경 합성
            background_img = Image.alpha_composite(
                background_img.convert('RGBA'), 
                overlay
            ).convert('RGB')
            
            draw = ImageDraw.Draw(background_img)
            
            # 6단계: 제목 텍스트 그리기
            draw.text(
                (title_x, title_y),
                title,
                fill='white',
                font=font_title
            )
            
            # 7단계: 저자명 텍스트 그리기
            author_text = f"저자: {author}"
            author_bbox = draw.textbbox((0, 0), author_text, font=font_author)
            author_width = author_bbox[2] - author_bbox[0]
            author_x = (width - author_width) // 2
            author_y = title_y + title_height + 40
            
            draw.text(
                (author_x, author_y),
                author_text,
                fill='white',
                font=font_author
            )
            
            # 8단계: 저장
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cover_{timestamp}.jpg"
                save_path = config.IMAGE_OUTPUT_DIR / filename
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            background_img.save(save_path, quality=95)
            
            logger.info(f"텍스트 오버레이 완료: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"책 표지 텍스트 오버레이 실패: {e}")
            return None
    
    def generate_banner_image(
        self,
        title: str,
        theme: str = "",
        keywords: List[str] = None,
        size: str = "1792x1024"
    ) -> Optional[str]:
        """
        배너 이미지 생성
        
        Args:
            title: 책 제목
            theme: 테마
            keywords: 키워드 리스트
            size: 이미지 크기
            
        Returns:
            생성된 이미지 URL
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            keywords_str = ', '.join(keywords) if keywords else ''
            
            prompt = f"""Create a wide banner image for a book promotion.
Book title: {title}
Theme: {theme}
Keywords: {keywords_str}
Requirements:
- Wide format suitable for website banner
- Professional and visually striking
- Abstract or thematic representation
- No text
"""
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            logger.info(f"배너 이미지 생성 완료: {title}")
            return image_url
            
        except Exception as e:
            logger.error(f"배너 이미지 생성 실패: {e}")
            return None
    
    def download_image(self, image_url: str, save_path: Path = None) -> Optional[Path]:
        """
        이미지 URL에서 이미지 다운로드
        
        Args:
            image_url: 이미지 URL
            save_path: 저장 경로 (없으면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        try:
            # 저장 경로 결정
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_{timestamp}.png"
                save_path = config.IMAGE_OUTPUT_DIR / filename
            
            # 디렉토리 생성
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 파일 저장
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"이미지 다운로드 완료: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"이미지 다운로드 실패: {e}")
            return None
    
    def generate_and_download(
        self,
        title: str,
        image_type: str = "cover",
        keywords: List[str] = None,
        save_path: Path = None,
        **kwargs
    ) -> Optional[Path]:
        """
        이미지 생성 및 다운로드
        
        Args:
            title: 책 제목
            image_type: 이미지 타입 (cover, banner)
            keywords: 키워드 리스트
            save_path: 저장 경로
            **kwargs: 추가 인자
            
        Returns:
            저장된 파일 경로
        """
        # 이미지 생성
        if image_type == "cover":
            image_url = self.generate_book_cover_image(title, keywords, **kwargs)
        elif image_type == "banner":
            image_url = self.generate_banner_image(title, keywords=keywords, **kwargs)
        else:
            logger.error(f"지원하지 않는 이미지 타입: {image_type}")
            return None
        
        if not image_url:
            return None
        
        # 이미지 다운로드
        return self.download_image(image_url, save_path)
    
    def generate_multiple_images(
        self,
        title: str,
        count: int = 2,
        image_type: str = "cover",
        keywords: List[str] = None,
        **kwargs
    ) -> List[Path]:
        """
        여러 이미지 생성
        
        Args:
            title: 책 제목
            count: 생성할 이미지 수
            image_type: 이미지 타입
            keywords: 키워드 리스트
            **kwargs: 추가 인자
            
        Returns:
            저장된 파일 경로 리스트
        """
        results = []
        
        for i in range(count):
            try:
                # 파일명에 번호 추가
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{image_type}_{i+1}_{timestamp}.png"
                save_path = config.IMAGE_OUTPUT_DIR / filename
                
                # 이미지 생성 및 다운로드
                path = self.generate_and_download(
                    title=title,
                    image_type=image_type,
                    keywords=keywords,
                    save_path=save_path,
                    **kwargs
                )
                
                if path:
                    results.append(path)
                    logger.info(f"이미지 {i+1}/{count} 생성 완료")
                    
            except Exception as e:
                logger.error(f"이미지 {i+1} 생성 실패: {e}")
                continue
        
        return results
