import os
import unicodedata
import re
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

def normalize(text):
    text = unicodedata.normalize("NFKC", text)  # Chuẩn hóa Unicode
    text = re.sub(r"\s+", " ", text).strip()    # Xóa khoảng trắng thừa
    return text

def read_answers(file_path):
    answers = {}
    with open(file_path, "r", encoding="utf-8") as file:
        question = None
        for line in file:
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                question = normalize(line.split(".", 1)[1].strip())
                answers[question] = []
            elif line.startswith("#") and question:
                answers[question].append(normalize(line[1:].strip()))
    return answers

def get_question_type(question_element):
    if len(question_element.find_elements(By.CSS_SELECTOR, "[data-automation-id='checkbox']")) > 0:
        return "Multiple Choice"
    elif len(question_element.find_elements(By.CSS_SELECTOR, "[data-automation-id='radio']")) > 0:
        return "Single Choice"
    return "Unknown"

def extract_questions(driver):
    questions_data = []
    question_elements = driver.find_elements(By.CSS_SELECTOR, "[data-automation-id='questionItem']")
    
    for question_element in question_elements:
        try:
            question_text_element = question_element.find_element(By.CSS_SELECTOR, "[data-automation-id='questionTitle'] .text-format-content")
            question_text = question_text_element.text.strip() if question_text_element else "Không tìm thấy câu hỏi"
            question_type = get_question_type(question_element)

            choices = []
            choice_elements = question_element.find_elements(By.CSS_SELECTOR, "[data-automation-id='choiceItem']")
            for choice_element in choice_elements:
                try:
                    choice_text_element = choice_element.find_element(By.CSS_SELECTOR, "[aria-label]")
                    choice_text = choice_text_element.get_attribute("aria-label").strip() if choice_text_element else "Không tìm thấy đáp án"
                    choices.append(choice_text)
                except Exception as e:
                    print(f"❌ Lỗi khi trích xuất đáp án: {e}")

            questions_data.append({
                "question": question_text,
                "type": question_type,
                "choices": choices
            })
        except Exception as e:
            print(f"❌ Lỗi khi trích xuất câu hỏi: {e}")
    return questions_data

def bypass_confirmation(driver):
    """Kiểm tra và nhấn nút xác nhận nếu có"""
    try:
        start_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Bắt đầu')] | //button[contains(text(), 'Tiếp tục')] | //button[contains(text(), 'start')] | //button[contains(text(), 'Start')]")
        start_button.click()
        time.sleep(2)  # Đợi form load
        print("✅ Đã xác nhận, vào form...")
    except NoSuchElementException:
        print("➡️ Không cần xác nhận, vào form trực tiếp.")

def auto_fill_form(txt_path, form_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    user_path = os.path.expanduser("~")  # Lấy đường dẫn thư mục người dùng
    chrome_profile_path = os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data")
    print(chrome_profile_path)
    options.add_argument(f"--user-data-dir={chrome_profile_path}")
    options.add_argument("--profile-directory=Default")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(form_url)
    time.sleep(3)

    # ✅ Thêm xử lý trang xác nhận
    bypass_confirmation(driver)

    questions_data = extract_questions(driver)
    #print(questions_data)
    answers = read_answers(txt_path)
    #print(answers)

    for question_data in questions_data:
        question_text = question_data["question"]
        choices = question_data["choices"]
        found_answer = False

        for key in answers.keys():
            if key in normalize(question_text):
                correct_answers = answers[key]
                question_container = driver.find_element(By.XPATH, f"//span[contains(text(), '{question_text}')]/ancestor::div[@data-automation-id='questionItem']")
                choice_elements = question_container.find_elements(By.XPATH, ".//input[@type='radio' or @type='checkbox']")      	

                for choice in choice_elements:
                    label = choice.get_attribute("aria-labelledby")
                    if label:
                        choice_label = driver.find_element(By.ID, label).text.strip()
                        if normalize(choice_label) in correct_answers:
                            choice.click()
                            found_answer = True
                
                break
        
        if not found_answer:
            print(f"⚠️ Không tìm thấy đáp án phù hợp cho câu: {question_text}")
    
    messagebox.showinfo("Hoàn thành", "Đã điền đáp án. Hãy kiểm tra lại trước khi nộp bài.")

# Giao diện người dùng
def browse_txt():
    file_path = filedialog.askopenfilename(filetypes=[["Text Files", "*.txt"]])
    txt_entry.delete(0, tk.END)
    txt_entry.insert(0, file_path)

def start_process():
    txt_path = txt_entry.get()
    form_url = url_entry.get()
    if not txt_path or not form_url:
        messagebox.showerror("Lỗi", "Vui lòng chọn file TXT và nhập link form")
        return
    auto_fill_form(txt_path, form_url)

# Tạo cửa sổ giao diện
tk_root = tk.Tk()
tk_root.title("Auto Fill Microsoft Forms")
tk.Label(tk_root, text="Chọn file TXT đáp án:").grid(row=0, column=0)
txt_entry = tk.Entry(tk_root, width=50)
txt_entry.grid(row=0, column=1)
tk.Button(tk_root, text="Chọn", command=browse_txt).grid(row=0, column=2)
tk.Label(tk_root, text="Nhập link Microsoft Forms:").grid(row=1, column=0)
url_entry = tk.Entry(tk_root, width=50)
url_entry.grid(row=1, column=1)
tk.Button(tk_root, text="Bắt đầu", command=start_process).grid(row=2, columnspan=3)
tk_root.mainloop()
