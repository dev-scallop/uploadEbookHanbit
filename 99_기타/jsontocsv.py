#!/usr/bin/env python3
"""
Stream a very large JSON file (~GBs) into CSV without loading everything into memory.

Features:
- Supports NDJSON (one JSON object per line), a single large JSON array, JSON-LD with @graph,
  and concatenated JSON objects.
- Two-pass safe mode: sample first N items to auto-detect fields (default 1000). This avoids
  scanning the whole 5GB file twice while producing meaningful headers.
- Option to provide explicit field list (recommended for stable schema and best performance).
- Nested objects are flattened with dot notation by default.

Usage examples:
  python jsontocsv.py -i large.json -o out.csv --mode ndjson --fields title,publisher,year
  python jsontocsv.py -i large.json -o out.csv --mode auto --sample-size 500

Requirements:
  pip install ijson

"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from typing import Any, Dict, Iterable, Iterator, List, Set

try:
    # prefer faster yajl backend if available
    import ijson.backends.yajl2_c as ijson
except Exception:
    import ijson
from ijson.common import JSONError


def flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Flatten nested dicts into dot.notation keys. Lists are JSON-dumped.
    Non-dict scalars are returned as-is.
    """
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten(v, key))
    elif isinstance(obj, list):
        # convert lists to JSON string to keep CSV cell single-valued
        out[prefix] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix] = obj
    return out


def concat_json_iterator(path: str, encoding: str = "utf-8") -> Iterator[Any]:
    """Iterator that parses concatenated JSON documents or NDJSON using raw_decode.
    Yields parsed JSON objects (or array elements if top-level is array).
    """
    decoder = json.JSONDecoder()
    with open(path, "r", encoding=encoding) as fh:
        buffer = ""
        for chunk in iter(lambda: fh.read(65536), ""):
            buffer += chunk
            buffer = buffer.lstrip()
            while buffer:
                try:
                    obj, idx = decoder.raw_decode(buffer)
                except ValueError:
                    # need more data
                    break
                if isinstance(obj, list):
                    for it in obj:
                        yield it
                else:
                    yield obj
                buffer = buffer[idx:]
                buffer = buffer.lstrip()
        # EOF: attempt to decode remainder
        buffer = buffer.lstrip()
        while buffer:
            try:
                obj, idx = decoder.raw_decode(buffer)
            except ValueError:
                break
            if isinstance(obj, list):
                for it in obj:
                    yield it
            else:
                yield obj
            buffer = buffer[idx:]
            buffer = buffer.lstrip()


def stream_items(path: str, mode: str = "auto") -> Iterator[Any]:
    """Yield JSON objects from path using the chosen mode.
    mode: auto | json-ld | array | ndjson | concat
    """
    mode = mode.lower()
    # auto tries json-ld(@graph) then array then concat
    if mode == "json-ld" or mode == "json-ld(@graph)":
        with open(path, "rb") as f:
            for item in ijson.items(f, "@graph.item"):
                yield item
        return
    if mode == "array":
        with open(path, "rb") as f:
            for item in ijson.items(f, "item"):
                yield item
        return
    if mode == "ndjson" or mode == "concat":
        for item in concat_json_iterator(path):
            yield item
        return

    # auto mode
    # 1) try @graph
    try:
        with open(path, "rb") as f:
            for item in ijson.items(f, "@graph.item"):
                yield item
        return
    except Exception:
        pass
    # 2) try array
    try:
        with open(path, "rb") as f:
            for item in ijson.items(f, "item"):
                yield item
        return
    except Exception:
        pass
    # 3) fallback
    for item in concat_json_iterator(path):
        yield item


