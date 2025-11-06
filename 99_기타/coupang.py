import time
import random
import atexit
import warnings
import sys
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import subprocess
import json
import requests
import tempfile
import re
from selenium.common.exceptions import InvalidSessionIdException, NoSuchWindowException

# undetected-chromedriver의 cleanup 경고 억제
warnings.filterwarnings("ignore", category=DeprecationWarning)

# __del__ 예외를 출력하지 않도록 후킹
def _silent_excepthook(exc_type, exc_value, exc_traceback):
    """__del__에서 발생하는 OSError 무시"""
    if exc_type == OSError and "핸들이 잘못되었습니다" in str(exc_value):
        return  # 무시
    # 다른 예외는 기본 핸들러로 처리
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = _silent_excepthook

try:
    import tkinter as tk
    from tkinter import messagebox
    _have_tk = True
except Exception:
    _have_tk = False

# playsound이 설치되어 있으면 사용하고, 없으면 OS 기본 열기로 대체
try:
    from playsound import playsound  # type: ignore
    _have_playsound = True
except Exception:
    playsound = None
    _have_playsound = False

def play_sound(path: str) -> None:
    """알림음 재생: playsound가 있으면 사용하고, 없으면 OS 기본 프로그램으로 연다."""
    if _have_playsound and playsound is not None:
        try:
            playsound(path)
            return
        except Exception as e:
            print("playsound 재생 중 오류:", e)

    # fallback: Windows는 os.startfile, macOS는 open, Linux는 xdg-open
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print("🔔 알림음 재생 실패 (파일 확인 필요):", e)


# Telegram 설정 로드 및 메시지 전송
_telegram_checked = False  # getMe로 토큰 1회 검증 캐시

def _validate_telegram_token(token: str) -> bool:
    """텔레그램 토큰 형식 검증: 숫자:문자열 패턴"""
    if not isinstance(token, str):
        return False
    token = token.strip()
    # 일반적인 토큰 패턴: bot_id(숫자 6자리 이상) : 키(영숫자/언더스코어/대시)
    return re.match(r"^\d{6,}:[A-Za-z0-9_-]{10,}$", token) is not None

def _sanitize_value(v):
    return str(v).strip() if isinstance(v, (str, int)) else v
def _load_telegram_config(verbose: bool = False):
    # 1) 환경변수 우선
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token:
        token = token.strip()
        # 사용자가 실수로 'bot' 접두사를 포함했을 경우 제거
        if token.lower().startswith("bot"):
            token = token[3:].strip()
    if chat_id:
        chat_id = str(chat_id).strip()
    if token and chat_id:
        if verbose:
            print("🔧 텔레그램 설정 감지(환경변수)")
        return token, chat_id
    # 2) json 파일에서 읽기 (telegram_config.json)
    try:
        config_path = os.path.join(os.path.dirname(__file__), "telegram_config.json")
        if os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                token_f = _sanitize_value(data.get("token"))
                chat_id_f = _sanitize_value(data.get("chat_id"))
                # 파일에 'bot' 접두사가 포함된 경우 제거
                if isinstance(token_f, str) and token_f.lower().startswith("bot"):
                    token_f = token_f[3:].strip()
                if token_f and chat_id_f:
                    if verbose:
                        print(f"🔧 텔레그램 설정 감지(파일): {os.path.basename(config_path)}")
                    return token_f, str(chat_id_f)
                elif verbose:
                    print("⚠️ telegram_config.json이 있지만 token/chat_id 중 일부가 비어있습니다.")
    except Exception as e:
        if verbose:
            print("⚠️ telegram_config.json 읽기 예외:", e.__class__.__name__)
    if verbose:
        missing = []
        if not token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            print("⚠️ 환경변수에서 누락:", ", ".join(missing))
        else:
            print("⚠️ 환경변수/설정파일에서 텔레그램 설정을 찾지 못했습니다.")
    return None, None


