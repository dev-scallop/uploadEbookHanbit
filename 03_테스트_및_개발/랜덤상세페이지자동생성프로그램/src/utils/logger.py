"""
유틸리티 모듈
"""
import logging
import logging.config
from pathlib import Path

import config


def setup_logger():
    """로거 설정"""
    # 로그 디렉토리 생성
    log_dir = config.BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일 경로 업데이트
    log_file = log_dir / 'automation.log'
    if 'file' in config.LOGGING_CONFIG['handlers']:
        config.LOGGING_CONFIG['handlers']['file']['filename'] = str(log_file)
    
    # 로거 설정 적용
    logging.config.dictConfig(config.LOGGING_CONFIG)
    
    logger = logging.getLogger(__name__)
    logger.info("로거 설정 완료")
    
    return logger
