# [복사본] 새 이름으로 변경된 파일입니다.
# 이 파일은 기존 파일을 새 이름으로 복사한 것입니다.
# 원본 파일명: data.py
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
import re

# CustomTkinter 설정
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# 색상 정의 (토스뱅크 스타일)
COLORS = {
    "primary": "#3182F6",      # 밝은 블루
    "secondary": "#00D4AA",    # 민트
    "accent": "#32D74B",       # 라임
    "background": "#F8F9FA",   # 밝은 배경
    "surface": "#FFFFFF",      # 카드 배경
    "text_primary": "#1A1A1A", # 주요 텍스트
    "text_secondary": "#6B7280", # 보조 텍스트
    "border": "#E5E7EB",       # 테두리
    "success": "#10B981",      # 성공
    "warning": "#F59E0B",      # 경고
    "error": "#EF4444"         # 오류
}

def has_text(value):
    """셀에 한글, 영문, 숫자가 있는지 확인하는 함수"""
    return bool(re.search(r'[가-힣a-zA-Z0-9]', str(value)))

def process_excel():
    file_path = file_path_entry.get()
    if not file_path:
        messagebox.showerror("오류", "엑셀 파일을 선택해주세요.")
        return

    dept_keywords = dept_keyword_entry.get().split(',') if dept_keyword_entry.get() else []
    course_keywords = course_keyword_entry.get().split(',') if course_keyword_entry.get() else []
    textbook_keywords = textbook_keyword_entry.get().split(',') if textbook_keyword_entry.get() else []

    report_textbox.delete("0.0", "end")  # 이전 보고서 내용 삭제
    report = ""

    try:
        df = pd.read_excel(file_path)
        initial_row_count = len(df)
        report += f"📊 원본 데이터 행 수: {initial_row_count}\n\n"

        # 0. "교재명"과 "교수명" 열에 글자 없이 기호만 있는 행 삭제
        for col in ["교재명", "교수명"]:
            original_count = len(df)
            mask = df[col].apply(lambda x: not has_text(x))
            deleted_rows = df[mask]
            df = df[~mask].copy()
            deleted_count = original_count - len(df)
            report += f"🔍 '{col}' 열에 기호만 있는 행 삭제: {deleted_count}개 삭제\n"
            if deleted_count > 0:
                sample_deleted = deleted_rows.head().to_string()
                report += f"   삭제된 행 샘플:\n{sample_deleted}\n\n"
            else:
                report += "   ✅ 해당되는 행 없음\n\n"

        # 1. "교수명" 열에 데이터가 없는 행 삭제
        original_count = len(df)
        df.dropna(subset=["교수명"], inplace=True)
        deleted_count = original_count - len(df)
        report += f"👤 '교수명' 열이 비어있는 행 삭제: {deleted_count}개 삭제\n"
        if deleted_count > 0:
            sample_deleted = df[~df.index.isin(df.dropna(subset=["교수명"]).index)].head().to_string()
            report += f"   삭제된 행 샘플:\n{sample_deleted}\n\n"
        else:
            report += "   ✅ 해당되는 행 없음\n\n"

        # 2. "교수명" 열 공백 제거 및 3글자 제한
        df["교수명"] = df["교수명"].str.strip().str[:3]
        report += f"✂️ '교수명' 열 공백 제거 및 3글자 제한 적용\n\n"

        # 3, 4. 키워드 기반 행 삭제
        columns_keywords = {
            "학과": dept_keywords,
            "교과명": course_keywords,
            "교재명": textbook_keywords
        }

        for col, keywords in columns_keywords.items():
            if not keywords:
                continue
            original_count = len(df)
            mask = df[col].str.contains('|'.join(map(re.escape, keywords)), na=False, regex=True)

            deleted_rows = df[mask]
            df = df[~mask].copy()

            deleted_count = original_count - len(df)

            report += f"🗑️ '{col}' 열에 키워드 '{', '.join(keywords)}' 포함 행 삭제: {deleted_count}개 삭제\n"
            if deleted_count > 0:
                sample_deleted = deleted_rows.head().to_string()
                report += f"   삭제된 행 샘플:\n{sample_deleted}\n\n"
            else:
                report += "   ✅ 해당되는 행 없음\n\n"

        final_row_count = len(df)
        report += f"🎯 최종 데이터 행 수: {final_row_count}\n"

        report_textbox.insert("0.0", report)

        # 저장 기능 추가
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if save_path:
            try:
                df.to_excel(save_path, index=False)
                messagebox.showinfo("완료", "✅ 데이터 정리 및 저장 완료!")
            except Exception as e:
                messagebox.showerror("오류", f"파일 저장 중 오류 발생: {e}")

    except FileNotFoundError:
        messagebox.showerror("오류", "파일을 찾을 수 없습니다.")
    except Exception as e:
        messagebox.showerror("오류", f"오류 발생: {e}")

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    file_path_entry.delete(0, "end")
    file_path_entry.insert(0, file_path)

def clear_all():
    """모든 입력 필드 초기화"""
    file_path_entry.delete(0, "end")
    dept_keyword_entry.delete(0, "end")
    course_keyword_entry.delete(0, "end")
    textbook_keyword_entry.delete(0, "end")
    report_textbox.delete("0.0", "end")

# 메인 윈도우
app = ctk.CTk()
app.title("타사채택파일 정리 도구")
app.geometry("900x700")
app.configure(fg_color=COLORS["background"])

# 메인 컨테이너
main_container = ctk.CTkFrame(app, fg_color="transparent")
main_container.pack(fill="both", expand=True, padx=20, pady=20)