def send_telegram_message(text: str, reply_markup: dict | None = None) -> bool:
    global _telegram_checked
    token, chat_id = _load_telegram_config(verbose=False)
    if not token or not chat_id:
        print("📭 텔레그램 설정이 없습니다. TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 환경변수나 telegram_config.json을 설정하세요.")
        return False
    # 공백 제거 및 형식 검증
    token = token.strip()
    chat_id = str(chat_id).strip()
    if not _validate_telegram_token(token):
        print("❌ 텔레그램 토큰 형식이 올바르지 않습니다. 예) 1234567890:ABCdefGhIjKLMN_opq — 'bot' 접두사나 공백/오타가 없는지 확인하세요.")
        return False
    try:
        # 최초 1회: 토큰 검증(getMe)
        if not _telegram_checked:
            me_url = f"https://api.telegram.org/bot{token}/getMe"
            me_resp = requests.get(me_url, timeout=10)
            if me_resp.status_code != 200 or not me_resp.json().get("ok"):
                print("❌ 텔레그램 토큰 검증 실패:", me_resp.text[:200])
                return False
            _telegram_checked = True

        # 텍스트 길이 제한(텔레그램 4096자). 너무 길면 앞부분만 전송
        if len(text) > 4000:
            text = text[:4000] + "\n... (생략)"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            # 상태코드별 가이드
            if resp.status_code == 404:
                print("⚠️ 404 Not Found: 토큰/URL 형식 문제가 의심됩니다. token 값에 'bot'을 붙이지 말고, 앞뒤 공백이나 '/' 같은 잘못된 문자가 없는지 확인하세요.")
            elif resp.status_code == 401:
                print("⚠️ 401 Unauthorized: 토큰이 잘못되었습니다. BotFather에서 새 토큰을 정확히 복사해 설정하세요.")
            elif resp.status_code == 400 and 'chat not found' in resp.text.lower():
                print("⚠️ 400 Chat not found: 봇과 1:1 대화를 먼저 시작하거나, 그룹/채널에 봇을 추가하고 메시지 권한을 부여하세요.")
            print("⚠️ 텔레그램 전송 실패:", resp.text)
            return False
        return True
    except Exception as e:
        print("⚠️ 텔레그램 전송 중 예외:", e.__class__.__name__)
        return False


def _try_fix_http2_error(driver, url: str, retries: int = 3, wait_sec: float = 2.0) -> None:
    """HTTP/2 프로토콜 오류 페이지가 보일 때 몇 차례 재시도한다."""
    for i in range(retries):
        try:
            html = driver.page_source or ""
        except Exception:
            html = ""
        if ("ERR_HTTP2_PROTOCOL_ERROR" in html) or ("사이트에 연결할 수 없음" in html):
            print(f"🌐 HTTP/2 오류 감지, 재시도 {i+1}/{retries}…")
            try:
                driver.get(url)
            except Exception as e:
                print("재시도 중 예외:", e)
            time.sleep(wait_sec)
        else:
            break

# ============ 설정 ============
URL = "https://www.coupang.com/"  # 사용자가 직접 로그인할 웹페이지 (쿠팡)
# 장바구니 수에 따라 클릭 대상이 바뀌므로 두 패턴을 모두 매칭 (XPath union)
# - 1개일 때: //*[@id="mainContent"]/div[2]/label/input
# - 2개 이상: //*[@id="mainContent"]/div[3]/label
CLICK_XPATH = '//*[@id="mainContent"]/div[3]/label | //*[@id="mainContent"]/div[2]/label/input'
WATCH_XPATH = '//*[@id="btnPay"]/span'
ALARM_FILE = "alarm.mp3"
# 알림 동작 설정
ALERT_BURST_COUNT = 3          # 최초 변화 시 연속 발송 횟수
ENABLE_PERIODIC = False        # 동일 내용 유지 시 주기 알림 사용 여부 (기본 비활성화)
PERIODIC_INTERVAL_SEC = 60     # 주기 알림 간격(초)
# ==============================

"""브라우저 옵션/프로필 설정"""
# 영구 사용자 프로필 경로(첫 실행 팝업/로그인 유지 등 안정성 향상)
PERSIST_PROFILE_DIR = os.path.join(os.path.dirname(__file__), ".uc_profile")
try:
    os.makedirs(PERSIST_PROFILE_DIR, exist_ok=True)
except Exception:
    pass

