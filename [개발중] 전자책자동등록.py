"""
전자책 검토자 자동 등록 시스템
Google Partners Center에서 전자책 검토자를 자동으로 등록하는 프로그램

Author: AI Assistant
Date: 2025-09-14
Version: 1.0.0
"""

import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import logging
from datetime import datetime
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# 설정 파일 import
try:
    from config import *
except ImportError:
    # config.py가 없는 경우 기본 설정 사용
    GOOGLE_PLAY_CONSOLE_BASE_URL = "https://play.google.com/console/"
    LOGIN_TIMEOUT = 300
    ELEMENT_WAIT_TIMEOUT = 15
    REQUEST_DELAY = 2


class EbookReviewerAutoRegister:
    """전자책 검토자 자동 등록 클래스"""
    
    def __init__(self):
        self.setup_logging()
        self.driver = None
        self.is_logged_in = False
        self.registration_results = []
        
    def setup_logging(self):
        """로깅 설정"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_filename = f"ebook_registration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = os.path.join(log_dir, log_filename)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filepath, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("전자책 검토자 자동 등록 시스템 시작")
    
    def read_excel_file(self, file_path):
        """엑셀 파일을 읽어서 데이터 반환"""
        try:
            # 엑셀 파일 읽기 (여러 확장자 지원)
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)
            
            self.logger.info(f"엑셀 파일 읽기 성공: {file_path}")
            self.logger.info(f"총 {len(df)}개의 행이 발견됨")
            
            # 필수 컬럼 확인
            required_columns = ['이름', '도서명', '지메일']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"필수 컬럼이 누락됨: {missing_columns}")
            
            # 빈 행 제거
            df = df.dropna(subset=['도서명', '지메일'])
            
            self.logger.info(f"유효한 데이터: {len(df)}개 행")
            return df
            
        except Exception as e:
            self.logger.error(f"엑셀 파일 읽기 실패: {str(e)}")
            raise
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            chrome_options = Options()
            
            # config.py에서 옵션 가져오기
            if 'CHROME_OPTIONS' in globals():
                for option in CHROME_OPTIONS:
                    chrome_options.add_argument(option)
            else:
                # 기본 옵션
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 사용자 데이터 디렉토리 설정 (세션 유지용)
            user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 자동화 감지 방지
            anti_detection_script = getattr(globals().get('config', None), 'ANTI_DETECTION_SCRIPT', 
                                          "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script(anti_detection_script)
            
            self.logger.info("Chrome 드라이버 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"드라이버 설정 실패: {str(e)}")
            return False
    
    def login_to_google(self, email=None, password=None):
        """Google 계정 로그인"""
        try:
            # Google Play Console 로그인 페이지로 이동
            console_url = getattr(globals().get('config', None), 'GOOGLE_PLAY_CONSOLE_BASE_URL', 
                                "https://play.google.com/console/")
            self.driver.get(console_url)
            
            # 기존 세션이 있는지 확인
            wait_timeout = getattr(globals().get('config', None), 'ELEMENT_WAIT_TIMEOUT', 10)
            wait = WebDriverWait(self.driver, wait_timeout)
            
            try:
                # 계정 메뉴 셀렉터들 시도
                account_selectors = getattr(globals().get('config', None), 'SELECTORS', {}).get('account_menu', 
                                          ["[data-testid='account-menu-button']"])
                
                for selector in account_selectors:
                    try:
                        if selector.startswith('//'):
                            wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                        else:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        self.is_logged_in = True
                        self.logger.info("기존 세션으로 로그인 성공")
                        return True
                    except TimeoutException:
                        continue
                        
            except TimeoutException:
                pass
            
            # 로그인이 필요한 경우
            self.logger.info("Google 로그인이 필요합니다. 브라우저에서 수동으로 로그인해주세요.")
            
            # 사용자가 수동으로 로그인할 때까지 대기
            login_timeout = getattr(globals().get('config', None), 'LOGIN_TIMEOUT', 300)
            start_time = time.time()
            
            while time.time() - start_time < login_timeout:
                try:
                    # 로그인 완료 확인
                    for selector in account_selectors:
                        try:
                            if selector.startswith('//'):
                                self.driver.find_element(By.XPATH, selector)
                            else:
                                self.driver.find_element(By.CSS_SELECTOR, selector)
                            self.is_logged_in = True
                            self.logger.info("수동 로그인 완료")
                            return True
                        except NoSuchElementException:
                            continue
                    time.sleep(2)
                except Exception:
                    time.sleep(2)
                    continue
            
            self.logger.error("로그인 시간 초과")
            return False
            
        except Exception as e:
            self.logger.error(f"로그인 실패: {str(e)}")
            return False
    
    def search_book(self, book_title):
        """도서 검색"""
        try:
            self.logger.info(f"도서 검색 시작: {book_title}")
            
            # Google Play Console 메인 페이지로 이동
            self.driver.get("https://play.google.com/console/")
            
            wait = WebDriverWait(self.driver, 15)
            
            # 앱/도서 목록으로 이동
            try:
                apps_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/console/u/0/developers/')]")))
                apps_link.click()
            except TimeoutException:
                self.logger.warning("앱 목록 링크를 찾을 수 없음. 대체 방법 시도")
                self.driver.get("https://play.google.com/console/u/0/developers/")
            
            time.sleep(3)
            
            # 검색 기능 사용 (페이지에 검색 기능이 있는 경우)
            try:
                search_box = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='검색'], input[placeholder*='Search']")
                search_box.clear()
                search_box.send_keys(book_title)
                search_box.send_keys("\n")
                time.sleep(3)
            except NoSuchElementException:
                self.logger.info("검색 박스를 찾을 수 없음. 페이지에서 직접 도서를 찾습니다.")
            
            # 도서 목록에서 해당 도서 찾기
            book_elements = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{book_title}') or contains(@title, '{book_title}')]")
            
            if not book_elements:
                # 부분 일치로 재검색
                book_elements = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{book_title[:10]}')]")
            
            if book_elements:
                book_elements[0].click()
                self.logger.info(f"도서 '{book_title}' 발견 및 클릭")
                time.sleep(3)
                return True
            else:
                self.logger.warning(f"도서 '{book_title}'를 찾을 수 없음")
                return False
                
        except Exception as e:
            self.logger.error(f"도서 검색 실패: {str(e)}")
            return False
    
    def add_reviewer(self, email):
        """검토자 추가"""
        try:
            self.logger.info(f"검토자 추가 시작: {email}")
            
            wait = WebDriverWait(self.driver, 15)
            
            # 검토자 관리 섹션으로 이동
            try:
                # 여러 가능한 검토자 관리 링크 시도
                reviewer_links = [
                    "//a[contains(text(), '검토자') or contains(text(), 'Reviewer')]",
                    "//a[contains(text(), '테스터') or contains(text(), 'Tester')]",
                    "//button[contains(text(), '검토자') or contains(text(), 'Reviewer')]",
                    "//span[contains(text(), '검토자') or contains(text(), 'Reviewer')]/parent::*"
                ]
                
                reviewer_element = None
                for xpath in reviewer_links:
                    try:
                        reviewer_element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        break
                    except TimeoutException:
                        continue
                
                if reviewer_element:
                    reviewer_element.click()
                    time.sleep(3)
                else:
                    self.logger.warning("검토자 관리 섹션을 찾을 수 없음")
                    return False
                
            except Exception as e:
                self.logger.warning(f"검토자 섹션 이동 실패: {str(e)}")
                return False
            
            # 검토자 추가 버튼 클릭
            try:
                add_buttons = [
                    "//button[contains(text(), '추가') or contains(text(), 'Add')]",
                    "//button[contains(text(), '검토자 추가')]",
                    "//a[contains(text(), '추가') or contains(text(), 'Add')]"
                ]
                
                add_button = None
                for xpath in add_buttons:
                    try:
                        add_button = self.driver.find_element(By.XPATH, xpath)
                        break
                    except NoSuchElementException:
                        continue
                
                if add_button:
                    add_button.click()
                    time.sleep(2)
                else:
                    self.logger.warning("검토자 추가 버튼을 찾을 수 없음")
                    return False
                    
            except Exception as e:
                self.logger.warning(f"검토자 추가 버튼 클릭 실패: {str(e)}")
                return False
            
            # 이메일 입력 필드에 이메일 입력
            try:
                email_inputs = [
                    "input[type='email']",
                    "input[placeholder*='이메일']",
                    "input[placeholder*='email']",
                    "input[name*='email']"
                ]
                
                email_input = None
                for selector in email_inputs:
                    try:
                        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        break
                    except TimeoutException:
                        continue
                
                if email_input:
                    email_input.clear()
                    email_input.send_keys(email)
                    time.sleep(1)
                else:
                    self.logger.warning("이메일 입력 필드를 찾을 수 없음")
                    return False
                    
            except Exception as e:
                self.logger.warning(f"이메일 입력 실패: {str(e)}")
                return False
            
            # 저장/추가 버튼 클릭
            try:
                save_buttons = [
                    "//button[contains(text(), '저장') or contains(text(), 'Save')]",
                    "//button[contains(text(), '추가') or contains(text(), 'Add')]",
                    "//button[contains(text(), '확인') or contains(text(), 'OK')]"
                ]
                
                save_button = None
                for xpath in save_buttons:
                    try:
                        save_button = self.driver.find_element(By.XPATH, xpath)
                        break
                    except NoSuchElementException:
                        continue
                
                if save_button:
                    save_button.click()
                    time.sleep(3)
                    self.logger.info(f"검토자 '{email}' 추가 완료")
                    return True
                else:
                    self.logger.warning("저장 버튼을 찾을 수 없음")
                    return False
                    
            except Exception as e:
                self.logger.warning(f"저장 버튼 클릭 실패: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"검토자 추가 실패: {str(e)}")
            return False
    
    def process_registration(self, data_df, progress_callback=None):
        """전체 등록 프로세스 실행"""
        try:
            self.registration_results = []
            
            if not self.setup_driver():
                raise Exception("드라이버 설정 실패")
            
            if not self.login_to_google():
                raise Exception("Google 로그인 실패")
            
            total_count = len(data_df)
            
            for index, row in data_df.iterrows():
                try:
                    name = row['이름']
                    book_title = row['도서명']
                    email = row['지메일']
                    
                    self.logger.info(f"처리 중 ({index + 1}/{total_count}): {name} - {book_title} - {email}")
                    
                    # 진행률 업데이트
                    if progress_callback:
                        progress_callback(index + 1, total_count, f"처리 중: {book_title}")
                    
                    # 도서 검색
                    if not self.search_book(book_title):
                        result = {
                            'name': name,
                            'book_title': book_title,
                            'email': email,
                            'status': 'FAILED',
                            'error': '도서를 찾을 수 없음'
                        }
                        self.registration_results.append(result)
                        continue
                    
                    # 검토자 추가
                    if self.add_reviewer(email):
                        result = {
                            'name': name,
                            'book_title': book_title,
                            'email': email,
                            'status': 'SUCCESS',
                            'error': None
                        }
                    else:
                        result = {
                            'name': name,
                            'book_title': book_title,
                            'email': email,
                            'status': 'FAILED',
                            'error': '검토자 추가 실패'
                        }
                    
                    self.registration_results.append(result)
                    
                    # 요청 간격 조정 (너무 빠른 요청 방지)
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"행 처리 실패 ({index + 1}): {str(e)}")
                    result = {
                        'name': row.get('이름', 'Unknown'),
                        'book_title': row.get('도서명', 'Unknown'),
                        'email': row.get('지메일', 'Unknown'),
                        'status': 'FAILED',
                        'error': str(e)
                    }
                    self.registration_results.append(result)
            
            # 결과 요약
            success_count = len([r for r in self.registration_results if r['status'] == 'SUCCESS'])
            failed_count = len([r for r in self.registration_results if r['status'] == 'FAILED'])
            
            self.logger.info(f"등록 완료 - 성공: {success_count}, 실패: {failed_count}")
            
            return self.registration_results
            
        except Exception as e:
            self.logger.error(f"등록 프로세스 실패: {str(e)}")
            raise
        finally:
            if self.driver:
                try:
                    # 브라우저를 완전히 닫지 않고 세션 유지
                    # self.driver.quit()
                    pass
                except:
                    pass
    
    def save_results(self, output_file="registration_results.xlsx"):
        """결과를 엑셀 파일로 저장"""
        try:
            if not self.registration_results:
                self.logger.warning("저장할 결과가 없습니다.")
                return False
            
            df_results = pd.DataFrame(self.registration_results)
            
            # 결과 파일명에 타임스탬프 추가
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"registration_results_{timestamp}.xlsx"
            
            df_results.to_excel(output_file, index=False, encoding='utf-8')
            self.logger.info(f"결과 저장 완료: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"결과 저장 실패: {str(e)}")
            return False


class EbookRegistrationGUI:
    """전자책 검토자 등록 GUI 클래스"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("전자책 검토자 자동 등록 시스템")
        self.root.geometry("800x600")
        
        self.registerer = EbookReviewerAutoRegister()
        self.excel_file_path = None
        self.data_df = None
        
        self.setup_gui()
    
    def setup_gui(self):
        """GUI 구성 요소 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="전자책 검토자 자동 등록 시스템", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 파일 선택 섹션
        file_frame = ttk.LabelFrame(main_frame, text="1. 엑셀 파일 선택", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_frame, text="파일 경로:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=60, state="readonly").grid(row=0, column=1, padx=(10, 5))
        ttk.Button(file_frame, text="파일 선택", command=self.select_file).grid(row=0, column=2)
        
        # 데이터 미리보기
        preview_frame = ttk.LabelFrame(main_frame, text="2. 데이터 미리보기", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 트리뷰로 데이터 표시
        columns = ('이름', '도서명', '지메일')
        self.tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200, anchor='center')
        
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 실행 섹션
        execute_frame = ttk.LabelFrame(main_frame, text="3. 등록 실행", padding="10")
        execute_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.execute_button = ttk.Button(execute_frame, text="등록 시작", command=self.start_registration, state="disabled")
        self.execute_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(execute_frame, text="중지", command=self.stop_registration, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # 진행률 표시
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(execute_frame, textvariable=self.progress_var).grid(row=0, column=2, padx=(20, 0))
        
        self.progress_bar = ttk.Progressbar(execute_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 로그 출력 섹션
        log_frame = ttk.LabelFrame(main_frame, text="4. 실행 로그", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 결과 저장 버튼
        self.save_button = ttk.Button(main_frame, text="결과 저장", command=self.save_results, state="disabled")
        self.save_button.grid(row=5, column=0, pady=(10, 0))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        execute_frame.columnconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.registration_thread = None
        self.stop_requested = False
    
    def select_file(self):
        """파일 선택 대화상자"""
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.excel_file_path = file_path
            self.file_path_var.set(file_path)
            self.load_data_preview()
    
    def load_data_preview(self):
        """데이터 미리보기 로드"""
        try:
            self.data_df = self.registerer.read_excel_file(self.excel_file_path)
            
            # 기존 데이터 제거
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 새 데이터 추가 (최대 100행까지만 표시)
            for index, row in self.data_df.head(100).iterrows():
                self.tree.insert('', 'end', values=(row['이름'], row['도서명'], row['지메일']))
            
            self.execute_button.config(state="normal")
            
            self.log_message(f"데이터 로드 완료: {len(self.data_df)}개 행")
            
            if len(self.data_df) > 100:
                self.log_message("미리보기는 첫 100개 행만 표시됩니다.")
                
        except Exception as e:
            messagebox.showerror("오류", f"파일 읽기 실패:\n{str(e)}")
            self.log_message(f"파일 읽기 실패: {str(e)}")
    
    def log_message(self, message):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current, total, status_text=""):
        """진행률 업데이트"""
        percentage = (current / total) * 100
        self.progress_bar['value'] = percentage
        
        progress_text = f"진행률: {current}/{total} ({percentage:.1f}%)"
        if status_text:
            progress_text += f" - {status_text}"
        
        self.progress_var.set(progress_text)
        self.root.update_idletasks()
    
    def start_registration(self):
        """등록 시작"""
        if not self.data_df is not None:
            messagebox.showerror("오류", "먼저 엑셀 파일을 선택해주세요.")
            return
        
        # 확인 대화상자
        if not messagebox.askyesno("확인", f"총 {len(self.data_df)}개의 검토자를 등록하시겠습니까?"):
            return
        
        self.stop_requested = False
        self.execute_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.save_button.config(state="disabled")
        
        # 별도 스레드에서 등록 실행
        self.registration_thread = threading.Thread(target=self.run_registration)
        self.registration_thread.daemon = True
        self.registration_thread.start()
    
    def run_registration(self):
        """등록 실행 (별도 스레드)"""
        try:
            self.log_message("등록 프로세스 시작...")
            
            results = self.registerer.process_registration(
                self.data_df,
                progress_callback=self.update_progress
            )
            
            # 결과 요약
            success_count = len([r for r in results if r['status'] == 'SUCCESS'])
            failed_count = len([r for r in results if r['status'] == 'FAILED'])
            
            self.log_message(f"등록 완료 - 성공: {success_count}, 실패: {failed_count}")
            
            # UI 업데이트
            self.root.after(0, self.registration_completed)
            
        except Exception as e:
            self.log_message(f"등록 실패: {str(e)}")
            self.root.after(0, self.registration_completed)
    
    def stop_registration(self):
        """등록 중지"""
        self.stop_requested = True
        self.log_message("등록 중지 요청됨...")
        self.stop_button.config(state="disabled")
    
    def registration_completed(self):
        """등록 완료 후 UI 업데이트"""
        self.execute_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.save_button.config(state="normal")
        
        self.progress_var.set("완료")
        self.progress_bar['value'] = 100
    
    def save_results(self):
        """결과 저장"""
        try:
            output_file = self.registerer.save_results()
            if output_file:
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{output_file}")
                self.log_message(f"결과 저장 완료: {output_file}")
            else:
                messagebox.showerror("오류", "결과 저장에 실패했습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"결과 저장 실패:\n{str(e)}")
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        # GUI 실행
        app = EbookRegistrationGUI()
        app.run()
        
    except Exception as e:
        print(f"프로그램 실행 오류: {str(e)}")
        input("아무 키나 눌러 종료...")


if __name__ == "__main__":
    main()
