"""
Bannerbear API를 통한 전문적인 책 상세페이지 이미지 생성
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


class BannerbearGenerator:
    """Bannerbear REST API를 사용한 책 표지 및 상세페이지 이미지 생성"""
    
    BASE_URL = "https://api.bannerbear.com/v2"
    
    def __init__(self, api_key: str = None, template_id: str = None):
        """
        Args:
            api_key: Bannerbear API 키 (Bearer token)
            template_id: 사용할 템플릿 ID
        """
        self.api_key = api_key or config.BANNERBEAR_API_KEY
        self.template_id = template_id or config.BANNERBEAR_TEMPLATE_ID
        
        if self.api_key and self.api_key != "your_bannerbear_api_key_here":
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            logger.info("Bannerbear API 클라이언트 초기화 완료")
        else:
            self.headers = None
            logger.warning("Bannerbear API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
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
            logger.error("Bannerbear API 키가 설정되지 않았습니다.")
            return None
        
        try:
            # 스타일 정보 추출 (랜덤 또는 지정)
            primary_color = style.get('primary_color', '#2C3E50') if style else '#2C3E50'
            secondary_color = style.get('secondary_color', '#E74C3C') if style else '#E74C3C'
            accent_color = style.get('accent_color', '#F39C12') if style else '#F39C12'
            neutral_color = style.get('neutral_color', '#ECF0F1') if style else '#ECF0F1'
            
            logger.info(f"적용 색상 - Primary: {primary_color}, Secondary: {secondary_color}")
            
            # 현재 템플릿: Food Recipe Pinterest Pin
            # 레이어: image_container, title, ingredients_title, ingredients, 
            #        instructions_title, instructions, footer
            
            # 템플릿 레이어에 맞게 데이터 매핑 + 색상 적용
            modifications = [
                {
                    "name": "title",  # 제목 레이어
                    "text": title,
                    "color": primary_color  # 랜덤 색상 적용
                },
                {
                    "name": "ingredients_title",  # "책 소개" 섹션 제목
                    "text": "📖 책 소개",
                    "color": secondary_color,
                    "background": neutral_color  # 배경색
                },
                {
                    "name": "ingredients",  # 책 소개 내용
                    "text": description[:300] if description else "상세 내용을 확인해보세요.",
                    "color": "#333333"
                },
                {
                    "name": "instructions_title",  # "추천 포인트" 섹션 제목
                    "text": "✨ 추천 포인트",
                    "color": accent_color,
                    "background": neutral_color
                },
                {
                    "name": "instructions",  # 키워드 및 추가 정보
                    "text": f"저자: {author}\n\n키워드: {' · '.join(keywords[:5]) if keywords else 'N/A'}",
                    "color": "#555555"
                },
                {
                    "name": "footer",  # 하단 정보
                    "text": f"저자: {author}",
                    "color": "#FFFFFF",
                    "background": primary_color  # 푸터 배경을 Primary 색상으로
                }
            ]
            
            # 책 표지 이미지가 있으면 추가
            if cover_image_url:
                modifications.append({
                    "name": "image_container",
                    "image_url": cover_image_url
                })
            
            logger.info(f"Bannerbear 이미지 생성 요청: {title}")
            logger.info(f"전달 데이터: {len(modifications)}개 레이어 수정")
            
            # 이미지 생성 요청 (REST API)
            payload = {
                "template": self.template_id,
                "modifications": modifications,
                "webhook_url": None  # 동기 방식
            }
            
            response = requests.post(
                f"{self.BASE_URL}/images",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            uid = result.get("uid")
            
            if not uid:
                logger.error("Bannerbear 이미지 UID를 받지 못했습니다.")
                return None
            
            # 이미지 생성 완료 대기 (폴링)
            max_attempts = 30  # 최대 30번 시도 (약 60초)
            attempt = 0
            image_url = None
            
            while attempt < max_attempts:
                time.sleep(2)  # 2초 대기
                
                # 이미지 상태 확인
                status_response = requests.get(
                    f"{self.BASE_URL}/images/{uid}",
                    headers=self.headers,
                    timeout=10
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data.get("status") == "completed":
                    image_url = status_data.get("image_url")
                    break
                elif status_data.get("status") == "failed":
                    logger.error("Bannerbear 이미지 생성 실패")
                    return None
                
                attempt += 1
            
            if not image_url:
                logger.error("Bannerbear 이미지 생성 타임아웃")
                return None
            
            if not image_url:
                logger.error("Bannerbear 이미지 URL을 받지 못했습니다.")
                return None
            
            # 이미지 다운로드
            logger.info(f"이미지 다운로드 중: {image_url}")
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            # 저장
            if save_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"bannerbear_{timestamp}.jpg"
                save_path = config.IMAGE_OUTPUT_DIR / filename
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Bannerbear 이미지 생성 완료: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Bannerbear 이미지 생성 실패: {e}")
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
            logger.error("Bannerbear API 키가 설정되지 않았습니다.")
            return None
        
        try:
            # 3D 목업 템플릿 사용 (별도 템플릿 ID 필요)
            modifications = [
                {
                    "name": "book_cover",
                    "image_url": cover_image_url
                }
            ]
            
            payload = {
                "template": self.template_id,  # 3D 목업 전용 템플릿 ID
                "modifications": modifications
            }
            
            response = requests.post(
                f"{self.BASE_URL}/images",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            uid = result.get("uid")
            
            # 이미지 생성 대기
            max_attempts = 30
            attempt = 0
            image_url = None
            
            while attempt < max_attempts:
                time.sleep(2)
                
                status_response = requests.get(
                    f"{self.BASE_URL}/images/{uid}",
                    headers=self.headers,
                    timeout=10
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data.get("status") == "completed":
                    image_url = status_data.get("image_url")
                    break
                elif status_data.get("status") == "failed":
                    return None
                
                attempt += 1
            
            if not image_url:
                return None
            
            # 다운로드 및 저장
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            if save_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mockup_3d_{timestamp}.jpg"
                save_path = config.IMAGE_OUTPUT_DIR / filename
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
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