def _build_options():
    opts = uc.ChromeOptions()
    # opts.add_argument("--headless")  # 백그라운드 실행 시 사용
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    # 네트워크/프로토콜 관련 우회 설정
    opts.add_argument("--disable-quic")
    opts.add_argument("--disable-http2")
    opts.add_argument("--ignore-certificate-errors")
    # 한국어/UA 설정
    opts.add_argument("--lang=ko-KR")
    # 자동화 흔적 최소화 (undetected-chromedriver가 대부분 자동 처리)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--start-maximized")
    # 사용자 프로필 지정
    opts.add_argument(f"--user-data-dir={PERSIST_PROFILE_DIR}")
    return opts

# 전역 드라이버 변수 (종료 시 정리용)
_global_driver = None


def _cleanup_driver():
    """프로그램 종료 시 드라이버를 안전하게 정리"""
    global _global_driver
    if _global_driver:
        try:
            # 브라우저 프로세스를 직접 종료 (quit() 에러 회피)
            if hasattr(_global_driver, 'service') and _global_driver.service.process:
                _global_driver.service.process.kill()
        except Exception:
            pass
        try:
            # 그 다음 quit 시도 (이미 종료되었으면 무시)
            _global_driver.quit()
        except Exception:
            pass
        _global_driver = None


def _new_driver():
    """undetected-chromedriver로 드라이버 생성 (자동화 감지 우회 강화)"""
    global _global_driver
    # 매번 새로운 옵션 객체를 생성하여 재사용 오류 방지
    options = _build_options()
    # 크롬 버전이 로그에 142로 표시되었으므로 명시적으로 맞춤
    drv = uc.Chrome(options=options, version_main=142, user_data_dir=PERSIST_PROFILE_DIR, use_subprocess=True)
    _global_driver = drv
    return drv


# 프로그램 종료 시 자동 정리 등록
atexit.register(_cleanup_driver)

# ===== 텔레그램 ACK(읽음 대체) 처리 =====
_tg_update_offset: int | None = None
current_alert_id: str | None = None
current_alert_acked: bool = False
should_exit: bool = False

def _poll_telegram_updates():
    """텔레그램 getUpdates로 콜백/메시지 확인 (웹훅 미사용 가정)."""
    global _tg_update_offset
    token, chat_id = _load_telegram_config(verbose=False)
    if not token or not chat_id:
        return []
    params = {
        "timeout": 0,
    }
    if _tg_update_offset is not None:
        params["offset"] = _tg_update_offset
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        r = requests.get(url, params=params, timeout=10)
        data = r.json() if r.status_code == 200 else {}
        updates = data.get("result", [])
        # offset 갱신
        if updates:
            _tg_update_offset = updates[-1]["update_id"] + 1
        return updates
    except Exception:
        return []

def _answer_callback_query(callback_query_id: str, text: str = "알림이 중지되었습니다."):
    token, _ = _load_telegram_config(verbose=False)
    if not token:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        requests.post(url, json={"callback_query_id": callback_query_id, "text": text, "show_alert": False}, timeout=10)
    except Exception:
        pass

def _process_ack_updates(target_alert_id: str | None, allowed_chat_id: str | None):
    """업데이트 스트림에서 ack를 찾아 현재 알림에 대한 중지 플래그 설정."""
    global current_alert_acked, should_exit
    if not target_alert_id:
        return
    for upd in _poll_telegram_updates() or []:
        # callback_query 통한 버튼 클릭
        cq = upd.get("callback_query")
        if cq:
            from_chat = str(cq.get("from", {}).get("id"))
            data = cq.get("data") or ""
            if allowed_chat_id and from_chat != str(allowed_chat_id):
                continue
            if isinstance(data, str) and data.startswith("ack:"):
                ack_id = data.split(":", 1)[1]
                if ack_id == target_alert_id:
                    current_alert_acked = True
                    _answer_callback_query(str(cq.get("id")))
                    should_exit = True
                    return
        # 메시지 텍스트로 ack 처리 (/ack 또는 확인 등)
        msg = upd.get("message") or {}
        if msg:
            from_chat = str(msg.get("chat", {}).get("id"))
            text = (msg.get("text") or "").strip().lower()
            if allowed_chat_id and from_chat != str(allowed_chat_id):
                continue
            if text in ("/ack", "ack", "확인", "읽음", "stop"):
                current_alert_acked = True
                should_exit = True
                return

