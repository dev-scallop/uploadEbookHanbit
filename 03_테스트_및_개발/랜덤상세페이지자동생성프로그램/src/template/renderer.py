"""
Jinja2 템플릿 렌더러
"""
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Dict
import logging
from pathlib import Path
import shutil

import config
from src.data.book_model import Book
from .randomizer import StyleRandomizer

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Jinja2를 사용하여 HTML 페이지를 렌더링하는 클래스"""
    
    def __init__(self, templates_dir: Path = None):
        """
        초기화
        
        Args:
            templates_dir: 템플릿 디렉토리 경로
        """
        self.templates_dir = templates_dir or config.TEMPLATES_DIR
        
        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # 커스텀 필터 추가
        self.env.filters['format_price'] = self._format_price
        
        logger.info(f"템플릿 렌더러 초기화: {self.templates_dir}")
    
    def _format_price(self, price: int) -> str:
        """
        가격 포맷팅 필터
        
        Args:
            price: 가격
            
        Returns:
            포맷팅된 가격 문자열
        """
        return f"{price:,}원"
    
    def render(self, book: Book, style: Dict[str, any] = None, template_name: str = None) -> str:
        """
        도서 정보와 스타일을 사용하여 HTML 페이지 렌더링
        
        Args:
            book: Book 객체
            style: 스타일 딕셔너리 (없으면 랜덤 생성)
            template_name: 사용할 템플릿 이름 (없으면 스타일에서 가져옴)
            
        Returns:
            렌더링된 HTML 문자열
        """
        # 스타일이 없으면 랜덤 생성
        if style is None:
            randomizer = StyleRandomizer()
            style = randomizer.get_complete_style()
        
        # 템플릿 이름 결정
        if template_name is None:
            template_name = style.get('layout', config.LAYOUT_TEMPLATES[0])
        
        try:
            # 템플릿 로드
            template = self.env.get_template(template_name)
            
            # 렌더링
            html = template.render(
                book=book,
                style=style,
            )
            
            logger.info(f"페이지 렌더링 완료: {book.title} ({template_name})")
            return html
            
        except TemplateNotFound:
            logger.error(f"템플릿을 찾을 수 없습니다: {template_name}")
            raise
        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {e}")
            raise
    
    def render_with_random_style(self, book: Book, seed=None) -> tuple[str, Dict]:
        """
        랜덤 스타일로 페이지 렌더링
        
        Args:
            book: Book 객체
            seed: 랜덤 시드
            
        Returns:
            (렌더링된 HTML, 사용된 스타일) 튜플
        """
        randomizer = StyleRandomizer(seed=seed)
        style = randomizer.get_complete_style()
        
        html = self.render(book=book, style=style)
        
        return html, style
    
    def save_html(self, html: str, output_path: Path):
        """
        HTML을 파일로 저장
        
        Args:
            html: HTML 문자열
            output_path: 출력 파일 경로
        """
        try:
            # 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 템플릿 정적 자산(css) 복사: 출력 디렉토리/html/css 로
            css_src = self.templates_dir / 'css'
            css_dst = output_path.parent / 'css'
            if css_src.exists():
                try:
                    shutil.copytree(css_src, css_dst, dirs_exist_ok=True)
                except Exception as copy_err:
                    logger.warning(f"CSS 자산 복사 경고: {copy_err}")
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"HTML 파일 저장 완료: {output_path}")
            
        except Exception as e:
            logger.error(f"HTML 파일 저장 실패: {e}")
            raise
    
    def render_and_save(
        self,
        book: Book,
        output_path: Path = None,
        style: Dict[str, any] = None,
        template_name: str = None
    ) -> Path:
        """
        페이지를 렌더링하고 파일로 저장
        
        Args:
            book: Book 객체
            output_path: 출력 파일 경로 (없으면 자동 생성)
            style: 스타일 딕셔너리
            template_name: 템플릿 이름
            
        Returns:
            저장된 파일 경로
        """
        # HTML 렌더링
        html = self.render(book=book, style=style, template_name=template_name)
        
        # 출력 경로 결정
        if output_path is None:
            filename = f"{book.isbn}_{book.title[:20]}.html"
            # 파일명에서 특수문자 제거
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.'))
            output_path = config.HTML_OUTPUT_DIR / filename
        
        # 파일 저장
        self.save_html(html, output_path)
        
        return output_path
    
    def batch_render(
        self,
        books: list[Book],
        ensure_diversity: bool = True
    ) -> list[tuple[Path, Dict]]:
        """
        여러 도서를 배치로 렌더링
        
        Args:
            books: Book 객체 리스트
            ensure_diversity: 다양성 보장 여부
            
        Returns:
            (파일 경로, 스타일) 튜플의 리스트
        """
        results = []
        recent_styles = []
        randomizer = StyleRandomizer()
        
        for book in books:
            try:
                # 스타일 생성
                if ensure_diversity and recent_styles:
                    style = randomizer.ensure_diversity(recent_styles)
                else:
                    style = randomizer.get_complete_style()
                
                # 렌더링 및 저장
                output_path = self.render_and_save(book=book, style=style)
                
                results.append((output_path, style))
                recent_styles.append(style)
                
                logger.info(f"배치 렌더링 완료: {book.title}")
                
            except Exception as e:
                logger.error(f"배치 렌더링 실패 ({book.title}): {e}")
                continue
        
        logger.info(f"배치 렌더링 총 {len(results)}개 완료")
        return results
    
    def get_available_templates(self) -> list[str]:
        """
        사용 가능한 템플릿 목록 반환
        
        Returns:
            템플릿 파일명 리스트
        """
        templates = []
        for template in config.LAYOUT_TEMPLATES:
            template_path = self.templates_dir / template
            if template_path.exists():
                templates.append(template)
        
        return templates
