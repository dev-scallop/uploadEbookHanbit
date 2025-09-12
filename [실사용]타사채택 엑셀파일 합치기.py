import pandas as pd
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime

# CustomTkinter 테마 설정 (애플 + 토스뱅크 스타일)
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ModernExcelProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel 데이터 통합 프로세서")
        self.root.geometry("1000x800")  # 창 크기를 더 크게 설정
        self.root.minsize(900, 700)     # 최소 크기도 조정
        
        # 창을 화면 중앙에 배치
        self.center_window()
        
        # 색상 팔레트 (애플 + 토스뱅크 스타일)
        self.colors = {
            'primary': '#007AFF',      # 애플 블루
            'secondary': '#34C759',    # 애플 그린
            'accent': '#00C7BE',       # 토스 민트
            'warning': '#FF9500',      # 애플 오렌지
            'error': '#FF3B30',        # 애플 레드
            'background': '#F2F2F7',   # 애플 라이트 그레이
            'surface': '#FFFFFF',      # 순백
            'text_primary': '#1C1C1E', # 다크 그레이
            'text_secondary': '#8E8E93', # 라이트 그레이
            'border': '#E5E5EA'        # 보더 그레이
        }
        
        self.setup_ui()
        self.folder_path = None
        self.is_processing = False

    def center_window(self):
        """창을 화면 중앙에 배치"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        # 메인 컨테이너
        self.main_container = ctk.CTkFrame(
            self.root, 
            fg_color="transparent",
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)  # 패딩을 20에서 15로 줄임

        # 헤더 섹션
        self.create_header_section()
        
        # 메인 컨텐츠 섹션
        self.create_main_content()
        
        # 로그 섹션
        self.create_log_section()

    def create_header_section(self):
        # 헤더 프레임
        header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['surface'],
            corner_radius=16,
            height=100  # 높이를 120에서 100으로 줄임
        )
        header_frame.pack(fill="x", pady=(0, 15))  # pady를 20에서 15로 줄임
        header_frame.pack_propagate(False)

        # 제목과 설명
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=25, pady=20)  # pady를 25에서 20으로 줄임

        title_label = ctk.CTkLabel(
            title_frame,
            text="Excel 데이터 통합 프로세서",
            font=ctk.CTkFont(family="Roboto", size=26, weight="bold"),  # 폰트 크기를 28에서 26으로 줄임
            text_color=self.colors['text_primary']
        )
        title_label.pack(anchor="w", pady=(0, 6))  # pady를 8에서 6으로 줄임

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="여러 Excel 파일의 데이터를 통합하고 정리합니다",
            font=ctk.CTkFont(family="Roboto", size=13),  # 폰트 크기를 14에서 13으로 줄임
            text_color=self.colors['text_secondary']
        )
        subtitle_label.pack(anchor="w")

        # 상태 표시기
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="● 준비",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),  # 폰트 크기를 14에서 13으로 줄임
            text_color=self.colors['secondary']
        )
        self.status_indicator.pack(side="right", padx=25, pady=20)  # pady를 25에서 20으로 줄임

    def create_main_content(self):
        # 메인 컨텐츠 프레임
        content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['surface'],
            corner_radius=16
        )
        content_frame.pack(fill="both", expand=True, pady=(0, 20))  # pady를 25에서 20으로 줄임

        # 입력 섹션
        self.create_input_section(content_frame)
        
        # 설정 섹션
        self.create_settings_section(content_frame)
        
        # 액션 섹션
        self.create_action_section(content_frame)

    def create_input_section(self, parent):
        # 입력 섹션 프레임
        input_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            corner_radius=12
        )
        input_frame.pack(fill="x", padx=25, pady=(25, 20))  # pady를 (35, 25)에서 (25, 20)으로 줄임

        # 섹션 제목
        section_title = ctk.CTkLabel(
            input_frame,
            text="📁 폴더 선택",
            font=ctk.CTkFont(family="Roboto", size=17, weight="bold"),  # 폰트 크기를 18에서 17으로 줄임
            text_color=self.colors['text_primary']
        )
        section_title.pack(anchor="w", pady=(0, 15))  # pady를 18에서 15로 줄임

        # 폴더 선택 영역
        folder_selection_frame = ctk.CTkFrame(
            input_frame,
            fg_color=self.colors['background'],
            corner_radius=12
        )
        folder_selection_frame.pack(fill="x", pady=(0, 15))  # pady를 18에서 15로 줄임

        # 폴더 경로 표시
        self.folder_path_var = ctk.StringVar(value="폴더를 선택해주세요")
        self.folder_label = ctk.CTkEntry(
            folder_selection_frame,
            textvariable=self.folder_path_var,
            font=ctk.CTkFont(family="Roboto", size=14),
            fg_color="transparent",
            border_color=self.colors['border'],
            border_width=1,
            corner_radius=8,
            height=45,
            state="readonly"
        )
        self.folder_label.pack(side="left", fill="x", expand=True, padx=20, pady=20)

        # 폴더 선택 버튼
        self.folder_button = ctk.CTkButton(
            folder_selection_frame,
            text="폴더 선택",
            command=self.select_folder,
            fg_color=self.colors['primary'],
            hover_color=self.colors['accent'],
            corner_radius=8,
            height=45,
            width=120,
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold")
        )
        self.folder_button.pack(side="right", padx=20, pady=20)

    def create_settings_section(self, parent):
        # 설정 섹션 프레임
        settings_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            corner_radius=12
        )
        settings_frame.pack(fill="x", padx=25, pady=(0, 20))  # pady를 25에서 20으로 줄임

        # 섹션 제목
        section_title = ctk.CTkLabel(
            settings_frame,
            text="⚙️ 처리 설정",
            font=ctk.CTkFont(family="Roboto", size=17, weight="bold"),  # 폰트 크기를 18에서 17으로 줄임
            text_color=self.colors['text_primary']
        )
        section_title.pack(anchor="w", pady=(0, 15))  # pady를 18에서 15로 줄임

        # 설정 옵션들
        options_frame = ctk.CTkFrame(
            settings_frame,
            fg_color=self.colors['background'],
            corner_radius=12
        )
        options_frame.pack(fill="x", pady=(0, 15))  # pady를 18에서 15로 줄임

        # 체크박스들
        checkbox_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", padx=20, pady=20)  # pady를 25에서 20으로 줄임

        self.auto_backup_var = ctk.BooleanVar(value=True)
        self.auto_backup_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="자동 백업 생성",
            variable=self.auto_backup_var,
            font=ctk.CTkFont(family="Roboto", size=13),  # 폰트 크기를 14에서 13으로 줄임
            fg_color=self.colors['primary'],
            hover_color=self.colors['accent'],
            corner_radius=6
        )
        self.auto_backup_checkbox.pack(side="left", padx=(0, 30))  # padx를 35에서 30으로 줄임

        self.remove_duplicates_var = ctk.BooleanVar(value=True)
        self.remove_duplicates_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="중복 데이터 제거",
            variable=self.remove_duplicates_var,
            font=ctk.CTkFont(family="Roboto", size=13),  # 폰트 크기를 14에서 13으로 줄임
            fg_color=self.colors['primary'],
            hover_color=self.colors['accent'],
            corner_radius=6
        )
        self.remove_duplicates_checkbox.pack(side="left", padx=(0, 30))  # padx를 35에서 30으로 줄임

        self.clean_data_var = ctk.BooleanVar(value=True)
        self.clean_data_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="데이터 정리 (공백 제거)",
            variable=self.clean_data_var,
            font=ctk.CTkFont(family="Roboto", size=13),  # 폰트 크기를 14에서 13으로 줄임
            fg_color=self.colors['primary'],
            hover_color=self.colors['accent'],
            corner_radius=6
        )
        self.clean_data_checkbox.pack(side="left")

    def create_action_section(self, parent):
        # 액션 섹션 프레임
        action_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            corner_radius=12
        )
        action_frame.pack(fill="x", padx=25, pady=(0, 25))  # pady를 35에서 25로 줄임

        # 섹션 제목
        section_title = ctk.CTkLabel(
            action_frame,
            text="🚀 실행",
            font=ctk.CTkFont(family="Roboto", size=17, weight="bold"),  # 폰트 크기를 18에서 17으로 줄임
            text_color=self.colors['text_primary']
        )
        section_title.pack(anchor="w", pady=(0, 15))  # pady를 18에서 15로 줄임

        # 버튼들
        button_frame = ctk.CTkFrame(
            action_frame,
            fg_color=self.colors['background'],
            corner_radius=12
        )
        button_frame.pack(fill="x", pady=(0, 15))  # pady를 18에서 15로 줄임

        # 실행 버튼
        self.run_button = ctk.CTkButton(
            button_frame,
            text="데이터 통합 실행",
            command=self.run_extraction,
            fg_color=self.colors['secondary'],
            hover_color=self.colors['accent'],
            corner_radius=12,
            height=50,
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            state="disabled"
        )
        self.run_button.pack(side="left", padx=20, pady=20)

        # 진행률 표시
        self.progress_bar = ctk.CTkProgressBar(
            button_frame,
            fg_color=self.colors['border'],
            progress_color=self.colors['primary'],
            corner_radius=6,
            height=8
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(20, 20), pady=20)
        self.progress_bar.set(0)

        # 진행률 텍스트
        self.progress_text = ctk.CTkLabel(
            button_frame,
            text="0%",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        self.progress_text.pack(side="right", padx=20, pady=20)

    def create_log_section(self):
        # 로그 섹션 프레임
        log_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['surface'],
            corner_radius=16
        )
        log_frame.pack(fill="both", expand=True)

        # 로그 헤더
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=25, pady=(20, 10))  # pady를 (25, 15)에서 (20, 10)으로 줄임

        log_title = ctk.CTkLabel(
            log_header,
            text="📊 처리 로그",
            font=ctk.CTkFont(family="Roboto", size=17, weight="bold"),  # 폰트 크기를 18에서 17으로 줄임
            text_color=self.colors['text_primary']
        )
        log_title.pack(side="left")

        # 로그 클리어 버튼
        clear_log_button = ctk.CTkButton(
            log_header,
            text="로그 지우기",
            command=self.clear_log,
            fg_color="transparent",
            text_color=self.colors['text_secondary'],
            hover_color=self.colors['background'],
            corner_radius=8,
            height=30,  # 높이를 32에서 30으로 줄임
            font=ctk.CTkFont(family="Roboto", size=11)  # 폰트 크기를 12에서 11로 줄임
        )
        clear_log_button.pack(side="right")

        # 로그 텍스트 영역
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Roboto", size=11),  # 폰트 크기를 12에서 11로 줄임
            fg_color=self.colors['background'],
            text_color=self.colors['text_primary'],
            corner_radius=12,
            border_color=self.colors['border'],
            border_width=1,
            wrap="word",  # 단어 단위로 줄바꿈
            state="normal"  # 읽기/쓰기 가능 상태로 설정
        )
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))  # pady를 25에서 20으로 줄임
        
        # 초기 로그 메시지 추가
        self.log_text.insert("end", "[시스템] Excel 데이터 통합 프로세서가 시작되었습니다.\n")
        self.log_text.insert("end", "[시스템] 폴더를 선택하고 데이터 통합을 시작하세요.\n")
        self.log_text.see("end")

    def select_folder(self):
        self.folder_path = filedialog.askdirectory(title="Excel 파일이 있는 폴더를 선택하세요")
        if self.folder_path:
            self.folder_path_var.set(self.folder_path)
            self.run_button.configure(state="normal")
            self.update_status("폴더 선택됨", self.colors['secondary'])
            self.log_message(f"폴더 선택됨: {self.folder_path}")
        else:
            self.folder_path_var.set("폴더를 선택해주세요")
            self.run_button.configure(state="disabled")
            self.update_status("준비", self.colors['text_secondary'])

    def run_extraction(self):
        if not self.folder_path or self.is_processing:
            return

        self.is_processing = True
        self.run_button.configure(state="disabled", text="처리 중...")
        self.update_status("처리 중", self.colors['warning'])
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self._process_extraction)
        thread.daemon = True
        thread.start()

    def _process_extraction(self):
        try:
            self.log_message("🚀 데이터 통합 프로세스를 시작합니다...")
            
            # 열 이름들
            columns_to_extract = ['h_departments', 'h_grade', 'h_subject', 'h_number', 
                                'h_professor', 'h_title', 'h_writer', 'h_publisher']

            # 새로운 데이터프레임 생성
            output_df = pd.DataFrame(columns=columns_to_extract + ['Filename'])

            # 폴더 내의 모든 엑셀 파일 탐색
            excel_files = [f for f in os.listdir(self.folder_path) if f.endswith('.xlsx')]
            total_files = len(excel_files)
            
            if total_files == 0:
                self.log_message("❌ Excel 파일을 찾을 수 없습니다.")
                return

            self.log_message(f"📁 총 {total_files}개의 Excel 파일을 발견했습니다.")
            self.log_message("=" * 60)

            # 처리 결과 통계
            processing_stats = {
                'total_files': total_files,
                'successful_files': 0,
                'failed_files': 0,
                'total_rows': 0,
                'extracted_columns': set(),
                'error_details': [],
                'file_details': []
            }

            for i, filename in enumerate(excel_files):
                try:
                    file_path = os.path.join(self.folder_path, filename)
                    self.log_message(f"📄 [{i+1}/{total_files}] 처리 중: {filename}")
                    
                    # 엑셀 파일 읽기
                    df = pd.read_excel(file_path, sheet_name='h_data')
                    
                    # 파일 기본 정보 로깅
                    file_info = {
                        'filename': filename,
                        'total_rows': len(df),
                        'total_columns': len(df.columns),
                        'available_columns': list(df.columns),
                        'extracted_columns': [],
                        'extracted_rows': 0,
                        'status': 'success'
                    }
                    
                    # 해당 열 이름이 데이터프레임에 존재하는지 확인
                    existing_columns = [col.strip() for col in df.columns if col.strip() in columns_to_extract]
                    
                    if not existing_columns:
                        error_msg = f"⚠️ {filename}: 추출할 열을 찾을 수 없습니다."
                        self.log_message(error_msg)
                        self.log_message(f"   📋 사용 가능한 열: {', '.join(df.columns)}")
                        self.log_message(f"   🎯 찾는 열: {', '.join(columns_to_extract)}")
                        
                        file_info['status'] = 'no_matching_columns'
                        file_info['error'] = '추출할 열을 찾을 수 없음'
                        processing_stats['failed_files'] += 1
                        processing_stats['error_details'].append(file_info)
                        continue

                    # 파일명 열 추가
                    df['Filename'] = filename

                    # 빈 값이나 모든 NA 값을 제외하고 열들을 필터링
                    df_filtered = df[existing_columns + ['Filename']].dropna(axis=1, how='all')
                    
                    # 실제 추출된 행 수 계산 (모든 열이 NA인 행 제외)
                    df_filtered = df_filtered.dropna(how='all')
                    
                    # 공백 문자열을 빈 값으로 변환 (NaN 대신 빈 문자열 사용)
                    for col in existing_columns:
                        if col in df_filtered.columns:
                            # 공백 문자열과 NaN을 빈 문자열로 변환
                            df_filtered[col] = df_filtered[col].fillna('')
                            df_filtered[col] = df_filtered[col].astype(str).replace('^\\s*$', '', regex=True)
                            # 빈 문자열을 다시 빈 값으로 변환
                            df_filtered[col] = df_filtered[col].replace('', None)
                    
                    # 파일 정보 업데이트
                    file_info['extracted_columns'] = existing_columns
                    file_info['extracted_rows'] = len(df_filtered)
                    processing_stats['extracted_columns'].update(existing_columns)
                    
                    # 추출된 열들을 새로운 데이터프레임에 추가
                    output_df = pd.concat([output_df, df_filtered], ignore_index=True)
                    
                    # 성공 로그
                    self.log_message(f"   ✅ 성공: {len(df_filtered)}행 추출")
                    self.log_message(f"   📊 추출된 열: {', '.join(existing_columns)}")
                    
                    processing_stats['successful_files'] += 1
                    processing_stats['total_rows'] += len(df_filtered)
                    processing_stats['file_details'].append(file_info)
                    
                    # 진행률 업데이트
                    progress = (i + 1) / total_files
                    self.root.after(0, lambda p=progress: self.update_progress(p))
                    
                except Exception as e:
                    error_msg = f"❌ {filename} 처리 중 오류 발생"
                    self.log_message(error_msg)
                    self.log_message(f"   🔍 오류 유형: {type(e).__name__}")
                    self.log_message(f"   📝 오류 내용: {str(e)}")
                    
                    # 오류 상세 정보 저장
                    file_info = {
                        'filename': filename,
                        'status': 'error',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                    
                    processing_stats['failed_files'] += 1
                    processing_stats['error_details'].append(file_info)
                    
                    # 일반적인 오류 원인 분석
                    if "No sheet named" in str(e):
                        self.log_message(f"   💡 원인: 'h_data' 시트가 존재하지 않습니다.")
                        self.log_message(f"   💡 해결방법: 시트 이름을 확인하거나 'h_data'로 변경하세요.")
                    elif "No module named" in str(e):
                        self.log_message(f"   💡 원인: 필요한 라이브러리가 설치되지 않았습니다.")
                        self.log_message(f"   💡 해결방법: 'pip install openpyxl' 명령을 실행하세요.")
                    elif "Permission denied" in str(e):
                        self.log_message(f"   💡 원인: 파일에 대한 접근 권한이 없습니다.")
                        self.log_message(f"   💡 해결방법: 파일을 닫고 다시 시도하세요.")
                    elif "File is not a zip file" in str(e):
                        self.log_message(f"   💡 원인: 파일이 손상되었거나 Excel 파일이 아닙니다.")
                        self.log_message(f"   💡 해결방법: 파일을 다시 다운로드하거나 다른 Excel 파일을 사용하세요.")

            self.log_message("=" * 60)
            self.log_message("🧹 데이터 후처리 작업을 시작합니다...")

            # 데이터 정리 옵션 적용
            if self.clean_data_var.get():
                self.log_message("🧹 데이터 정리 중...")
                initial_rows = len(output_df)
                for col in output_df.columns:
                    if col != 'Filename' and output_df[col].dtype == 'object':
                        # 공백 제거 및 빈 값 처리
                        output_df[col] = output_df[col].fillna('')
                        output_df[col] = output_df[col].astype(str).str.strip()
                        # 빈 문자열을 None으로 변환 (Excel에서 빈 셀로 표시)
                        output_df[col] = output_df[col].replace('', None)
                self.log_message(f"   ✅ 공백 제거 완료: {initial_rows}행 → {len(output_df)}행")

            if self.remove_duplicates_var.get():
                self.log_message("🔄 중복 데이터 제거 중...")
                initial_count = len(output_df)
                output_df = output_df.drop_duplicates()
                removed_count = initial_count - len(output_df)
                self.log_message(f"   ✅ 중복 제거 완료: {removed_count}개 행 제거됨")

            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f'통합된_데이터_{timestamp}.xlsx'
            output_file = os.path.join(self.folder_path, output_filename)
            
            # NaN 값을 빈 셀로 저장
            output_df.to_excel(output_file, index=False, na_rep='')
            
            # 최종 결과 보고서 생성
            self.generate_final_report(processing_stats, output_df, output_filename)
            
            # 백업 생성
            if self.auto_backup_var.get():
                backup_file = os.path.join(self.folder_path, f'백업_{output_filename}')
                output_df.to_excel(backup_file, index=False, na_rep='')
                self.log_message(f"💾 백업 파일이 생성되었습니다: {backup_file}")

            self.root.after(0, lambda: self.update_status("완료", self.colors['secondary']))
            self.root.after(0, lambda: messagebox.showinfo("성공", f"데이터 통합이 완료되었습니다!\n결과 파일: {output_filename}"))

        except Exception as e:
            error_msg = f"❌ 데이터 통합 중 치명적 오류가 발생했습니다: {str(e)}"
            self.log_message(error_msg)
            self.log_message(f"   🔍 오류 유형: {type(e).__name__}")
            self.log_message(f"   📝 오류 내용: {str(e)}")
            self.root.after(0, lambda: self.update_status("오류", self.colors['error']))
            self.root.after(0, lambda: messagebox.showerror("오류", error_msg))
        
        finally:
            self.root.after(0, self._reset_ui)

    def generate_final_report(self, stats, output_df, output_filename):
        """최종 결과 보고서 생성 및 로그에 출력"""
        self.log_message("=" * 60)
        self.log_message("📊 📋 최종 결과 보고서")
        self.log_message("=" * 60)
        
        # 전체 통계
        self.log_message(f"📁 전체 파일 수: {stats['total_files']}개")
        self.log_message(f"✅ 성공 처리: {stats['successful_files']}개")
        self.log_message(f"❌ 실패 처리: {stats['failed_files']}개")
        self.log_message(f"📊 총 추출된 행 수: {stats['total_rows']:,}행")
        self.log_message(f"📋 최종 결과 행 수: {len(output_df):,}행")
        
        # 추출된 열 정보
        self.log_message(f"🔍 추출된 열: {', '.join(sorted(stats['extracted_columns']))}")
        
        # 성공한 파일들의 상세 정보
        if stats['file_details']:
            self.log_message("\n📄 성공 처리된 파일 상세:")
            for file_info in stats['file_details']:
                self.log_message(f"   📁 {file_info['filename']}")
                self.log_message(f"      📊 전체 행: {file_info['total_rows']:,}행")
                self.log_message(f"      ✅ 추출 행: {file_info['extracted_rows']:,}행")
                self.log_message(f"      🔍 추출 열: {', '.join(file_info['extracted_columns'])}")
        
        # 실패한 파일들의 상세 정보
        if stats['error_details']:
            self.log_message("\n❌ 실패한 파일 상세:")
            for error_info in stats['error_details']:
                if error_info['status'] == 'error':
                    self.log_message(f"   📁 {error_info['filename']}")
                    self.log_message(f"      🔍 오류 유형: {error_info['error_type']}")
                    self.log_message(f"      📝 오류 내용: {error_info['error_message']}")
                elif error_info['status'] == 'no_matching_columns':
                    self.log_message(f"   📁 {error_info['filename']}")
                    self.log_message(f"      ⚠️ 문제: 추출할 열을 찾을 수 없음")
                    self.log_message(f"      📋 사용 가능한 열: {', '.join(error_info['available_columns'])}")
        
        # 결과 파일 정보
        self.log_message(f"\n💾 결과 파일: {output_filename}")
        self.log_message(f"📁 저장 위치: {self.folder_path}")
        
        # 성공률 계산
        success_rate = (stats['successful_files'] / stats['total_files']) * 100
        self.log_message(f"📈 성공률: {success_rate:.1f}%")
        
        self.log_message("=" * 60)
        self.log_message("🎉 모든 작업이 완료되었습니다!")
        self.log_message("=" * 60)

    def _reset_ui(self):
        self.is_processing = False
        self.run_button.configure(state="normal", text="데이터 통합 실행")
        self.progress_bar.set(0)
        self.progress_text.configure(text="0%")

    def update_status(self, status, color):
        self.status_indicator.configure(text=f"● {status}", text_color=color)

    def update_progress(self, progress):
        self.progress_bar.set(progress)
        percentage = int(progress * 100)
        self.progress_text.configure(text=f"{percentage}%")
        
        # 진행률에 따른 색상 변경
        if percentage < 30:
            self.progress_bar.configure(progress_color=self.colors['warning'])
        elif percentage < 70:
            self.progress_bar.configure(progress_color=self.colors['primary'])
        else:
            self.progress_bar.configure(progress_color=self.colors['secondary'])

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 메인 스레드에서 안전하게 로그 추가
        def add_log():
            try:
                self.log_text.insert("end", log_entry)
                self.log_text.see("end")
                
                # 로그 텍스트가 너무 길어지면 오래된 부분만 삭제 (메모리 관리)
                # 2000줄을 넘어가면 처음 500줄 삭제
                current_lines = int(self.log_text.index("end-1c").split('.')[0])
                if current_lines > 2000:
                    self.log_text.delete("1.0", "500.0")
                    
            except Exception as e:
                print(f"로그 추가 중 오류: {e}")
        
        # 약간의 지연을 추가하여 UI 안정성 확보
        self.root.after(10, add_log)

    def clear_log(self):
        """로그를 지우고 초기 메시지만 남깁니다."""
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "[시스템] 로그가 지워졌습니다.\n")
        self.log_text.insert("end", "[시스템] 새로운 작업을 시작하세요.\n")
        self.log_text.see("end")

# 애플리케이션 실행
if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernExcelProcessorApp(root)
    root.mainloop()