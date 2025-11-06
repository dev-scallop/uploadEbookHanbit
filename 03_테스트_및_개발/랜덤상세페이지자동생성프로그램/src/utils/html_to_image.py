"""
HTML to JPG 변환 모듈
Playwright를 사용하여 HTML 페이지를 JPG 이미지로 변환합니다.
"""
from pathlib import Path
from typing import Optional
import logging
from playwright.sync_api import sync_playwright
import os

import config

logger = logging.getLogger(__name__)


class HTMLToImageConverter:
    """HTML을 이미지로 변환하는 클래스"""
    
    def __init__(self):
        """초기화"""
        self.playwright = None
        self.browser = None
        logger.info("HTML→이미지 변환기 초기화")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.playwright = sync_playwright().start()
        # 헤드리스 모드로 브라우저 시작
        self.browser = self.playwright.chromium.launch(headless=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def convert_html_to_jpg(
        self,
        html_path: Path,
        output_path: Path = None,
        width: int = 1200,
        quality: int = 90,
        full_page: bool = True
    ) -> Optional[Path]:
        """
        HTML 파일을 JPG 이미지로 변환
        
        Args:
            html_path: HTML 파일 경로
            output_path: 출력 JPG 경로 (없으면 자동 생성)
            width: 뷰포트 너비 (픽셀)
            quality: JPG 품질 (0-100)
            full_page: 전체 페이지 캡처 여부
            
        Returns:
            저장된 JPG 파일 경로
        """
        if not html_path.exists():
            logger.error(f"HTML 파일을 찾을 수 없습니다: {html_path}")
            return None
        
        try:
            # 출력 경로 결정
            if output_path is None:
                output_path = config.IMAGE_OUTPUT_DIR / f"{html_path.stem}.jpg"
            
            # 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 페이지 열기
            page = self.browser.new_page(
                viewport={'width': width, 'height': 800}
            )
            
            # HTML 파일 로드 (file:// 프로토콜 사용)
            file_url = html_path.absolute().as_uri()
            page.goto(file_url, wait_until='networkidle')
            
            # 페이지가 완전히 로드될 때까지 대기
            page.wait_for_timeout(1000)  # 1초 대기
            
            # 스크린샷 촬영 (JPG)
            page.screenshot(
                path=str(output_path),
                type='jpeg',
                quality=quality,
                full_page=full_page
            )
            
            page.close()
            
            logger.info(f"HTML→JPG 변환 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"HTML→JPG 변환 실패: {e}")
            return None
    
    def batch_convert(
        self,
        html_paths: list[Path],
        output_dir: Path = None,
        **kwargs
    ) -> list[Path]:
        """
        여러 HTML 파일을 JPG로 일괄 변환
        
        Args:
            html_paths: HTML 파일 경로 리스트
            output_dir: 출력 디렉토리
            **kwargs: convert_html_to_jpg에 전달할 추가 인자
            
        Returns:
            저장된 JPG 파일 경로 리스트
        """
        output_dir = output_dir or config.IMAGE_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for i, html_path in enumerate(html_paths, 1):
            logger.info(f"변환 진행: {i}/{len(html_paths)}")
            
            try:
                output_path = output_dir / f"{html_path.stem}.jpg"
                
                jpg_path = self.convert_html_to_jpg(
                    html_path=html_path,
                    output_path=output_path,
                    **kwargs
                )
                
                if jpg_path:
                    results.append(jpg_path)
                    
            except Exception as e:
                logger.error(f"변환 실패 ({html_path.name}): {e}")
                continue
        
        logger.info(f"일괄 변환 완료: {len(results)}/{len(html_paths)}개 성공")
        return results


def convert_single_html(html_path: Path, output_path: Path = None, **kwargs) -> Optional[Path]:
    """
    단일 HTML 파일을 JPG로 변환 (편의 함수)
    
    Args:
        html_path: HTML 파일 경로
        output_path: 출력 JPG 경로
        **kwargs: 추가 인자
        
    Returns:
        저장된 JPG 파일 경로
    """
    with HTMLToImageConverter() as converter:
        return converter.convert_html_to_jpg(html_path, output_path, **kwargs)


def convert_html_directory(html_dir: Path, output_dir: Path = None, **kwargs) -> list[Path]:
    """
    디렉토리 내 모든 HTML 파일을 JPG로 변환 (편의 함수)
    
    Args:
        html_dir: HTML 파일들이 있는 디렉토리
        output_dir: 출력 디렉토리
        **kwargs: 추가 인자
        
    Returns:
        저장된 JPG 파일 경로 리스트
    """
    html_files = list(html_dir.glob("*.html"))
    
    if not html_files:
        logger.warning(f"HTML 파일을 찾을 수 없습니다: {html_dir}")
        return []
    
    with HTMLToImageConverter() as converter:
        return converter.batch_convert(html_files, output_dir, **kwargs)