# 제목
title_label = ctk.CTkLabel(
    main_container, 
    text="📚 타사채택파일 정리 도구", 
    font=ctk.CTkFont(family="Roboto", size=24, weight="bold"),
    text_color=COLORS["text_primary"]
)
title_label.pack(pady=(0, 20))

# 설명
description_label = ctk.CTkLabel(
    main_container, 
    text="특정 엑셀파일의 특정 열마다 사용자가 입력한 키워드가 포함된 행을 삭제합니다.\n사용 방법: 엑셀파일 선택 후 제외할 키워드를 공백없이 쉼표(,)로 구분해 입력하세요.", 
    font=ctk.CTkFont(family="Roboto", size=12),
    text_color=COLORS["text_secondary"],
    wraplength=800
)
description_label.pack(pady=(0, 30))

# 파일 선택 카드
file_card = ctk.CTkFrame(main_container, fg_color=COLORS["surface"], corner_radius=12)
file_card.pack(fill="x", pady=(0, 20), padx=10)

file_card_title = ctk.CTkLabel(
    file_card, 
    text="📁 파일 선택", 
    font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
    text_color=COLORS["text_primary"]
)
file_card_title.pack(pady=(15, 10))

file_frame = ctk.CTkFrame(file_card, fg_color="transparent")
file_frame.pack(fill="x", padx=20, pady=(0, 15))

file_path_entry = ctk.CTkEntry(
    file_frame, 
    placeholder_text="엑셀 파일을 선택하세요...",
    font=ctk.CTkFont(family="Roboto", size=12),
    height=40
)
file_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

select_file_button = ctk.CTkButton(
    file_frame, 
    text="파일 선택",
    command=select_file,
    font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
    fg_color=COLORS["primary"],
    hover_color=COLORS["secondary"],
    height=40,
    width=100
)
select_file_button.pack(side="right")

# 키워드 입력 카드
keyword_card = ctk.CTkFrame(main_container, fg_color=COLORS["surface"], corner_radius=12)
keyword_card.pack(fill="x", pady=(0, 20), padx=10)

keyword_card_title = ctk.CTkLabel(
    keyword_card, 
    text="🔍 키워드 설정", 
    font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
    text_color=COLORS["text_primary"]
)
keyword_card_title.pack(pady=(15, 15))

# 키워드 입력 프레임들
keyword_inputs = [
    ("학과 키워드", "학과명에 포함된 키워드를 쉼표로 구분하여 입력하세요..."),
    ("교과명 키워드", "교과명에 포함된 키워드를 쉼표로 구분하여 입력하세요..."),
    ("교재명 키워드", "교재명에 포함된 키워드를 쉼표로 구분하여 입력하세요...")
]

keyword_entries = []
for i, (label_text, placeholder) in enumerate(keyword_inputs):
    keyword_frame = ctk.CTkFrame(keyword_card, fg_color="transparent")
    keyword_frame.pack(fill="x", padx=20, pady=(0, 10))
    
    keyword_label = ctk.CTkLabel(
        keyword_frame, 
        text=label_text,
        font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
        text_color=COLORS["text_primary"]
    )
    keyword_label.pack(anchor="w", pady=(0, 5))
    
    keyword_entry = ctk.CTkEntry(
        keyword_frame, 
        placeholder_text=placeholder,
        font=ctk.CTkFont(family="Roboto", size=12),
        height=35
    )
    keyword_entry.pack(fill="x")
    keyword_entries.append(keyword_entry)

# 키워드 엔트리 변수 할당
dept_keyword_entry = keyword_entries[0]
course_keyword_entry = keyword_entries[1]
textbook_keyword_entry = keyword_entries[2]

# 버튼 프레임
button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
button_frame.pack(pady=20)

process_button = ctk.CTkButton(
    button_frame, 
    text="🚀 처리 시작",
    command=process_excel,
    font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
    fg_color=COLORS["primary"],
    hover_color=COLORS["secondary"],
    height=45,
    width=150
)
process_button.pack(side="left", padx=(0, 10))

clear_button = ctk.CTkButton(
    button_frame, 
    text="🗑️ 초기화",
    command=clear_all,
    font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
    fg_color=COLORS["text_secondary"],
    hover_color=COLORS["error"],
    height=45,
    width=100
)
clear_button.pack(side="left")

# 결과 출력 카드
result_card = ctk.CTkFrame(main_container, fg_color=COLORS["surface"], corner_radius=12)
result_card.pack(fill="both", expand=True, pady=(0, 20), padx=10)

result_card_title = ctk.CTkLabel(
    result_card, 
    text="📋 처리 결과", 
    font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
    text_color=COLORS["text_primary"]
)
result_card_title.pack(pady=(15, 10))

# 결과 텍스트박스
report_textbox = ctk.CTkTextbox(
    result_card,
    font=ctk.CTkFont(family="Roboto", size=11),
    fg_color=COLORS["background"],
    text_color=COLORS["text_primary"],
    corner_radius=8
)
report_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 15))

# 상태바
status_frame = ctk.CTkFrame(main_container, fg_color="transparent")
status_frame.pack(fill="x", padx=10)

status_label = ctk.CTkLabel(
    status_frame, 
    text="✨ 준비 완료 - 파일을 선택하고 키워드를 입력한 후 처리 시작 버튼을 클릭하세요",
    font=ctk.CTkFont(family="Roboto", size=10),
    text_color=COLORS["text_secondary"]
)
status_label.pack(side="left")

# 창 크기 조절 시 위젯 자동 조정
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(0, weight=1)

main_container.grid_columnconfigure(0, weight=1)
main_container.grid_rowconfigure(0, weight=1)

app.mainloop()