def detect_fields(path: str, mode: str, sample_size: int = 1000, flatten_nested: bool = True) -> List[str]:
    """Scan up to sample_size items to detect set of fields (flattened).
    Returns ordered list of fields discovered.
    """
    fields: List[str] = []
    seen: Set[str] = set()
    it = stream_items(path, mode)
    for i, obj in enumerate(it):
        if i >= sample_size:
            break
        if not isinstance(obj, dict):
            continue
        if flatten_nested:
            flat = flatten(obj)
        else:
            flat = {k: v for k, v in obj.items()}
        for k in flat.keys():
            if k not in seen:
                seen.add(k)
                fields.append(k)
    return fields


def write_csv(input_path: str, output_path: str, mode: str, fields: List[str] | None,
              sample_size: int = 1000, flatten_nested: bool = True, max_items: int | None = None,
              encoding: str = "utf-8-sig"):
    start = time.time()
    # determine fields
    if fields:
        chosen = fields
    else:
        print(f"Detecting fields from first {sample_size} items (this is fast)...")
        chosen = detect_fields(input_path, mode, sample_size=sample_size, flatten_nested=flatten_nested)
        if not chosen:
            print("No fields detected from sample. Try specifying --fields or use a different --mode.")
            return

    print(f"Using {len(chosen)} fields. Writing CSV to: {output_path}")

    # Use a Windows/Excel-friendly default encoding: UTF-8 with BOM (utf-8-sig).
    # For older Excel versions in Korean locales, 'cp949' may be preferred.
    with open(output_path, "w", newline="", encoding=encoding) as outfh:
        writer = csv.DictWriter(outfh, fieldnames=chosen, extrasaction="ignore")
        writer.writeheader()
        count = 0
        matched = 0
        for item in stream_items(input_path, mode):
            if max_items is not None and count >= max_items:
                break
            count += 1
            if not isinstance(item, dict):
                continue
            row = flatten(item) if flatten_nested else item
            # ensure values are strings or primitives; lists already json-dumped in flatten
            safe_row = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                        for k, v in row.items() if k in chosen}
            writer.writerow(safe_row)
            if count % 10000 == 0:
                elapsed = time.time() - start
                print(f"  {count:,} items processed ({elapsed:.0f}s)")

    elapsed = time.time() - start
    print(f"Done. Written {count:,} rows to {output_path} in {elapsed:.1f}s")


def parse_comma_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def main(argv: List[str] | None = None):
    p = argparse.ArgumentParser(description="Stream JSON -> CSV for very large files")
    p.add_argument("-i", "--input", required=True, help="Input JSON file path")
    p.add_argument("-o", "--output", required=True, help="Output CSV path")
    p.add_argument("--mode", default="auto", choices=["auto", "json-ld(@graph)", "json-ld",
                                                          "array", "ndjson", "concat"],
                   help="Parsing mode. 'auto' will try json-ld, array, then concat")
    p.add_argument("--fields", help="Comma-separated list of fields to include (use dot for nested)")
    p.add_argument("--sample-size", type=int, default=1000, help="Number of items to sample for field detection")
    p.add_argument("--no-flatten", dest="flatten", action="store_false", help="Don't flatten nested objects")
    p.add_argument("--encoding", default="utf-8-sig", choices=["utf-8-sig", "utf-8", "cp949"],
                   help="Output file encoding. 'utf-8-sig' adds BOM so Excel recognizes UTF-8. 'cp949' for legacy Korean Excel.")
    p.add_argument("--max-items", type=int, default=None, help="Stop after N items (useful for tests)")
    args = p.parse_args(argv)

    fields = parse_comma_list(args.fields) if args.fields else None
    write_csv(args.input, args.output, args.mode, fields, sample_size=args.sample_size,
              flatten_nested=args.flatten, max_items=args.max_items, encoding=args.encoding)