def _inline_ack_kb(alert_id: str) -> dict:
    return {"inline_keyboard": [[{"text": "확인(알림중지)", "callback_data": f"ack:{alert_id}"}]]}


def _human_like_click(driver, xpath: str, description: str = "요소") -> bool:
    """사람처럼 클릭: 스크롤 → 마우스 이동 → 랜덤 대기 → 클릭"""
    try:
        # 요소가 나타날 때까지 최대 10초 대기
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        
        # 요소가 보이도록 스크롤
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(random.uniform(0.3, 0.8))  # 스크롤 후 잠깐 대기
        
        # 마우스를 요소로 이동 (hover 효과)
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(random.uniform(0.2, 0.5))  # 마우스 이동 후 대기
        
        # 클릭 가능할 때까지 대기(실패 시 기존 element로 JS 클릭 시도)
        try:
            element = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
        except Exception:
            pass
        
        # JavaScript 클릭 (일반 클릭보다 안정적)
        driver.execute_script("arguments[0].click();", element)
        
        return True
    except Exception as e:
        print(f"❌ {description} 클릭 실패: {e.__class__.__name__}")
        return False


driver = _new_driver()

# 드라이버 안정화 대기 (창이 완전히 열릴 때까지)
time.sleep(2)

# 브라우저 창 최대화 (일반 사용자처럼 보이게)
try:
    driver.maximize_window()
except Exception:
    pass

# 페이지 로드 타임아웃 설정
try:
    driver.set_page_load_timeout(30)
except Exception:
    pass

# 초기 페이지 로드 (재시도 로직 포함)
max_retries = 5
for attempt in range(max_retries):
    try:
        driver.get(URL)
        _try_fix_http2_error(driver, URL)
        print(f"✅ 페이지 로드 성공 (시도 {attempt + 1}/{max_retries})")
        break
    except (NoSuchWindowException, InvalidSessionIdException) as e:
        print(f"🪟 창/세션 오류로 드라이버 재생성 (시도 {attempt + 1}/{max_retries}): {e.__class__.__name__}")
        try:
            if hasattr(driver, 'service') and driver.service.process:
                driver.service.process.kill()
        except Exception:
            pass
        try:
            driver.quit()
        except Exception:
            pass
        driver = _new_driver()
        time.sleep(2)
        continue
    except Exception as e:
        print(f"⚠️ 페이지 로드 실패 (시도 {attempt + 1}/{max_retries}): {e.__class__.__name__}")
        if attempt < max_retries - 1:
            print("재시도 중...")
            time.sleep(3)
            continue
        else:
            print("❌ 페이지 로드 최종 실패. 프로그램을 종료합니다.")
            _cleanup_driver()
            sys.exit(1)

# 페이지 완전 로드 대기 (자바스크립트 실행 시간 확보)
time.sleep(5)

print("🔐 쿠팡 로그인 페이지가 열렸습니다.")
print("👉 브라우저에서 직접 로그인하고, 감시할 페이지로 이동하세요.")

# Enter 대신 팝업 '확인'으로 진행
if _have_tk:
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        messagebox.showinfo(
            "준비 완료?",
            "브라우저에서 쿠팡에 로그인하고\n감시할 페이지로 이동한 뒤\n확인 버튼을 누르면 시작합니다.",
        )
        root.destroy()
    except Exception as e:
        print("❗ 알림창 표시 실패:", e)
        input("로그인과 페이지 이동을 마쳤다면 Enter를 눌러 시작합니다.\n")
else:
    input("브라우저에서 로그인과 페이지 이동을 마친 후 Enter를 눌러 시작합니다.\n")

# 초기 감시 대상 텍스트 저장
try:
    target_element = driver.find_element(By.XPATH, WATCH_XPATH)
    previous_text = target_element.text.strip()
    print(f"초기 감시 내용: {previous_text}")
except Exception as e:
    # 상세 스택 대신 짧은 형식으로만 출력
    print("❌ 감시 대상 초기화 실패:", e.__class__.__name__)
    previous_text = ""

