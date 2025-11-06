"""
메인 실행 파일
랜덤 레이아웃 상세페이지 자동 생성 시스템
"""
import argparse
import logging
from pathlib import Path
import random
from typing import List, Optional

from src.utils.logger import setup_logger
from src.utils.html_to_image import HTMLToImageConverter
from src.data import Book, GoogleSheetsConnector
from src.ai import TextGenerator, ImageGenerator
from src.ai.bannerbear_generator import BannerbearGenerator
from src.ai.placid_generator import PlacidGenerator
from src.ai.auto_template import AutoTemplateGenerator
from src.template import TemplateRenderer, StyleRandomizer
import config

# 로거 설정
logger = setup_logger()


class PageGenerationPipeline:
    """상세페이지 생성 파이프라인"""
    
    def __init__(self, use_bannerbear: bool = False, use_placid: bool = False):
        """초기화
        
        Args:
            use_bannerbear: Bannerbear 사용 여부
            use_placid: Placid 사용 여부
        """
        self.text_generator = TextGenerator()
        self.image_generator = ImageGenerator()
        self.bannerbear_generator = BannerbearGenerator() if use_bannerbear else None
        self.placid_generator = PlacidGenerator() if use_placid else None
        self.template_renderer = TemplateRenderer()
        self.style_randomizer = StyleRandomizer()
        self.html_converter = HTMLToImageConverter()
        self.use_bannerbear = use_bannerbear
        self.use_placid = use_placid
        
        if use_placid and self.placid_generator and self.placid_generator.headers:
            logger.info("Placid 모드로 파이프라인 초기화 완료")
        elif use_bannerbear and self.bannerbear_generator and self.bannerbear_generator.headers:
            logger.info("Bannerbear 모드로 파이프라인 초기화 완료")
        else:
            logger.info("파이프라인 초기화 완료")
    
    def enrich_book_with_ai(self, book: Book, text_tone: str = 'formal') -> Book:
        """
        AI를 사용하여 도서 정보 보강
        
        Args:
            book: Book 객체
            text_tone: 텍스트 톤
            
        Returns:
            보강된 Book 객체
        """
        logger.info(f"AI 콘텐츠 생성 시작: {book.title}")
        
        # 책 소개 생성
        if not book.generated_intro and self.text_generator.client:
            intro = self.text_generator.generate_book_intro(
                title=book.title,
                author=book.author,
                description=book.description,
                keywords=book.keywords,
                tone=text_tone
            )
            if intro:
                book.generated_intro = intro
                logger.info("책 소개 생성 완료")
        
        # 마케팅 카피 생성
        if not book.generated_marketing_copy and self.text_generator.client:
            copy = self.text_generator.generate_marketing_copy(
                title=book.title,
                author=book.author,
                description=book.description or book.generated_intro,
                keywords=book.keywords,
                tone='marketing'
            )
            if copy:
                book.generated_marketing_copy = copy
                logger.info("마케팅 카피 생성 완료")
        
        # 저자 소개 생성
        if not book.generated_author_bio and self.text_generator.client:
            bio = self.text_generator.generate_author_bio(
                author=book.author,
                book_title=book.title,
                tone=text_tone
            )
            if bio:
                book.generated_author_bio = bio
                logger.info("저자 소개 생성 완료")
        
        logger.info(f"AI 콘텐츠 생성 완료: {book.title}")
        return book
    
    def generate_page(
        self,
        book: Book,
        use_ai: bool = True,
        generate_images: bool = False,
        convert_to_jpg: bool = True,
        style: dict = None,
        template_override: str = None,
    ) -> tuple[str, dict, Path, Optional[Path]]:
        """
        단일 도서 페이지 생성
        
        Args:
            book: Book 객체
            use_ai: AI 사용 여부
            generate_images: 이미지 생성 여부
            convert_to_jpg: JPG로 변환 여부
            style: 사용할 스타일 (없으면 랜덤)
            
        Returns:
            (HTML 문자열, 스타일, HTML 경로, JPG 경로) 튜플
        """
        logger.info(f"페이지 생성 시작: {book.title}")
        
        # AI로 필수 콘텐츠만 생성 (저자 소개 제외)
        if use_ai:
            text_tone = style.get('text_tone', 'formal') if style else 'formal'
            
            # 책 소개 생성
            intro = self.text_generator.generate_book_intro(
                title=book.title,
                author=book.author,
                description=book.description,
                keywords=book.keywords,
                tone=text_tone
            )
            if intro:
                book.generated_intro = intro
                logger.info("책 소개 생성 완료")
            
            # 마케팅 카피 생성
            copy = self.text_generator.generate_marketing_copy(
                title=book.title,
                author=book.author,
                description=book.description or intro,
                keywords=book.keywords,
                tone='marketing'
            )
            if copy:
                book.generated_marketing_copy = copy
                logger.info("마케팅 카피 생성 완료")
            
            # 저자 소개는 생성하지 않음 (제거)
            logger.info(f"AI 콘텐츠 생성 완료: {book.title}")
        
        # AI 자동 템플릿이 지정된 경우: HTML 렌더 + JPG 변환 경로로 우선 수행
        if template_override:
            output_path = self.template_renderer.render_and_save(
                book=book,
                style=style,
                template_name=template_override
            )

            with open(output_path, 'r', encoding='utf-8') as f:
                html = f.read()

            jpg_path = None
            if convert_to_jpg:
                try:
                    with self.html_converter as converter:
                        jpg_path = converter.convert_html_to_jpg(
                            html_path=output_path,
                            width=1200,
                            quality=90,
                            full_page=True
                        )
                    if jpg_path:
                        logger.info(f"JPG 변환 완료: {jpg_path}")
                except Exception as e:
                    logger.error(f"JPG 변환 실패: {e}")

            logger.info(f"페이지 생성 완료: {output_path}")
            return html, style or {}, output_path, jpg_path

        # Placid 사용 시 (우선순위 1)
        if self.use_placid and self.placid_generator and self.placid_generator.headers:
            logger.info("Placid로 상세페이지 이미지 생성 중...")
            logger.info(f"랜덤 스타일 적용 - Primary: {style['primary_color']}, Secondary: {style['secondary_color']}")
            
            # 섹션 데이터 준비
            sections = []
            if book.generated_intro:
                sections.append({"title": "책 소개", "content": book.generated_intro})
            if book.generated_marketing_copy:
                sections.append({"title": "추천 포인트", "content": book.generated_marketing_copy})
            if book.keywords:
                sections.append({"title": "키워드", "content": " · ".join(book.keywords[:5])})
            
            # Placid로 최종 이미지 생성 (랜덤 스타일 전달)
            jpg_path = self.placid_generator.create_book_detail_page(
                title=book.title,
                author=book.author,
                description=book.generated_intro or book.description or "",
                keywords=book.keywords or [],
                cover_image_url=book.cover_image_url,
                sections=sections,
                style=style  # 랜덤 색상 전달
            )
            
            if jpg_path:
                logger.info(f"Placid 이미지 생성 완료: {jpg_path}")
                # Placid 사용 시 HTML은 생성하지 않음
                return None, style or {}, None, jpg_path
            else:
                logger.warning("Placid 생성 실패, HTML 템플릿으로 대체")
        
        # Bannerbear 사용 시 (우선순위 2 - Placid 실패 시 대체)
        elif self.use_bannerbear and self.bannerbear_generator and self.bannerbear_generator.headers:
            logger.info("Bannerbear로 상세페이지 이미지 생성 중...")
            logger.info(f"랜덤 스타일 적용 - Primary: {style['primary_color']}, Secondary: {style['secondary_color']}")
            
            # 섹션 데이터 준비
            sections = []
            if book.generated_intro:
                sections.append({"title": "책 소개", "content": book.generated_intro})
            if book.generated_marketing_copy:
                sections.append({"title": "추천 포인트", "content": book.generated_marketing_copy})
            if book.keywords:
                sections.append({"title": "키워드", "content": " · ".join(book.keywords[:5])})
            
            # Bannerbear로 최종 이미지 생성 (랜덤 스타일 전달)
            jpg_path = self.bannerbear_generator.create_book_detail_page(
                title=book.title,
                author=book.author,
                description=book.generated_intro or book.description or "",
                keywords=book.keywords or [],
                cover_image_url=book.cover_image_url,
                sections=sections,
                style=style  # 랜덤 색상 전달
            )
            
            if jpg_path:
                logger.info(f"Bannerbear 이미지 생성 완료: {jpg_path}")
                # Bannerbear 사용 시 HTML은 생성하지 않음
                return None, style or {}, None, jpg_path
            else:
                logger.warning("Bannerbear 생성 실패, HTML 템플릿으로 대체")
        
        # 기존 HTML 템플릿 방식 (Bannerbear 미사용 시)
        # 이미지 생성 (선택사항)
        if generate_images and self.image_generator.client:
            logger.info("AI 이미지 생성 시작...")
            images = self.image_generator.generate_multiple_images(
                title=book.title,
                count=config.AI_SETTINGS['image_variations'],
                keywords=book.keywords
            )
            if images:
                book.generated_images = [str(img) for img in images]
                # 첫 번째 이미지를 표지로 사용
                book.cover_image_url = str(images[0])
                logger.info(f"{len(images)}개 이미지 생성 완료")
        
        # 페이지 렌더링
        output_path = self.template_renderer.render_and_save(
            book=book,
            style=style
        )
        
        # HTML 읽기
        with open(output_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # 사용된 스타일 정보
        if style is None:
            style = self.style_randomizer.get_complete_style()
        
        # JPG 변환
        jpg_path = None
        if convert_to_jpg:
            try:
                with self.html_converter as converter:
                    jpg_path = converter.convert_html_to_jpg(
                        html_path=output_path,
                        width=1200,
                        quality=90,
                        full_page=True
                    )
                if jpg_path:
                    logger.info(f"JPG 변환 완료: {jpg_path}")
            except Exception as e:
                logger.error(f"JPG 변환 실패: {e}")
        
        logger.info(f"페이지 생성 완료: {output_path}")
        return html, style, output_path, jpg_path
    
    def batch_generate(
        self,
        books: List[Book],
        use_ai: bool = True,
        generate_images: bool = False,
        convert_to_jpg: bool = True,
        ensure_diversity: bool = True,
        template_override: str = None,
    ) -> list:
        """
        여러 도서 페이지 일괄 생성
        
        Args:
            books: Book 객체 리스트
            use_ai: AI 사용 여부
            generate_images: 이미지 생성 여부
            convert_to_jpg: JPG로 변환 여부
            ensure_diversity: 다양성 보장 여부
            
        Returns:
            결과 리스트 [(html, style, html_path, jpg_path), ...]
        """
        results = []
        recent_styles = []
        
        for i, book in enumerate(books, 1):
            logger.info(f"배치 생성 진행중: {i}/{len(books)}")
            
            try:
                # 스타일 결정
                if ensure_diversity and recent_styles:
                    style = self.style_randomizer.ensure_diversity(recent_styles)
                else:
                    style = self.style_randomizer.get_complete_style()
                
                # 페이지 생성
                html, used_style, html_path, jpg_path = self.generate_page(
                    book=book,
                    use_ai=use_ai,
                    generate_images=generate_images,
                    convert_to_jpg=convert_to_jpg,
                    style=style,
                    template_override=template_override,
                )
                
                results.append((html, used_style, html_path, jpg_path))
                recent_styles.append(used_style)
                
            except Exception as e:
                logger.error(f"페이지 생성 실패 ({book.title}): {e}")
                continue
        
        logger.info(f"배치 생성 완료: 총 {len(results)}개 페이지")
        return results


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='랜덤 레이아웃 상세페이지 자동 생성 시스템'
    )
    
    parser.add_argument(
        '--source',
        choices=['sheets', 'test'],
        default='test',
        help='데이터 소스 (sheets: Google Sheets, test: 테스트 데이터)'
    )
    
    parser.add_argument(
        '--isbn',
        type=str,
        help='특정 ISBN의 도서만 생성'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='생성할 페이지 수 (테스트 모드)'
    )
    
    parser.add_argument(
        '--use-ai',
        action='store_true',
        default=True,
        help='AI 텍스트 생성 사용'
    )
    
    parser.add_argument(
        '--generate-images',
        action='store_true',
        help='AI 이미지 생성 사용'
    )
    
    parser.add_argument(
        '--use-bannerbear',
        action='store_true',
        help='Bannerbear로 전문 디자인 이미지 생성'
    )
    
    parser.add_argument(
        '--use-placid',
        action='store_true',
        help='Placid.app로 전문 디자인 이미지 생성 (추천!)'
    )
    
    parser.add_argument(
        '--use-ai-template',
        action='store_true',
        help='참조 이미지를 기반으로 AI가 HTML 템플릿을 자동 생성해서 사용'
    )

    parser.add_argument(
        '--reference-image',
        type=str,
        help='AI 템플릿 생성을 위한 참조 이미지 경로 또는 URL'
    )

    parser.add_argument(
        '--no-jpg',
        action='store_true',
        help='JPG 변환 생략 (HTML만 생성)'
    )
    
    args = parser.parse_args()
    
    # 파이프라인 초기화 (Placid 또는 Bannerbear 옵션 전달)
    pipeline = PageGenerationPipeline(
        use_bannerbear=args.use_bannerbear,
        use_placid=args.use_placid
    )
    
    # 데이터 로드
    books = []
    
    if args.source == 'sheets':
        logger.info("Google Sheets에서 데이터 로드 중...")
        try:
            connector = GoogleSheetsConnector()
            if args.isbn:
                book = connector.get_book_by_isbn(args.isbn)
                if book:
                    books = [book]
            else:
                books = connector.get_all_books()
        except Exception as e:
            logger.error(f"Google Sheets 연결 실패: {e}")
            return
    
    else:  # test mode
        logger.info("테스트 데이터 생성 중...")
        # 테스트용 샘플 데이터
        for i in range(args.count):
            book = Book(
                isbn=f"978890123456{i}",
                title=f"테스트 도서 {i+1}: 파이썬 프로그래밍",
                author="홍길동",
                publisher="테스트 출판사",
                publish_date="2024-01-15",
                price=25000,
                keywords=["프로그래밍", "파이썬", "개발"],
                description="파이썬 프로그래밍의 기초부터 실전까지 다루는 종합 가이드북입니다.",
                table_of_contents="1장: 파이썬 기초\n2장: 데이터 구조\n3장: 객체 지향 프로그래밍\n4장: 실전 프로젝트",
                cover_image_url="https://via.placeholder.com/400x600/2C3E50/ffffff?text=Book+Cover"
            )
            books.append(book)
    
    if not books:
        logger.error("처리할 도서 데이터가 없습니다.")
        return
    
    logger.info(f"총 {len(books)}개 도서 처리 시작")

    # AI 템플릿 자동 생성 모드일 경우, 참조 이미지 기반 템플릿을 먼저 준비
    template_override = None
    if args.use_ai_template and args.reference_image:
        try:
            auto_gen = AutoTemplateGenerator()
            rel_template_path = auto_gen.generate_from_reference(args.reference_image)
            if rel_template_path:
                template_override = rel_template_path
                logger.info(f"AI 템플릿 사용: {rel_template_path}")
            else:
                logger.warning("AI 템플릿 생성 실패. 기본 흐름으로 진행합니다.")
        except Exception as e:
            logger.error(f"AI 템플릿 생성 중 오류: {e}")
    
    # 페이지 생성 (로컬 생성 모드)
    results = pipeline.batch_generate(
        books=books,
        use_ai=args.use_ai,
        generate_images=args.generate_images,
        convert_to_jpg=not args.no_jpg,
        ensure_diversity=True,
        template_override=template_override,
    )
    
    logger.info(f"\n{'='*60}")
    logger.info(f"생성 완료! 총 {len(results)}개 페이지")
    if template_override:
        logger.info(f"HTML 출력: {config.HTML_OUTPUT_DIR}")
        if not args.no_jpg:
            logger.info(f"JPG 출력: {config.IMAGE_OUTPUT_DIR}")
    elif args.use_placid:
        logger.info(f"Placid 이미지 출력: {config.IMAGE_OUTPUT_DIR}")
    elif args.use_bannerbear:
        logger.info(f"Bannerbear 이미지 출력: {config.IMAGE_OUTPUT_DIR}")
    else:
        logger.info(f"HTML 출력: {config.HTML_OUTPUT_DIR}")
        if not args.no_jpg:
            logger.info(f"JPG 출력: {config.IMAGE_OUTPUT_DIR}")
    logger.info(f"{'='*60}\n")
    
    for html, style, html_path, jpg_path in results:
        if jpg_path:
            logger.info(f"  - {jpg_path.name if hasattr(jpg_path, 'name') else jpg_path}")
        elif html_path:
            logger.info(f"  - {html_path.name}")
        
        if style and isinstance(style, dict):
            if 'layout' in style:
                logger.info(f"    레이아웃: {style['layout']}")
            if 'primary_color' in style:
                logger.info(f"    컬러: {style['primary_color']}")
            if 'heading_font' in style:
                logger.info(f"    폰트: {style['heading_font']}")
        
        if jpg_path:
            jpg_name = jpg_path.name if hasattr(jpg_path, 'name') else Path(jpg_path).name
            logger.info(f"    JPG: {jpg_name}")
        logger.info(f"    폰트: {style['heading_font']}")
        if jpg_path:
            logger.info(f"    JPG: {jpg_path.name}")


if __name__ == '__main__':
    main()
