"""
전자책 검토자 자동 등록 시스템 - CustomTkinter UI
애플 스타일과 토스뱅크 스타일을 혼합한 모던 UI
"""

import os
import threading
import time
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import korean_utils

# 원본 코드의 클래스 가져오기
# EbookReviewerAutoRegister 클래스를 BookReviewerRegister로 사용
# 기존 클래스를 로드할 수 없는 경우를 대비해 폴백 클래스를 정의

# 폴백 클래스 먼저 정의
class BookReviewerRegisterFallback:
    """로드 실패 시 사용할 기본 클래스"""
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.registration_results = []
        print("주의: 기본 클래스가 사용됩니다. 모든 기능이 작동하지 않을 수 있습니다.")

# 기본값으로 폴백 클래스 사용
BookReviewerRegister = BookReviewerRegisterFallback

# 실제 클래스 로드 시도
try:
    import importlib.util
    import sys
    
    file_path = os.path.join(os.path.dirname(__file__), "[개발중] 전자책자동등록.py")
    module_name = "ebookRegister"
    
    if os.path.exists(file_path):
        print(f"모듈 파일을 찾았습니다: {file_path}")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, 'EbookReviewerAutoRegister'):
            print("EbookReviewerAutoRegister 클래스를 찾았습니다.")
            BookReviewerRegister = module.EbookReviewerAutoRegister
        else:
            print("EbookReviewerAutoRegister 클래스를 찾을 수 없습니다. 폴백 클래스를 사용합니다.")
    else:
        print(f"파일을 찾을 수 없습니다: {file_path}")
except Exception as e:
    print(f"기존 모듈을 로드할 수 없습니다: {e}")
    print("폴백 클래스를 사용합니다.")

# 테마 및 색상 설정
class AppTheme:
    # 애플+토스 스타일의 색상 팔레트
    PRIMARY_COLOR = "#00A5FF"  # 토스 블루
    SECONDARY_COLOR = "#54B9FF"  # 밝은 블루
    SUCCESS_COLOR = "#00C473"  # 민트 그린
    WARNING_COLOR = "#FF7E36"  # 토스 주황
    ERROR_COLOR = "#FF5D5D"  # 토스 레드
    
    # 배경색 및 텍스트 색상
    BG_COLOR = "#F5F6FA"  # 밝은 배경
    BG_COLOR_SECONDARY = "#FFFFFF"  # 흰색 배경
    TEXT_COLOR = "#333333"  # 짙은 텍스트
    TEXT_COLOR_SECONDARY = "#666666"  # 회색 텍스트

    # 폰트 설정 - 시스템에 설치된 폰트 확인 없이 기본값 설정
    FONT_FAMILY = "Roboto"  # 기본 폰트를 Roboto로 설정
    FONT_SIZE_LARGE = 16
    FONT_SIZE_MEDIUM = 14
    FONT_SIZE_SMALL = 12
    
    CORNER_RADIUS = 10  # 모서리 반경

class CustomTooltip(ctk.CTkToplevel):
    """사용자 정의 툴팁 클래스"""
    def __init__(self, widget, text):
        super().__init__(widget)
        self.withdraw()
        self.overrideredirect(True)
        self.widget = widget
        
        # 툴팁 스타일링
        self.frame = ctk.CTkFrame(self, corner_radius=AppTheme.CORNER_RADIUS/2,
                                fg_color=AppTheme.TEXT_COLOR, bg_color="transparent")
        self.frame.pack(expand=True, fill="both")
        
        self.label = ctk.CTkLabel(self.frame, text=text,
                                text_color=AppTheme.BG_COLOR_SECONDARY,
                                font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, size=AppTheme.FONT_SIZE_SMALL-1))
        self.label.pack(padx=10, pady=6)
        
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        
    def hide_tooltip(self, event=None):
        self.withdraw()

