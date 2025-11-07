import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from dotenv import load_dotenv, set_key
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv")

import main as pipeline


# Toss 스타일 컬러 팔레트
COLORS = {
    'primary': '#0064FF',      # Toss 블루
    'primary_dark': '#0050CC',
    'bg_main': '#F9FAFB',
    'bg_card': '#FFFFFF',
    'text_primary': '#191F28',
    'text_secondary': '#4E5968',
    'text_tertiary': '#8B95A1',
    'border': '#E5E8EB',
    'success': '#0ECC5E',
    'warning': '#FFAE0D',
    'error': '#FF4747',
    'divider': '#F2F4F6',
}


@dataclass
class AppSettings:
    openai_api_key: str = ""
    hcti_user_id: str = ""
    hcti_api_key: str = ""
    sheets_web_app_url: str = ""
    watch_spreadsheet_id: str = "1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c"
    watch_sheet_name: str = "시트1"
    target_spreadsheet_id: str = "1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c"
    target_sheet_name: str = "도서정리"
    poll_interval: int = 60
    output_dir: str = ""


class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue: "queue.Queue[str]"):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            pass


def sanitize_filename(name: str) -> str:
    keep = [c if c.isalnum() or c in (" ", "-", "_", ".") else "_" for c in name]
    s = "".join(keep).strip()
    return s or "output"


class ModernButton(tk.Canvas):
    """Toss 스타일 버튼"""
    def __init__(self, parent, text, command, bg_color=COLORS['primary'], 
                 fg_color='white', width=120, height=44, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, **kwargs)
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.command = command
        self.hover = False
        
        self.config(bg=parent.cget('bg') if hasattr(parent, 'cget') else COLORS['bg_main'])
        self._draw()
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        
    def _draw(self):
        self.delete('all')
        color = self._adjust_brightness(self.bg_color, 0.9) if self.hover else self.bg_color
        
        # 둥근 사각형
        r = 8
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.create_oval(0, 0, r*2, r*2, fill=color, outline='')
        self.create_oval(w-r*2, 0, w, r*2, fill=color, outline='')
        self.create_oval(0, h-r*2, r*2, h, fill=color, outline='')
        self.create_oval(w-r*2, h-r*2, w, h, fill=color, outline='')
        self.create_rectangle(r, 0, w-r, h, fill=color, outline='')
        self.create_rectangle(0, r, w, h-r, fill=color, outline='')
        
        # 텍스트
        self.create_text(w/2, h/2, text=self.text, fill=self.fg_color,
                        font=('Segoe UI', 10, 'bold'))
    
    def _adjust_brightness(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * factor) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def _on_enter(self, e):
        self.hover = True
        self._draw()
        self.config(cursor='hand2')
        
    def _on_leave(self, e):
        self.hover = False
        self._draw()
        self.config(cursor='')
        
    def _on_click(self, e):
        if self.command:
            self.command()


class ModernEntry(tk.Frame):
    """Toss 스타일 입력 필드"""
    def __init__(self, parent, label, variable, show=None, placeholder="", **kwargs):
        super().__init__(parent, bg=COLORS['bg_main'])
        self.variable = variable
        
        # 레이블
        label_widget = tk.Label(self, text=label, 
                               font=('Segoe UI', 10, 'bold'),
                               fg=COLORS['text_primary'],
                               bg=COLORS['bg_main'])
        label_widget.pack(anchor='w', pady=(0, 6))
        
        # 입력 필드 컨테이너
        entry_frame = tk.Frame(self, bg=COLORS['bg_card'], 
                              highlightbackground=COLORS['border'],
                              highlightthickness=1)
        entry_frame.pack(fill='x')
        
        # 입력 필드
        self.entry = tk.Entry(entry_frame, textvariable=variable,
                            font=('Segoe UI', 10),
                            fg=COLORS['text_primary'],
                            bg=COLORS['bg_card'],
                            relief='flat',
                            show=show,
                            bd=0)
        self.entry.pack(fill='both', padx=12, pady=10)
        
        # 포커스 효과
        self.entry.bind('<FocusIn>', lambda e: entry_frame.config(
            highlightbackground=COLORS['primary'], highlightthickness=2))
        self.entry.bind('<FocusOut>', lambda e: entry_frame.config(
            highlightbackground=COLORS['border'], highlightthickness=1))


