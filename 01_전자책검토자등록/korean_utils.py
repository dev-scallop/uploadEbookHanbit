"""
한글 인코딩 처리 유틸리티 모듈
URL 인코딩/디코딩 및 깨진 한글 복원 기능 제공
"""

import urllib.parse
import logging

logger = logging.getLogger(__name__)

def fix_korean_encoding(text):
    """
    URL 인코딩된 문자열 또는 깨진 한글을 UTF-8로 복원
    
    Args:
        text: 처리할 문자열
    
    Returns:
        복원된 UTF-8 문자열
    """
    if not isinstance(text, str) or not text:
        return text
        
    result = text
    
    # URL 디코딩
    if '%' in result:
        try:
            result = urllib.parse.unquote(result)
            # 한 번 더 디코딩 (중복 인코딩된 경우)
            if '%' in result:
                result = urllib.parse.unquote(result)
        except Exception as e:
            logger.warning(f"URL 디코딩 실패: {e}")
    
    # 깨진 한글 감지 및 복원
    try:
        if any(c > '\u007F' for c in result) and any(c in result for c in 'ë¥¼íì©íìëë¡ì´ëíë¡ê·¸ëë°çðéèäö'):
            # 깨진 한글 탐지됨, UTF-8로 변환 시도
            bytes_val = result.encode('latin1', errors='replace')
            result = bytes_val.decode('utf-8', errors='replace')
            logger.debug(f"한글 복원: '{text}' -> '{result}'")
    except Exception as e:
        logger.warning(f"한글 복원 실패: {e}")
        
    return result

def ensure_utf8(content, source_encoding=None):
    """
    주어진 내용이 UTF-8이 되도록 보장
    
    Args:
        content: 바이트 또는 문자열 내용
        source_encoding: 소스 인코딩 (없으면 자동 감지)
    
    Returns:
        UTF-8로 변환된 문자열
    """
    if isinstance(content, str):
        return content
        
    if isinstance(content, bytes):
        # 인코딩이 지정되었으면 그걸 사용
        if source_encoding:
            try:
                return content.decode(source_encoding, errors='replace')
            except UnicodeDecodeError:
                pass
                
        # 여러 인코딩 시도
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
        for encoding in encodings:
            try:
                return content.decode(encoding, errors='replace')
            except UnicodeDecodeError:
                continue
                
    # 기본값
    return str(content)