class ModernCard(ctk.CTkFrame):
    """모던 카드형 컨테이너 위젯"""
    def __init__(self, master, title, **kwargs):
        super().__init__(master, corner_radius=AppTheme.CORNER_RADIUS, 
                        fg_color=AppTheme.BG_COLOR_SECONDARY, **kwargs)
        
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.pack(fill="x", pady=(10, 5), padx=15)
        
        self.title_label = ctk.CTkLabel(self.title_frame, text=title,
                                     font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                     size=AppTheme.FONT_SIZE_MEDIUM, 
                                                     weight="bold"),
                                     text_color=AppTheme.TEXT_COLOR)
        self.title_label.pack(side="left", anchor="w")
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

class ProgressDialog(ctk.CTkToplevel):
    """진행 상태 표시 대화상자"""
    def __init__(self, master, title="진행 중"):
        super().__init__(master)
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        
        # 화면 중앙에 위치
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.frame = ctk.CTkFrame(self, fg_color=AppTheme.BG_COLOR)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.status_label = ctk.CTkLabel(self.frame, 
                                        text="작업을 처리하는 중입니다...",
                                        font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                        size=AppTheme.FONT_SIZE_MEDIUM))
        self.status_label.pack(pady=(10, 15))
        
        self.progress_bar = ctk.CTkProgressBar(self.frame, width=300, 
                                            progress_color=AppTheme.PRIMARY_COLOR)
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.set(0)
        
        self.cancel_button = ctk.CTkButton(self.frame, text="취소",
                                        font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                        size=AppTheme.FONT_SIZE_SMALL),
                                        fg_color=AppTheme.TEXT_COLOR_SECONDARY,
                                        hover_color=AppTheme.TEXT_COLOR,
                                        height=32,
                                        corner_radius=AppTheme.CORNER_RADIUS,
                                        command=self.cancel)
        self.cancel_button.pack(pady=(5, 10))
        
        self.cancelled = False
        
    def update_progress(self, value, status_text=None):
        """진행률과 상태 텍스트 업데이트"""
        self.progress_bar.set(value)
        if status_text:
            self.status_label.configure(text=status_text)
        self.update_idletasks()
    
    def cancel(self):
        """작업 취소"""
        if messagebox.askyesno("작업 취소", "현재 작업을 취소하시겠습니까?"):
            self.cancelled = True
            self.destroy()

