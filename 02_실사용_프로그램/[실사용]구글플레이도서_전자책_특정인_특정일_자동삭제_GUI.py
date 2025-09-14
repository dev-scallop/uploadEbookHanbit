import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import time
import os
import logging
from typing import List, Tuple, Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# CustomTkinter 테마 설정
ctk.set_appearance_mode("light")  # 라이트 모드
ctk.set_default_color_theme("blue")  # 파란색 테마

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('book_deletion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BookDeletionConstants:
    """애플리케이션 상수 정의"""
    
    # UI 관련 상수
    WINDOW_TITLE = "전자책 삭제 프로그램"
    WINDOW_SIZE = "900x700"
    
    # 웹 관련 상수
    BASE_URL = 'https://play.google.com/books/publish/u/0/?hl=ko'
    WAIT_TIME = 10  # 기본 대기 시간
    PAGE_LOAD_WAIT = 5  # 페이지 로딩 대기 시간
    DELETE_WAIT = 2  # 삭제 후 대기 시간
    RETRY_COUNT = 3  # 재시도 횟수
    
    # 셀렉터 상수
    EMAIL_XPATH = "//h4[@class='mat-mdc-list-item-title mdc-list-item__primary-text' and contains(text(),'{}')]"
    DELETE_BUTTON_XPATH = ".//button[@aria-label='삭제']"
    CONFIRM_SELECTORS = [
        "//button[contains(text(), '삭제')]",
        "//button[contains(text(), '확인')]",
        "//button[contains(text(), 'Delete')]",
        "//button[contains(text(), 'OK')]",
        "//button[contains(text(), 'Yes')]",
        "//button[contains(text(), '네')]",
        "//button[@aria-label='삭제']",
        "//button[@aria-label='확인']",
        "//button[@aria-label='Delete']",
        "//button[@aria-label='OK']",
        "//button[@type='submit']",
        "//button[contains(@class, 'confirm')]",
        "//button[contains(@class, 'delete')]"
    ]
    
    # 로그 레벨
    LOG_LEVELS = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️", 
        "ERROR": "❌",
        "SUMMARY": "📊"
    }
    
    # 파일 관련 상수
    EXCEL_FILETYPES = [("Excel 파일", "*.xlsx *.xls")]
    TEMPLATE_FILENAME = "book_deletion_template.xlsx"

class BookDeletionApp:
    """
    구글 플레이 도서에서 특정 사용자의 전자책을 자동으로 삭제하는 GUI 애플리케이션
    
    Features:
    - 엑셀 파일을 통한 배치 처리
    - 자동 크롬드라이버 관리
    - 실시간 진행률 표시
    - 상세한 로그 기록
    - 오류 복구 및 재시도 메커니즘
    """
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title(BookDeletionConstants.WINDOW_TITLE)
        self.root.geometry(BookDeletionConstants.WINDOW_SIZE)
        self.root.resizable(True, True)
        
        # 로거 초기화
        self.logger = logging.getLogger(__name__)
        
        # 변수 초기화
        self.chrome_driver_path: Optional[str] = None
        self.excel_file_path: Optional[str] = None
        self.driver: Optional[webdriver.Chrome] = None
        self.current_url: Optional[str] = None
        self.is_processing: bool = False
        self.cancel_requested: bool = False
        
        # 통계 변수
        self.total_processed: int = 0
        self.total_success: int = 0
        self.total_errors: int = 0
        
        self.create_widgets()
        
    def create_widgets(self):
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 헤더 섹션
        self.create_header_section(main_container)
        
        # 파일 선택 섹션
        self.create_file_section(main_container)
        
        # 드라이버 정보 섹션
        self.create_driver_section(main_container)
        
        # 진행률 섹션
        self.create_progress_section(main_container)
        
        # 로그 섹션
        self.create_log_section(main_container)
        
        # 버튼 섹션
        self.create_button_section(main_container)
        
    def create_header_section(self, parent):
        """헤더 섹션 생성"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # 제목
        title_label = ctk.CTkLabel(
            header_frame, 
            text="📚 전자책 삭제 프로그램",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1f538d", "#1f538d")
        )
        title_label.pack(pady=(0, 5))
        
        # 부제목
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="구글 플레이 도서에서 특정 사용자의 전자책을 자동으로 삭제합니다",
            font=ctk.CTkFont(size=14),
            text_color=("#666666", "#cccccc")
        )
        subtitle_label.pack()
        
    def create_file_section(self, parent):
        """파일 선택 섹션 생성"""
        file_frame = ctk.CTkFrame(parent, corner_radius=12)
        file_frame.pack(fill="x", pady=(0, 15))
        
        # 섹션 제목
        section_title = ctk.CTkLabel(
            file_frame,
            text="📁 파일 선택",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#1f538d")
        )
        section_title.pack(pady=(15, 10), padx=15, anchor="w")
        
        # 엑셀 파일 형식 안내
        format_info_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        format_info_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # 안내 제목
        info_title = ctk.CTkLabel(
            format_info_frame,
            text="📋 엑셀 파일 형식 안내",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#28a745", "#28a745")
        )
        info_title.pack(anchor="w", pady=(0, 5))
        
        # 형식 설명
        format_text = """• A열: 구글 플레이 도서 URL (필수)
