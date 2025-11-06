import re
import pandas as pd
import openpyxl
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os

# ------------------------------
# 도서 데이터 파싱 함수
# ------------------------------
def parse_books(text, publisher_name):
    # 항목 구분 (예: [종이책], [전자출판물], [무료체험판] 기준)
    blocks = re.split(r'\[\s*(?:종이책|전자출판물|무료체험판)\s*\]\s*\d*\.\s*', text)
    results = []
    for b in blocks:
        b = b.strip()
        if not b or len(b) < 10:
            continue

        # 정규식 패턴으로 각 항목 추출
        title = re.search(r'^\d*\.?\s*(.*?)\n', b)
        author = re.search(r'저자\s*:\s*(.*?)\n', b)
        publisher = re.search(r'발행처\s*:\s*(.*?)\n', b)
        isbn = re.search(r'ISBN\s*:\s*([\d\-]+.*)\n', b)
        binding = re.search(r'제본형태\s*:\s*(.*?)\n', b)
        date = re.search(r'발행\(예정\)일\s*:\s*(.*?)\n', b)
        price = re.search(r'가격\s*:\s*(.*?)\n', b)

        results.append({
            "출판사명": publisher_name,
            "도서명": title.group(1).strip() if title else "",
            "저자": author.group(1).strip() if author else "",
            "발행처": publisher.group(1).strip() if publisher else "",
            "ISBN": isbn.group(1).strip() if isbn else "",
            "제본형태": binding.group(1).strip() if binding else "",
            "발행(예정)일": date.group(1).strip() if date else "",
            "가격": price.group(1).strip() if price else "",
        })
    return results


# ------------------------------
# 엑셀 처리 함수
# ------------------------------
def process_excel(file_path, progress_var, log_box, run_button):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    total = len(rows)
    all_results = []
    idx = 1

    for i, row in enumerate(rows, start=1):
        publisher, text = row
        if not text:
            continue

        # 텍스트 파싱 후 결과 누적
        books = parse_books(text, publisher)
        for b in books:
            b["번호"] = idx
            idx += 1
            all_results.append(b)

        progress_var.set(int(i / total * 100))
        log_box.insert("end", f"✅ {publisher} ({i}/{total}) 변환 완료\n")
        log_box.see("end")

    # DataFrame 생성 및 열 순서 지정
    df = pd.DataFrame(all_results, columns=["번호", "출판사명", "도서명", "저자", "발행처", "ISBN", "제본형태", "발행(예정)일", "가격"])
    
    # 저장 경로
    output_path = os.path.join(os.path.dirname(file_path), "도서정보_정리결과.xlsx")
    df.to_excel(output_path, index=False)

    log_box.insert("end", f"\n🎯 모든 변환 완료 → {output_path}\n")
    messagebox.showinfo("완료", f"엑셀 파일이 저장되었습니다:\n{output_path}")
    progress_var.set(100)
    run_button.config(state="normal")


# ------------------------------
# 스레드 실행
# ------------------------------
def run_in_thread(file_path, progress_var, log_box, run_button):
    run_button.config(state="disabled")
    thread = threading.Thread(target=process_excel, args=(file_path, progress_var, log_box, run_button))
    thread.start()


# ------------------------------
# 파일 선택
# ------------------------------
def open_file():
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )
    if file_path:
        run_in_thread(file_path, progress_var, log_box, run_button)


# ------------------------------
# GUI 구성
# ------------------------------
root = tk.Tk()
root.title("도서정보 자동 표 변환기 (출판사명 포함 버전)")
root.geometry("600x450")

ttk.Label(root, text="📗 출판사명 | 결과텍스트 자동 표 변환기", font=("맑은 고딕", 13, "bold")).pack(pady=10)
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

run_button = ttk.Button(root, text="엑셀 파일 선택 및 실행", command=open_file)
run_button.pack(pady=5)

log_box = scrolledtext.ScrolledText(root, width=70, height=15, wrap="word")
log_box.pack(pady=10)
log_box.insert("end", "준비 완료. 엑셀 파일을 선택하세요.\n")

root.mainloop()