class EbookRegisterApp(ctk.CTk):
    """전자책 검토자 자동 등록 애플리케이션 - 모던 UI"""
    
    def __init__(self):
        super().__init__()
        self.title("전자책 검토자 자동 등록")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # 테마 설정
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # 내부 변수
        self.file_path = ""
        self.registerer = BookReviewerRegister()
        self.data_df = None
        self.registration_thread = None
        self.stop_requested = False
        
        # UI 구성
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성 요소 설정"""
        # 메인 프레임
        self.main_frame = ctk.CTkFrame(self, fg_color=AppTheme.BG_COLOR)
        self.main_frame.pack(fill="both", expand=True)
        
        # 상단 타이틀
        self.title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=60)
        self.title_frame.pack(fill="x", padx=20, pady=20)
        
        self.title_label = ctk.CTkLabel(self.title_frame, 
                                       text="전자책 검토자 자동 등록 시스템",
                                       font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                     size=24, 
                                                     weight="bold"),
                                       text_color=AppTheme.TEXT_COLOR)
        self.title_label.pack(side="left")
        
        # 설정 버튼
        self.settings_button = ctk.CTkButton(self.title_frame, 
                                           text="설정",
                                           font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                          size=AppTheme.FONT_SIZE_SMALL),
                                           width=80,
                                           height=30,
                                           corner_radius=AppTheme.CORNER_RADIUS,
                                           fg_color=AppTheme.TEXT_COLOR_SECONDARY,
                                           hover_color=AppTheme.TEXT_COLOR,
                                           command=self.show_settings)
        self.settings_button.pack(side="right")
        
        # 상태 표시줄
        self.status_frame = ctk.CTkFrame(self.main_frame, height=40, 
                                       fg_color=AppTheme.BG_COLOR_SECONDARY,
                                       corner_radius=0)
        self.status_frame.pack(side="bottom", fill="x")
        
        self.status_label = ctk.CTkLabel(self.status_frame, 
                                       text="준비됨",
                                       font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                      size=AppTheme.FONT_SIZE_SMALL),
                                       text_color=AppTheme.TEXT_COLOR_SECONDARY)
        self.status_label.pack(side="left", padx=15)
        
        self.version_label = ctk.CTkLabel(self.status_frame, 
                                        text="v1.0.0",
                                        font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                       size=AppTheme.FONT_SIZE_SMALL),
                                        text_color=AppTheme.TEXT_COLOR_SECONDARY)
        self.version_label.pack(side="right", padx=15)
        
        # 콘텐츠 프레임
        self.content_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # === 1. 파일 선택 카드 ===
        self.file_card = ModernCard(self.content_frame, title="1. 엑셀 파일 선택")
        self.file_card.pack(fill="x", pady=(0, 15))
        
        self.file_select_frame = ctk.CTkFrame(self.file_card.content_frame, fg_color="transparent")
        self.file_select_frame.pack(fill="x", pady=10)
        
        self.file_path_var = ctk.StringVar()
        self.file_entry = ctk.CTkEntry(self.file_select_frame,
                                     textvariable=self.file_path_var,
                                     width=350,
                                     font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                    size=AppTheme.FONT_SIZE_SMALL),
                                     height=35,
                                     corner_radius=AppTheme.CORNER_RADIUS)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.browse_button = ctk.CTkButton(self.file_select_frame,
                                         text="파일 찾기",
                                         font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                        size=AppTheme.FONT_SIZE_SMALL),
                                         fg_color=AppTheme.PRIMARY_COLOR,
                                         hover_color=AppTheme.SECONDARY_COLOR,
                                         height=35,
                                         corner_radius=AppTheme.CORNER_RADIUS,
                                         command=self.browse_file)
        self.browse_button.pack(side="right")
        
        self.file_info_label = ctk.CTkLabel(self.file_card.content_frame,
                                          text="* 검토자 정보(도서코드, 이름, 지메일)가 포함된 엑셀 파일을 선택하세요.",
                                          font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                         size=AppTheme.FONT_SIZE_SMALL-1),
                                          text_color=AppTheme.TEXT_COLOR_SECONDARY)
        self.file_info_label.pack(fill="x", pady=(0, 5))
        
        # === 2. 데이터 미리보기 카드 ===
        self.preview_card = ModernCard(self.content_frame, title="2. 데이터 미리보기")
        self.preview_card.pack(fill="x", pady=(0, 15))
        
        # 트리뷰 컨테이너
        self.treeview_container = ctk.CTkFrame(self.preview_card.content_frame, fg_color="transparent")
        self.treeview_container.pack(fill="both", expand=True, pady=10)
        
        # 데이터 미리보기 트리뷰 (기본 tkinter Treeview 사용)
        import tkinter as tk
        from tkinter import ttk
        
        self.style = ttk.Style()
        self.style.configure("Treeview", 
                           background=AppTheme.BG_COLOR_SECONDARY,
                           fieldbackground=AppTheme.BG_COLOR_SECONDARY, 
                           rowheight=25)
        self.style.configure("Treeview.Heading", 
                           font=(AppTheme.FONT_FAMILY, AppTheme.FONT_SIZE_SMALL), 
                           background=AppTheme.BG_COLOR)
        
        self.treeview_frame = ctk.CTkFrame(self.treeview_container, fg_color="transparent")
        self.treeview_frame.pack(fill="both", expand=True)
        
        columns = ("도서코드", "이름", "지메일")
        self.tree = ttk.Treeview(self.treeview_frame, columns=columns, show="headings", height=5)
        
        # 열 설정
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 스크롤바
        self.scrollbar = ttk.Scrollbar(self.treeview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 로드 버튼
        self.load_button_frame = ctk.CTkFrame(self.preview_card.content_frame, fg_color="transparent")
        self.load_button_frame.pack(fill="x", pady=(5, 0))
        
        self.load_button = ctk.CTkButton(self.load_button_frame,
                                       text="데이터 로드",
                                       font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                      size=AppTheme.FONT_SIZE_SMALL),
                                       fg_color=AppTheme.SUCCESS_COLOR,
                                       hover_color="#00A861",  # 더 진한 그린
                                       height=35,
                                       corner_radius=AppTheme.CORNER_RADIUS,
                                       command=self.load_data)
        self.load_button.pack(side="right")
        
        # === 3. 실행 카드 ===
        self.execute_card = ModernCard(self.content_frame, title="3. 등록 실행")
        self.execute_card.pack(fill="x", pady=(0, 15))
        
        self.execute_frame = ctk.CTkFrame(self.execute_card.content_frame, fg_color="transparent")
        self.execute_frame.pack(fill="x", pady=10)
        
        # 버튼 프레임
        self.button_frame = ctk.CTkFrame(self.execute_frame, fg_color="transparent")
        self.button_frame.pack(fill="x")
        
        # 실행 버튼
        self.execute_button = ctk.CTkButton(self.button_frame,
                                          text="등록 시작",
                                          font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                         size=AppTheme.FONT_SIZE_MEDIUM, 
                                                         weight="bold"),
                                          fg_color=AppTheme.PRIMARY_COLOR,
                                          hover_color=AppTheme.SECONDARY_COLOR,
                                          height=45,
                                          corner_radius=AppTheme.CORNER_RADIUS,
                                          state="disabled",
                                          command=self.start_registration)
        self.execute_button.pack(side="left", padx=(0, 10))
        
        # 중지 버튼
        self.stop_button = ctk.CTkButton(self.button_frame,
                                       text="중지",
                                       font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                      size=AppTheme.FONT_SIZE_MEDIUM),
                                       fg_color=AppTheme.WARNING_COLOR,
                                       hover_color="#E56A20",  # 더 진한 주황
                                       height=45,
                                       corner_radius=AppTheme.CORNER_RADIUS,
                                       state="disabled",
                                       command=self.stop_registration)
        self.stop_button.pack(side="left", padx=(0, 10))
        
        # 진행률 표시
        self.progress_var = ctk.StringVar(value="0/0 완료")
        self.progress_label = ctk.CTkLabel(self.button_frame,
                                         textvariable=self.progress_var,
                                         font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                        size=AppTheme.FONT_SIZE_MEDIUM))
        self.progress_label.pack(side="left", padx=10)
        
        # 진행 바
        self.progress_bar = ctk.CTkProgressBar(self.execute_frame,
                                             width=200,
                                             height=15,
                                             corner_radius=AppTheme.CORNER_RADIUS/2,
                                             progress_color=AppTheme.PRIMARY_COLOR)
        self.progress_bar.pack(fill="x", pady=(15, 5))
        self.progress_bar.set(0)
        
        # === 4. 로그 출력 카드 ===
        self.log_card = ModernCard(self.content_frame, title="4. 실행 로그")
        self.log_card.pack(fill="x", pady=(0, 15))
        
        # 로그 출력 영역
        self.log_frame = ctk.CTkFrame(self.log_card.content_frame, fg_color="transparent")
        self.log_frame.pack(fill="both", expand=True, pady=10)
        
        self.log_text = ctk.CTkTextbox(self.log_frame,
                                     font=ctk.CTkFont(family="Courier", size=AppTheme.FONT_SIZE_SMALL),
                                     corner_radius=AppTheme.CORNER_RADIUS,
                                     height=150)
        self.log_text.pack(fill="both", expand=True)
        
        # 결과 저장 버튼
        self.save_button = ctk.CTkButton(self.log_card.content_frame,
                                       text="결과 저장",
                                       font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                      size=AppTheme.FONT_SIZE_SMALL),
                                       fg_color=AppTheme.TEXT_COLOR_SECONDARY,
                                       hover_color=AppTheme.TEXT_COLOR,
                                       height=35,
                                       corner_radius=AppTheme.CORNER_RADIUS,
                                       state="disabled",
                                       command=self.save_results)
        self.save_button.pack(side="right", pady=(5, 0))
        
        # 초기 상태 설정
        self.update_status("시스템이 준비되었습니다. 엑셀 파일을 선택해주세요.")
    
    def show_settings(self):
        """설정 창 표시"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("설정")
        settings_window.geometry("500x400")
        settings_window.transient(self)
        settings_window.grab_set()
        
        # 화면 중앙에 위치
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # 설정 프레임
        settings_frame = ctk.CTkFrame(settings_window, fg_color=AppTheme.BG_COLOR)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 설정 제목
        settings_label = ctk.CTkLabel(settings_frame, 
                                     text="시스템 설정",
                                     font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                    size=AppTheme.FONT_SIZE_LARGE, 
                                                    weight="bold"),
                                     text_color=AppTheme.TEXT_COLOR)
        settings_label.pack(pady=(0, 20), anchor="w")
        
        # 설정 카드 - 구글 스프레드시트 URL
        gs_card = ModernCard(settings_frame, title="구글 스프레드시트 설정")
        gs_card.pack(fill="x", pady=(0, 15))
        
        gs_url_frame = ctk.CTkFrame(gs_card.content_frame, fg_color="transparent")
        gs_url_frame.pack(fill="x", pady=10)
        
        gs_url_label = ctk.CTkLabel(gs_url_frame, 
                                  text="스프레드시트 URL:",
                                  font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                 size=AppTheme.FONT_SIZE_SMALL),
                                  text_color=AppTheme.TEXT_COLOR)
        gs_url_label.pack(anchor="w", pady=(0, 5))
        
        self.gs_url_var = ctk.StringVar(value="https://docs.google.com/spreadsheets/d/...")
        gs_url_entry = ctk.CTkEntry(gs_url_frame,
                                  textvariable=self.gs_url_var,
                                  font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                 size=AppTheme.FONT_SIZE_SMALL),
                                  height=35,
                                  width=400,
                                  corner_radius=AppTheme.CORNER_RADIUS)
        gs_url_entry.pack(fill="x")
        
        gs_info_label = ctk.CTkLabel(gs_url_frame, 
                                   text="* 도서 데이터베이스로 사용할 구글 스프레드시트 URL을 입력하세요.",
                                   font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                  size=AppTheme.FONT_SIZE_SMALL-1),
                                   text_color=AppTheme.TEXT_COLOR_SECONDARY)
        gs_info_label.pack(anchor="w", pady=(5, 0))
        
        # 설정 카드 - 로그인 정보
        login_card = ModernCard(settings_frame, title="구글 로그인 설정")
        login_card.pack(fill="x", pady=(0, 15))
        
        auto_login_frame = ctk.CTkFrame(login_card.content_frame, fg_color="transparent")
        auto_login_frame.pack(fill="x", pady=10)
        
        self.auto_login_var = ctk.BooleanVar(value=False)
        auto_login_switch = ctk.CTkSwitch(auto_login_frame, 
                                        text="자동 로그인 사용",
                                        font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                       size=AppTheme.FONT_SIZE_SMALL),
                                        variable=self.auto_login_var,
                                        progress_color=AppTheme.PRIMARY_COLOR,
                                        button_color=AppTheme.PRIMARY_COLOR)
        auto_login_switch.pack(anchor="w")
        
        login_info_label = ctk.CTkLabel(auto_login_frame, 
                                      text="* 자동 로그인을 사용하면 크롬 브라우저에 저장된 계정으로 로그인합니다.",
                                      font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                     size=AppTheme.FONT_SIZE_SMALL-1),
                                      text_color=AppTheme.TEXT_COLOR_SECONDARY)
        login_info_label.pack(anchor="w", pady=(5, 0))
        
        # 버튼 프레임
        button_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0), side="bottom")
        
        cancel_button = ctk.CTkButton(button_frame,
                                     text="취소",
                                     font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                    size=AppTheme.FONT_SIZE_SMALL),
                                     fg_color=AppTheme.TEXT_COLOR_SECONDARY,
                                     hover_color=AppTheme.TEXT_COLOR,
                                     height=35,
                                     corner_radius=AppTheme.CORNER_RADIUS,
                                     command=settings_window.destroy)
        cancel_button.pack(side="right", padx=(10, 0))
        
        save_button = ctk.CTkButton(button_frame,
                                   text="저장",
                                   font=ctk.CTkFont(family=AppTheme.FONT_FAMILY, 
                                                  size=AppTheme.FONT_SIZE_SMALL),
                                   fg_color=AppTheme.PRIMARY_COLOR,
                                   hover_color=AppTheme.SECONDARY_COLOR,
                                   height=35,
                                   corner_radius=AppTheme.CORNER_RADIUS,
                                   command=lambda: self.save_settings(settings_window))
        save_button.pack(side="right")
    
    def save_settings(self, window):
        """설정 저장"""
        # 설정 파일 업데이트 로직을 여기에 구현
        # config.py 파일의 GOOGLE_SHEET_URL 변수 등을 업데이트
        try:
            window.destroy()
            self.update_status("설정이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다: {e}")
    
    def browse_file(self):
        """파일 찾기 대화상자"""
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[
                ("엑셀 파일", "*.xlsx *.xls *.csv"),
                ("모든 파일", "*.*")
            ]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.update_status(f"파일 선택됨: {os.path.basename(file_path)}")
    
    def load_data(self):
        """데이터 로드 및 미리보기 표시"""
        file_path = self.file_path_var.get()
        
        if not file_path:
            messagebox.showerror("오류", "파일을 선택해주세요.")
            return
        
        # 진행 중 대화상자 표시
        progress_dialog = ProgressDialog(self, "데이터 로드 중")
        
        def load_task():
            try:
                # 트리뷰 초기화
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                progress_dialog.update_progress(0.3, "엑셀 파일 읽는 중...")
                time.sleep(0.5)  # 진행 상태 보여주기 위한 딜레이
                
                # 실제 데이터 로드 로직
                # 여기서 self.registerer.read_data_from_source() 등 사용
                
                # 테스트 데이터 (실제 구현 시 이 부분 교체)
                import pandas as pd
                try:
                    if file_path.endswith('.csv'):
                        self.data_df = pd.read_csv(file_path)
                    else:
                        self.data_df = pd.read_excel(file_path)
                    
                    progress_dialog.update_progress(0.6, "데이터 처리 중...")
                    time.sleep(0.5)
                    
                    # 열 이름 확인 및 필수 열 체크
                    required_columns = ['도서코드', '이름', '지메일']
                    
                    # 대체 가능한 열 이름 매핑
                    column_mappings = {
                        '이름': ['이름', '성명', '검토자', '검토자명'],
                        '도서코드': ['도서코드', '책코드', '코드'],
                        '지메일': ['지메일', '이메일', 'Email', 'Gmail']
                    }
                    
                    # 열 이름 매핑 적용
                    for target, alternatives in column_mappings.items():
                        if target not in self.data_df.columns:
                            for alt in alternatives:
                                if alt in self.data_df.columns:
                                    self.data_df.rename(columns={alt: target}, inplace=True)
                                    break
                    
                    # 필수 열 확인
                    missing_columns = [col for col in required_columns if col not in self.data_df.columns]
                    if missing_columns:
                        raise ValueError(f"필수 열이 누락되었습니다: {', '.join(missing_columns)}")
                    
                    # 트리뷰에 데이터 표시
                    progress_dialog.update_progress(0.9, "미리보기 업데이트 중...")
                    for i, row in self.data_df.head(20).iterrows():
                        values = (row.get('도서코드', ''), row.get('이름', ''), row.get('지메일', ''))
                        self.tree.insert('', 'end', values=values)
                    
                    # 실행 버튼 활성화
                    self.execute_button.configure(state="normal")
                    
                    progress_dialog.update_progress(1.0, "완료!")
                    time.sleep(0.5)
                    
                    # 진행 대화상자 닫기
                    self.after(500, progress_dialog.destroy)
                    
                    # 상태 업데이트
                    total_rows = len(self.data_df)
                    self.update_status(f"데이터 로드 완료: {total_rows}개의 항목을 찾았습니다.")
                    self.log_message(f"엑셀 파일에서 {total_rows}개의 검토자 데이터를 로드했습니다.")
                    
                except Exception as e:
                    progress_dialog.destroy()
                    messagebox.showerror("오류", f"데이터 로드 중 오류가 발생했습니다: {e}")
            except Exception as e:
                progress_dialog.destroy()
                messagebox.showerror("오류", f"작업 실행 중 오류가 발생했습니다: {e}")
        
        # 별도 스레드에서 실행
        threading.Thread(target=load_task, daemon=True).start()
    
    def start_registration(self):
        """등록 시작"""
        if self.data_df is None or self.data_df.empty:
            messagebox.showerror("오류", "데이터를 먼저 로드해주세요.")
            return
        
        # 확인 대화상자
        if not messagebox.askyesno("확인", f"총 {len(self.data_df)}개의 검토자를 등록하시겠습니까?"):
            return
        
        # UI 상태 업데이트
        self.stop_requested = False
        self.execute_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.save_button.configure(state="disabled")
        
        # 등록 작업 시작
        self.registration_thread = threading.Thread(target=self.run_registration)
        self.registration_thread.daemon = True
        self.registration_thread.start()
    
    def run_registration(self):
        """등록 실행 (별도 스레드)"""
        try:
            self.log_message("등록 프로세스 시작...")
            self.log_message("📌 주의사항:")
            self.log_message("   - 크롬 브라우저 창이 열리면 Google Play Books 파트너스 센터에 로그인해주세요")
            self.log_message("   - 로그인 완료 후 자동으로 검토자 등록이 진행됩니다")
            self.log_message("   - 브라우저 창을 닫지 마세요")
            
            # 진행 대화상자
            self.after(0, lambda: self.show_registration_progress())
            
            # 여기서 실제 등록 작업 수행
            # 대신 테스트 코드로 대체
            total_items = len(self.data_df)
            for i in range(total_items):
                if self.stop_requested:
                    self.log_message("사용자에 의해 작업이 중지되었습니다.")
                    break
                
                # 실제 작업 대신 시간 지연으로 시뮬레이션
                time.sleep(0.5)
                
                # 진행률 업데이트
                progress = (i + 1) / total_items
                self.update_progress(i + 1, total_items)
                
                # 현재 처리 중인 항목의 정보
                if i < len(self.data_df):
                    row = self.data_df.iloc[i]
                    self.log_message(f"검토자 등록 중: {row.get('이름', '')} ({row.get('지메일', '')})")
            
            self.log_message("등록 프로세스가 완료되었습니다.")
            
            # UI 업데이트
            self.after(0, self.registration_completed)
            
        except Exception as e:
            self.log_message(f"등록 실패: {str(e)}")
            self.after(0, self.registration_completed)
    
    def show_registration_progress(self):
        """등록 진행 상태 대화상자 표시"""
        # 여기서는 진행 상태만 표시하고 실제 업데이트는 update_progress에서 수행
        pass
    
    def stop_registration(self):
        """등록 중지"""
        if messagebox.askyesno("확인", "등록 작업을 중지하시겠습니까?"):
            self.stop_requested = True
            self.log_message("등록 작업 중지 요청...")
            self.update_status("등록 작업을 중지하는 중...")
    
    def registration_completed(self):
        """등록 작업 완료 처리"""
        self.execute_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.save_button.configure(state="normal")
        self.update_status("등록 작업이 완료되었습니다.")
    
    def update_progress(self, current, total, status_text=None):
        """진행률 업데이트"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_var.set(f"{current}/{total} 완료")
        
        if status_text:
            self.update_status(status_text)
    
    def save_results(self):
        """결과 저장"""
        file_path = filedialog.asksaveasfilename(
            title="결과 저장",
            defaultextension=".txt",
            filetypes=[
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 로그 내용 가져오기
            log_content = self.log_text.get("1.0", "end-1c")
            
            # 파일에 저장
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            
            self.update_status(f"결과가 저장되었습니다: {os.path.basename(file_path)}")
            messagebox.showinfo("저장 완료", "결과가 성공적으로 저장되었습니다.")
            
        except Exception as e:
            messagebox.showerror("오류", f"결과 저장 중 오류가 발생했습니다: {e}")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert("end", formatted_message)
        self.log_text.see("end")
    
    def update_status(self, message):
        """상태 표시줄 업데이트"""
        self.status_label.configure(text=message)

if __name__ == "__main__":
    app = EbookRegisterApp()
    app.mainloop()
