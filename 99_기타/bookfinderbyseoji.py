import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import time, random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def search_publisher(driver, publisher):
    wait = WebDriverWait(driver, 10)
    driver.get("https://www.nl.go.kr/seoji/")
    try:
        select_box_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="topSearchWrap"]/select')))
        select_box = Select(select_box_element)
        select_box.select_by_visible_text("발행처")

        input_box = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="topSearchWrap"]/input')))
        input_box.clear()
        for char in publisher:
            input_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(0.5, 1.5))
        input_box.submit()

        try:
            select_count_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="contents"]/div[2]/div/form/div/div[2]/div[1]/select'))
            )
            select_count = Select(select_count_element)
            select_count.select_by_visible_text("100개")

            # 클릭 후 확인(검색/적용) 버튼이 있으면 누른다, 그 다음 결과 영역이 로드될 때까지 대기
            try:
                confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="contents"]/div[2]/div[2]/form/div/div[2]/a')))
                try:
                    confirm_btn.click()
                except Exception:
                    # 일부 경우 스크립트로 클릭이 필요할 수 있음
                    driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(random.uniform(0.5, 1.0))
            except Exception:
                # 확인 버튼이 없거나 클릭할 수 없는 경우도 있으므로 무시하고 진행
                pass

            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="resultList_div"]/form')))
        except Exception:
            pass

        all_results = []
        page_loaded = True
        while page_loaded:
            try:
                result_form = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="resultList_div"]/form')))
                page_text = result_form.text
                all_results.append(page_text)

                next_button_xpath = '//*[@id="contents"]/div[2]/div[2]/form/div/div[2]/a'
                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
                    wait.until(EC.staleness_of(result_form))
                    next_button.click()
                    time.sleep(random.uniform(1.5, 2.5))
                    page_loaded = True
                except:
                    page_loaded = False
            except:
                page_loaded = False
                if not all_results:
                    all_results.append("검색 결과 없음")

        result_text = "\n\n--- 페이지 구분 ---\n\n".join(all_results)
    except Exception as e:
        print(f"'{publisher}' 검색 중 오류 발생: {e}")
        result_text = f"오류 발생: {e}"
    return result_text


def load_excel_publishers():
    excel_path = filedialog.askopenfilename(
        title="출판사명 엑셀 파일 선택", filetypes=[("Excel files", "*.xlsx")]
    )
    if not excel_path:
        messagebox.showwarning("선택 취소", "엑셀 파일이 선택되지 않았습니다.")
        return []

    try:
        df = pd.read_excel(excel_path)
        publishers = df.iloc[:, 0].dropna().tolist()
        return publishers
    except Exception as e:
        messagebox.showerror("파일 오류", f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
        return []


def run_process():
    # --- 출판사 목록 불러오기 ---
    publishers = load_excel_publishers()
    if not publishers:
        return

    # --- 출판사 선택 ---
    selection_window = tk.Toplevel(app)
    selection_window.title("검색할 출판사 선택")
    selection_window.geometry("400x250")

    ttk.Label(selection_window, text="엑셀에서 불러온 출판사 목록").pack(pady=5)
    publisher_var = tk.StringVar(value=publishers)
    listbox = tk.Listbox(selection_window, listvariable=publisher_var, height=10, selectmode="extended")
    listbox.pack(fill="both", expand=True, padx=10, pady=5)

    selected_publishers = []

    def confirm_selection():
        selection = [listbox.get(i) for i in listbox.curselection()]
        if not selection:
            messagebox.showwarning("선택 오류", "최소 1개 이상의 출판사를 선택하세요.")
            return
        selected_publishers.extend(selection)
        selection_window.destroy()

    ttk.Button(selection_window, text="선택 완료", command=confirm_selection).pack(pady=10)
    selection_window.wait_window()

    if not selected_publishers:
        return

    # --- 결과 저장 폴더 선택 ---
    save_folder = filedialog.askdirectory(title="결과 저장 폴더 선택")
    if not save_folder:
        messagebox.showwarning("취소", "저장 폴더가 선택되지 않았습니다.")
        return

    progress["maximum"] = len(selected_publishers)
    results = []
    driver = None
    try:
        driver = make_driver()
        for i, pub in enumerate(selected_publishers, start=1):
            log.insert(tk.END, f"[{i}/{len(selected_publishers)}] {pub} 검색 중...\n")
            log.see(tk.END)
            app.update_idletasks()
            text_data = search_publisher(driver, pub)
            results.append({"출판사명": pub, "결과텍스트": text_data})
            progress["value"] = i
            time.sleep(random.uniform(2.5, 4.5))
    except Exception as e:
        messagebox.showerror("실행 오류", f"자동화 중 심각한 오류 발생: {e}")
    finally:
        if driver:
            driver.quit()

    if not results:
        messagebox.showinfo("완료", "검색 결과가 없습니다.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_filename = f"검색결과_{timestamp}.xlsx"
    save_path = f"{save_folder}/{save_filename}"

    try:
        pd.DataFrame(results).to_excel(save_path, index=False)
        messagebox.showinfo("완료", f"총 {len(results)}개 결과 저장 완료:\n{save_path}")
    except Exception as e:
        messagebox.showerror("저장 오류", f"엑셀 저장 중 오류 발생: {e}")


# ---------------- GUI ----------------
app = tk.Tk()
app.title("국립중앙도서관 출판사별 자료 수집기")
app.geometry("650x420")
frame = ttk.Frame(app, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="1️⃣ 출판사 엑셀을 불러와 선택 후 자동 검색").pack(pady=5)
ttk.Button(frame, text="실행", command=run_process).pack(pady=5)
progress = ttk.Progressbar(frame, length=550, mode="determinate")
progress.pack(pady=5)
log = tk.Text(frame, height=15)
log.pack(fill="both", expand=True)

app.mainloop()