class StatusCard(tk.Frame):
    """상태 표시 카드"""
    def __init__(self, parent, title, value="대기 중", icon="●"):
        super().__init__(parent, bg=COLORS['bg_card'],
                        highlightbackground=COLORS['border'],
                        highlightthickness=1)
        
        content = tk.Frame(self, bg=COLORS['bg_card'])
        content.pack(fill='both', expand=True, padx=16, pady=12)
        
        # 아이콘 + 제목
        header = tk.Frame(content, bg=COLORS['bg_card'])
        header.pack(fill='x')
        
        tk.Label(header, text=icon, font=('Segoe UI', 14),
                fg=COLORS['primary'], bg=COLORS['bg_card']).pack(side='left', padx=(0,6))
        tk.Label(header, text=title, font=('Segoe UI', 9),
                fg=COLORS['text_secondary'], bg=COLORS['bg_card']).pack(side='left')
        
        # 값
        self.value_label = tk.Label(content, text=value,
                                    font=('Segoe UI', 16, 'bold'),
                                    fg=COLORS['text_primary'],
                                    bg=COLORS['bg_card'])
        self.value_label.pack(anchor='w', pady=(8, 0))
    
    def set_value(self, value, color=None):
        self.value_label.config(text=value)
        if color:
            self.value_label.config(fg=color)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("상세페이지 제작 도구")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS['bg_main'])
        
        # .env 로드
        self.env_path = Path('.env')
        if DOTENV_AVAILABLE and self.env_path.exists():
            load_dotenv(self.env_path)
        
        self.settings = AppSettings()
        self.stop_event = threading.Event()
        self.worker: Optional[threading.Thread] = None
        self.log_queue: "queue.Queue[str]" = queue.Queue()

        # 로거 설정
        self.logger = logging.getLogger("gui")
        self.logger.setLevel(logging.INFO)
        qh = QueueLogHandler(self.log_queue)
        qh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(qh)

        self._build_ui()
        self._load_from_env()
        self._poll_log_queue()

    def _build_ui(self):
        # 메인 컨테이너 (좌우 분할)
        main_container = tk.Frame(self.root, bg=COLORS['bg_main'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 좌측: 설정 및 컨트롤 (40%)
        left_panel = tk.Frame(main_container, bg=COLORS['bg_main'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 우측: 로그 및 상태 (60%)
        right_panel = tk.Frame(main_container, bg=COLORS['bg_main'])
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        self._build_left_panel(left_panel)
        self._build_right_panel(right_panel)

    def _build_left_panel(self, parent):
        # 헤더
        header = tk.Frame(parent, bg=COLORS['bg_main'])
        header.pack(fill='x', pady=(0, 20))
        
        tk.Label(header, text="상세페이지 제작 도구",
                font=('Segoe UI', 20, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_main']).pack(anchor='w')
        
        tk.Label(header, text="Google Sheets + OpenAI + HTML to Image",
                font=('Segoe UI', 10),
                fg=COLORS['text_secondary'],
                bg=COLORS['bg_main']).pack(anchor='w', pady=(4, 0))
        
        # 스크롤 가능한 설정 영역
        canvas = tk.Canvas(parent, bg=COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 설정 카드
        settings_card = tk.Frame(scrollable_frame, bg=COLORS['bg_card'],
                                highlightbackground=COLORS['border'],
                                highlightthickness=1)
        settings_card.pack(fill='x', pady=(0, 16))
        
        settings_content = tk.Frame(settings_card, bg=COLORS['bg_card'])
        settings_content.pack(fill='both', padx=20, pady=20)
        
        tk.Label(settings_content, text="🔑 API 설정",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card']).pack(anchor='w', pady=(0, 16))
        
        # 변수 초기화
        self.var_openai = tk.StringVar()
        self.var_hcti_user = tk.StringVar()
        self.var_hcti_key = tk.StringVar()
        self.var_webapp_url = tk.StringVar()
        self.var_watch_id = tk.StringVar(value=self.settings.watch_spreadsheet_id)
        self.var_watch_sheet = tk.StringVar(value=self.settings.watch_sheet_name)
        self.var_target_id = tk.StringVar(value=self.settings.target_spreadsheet_id)
        self.var_target_sheet = tk.StringVar(value=self.settings.target_sheet_name)
        self.var_interval = tk.IntVar(value=self.settings.poll_interval)
        self.var_output_dir = tk.StringVar()
        
        # API 설정
        ModernEntry(settings_content, "OpenAI API Key", self.var_openai, show="●").pack(fill='x', pady=(0, 12))
        ModernEntry(settings_content, "HCTI User ID", self.var_hcti_user).pack(fill='x', pady=(0, 12))
        ModernEntry(settings_content, "HCTI API Key", self.var_hcti_key, show="●").pack(fill='x', pady=(0, 12))
        ModernEntry(settings_content, "Google Apps Script URL", self.var_webapp_url).pack(fill='x', pady=(0, 8))
        
        tk.Label(settings_content, text="※ 시트에 쓰기 위한 Apps Script 웹앱 URL",
                font=('Segoe UI', 8),
                fg=COLORS['text_tertiary'],
                bg=COLORS['bg_card']).pack(anchor='w')
        
        # 구분선
        tk.Frame(settings_content, height=1, bg=COLORS['divider']).pack(fill='x', pady=20)
        
        tk.Label(settings_content, text="📊 Google Sheets 설정",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card']).pack(anchor='w', pady=(0, 16))
        
        ModernEntry(settings_content, "Watch Spreadsheet ID", self.var_watch_id).pack(fill='x', pady=(0, 12))
        ModernEntry(settings_content, "Watch Sheet Name", self.var_watch_sheet).pack(fill='x', pady=(0, 12))
        ModernEntry(settings_content, "Target Spreadsheet ID", self.var_target_id).pack(fill='x', pady=(0, 12))
        ModernEntry(settings_content, "Target Sheet Name", self.var_target_sheet).pack(fill='x', pady=(0, 12))
        
        # 폴링 간격
        interval_frame = tk.Frame(settings_content, bg=COLORS['bg_card'])
        interval_frame.pack(fill='x', pady=(0, 12))
        
        tk.Label(interval_frame, text="Poll Interval (초)",
                font=('Segoe UI', 10, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card']).pack(anchor='w', pady=(0, 6))
        
        spin_frame = tk.Frame(interval_frame, bg=COLORS['bg_card'],
                             highlightbackground=COLORS['border'],
                             highlightthickness=1)
        spin_frame.pack(fill='x')
        
        ttk.Spinbox(spin_frame, from_=10, to=3600, textvariable=self.var_interval,
                   width=10).pack(padx=12, pady=8)
        
        # 출력 폴더
        output_frame = tk.Frame(settings_content, bg=COLORS['bg_card'])
        output_frame.pack(fill='x')
        
        tk.Label(output_frame, text="저장 폴더",
                font=('Segoe UI', 10, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card']).pack(anchor='w', pady=(0, 6))
        
        folder_select = tk.Frame(output_frame, bg=COLORS['bg_card'])
        folder_select.pack(fill='x')
        
        folder_entry_frame = tk.Frame(folder_select, bg=COLORS['bg_card'],
                                     highlightbackground=COLORS['border'],
                                     highlightthickness=1)
        folder_entry_frame.pack(side='left', fill='x', expand=True, padx=(0, 8))
        
        tk.Entry(folder_entry_frame, textvariable=self.var_output_dir,
                font=('Segoe UI', 10),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card'],
                relief='flat', bd=0).pack(fill='both', padx=12, pady=10)
        
        ModernButton(folder_select, "폴더 선택", self._pick_output_dir,
                    bg_color=COLORS['text_secondary'], width=100).pack(side='left')
        
        # 버튼 영역
        button_card = tk.Frame(scrollable_frame, bg=COLORS['bg_card'],
                              highlightbackground=COLORS['border'],
                              highlightthickness=1)
        button_card.pack(fill='x', pady=(0, 16))
        
        button_content = tk.Frame(button_card, bg=COLORS['bg_card'])
        button_content.pack(fill='both', padx=20, pady=20)
        
        tk.Label(button_content, text="⚡ 실행",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card']).pack(anchor='w', pady=(0, 16))
        
        btn_row1 = tk.Frame(button_content, bg=COLORS['bg_card'])
        btn_row1.pack(fill='x', pady=(0, 8))
        
        ModernButton(btn_row1, "💾 설정 저장", self._save_to_env,
                    bg_color=COLORS['success'], width=180, height=50).pack(side='left', padx=(0, 8))
        ModernButton(btn_row1, "▶ 한 번 실행", self.run_once,
                    bg_color=COLORS['primary'], width=180, height=50).pack(side='left')
        
        btn_row2 = tk.Frame(button_content, bg=COLORS['bg_card'])
        btn_row2.pack(fill='x')
        
        ModernButton(btn_row2, "🔄 시작 (연속)", self.start_loop,
                    bg_color=COLORS['primary'], width=180, height=50).pack(side='left', padx=(0, 8))
        ModernButton(btn_row2, "⏸ 중지", self.stop_loop,
                    bg_color=COLORS['error'], width=180, height=50).pack(side='left')
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _build_right_panel(self, parent):
        # 상태 카드들
        status_container = tk.Frame(parent, bg=COLORS['bg_main'])
        status_container.pack(fill='x', pady=(0, 16))
        
        col1 = tk.Frame(status_container, bg=COLORS['bg_main'])
        col1.pack(side='left', fill='x', expand=True, padx=(0, 8))
        
        col2 = tk.Frame(status_container, bg=COLORS['bg_main'])
        col2.pack(side='right', fill='x', expand=True, padx=(8, 0))
        
        self.status_card = StatusCard(col1, "실행 상태", "대기 중", "●")
        self.status_card.pack(fill='both')
        
        self.processed_card = StatusCard(col2, "처리 완료", "0건", "✓")
        self.processed_card.pack(fill='both')
        
        # 로그 카드
        log_card = tk.Frame(parent, bg=COLORS['bg_card'],
                           highlightbackground=COLORS['border'],
                           highlightthickness=1)
        log_card.pack(fill='both', expand=True)
        
        log_header = tk.Frame(log_card, bg=COLORS['bg_card'])
        log_header.pack(fill='x', padx=20, pady=(16, 0))
        
        tk.Label(log_header, text="📋 실행 로그",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['bg_card']).pack(side='left')
        
        ModernButton(log_header, "지우기", self.clear_log,
                    bg_color=COLORS['text_tertiary'], width=80, height=32).pack(side='right')
        
        # 로그 텍스트
        log_content = tk.Frame(log_card, bg=COLORS['bg_card'])
        log_content.pack(fill='both', expand=True, padx=20, pady=(12, 20))
        
        self.txt_log = tk.Text(log_content,
                              font=('Consolas', 9),
                              fg=COLORS['text_primary'],
                              bg='#F8F9FA',
                              relief='flat',
                              wrap=tk.WORD,
                              state=tk.DISABLED)
        
        yscroll = ttk.Scrollbar(log_content, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=yscroll.set)
        
        self.txt_log.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')

    def _load_from_env(self):
        """환경변수에서 설정 로드"""
        self.var_openai.set(os.getenv('OPENAI_API_KEY', ''))
        self.var_hcti_user.set(os.getenv('HCTI_USER_ID', ''))
        self.var_hcti_key.set(os.getenv('HCTI_API_KEY', ''))
        self.var_webapp_url.set(os.getenv('SHEETS_WEB_APP_URL', ''))
        self.var_watch_id.set(os.getenv('WATCH_SPREADSHEET_ID', self.settings.watch_spreadsheet_id))
        self.var_watch_sheet.set(os.getenv('WATCH_SHEET_NAME', self.settings.watch_sheet_name))
        self.var_target_id.set(os.getenv('TARGET_SPREADSHEET_ID', self.settings.target_spreadsheet_id))
        self.var_target_sheet.set(os.getenv('TARGET_SHEET_NAME', self.settings.target_sheet_name))
        self.var_output_dir.set(os.getenv('OUTPUT_DIR', ''))
        
        try:
            interval = int(os.getenv('POLL_INTERVAL', '60'))
            self.var_interval.set(interval)
        except:
            pass

    def _save_to_env(self):
        """설정을 .env 파일에 저장"""
        if not DOTENV_AVAILABLE:
            messagebox.showwarning("경고", "python-dotenv가 설치되지 않았습니다.\npip install python-dotenv")
            return
        
        try:
            env_vars = {
                'OPENAI_API_KEY': self.var_openai.get().strip(),
                'HCTI_USER_ID': self.var_hcti_user.get().strip(),
                'HCTI_API_KEY': self.var_hcti_key.get().strip(),
                'SHEETS_WEB_APP_URL': self.var_webapp_url.get().strip(),
                'WATCH_SPREADSHEET_ID': self.var_watch_id.get().strip(),
                'WATCH_SHEET_NAME': self.var_watch_sheet.get().strip(),
                'TARGET_SPREADSHEET_ID': self.var_target_id.get().strip(),
                'TARGET_SHEET_NAME': self.var_target_sheet.get().strip(),
                'POLL_INTERVAL': str(self.var_interval.get()),
                'OUTPUT_DIR': self.var_output_dir.get().strip(),
            }
            
            # .env 파일 생성/업데이트
            for key, value in env_vars.items():
                set_key(self.env_path, key, value)
            
            self._append_log("✅ 설정이 .env 파일에 저장되었습니다.")
            messagebox.showinfo("성공", "설정이 .env 파일에 저장되었습니다.")
            
        except Exception as e:
            self._append_log(f"❌ 설정 저장 실패: {e}")
            messagebox.showerror("오류", f"설정 저장 중 오류:\n{e}")

    def _pick_output_dir(self):
        path = filedialog.askdirectory(title="결과물 저장 폴더 선택")
        if path:
            self.var_output_dir.set(path)

    def _apply_env(self):
        os.environ["OPENAI_API_KEY"] = self.var_openai.get().strip()
        os.environ["HCTI_USER_ID"] = self.var_hcti_user.get().strip()
        os.environ["HCTI_API_KEY"] = self.var_hcti_key.get().strip()
        os.environ["SHEETS_WEB_APP_URL"] = self.var_webapp_url.get().strip()
        os.environ["WATCH_SPREADSHEET_ID"] = self.var_watch_id.get().strip()
        os.environ["WATCH_SHEET_NAME"] = self.var_watch_sheet.get().strip()
        os.environ["TARGET_SPREADSHEET_ID"] = self.var_target_id.get().strip()
        os.environ["TARGET_SHEET_NAME"] = self.var_target_sheet.get().strip()

    def _make_on_artifacts(self) -> callable:
        out_dir = self.var_output_dir.get().strip()
        if not out_dir:
            return lambda _a: None

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        def cb(art: Dict):
            title = art.get("data", {}).get("title", "")
            fname_base = sanitize_filename(
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_src{art.get('source_row')}_dst{art.get('target_row')}_{title}"
            )

            # HTML
            html = art.get("html", "")
            (out_path / f"{fname_base}.html").write_text(html, encoding="utf-8")

            # JSON
            data = art.get("data", {})
            (out_path / f"{fname_base}.json").write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")), 
                encoding="utf-8"
            )

            # Image
            url = art.get("image_url")
            if url:
                try:
                    r = requests.get(url, timeout=120)
                    if r.status_code == 200:
                        (out_path / f"{fname_base}.png").write_bytes(r.content)
                except Exception as ex:
                    logging.warning("이미지 저장 실패: %s", ex)

        return cb

    def run_once(self):
        try:
            self._apply_env()
            self.status_card.set_value("실행 중...", COLORS['warning'])
            
            config = pipeline.load_config(poll_interval=self.var_interval.get())
            client = pipeline.OpenAI(api_key=config.openai_api_key)

            rows = pipeline.fetch_rows(
                os.getenv("WATCH_SPREADSHEET_ID"), 
                os.getenv("WATCH_SHEET_NAME")
            )
            last_processed = pipeline.load_state()
            processed_any = None
            on_artifacts = self._make_on_artifacts()
            
            for row_number, row_values in pipeline.iter_new_rows(rows, last_processed):
                processed_any = pipeline.process_row(
                    client, config, row_number, row_values, on_artifacts=on_artifacts
                )
                pipeline.save_state(row_number)
                
            if processed_any is None:
                self._append_log("ℹ️  새로운 행이 없습니다.")
                self.status_card.set_value("대기 중", COLORS['text_primary'])
            else:
                self._append_log(f"✅ 처리 완료: 원본 행 {processed_any}")
                self.status_card.set_value("완료", COLORS['success'])
                
        except Exception as exc:
            logging.exception("한 번 실행 실패: %s", exc)
            self.status_card.set_value("오류", COLORS['error'])
            messagebox.showerror("오류", f"실행 중 오류 발생:\n{exc}")

    def _loop_worker(self):
        processed_count = 0
        try:
            self._apply_env()
            config = pipeline.load_config(poll_interval=self.var_interval.get())
            client = pipeline.OpenAI(api_key=config.openai_api_key)
            on_artifacts = self._make_on_artifacts()

            while not self.stop_event.is_set():
                rows = pipeline.fetch_rows(
                    os.getenv("WATCH_SPREADSHEET_ID"), 
                    os.getenv("WATCH_SHEET_NAME")
                )
                last_processed = pipeline.load_state()
                processed_any = None
                
                for row_number, row_values in pipeline.iter_new_rows(rows, last_processed):
                    if self.stop_event.is_set():
                        break
                    processed_any = pipeline.process_row(
                        client, config, row_number, row_values, on_artifacts=on_artifacts
                    )
                    pipeline.save_state(row_number)
                    processed_count += 1
                    self.processed_card.set_value(f"{processed_count}건", COLORS['success'])
                    
                if processed_any is None:
                    self.status_card.set_value("대기 중 (신규 없음)", COLORS['text_secondary'])
                else:
                    self.status_card.set_value(f"실행 중 (최근: {processed_any})", COLORS['success'])
                    
                for _ in range(config.poll_interval):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
        except Exception as exc:
            logging.exception("백그라운드 실행 실패: %s", exc)
            self.status_card.set_value("오류 발생", COLORS['error'])
            messagebox.showerror("오류", f"백그라운드 실행 중 오류:\n{exc}")
        finally:
            self.worker = None
            self.stop_event.clear()
            self.status_card.set_value("중지됨", COLORS['text_tertiary'])

    def start_loop(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("정보", "이미 실행 중입니다.")
            return
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._loop_worker, daemon=True)
        self.worker.start()
        self.status_card.set_value("실행 중...", COLORS['primary'])
        self._append_log("🔄 연속 실행 시작")

    def stop_loop(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self._append_log("⏸  중지 요청됨...")

    def clear_log(self):
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.configure(state=tk.DISABLED)

    def _append_log(self, text: str):
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state=tk.DISABLED)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._append_log(msg)
        except queue.Empty:
            pass
        self.root.after(200, self._poll_log_queue)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
