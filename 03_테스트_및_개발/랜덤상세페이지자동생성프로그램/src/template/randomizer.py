"""
스타일 랜덤화 엔진
폰트, 컬러, 레이아웃, 이미지 배치를 랜덤화합니다.
"""
import random
from typing import Dict, List
import logging

import config

logger = logging.getLogger(__name__)


class StyleRandomizer:
    """스타일 요소를 랜덤화하는 클래스"""
    
    def __init__(self, seed=None):
        """
        초기화
        
        Args:
            seed: 랜덤 시드 (재현성을 위해)
        """
        self.seed = seed or config.RANDOMIZATION_SEED
        if self.seed:
            random.seed(self.seed)
            logger.info(f"랜덤 시드 설정: {self.seed}")
    
    def get_random_layout(self) -> str:
        """
        랜덤 레이아웃 선택
        
        Returns:
            선택된 레이아웃 템플릿 파일명
        """
        layout = random.choice(config.LAYOUT_TEMPLATES)
        logger.info(f"선택된 레이아웃: {layout}")
        return layout
    
    def get_random_fonts(self) -> Dict[str, str]:
        """
        랜덤 폰트 조합 선택
        
        Returns:
            폰트 딕셔너리 (heading_font, body_font)
        """
        fonts = {
            'heading_font': random.choice(config.BRAND_FONTS['heading']),
            'body_font': random.choice(config.BRAND_FONTS['body']),
        }
        
        # 가끔 악센트 폰트를 heading으로 사용
        if random.random() < 0.2:
            fonts['heading_font'] = random.choice(config.BRAND_FONTS['accent'])
        
        logger.info(f"선택된 폰트: {fonts}")
        return fonts
    
    def get_random_colors(self) -> Dict[str, str]:
        """
        랜덤 컬러 팔레트 선택
        
        Returns:
            컬러 딕셔너리 (primary, secondary, neutral, accent)
        """
        colors = {
            'primary_color': random.choice(config.BRAND_COLORS['primary']),
            'secondary_color': random.choice(config.BRAND_COLORS['secondary']),
            'neutral_color': random.choice(config.BRAND_COLORS['neutral']),
            'accent_color': random.choice(config.BRAND_COLORS['accent']),
        }
        
        logger.info(f"선택된 컬러: {colors}")
        return colors
    
    def get_random_image_position(self) -> str:
        """
        랜덤 이미지 배치 선택
        
        Returns:
            이미지 배치 위치
        """
        position = random.choice(config.IMAGE_POSITIONS)
        logger.info(f"선택된 이미지 배치: {position}")
        return position
    
    def get_random_text_tone(self) -> str:
        """
        랜덤 텍스트 톤 선택
        
        Returns:
            텍스트 톤 (formal, marketing, emotional)
        """
        tone = random.choice(config.TEXT_TONES)
        logger.info(f"선택된 텍스트 톤: {tone}")
        return tone
    
    def get_complete_style(self) -> Dict[str, any]:
        """
        완전한 스타일 세트 생성
        
        Returns:
            모든 스타일 요소를 포함하는 딕셔너리
        """
        style = {
            'layout': self.get_random_layout(),
            'image_position': self.get_random_image_position(),
            'text_tone': self.get_random_text_tone(),
        }
        
        # 폰트와 컬러 추가
        style.update(self.get_random_fonts())
        style.update(self.get_random_colors())
        
        logger.info("완전한 스타일 세트 생성 완료")
        return style
    
    def get_weighted_layout(self, weights: Dict[str, float] = None) -> str:
        """
        가중치를 적용한 레이아웃 선택
        
        Args:
            weights: 레이아웃별 가중치 딕셔너리
            
        Returns:
            선택된 레이아웃
        """
        if not weights:
            return self.get_random_layout()
        
        layouts = list(weights.keys())
        weight_values = list(weights.values())
        
        layout = random.choices(layouts, weights=weight_values, k=1)[0]
        logger.info(f"가중치 적용 레이아웃 선택: {layout}")
        return layout
    
    def ensure_diversity(self, recent_styles: List[Dict], max_similar: int = 2) -> Dict[str, any]:
        """
        최근 사용된 스타일과 다양성을 보장
        
        Args:
            recent_styles: 최근 사용된 스타일 리스트
            max_similar: 허용 가능한 최대 유사 횟수
            
        Returns:
            다양성이 보장된 스타일
        """
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            style = self.get_complete_style()
            
            # 최근 스타일과 비교
            similar_count = 0
            for recent in recent_styles[-5:]:  # 최근 5개만 확인
                if recent.get('layout') == style['layout']:
                    similar_count += 1
            
            if similar_count < max_similar:
                logger.info(f"다양성 보장 완료 (시도 횟수: {attempts + 1})")
                return style
            
            attempts += 1
        
        logger.warning("다양성 보장 실패, 기본 스타일 반환")
        return style
    
    def get_style_hash(self, style: Dict[str, any]) -> str:
        """
        스타일의 해시값 생성 (중복 확인용)
        
        Args:
            style: 스타일 딕셔너리
            
        Returns:
            해시 문자열
        """
        key_elements = [
            style.get('layout', ''),
            style.get('primary_color', ''),
            style.get('heading_font', ''),
        ]
        return '|'.join(key_elements)
    
    def reset_seed(self, new_seed=None):
        """
        랜덤 시드 재설정
        
        Args:
            new_seed: 새로운 시드값
        """
        self.seed = new_seed
        if self.seed:
            random.seed(self.seed)
            logger.info(f"랜덤 시드 재설정: {self.seed}")
        else:
            random.seed()
            logger.info("랜덤 시드 초기화")
