# -*- coding: utf-8 -*-
"""
@Toolsname: SpiderX
@Author  : LiChaser
@Time    : 2025-01-25
@Version : 1.0
@Description:
    - 这是一个基于 Selenium 的自动化脚本。
    - 功能包括：登录、验证码识别、数据抓取等。
    - 使用了 ddddocr 进行验证码识别。
"""
import concurrent.futures
import logging
import os
import threading
import tkinter as tk
import time
import sys
import customtkinter as ctk
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ddddocr
import requests
import base64
from io import BytesIO
from PIL import Image

# 配置界面主题和图标
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# 在文件开头添加计数器类
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._value += 1
            return self._value

    def get_value(self):
        with self._lock:
            return self._value

    def reset(self):
        with self._lock:
            self._value = 0

# 修改全局变量声明
numbers = ThreadSafeCounter()
PWD = ''
USER = ''
usernames = []
passwords = []

# 在 DEFAULT_CONFIG 中添加验证码相关配置
DEFAULT_CONFIG = {
    "url": "http://127.0.0.1:5000/",
    "name_xpath": '//*[@id="username"]',
    "pass_xpath": '//*[@id="password"]',
    "btn_xpath": '/html/body/form/div[4]/button',
    "success_xpath": '//*[contains(text(),"欢迎")]',  # 新增成功检测元素
    "user_file": "username.txt",
    "pass_file": "password.txt",
    "threads": 2,               # 根据CPU核心数优化
    "headless": True,
    "timeout": 5,               # 延长超时时间
    "max_retries": 3,           # 最大重试次数
    "min_delay": 0.5,           # 最小延迟（秒）
    "max_delay": 1.5,            # 最大延迟（秒）
    "captcha_xpath": '/html/body/form/div[3]/img',  # 验证码图片元素
    "captcha_input_xpath": '//*[@id="captcha"]',  # 验证码输入框
    "captcha_refresh_xpath": '/html/body/form/div[3]/img',  # 验证码刷新按钮（如果有）
    "has_captcha": True,  # 是否启用验证码识别
    "captcha_retry_limit": 3,  # 验证码识别重试次数
    "captcha_timeout": 1,  # 验证码加载超时时间
}

class CaptchaHandler:
    def __init__(self):
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.retry_count = 0
        self.last_captcha = None
        self._lock = threading.Lock()

    def recognize_captcha(self, image_data):
        """识别验证码"""
        with self._lock:
            try:
                # 确保图片数据是字节格式
                if isinstance(image_data, str):
                    if image_data.startswith('data:image'):
                        image_data = base64.b64decode(image_data.split(',')[1])
                    else:
                        # 假设是base64字符串
                        try:
                            image_data = base64.b64decode(image_data)
                        except:
                            raise Exception("Invalid image data format")

                # 使用PIL处理图片
                image = Image.open(BytesIO(image_data))
                
                # 转换为RGB模式（如果需要）
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # 调整图片大小（如果需要）
                # image = image.resize((100, 30), Image.LANCZOS)
                
                # 转回字节流
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                image_bytes = buffered.getvalue()

                # 识别验证码
                result = self.ocr.classification(image_bytes)
                
                # 清理结果
                result = result.strip()
                if not result:
                    raise Exception("OCR result is empty")

                self.last_captcha = result
                return result
            except Exception as e:
                logging.error(f"验证码识别失败: {str(e)}")
                return None

    def verify_captcha(self, driver, captcha_code):
        """验证验证码是否正确"""
        try:
            # 这里添加验证码验证逻辑
            # 可以根据实际情况判断验证码是否正确
            return True
        except Exception as e:
            logging.error(f"验证码验证失败: {str(e)}")
            return False

