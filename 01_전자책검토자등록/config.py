"""
Google Play Console 전자책 검토자 등록을 위한 고급 설정 파일
실제 Google Play Console 구조에 맞춘 셀렉터 및 설정
"""

# Google Play Console 관련 URL
GOOGLE_PLAY_CONSOLE_BASE_URL = "https://play.google.com/console/"
GOOGLE_PLAY_DEVELOPER_CONSOLE = "https://play.google.com/console/u/0/developers/"
GOOGLE_PLAY_BOOKS_PARTNER_CENTER = "https://play.google.com/books/publish/u/0/?hl=ko"

# --- Google 스프레드시트 설정 ---
# '링크가 있는 모든 사용자에게 공개'로 설정된 Google 스프레드시트의 URL을 입력하세요.
# URL 형식: https://docs.google.com/spreadsheets/d/{스프레드시트_ID}/export?format=csv
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/18uXAoTIz07WEBzFgCYC5asaOUkLujYgQtezDsmPWiGY/export?format=csv&gid=0" # <--- 여기에 실제 스프레드시트 URL을 입력하세요.
# ------------------------------------

# 로그인 관련 설정
LOGIN_TIMEOUT = 300  # 5분
ELEMENT_WAIT_TIMEOUT = 15  # 15초
REQUEST_DELAY = 2  # 요청 간 대기 시간

# 크롬 드라이버 설정
# 직접 크롬 드라이버 경로를 지정하려면 아래 주석을 해제하고 경로를 입력하세요
# CHROME_DRIVER_PATH = r"C:\path\to\chromedriver.exe"  # 윈도우 예시

# 크롬 브라우저 옵션 (주석을 해제하여 원하는 옵션 활성화)
CHROME_OPTIONS = [
    "--disable-web-security", 
    "--disable-features=VizDisplayCompositor",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    # "--headless",  # 브라우저 창 없이 실행 (백그라운드 모드)
    # "--disable-gpu",  # GPU 사용 안 함
    # "--window-size=1920,1080"  # 창 크기 설정
]

# CSS 셀렉터 및 XPath 설정
SELECTORS = {
    # 로그인 확인
    'account_menu': [
        "[data-testid='account-menu-button']",
        ".gb_d",
        "#gb_70",
        ".gb_b.gb_9a.gb_R"
    ],
    
    # 앱/도서 검색
    'search_box': [
        "input[type='search']",
        "input[placeholder*='검색']",
        "input[placeholder*='Search']",
        "input[aria-label*='Search']",
        ".devsite-searchbox input",
        "#searchbox input"
    ],
    
    # 도서 링크
    'book_links': [
        "//a[contains(@href, '/console/') and contains(text(), '{}')]",
        "//div[contains(@class, 'app-title') and contains(text(), '{}')]/parent::*/parent::*//a",
        "//span[contains(text(), '{}')]/ancestor::a",
        "//td[contains(text(), '{}')]/parent::tr//a"
    ],
    
    # 검토자/테스터 관리
    'reviewer_section': [
        "//a[contains(text(), '검토자') or contains(text(), 'Reviewer')]",
        "//a[contains(text(), '테스터') or contains(text(), 'Tester')]",
        "//button[contains(text(), '검토자') or contains(text(), 'Reviewer')]",
        "//span[contains(text(), '검토자') or contains(text(), 'Reviewer')]/parent::*",
        "//a[contains(@href, 'testers')]",
        "//a[contains(@href, 'reviewer')]"
    ],
    
    # 검토자 추가 버튼
    'add_reviewer_button': [
        "//button[contains(text(), '추가') or contains(text(), 'Add')]",
        "//button[contains(text(), '검토자 추가')]",
        "//a[contains(text(), '추가') or contains(text(), 'Add')]",
        "//button[contains(@aria-label, '추가') or contains(@aria-label, 'Add')]",
        "//button[contains(text(), '초대') or contains(text(), 'Invite')]"
    ],
    
    # 이메일 입력 필드
    'email_input': [
        "input[type='email']",
        "input[placeholder*='이메일']",
        "input[placeholder*='email']",
        "input[name*='email']",
        "input[aria-label*='email']",
        "input[aria-label*='이메일']",
        "textarea[placeholder*='email']"
    ],
    
    # 저장/확인 버튼
    'save_button': [
        "//button[contains(text(), '저장') or contains(text(), 'Save')]",
        "//button[contains(text(), '추가') or contains(text(), 'Add')]",
        "//button[contains(text(), '확인') or contains(text(), 'OK')]",
        "//button[contains(text(), '초대') or contains(text(), 'Invite')]",
        "//button[contains(@type, 'submit')]"
    ]
}

# Chrome 브라우저 설정
CHROME_OPTIONS = [
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-translate",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding"
]

# 크롬 브라우저 경로 직접 지정 (설치 경로에 맞게 수정)
# 예시: CHROME_BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# 자동화 감지 방지 스크립트
ANTI_DETECTION_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
window.chrome = {runtime: {}};
"""

# 에러 메시지 매핑
ERROR_MESSAGES = {
    'book_not_found': '도서를 찾을 수 없습니다',
    'reviewer_section_not_found': '검토자 관리 섹션을 찾을 수 없습니다',
    'add_button_not_found': '검토자 추가 버튼을 찾을 수 없습니다',
    'email_input_not_found': '이메일 입력 필드를 찾을 수 없습니다',
    'save_button_not_found': '저장 버튼을 찾을 수 없습니다',
    'login_timeout': '로그인 시간이 초과되었습니다',
    'network_error': '네트워크 연결 오류가 발생했습니다'
}

# 성공률 임계값
SUCCESS_RATE_THRESHOLD = 0.95  # 95%
MAX_RETRY_ATTEMPTS = 3  # 최대 재시도 횟수

# 로그 설정
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
