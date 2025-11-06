"""
Placid.app API를 통한 전문적인 책 상세페이지 이미지 생성
REST API 직접 호출 방식
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
import requests
import time
import json
import logging

import config

logger = logging.getLogger(__name__)


class PlacidGenerator:
    """Placid.app REST API를 사용한 책 표지 및 상세페이지 이미지 생성"""
    
    BASE_URL = "https://api.placid.app/api/rest"
    
    def __init__(self, api_token: str = None, template_id: str = None):
        """
        Args:
            api_token: Placid API 토큰
            template_id: 사용할 템플릿 ID
        """
        self.api_token = api_token or config.PLACID_API_TOKEN
        self.template_id = template_id or config.PLACID_TEMPLATE_ID
        
        if self.api_token and self.api_token != "your_placid_api_token_here":
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            logger.info("Placid API 클라이언트 초기화 완료")
        else:
            self.headers = None
            logger.warning("Placid API 토큰이 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    def create_book_detail_page(
        self,
        title: str,
        author: str,
        description: str,
        keywords: List[str],
        cover_image_url: str = None,
        sections: List[Dict[str, str]] = None,
        save_path: Path = None,
        style: Dict[str, str] = None
    ) -> Optional[Path]:
        """
        책 상세페이지 전체 이미지 생성 (랜덤 스타일 적용)
        
        Args:
            title: 책 제목
            author: 저자명
            description: 책 소개
            keywords: 키워드 리스트
            cover_image_url: 책 표지 이미지 URL (옵션)
            sections: 섹션 리스트 [{"title": "...", "content": "..."}]
            save_path: 저장 경로
            style: 랜덤 스타일 딕셔너리 (색상, 폰트 등)
            
        Returns:
            생성된 이미지 파일 경로
        """
        if not self.headers:
            logger.error("Placid API 토큰이 설정되지 않았습니다.")
            return None
        
        try:
            # 스타일 정보 추출 (랜덤 또는 지정)
            primary_color = style.get('primary_color', '#2C3E50') if style else '#2C3E50'
            secondary_color = style.get('secondary_color', '#E74C3C') if style else '#E74C3C'
            accent_color = style.get('accent_color', '#F39C12') if style else '#F39C12'
            neutral_color = style.get('neutral_color', '#ECF0F1') if style else '#ECF0F1'
            
            logger.info(f"Placid 이미지 생성 요청: {title}")
            logger.info(f"적용 색상 - Primary: {primary_color}, Secondary: {secondary_color}")
            
            # Placid layers 구조
            # 템플릿에 정의된 레이어 이름에 맞게 데이터 매핑
            layers = {
                "book_title": {
                    "text": title,
                    "color": primary_color
                },
                "header_subtitle": {
                    "text": "이론과 실습을 통해 배우는",
                    "color": secondary_color
                },
                "author_name": {
                    "text": f"저자: {author}",
                    "color": "#FFFFFF",
                    "background_color": primary_color
                },
                "section1_title": {
                    "text": "📖 이 책의 특징",
                    "color": secondary_color
                },
                "section1_content": {
                    "text": description[:300] if description else "상세 내용을 확인해보세요.",
                    "color": "#333333"
                },
                "section2_title": {
                    "text": "✨ 핵심 키워드",
                    "color": accent_color
                },
                "section2_content": {
                    "text": " · ".join(keywords[:5]) if keywords else "N/A",
                    "color": "#555555"
                },
                "background": {
                    "background_color": neutral_color
                }
            }
            
            # 책 표지 이미지가 있으면 추가
            if cover_image_url:
                layers["book_cover_image"] = {
                    "image": cover_image_url
                }
            
            # 섹션 데이터 추가
            if sections:
                for i, section in enumerate(sections[:3], 1):
                    layers[f"section{i}_title"] = {
                        "text": section.get("title", ""),
                        "color": accent_color
                    }
                    layers[f"section{i}_content"] = {
                        "text": section.get("content", "")[:200],
                        "color": "#666666"
                    }
            
            logger.info(f"전달 데이터: {len(layers)}개 레이어 수정")
            
            # Placid API 요청
            payload = {
                "template_uuid": self.template_id,
                "create_now": True,  # 동기 방식 (즉시 생성)
                "layers": layers
            }
            
            response = requests.post(
                f"{self.BASE_URL}/images",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 이미지 URL 확인
            image_url = result.get("image_url")
            
            if not image_url:
                # 폴링 방식 (비동기인 경경우)
                image_id = result.get("id")
                if not image_id:
                    logger.error("Placid 이미지 ID를 받지 못했습니다.")
                    return None
                
                # 이미지 생성 완료 대기
                max_attempts = 30
                attempt = 0
                
                while attempt < max_attempts:
                    time.sleep(2)
                    
                    status_response = requests.get(
                        f"{self.BASE_URL}/images/{image_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "finished":
                        image_url = status_data.get("image_url")
                        break
                    elif status_data.get("status") == "failed":
                        logger.error("Placid 이미지 생성 실패")
                        return None
                    
                    attempt += 1
                
                if not image_url:
                    logger.error("Placid 이미지 생성 타임아웃")
                    return None
            
            # 이미지 다운로드
            logger.info(f"이미지 다운로드 중: {image_url}")
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()
            
            # 저장
            if save_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"placid_{timestamp}.jpg"
                save_path = config.IMAGE_OUTPUT_DIR / filename
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"Placid 이미지 생성 완료: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Placid 이미지 생성 실패: {e}")
            return None
    
    def create_3d_book_mockup(
        self,
        cover_image_url: str,
        save_path: Path = None
    ) -> Optional[Path]:
        """
        3D 책 목업 이미지 생성
        
        Args:
            cover_image_url: 책 표지 이미지 URL
            save_path: 저장 경로
            
        Returns:
            생성된 이미지 파일 경로
        """
        if not self.headers:
            logger.error("Placid API 토큰이 설정되지 않았습니다.")
            return None
        
        try:
            layers = {
                "book_cover": {
                    "image": cover_image_url
                }
            }
            
            payload = {
                "create_now": True,
                "layers": layers
            }
            
            response = requests.post(
                f"{self.BASE_URL}/images/templates/{self.template_id}",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            image_url = result.get("image_url")
            
            if not image_url:
                return None
            
            # 다운로드 및 저장
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()
            
            if save_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mockup_3d_{timestamp}.jpg"
                save_path = config.IMAGE_OUTPUT_DIR / filename
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"3D 목업 이미지 생성 완료: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"3D 목업 생성 실패: {e}")
            return None
    
    def get_template_info(self) -> Optional[Dict[str, Any]]:
        """
        현재 템플릿 정보 조회
        
        Returns:
            템플릿 정보 딕셔너리
        """
        if not self.headers:
            return None
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/templates/{self.template_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            template = response.json()
            logger.info(f"템플릿 정보: {template.get('name')}")
            return template
        except Exception as e:
            logger.error(f"템플릿 정보 조회 실패: {e}")
            return None
    
    def list_templates(self) -> Optional[List[Dict[str, Any]]]:
        """
        사용 가능한 모든 템플릿 목록 조회
        
        Returns:
            템플릿 리스트
        """
        if not self.headers:
            return None
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/templates",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            templates = response.json()
            logger.info(f"템플릿 {len(templates)}개 발견")
            return templates
        except Exception as e:
            logger.error(f"템플릿 목록 조회 실패: {e}")
            return None
