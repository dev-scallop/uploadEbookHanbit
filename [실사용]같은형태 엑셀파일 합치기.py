import pandas as pd
import glob
import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io

# CustomTkinter 설정
ctk.set_appearance_mode("light")  # 라이트 모드
ctk.set_default_color_theme("blue")  # 블루 테마

class ModernExcelMerger:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("엑셀 파일 합치기")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # 색상 팔레트
        self.colors = {
            "primary": "#0064FF",
            "secondary": "#F8F9FA", 
            "success": "#00D4AA",
            "warning": "#FF6B6B",
            "text": "#191F28",
            "light_text": "#8B95A1",
            "white": "#FFFFFF",
            "border": "#E1E5E9"
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # 헤더 섹션
        self.create_header(main_container)
        
        # 폴더 선택 섹션
        self.create_folder_section(main_container)
        
        # 파일 정보 섹션
        self.create_file_info_section(main_container)
        
        # 진행 상황 섹션
        self.create_progress_section(main_container)
        
        # 액션 버튼 섹션
        self.create_action_section(main_container)
        
        # 결과 섹션
        self.create_result_section(main_container)
        
    def create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 30))
        
        # 아이콘과 제목
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack()
        
        # 아이콘 라벨 (이모지 사용)
        icon_label = ctk.CTkLabel(
            title_frame,
            text="📊",
            font=ctk.CTkFont(size=48),
            text_color=self.colors["primary"]
        )
        icon_label.pack()
        
        # 메인 제목
        title_label = ctk.CTkLabel(
            title_frame,
            text="엑셀 파일 합치기",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors["text"]
        )
        title_label.pack(pady=(10, 5))
        
        # 서브타이틀
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="같은 형태의 엑셀 파일들을 하나로 합쳐드립니다",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["light_text"]
        )
        subtitle_label.pack()
        
    def create_folder_section(self, parent):
        folder_frame = ctk.CTkFrame(parent, fg_color=self.colors["white"], corner_radius=12)
        folder_frame.pack(fill="x", pady=15)
        
        # 섹션 제목
        section_title = ctk.CTkLabel(
            folder_frame,
            text="📁 폴더 선택",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        )
        section_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # 설명 텍스트
        desc_label = ctk.CTkLabel(
            folder_frame,
            text="엑셀 파일이 있는 폴더를 선택해주세요",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["light_text"]
        )
        desc_label.pack(anchor="w", padx=20, pady=(0, 15))
        
        # 폴더 선택 버튼
        self.folder_button = ctk.CTkButton(
            folder_frame,
            text="폴더 선택하기",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["primary"],
            hover_color="#0052CC",
            corner_radius=8,
            height=45,
            command=self.select_folder
        )
        self.folder_button.pack(fill="x", padx=20, pady=(0, 15))
        
        # 선택된 폴더 표시
        self.folder_label = ctk.CTkLabel(
            folder_frame,
            text="폴더를 선택해주세요",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["light_text"]
        )
        self.folder_label.pack(anchor="w", padx=20, pady=(0, 20))
        
    def create_file_info_section(self, parent):
        self.info_frame = ctk.CTkFrame(parent, fg_color=self.colors["white"], corner_radius=12)
        self.info_frame.pack(fill="x", pady=15)
        
        # 섹션 제목
        info_title = ctk.CTkLabel(
            self.info_frame,
            text="📋 파일 정보",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        )
        info_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # 파일 정보 표시
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="폴더를 선택하면 파일 정보가 표시됩니다",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["light_text"]
        )
        self.info_label.pack(anchor="w", padx=20, pady=(0, 20))
        
    def create_progress_section(self, parent):
        self.progress_frame = ctk.CTkFrame(parent, fg_color=self.colors["white"], corner_radius=12)
        self.progress_frame.pack(fill="x", pady=15)
        
        # 섹션 제목
        progress_title = ctk.CTkLabel(
            self.progress_frame,
            text="⚡ 진행 상황",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        )
        progress_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # 진행률 표시
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="대기 중...",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["light_text"]
        )
        self.progress_label.pack(anchor="w", padx=20, pady=(0, 20))
        
    def create_action_section(self, parent):
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.pack(fill="x", pady=15)
        
        # 합치기 버튼
        self.merge_button = ctk.CTkButton(
            action_frame,
            text="🔗 파일 합치기",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["success"],
            hover_color="#00B894",
            corner_radius=10,
            height=55,
            command=self.merge_files,
            state="disabled"
        )
        self.merge_button.pack(fill="x")
        
    def create_result_section(self, parent):
        self.result_frame = ctk.CTkFrame(parent, fg_color=self.colors["white"], corner_radius=12)
        self.result_frame.pack(fill="x", pady=15)
        
        # 섹션 제목
        result_title = ctk.CTkLabel(
            self.result_frame,
            text="✅ 결과",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        )
        result_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # 결과 표시
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="처리 결과가 여기에 표시됩니다",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["light_text"]
        )
        self.result_label.pack(anchor="w", padx=20, pady=(0, 20))
        
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="엑셀 파일이 있는 폴더를 선택하세요")
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.configure(text=f"선택된 폴더: {folder_path}")
            
            # 엑셀 파일 확인
            file_paths = glob.glob(os.path.join(folder_path, "*.xlsx"))
            if file_paths:
                self.info_label.configure(
                    text=f"발견된 엑셀 파일: {len(file_paths)}개\n파일 목록:\n" + 
                         "\n".join([f"• {os.path.basename(f)}" for f in file_paths[:5]]) +
                         (f"\n... 및 {len(file_paths)-5}개 더" if len(file_paths) > 5 else "")
                )
                self.merge_button.configure(state="normal")
                self.progress_label.configure(text="✅ 파일을 찾았습니다. 합치기를 진행할 수 있습니다.")
            else:
                self.info_label.configure(text="선택한 폴더에 엑셀 파일이 없습니다.")
                self.merge_button.configure(state="disabled")
                self.progress_label.configure(text="⚠️ 엑셀 파일을 찾을 수 없습니다.")
        else:
            self.progress_label.configure(text="폴더 선택이 취소되었습니다.")
    
    def merge_files(self):
        if not hasattr(self, 'folder_path'):
            messagebox.showwarning("경고", "폴더를 먼저 선택해주세요.")
            return
        
        # UI 비활성화
        self.merge_button.configure(state="disabled", text="처리 중...")
        self.progress_label.configure(text="파일을 처리하고 있습니다...")
        
        # 별도 스레드에서 처리
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def process_files(self):
        try:
            file_paths = glob.glob(os.path.join(self.folder_path, "*.xlsx"))
            
            if not file_paths:
                self.root.after(0, lambda: messagebox.showwarning("경고", "선택한 폴더에 엑셀 파일이 없습니다."))
                return
            
            all_data_frames = []
            total_files = len(file_paths)
            
            for i, file in enumerate(file_paths):
                self.root.after(0, lambda f=file, idx=i+1, total=total_files: 
                    self.progress_label.configure(text=f"파일 처리 중... ({idx}/{total})"))
                
                xls = pd.ExcelFile(file)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    all_data_frames.append(df)
            
            merged_df = pd.concat(all_data_frames, ignore_index=True)
            output_path = os.path.join(self.folder_path, "merged_file.xlsx")
            merged_df.to_excel(output_path, index=False)
            
            self.root.after(0, lambda: self.show_success(output_path, len(all_data_frames)))
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def show_success(self, output_path, total_sheets):
        self.progress_label.configure(text="✅ 처리 완료!")
        self.result_label.configure(
            text=f"총 {total_sheets}개 시트가 성공적으로 병합되었습니다.\n저장 위치: {output_path}",
            text_color=self.colors["success"]
        )
        self.merge_button.configure(state="normal", text="🔗 파일 합치기")
        
        messagebox.showinfo("완료", f"모든 파일의 모든 시트가 성공적으로 병합되었습니다.\n저장 위치: {output_path}")
    
    def show_error(self, error_message):
        self.progress_label.configure(text="❌ 오류 발생")
        self.result_label.configure(
            text=f"오류: {error_message}",
            text_color=self.colors["warning"]
        )
        self.merge_button.configure(state="normal", text="🔗 파일 합치기")
        
        messagebox.showerror("오류", f"파일 처리 중 오류가 발생했습니다:\n{error_message}")
    
    def run(self):
        # 창을 화면 중앙에 배치
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = ModernExcelMerger()
    app.run()