print("✅ 감시 및 자동 클릭을 시작합니다...")

# 알림 전송 제어 변수
alert_active = False          # 알림 활성 상태 (최초 변화 감지 이후 True)
last_alert_text = None        # 마지막으로 알림을 보낸 감시 텍스트 값
last_send_ts = 0.0            # 마지막 알림 전송 시각(epoch)

while True:
    try:
        # 1️⃣ 사람처럼 클릭 시도 (스크롤 + 마우스 이동 + 대기)
        _human_like_click(driver, CLICK_XPATH, "클릭 대상")

        # 2️⃣ 감시 영역 텍스트 비교
        watch_el = driver.find_element(By.XPATH, WATCH_XPATH)
        current_text = watch_el.text.strip()

        # 새로운 변화 감지: 초기 3회 발송 후 1분 주기 알림(읽음 ACK 시 중지)
        if last_alert_text != current_text:
            print("⚠️ 페이지 내용이 변경되었습니다!")
            # 새 알림 ID 생성 및 ACK 초기화
            current_alert_id = str(int(time.time()))
            current_alert_acked = False
            kb = _inline_ack_kb(current_alert_id)
            msg = (
                "[쿠팡 감시 알림]\n"
                "링크: https://kxowls.github.io/coupang-cart/\n"
                f"변경된 내용: {current_text}"
            )
            for _ in range(ALERT_BURST_COUNT):
                send_telegram_message(msg, reply_markup=kb)
                # 전송 사이에 ACK(확인 버튼/메시지) 수신 여부 확인
                _process_ack_updates(current_alert_id, _load_telegram_config(False)[1])
                if current_alert_acked or should_exit:
                    break
                time.sleep(0.4)
            alert_active = True
            last_alert_text = current_text
            last_send_ts = time.time()
            previous_text = current_text
            if should_exit:
                print("👋 사용자가 알림을 확인하여 프로그램을 종료합니다.")
                _cleanup_driver()
                sys.exit(0)
        else:
            # 변화 없음: 활성 상태면 ACK 확인 후 1분 간격 주기 알림
            _process_ack_updates(current_alert_id, _load_telegram_config(False)[1])
            if should_exit:
                print("👋 사용자가 알림을 확인하여 프로그램을 종료합니다.")
                _cleanup_driver()
                sys.exit(0)
            if ENABLE_PERIODIC and alert_active and (not current_alert_acked) and (time.time() - last_send_ts >= PERIODIC_INTERVAL_SEC):
                msg = (
                    "[쿠팡 감시 알림 - 주기]\n"
                    "링크: https://kxowls.github.io/coupang-cart/\n"
                    f"변경된 내용: {last_alert_text}\n"
                    "(1분 간격 알림)"
                )
                send_telegram_message(msg, reply_markup=_inline_ack_kb(current_alert_id))
                last_send_ts = time.time()
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 변경 없음")

    except InvalidSessionIdException:
        print("🔄 브라우저 세션이 만료되어 복구를 시도합니다…")
        try:
            if hasattr(driver, 'service') and driver.service.process:
                driver.service.process.kill()
        except Exception:
            pass
        try:
            driver.quit()
        except Exception:
            pass
        driver = _new_driver()
        try:
            driver.get(URL)
            _try_fix_http2_error(driver, URL)
        except Exception:
            pass
        continue
    except NoSuchWindowException:
        print("🪟 브라우저 창이 닫혀 세션을 재생성합니다…")
        try:
            if hasattr(driver, 'service') and driver.service.process:
                driver.service.process.kill()
        except Exception:
            pass
        try:
            driver.quit()
        except Exception:
            pass
        driver = _new_driver()
        try:
            driver.get(URL)
            _try_fix_http2_error(driver, URL)
        except Exception:
            pass
        continue
    except Exception as e:
        # 장황한 스택 메시지 대신 예외 타입만 출력하여 화면 오염 방지
        print(f"❗ 오류 발생: {e.__class__.__name__}")

    # 사람처럼 불규칙한 간격으로 반복 (0.8~1.5초)
    time.sleep(random.uniform(0.8, 1.5))
