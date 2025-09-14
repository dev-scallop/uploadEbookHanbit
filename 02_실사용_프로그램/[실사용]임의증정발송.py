import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
from datetime import datetime
import re

class DispatchListGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("발송 대상 리스트 생성 프로그램")
        master.geometry("800x700") # 창 크기 설정

        self.dispatch_history_df = None # 견본 발송 내역 DataFrame

        # UI 요소 생성 및 배치
        self._create_widgets()

    def _create_widgets(self):
        # 1. 홍보 타겟 도서명 입력
        tk.Label(self.master, text="1. 홍보 타겟 도서명 입력:", font=("Inter", 12, "bold")).pack(pady=(10, 0), anchor="w", padx=10)
        self.target_book_name_entry = tk.Entry(self.master, width=50, font=("Inter", 10), relief="solid", bd=1, highlightbackground="gray", highlightthickness=1)
        self.target_book_name_entry.pack(pady=5, padx=10, anchor="w")

        # 2. 강의 정보 입력 (텍스트 영역)
        tk.Label(self.master, text="2. 강의 정보 입력 (대학, 이름, 연락처를 공백/탭/쉼표로 구분하여 붙여넣으세요):", font=("Inter", 12, "bold")).pack(pady=(10, 0), anchor="w", padx=10)
        self.lecture_info_text = scrolledtext.ScrolledText(self.master, width=90, height=10, font=("Inter", 10), relief="solid", bd=1, highlightbackground="gray", highlightthickness=1)
        self.lecture_info_text.pack(pady=5, padx=10)
        self.lecture_info_text.insert(tk.END, "예시:\n대학1 이름1 010-1234-5678\n대학2 이름2 01098765432\n대학3,이름3,01011223344")

        # 3. 견본 발송 내역 파일 업로드
        tk.Label(self.master, text="3. 견본 발송 내역 파일 업로드 (.xlsx 또는 .xls):", font=("Inter", 12, "bold")).pack(pady=(10, 0), anchor="w", padx=10)
        self.file_path_label = tk.Label(self.master, text="선택된 파일 없음", font=("Inter", 10), width=50, anchor="w", relief="solid", bd=1, highlightbackground="gray", highlightthickness=1)
        self.file_path_label.pack(pady=5, padx=10, anchor="w")
        tk.Button(self.master, text="파일 선택", command=self._load_dispatch_history_file,
                  bg="#4CAF50", fg="white", font=("Inter", 10, "bold"),
                  relief="raised", bd=2, cursor="hand2",
                  activebackground="#45a049", activeforeground="white",
                  width=15, height=1).pack(pady=5, padx=10, anchor="w")

        # 4. 발송 리스트 생성 버튼
        tk.Button(self.master, text="발송 리스트 생성", command=self._generate_dispatch_list,
                  bg="#008CBA", fg="white", font=("Inter", 14, "bold"),
                  relief="raised", bd=3, cursor="hand2",
                  activebackground="#007B9E", activeforeground="white",
                  width=20, height=2).pack(pady=20)

        # 상태 메시지 라벨
        self.status_label = tk.Label(self.master, text="", fg="blue", font=("Inter", 10))
        self.status_label.pack(pady=10)

    def _normalize_phone_number(self, phone_str):
        """전화번호에서 하이픈과 공백을 제거하고 숫자만 반환합니다."""
        if pd.isna(phone_str):
            return ""
        return re.sub(r'[^0-9]', '', str(phone_str))

    def _parse_lecture_info(self, text_data):
        """
        텍스트 영역에서 강의 정보를 파싱하여 DataFrame으로 반환합니다.
        형식: 대학 이름 연락처 (공백, 탭 또는 쉼표로 구분)
        """
        lines = text_data.strip().split('\n')
        parsed_data = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 공백, 탭 또는 쉼표로 분리
            parts = re.split(r'[\s,]+', line)
            if len(parts) >= 3:
                university = parts[0]
                name = parts[1]
                contact = self._normalize_phone_number(parts[2]) # 연락처 정규화
                parsed_data.append({"대학": university, "이름": name, "연락처": contact})
            else:
                print(f"경고: 유효하지 않은 강의 정보 형식입니다: {line}")
        return pd.DataFrame(parsed_data)

    def _load_dispatch_history_file(self):
        """견본 발송 내역 엑셀 파일을 로드합니다."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            try:
                self.file_path_label.config(text=file_path)
                # 파일 확장자에 따라 다른 엔진 사용
                if file_path.endswith('.xls'):
                    self.dispatch_history_df = pd.read_excel(file_path, engine='xlrd')
                else: # .xlsx
                    self.dispatch_history_df = pd.read_excel(file_path, engine='openpyxl')

                # '전화번호' 열 정규화
                if '전화번호' in self.dispatch_history_df.columns:
                    self.dispatch_history_df['전화번호_정규화'] = self.dispatch_history_df['전화번호'].apply(self._normalize_phone_number)
                else:
                    messagebox.showerror("오류", "견본 발송 내역 파일에 '전화번호' 열이 없습니다.")
                    self.dispatch_history_df = None
                    self.file_path_label.config(text="선택된 파일 없음")
                    return

                # '출고일자' 열을 datetime 형식으로 변환
                if '출고일자' in self.dispatch_history_df.columns:
                    self.dispatch_history_df['출고일자'] = pd.to_datetime(self.dispatch_history_df['출고일자'], errors='coerce')
                    # 날짜 변환 실패한 행 제거 (또는 경고)
                    self.dispatch_history_df.dropna(subset=['출고일자'], inplace=True)
                else:
                    messagebox.showerror("오류", "견본 발송 내역 파일에 '출고일자' 열이 없습니다.")
                    self.dispatch_history_df = None
                    self.file_path_label.config(text="선택된 파일 없음")
                    return
                
                # '대표도서명' 열이 없는 경우 오류 메시지
                if '대표도서명' not in self.dispatch_history_df.columns:
                    messagebox.showerror("오류", "견본 발송 내역 파일에 '대표도서명' 열이 없습니다.")
                    self.dispatch_history_df = None
                    self.file_path_label.config(text="선택된 파일 없음")
                    return

                self.status_label.config(text=f"'{file_path.split('/')[-1]}' 파일이 성공적으로 로드되었습니다.", fg="green")

            except FileNotFoundError:
                messagebox.showerror("오류", "파일을 찾을 수 없습니다.")
                self.dispatch_history_df = None
                self.file_path_label.config(text="선택된 파일 없음")
            except pd.errors.EmptyDataError:
                messagebox.showerror("오류", "파일이 비어있습니다.")
                self.dispatch_history_df = None
                self.file_path_label.config(text="선택된 파일 없음")
            except Exception as e:
                messagebox.showerror("오류", f"파일 로드 중 오류 발생: {e}\n파일 형식이 올바른지 확인해주세요.")
                self.dispatch_history_df = None
                self.file_path_label.config(text="선택된 파일 없음")

    def _process_data(self, target_book_name, lecture_df, dispatch_df):
        """
        강의 정보와 발송 내역을 비교하여 발송 대상 리스트를 생성합니다.
        """
        output_data = []

        # 타겟 도서명에 대한 공백 제거 및 소문자 변환
        normalized_target_book_name = target_book_name.strip().lower()

        for idx, lecture_row in lecture_df.iterrows():
            lecture_contact = lecture_row['연락처']
            lecture_name = lecture_row['이름']
            lecture_university = lecture_row['대학'] # Get the university name

            # 해당 연락처로 발송된 내역 필터링
            matching_dispatches = dispatch_df[dispatch_df['전화번호_정규화'] == lecture_contact].copy()

            memo = ""
            memo2 = ""
            memo2_entries = [] # 메모2에 들어갈 항목들을 저장할 리스트
            address = ""
            name_from_dispatch = lecture_name # 기본값은 강의 정보의 이름

            if not matching_dispatches.empty:
                # 가장 최근 출고일자 기준으로 정렬
                matching_dispatches = matching_dispatches.sort_values(by='출고일자', ascending=False)
                
                # 택배고객명과 배송지주소 추출 (가장 최근 발송 내역 기준)
                latest_dispatch = matching_dispatches.iloc[0]
                if '택배고객명' in latest_dispatch and pd.notna(latest_dispatch['택배고객명']):
                    name_from_dispatch = latest_dispatch['택배고객명']
                if '배송지주소' in latest_dispatch and pd.notna(latest_dispatch['배송지주소']):
                    address = latest_dispatch['배송지주소']

                # '메모'에는 타겟 도서 발송 여부만 기록
                # 해당 연락처로 타겟 도서가 발송된 적이 있는지 모든 매칭 내역을 확인
                if '대표도서명' in matching_dispatches.columns: # 열 존재 여부 다시 확인
                    for _, disp_row in matching_dispatches.iterrows():
                        if pd.notna(disp_row['대표도서명']) and str(disp_row['대표도서명']).strip().lower() == normalized_target_book_name:
                            memo = "이미 발송함"
                            break # 타겟 도서가 발송된 것을 찾았으므로 더 이상 확인할 필요 없음
                
                # '메모2'에는 최근 6권까지의 발송 내역 기록
                # '대표도서명' 열이 존재하고 유효한 경우에만 처리
                if '대표도서명' in matching_dispatches.columns:
                    for i in range(min(6, len(matching_dispatches))):
                        dispatch_entry = matching_dispatches.iloc[i]
                        dispatch_date_str = dispatch_entry['출고일자'].strftime('%Y-%m-%d')
                        book_name = str(dispatch_entry['대표도서명']).strip() if pd.notna(dispatch_entry['대표도서명']) else "도서명 없음"
                        memo2_entries.append(f"{dispatch_date_str}: {book_name}")
                
                memo2 = "\n".join(memo2_entries) # 줄바꿈으로 연결

            else:
                # 발송 내역이 없는 경우, 주소는 빈 값
                address = ""
                # 발송 내역이 없으므로 memo와 memo2는 초기화된 빈 값으로 유지됩니다.

            output_data.append({
                "NO": 0, # 순번은 최종 DataFrame 생성 후 부여
                "이름": name_from_dispatch,
                "우편번호": "", # 현재 데이터 없음, 빈 값
                "주소": address,
                "전화번호": lecture_row['연락처'],
                "휴대전화": lecture_row['연락처'], # 전화번호와 동일
                "도서코드": "", # 현재 데이터 없음, 빈 값
                "도서명": target_book_name,
                "수량": 1,
                "정가": "", # 현재 데이터 없음, 빈 값
                "할인율": "", # 현재 데이터 없음, 빈 값
                "할인가": "", # 현재 데이터 없음, 빈 값
                "메모": memo, # 타겟 도서 발송 여부
                "메모2": memo2, # 최근 발송일자 및 도서명 (최대 6권)
                "메모3": lecture_university # Added Memo3 for university
            })

        output_df = pd.DataFrame(output_data)
        output_df['NO'] = range(1, len(output_df) + 1) # 순번 부여
        return output_df

    def _generate_dispatch_list(self):
        """발송 리스트 생성 버튼 클릭 시 호출되는 함수입니다."""
        target_book_name = self.target_book_name_entry.get().strip()
        lecture_info_text = self.lecture_info_text.get("1.0", tk.END).strip()

        # 필수 입력값 검증
        if not target_book_name:
            messagebox.showwarning("입력 오류", "홍보 타겟 도서명을 입력해주세요.")
            return
        if not lecture_info_text or lecture_info_text == "예시:\n대학1 이름1 010-1234-5678\n대학2 이름2 01098765432\n대학3,이름3,01011223344":
            messagebox.showwarning("입력 오류", "강의 정보를 입력해주세요.")
            return
        if self.dispatch_history_df is None:
            messagebox.showwarning("입력 오류", "견본 발송 내역 파일을 업로드해주세요.")
            return

        self.status_label.config(text="발송 리스트를 생성 중입니다...", fg="blue")
        self.master.update_idletasks() # GUI 업데이트

        try:
            # 강의 정보 파싱
            lecture_df = self._parse_lecture_info(lecture_info_text)
            if lecture_df.empty:
                messagebox.showerror("데이터 오류", "강의 정보를 올바르게 파싱할 수 없습니다. 형식을 확인해주세요.")
                self.status_label.config(text="발송 리스트 생성 실패.", fg="red")
                return

            # 데이터 처리
            output_df = self._process_data(target_book_name, lecture_df, self.dispatch_history_df)

            # 파일 저장
            current_date = datetime.now().strftime("%Y%m%d")
            # 파일명에 사용할 수 없는 문자 제거
            safe_target_book_name = re.sub(r'[\\/:*?"<>|]', '', target_book_name) 
            file_name = f"발송대상리스트_{safe_target_book_name}_{current_date}.xlsx"
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=file_name
            )

            if save_path:
                output_df.to_excel(save_path, index=False)
                messagebox.showinfo("완료", f"발송 대상 리스트가 성공적으로 생성되었습니다:\n{save_path}")
                self.status_label.config(text=f"리스트 생성 완료: {file_name}", fg="green")
            else:
                self.status_label.config(text="파일 저장이 취소되었습니다.", fg="orange")

        except Exception as e:
            messagebox.showerror("오류", f"리스트 생성 중 오류 발생: {e}")
            self.status_label.config(text="발송 리스트 생성 실패.", fg="red")

# 메인 함수
if __name__ == "__main__":
    # xlrd 엔진이 필요할 수 있으므로 설치 안내
    try:
        import xlrd
    except ImportError:
        print("xlrd 라이브러리가 설치되어 있지 않습니다. .xls 파일을 처리하려면 'pip install xlrd'를 실행해주세요.")

    root = tk.Tk()
    app = DispatchListGeneratorApp(root)
    root.mainloop()