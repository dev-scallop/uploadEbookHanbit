import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import threading


def run_script_threaded():
    file_path = excel_path_entry.get()
    driver_path = driver_path_entry.get()

    if not file_path or not driver_path:
        messagebox.showerror("오류", "엑셀 파일과 크롬드라이버 파일을 모두 선택해주세요.")
        return

    try:
        df = pd.read_excel(file_path, sheet_name=None)
    except Exception as e:
        messagebox.showerror("오류", f"엑셀 파일 처리 중 오류 발생: {e}")
        return

    names = df['Sheet1'].iloc[:, 0].dropna().tolist()
    emails = df['Sheet1'].iloc[:, 1].dropna().tolist()
    links = df['Sheet1'].iloc[:, 2].dropna().tolist()

    if not names or not emails or not links:
        messagebox.showerror("오류", "엑셀 파일에 필요한 데이터가 부족합니다.")
        return

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 25)  # ⏳ 요소 찾는 시간 증가 (최대 25초)

    if 'Sheet2' not in df:
        df['Sheet2'] = pd.DataFrame(columns=["로그"])

    try:
        driver.get(links[0])
        response = messagebox.askyesno("로그인 확인", "로그인을 완료하시면 확인 버튼을 눌러주세요")
        if not response:
            driver.quit()
            return

        for name, email, link in zip(names, emails, links):
            try:
                driver.get(link)
                time.sleep(5)

                # ✅ 이메일 입력 필드 최적화된 XPATH
                email_input_xpath = "//input[contains(@class, 'mat-mdc-input-element') and contains(@class, 'mdc-text-field__input')]"

                # ✅ 최대 25초까지 요소 기다리기 후 첫 번째 요소 선택
                email_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, email_input_xpath)))

                if not email_inputs:
                    raise NoSuchElementException("입력 필드를 찾을 수 없음")

                email_input = email_inputs[0]  # 첫 번째 입력 필드 선택
                email_input.clear()
                email_input.send_keys(email)

                # 엔터 키 입력 후 8초 대기
                email_input.send_keys("\ue007")  # 엔터 키 코드
                time.sleep(8)

                # ✅ 이메일 검증 방식 변경 (입력 필드 → 표시 영역 확인)
                try:
                    # 타겟 요소 XPATH
                    target_xpath = "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/div/ng-component/div[2]/quality-reviewers/mat-list"

                    # 요소 존재 확인 (최대 25초 대기)
                    email_display_element = wait.until(
                        EC.presence_of_element_located((By.XPATH, target_xpath))
                    )

                    # 요소 내 텍스트 추출 및 이메일 포함 여부 확인
                    displayed_text = email_display_element.text.strip().lower()
                    target_email = email.strip().lower()

                    if target_email in displayed_text:
                        log_text.insert(tk.END, f"{name} ({email}) 등록 확인 완료 ✅\n")
                        df['Sheet2'] = pd.concat([df['Sheet2'], pd.DataFrame([{"로그": f"{name} ({email}) 등록 완료 ✅"}])],
                                                 ignore_index=True)
                    else:
                        raise ValueError("이메일이 표시 영역에 없음")

                except Exception as e:
                    log_text.insert(tk.END, f"{name} ({email}) 등록 실패 ❌ (사유: {str(e)})\n")
                    df['Sheet2'] = pd.concat(
                        [df['Sheet2'], pd.DataFrame([{"로그": f"{name} ({email}) 등록 실패 ❌: {str(e)}"}])],
                        ignore_index=True)
                    log_text.see(tk.END)
                    continue

                log_text.see(tk.END)

            except TimeoutException:
                log_text.insert(tk.END, f"{name} ({email}) 처리 중 시간 초과 오류 발생: 요소가 나타나지 않음 ⏳\n")
                df['Sheet2'] = pd.concat([df['Sheet2'], pd.DataFrame([{"로그": f"{name} ({email}) 처리 중 시간 초과 오류 발생 ⏳"}])],
                                         ignore_index=True)
                log_text.see(tk.END)
            except NoSuchElementException:
                log_text.insert(tk.END, f"{name} ({email}) 요소 찾기 실패 ❌ (입력 필드 없음)\n")
                df['Sheet2'] = pd.concat([df['Sheet2'], pd.DataFrame([{"로그": f"{name} ({email}) 요소 찾기 실패 ❌"}])],
                                         ignore_index=True)
                log_text.see(tk.END)
            except Exception as e:
                log_text.insert(tk.END, f"{name} ({email}) 처리 중 예기치 않은 오류 발생: {e} ⚠️\n")
                df['Sheet2'] = pd.concat(
                    [df['Sheet2'], pd.DataFrame([{"로그": f"{name} ({email}) 처리 중 예기치 않은 오류 발생 ⚠️: {e}"}])],
                    ignore_index=True)
                log_text.see(tk.END)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df['Sheet1'].to_excel(writer, sheet_name='Sheet1', index=False)
            df['Sheet2'].to_excel(writer, sheet_name='Sheet2', index=False)

    except Exception as e:
        messagebox.showerror("오류", f"전체 작업 중 오류 발생: {e}")

    finally:
        messagebox.showinfo("완료", "모든 작업이 완료되었습니다.")
        if 'driver' in locals():
            driver.quit()


def run_script():
    threading.Thread(target=run_script_threaded).start()


def select_excel_file():
    file_path = filedialog.askopenfilename(title="엑셀 파일을 선택하세요", filetypes=[("Excel files", "*.xls;*.xlsx")])
    excel_path_entry.delete(0, tk.END)
    excel_path_entry.insert(0, file_path)


def select_driver_file():
    driver_path = filedialog.askopenfilename(title="크롬 드라이버 파일을 선택하세요", filetypes=[("Executable files", "*.exe")])
    driver_path_entry.delete(0, tk.END)
    driver_path_entry.insert(0, driver_path)


def on_enter_key(event):
    run_script()


def close_app():
    root.destroy()


# 🖥️ GUI 인터페이스 설정
root = tk.Tk()
root.title("전자책 자동 등록 스크립트")

excel_label = tk.Label(root, text="엑셀 파일 경로:")
excel_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

excel_path_entry = tk.Entry(root, width=50)
excel_path_entry.grid(row=0, column=1, padx=10, pady=5)

excel_button = tk.Button(root, text="찾아보기", command=select_excel_file)
excel_button.grid(row=0, column=2, padx=10, pady=5)

driver_label = tk.Label(root, text="크롬 드라이버 경로:")
driver_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)

driver_path_entry = tk.Entry(root, width=50)
driver_path_entry.grid(row=1, column=1, padx=10, pady=5)

driver_button = tk.Button(root, text="찾아보기", command=select_driver_file)
driver_button.grid(row=1, column=2, padx=10, pady=5)

run_button = tk.Button(root, text="실행", command=run_script)
run_button.grid(row=2, column=1, pady=10)

log_text = scrolledtext.ScrolledText(root, width=60, height=10)
log_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5)

exit_button = tk.Button(root, text="종료", command=close_app)
exit_button.grid(row=4, column=1, pady=10)

root.bind("<Return>", on_enter_key)

root.mainloop()
