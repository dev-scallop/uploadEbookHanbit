import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# CustomTkinter 테마 설정
ctk.set_appearance_mode("light")  # 라이트 모드
ctk.set_default_color_theme("blue")  # 파란색 테마

class BookDeletionApp:
    # 상수 정의
    WINDOW_TITLE = "전자책 삭제 프로그램"
    WINDOW_SIZE = "900x700"
    BASE_URL = 'https://play.google.com/books/publish/u/0/?hl=ko'
    WAIT_TIME = 10  # 기본 대기 시간
    PAGE_LOAD_WAIT = 5  # 페이지 로딩 대기 시간
    DELETE_WAIT = 2  # 삭제 후 대기 시간
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.resizable(True, True)
        
        # 변수 초기화
        self.chrome_driver_path = None
        self.excel_file_path = None
        self.driver = None
        self.current_url = None
        self.total_processed = 0
        self.total_success = 0
        self.total_errors = 0
        
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
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # 종료 버튼
        quit_button = ctk.CTkButton(
            button_frame,
            text="❌ 종료",
            command=self.root.quit,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("#dc3545", "#dc3545"),
            hover_color=("#c82333", "#c82333")
        )
        quit_button.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        
        # 이모지 추가
        emoji_map = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️", 
            "ERROR": "❌",
            "SUMMARY": "📊"
        }
        
        emoji = emoji_map.get(level, "ℹ️")
        
        log_entry = f"[{timestamp}] {emoji} {level}: {message}\n"
        
        # 로그 텍스트에 추가
        self.log_text.insert("end", log_entry)
        
        # 스크롤을 맨 아래로
        self.log_text.see("end")
        self.root.update()
        
    def handle_error(self, error, context=""):
        error_message = f"{context}: {str(error)}" if context else str(error)
        self.log_message(error_message, "ERROR")
        self.total_errors += 1
        
    def select_excel(self):
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel 파일", "*.xlsx *.xls")]
        )
        if file_path:
            try:
                # 엑셀 파일 미리 읽어서 형식 확인
                df = pd.read_excel(file_path)
                
                # 데이터 형식 검증
                if len(df.columns) < 2:
                    messagebox.showerror("오류", "엑셀 파일에 최소 2개의 열(A, B)이 필요합니다.")
                    return
                
                # 데이터가 있는지 확인
                if len(df) == 0:
                    messagebox.showerror("오류", "엑셀 파일에 데이터가 없습니다.")
                    return
                
                # URL 형식 확인 (간단한 검증)
                first_url = str(df.iloc[0, 0])
                if not first_url.startswith('http'):
                    messagebox.showwarning("경고", "A열의 첫 번째 데이터가 URL 형식이 아닙니다.\n구글 플레이 도서 URL을 확인해주세요.")
                
                self.excel_file_path = file_path
                filename = os.path.basename(file_path)
                self.excel_label.configure(text=f"선택된 엑셀: {filename}")
                
                # 파일 정보 로그
                self.log_message(f"엑셀 파일이 선택되었습니다: {filename}", "SUCCESS")
                self.log_message(f"총 {len(df)}개의 항목이 발견되었습니다", "INFO")
                self.log_message(f"A열 (URL): {len(df.iloc[:, 0].dropna())}개", "INFO")
                self.log_message(f"B열 (이메일): {len(df.iloc[:, 1].dropna())}개", "INFO")
                
            except Exception as e:
                messagebox.showerror("오류", f"엑셀 파일을 읽는 중 오류가 발생했습니다:\n{str(e)}")
                return
                
    def create_template(self):
        """엑셀 템플릿 파일 생성"""
        try:
            # 저장할 파일 경로 선택
            file_path = filedialog.asksaveasfilename(
                title="템플릿 파일 저장",
                defaultextension=".xlsx",
                filetypes=[("Excel 파일", "*.xlsx")]
            )
            
            if file_path:
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
            messagebox.showerror("오류", f"템플릿 생성 중 오류가 발생했습니다:\n{str(e)}")
            
    def find_and_click_with_retry(self, email, max_retries=3):
        for attempt in range(max_retries):
            try:
                # 페이지가 완전히 로드될 때까지 대기
                WebDriverWait(self.driver, self.WAIT_TIME).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # 이메일 요소 찾기 (더 안정적인 방법)
                email_xpath = f"//h4[@class='mat-mdc-list-item-title mdc-list-item__primary-text' and contains(text(),'{email}')]"
                
                # 요소가 존재하는지 먼저 확인
                try:
                    email_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, email_xpath))
                    )
                except:
                    self.log_message(f"이메일 요소를 찾을 수 없습니다: {email}", "WARNING")
                    return False
                
                # 삭제 버튼 찾기 (더 안정적인 방법)
                try:
                    # 상위 요소 찾기
                    item_element = email_element.find_element(By.XPATH, "./ancestor::mat-list-item")
                    
                    # 삭제 버튼 찾기
                    delete_button = item_element.find_element(By.XPATH, ".//button[@aria-label='삭제']")
                    
                    # 버튼이 클릭 가능할 때까지 대기
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, ".//button[@aria-label='삭제']"))
                    )
                    
                    # 스크롤하여 요소가 보이도록 함
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
                    time.sleep(0.5)
                    
                    # 자바스크립트로 클릭 실행
                    self.driver.execute_script("arguments[0].click();", delete_button)
                    
                    # 삭제 확인 다이얼로그 대기 및 처리
                    time.sleep(2)
                    
                    # 삭제 확인 버튼 찾기 및 클릭
                    try:
                        # 확인 버튼 찾기 (여러 가능한 선택자)
                        confirm_selectors = [
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
                        
                        confirm_button = None
                        for selector in confirm_selectors:
                            try:
                                confirm_button = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                break
                            except:
                                continue
                        
                        if confirm_button:
                            self.driver.execute_script("arguments[0].click();", confirm_button)
                            self.log_message(f"삭제 확인 버튼 클릭 완료: {email}", "INFO")
                            time.sleep(5)  # 삭제 완료 대기 (시간 증가)
                            
                            # 실제 삭제 완료 확인
                            try:
                                # 페이지 새로고침하여 변경사항 반영
                                self.driver.refresh()
                                time.sleep(3)
                                
                                # 이메일이 여전히 존재하는지 확인
                                remaining_elements = self.driver.find_elements(By.XPATH, email_xpath)
                                if len(remaining_elements) == 0:
                                    self.log_message(f"삭제 완료 확인됨: {email}", "SUCCESS")
                                else:
                                    self.log_message(f"삭제가 완료되지 않았습니다: {email}", "WARNING")
                            except Exception as e:
                                self.log_message(f"삭제 완료 확인 중 오류: {str(e)}", "WARNING")
                        else:
                            self.log_message(f"삭제 확인 버튼을 찾을 수 없습니다: {email}", "WARNING")
                            time.sleep(2)
                    
                    except Exception as e:
                        self.log_message(f"삭제 확인 처리 중 오류: {str(e)}", "WARNING")
                        time.sleep(2)
                    
                    return True
                    
                except Exception as e:
                    self.log_message(f"삭제 버튼 클릭 실패: {str(e)}", "ERROR")
                    return False
                
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    self.log_message(f"요소를 다시 찾아 시도합니다... (시도 {attempt + 1}/{max_retries})", "WARNING")
                    time.sleep(2)
                    # 페이지 새로고침 시도
                    try:
                        self.driver.refresh()
                        time.sleep(3)
                    except:
                        pass
                    continue
                else:
                    self.log_message(f"최대 재시도 횟수 초과: {email}", "ERROR")
                    return False
            except Exception as e:
                if attempt < max_retries - 1:
                    self.log_message(f"예외 발생, 재시도 중... (시도 {attempt + 1}/{max_retries}): {str(e)}", "WARNING")
                    time.sleep(2)
                    continue
                else:
                    self.log_message(f"최대 재시도 횟수 초과: {email}", "ERROR")
                    return False
        return False

    def check_email_exists(self, email):
        try:
            # 페이지가 완전히 로드될 때까지 대기
            WebDriverWait(self.driver, 5).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 이메일 요소 찾기
            email_xpath = f"//h4[@class='mat-mdc-list-item-title mdc-list-item__primary-text' and contains(text(),'{email}')]"
            
            # 요소 존재 확인
            elements = self.driver.find_elements(By.XPATH, email_xpath)
            return len(elements) > 0
            
        except Exception as e:
            self.log_message(f"이메일 존재 확인 중 오류: {str(e)}", "ERROR")
            return False
    
    def click_delete_button(self, email):
        """삭제 버튼만 클릭"""
        try:
            # 이메일 요소 찾기
            email_xpath = f"//h4[@class='mat-mdc-list-item-title mdc-list-item__primary-text' and contains(text(),'{email}')]"
            email_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, email_xpath))
            )
            
            # 상위 요소 찾기
            item_element = email_element.find_element(By.XPATH, "./ancestor::mat-list-item")
            
            # 삭제 버튼 찾기
            delete_button = item_element.find_element(By.XPATH, ".//button[@aria-label='삭제']")
            
            # 스크롤하여 요소가 보이도록 함
            self.driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
            time.sleep(0.5)
            
            # 자바스크립트로 클릭 실행
            self.driver.execute_script("arguments[0].click();", delete_button)
            return True
            
        except Exception as e:
            self.log_message(f"삭제 버튼 클릭 실패: {str(e)}", "ERROR")
            return False
    
    def click_confirm_button(self, email):
        """삭제 확인 버튼 클릭"""
        try:
            # 확인 버튼 찾기 (여러 가능한 선택자)
            confirm_selectors = [
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
            
            confirm_button = None
            for selector in confirm_selectors:
                try:
                    confirm_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if confirm_button:
                self.driver.execute_script("arguments[0].click();", confirm_button)
                return True
            else:
                self.log_message(f"삭제 확인 버튼을 찾을 수 없습니다: {email}", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f"삭제 확인 버튼 클릭 실패: {str(e)}", "ERROR")
            return False
    
    def verify_deletion(self, email):
        """삭제 완료 확인"""
        try:
            # 페이지 새로고침하여 변경사항 반영
            self.driver.refresh()
            time.sleep(3)
            
            # 이메일이 여전히 존재하는지 확인
            email_xpath = f"//h4[@class='mat-mdc-list-item-title mdc-list-item__primary-text' and contains(text(),'{email}')]"
            remaining_elements = self.driver.find_elements(By.XPATH, email_xpath)
            
            if len(remaining_elements) == 0:
                return True
            else:
                return False
                
        except Exception as e:
            self.log_message(f"삭제 완료 확인 중 오류: {str(e)}", "WARNING")
            return False
            
    def start_deletion(self):
        if not self.excel_file_path:
            messagebox.showerror("오류", "엑셀 파일을 선택해주세요.")
            return
            
        try:
            start_time = time.time()
            self.log_message("작업을 시작합니다...", "INFO")
            self.log_message("크롬드라이버를 자동으로 설정합니다...", "INFO")
            
            # 시작 버튼 비활성화
            self.start_button.configure(state="disabled", text="🔄 처리 중...")
            
            # webdriver-manager를 사용하여 크롬드라이버 자동 설정
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            
            # 엑셀 파일 읽기
            try:
                df = pd.read_excel(self.excel_file_path)
                book_urls = df.iloc[:, 0].dropna().tolist()
                emails = df.iloc[:, 1].dropna().tolist()
                if not book_urls or not emails:
                    raise ValueError("엑셀 파일에 데이터가 없습니다.")
            except Exception as e:
                self.handle_error(e, "엑셀 파일 읽기 실패")
                return

            total_items = len(book_urls)
            self.driver.get(self.BASE_URL)
            
            self.log_message("로그인이 필요합니다. 로그인을 완료한 후 확인 버튼을 눌러주세요.", "WARNING")
            messagebox.showinfo("안내", "로그인을 완료한 후 확인을 눌러주세요.")
            
            # URL별로 데이터 그룹화 (효율성 향상)
            url_groups = {}
            processed_emails = set()  # 중복 이메일 방지
            
            for url, email in zip(book_urls, emails):
                if url not in url_groups:
                    url_groups[url] = []
                
                # 중복 이메일 체크
                if email not in processed_emails:
                    url_groups[url].append(email)
                    processed_emails.add(email)
                else:
                    self.log_message(f"중복 이메일 제외: {email}", "WARNING")
            
            # 실제 처리할 항목 수 계산
            actual_total_items = sum(len(emails) for emails in url_groups.values())
            
            # URL별 처리 개수 통계
            url_stats = {url: len(emails) for url, emails in url_groups.items()}
            most_common_url = max(url_stats.items(), key=lambda x: x[1])
            
            self.log_message(f"총 {len(url_groups)}개의 고유 URL에서 {actual_total_items}개의 이메일을 처리합니다", "INFO")
            self.log_message(f"가장 많은 이메일이 있는 URL: {most_common_url[0]} ({most_common_url[1]}개)", "INFO")
            
            if actual_total_items != total_items:
                self.log_message(f"중복 제거: {total_items - actual_total_items}개의 중복 이메일이 제외되었습니다", "INFO")
            
            # URL을 처리 개수 순으로 정렬 (효율성 향상)
            sorted_urls = sorted(url_groups.items(), key=lambda x: len(x[1]), reverse=True)
            self.log_message("URL을 처리 개수 순으로 정렬하여 효율성을 높입니다", "INFO")
            
            processed_count = 0
            for url, email_list in sorted_urls:
                try:
                    # URL이 변경된 경우에만 페이지 로드
                    if url != self.current_url:
                        self.log_message(f"페이지 로딩: {url}", "INFO")
                        try:
                            self.driver.get(url)
                            # 페이지 로딩 완료 대기
                            WebDriverWait(self.driver, self.WAIT_TIME).until(
                                lambda driver: driver.execute_script("return document.readyState") == "complete"
                            )
                            time.sleep(self.PAGE_LOAD_WAIT)
                            self.current_url = url
                            self.log_message(f"페이지 로딩 완료: {url}", "SUCCESS")
                        except Exception as e:
                            self.handle_error(e, f"페이지 로딩 실패: {url}")
                            continue
                    else:
                        self.log_message(f"이미 로드된 페이지 사용: {url} (시간 절약)", "INFO")
                    
                    # 해당 URL의 모든 이메일 처리
                    for email in email_list:
                        processed_count += 1
                        progress = (processed_count / actual_total_items) * 100
                        self.progress_var.set(progress)
                        
                        self.log_message(f"[{processed_count}/{actual_total_items}] {email} 처리 중...", "INFO")
                        
                        # 이메일이 존재하는지 확인
                        if self.check_email_exists(email):
                            self.log_message(f"{email} 이메일 발견, 삭제 버튼 클릭 중...", "INFO")
                            
                            # 삭제 버튼 클릭
                            if self.click_delete_button(email):
                                self.log_message(f"{email} 삭제 버튼 클릭 완료, 5초 대기 중...", "INFO")
                                time.sleep(5)  # 5초 대기
                                
                                # 삭제 확인 버튼 클릭
                                if self.click_confirm_button(email):
                                    self.log_message(f"{email} 삭제 확인 완료, 5초 대기 중...", "INFO")
                                    time.sleep(5)  # 5초 대기
                                    
                                    # 삭제 완료 확인
                                    if self.verify_deletion(email):
                                        self.log_message(f"{email} 삭제 성공", "SUCCESS")
                                        self.total_success += 1
                                    else:
                                        self.log_message(f"{email} 삭제 실패", "ERROR")
                                        self.total_errors += 1
                                else:
                                    self.log_message(f"{email} 삭제 확인 실패", "ERROR")
                                    self.total_errors += 1
                            else:
                                self.log_message(f"{email} 삭제 버튼 클릭 실패", "ERROR")
                                self.total_errors += 1
                        else:
                            self.log_message(f"{email} 해당 이메일을 찾을 수 없습니다", "WARNING")
                        
                        self.total_processed += 1
                        
                        # 다음 이메일 처리 전 짧은 대기
                        time.sleep(1)
                    
                except Exception as e:
                    self.handle_error(e, f"URL 처리 실패: {url}")
                    
            # 작업 완료 시간 계산
            end_time = time.time()
            total_time = end_time - start_time
            avg_time_per_item = total_time / actual_total_items if actual_total_items > 0 else 0
            
            self.log_message(f"총 처리 시간: {total_time:.1f}초", "INFO")
            self.log_message(f"평균 처리 시간: {avg_time_per_item:.2f}초/항목", "INFO")
            
            self.show_summary()
            
        except Exception as e:
            self.handle_error(e, "전체 작업 실패")
        finally:
            if self.driver:
                self.driver.quit()
            # 시작 버튼 다시 활성화
            self.start_button.configure(state="normal", text="🚀 작업 시작")
                
    def show_summary(self):
        summary = f"""
📊 작업 완료!

총 처리: {self.total_processed}개
성공: {self.total_success}개
실패: {self.total_errors}개
        """
        self.log_message(summary, "SUMMARY")
        messagebox.showinfo("작업 완료", summary)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = BookDeletionApp()
    app.run()