class LoginGUI(ctk.CTk):
    def __init__(self):
        try:
            super().__init__()
            self.title("Licharsec - SpiderX Pro v1.0")
            self.geometry("1200x800")
            self._create_widgets()
            self._load_default_files()
            self.running = False
            self.executor = None
            self.captcha_handler = CaptchaHandler()

            # 添加全局异常处理
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # 添加错误统计计数器
            self.error_counter = {
                'network_errors': 0,    # 网络错误
                'xpath_errors': 0,      # 元素定位错误
                'captcha_errors': 0,    # 验证码错误
                'browser_errors': 0,    # 浏览器错误
                'other_errors': 0       # 其他错误
            }
            
            # 添加日志记录器
            self.setup_logger()
            
        except Exception as e:
            self.show_error_dialog(
                "❌ 程序错误",
                "程序初始化失败",
                f"错误信息：{str(e)}"
            )
            sys.exit(1)

    def _create_widgets(self):
        # 主界面布局配置
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ========== 左侧配置面板 ==========
        self.config_frame = ctk.CTkFrame(self, width=320, corner_radius=10)
        self.config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        self.config_frame.grid_propagate(False)
        self.config_frame.grid_columnconfigure(0, weight=1)

        # 配置项控件初始化
        self.url_entry = ctk.CTkEntry(self.config_frame)
        self.name_xpath_entry = ctk.CTkEntry(self.config_frame)
        self.pass_xpath_entry = ctk.CTkEntry(self.config_frame)
        self.btn_xpath_entry = ctk.CTkEntry(self.config_frame)

        # 动态创建配置项
        config_items = [
            ("目标URL:", self.url_entry, DEFAULT_CONFIG["url"]),
            ("用户名XPath:", self.name_xpath_entry, DEFAULT_CONFIG["name_xpath"]),
            ("密码XPath:", self.pass_xpath_entry, DEFAULT_CONFIG["pass_xpath"]),
            ("按钮XPath:", self.btn_xpath_entry, DEFAULT_CONFIG["btn_xpath"])
        ]

        current_row = 0
        for label_text, entry_widget, default_value in config_items:
            ctk.CTkLabel(
                self.config_frame,
                text=label_text,
                font=("Helvetica", 23),
                anchor="w"
            ).grid(row=current_row, column=0, padx=10, pady=(10, 0), sticky="we")

            entry_widget.delete(0, "end")
            entry_widget.insert(0, default_value)
            entry_widget.grid(row=current_row + 1, column=0, padx=10, pady=(0, 10), sticky="we")
            
            current_row += 2

        # 修改验证码配置区域
        self.captcha_frame = ctk.CTkFrame(self.config_frame)
        self.captcha_frame.grid(row=current_row, column=0, pady=10, padx=10, sticky="we")
        self.captcha_frame.grid_columnconfigure(0, weight=1)

        # 验证码标题
        ctk.CTkLabel(
            self.captcha_frame,
            text="验证码配置",
            font=("Helvetica", 23),
            anchor="w"
        ).grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        # 验证码选项子框架
        captcha_options = ctk.CTkFrame(self.captcha_frame, fg_color="transparent")
        captcha_options.grid(row=1, column=0, padx=10, pady=10, sticky="we")
        captcha_options.grid_columnconfigure(0, weight=1)

        # 启用验证码复选框
        self.captcha_enabled = ctk.CTkCheckBox(
            captcha_options,
            text="启用验证码识别",
            command=self.toggle_captcha,
            variable=ctk.BooleanVar(value=DEFAULT_CONFIG["has_captcha"]),
            font=("Helvetica", 16)
        )
        self.captcha_enabled.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # 验证码XPath输入框
        ctk.CTkLabel(
            captcha_options,
            text="验证码图片XPath:",
            font=("Helvetica", 16),
            anchor="w"
        ).grid(row=1, column=0, padx=5, pady=(10, 0), sticky="w")

        self.captcha_xpath_entry = ctk.CTkEntry(captcha_options)
        self.captcha_xpath_entry.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="we")
        self.captcha_xpath_entry.insert(0, DEFAULT_CONFIG["captcha_xpath"])

        # 验证码输入框XPath
        ctk.CTkLabel(
            captcha_options,
            text="验证码输入框XPath:",
            font=("Helvetica", 16),
            anchor="w"
        ).grid(row=3, column=0, padx=5, pady=(10, 0), sticky="w")

        self.captcha_input_xpath_entry = ctk.CTkEntry(captcha_options)
        self.captcha_input_xpath_entry.grid(row=4, column=0, padx=5, pady=(0, 5), sticky="we")
        self.captcha_input_xpath_entry.insert(0, DEFAULT_CONFIG["captcha_input_xpath"])

        # 验证码刷新按钮XPath
        ctk.CTkLabel(
            captcha_options,
            text="验证码刷新按钮XPath:",
            font=("Helvetica", 16),
            anchor="w"
        ).grid(row=5, column=0, padx=5, pady=(10, 0), sticky="w")

        self.captcha_refresh_xpath_entry = ctk.CTkEntry(captcha_options)
        self.captcha_refresh_xpath_entry.grid(row=6, column=0, padx=5, pady=(0, 5), sticky="we")
        self.captcha_refresh_xpath_entry.insert(0, DEFAULT_CONFIG["captcha_refresh_xpath"])

        current_row += 1

        # ========== 文件选择区域 ==========
        self.file_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.file_frame.grid(row=current_row + 1, column=0, pady=10, sticky="we")
        self.file_frame.grid_columnconfigure((0, 1), weight=1)

        self.user_file_btn = ctk.CTkButton(
            self.file_frame,
            text="选择用户名字典",
            command=lambda: self.select_file("username")
        )
        self.user_file_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.pass_file_btn = ctk.CTkButton(
            self.file_frame,
            text="选择密码字典",
            command=lambda: self.select_file("password")
        )
        self.pass_file_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # ========== 控制按钮 ==========
        self.control_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.control_frame.grid(row=current_row + 2, column=0, pady=10, sticky="we")
        self.control_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_btn = ctk.CTkButton(
            self.control_frame,
            text="▶ 开始扫描",
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self.start_scan
        )
        self.start_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.stop_btn = ctk.CTkButton(
            self.control_frame,
            text="⏹ 停止扫描",
            fg_color="#f44336",
            hover_color="#da190b",
            state="disabled",
            command=self.stop_scan
        )
        self.stop_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # ========== 右侧显示面板 ==========
        self.display_frame = ctk.CTkFrame(self, corner_radius=10)
        self.display_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.display_frame.grid_columnconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(1, weight=1)

        # 状态栏
        self.status_bar = ctk.CTkFrame(self.display_frame, height=40)
        self.status_bar.grid(row=0, column=0, sticky="we", padx=10, pady=10)
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="🟢 就绪",
            font=("Helvetica", 14)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10)

        self.progress_label = ctk.CTkLabel(
            self.status_bar,
            text="尝试次数: 0",
            font=("Helvetica", 12)
        )
        self.progress_label.grid(row=0, column=1, sticky="e", padx=10)

        # 添加错误统计显示
        self.error_stats_label = ctk.CTkLabel(
            self.status_bar,
            text="错误统计: 0",
            font=("Helvetica", 12)
        )
        self.error_stats_label.grid(row=0, column=2, sticky="e", padx=10)

        # 添加公众号图标
        self.qr_frame = ctk.CTkFrame(
            self.status_bar, 
            width=30, 
            height=30,
            fg_color="transparent"
        )
        self.qr_frame.grid(row=0, column=3, padx=(10, 5))
        
        # 创建小图标标签
        self.info_label = ctk.CTkLabel(
            self.qr_frame,
            text="ℹ️",
            font=("Arial", 16),
            text_color="#4a9eff",
            cursor="hand2"
        )
        self.info_label.pack(padx=5, pady=5)
        
        # 初始化变量
        self.qr_window = None
        
        # 绑定点击事件（改用点击而不是悬停）
        self.info_label.bind("<Button-1>", self.toggle_qr_code)

        # 日志区域
        self.log_area = ctk.CTkTextbox(
            self.display_frame,
            wrap="word",
            font=("Consolas", 10),
            scrollbar_button_color="#4a4a4a"
        )
        self.log_area.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # 日志工具栏
        self.log_tools = ctk.CTkFrame(self.display_frame, height=30, fg_color="transparent")
        self.log_tools.grid(row=2, column=0, sticky="we", padx=10)

        self.clear_log_btn = ctk.CTkButton(
            self.log_tools,
            text="清空日志",
            width=80,
            command=self.clear_log
        )
        self.clear_log_btn.pack(side="right", padx=5)

    def _load_default_files(self):
        """安全加载默认字典文件"""

        def load_file(file_type, file_path):
            try:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding='utf-8') as f:
                        content = f.read().splitlines()
                    self.after(0, self._show_info, f"已加载{file_type}字典: {file_path} ({len(content)}条)")
                    return content
                else:
                    self.after(0, self._show_warning, f"默认{file_type}字典不存在: {file_path}")
            except Exception as e:
                self.after(0, self._show_error, f"加载{file_type}字典失败: {str(e)}")
            return []

        global usernames, passwords
        usernames = load_file("用户名", DEFAULT_CONFIG["user_file"])
        passwords = load_file("密码", DEFAULT_CONFIG["pass_file"])

    def _show_info(self, message):
        """线程安全的日志信息显示"""
        if hasattr(self, 'log_area'):
            self.log_area.configure(state="normal")
            self.log_area.insert("end", f"[INFO] {message}\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

    def _show_warning(self, message):
        if hasattr(self, 'log_area'):
            self.log_area.configure(state="normal")
            self.log_area.insert("end", f"[WARN] {message}\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

    def _show_error(self, message):
        if hasattr(self, 'log_area'):
            self.log_area.configure(state="normal")
            self.log_area.insert("end", f"[ERROR] {message}\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

    def select_file(self, file_type):
        filename = tk.filedialog.askopenfilename(
            title=f"选择{file_type}文件",
            filetypes=(("文本文件", "*.txt"),)
        )
        if filename:
            try:
                with open(filename, "r", encoding='utf-8') as f:
                    content = f.read().splitlines()
                if file_type == "username":
                    global usernames
                    usernames = content
                else:
                    global passwords
                    passwords = content
                self._show_info(f"已加载 {file_type} 文件: {filename} ({len(content)}条)")
            except Exception as e:
                self._show_error(f"文件加载失败: {str(e)}")

    def clear_log(self):
        if hasattr(self, 'log_area'):
            self.log_area.configure(state="normal")
            self.log_area.delete("1.0", "end")
            self.log_area.configure(state="disabled")

    def start_scan(self):
        if not self.running:
            self.running = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_label.configure(text="🔴 扫描进行中", text_color="#ff4444")

            url = self.url_entry.get()
            name_elem = self.name_xpath_entry.get()
            pass_elem = self.pass_xpath_entry.get()
            btn_elem = self.btn_xpath_entry.get()

            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=DEFAULT_CONFIG["threads"])
            self.future = self.executor.submit(
                self.start_attack,
                url,
                name_elem,
                pass_elem,
                btn_elem
            )

    def stop_scan(self):
        if self.running:
            self.running = False
            self.executor.shutdown(wait=False)
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_label.configure(text="🟡 已停止", text_color="#ffd700")
            self._show_info("扫描已手动终止")
            numbers.reset()  # 重置计数器

    def start_attack(self, url, name_elem, pass_elem, btn_elem):
        global USER, PWD
        start_time = time.time()
        login_success = False
        num_threads = DEFAULT_CONFIG["threads"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            for username in usernames:
                if not self.running or login_success:
                    break

                # 分割密码列表
                password_chunks = self.chunk_list(passwords, num_threads)

                # 为当前用户提交多个任务
                futures = [
                    executor.submit(
                        self.process_password_chunk,
                        username,
                        chunk,
                        url,
                        name_elem,
                        pass_elem,
                        btn_elem
                    ) for chunk in password_chunks
                ]

                try:
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result:
                            USER, PWD = result
                            login_success = True
                            # 取消其他任务
                            for f in futures:
                                f.cancel()
                            break
                except concurrent.futures.CancelledError:
                    pass

                if login_success:
                    break

        end_time = time.time()
        self._show_info(f"总耗时: {end_time - start_time:.2f} 秒")

        if login_success:
            self._show_info(f"✅ 登录成功! 用户名: {USER} 密码: {PWD}")
            self.after(0, self.show_success_alert)
        else:
            self._show_info("❌ 所有组合尝试完毕，未找到有效凭证")

    @staticmethod
    def chunk_list(lst, n):
        """将列表分割为n个近似相等的块"""
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

    def process_password_chunk(self, username, password_chunk, url, name_elem, pass_elem, btn_elem):
        driver = None
        try:
            # 优化浏览器配置
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")  # 使用新版无头模式
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-site-isolation-trials")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-features=GlobalMediaControls")
            options.add_argument("--disable-features=AutofillServerCommunication")
            options.add_argument("--disable-features=OptimizationHints")
            options.add_argument("--disable-features=NetworkService")
            options.add_argument("--disable-features=NetworkServiceInProcess")
            options.add_argument("--disable-features=Translate")
            options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
            options.add_argument("--disable-features=MediaRouter")
            options.add_argument("--disable-features=WebUIDarkMode")
            options.add_argument("--disable-features=WebContentsForceDark")
            options.add_argument("--disable-features=AutofillEnableAccountWalletStorage")
            options.add_argument("--disable-features=AutofillServerCommunication")
            options.add_argument("--disable-features=AutofillShowTypePredictions")
            options.add_argument("--disable-features=AutofillShowManualFallbackInSidebar")
            options.add_argument("--disable-features=AutofillShowTypePredictions")
            options.add_argument("--disable-features=AutofillShowManualFallbackInSidebar")
            options.add_argument("--disable-features=AutofillShowTypePredictions")
            options.add_argument("--disable-features=AutofillShowManualFallbackInSidebar")
            options.add_argument("--disable-features=AutofillShowTypePredictions")
            options.add_argument("--disable-features=AutofillShowManualFallbackInSidebar")
            options.add_argument("--disable-features=AutofillShowTypePredictions")
            options.add_argument("--disable-features=AutofillShowManualFallbackInSidebar")
            
            # 性能优化参数
            options.add_argument("--js-flags=--expose-gc")
            options.add_argument("--enable-precise-memory-info")
            options.add_argument("--disable-javascript")
            options.add_argument("--disable-images")
            options.add_argument("--disable-css")
            options.add_argument("--disable-animations")
            options.add_argument("--disable-webgl")
            options.add_argument("--disk-cache-size=1")
            options.add_argument("--media-cache-size=1")
            options.add_argument("--disk-cache-dir=/dev/null")
            options.add_argument("--aggressive-cache-discard")
            options.add_argument("--disable-application-cache")
            
            # 内存优化
            options.add_argument("--memory-pressure-off")
            options.add_argument("--no-zygote")
            options.add_argument("--single-process")
            options.add_argument("--process-per-site")
            options.add_argument("--renderer-process-limit=1")
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)

            # 预加载元素定位
            try:
                username_field = driver.find_element(By.XPATH, name_elem)
                password_field = driver.find_element(By.XPATH, pass_elem)
                submit_btn = driver.find_element(By.XPATH, btn_elem)
            except NoSuchElementException as e:
                self.log_error('xpath_errors', f"元素未找到: {str(e)}")
                return None

            for password in password_chunk:
                if not self.running:
                    break

                try:
                    current_count = numbers.increment()
                    self.after(0, self._update_progress, current_count)

                    # 处理验证码
                    if DEFAULT_CONFIG["has_captcha"]:
                        captcha_success = self.handle_captcha(driver)
                        if not captcha_success:
                            continue

                    # 填充表单
                    driver.execute_script("arguments[0].value = '';", username_field)
                    driver.execute_script("arguments[0].value = '';", password_field)
                    driver.execute_script(f"arguments[0].value = '{username}';", username_field)
                    driver.execute_script(f"arguments[0].value = '{password}';", password_field)
                    
                    driver.execute_script("arguments[0].click();", submit_btn)

                    # 优化登录检测
                    try:
                        if self.check_login_success(driver):
                            self.after(0, self._show_info, f"尝试[{current_count}] 用户:{username} 密码:{password} 成功!!!")
                            self.stop_scan()
                            return (username, password)
                        else:
                            self.after(0, self._show_info, f"尝试[{current_count}] 用户:{username} 密码:{password} 错误")
                    except Exception as e:
                        continue

                    # 使用JavaScript重新加载页面（更快）
                    driver.execute_script("window.location.href = arguments[0];", url)
                    
                    # 重新获取元素（使用缓存的定位器）
                    try:
                        username_field = driver.find_element(By.XPATH, name_elem)
                        password_field = driver.find_element(By.XPATH, pass_elem)
                        submit_btn = driver.find_element(By.XPATH, btn_elem)
                    except TimeoutException as e:
                        self.log_error('network_errors', f"网络超时: {str(e)}")
                        driver.execute_script("window.location.reload();")
                        username_field = driver.find_element(By.XPATH, name_elem)
                        password_field = driver.find_element(By.XPATH, pass_elem)
                        submit_btn = driver.find_element(By.XPATH, btn_elem)

                except Exception as e:
                    # 发生异常时进行恢复
                    try:
                        driver.execute_script("window.location.reload();")
                        username_field = driver.find_element(By.XPATH, name_elem)
                        password_field = driver.find_element(By.XPATH, pass_elem)
                        submit_btn = driver.find_element(By.XPATH, btn_elem)
                    except:
                        # 如果恢复失败，重新创建driver
                        if driver:
                            driver.quit()
                        driver = webdriver.Chrome(options=options)
                        driver.get(url)
                        username_field = driver.find_element(By.XPATH, name_elem)
                        password_field = driver.find_element(By.XPATH, pass_elem)
                        submit_btn = driver.find_element(By.XPATH, btn_elem)
                    continue

        except NoSuchElementException as e:
            self.log_error('xpath_errors', f"元素未找到: {str(e)}")
        except TimeoutException as e:
            self.log_error('network_errors', f"网络超时: {str(e)}")
        except WebDriverException as e:
            self.log_error('browser_errors', f"浏览器错误: {str(e)}")
        except Exception as e:
            self.log_error('other_errors', f"未知错误: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        return None

    def check_login_success(self, driver):
        """优化的登录成功检测"""
        try:
            # 1. 检查URL变化
            current_url = driver.current_url.lower()
            if 'login' not in current_url and 'index' in current_url:
                return True

            # 2. 检查常见的成功标识
            success_indicators = [
                "//div[contains(text(),'欢迎')]",
                "//span[contains(text(),'欢迎')]",
                "//div[contains(text(),'成功')]",
                "//div[contains(text(),'登录成功')]",
                "//div[contains(@class,'success')]",
                "//div[contains(@class,'welcome')]",
                DEFAULT_CONFIG["success_xpath"]  # 用户自定义的成功标识
            ]

            for xpath in success_indicators:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        return True
                except:
                    continue

            # 3. 检查登录表单是否消失（使用配置的密码输入框XPath）
            try:
                password_field = driver.find_element(By.XPATH, DEFAULT_CONFIG["pass_xpath"])
                if not password_field.is_displayed():
                    return True
            except NoSuchElementException:
                # 如果找不到密码输入框，可能已经登录成功
                return True
            except:
                pass

            # 4. 检查是否存在登出按钮
            logout_indicators = [
                "//a[contains(text(),'退出')]",
                "//a[contains(text(),'注销')]",
                "//button[contains(text(),'退出')]",
                "//button[contains(text(),'注销')]",
                "//a[contains(@href,'logout')]",
                "//a[contains(@href,'signout')]"
            ]

            for xpath in logout_indicators:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        return True
                except:
                    continue

            # 5. 检查错误提示是否存在
            error_indicators = [
                "//div[contains(text(),'密码错误')]",
                "//div[contains(text(),'登录失败')]",
                "//div[contains(@class,'error')]",
                "//span[contains(text(),'错误')]",
                "//p[contains(text(),'失败')]"
            ]

            for xpath in error_indicators:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        return False
                except:
                    continue

            return False

        except Exception as e:
            self._show_error(f"登录检测异常: {str(e)}")
            return False

    def _update_progress(self, count):
        self.progress_label.configure(text=f"尝试次数: {count}")

    def show_success_alert(self):
        """美观的成功提示弹窗"""
        success_win = ctk.CTkToplevel(self)
        success_win.title("🎉 登录成功")
        success_win.geometry("400x250")

        # 主容器
        main_frame = ctk.CTkFrame(success_win, corner_radius=15)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # 图标部分
        icon_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        icon_frame.pack(pady=(15, 10))
        ctk.CTkLabel(
            icon_frame,
            text="✅",
            font=("Arial", 32),
            text_color="#4CAF50"
        ).pack()

        # 信息部分
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(pady=10)

        ctk.CTkLabel(
            info_frame,
            text="发现有效凭证",
            font=("Microsoft YaHei", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=5)

        info_text = f"用户名：{USER}\n密码：{PWD}"
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Consolas", 14),
            justify="left"
        ).pack(pady=10)

        # 操作按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 15))

        ctk.CTkButton(
            btn_frame,
            text="确 定",
            width=100,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=("Microsoft YaHei", 12),
            command=success_win.destroy
        ).pack()

        # 窗口设置
        success_win.resizable(False, False)
        success_win.grab_set()  # 保持窗口置顶
        self.stop_scan()

    def handle_captcha(self, driver):
        """处理验证码识别流程"""
        retry_count = 0
        while retry_count < DEFAULT_CONFIG["captcha_retry_limit"]:
            try:
                # 等待验证码图片加载
                captcha_img = WebDriverWait(driver, DEFAULT_CONFIG["captcha_timeout"]).until(EC.presence_of_element_located((By.XPATH, DEFAULT_CONFIG["captcha_xpath"])))
                
                # 确保验证码图片完全加载
                time.sleep(0.5)
                
                # 获取验证码图片
                try:
                    # 获取图片URL
                    img_url = captcha_img.get_attribute('src')
                    if not img_url:
                        raise Exception("No image source found")

                    # 检查是否是动态验证码URL（包含时间戳或随机数）
                    if '?' in img_url or 'timestamp' in img_url or 'random' in img_url:
                        # 使用requests直接获取图片内容
                        response = requests.get(img_url, timeout=3)
                        image_data = response.content
                    else:
                        # 使用Selenium截图方式
                        image_data = captcha_img.screenshot_as_png

                except Exception as e:
                    self._show_error(f"获取验证码图片失败: {str(e)}")
                    # 尝试使用Canvas方式
                    try:
                        canvas_data = driver.execute_script("""
                            var canvas = document.createElement('canvas');
                            var context = canvas.getContext('2d');
                            var img = arguments[0];
                            canvas.width = img.naturalWidth || img.width;
                            canvas.height = img.naturalHeight || img.height;
                            context.drawImage(img, 0, 0);
                            return canvas.toDataURL('image/png').substring(22);
                        """, captcha_img)
                        image_data = base64.b64decode(canvas_data)
                    except:
                        retry_count += 1
                        continue

                # 识别验证码
                try:
                    captcha_text = self.captcha_handler.recognize_captcha(image_data)
                    if not captcha_text or len(captcha_text.strip()) == 0:
                        raise Exception("验证码识别结果为空")
                    
                    #self._show_info(f"验证码识别结果: {captcha_text}")

                    # 查找并填写验证码输入框
                    captcha_input = WebDriverWait(driver, 0.5).until(
                        EC.presence_of_element_located((By.XPATH, DEFAULT_CONFIG["captcha_input_xpath"]))
                    )

                    # 清空并填写验证码
                    driver.execute_script("""
                        arguments[0].value = '';
                        arguments[0].value = arguments[1];
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """, captcha_input, captcha_text)

                    # 等待一小段时间确保验证码已填写
                    time.sleep(0.2)
                    
                    # 验证验证码是否填写成功
                    actual_value = driver.execute_script("return arguments[0].value;", captcha_input)
                    if actual_value != captcha_text:
                        raise Exception("验证码填写验证失败")

                    return True

                except Exception as e:
                    retry_count += 1
                    self._show_warning(f"验证码处理失败: {str(e)}，正在重试 ({retry_count}/{DEFAULT_CONFIG['captcha_retry_limit']})")
                    
                    # 尝试刷新验证码
                    try:
                        refresh_btn = driver.find_element(By.XPATH, DEFAULT_CONFIG["captcha_refresh_xpath"])
                        driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(0.5)  # 等待新验证码加载
                    except:
                        try:
                            # 如果没有刷新按钮，尝试点击验证码图片本身
                            driver.execute_script("arguments[0].click();", captcha_img)
                            time.sleep(0.5)
                        except:
                            # 如果点击失败，刷新整个页面
                            driver.refresh()
                            time.sleep(1)
                    continue

            except Exception as e:
                retry_count += 1
                self.show_error(f"{captcha_text}")
                self._show_error(f"验证码处理失败")
                if retry_count >= DEFAULT_CONFIG["captcha_retry_limit"]:
                    return False
                
                try:
                    driver.refresh()
                    time.sleep(1)
                except:
                    pass

        return False

    def toggle_captcha(self):
        """切换验证码识别功能"""
        DEFAULT_CONFIG["has_captcha"] = self.captcha_enabled.get()
        # 更新配置
        DEFAULT_CONFIG["captcha_xpath"] = self.captcha_xpath_entry.get()
        DEFAULT_CONFIG["captcha_input_xpath"] = self.captcha_input_xpath_entry.get()
        DEFAULT_CONFIG["captcha_refresh_xpath"] = self.captcha_refresh_xpath_entry.get()
        
        if DEFAULT_CONFIG["has_captcha"]:
            self._show_info("已启用验证码识别")
        else:
            self._show_info("已禁用验证码识别")

    def show_error_dialog(self, title, error_type, error_msg):
        """显示错误弹窗"""
        error_win = ctk.CTkToplevel(self)
        error_win.title(title)
        error_win.geometry("400x200")
        
        # 主容器
        main_frame = ctk.CTkFrame(error_win, corner_radius=15)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # 错误图标
        icon_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        icon_frame.pack(pady=(15, 10))
        ctk.CTkLabel(
            icon_frame,
            text="❌",
            font=("Arial", 32),
            text_color="#f44336"
        ).pack()
        
        # 错误信息
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=error_type,
            font=("Microsoft YaHei", 18, "bold"),
            text_color="#f44336"
        ).pack(pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text=error_msg,
            font=("Consolas", 12),
            justify="left",
            wraplength=300  # 文本自动换行
        ).pack(pady=10)
        
        # 确定按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 15))
        
        ctk.CTkButton(
            btn_frame,
            text="确 定",
            width=100,
            fg_color="#f44336",
            hover_color="#da190b",
            font=("Microsoft YaHei", 12),
            command=error_win.destroy
        ).pack()
        
        # 窗口设置
        error_win.resizable(False, False)
        error_win.grab_set()  # 模态窗口
        
        # 计算居中位置
        error_win.update_idletasks()  # 更新窗口大小
        width = error_win.winfo_width()
        height = error_win.winfo_height()
        x = (error_win.winfo_screenwidth() // 2) - (width // 2)
        y = (error_win.winfo_screenheight() // 2) - (height // 2)
        
        # 设置窗口位置
        error_win.geometry(f'+{x}+{y}')
        error_win.focus_force()  # 强制获取焦点

    def on_closing(self):
        """处理窗口关闭事件"""
        try:
            if self.running:
                self.stop_scan()
            if self.executor:
                self.executor.shutdown(wait=False)
            self.quit()
        except Exception as e:
            self.show_error_dialog(
                "❌ 程序错误",
                "程序关闭异常",
                f"错误信息：{str(e)}"
            )
            sys.exit(1)

    def setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        
        # 创建错误日志文件处理器
        error_handler = logging.FileHandler('error_logs.txt', encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(error_handler)

    def log_error(self, error_type, error_msg):
        """记录错误并更新计数"""
        try:
            # 更新错误计数
            if error_type in self.error_counter:
                self.error_counter[error_type] += 1
            
            # 记录错误日志
            self.logger.error(f"{error_type}: {error_msg}")
            
            # 更新界面显示
            self.update_error_stats()
        except Exception as e:
            print(f"日志记录失败: {str(e)}")

    def update_error_stats(self):
        """更新错误统计显示"""
        total_errors = sum(self.error_counter.values())
        total_attempts = numbers.get_value()
        
        if total_attempts > 0:
            error_rate = (total_errors / total_attempts) * 100
            stats_text = (
                f"错误统计:\n"
                f"网络错误: {self.error_counter['network_errors']}\n"
                f"元素定位错误: {self.error_counter['xpath_errors']}\n"
                f"验证码错误: {self.error_counter['captcha_errors']}\n"
                f"浏览器错误: {self.error_counter['browser_errors']}\n"
                f"其他错误: {self.error_counter['other_errors']}\n"
            )
            
            # 更新界面显示
            self.error_stats_label.configure(text=stats_text)

    def toggle_qr_code(self, event=None):
        """切换二维码显示状态"""
        if self.qr_window:
            self.hide_qr_code()
        else:
            self.show_qr_code()

    def show_qr_code(self):
        """显示二维码窗口"""
        try:
            if self.qr_window:
                return
            
            # 创建窗口
            self.qr_window = ctk.CTkToplevel(self)
            self.qr_window.title("扫码关注")
            self.qr_window.geometry("200x240")  # 先设置大小
            
            # 主框架
            main_frame = ctk.CTkFrame(self.qr_window, corner_radius=10)
            main_frame.pack(expand=True, fill="both", padx=5, pady=5)
            
            # 加载二维码图片
            qr_path = os.path.join("resources", "qrcode.jpg")
            if os.path.exists(qr_path):
                img = Image.open(qr_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                self.qr_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(180, 180)
                )
                
                ctk.CTkLabel(
                    main_frame,
                    image=self.qr_image,
                    text=""
                ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                main_frame,
                text="扫码关注公众号(感谢感谢🐟)",
                font=("Microsoft YaHei", 12)
            ).pack(pady=5)
            
            # 窗口设置
            self.qr_window.resizable(False, False)
            self.qr_window.transient(self)
            self.qr_window.grab_set()
            
            # 绑定关闭事件
            self.qr_window.protocol("WM_DELETE_WINDOW", self.hide_qr_code)
            
            # 计算居中位置
            self.qr_window.update_idletasks()  # 更新窗口大小
            window_width = self.qr_window.winfo_width()
            window_height = self.qr_window.winfo_height()
            
            # 获取主窗口位置和大小
            main_x = self.winfo_x()
            main_y = self.winfo_y()
            main_width = self.winfo_width()
            main_height = self.winfo_height()
            
            # 计算居中坐标
            x = main_x + (main_width - window_width) // 2
            y = main_y + (main_height - window_height) // 2
            
            # 设置窗口位置
            self.qr_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            print(f"显示二维码失败: {str(e)}")
            if self.qr_window:
                self.qr_window.destroy()
                self.qr_window = None

    def hide_qr_code(self):
        """隐藏二维码窗口"""
        try:
            if hasattr(self, 'qr_image'):
                del self.qr_image
            if self.qr_window:
                self.qr_window.destroy()
                self.qr_window = None
        except Exception as e:
            print(f"隐藏二维码失败: {str(e)}")

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        app = LoginGUI()
        # 设置图标
        app.mainloop()
    except Exception as e:
        # 创建一个基础的错误窗口，因为GUI可能还未初始化
        error_win = tk.Tk()
        error_win.title('SpiderX')  # 更改标题名字
        error_win.geometry('400x450')  
        error_win.iconbitmap('spider.ico') 
        error_win.withdraw()  # 隐藏主窗口
        tk.messagebox.showerror(
            "❌ 致命错误",
            f"程序发生致命错误：\n\n请检查程序环境或联系开发者。"
        )
        sys.exit(1)
