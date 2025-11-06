"""
프로젝트 설정 파일
환경 변수와 브랜드 가이드라인을 관리합니다.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
load_dotenv()

# 기본 경로
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / os.getenv('OUTPUT_DIR', 'output')
HTML_OUTPUT_DIR = BASE_DIR / os.getenv('HTML_OUTPUT_DIR', 'output/html')
IMAGE_OUTPUT_DIR = BASE_DIR / os.getenv('IMAGE_OUTPUT_DIR', 'output/images')
TEMPLATES_DIR = BASE_DIR / 'templates'

# 디렉토리 생성
OUTPUT_DIR.mkdir(exist_ok=True)
HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BANNERBEAR_API_KEY = os.getenv('BANNERBEAR_API_KEY')
BANNERBEAR_TEMPLATE_ID = os.getenv('BANNERBEAR_TEMPLATE_ID')
PLACID_API_TOKEN = os.getenv('PLACID_API_TOKEN')
PLACID_TEMPLATE_ID = os.getenv('PLACID_TEMPLATE_ID')
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', '도서목록')
GOOGLE_SHEET_GID = os.getenv('GOOGLE_SHEET_GID', '0')
GOOGLE_SHEET_PUBLIC = os.getenv('GOOGLE_SHEET_PUBLIC', 'false').lower() in ('1', 'true', 'yes', 'y')

# WordPress 설정
WORDPRESS_URL = os.getenv('WORDPRESS_URL')
WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME')
WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD')

# Shopify 설정
SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_PASSWORD = os.getenv('SHOPIFY_API_PASSWORD')

# 브랜드 가이드라인 - 폰트
BRAND_FONTS = {
    'heading': [
        'Noto Serif KR',
        'Nanum Myeongjo',
        'Playfair Display'
    ],
    'body': [
        'Noto Sans KR',
        'Nanum Gothic',
        'Roboto'
    ],
    'accent': [
        'Pacifico',
        'Lobster',
        'Dancing Script'
    ]
}

# 브랜드 가이드라인 - 컬러 팔레트
BRAND_COLORS = {
    'primary': [
        '#2C3E50',  # 네이비
        '#34495E',  # 진한 회색
        '#1ABC9C',  # 청록색
    ],
    'secondary': [
        '#E74C3C',  # 붉은색
        '#F39C12',  # 주황색
        '#9B59B6',  # 보라색
    ],
    'neutral': [
        '#ECF0F1',  # 밝은 회색
        '#BDC3C7',  # 중간 회색
        '#95A5A6',  # 어두운 회색
    ],
    'accent': [
        '#F1C40F',  # 노란색
        '#E67E22',  # 진한 주황색
        '#16A085',  # 청록 변형
    ]
}

# 레이아웃 템플릿 목록
LAYOUT_TEMPLATES = [
    'layout_premium.html',  # 새 프리미엄 디자인
    'layout_hero_left.html',
    'layout_hero_right.html',
    'layout_card_grid.html',
    'layout_banner_top.html',
    'layout_magazine.html',
    'layout_minimal.html',
    'layout_classic.html',
    'layout_modern.html',
]

# 텍스트 톤 옵션
TEXT_TONES = [
    'formal',      # 격식체
    'marketing',   # 마케팅체
    'emotional',   # 감성체
]

# 이미지 배치 옵션
IMAGE_POSITIONS = [
    'left',
    'right',
    'center',
    'top',
    'background',
]

# AI 생성 설정
AI_SETTINGS = {
    'text_variations': 3,  # 생성할 텍스트 변형 수
    'image_variations': 2,  # 생성할 이미지 변형 수
    'max_tokens': 1000,     # OpenAI 최대 토큰
    'temperature': 0.8,     # 창의성 수준
}

# 랜덤화 설정
RANDOMIZATION_SEED = os.getenv('RANDOMIZATION_SEED')
if RANDOMIZATION_SEED and RANDOMIZATION_SEED.lower() != 'none':
    RANDOMIZATION_SEED = int(RANDOMIZATION_SEED)
else:
    RANDOMIZATION_SEED = None

MIN_TEMPLATE_DIVERSITY = float(os.getenv('MIN_TEMPLATE_DIVERSITY', 0.8))

# 도서 데이터 필드
BOOK_FIELDS = [
    'isbn',
    'title',
    'author',
    'publisher',
    'publish_date',
    'price',
    'keywords',
    'description',
    'table_of_contents',
    'cover_image_url',
]

# 로깅 설정
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'automation.log',
            'formatter': 'standard',
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}
