import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from dotenv import load_dotenv, set_key
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv가 설치되지 않았습니다. pip install python-dotenv")

import main as pipeline


# Toss 스타일 컬러
COLORS = {
    'primary': '#0064FF',
    'primary_dark': '#0050CC',
    'bg': '#F9FAFB',
    'card': '#FFFFFF',
    'text': '#191F28',
    'text_secondary': '#4E5968',
    'border': '#E5E8EB',
    'success': '#0ECC5E',
    'warning': '#FFAE0D',
    'error': '#FF4747',
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


class RoundedButton(tk.Canvas):
    """간단한 둥근 버튼"""
    def __init__(self, parent, text, command, bg_color=COLORS['primary'], 
                 width=150, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=COLORS['bg'], **kwargs)
        self.bg_color = bg_color
        self.text = text
        self.command = command
        self.hover = False
        
        self._draw()
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        
    def _draw(self):
        self.delete('all')
        color = self._darken(self.bg_color) if self.hover else self.bg_color
        
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        r = 8
        self.create_oval(0, 0, r*2, r*2, fill=color, outline='')
        self.create_oval(w-r*2, 0, w, r*2, fill=color, outline='')
        self.create_oval(0, h-r*2, r*2, h, fill=color, outline='')
        self.create_oval(w-r*2, h-r*2, w, h, fill=color, outline='')
        self.create_rectangle(r, 0, w-r, h, fill=color, outline='')
        self.create_rectangle(0, r, w, h-r, fill=color, outline='')
        
        self.create_text(w/2, h/2, text=self.text, fill='white',
                        font=('Segoe UI', 10, 'bold'))
    
    def _darken(self, hex_color):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(int(c * 0.85) for c in rgb)
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


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("상세페이지 제작 도구")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLORS['bg'])
        
        self.env_path = Path('.env')
        if DOTENV_AVAILABLE and self.env_path.exists():
            load_dotenv(self.env_path)
        
        self.settings = AppSettings()
        self.stop_event = threading.Event()
        self.worker: Optional[threading.Thread] = None
        self.log_queue: "queue.Queue[str]" = queue.Queue()

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
        # 메인 컨테이너
        container = tk.Frame(self.root, bg=COLORS['bg'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 좌측 패널 (설정)
        left = tk.Frame(container, bg=COLORS['bg'])
        left.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 우측 패널 (로그)
        right = tk.Frame(container, bg=COLORS['bg'])
        right.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # === 좌측: 설정 ===
        # 헤더
        tk.Label(left, text="📋 상세페이지 제작",
                font=('Segoe UI', 18, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg']).pack(anchor='w', pady=(0, 5))
        
        tk.Label(left, text="Google Sheets → AI → 이미지 자동 생성",
                font=('Segoe UI', 9),
                fg=COLORS['text_secondary'], bg=COLORS['bg']).pack(anchor='w', pady=(0, 20))
        
        # 설정 카드
        card = tk.Frame(left, bg=COLORS['card'], highlightbackground=COLORS['border'],
                       highlightthickness=1)
        card.pack(fill='both', pady=(0, 10))
        
        inside = tk.Frame(card, bg=COLORS['card'])
        inside.pack(fill='both', padx=16, pady=16)
        
        # 변수
        self.var_openai = tk.StringVar()
        self.var_hcti_user = tk.StringVar()
        self.var_hcti_key = tk.StringVar()
        self.var_webapp_url = tk.StringVar()
        self.var_output_dir = tk.StringVar()
        
        # 간단한 입력 필드
        self._add_field(inside, "OpenAI API Key", self.var_openai, show="*")
        self._add_field(inside, "HCTI User ID", self.var_hcti_user)
        self._add_field(inside, "HCTI API Key", self.var_hcti_key, show="*")
        self._add_field(inside, "Apps Script URL", self.var_webapp_url)
        
        # 출력 폴더
        folder_frame = tk.Frame(inside, bg=COLORS['card'])
        folder_frame.pack(fill='x', pady=(8, 0))
        
        tk.Label(folder_frame, text="저장 폴더",
                font=('Segoe UI', 9, 'bold'),
                fg=COLORS['text'], bg=COLORS['card']).pack(anchor='w', pady=(0, 4))
        
        folder_input = tk.Frame(folder_frame, bg=COLORS['card'])
        folder_input.pack(fill='x')
        
        entry_frame = tk.Frame(folder_input, bg=COLORS['card'],
                              highlightbackground=COLORS['border'],
                              highlightthickness=1)
        entry_frame.pack(side='left', fill='x', expand=True, padx=(0, 6))
        
        tk.Entry(entry_frame, textvariable=self.var_output_dir,
                font=('Segoe UI', 9), fg=COLORS['text'],
                bg=COLORS['card'], relief='flat', bd=0).pack(fill='x', padx=10, pady=8)
        
        RoundedButton(folder_input, "선택", self._pick_output_dir,
                     bg_color=COLORS['text_secondary'], width=70, height=34).pack(side='left')
        
        # 버튼 영역
        btn_card = tk.Frame(left, bg=COLORS['card'],
                           highlightbackground=COLORS['border'],
                           highlightthickness=1)
        btn_card.pack(fill='x', pady=(0, 10))
        
        btn_inside = tk.Frame(btn_card, bg=COLORS['card'])
        btn_inside.pack(fill='both', padx=16, pady=16)
        
        tk.Label(btn_inside, text="⚡ 실행",
                font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['card']).pack(anchor='w', pady=(0, 12))
        
        btn_row1 = tk.Frame(btn_inside, bg=COLORS['card'])
        btn_row1.pack(fill='x', pady=(0, 6))
        
        RoundedButton(btn_row1, "💾 설정 저장", self._save_to_env,
                     bg_color=COLORS['success'], width=145, height=44).pack(side='left', padx=(0, 6))
        RoundedButton(btn_row1, "▶ 한 번 실행", self.run_once,
                     bg_color=COLORS['primary'], width=145, height=44).pack(side='left')
        
        btn_row2 = tk.Frame(btn_inside, bg=COLORS['card'])
        btn_row2.pack(fill='x')
        
        RoundedButton(btn_row2, "🔄 연속 실행", self.start_loop,
                     bg_color=COLORS['primary'], width=145, height=44).pack(side='left', padx=(0, 6))
        RoundedButton(btn_row2, "⏸ 중지", self.stop_loop,
                     bg_color=COLORS['error'], width=145, height=44).pack(side='left')
        
        # 상태 표시
        status_card = tk.Frame(left, bg=COLORS['card'],
                              highlightbackground=COLORS['border'],
                              highlightthickness=1)
        status_card.pack(fill='x')
        
        status_inside = tk.Frame(status_card, bg=COLORS['card'])
        status_inside.pack(fill='both', padx=16, pady=12)
        
        tk.Label(status_inside, text="● 상태",
                font=('Segoe UI', 9),
                fg=COLORS['text_secondary'], bg=COLORS['card']).pack(anchor='w')
        
        self.status_label = tk.Label(status_inside, text="대기 중",
                                     font=('Segoe UI', 14, 'bold'),
                                     fg=COLORS['text'], bg=COLORS['card'])
        self.status_label.pack(anchor='w', pady=(4, 0))
        
        # === 우측: 로그 ===
        tk.Label(right, text="📋 실행 로그",
                font=('Segoe UI', 18, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg']).pack(anchor='w', pady=(0, 20))
        
        log_card = tk.Frame(right, bg=COLORS['card'],
                           highlightbackground=COLORS['border'],
                           highlightthickness=1)
        log_card.pack(fill='both', expand=True)
        
        log_header = tk.Frame(log_card, bg=COLORS['card'])
        log_header.pack(fill='x', padx=16, pady=(12, 0))
        
        RoundedButton(log_header, "지우기", self.clear_log,
                     bg_color=COLORS['text_secondary'], width=80, height=30).pack(side='right')
        
        log_content = tk.Frame(log_card, bg=COLORS['card'])
        log_content.pack(fill='both', expand=True, padx=16, pady=(8, 16))
        
        self.txt_log = tk.Text(log_content,
                              font=('Consolas', 9),
                              fg=COLORS['text'],
                              bg='#F8F9FA',
                              relief='flat',
                              wrap=tk.WORD,
                              state=tk.DISABLED)
        
        scrollbar = tk.Scrollbar(log_content, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        
        self.txt_log.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _add_field(self, parent, label, var, show=None):
        frame = tk.Frame(parent, bg=COLORS['card'])
        frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(frame, text=label,
                font=('Segoe UI', 9, 'bold'),
                fg=COLORS['text'], bg=COLORS['card']).pack(anchor='w', pady=(0, 4))
        
        entry_frame = tk.Frame(frame, bg=COLORS['card'],
                              highlightbackground=COLORS['border'],
                              highlightthickness=1)
        entry_frame.pack(fill='x')
        
        entry = tk.Entry(entry_frame, textvariable=var,
                        font=('Segoe UI', 9),
                        fg=COLORS['text'],
                        bg=COLORS['card'],
                        relief='flat',
                        show=show,
                        bd=0)
        entry.pack(fill='x', padx=10, pady=8)
        
        entry.bind('<FocusIn>', lambda e: entry_frame.config(
            highlightbackground=COLORS['primary'], highlightthickness=2))
        entry.bind('<FocusOut>', lambda e: entry_frame.config(
            highlightbackground=COLORS['border'], highlightthickness=1))

    def _load_from_env(self):
        self.var_openai.set(os.getenv('OPENAI_API_KEY', ''))
        self.var_hcti_user.set(os.getenv('HCTI_USER_ID', ''))
        self.var_hcti_key.set(os.getenv('HCTI_API_KEY', ''))
        self.var_webapp_url.set(os.getenv('SHEETS_WEB_APP_URL', ''))
        self.var_output_dir.set(os.getenv('OUTPUT_DIR', ''))

    def _save_to_env(self):
        if not DOTENV_AVAILABLE:
            messagebox.showwarning("경고", "python-dotenv가 설치되지 않았습니다.")
            return
        
        try:
            env_vars = {
                'OPENAI_API_KEY': self.var_openai.get().strip(),
                'HCTI_USER_ID': self.var_hcti_user.get().strip(),
                'HCTI_API_KEY': self.var_hcti_key.get().strip(),
                'SHEETS_WEB_APP_URL': self.var_webapp_url.get().strip(),
                'OUTPUT_DIR': self.var_output_dir.get().strip(),
            }
            
            for key, value in env_vars.items():
                set_key(self.env_path, key, value)
            
            self._append_log("✅ 설정이 저장되었습니다.")
            messagebox.showinfo("완료", "설정이 .env 파일에 저장되었습니다.")
            
        except Exception as e:
            self._append_log(f"❌ 저장 실패: {e}")
            messagebox.showerror("오류", f"설정 저장 실패:\n{e}")

    def _pick_output_dir(self):
        path = filedialog.askdirectory(title="결과물 저장 폴더 선택")
        if path:
            self.var_output_dir.set(path)

    def _apply_env(self):
        os.environ["OPENAI_API_KEY"] = self.var_openai.get().strip()
        os.environ["HCTI_USER_ID"] = self.var_hcti_user.get().strip()
        os.environ["HCTI_API_KEY"] = self.var_hcti_key.get().strip()
        os.environ["SHEETS_WEB_APP_URL"] = self.var_webapp_url.get().strip()

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

            html = art.get("html", "")
            (out_path / f"{fname_base}.html").write_text(html, encoding="utf-8")

            data = art.get("data", {})
            (out_path / f"{fname_base}.json").write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")), 
                encoding="utf-8"
            )

            url = art.get("image_url")
            if url:
                try:
                    r = requests.get(url, timeout=120)
                    if r.status_code == 200:
                        (out_path / f"{fname_base}.png").write_bytes(r.content)
                        self._append_log(f"💾 저장됨: {fname_base}.png")
                except Exception as ex:
                    logging.warning("이미지 저장 실패: %s", ex)

        return cb

    def run_once(self):
        """백그라운드 스레드에서 한 번 실행"""
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("알림", "이미 실행 중입니다.")
            return
        
        def worker():
            try:
                self._update_status("실행 중...", COLORS['warning'])
                self._apply_env()
                
                config = pipeline.load_config(poll_interval=60)
                client = pipeline.OpenAI(api_key=config.openai_api_key)

                rows = pipeline.fetch_rows(
                    os.getenv("WATCH_SPREADSHEET_ID", "1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c"), 
                    os.getenv("WATCH_SHEET_NAME", "시트1")
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
                    self._update_status("대기 중", COLORS['text'])
                else:
                    self._append_log(f"✅ 완료: 행 {processed_any}")
                    self._update_status("완료", COLORS['success'])
                    
            except Exception as exc:
                logging.exception("실행 실패: %s", exc)
                self._update_status("오류", COLORS['error'])
                self.root.after(0, lambda: messagebox.showerror("오류", f"실행 실패:\n{exc}"))
            finally:
                self.worker = None
        
        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _loop_worker(self):
        processed_count = 0
        try:
            self._apply_env()
            config = pipeline.load_config(poll_interval=60)
            client = pipeline.OpenAI(api_key=config.openai_api_key)
            on_artifacts = self._make_on_artifacts()

            while not self.stop_event.is_set():
                rows = pipeline.fetch_rows(
                    os.getenv("WATCH_SPREADSHEET_ID", "1P6F7Z7V6CALlotkcP6bzZHYNTXILbItj7pevVk13L9c"), 
                    os.getenv("WATCH_SHEET_NAME", "시트1")
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
                    
                if processed_any is None:
                    self._update_status("대기 중", COLORS['text_secondary'])
                else:
                    self._update_status(f"실행 중 ({processed_count}건)", COLORS['success'])
                    
                for _ in range(60):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
        except Exception as exc:
            logging.exception("연속 실행 실패: %s", exc)
            self._update_status("오류", COLORS['error'])
        finally:
            self.worker = None
            self.stop_event.clear()
            self._update_status("중지됨", COLORS['text_secondary'])

    def start_loop(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("알림", "이미 실행 중입니다.")
            return
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._loop_worker, daemon=True)
        self.worker.start()
        self._update_status("실행 중...", COLORS['primary'])
        self._append_log("🔄 연속 실행 시작")

    def stop_loop(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self._append_log("⏸  중지 요청...")

    def clear_log(self):
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.configure(state=tk.DISABLED)

    def _append_log(self, text: str):
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state=tk.DISABLED)

    def _update_status(self, text: str, color: str):
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

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
