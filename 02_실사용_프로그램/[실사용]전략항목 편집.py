import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

class ExcelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("엑셀 관리 프로그램")
        self.root.geometry("800x600")
        
        self.df = None
        self.file_path = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # 파일 선택 프레임
        file_frame = ttk.Frame(self.root)
        file_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Button(file_frame, text="엑셀 파일 선택", command=self.load_file).pack(side='left')
        self.file_label = ttk.Label(file_frame, text="파일이 선택되지 않았습니다.")
        self.file_label.pack(side='left', padx=(10, 0))
        
        # 검색 조건 프레임
        search_frame = ttk.LabelFrame(self.root, text="검색 조건")
        search_frame.pack(pady=10, padx=10, fill='x')
        
        # 필터링 모드
        mode_frame = ttk.Frame(search_frame)
        mode_frame.pack(pady=5, fill='x')
        
        self.filter_mode = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="단독 필터링", variable=self.filter_mode, 
                       value="single").pack(side='left')
        ttk.Radiobutton(mode_frame, text="중복 필터링", variable=self.filter_mode, 
                       value="multiple").pack(side='left', padx=(20, 0))
        
        # 검색 입력 필드
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(pady=5, fill='x')
        
        ttk.Label(input_frame, text="학교:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.school_entry = ttk.Entry(input_frame, width=20)
        self.school_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(input_frame, text="이름:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.name_entry = ttk.Entry(input_frame, width=20)
        self.name_entry.grid(row=0, column=3)
        
        # 검색 버튼
        ttk.Button(search_frame, text="검색", command=self.search_data).pack(pady=10)
        
        # 결과 표시 프레임
        result_frame = ttk.LabelFrame(self.root, text="검색 결과")
        result_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # 트리뷰로 결과 표시
        columns = ("학교", "강좌수", "이름", "과목", "타겟강좌수", "목표매출액", "실행관리")
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=8, selectmode='extended')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 실행관리 추가 프레임
        manage_frame = ttk.LabelFrame(self.root, text="실행관리 추가")
        manage_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(manage_frame, text="실행관리 내용:").pack(anchor='w')
        self.manage_text = tk.Text(manage_frame, height=3, width=50)
        self.manage_text.pack(pady=5, fill='x')
        
        ttk.Button(manage_frame, text="선택된 행에 실행관리 추가", 
                  command=self.add_management).pack(pady=5)
        
        # 엑셀 표 붙여넣기 실행관리 일괄 추가 프레임 (하단)
        bulk_frame = ttk.LabelFrame(self.root, text="엑셀 표 붙여넣기 실행관리 일괄 추가")
        bulk_frame.pack(pady=10, padx=10, fill='x')
        ttk.Label(bulk_frame, text="학교\t이름\t실행관리 (탭으로 구분된 표를 붙여넣으세요)").pack(anchor='w')
        self.bulk_text = tk.Text(bulk_frame, height=6, width=80)
        self.bulk_text.pack(pady=5, fill='x')
        ttk.Button(bulk_frame, text="엑셀 표 실행관리 일괄 추가", command=self.bulk_add_management).pack(pady=5)
        
    def bulk_add_management(self):
        raw = self.bulk_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("경고", "붙여넣기 데이터를 입력해주세요.")
            return
        # 표 데이터 파싱 (탭 구분)
        for line in raw.splitlines():
            parts = [p.strip() for p in line.split('\t')]
            if len(parts) < 3:
                continue
            school, name, content = parts[0], parts[1], parts[2]
            mask = (self.df['학교'] == school) & (self.df['이름'] == name)
            idxs = self.df[mask].index
            for idx in idxs:
                current_content = str(self.df.loc[idx, '실행관리'])
                if current_content == 'nan' or pd.isna(current_content):
                    current_content = ""
                if current_content:
                    updated_content = current_content + "\n" + content
                else:
                    updated_content = content
                self.df.loc[idx, '실행관리'] = updated_content
        try:
            self.df.to_excel(self.file_path, index=False)
            messagebox.showinfo("성공", "일괄 실행관리가 추가되고 파일이 저장되었습니다.")
            self.bulk_text.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 실패: {str(e)}")
    
    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                self.file_path = file_path
                self.file_label.config(text=f"파일: {file_path.split('/')[-1]}")
                messagebox.showinfo("성공", "파일이 성공적으로 로드되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"파일 로드 실패: {str(e)}")
    
    def search_data(self):
        if self.df is None:
            messagebox.showwarning("경고", "먼저 엑셀 파일을 선택해주세요.")
            return
        
        # 기존 결과 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        school = self.school_entry.get().strip()
        name = self.name_entry.get().strip()
        
        if not school and not name:
            messagebox.showwarning("경고", "학교 또는 이름 중 하나는 입력해주세요.")
            return
        
        # 필터링 수행
        filtered_df = self.df.copy()
        
        if self.filter_mode.get() == "single":
            # 단독 필터링
            if school and name:
                filtered_df = filtered_df[(filtered_df['학교'] == school) | 
                                        (filtered_df['이름'] == name)]
            elif school:
                filtered_df = filtered_df[filtered_df['학교'] == school]
            elif name:
                filtered_df = filtered_df[filtered_df['이름'] == name]
        else:
            # 중복 필터링
            if school:
                filtered_df = filtered_df[filtered_df['학교'] == school]
            if name:
                filtered_df = filtered_df[filtered_df['이름'] == name]
        
        # 결과 표시
        for idx, row in filtered_df.iterrows():
            self.tree.insert('', 'end', values=tuple(row), tags=(idx,))
        
        if len(filtered_df) == 0:
            messagebox.showinfo("결과", "검색 결과가 없습니다.")
    
    def add_management(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "실행관리를 추가할 행을 선택해주세요.")
            return
        new_content = self.manage_text.get("1.0", tk.END).strip()
        if not new_content:
            messagebox.showwarning("경고", "실행관리 내용을 입력해주세요.")
            return
        for item in selected_items:
            row_idx = self.tree.item(item)['tags'][0]
            current_content = str(self.df.loc[row_idx, '실행관리'])
            if current_content == 'nan' or pd.isna(current_content):
                current_content = ""
            if current_content:
                updated_content = current_content + "\n" + new_content
            else:
                updated_content = new_content
            self.df.loc[row_idx, '실행관리'] = updated_content
            updated_values = list(self.df.loc[row_idx])
            self.tree.item(item, values=updated_values)
        try:
            self.df.to_excel(self.file_path, index=False)
            messagebox.showinfo("성공", "선택된 모든 행에 실행관리가 추가되고 파일이 저장되었습니다.")
            self.manage_text.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 실패: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelGUI(root)
    root.mainloop()