class JsonToCsvGUI:
    def __init__(self, root):
        self.root = root
        root.title("JSON → CSV 변환기")
        root.geometry("720x520")

        self.input_path = tk.StringVar(value="입력 JSON 파일을 선택하세요.")
        self.output_dir = tk.StringVar(value="출력 폴더를 선택하세요.")
        self.mode = tk.StringVar(value="auto")
        self.encoding = tk.StringVar(value="utf-8-sig")
        self.fields = tk.StringVar(value="")
        self.sample_size = tk.IntVar(value=1000)

        frm = ttk.LabelFrame(root, text="설정")
        frm.pack(fill="x", padx=10, pady=8)

        ttk.Button(frm, text="입력 파일 선택", command=self.select_input).grid(row=0, column=0, padx=6, pady=6)
        ttk.Label(frm, textvariable=self.input_path, width=70, relief="sunken").grid(row=0, column=1, padx=6, pady=6)

        ttk.Button(frm, text="출력 폴더 선택", command=self.select_output_dir).grid(row=1, column=0, padx=6, pady=6)
        ttk.Label(frm, textvariable=self.output_dir, width=70, relief="sunken").grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(frm, text="파싱 모드:").grid(row=2, column=0, padx=6, pady=6)
        ttk.Combobox(frm, textvariable=self.mode, values=["auto", "json-ld(@graph)", "array", "ndjson", "concat"], state="readonly", width=30).grid(row=2, column=1, padx=6, pady=6, sticky='w')

        ttk.Label(frm, text="출력 인코딩:").grid(row=5, column=0, padx=6, pady=6)
        ttk.Combobox(frm, textvariable=self.encoding, values=["utf-8-sig", "utf-8", "cp949"], state="readonly", width=30).grid(row=5, column=1, padx=6, pady=6, sticky='w')

        ttk.Label(frm, text="필드(콤마 구분, 비워두면 자동감지):").grid(row=3, column=0, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.fields, width=72).grid(row=3, column=1, padx=6, pady=6)

        ttk.Label(frm, text="샘플 크기:").grid(row=4, column=0, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.sample_size, width=12).grid(row=4, column=1, padx=6, pady=6, sticky='w')

        self.start_btn = ttk.Button(root, text="변환 시작", command=self.start)
        self.start_btn.pack(pady=6)

        log_frame = ttk.LabelFrame(root, text="로그")
        log_frame.pack(fill="both", expand=True, padx=10, pady=6)
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_widget.pack(fill="both", expand=True, padx=6, pady=6)

    def select_input(self):
        fp = filedialog.askopenfilename(title="JSON 파일 선택", filetypes=[("JSON files", "*.json *.ndjson")])
        if fp:
            self.input_path.set(fp)
            self.log(f"입력 파일: {fp}")

    def select_output_dir(self):
        d = filedialog.askdirectory(title="출력 폴더 선택")
        if d:
            self.output_dir.set(d)
            self.log(f"출력 폴더: {d}")

    def log(self, msg: str):
        self.log_widget.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_widget.see(tk.END)

    def start(self):
        inp = self.input_path.get()
        outdir = self.output_dir.get()
        if not os.path.isfile(inp):
            self.log("입력 파일을 선택하세요.")
            return
        if not os.path.isdir(outdir):
            self.log("출력 폴더를 선택하세요.")
            return
        basename = os.path.splitext(os.path.basename(inp))[0]
        outpath = os.path.join(outdir, basename + ".csv")
        mode = self.mode.get()
        fields = parse_comma_list(self.fields.get()) if self.fields.get().strip() else None
        sample = int(self.sample_size.get())

        self.start_btn.config(state="disabled", text="처리 중...")
        self.log(f"변환 시작: {inp} -> {outpath} (mode={mode})")

        def worker():
            try:
                enc = self.encoding.get()
                write_csv(inp, outpath, mode, fields, sample_size=sample, encoding=enc)
                self.log(f"완료: {outpath} (encoding={enc})")
            except Exception as e:
                self.log(f"오류 발생: {e}\n{repr(e)}")
            finally:
                self.start_btn.config(state="normal", text="변환 시작")

        th = threading.Thread(target=worker, daemon=True)
        th.start()


if __name__ == "__main__":
    # If script launched without CLI args, open GUI
    if len(sys.argv) == 1:
        root = tk.Tk()
        app = JsonToCsvGUI(root)
        root.mainloop()
    else:
        main()
