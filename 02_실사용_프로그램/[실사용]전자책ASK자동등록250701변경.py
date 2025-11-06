import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, NoAlertPresentException
import threading
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options
from typing import List, Tuple
from webdriver_manager.chrome import ChromeDriverManager

class EbookRegistration:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        """크롬 드라이버 설정 - 자동 다운로드"""
        try:
            chrome_options = Options()
            # chrome_options.add_argument("--headless")  # 일단 주석 처리
            
            # ChromeDriverManager를 사용하여 자동으로 크롬 드라이버 다운로드 및 설정
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
        except Exception as e:
            messagebox.showerror("드라이버 오류", f"크롬 드라이버 설정 중 오류 발생: {e}")
            raise

    def login(self):
        """로그인 페이지로 이동 후, 사용자가 직접 로그인하도록 안내"""
        self.driver.get("https://www.hanbit.co.kr/login?redirect=https://www.hanbit.co.kr/hb_admin")
        messagebox.showinfo("로그인 필요", "로그인 페이지가 열렸습니다.\n로그인을 완료한 후 확인을 눌러주세요.")
        # 사용자가 직접 로그인할 때까지 대기
        while True:
            if self.driver is not None and "hb_admin" in self.driver.current_url:
                break
            time.sleep(1)

    def click_register_button(self):
        """검색 목록의 마지막 등록 버튼을 클릭하는 함수"""
        attempts = 3
        for attempt in range(attempts):
            try:
                register_buttons = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "btn_register")))
                if register_buttons:
                    register_buttons[-1].click()
                return
            except StaleElementReferenceException:
                if attempt < attempts - 1:
                    time.sleep(1)
                else:
                    raise

    def process_ebook_registration(self, user_name: str, email: str, book_name: str) -> bool:
        """전자책 등록 처리"""
        try:
            self.driver.get("https://www.hanbit.co.kr/hb_admin/front.acaebookask.php")
            time.sleep(2)

            self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn_sch"))).click()
            time.sleep(2)
            self.driver.switch_to.window(self.driver.window_handles[-1])

            search_key = self.wait.until(EC.presence_of_element_located((By.ID, "search_key")))
            search_key.click()
            time.sleep(1)
            
            # 드롭다운에서 "아이디" 옵션 선택 (보통 1번 인덱스)
            options = search_key.find_elements(By.TAG_NAME, "option")
            # 옵션 텍스트로 "아이디" 또는 "ID" 찾기
            for i, option in enumerate(options):
                if "아이디" in option.text or "ID" in option.text.upper():
                    option.click()
                    break
            else:
                # 아이디 옵션을 찾지 못한 경우 1번 인덱스 선택 (일반적으로 아이디가 1번)
                options[1].click() if len(options) > 1 else options[0].click()

            keyword_input = self.wait.until(EC.presence_of_element_located((By.ID, "keyword")))
            keyword_input.send_keys(user_name + "\n")
            time.sleep(2)

            self.click_register_button()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(2)

            email_input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='hao_gmail']")))
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)

            checkbox = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='frm']/section/div/div/div[1]/div[2]/div[2]/div/input[2]")))
            checkbox.click()
            time.sleep(1)

            ebook_search_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'btn-primary') and contains(@class, 'mb10') and contains(., 'eBook 검색')]")))
            ebook_search_button.click()
            time.sleep(2)

            original_window = self.driver.current_window_handle
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break

            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "keyword")))
                ebook_input = self.wait.until(EC.presence_of_element_located((By.ID, "keyword")))
                ebook_input.clear()
                ebook_input.send_keys(book_name)
                time.sleep(1)
                ebook_input.send_keys("\n")
                time.sleep(2)

                try:
                    register_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn_register")))
                    register_button.click()
                except TimeoutException:
                    messagebox.showerror("오류", f"{book_name} 책 검색 후 등록 버튼을 찾을 수 없습니다.")
                    self.driver.switch_to.window(original_window)
                    return False

                self.driver.close()
                self.driver.switch_to.window(original_window)
                time.sleep(2)

                self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn_register"))).click()
                time.sleep(1)
                try:
                    alert = Alert(self.driver)
                    alert.accept()
                    log_text.insert(tk.END, "Alert 창 확인 및 처리 완료\n")
                except NoAlertPresentException:
                    pass
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).send_keys(Keys.ENTER)
                time.sleep(2)

                log_text.insert(tk.END, f"{user_name} - {book_name} - {email} 입력 완료!\n")
                log_text.see(tk.END)
                return True

            except (NoSuchElementException, TimeoutException, NoAlertPresentException) as e:
                log_text.insert(tk.END, f"오류 발생: {e}\n")
                self.driver.close()
                self.driver.switch_to.window(original_window)
                return False

        except Exception as e:
            log_text.insert(tk.END, f"처리 중 오류 발생: {e}\n")
            return False

    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()

