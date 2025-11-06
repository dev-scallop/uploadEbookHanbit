"""
기본 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.book_model import Book
from src.template import TemplateRenderer, StyleRandomizer
from src.utils.logger import setup_logger

# 로거 설정
logger = setup_logger()


def test_basic_generation():
    """기본 페이지 생성 테스트"""
    logger.info("기본 페이지 생성 테스트 시작")
    
    # 테스트용 도서 데이터
    book = Book(
        isbn="9788901234567",
        title="파이썬 완벽 가이드",
        author="김개발",
        publisher="프로그래밍 출판사",
        publish_date="2024-01-15",
        price=32000,
        keywords=["Python", "프로그래밍", "개발", "코딩"],
        description="""
        이 책은 파이썬 프로그래밍의 기초부터 고급 기술까지 다루는 종합 가이드입니다.
        초보자부터 중급 개발자까지 누구나 쉽게 따라할 수 있도록 구성되어 있으며,
        실전 프로젝트를 통해 실무 능력을 키울 수 있습니다.
        """,
        table_of_contents="""
Part 1: 파이썬 기초
  1장: 파이썬 소개와 설치
  2장: 변수와 데이터 타입
  3장: 제어문과 반복문
  
Part 2: 중급 파이썬
  4장: 함수와 모듈
  5장: 객체 지향 프로그래밍
  6장: 파일 입출력
  
Part 3: 고급 파이썬
  7장: 예외 처리
  8장: 데이터베이스 연동
  9장: 웹 스크래핑
  
Part 4: 실전 프로젝트
  10장: 웹 애플리케이션 개발
  11장: 데이터 분석
  12장: 머신러닝 기초
        """,
        cover_image_url="https://via.placeholder.com/400x600/2C3E50/ffffff?text=Python+Guide"
    )
    
    # 템플릿 렌더러 초기화
    renderer = TemplateRenderer()
    randomizer = StyleRandomizer()
    
    # 여러 스타일로 페이지 생성
    for i in range(5):
        logger.info(f"\n{'='*60}")
        logger.info(f"테스트 {i+1}/5: 랜덤 스타일로 페이지 생성")
        logger.info(f"{'='*60}")
        
        # 랜덤 스타일 생성
        style = randomizer.get_complete_style()
        
        # 페이지 렌더링 및 저장
        output_path = renderer.render_and_save(
            book=book,
            style=style
        )
        
        logger.info(f"✓ 생성 완료: {output_path}")
        logger.info(f"  - 레이아웃: {style['layout']}")
        logger.info(f"  - 주 컬러: {style['primary_color']}")
        logger.info(f"  - 보조 컬러: {style['secondary_color']}")
        logger.info(f"  - 제목 폰트: {style['heading_font']}")
        logger.info(f"  - 본문 폰트: {style['body_font']}")
        logger.info(f"  - 텍스트 톤: {style['text_tone']}")
    
    logger.info(f"\n{'='*60}")
    logger.info("✅ 모든 테스트 완료!")
    logger.info(f"{'='*60}\n")


def test_all_templates():
    """모든 템플릿 테스트"""
    logger.info("모든 템플릿 테스트 시작")
    
    import config
    
    book = Book(
        isbn="9788901234567",
        title="모던 자바스크립트 Deep Dive",
        author="이웅모",
        publisher="위키북스",
        publish_date="2023-09-01",
        price=45000,
        keywords=["JavaScript", "웹개발", "프론트엔드"],
        description="자바스크립트의 기본 개념부터 동작 원리까지 깊이 있게 학습하는 책입니다.",
        table_of_contents="1부: 핵심 개념\n2부: 함수\n3부: 객체\n4부: 비동기 프로그래밍",
        cover_image_url="https://via.placeholder.com/400x600/3498db/ffffff?text=JavaScript"
    )
    
    renderer = TemplateRenderer()
    
    # 각 템플릿별로 페이지 생성
    for template in config.LAYOUT_TEMPLATES:
        logger.info(f"\n템플릿 테스트: {template}")
        
        style = {
            'layout': template,
            'primary_color': '#2C3E50',
            'secondary_color': '#E74C3C',
            'neutral_color': '#ECF0F1',
            'accent_color': '#F1C40F',
            'heading_font': 'Noto Serif KR',
            'body_font': 'Noto Sans KR',
            'text_tone': 'formal',
            'image_position': 'left',
        }
        
        try:
            output_path = renderer.render_and_save(
                book=book,
                style=style,
                template_name=template
            )
            logger.info(f"✓ {template} 생성 완료: {output_path}")
        except Exception as e:
            logger.error(f"✗ {template} 생성 실패: {e}")
    
    logger.info("\n✅ 모든 템플릿 테스트 완료!")


def test_diversity():
    """다양성 보장 테스트"""
    logger.info("다양성 보장 테스트 시작")
    
    book = Book(
        isbn="9788901234567",
        title="클린 코드",
        author="로버트 C. 마틴",
        publisher="인사이트",
        publish_date="2013-12-24",
        price=33000,
        keywords=["클린코드", "소프트웨어", "개발"],
        description="좋은 코드를 작성하는 방법에 대한 실용적인 가이드",
        cover_image_url="https://via.placeholder.com/400x600/27ae60/ffffff?text=Clean+Code"
    )
    
    renderer = TemplateRenderer()
    randomizer = StyleRandomizer()
    
    recent_styles = []
    
    for i in range(10):
        # 다양성 보장하여 스타일 생성
        style = randomizer.ensure_diversity(recent_styles, max_similar=2)
        
        logger.info(f"\n생성 {i+1}/10:")
        logger.info(f"  레이아웃: {style['layout']}")
        logger.info(f"  주 컬러: {style['primary_color']}")
        
        recent_styles.append(style)
    
    # 다양성 분석
    layouts = [s['layout'] for s in recent_styles]
    layout_counts = {layout: layouts.count(layout) for layout in set(layouts)}
    
    logger.info(f"\n{'='*60}")
    logger.info("다양성 분석 결과:")
    logger.info(f"{'='*60}")
    for layout, count in layout_counts.items():
        logger.info(f"  {layout}: {count}회 ({count/len(recent_styles)*100:.1f}%)")
    
    logger.info("\n✅ 다양성 테스트 완료!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='테스트 실행')
    parser.add_argument(
        '--test',
        choices=['basic', 'templates', 'diversity', 'all'],
        default='basic',
        help='실행할 테스트'
    )
    
    args = parser.parse_args()
    
    if args.test == 'basic' or args.test == 'all':
        test_basic_generation()
    
    if args.test == 'templates' or args.test == 'all':
        test_all_templates()
    
    if args.test == 'diversity' or args.test == 'all':
        test_diversity()
