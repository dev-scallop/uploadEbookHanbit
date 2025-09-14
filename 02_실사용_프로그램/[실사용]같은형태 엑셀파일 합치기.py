import pandas as pd
import glob
import os
import threading
import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox

# CustomTkinter 설정
ctk.set_appearance_mode("light")  # 라이트 모드
ctk.set_default_color_theme("blue")  # 블루 테마

# 상수 정의
SUPPORTED_EXTENSIONS = ['*.xlsx', '*.xls']
MAX_FILES_PREVIEW = 5
DEFAULT_OUTPUT_NAME = "merged_file.xlsx"

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModernExcelMerger:
    """
    모던한 엑셀 파일 합치기 GUI 애플리케이션
    
    Features:
    - CustomTkinter를 사용한 모던 UI
    - .xlsx, .xls 파일 지원
    - 다중 시트 처리
    - 진행률 표시 및 취소 기능
    - 오류 처리 및 로깅
    - 메모리 효율적인 처리
    """
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("엑셀 파일 합치기")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.colors = self.get_colors()
        
        # 클래스 속성 초기화
        self.folder_path = None
        self.is_processing = False
        self.cancel_processing = False
        
        self.setup_ui()

    def get_colors(self):
        return {
            "primary": "#0064FF",
            "secondary": "#F8F9FA",
            "success": "#00D4AA",
            "warning": "#FF6B6B",
            "text": "#191F28",
            "light_text": "#8B95A1",
            "white": "#FFFFFF",
            "border": "#E1E5E9"
        }
        
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
        
        # 버튼 컨테이너
        button_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_container.pack(fill="x")
        
        # 합치기 버튼
        self.merge_button = ctk.CTkButton(
            button_container,
            text="🔗 파일 합치기",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["success"],
            hover_color="#00B894",
            corner_radius=10,
            height=55,
            command=self.merge_files,
            state="disabled"
        )
        self.merge_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # 취소 버튼
        self.cancel_button = ctk.CTkButton(
            button_container,
            text="❌ 취소",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["warning"],
            hover_color="#FF5252",
            corner_radius=10,
            height=55,
            width=100,
            command=self.cancel_processing_func,
            state="disabled"
        )
        self.cancel_button.pack(side="right")
    
    def cancel_processing_func(self):
        """처리 취소 함수"""
        if self.is_processing:
            self.cancel_processing = True
            self.cancel_button.configure(state="disabled")
            self.progress_label.configure(text="취소 중...")
        
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
        
    def get_excel_files(self, folder_path):
        """폴더에서 엑셀 파일 목록을 가져옵니다."""
        file_paths = []
        for extension in SUPPORTED_EXTENSIONS:
            file_paths.extend(glob.glob(os.path.join(folder_path, extension)))
        return file_paths
    
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="엑셀 파일이 있는 폴더를 선택하세요")
        if not folder_path:
            self.progress_label.configure(text="폴더 선택이 취소되었습니다.")
            return
            
        self.folder_path = folder_path
        self.folder_label.configure(text=f"선택된 폴더: {folder_path}")
        
        file_paths = self.get_excel_files(folder_path)
        
        if file_paths:
            file_preview = "\n".join([f"• {os.path.basename(f)}" for f in file_paths[:MAX_FILES_PREVIEW]])
            more_files = f"\n... 및 {len(file_paths)-MAX_FILES_PREVIEW}개 더" if len(file_paths) > MAX_FILES_PREVIEW else ""
            self.info_label.configure(
                text=f"발견된 엑셀 파일: {len(file_paths)}개\n파일 목록:\n{file_preview}{more_files}"
            )
            self.merge_button.configure(state="normal")
            self.progress_label.configure(text="✅ 파일을 찾았습니다. 합치기를 진행할 수 있습니다.")
        else:
            self.info_label.configure(text="선택한 폴더에 엑셀 파일이 없습니다.")
            self.merge_button.configure(state="disabled")
            self.progress_label.configure(text="⚠️ 엑셀 파일을 찾을 수 없습니다.")
    
    def merge_files(self):
        if not self.folder_path:
            messagebox.showwarning("경고", "폴더를 먼저 선택해주세요.")
            return
        
        if self.is_processing:
            messagebox.showinfo("알림", "이미 처리 중입니다.")
            return
        
        # UI 비활성화/활성화
        self.is_processing = True
        self.cancel_processing = False
        self.merge_button.configure(state="disabled", text="처리 중...")
        self.cancel_button.configure(state="normal")
        self.progress_label.configure(text="파일을 처리하고 있습니다...")
        
        # 별도 스레드에서 처리
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def read_excel_file(self, file_path):
        """엑셀 파일을 읽어서 데이터프레임 리스트를 반환합니다."""
        try:
            data_frames = []
            xls = pd.ExcelFile(file_path)
            
            for sheet_name in xls.sheet_names:
                if self.cancel_processing:
                    return []
                    
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if not df.empty:
                    # 파일명과 시트명 정보 추가 (선택사항)
                    df['_source_file'] = os.path.basename(file_path)
                    df['_source_sheet'] = sheet_name
                    data_frames.append(df)
                    
            return data_frames
            
        except Exception as e:
            logging.error(f"파일 읽기 오류 - {file_path}: {str(e)}")
            raise Exception(f"{os.path.basename(file_path)} 파일을 읽을 수 없습니다: {str(e)}")
    
    def process_files(self):
        try:
            file_paths = self.get_excel_files(self.folder_path)
            
            if not file_paths:
                self.root.after(0, lambda: self.show_error("선택한 폴더에 엑셀 파일이 없습니다."))
                return
            
            all_data_frames = []
            total_files = len(file_paths)
            
            for i, file in enumerate(file_paths):
                if self.cancel_processing:
                    self.root.after(0, lambda: self.show_error("사용자가 처리를 취소했습니다."))
                    return
                    
                self.root.after(0, lambda idx=i+1, total=total_files, filename=os.path.basename(file):
                    self.progress_label.configure(text=f"파일 처리 중... ({idx}/{total}) - {filename}"))
                
                try:
                    file_dataframes = self.read_excel_file(file)
                    all_data_frames.extend(file_dataframes)
                    
                except Exception as fe:
                    logging.error(f"파일 처리 오류 - {file}: {str(fe)}")
                    self.root.after(0, lambda f=file, msg=str(fe):
                        self.progress_label.configure(text=f"⚠️ {os.path.basename(f)} 처리 오류: {msg}"))
                    continue  # 다른 파일 계속 처리
            
            if not all_data_frames:
                self.root.after(0, lambda: self.show_error("병합할 데이터가 없습니다."))
                return
            
            # 메모리 효율적인 병합
            self.root.after(0, lambda: self.progress_label.configure(text="데이터를 병합하고 있습니다..."))
            
            # 소스 컬럼 제거 (필요시)
            for df in all_data_frames:
                if '_source_file' in df.columns:
                    df.drop(['_source_file', '_source_sheet'], axis=1, inplace=True)
            
            merged_df = pd.concat(all_data_frames, ignore_index=True)
            
            # 파일 저장
            output_path = os.path.join(self.folder_path, DEFAULT_OUTPUT_NAME)
            self.root.after(0, lambda: self.progress_label.configure(text="파일을 저장하고 있습니다..."))
            
            merged_df.to_excel(output_path, index=False)
            
            self.root.after(0, lambda: self.show_success(output_path, len(all_data_frames)))
            
        except Exception as e:
            logging.error(f"전체 처리 오류: {str(e)}")
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            self.is_processing = False
    
    def show_success(self, output_path, total_sheets):
        self.progress_label.configure(text="✅ 처리 완료!")
        self.result_label.configure(
            text=f"총 {total_sheets}개 시트가 성공적으로 병합되었습니다.\n저장 위치: {output_path}",
            text_color=self.colors["success"]
        )
        self.merge_button.configure(state="normal", text="🔗 파일 합치기")
        self.cancel_button.configure(state="disabled")
        
        logging.info(f"파일 병합 완료: {output_path}, 총 {total_sheets}개 시트")
        messagebox.showinfo("완료", f"모든 파일의 모든 시트가 성공적으로 병합되었습니다.\n저장 위치: {output_path}")
    
    def show_error(self, error_message):
        self.progress_label.configure(text="❌ 오류 발생")
        self.result_label.configure(
            text=f"오류: {error_message}",
            text_color=self.colors["warning"]
        )
        self.merge_button.configure(state="normal", text="🔗 파일 합치기")
        self.cancel_button.configure(state="disabled")
        
        logging.error(f"처리 오류: {error_message}")
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