def run_script_threaded():
    file_path = excel_path_entry.get()

    if not file_path:
        messagebox.showerror("오류", "엑셀 파일을 선택해주세요.")
        return

    try:
        # openpyxl을 사용하여 엑셀 파일 읽기
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        
        names = []
        emails = []
        books = []
        
        for row in sheet.iter_rows(min_row=2, values_only=True):  # 헤더 제외
            if row[0] and row[1] and row[2]:  # 모든 컬럼에 값이 있는 경우만
                names.append(row[0])
                emails.append(row[1])
                books.append(row[2])
                
    except Exception as e:
        messagebox.showerror("오류", f"엑셀 파일 처리 중 오류 발생: {e}")
        return

    if not names or not emails or not books:
        messagebox.showerror("오류", "엑셀 파일에 필요한 데이터가 부족합니다.")
        return

    ebook_reg = EbookRegistration()
    try:
        ebook_reg.login()
        success_count = 0
        total_count = len(names)

        for user_name, email, book_name in zip(names, emails, books):
            if ebook_reg.process_ebook_registration(user_name, email, book_name):
                success_count += 1
                log_text.insert(tk.END, f"{user_name} - {book_name} 신청 완료!\n")
                log_text.see(tk.END)

        messagebox.showinfo("완료", f"총 {total_count}건 중 {success_count}건 처리 완료되었습니다.")

    except Exception as e:
        messagebox.showerror("오류", f"전체 작업 중 오류 발생: {e}")
    finally:
        ebook_reg.close()

def run_script():
    threading.Thread(target=run_script_threaded).start()

def select_excel_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls;*.xlsx")])
    excel_path_entry.delete(0, tk.END)
    excel_path_entry.insert(0, file_path)

# GUI 설정
root = tk.Tk()
root.title("전자책 자동 등록 스크립트")

# 엑셀 파일 형태 설명 추가
info_label = tk.Label(root, text="엑셀 파일 형태: A열(이름), B열(이메일), C열(책제목) - 첫 번째 행은 헤더로 제외됩니다", 
                     fg="blue", font=("Arial", 9))
info_label.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

# 크롬 드라이버 자동 다운로드 안내 추가
driver_info_label = tk.Label(root, text="크롬 드라이버는 자동으로 다운로드됩니다", 
                            fg="green", font=("Arial", 9))
driver_info_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

excel_label = tk.Label(root, text="엑셀 파일 경로:")
excel_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)

excel_path_entry = tk.Entry(root, width=50)
excel_path_entry.grid(row=2, column=1, padx=10, pady=5)

excel_button = tk.Button(root, text="찾아보기", command=select_excel_file)
excel_button.grid(row=2, column=2, padx=10, pady=5)

run_button = tk.Button(root, text="실행", command=run_script)
run_button.grid(row=3, column=1, pady=20)

log_text = scrolledtext.ScrolledText(root, width=60, height=10)
log_text.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

root.mainloop()