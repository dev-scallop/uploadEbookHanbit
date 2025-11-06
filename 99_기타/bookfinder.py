import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading, time, json, itertools, traceback, gc, os
import openpyxl

try:
    import ijson.backends.yajl2_c as ijson
except Exception:
    import ijson
from ijson.common import JSONError


class FileProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("국립중앙도서관 Offline JSON-LD 폴더 매칭 도구")
        self.root.geometry("700x550")

        self.folder_path = tk.StringVar(value="JSON 파일 폴더를 선택하세요.")
        self.excel_path = tk.StringVar(value="엑셀 파일을 선택하세요.")

        # -------- 폴더/파일 선택 UI --------
        file_frame = ttk.LabelFrame(root, text="파일 선택")
        file_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(file_frame, text="JSON 폴더 선택", width=15,
                   command=self.select_folder).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(file_frame, textvariable=self.folder_path, relief="sunken",
                  width=80).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="엑셀 파일 선택", width=15,
                   command=self.select_excel).grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(file_frame, textvariable=self.excel_path, relief="sunken",
                  width=80).grid(row=1, column=1, padx=5, pady=5)
        # 파싱 모드 선택 (auto, json-ld(@graph), array, ndjson, concat)
        ttk.Label(file_frame, text="파싱 모드:").grid(row=2, column=0, padx=5, pady=5)
        self.parse_mode = tk.StringVar(value="auto")
        parse_combo = ttk.Combobox(
            file_frame,
            textvariable=self.parse_mode,
            values=["auto", "json-ld(@graph)", "array", "ndjson", "concat"],
            state="readonly",
            width=24,
        )
        parse_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        parse_combo.set("auto")

        self.start_button = ttk.Button(root, text="처리 시작",
                                       command=self.start_processing_thread)
        self.start_button.pack(pady=10)

        log_frame = ttk.LabelFrame(root, text="진행 상황")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_widget = scrolledtext.ScrolledText(log_frame, width=80, height=20, wrap=tk.WORD)
        self.log_widget.pack(fill="both", expand=True, padx=5, pady=5)
        self.log("시스템 준비 완료. JSON 폴더와 엑셀을 선택하세요.")

    # -------------------------------------------------

    def log(self, msg):
        self.log_widget.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_widget.see(tk.END)

    def update_log_safe(self, msg):
        self.root.after(0, self.log, msg)

    def select_folder(self):
        folder = filedialog.askdirectory(title="JSON 파일이 들어있는 폴더 선택")
        if folder:
            self.folder_path.set(folder)
            self.log(f"폴더 선택됨: {folder}")

    def select_excel(self):
        fp = filedialog.askopenfilename(title="출판사 목록 엑셀 파일 선택",
                                        filetypes=[("Excel files", "*.xlsx *.xls")])
        if fp:
            self.excel_path.set(fp)
            self.log(f"엑셀 파일 로드됨: {fp}")

    # -------------------------------------------------

    def start_processing_thread(self):
        folder, excel = self.folder_path.get(), self.excel_path.get()
        if "파일" in folder or "파일" in excel:
            self.log("!!! 오류: JSON 폴더와 엑셀 파일을 모두 선택해야 합니다.")
            return
        self.start_button.config(state="disabled", text="처리 중...")
        self.log("--- 작업 스레드 시작 ---")
        th = threading.Thread(target=self.process_folder, args=(folder, excel), daemon=True)
        th.start()

    # -------------------------------------------------

    def process_folder(self, folder, excel_file):
        try:
            normalize = lambda s: ''.join(str(s).lower().split())
            pubs = set()

            # --- 엑셀 로드 ---
            self.update_log_safe("엑셀 파일에서 출판사 목록 읽는 중...")
            try:
                wb = openpyxl.load_workbook(excel_file, read_only=True)
                ws = wb.active
                for r in ws.iter_rows(min_row=1, max_col=1, values_only=True):
                    if r[0]:
                        pubs.add(normalize(r[0]))
                wb.close()
            except Exception as e:
                self.update_log_safe(f"엑셀 읽기 오류: {e}")
                return
            if not pubs:
                self.update_log_safe("엑셀의 첫 열에 출판사명이 없습니다.")
                return
            self.update_log_safe(f"✅ {len(pubs)}개 출판사명 로드 완료.")

            # --- 폴더 내 JSON 파일 목록 ---
            json_files = sorted([os.path.join(folder, f)
                                 for f in os.listdir(folder)
                                 if f.lower().endswith(".json")])
            if not json_files:
                self.update_log_safe("폴더 내에 JSON 파일이 없습니다.")
                return
            self.update_log_safe(f"총 {len(json_files)}개 JSON 파일 탐색됨.")

            total_all, found_all = 0, 0
            for idx, path in enumerate(json_files, 1):
                self.update_log_safe(f"({idx}/{len(json_files)}) 처리 중: {os.path.basename(path)}")
                total, found = self.process_single_json(path, pubs)
                total_all += total
                found_all += found
                self.update_log_safe(f" └ 완료: {found}/{total}건 매칭")

            self.update_log_safe(f"🏁 전체 완료: 총 {total_all:,}건 중 {found_all:,}건 일치")

        except Exception as e:
            self.update_log_safe(f"!!! 처리 중 오류: {e}\n{traceback.format_exc(limit=3)}")
        finally:
            self.root.after(0, lambda: self.start_button.config(state="normal", text="처리 시작"))

    # -------------------------------------------------

    def process_single_json(self, path, pubs):
        """개별 JSON 파일(@graph 구조)을 처리"""
        normalize = lambda s: ''.join(str(s).lower().split())
        total, found, last_log = 0, 0, time.time()
        def sample_file(p, n=1024):
            try:
                with open(p, 'r', encoding='utf-8') as fh:
                    return fh.read(n)
            except Exception:
                try:
                    with open(p, 'rb') as fh:
                        return fh.read(n).decode('utf-8', errors='replace')
                except Exception:
                    return ''

        def concat_json_iterator(p, encoding='utf-8'):
            decoder = json.JSONDecoder()
            with open(p, 'r', encoding=encoding) as fh:
                buffer = ''
                for chunk in iter(lambda: fh.read(65536), ''):
                    buffer += chunk
                    buffer = buffer.lstrip()
                    while buffer:
                        try:
                            obj, idx = decoder.raw_decode(buffer)
                            if isinstance(obj, list):
                                for it in obj:
                                    yield it
                            else:
                                yield obj
                            buffer = buffer[idx:]
                            buffer = buffer.lstrip()
                        except ValueError:
                            break
                buffer = buffer.lstrip()
                while buffer:
                    try:
                        obj, idx = decoder.raw_decode(buffer)
                        if isinstance(obj, list):
                            for it in obj:
                                yield it
                        else:
                            yield obj
                        buffer = buffer[idx:]
                        buffer = buffer.lstrip()
                    except ValueError:
                        break

        mode = getattr(self, 'parse_mode', tk.StringVar(value='auto')).get()

        def process_iterable(it):
            nonlocal total, found, last_log
            for book in it:
                total += 1
                if not isinstance(book, dict):
                    continue
                pub = book.get('publisher')
                if pub and normalize(pub) in pubs:
                    found += 1
                    self.update_log_safe(f"  - {book.get('title','제목 없음')} ({pub})")
                if total % 10000 == 0:
                    gc.collect()
                    if time.time() - last_log > 5:
                        self.update_log_safe(f"    ... {total:,}개 항목 처리 중 ...")
                        last_log = time.time()

        try:
            # 강제 모드 지정
            if mode == 'json-ld(@graph)':
                try:
                    with open(path, 'rb') as f:
                        process_iterable(ijson.items(f, '@graph.item'))
                except Exception as e:
                    self.update_log_safe(f"⚠ json-ld(@graph) 강제 파싱 실패: {e}\n{self.explain_exception(e)}")
                    self.update_log_safe(f"파일 앞부분 샘플:\n{sample_file(path,1024)}")
            elif mode == 'array':
                try:
                    with open(path, 'rb') as f:
                        process_iterable(ijson.items(f, 'item'))
                except Exception as e:
                    self.update_log_safe(f"⚠ array 강제 파싱 실패: {e}\n{self.explain_exception(e)}")
                    self.update_log_safe(f"파일 앞부분 샘플:\n{sample_file(path,1024)}")
            elif mode in ('ndjson', 'concat'):
                try:
                    process_iterable(concat_json_iterator(path))
                except Exception as e:
                    self.update_log_safe(f"⚠ NDJSON/concat 파싱 실패: {e}\n{self.explain_exception(e)}")
                    self.update_log_safe(f"파일 앞부분 샘플:\n{sample_file(path,1024)}")
            else:
                # auto: 시도-대체 전략
                tried = False
                try:
                    with open(path, 'rb') as f:
                        process_iterable(ijson.items(f, '@graph.item'))
                    tried = True
                except Exception as e1:
                    self.update_log_safe(f"⚠ ijson('@graph.item') 파싱 오류: {e1}\n{self.explain_exception(e1)}")
                if not tried:
                    try:
                        with open(path, 'rb') as f:
                            process_iterable(ijson.items(f, 'item'))
                        tried = True
                    except Exception as e2:
                        self.update_log_safe(f"⚠ ijson('item') 파싱 오류: {e2}\n{self.explain_exception(e2)}")
                if not tried:
                    try:
                        process_iterable(concat_json_iterator(path))
                    except Exception as e3:
                        self.update_log_safe(f"⚠ concatenated 파싱도 실패: {e3}\n{self.explain_exception(e3)}")
                        self.update_log_safe(f"파일 앞부분 샘플:\n{sample_file(path,1024)}")
        except Exception as e:
            self.update_log_safe(f"⚠ 파일 {path} 처리 오류: {e}\n{self.explain_exception(e)}")

        return total, found


# -------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FileProcessorApp(root)
    root.mainloop()