• B열: 삭제할 사용자 이메일 주소 (필수)
• 첫 번째 행은 헤더로 사용 가능
• 데이터는 A2, B2부터 시작"""
        
        format_label = ctk.CTkLabel(
            format_info_frame,
            text=format_text,
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#cccccc"),
            justify="left"
        )
        format_label.pack(anchor="w", pady=(0, 10))
        
        # 예시 표
        example_frame = ctk.CTkFrame(format_info_frame, corner_radius=6)
        example_frame.pack(fill="x", pady=(0, 10))
        
        example_text = """예시:
A열: https://play.google.com/books/publish/u/0/book/123456789
B열: user@example.com"""
        
        example_label = ctk.CTkLabel(
            example_frame,
            text=example_text,
            font=ctk.CTkFont(size=10, family="Consolas"),
            text_color=("#495057", "#adb5bd"),
            justify="left"
        )
        example_label.pack(padx=10, pady=8, anchor="w")
        
        # 버튼 프레임
        button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # 엑셀 파일 선택 버튼
        select_btn = ctk.CTkButton(
            button_frame,
            text="📄 엑셀 파일 선택",
            command=self.select_excel,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8
        )
        select_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 템플릿 생성 버튼
        template_btn = ctk.CTkButton(
            button_frame,
            text="📋 템플릿 생성",
            command=self.create_template,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color=("#28a745", "#28a745"),
            hover_color=("#218838", "#218838")
        )
        template_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # 선택된 파일 표시
        self.excel_label = ctk.CTkLabel(
            file_frame,
            text="선택된 엑셀: 없음",
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#cccccc")
        )
        self.excel_label.pack(pady=(0, 15), padx=15, anchor="w")
        
    def create_driver_section(self, parent):
        """드라이버 정보 섹션 생성"""
        driver_frame = ctk.CTkFrame(parent, corner_radius=12)
        driver_frame.pack(fill="x", pady=(0, 15))
        
        # 섹션 제목
        section_title = ctk.CTkLabel(
            driver_frame,
            text="🚀 크롬드라이버 설정",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#1f538d")
        )
        section_title.pack(pady=(15, 10), padx=15, anchor="w")
        
        # 드라이버 정보
        info_frame = ctk.CTkFrame(driver_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 상태 아이콘과 텍스트
        status_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_frame.pack(fill="x")
        
        status_icon = ctk.CTkLabel(
            status_frame,
            text="✅",
            font=ctk.CTkFont(size=16)
        )
        status_icon.pack(side="left", padx=(0, 8))
        
        status_text = ctk.CTkLabel(
            status_frame,
            text="자동으로 관리됩니다",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#28a745", "#28a745")
        )
        status_text.pack(side="left")
        
        # 설명 텍스트
        desc_text = ctk.CTkLabel(
            info_frame,
            text="webdriver-manager가 자동으로 최신 버전을 다운로드하고 관리합니다",
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#cccccc")
        )
        desc_text.pack(anchor="w")
        
    def create_progress_section(self, parent):
        """진행률 섹션 생성"""
        progress_frame = ctk.CTkFrame(parent, corner_radius=12)
        progress_frame.pack(fill="x", pady=(0, 15))
        
        # 섹션 제목
        section_title = ctk.CTkLabel(
            progress_frame,
            text="📊 진행률",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#1f538d")
        )
        section_title.pack(pady=(15, 10), padx=15, anchor="w")
        
        # 진행률 바
        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            height=8,
            corner_radius=4
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 15))
        self.progress_bar.set(0)
        
    def create_log_section(self, parent):
        """로그 섹션 생성"""
        log_frame = ctk.CTkFrame(parent, corner_radius=12)
        log_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 섹션 제목
        section_title = ctk.CTkLabel(
            log_frame,
            text="📝 작업 로그",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#1f538d")
        )
        section_title.pack(pady=(15, 10), padx=15, anchor="w")
        
        # 로그 텍스트 영역
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=12),
            corner_radius=8
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def create_button_section(self, parent):
        """버튼 섹션 생성"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # 시작 버튼
        self.start_button = ctk.CTkButton(
            button_frame,
            text="🚀 작업 시작",
            command=self.start_deletion,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("#007bff", "#007bff"),
            hover_color=("#0056b3", "#0056b3")
        )
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 취소 버튼
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="⏹️ 작업 취소",
            command=self.cancel_operation,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("#ffc107", "#ffc107"),
            hover_color=("#e0a800", "#e0a800"),
            state="disabled"
        )
        self.cancel_button.pack(side="left", fill="x", expand=True, padx=(5, 5))
        
        # 종료 버튼
        quit_button = ctk.CTkButton(
            button_frame,
            text="❌ 종료",
            command=self.quit_application,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("#dc3545", "#dc3545"),
            hover_color=("#c82333", "#c82333")
        )
        quit_button.pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def cancel_operation(self) -> None:
        """작업을 취소합니다."""
        if self.is_processing:
            self.cancel_requested = True
            self.cancel_button.configure(state="disabled")
            self.log_message("사용자가 작업 취소를 요청했습니다...", "WARNING")
    
    def quit_application(self) -> None:
        """애플리케이션을 종료합니다."""
        if self.is_processing:
            if messagebox.askyesno("확인", "작업이 진행 중입니다. 정말 종료하시겠습니까?"):
                self.cancel_requested = True
                if self.driver:
                    self.driver.quit()
                self.root.quit()
        else:
            self.root.quit()
        
    def log_message(self, message: str, level: str = "INFO") -> None:
        """로그 메시지를 UI와 파일에 기록합니다."""
        timestamp = time.strftime("%H:%M:%S")
        emoji = BookDeletionConstants.LOG_LEVELS.get(level, "ℹ️")
        log_entry = f"[{timestamp}] {emoji} {level}: {message}\n"
        
        # 로그 텍스트에 추가
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
        self.root.update()
        
        # 파일 로깅
        logger_method = getattr(self.logger, level.lower(), self.logger.info)
        logger_method(message)
        
    def handle_error(self, error: Exception, context: str = "") -> None:
        """오류를 처리하고 로그에 기록합니다."""
        error_message = f"{context}: {str(error)}" if context else str(error)
        self.log_message(error_message, "ERROR")
        self.total_errors += 1
        self.logger.exception(f"Exception in {context}: {error}")
        
    def validate_excel_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """엑셀 데이터의 유효성을 검사합니다."""
        try:
            # 열 개수 확인
            if len(df.columns) < 2:
                return False, "엑셀 파일에 최소 2개의 열(A, B)이 필요합니다."
            
            # 데이터 존재 확인
            if len(df) == 0:
                return False, "엑셀 파일에 데이터가 없습니다."
            
            # URL 형식 확인
            urls = df.iloc[:, 0].dropna()
            emails = df.iloc[:, 1].dropna()
            
            if len(urls) == 0:
                return False, "A열(URL)에 데이터가 없습니다."
            
            if len(emails) == 0:
                return False, "B열(이메일)에 데이터가 없습니다."
            
            # URL 형식 검증
            invalid_urls = []
            for idx, url in enumerate(urls):
                url_str = str(url)
                if not url_str.startswith(('http://', 'https://')):
                    invalid_urls.append(f"행 {idx + 2}: {url_str}")
            
            if invalid_urls:
                return False, f"잘못된 URL 형식이 발견되었습니다:\n" + "\n".join(invalid_urls[:5])
            
            # 이메일 형식 간단 검증
            invalid_emails = []
            for idx, email in enumerate(emails):
                email_str = str(email)
                if '@' not in email_str or '.' not in email_str:
                    invalid_emails.append(f"행 {idx + 2}: {email_str}")
            
            if invalid_emails:
                return False, f"잘못된 이메일 형식이 발견되었습니다:\n" + "\n".join(invalid_emails[:5])
            
            return True, "데이터 검증 완료"
            
        except Exception as e:
            return False, f"데이터 검증 중 오류: {str(e)}"
    
    def select_excel(self) -> None:
        """엑셀 파일을 선택하고 검증합니다."""
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=BookDeletionConstants.EXCEL_FILETYPES
        )
        
        if not file_path:
            return
            
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 데이터 검증
            is_valid, message = self.validate_excel_data(df)
            
            if not is_valid:
                messagebox.showerror("데이터 검증 오류", message)
                return
            
            # 성공적으로 검증된 경우
            self.excel_file_path = file_path
            filename = os.path.basename(file_path)
            self.excel_label.configure(text=f"선택된 엑셀: {filename}")
            
            # 파일 정보 로그
            urls = df.iloc[:, 0].dropna()
            emails = df.iloc[:, 1].dropna()
            
            self.log_message(f"엑셀 파일이 선택되었습니다: {filename}", "SUCCESS")
            self.log_message(f"총 {len(df)}개의 행이 발견되었습니다", "INFO")
            self.log_message(f"A열 (URL): {len(urls)}개", "INFO")
            self.log_message(f"B열 (이메일): {len(emails)}개", "INFO")
            self.log_message(message, "SUCCESS")
            
            # 중복 이메일 확인
            duplicate_emails = emails[emails.duplicated()].tolist()
            if duplicate_emails:
                self.log_message(f"중복 이메일 발견: {len(duplicate_emails)}개", "WARNING")
                
        except Exception as e:
            error_msg = f"엑셀 파일을 읽는 중 오류가 발생했습니다:\n{str(e)}"
            messagebox.showerror("파일 읽기 오류", error_msg)
            self.handle_error(e, "엑셀 파일 읽기")
                
    def create_template(self) -> None:
        """엑셀 템플릿 파일을 생성합니다."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="템플릿 파일 저장",
                defaultextension=".xlsx",
                filetypes=BookDeletionConstants.EXCEL_FILETYPES
            )
            
            if not file_path:
                return
                
            # 템플릿 데이터 생성
            template_data = {
                '구글플레이도서_URL': [
                    'https://play.google.com/books/publish/u/0/book/123456789',
                    'https://play.google.com/books/publish/u/0/book/987654321',
                    ''
                ],
                '삭제할_이메일': [
                    'user1@example.com',
                    'user2@example.com',
                    ''
                ]
            }
            
            df = pd.DataFrame(template_data)
            
            # 엑셀 파일로 저장
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='삭제목록', index=False)
                
                # 워크시트 가져오기
                worksheet = writer.sheets['삭제목록']
                
                # 열 너비 자동 조정
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            filename = os.path.basename(file_path)
            self.log_message(f"템플릿 파일이 생성되었습니다: {filename}", "SUCCESS")
            messagebox.showinfo("완료", f"템플릿 파일이 생성되었습니다:\n{file_path}")
            
        except Exception as e:
            error_msg = f"템플릿 생성 중 오류가 발생했습니다:\n{str(e)}"
            messagebox.showerror("템플릿 생성 오류", error_msg)
            self.handle_error(e, "템플릿 생성")

    def wait_for_page_load(self, timeout: int = None) -> bool:
        """페이지 로딩 완료를 대기합니다."""
        try:
            timeout = timeout or BookDeletionConstants.WAIT_TIME
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            self.log_message("페이지 로딩 타임아웃", "WARNING")
            return False
    
    def check_email_exists(self, email: str) -> bool:
        """이메일이 페이지에 존재하는지 확인합니다."""
        try:
            if not self.wait_for_page_load(5):
                return False
                
            email_xpath = BookDeletionConstants.EMAIL_XPATH.format(email)
            elements = self.driver.find_elements(By.XPATH, email_xpath)
            return len(elements) > 0
            
        except Exception as e:
            self.log_message(f"이메일 존재 확인 중 오류: {str(e)}", "ERROR")
            return False
    
    def click_delete_button(self, email: str) -> bool:
        """삭제 버튼을 클릭합니다."""
        try:
            email_xpath = BookDeletionConstants.EMAIL_XPATH.format(email)
            email_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, email_xpath))
            )
            
            # 상위 요소 찾기
            item_element = email_element.find_element(By.XPATH, "./ancestor::mat-list-item")
            
            # 삭제 버튼 찾기
            delete_button = item_element.find_element(
                By.XPATH, BookDeletionConstants.DELETE_BUTTON_XPATH
            )
            
            # 요소가 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
            time.sleep(0.5)
            
            # 자바스크립트로 클릭
            self.driver.execute_script("arguments[0].click();", delete_button)
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            self.log_message(f"삭제 버튼을 찾을 수 없습니다: {email}", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"삭제 버튼 클릭 실패: {str(e)}", "ERROR")
            return False
    
    def click_confirm_button(self, email: str) -> bool:
        """삭제 확인 버튼을 클릭합니다."""
        try:
            for selector in BookDeletionConstants.CONFIRM_SELECTORS:
                try:
                    confirm_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", confirm_button)
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            self.log_message(f"삭제 확인 버튼을 찾을 수 없습니다: {email}", "WARNING")
            return False
                
        except Exception as e:
            self.log_message(f"삭제 확인 버튼 클릭 실패: {str(e)}", "ERROR")
            return False
    
    def verify_deletion(self, email: str) -> bool:
        """삭제 완료를 확인합니다."""
        try:
            # 페이지 새로고침
            self.driver.refresh()
            time.sleep(3)
            
            # 이메일 존재 여부 재확인
            return not self.check_email_exists(email)
                
        except Exception as e:
            self.log_message(f"삭제 완료 확인 중 오류: {str(e)}", "WARNING")
            return False
    
    def delete_single_email(self, email: str) -> bool:
        """단일 이메일을 삭제합니다."""
        try:
            # 이메일 존재 확인
            if not self.check_email_exists(email):
                self.log_message(f"이메일을 찾을 수 없습니다: {email}", "WARNING")
                return False
            
            self.log_message(f"{email} 이메일 발견, 삭제 시작", "INFO")
            
            # 삭제 버튼 클릭
            if not self.click_delete_button(email):
                return False
            
            self.log_message(f"{email} 삭제 버튼 클릭 완료, 대기 중...", "INFO")
            time.sleep(5)
            
            # 삭제 확인 버튼 클릭
            if not self.click_confirm_button(email):
                return False
            
            self.log_message(f"{email} 삭제 확인 완료, 대기 중...", "INFO")
            time.sleep(5)
            
            # 삭제 완료 확인
            if self.verify_deletion(email):
                self.log_message(f"{email} 삭제 성공", "SUCCESS")
                return True
            else:
                self.log_message(f"{email} 삭제 실패", "ERROR")
                return False
                
        except Exception as e:
            self.handle_error(e, f"이메일 삭제 처리 - {email}")
            return False
            
    def start_deletion(self) -> None:
        """삭제 작업을 시작합니다."""
        if not self.excel_file_path:
            messagebox.showerror("오류", "엑셀 파일을 선택해주세요.")
            return
        
        if self.is_processing:
            messagebox.showinfo("알림", "이미 작업이 진행 중입니다.")
            return
            
        try:
            # 작업 시작 설정
            start_time = time.time()
            self.is_processing = True
            self.cancel_requested = False
            self.total_processed = 0
            self.total_success = 0
            self.total_errors = 0
            
            # UI 상태 변경
            self.start_button.configure(state="disabled", text="🔄 처리 중...")
            self.cancel_button.configure(state="normal")
            
            self.log_message("작업을 시작합니다...", "INFO")
            
            # 웹드라이버 설정
            if not self.setup_webdriver():
                return
            
            # 데이터 준비
            try:
                url_groups, actual_total_items = self.prepare_data()
                if not url_groups:
                    raise ValueError("처리할 데이터가 없습니다.")
            except Exception as e:
                self.handle_error(e, "데이터 준비 실패")
                return
            
            # 로그인 대기
            self.log_message("로그인이 필요합니다. 로그인을 완료한 후 확인 버튼을 눌러주세요.", "WARNING")
            messagebox.showinfo("안내", "로그인을 완료한 후 확인을 눌러주세요.")
            
            if self.cancel_requested:
                return
            
            # URL을 처리 개수 순으로 정렬 (효율성 향상)
            sorted_urls = sorted(url_groups.items(), key=lambda x: len(x[1]), reverse=True)
            self.log_message("URL을 처리 개수 순으로 정렬하여 효율성을 높입니다", "INFO")
            
            # 각 URL 그룹 처리
            processed_count = 0
            for url, email_list in sorted_urls:
                if self.cancel_requested:
                    self.log_message("사용자 요청으로 작업이 취소되었습니다", "WARNING")
                    break
                    
                processed_count = self.process_url_group(url, email_list, processed_count, actual_total_items)
            
            # 작업 완료 시간 계산
            end_time = time.time()
            total_time = end_time - start_time
            avg_time_per_item = total_time / actual_total_items if actual_total_items > 0 else 0
            
            self.log_message(f"총 처리 시간: {total_time:.1f}초", "INFO")
            self.log_message(f"평균 처리 시간: {avg_time_per_item:.2f}초/항목", "INFO")
            
            if not self.cancel_requested:
                self.show_summary()
            
        except Exception as e:
            self.handle_error(e, "전체 작업 실패")
        finally:
            # 정리 작업
            self.cleanup_resources()
    
    def prepare_data(self) -> Tuple[Dict[str, List[str]], int]:
        """엑셀 데이터를 준비하고 중복을 제거합니다."""
        df = pd.read_excel(self.excel_file_path)
        book_urls = df.iloc[:, 0].dropna().tolist()
        emails = df.iloc[:, 1].dropna().tolist()
        
        # URL별로 데이터 그룹화
        url_groups = {}
        processed_emails = set()
        
        for url, email in zip(book_urls, emails):
            if self.cancel_requested:
                break
                
            if url not in url_groups:
                url_groups[url] = []
            
            # 중복 이메일 체크
            if email not in processed_emails:
                url_groups[url].append(email)
                processed_emails.add(email)
            else:
                self.log_message(f"중복 이메일 제외: {email}", "WARNING")
        
        actual_total_items = sum(len(emails) for emails in url_groups.values())
        
        # 통계 정보 로그
        self.log_message(f"총 {len(url_groups)}개의 고유 URL에서 {actual_total_items}개의 이메일을 처리합니다", "INFO")
        
        if url_groups:
            url_stats = {url: len(emails) for url, emails in url_groups.items()}
            most_common_url = max(url_stats.items(), key=lambda x: x[1])
            self.log_message(f"가장 많은 이메일이 있는 URL: {most_common_url[1]}개", "INFO")
        
        return url_groups, actual_total_items
    
    def setup_webdriver(self) -> bool:
        """웹드라이버를 설정합니다."""
        try:
            self.log_message("크롬드라이버를 자동으로 설정합니다...", "INFO")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            self.driver.get(BookDeletionConstants.BASE_URL)
            return True
        except Exception as e:
            self.handle_error(e, "웹드라이버 설정")
            return False
    
    def process_url_group(self, url: str, email_list: List[str], processed_count: int, total_items: int) -> int:
        """특정 URL의 이메일 그룹을 처리합니다."""
        try:
            # URL이 변경된 경우에만 페이지 로드
            if url != self.current_url:
                self.log_message(f"페이지 로딩: {url}", "INFO")
                try:
                    self.driver.get(url)
                    if not self.wait_for_page_load():
                        self.log_message(f"페이지 로딩 실패: {url}", "ERROR")
                        return processed_count
                    
                    time.sleep(BookDeletionConstants.PAGE_LOAD_WAIT)
                    self.current_url = url
                    self.log_message(f"페이지 로딩 완료: {url}", "SUCCESS")
                except Exception as e:
                    self.handle_error(e, f"페이지 로딩 실패: {url}")
                    return processed_count
            else:
                self.log_message(f"이미 로드된 페이지 사용: 시간 절약", "INFO")
            
            # 해당 URL의 모든 이메일 처리
            for email in email_list:
                if self.cancel_requested:
                    break
                    
                processed_count += 1
                progress = (processed_count / total_items) * 100
                self.progress_var.set(progress)
                
                self.log_message(f"[{processed_count}/{total_items}] {email} 처리 중...", "INFO")
                
                # 이메일 삭제 시도
                if self.delete_single_email(email):
                    self.total_success += 1
                else:
                    self.total_errors += 1
                
                self.total_processed += 1
                
                # 다음 이메일 처리 전 짧은 대기
                if not self.cancel_requested:
                    time.sleep(1)
                    
            return processed_count
            
        except Exception as e:
            self.handle_error(e, f"URL 처리 실패: {url}")
            return processed_count
            
    def cleanup_resources(self) -> None:
        """리소스를 정리하고 UI를 복원합니다."""
        self.is_processing = False
        self.cancel_requested = False
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            
        # UI 상태 복원
        self.start_button.configure(state="normal", text="🚀 작업 시작")
        self.cancel_button.configure(state="disabled")
        self.progress_var.set(0)
                
    def show_summary(self) -> None:
        """작업 완료 요약을 표시합니다."""
        success_rate = (self.total_success / self.total_processed * 100) if self.total_processed > 0 else 0
        
        summary = f"""
📊 작업 완료!

총 처리: {self.total_processed}개
성공: {self.total_success}개 ({success_rate:.1f}%)
실패: {self.total_errors}개
        """
        
        self.log_message(summary.strip(), "SUMMARY")
        
        # 성공률에 따라 메시지 타입 결정
        if success_rate >= 90:
            messagebox.showinfo("작업 완료", summary)
        elif success_rate >= 70:
            messagebox.showwarning("작업 완료 (일부 실패)", summary)
        else:
            messagebox.showerror("작업 완료 (다수 실패)", summary)
        
    def run(self) -> None:
        """애플리케이션을 실행합니다."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("사용자가 프로그램을 중단했습니다", "INFO")
        finally:
            self.cleanup_resources()

if __name__ == "__main__":
    app = BookDeletionApp()
    app.run()