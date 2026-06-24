import requests
from bs4 import BeautifulSoup
import config
from utils import logger
import urllib3
import concurrent.futures
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STOP_FLAG = False

def process_url(url, simple_list, complex_list, unknown_list):
    global STOP_FLAG
    if STOP_FLAG:
        return
    if not url.startswith('http'):
        url = 'http://' + url
    try:
        if config.FORCE_COMPLEX_MODE:
            logger.info(f"[Force Mode] Classify as complex: {url}")
            complex_list.append(url)
            return
        logger.info(f"Analyzing: {url}")
        resp = requests.get(url, timeout=config.TIMEOUT, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        password_input = soup.find('input', {'type': 'password'})
        if not password_input:
            logger.info(f"Classify as unknown: {url} (no password field)")
            unknown_list.append(f"{url} | No password field")
            return
        html_content = resp.text.lower()
        is_complex = False
        for keyword in config.ENCRYPTION_KEYWORDS:
            if keyword in html_content:
                is_complex = True
                logger.info(f"Found encryption feature [{keyword}]: {url}")
                break
        if not is_complex:
            images = soup.find_all('img')
            for img in images:
                src = img.get('src', '').lower()
                img_id = img.get('id', '').lower()
                img_class = img.get('class', [])
                if isinstance(img_class, list):
                    img_class = ' '.join(img_class).lower()
                img_alt = img.get('alt', '').lower()
                captcha_keywords = ["captcha", "code", "verify", "check", "yzm", "random"]
                if any(k in src for k in captcha_keywords) or \
                   any(k in img_id for k in captcha_keywords) or \
                   any(k in img_class for k in captcha_keywords) or \
                   any(k in img_alt for k in captcha_keywords):
                    is_complex = True
                    logger.info(f"Found captcha feature (img): {url}")
                    break
            if not is_complex:
                inputs = soup.find_all('input')
                for i in inputs:
                    name = i.get('name', '').lower()
                    i_id = i.get('id', '').lower()
                    placeholder = i.get('placeholder', '').lower()
                    captcha_keywords = ["captcha", "code", "verify", "yzm", "验证码"]
                    if any(k in name for k in captcha_keywords) or \
                       any(k in i_id for k in captcha_keywords) or \
                       any(k in placeholder for k in captcha_keywords):
                        is_complex = True
                        logger.info(f"Found captcha feature (input): {url}")
                        break
        if is_complex:
            complex_list.append(url)
        else:
            simple_list.append(url)
    except Exception as e:
        logger.error(f"Cannot access {url}: {e}")
        unknown_list.append(f"{url} | Access failed: {str(e)}")

def classify_targets(urls=None):
    global STOP_FLAG
    logger.info("Starting target classification...")
    if urls is None:
        try:
            with open(config.URL_LIST_FILE, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"URL list file not found: {config.URL_LIST_FILE}")
            return {"simple": [], "complex": [], "unknown": []}
    simple_list = []
    complex_list = []
    unknown_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.THREADS) as executor:
        futures = [executor.submit(process_url, url, simple_list, complex_list, unknown_list) for url in urls]
        concurrent.futures.wait(futures)
    os.makedirs(config.LISTDIR_PATH, exist_ok=True)
    with open(config.SIMPLE_LIST_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(simple_list))
    with open(config.COMPLEX_LIST_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(complex_list))
    with open(config.UNKNOWN_LIST_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unknown_list))
    logger.info(f"Classification complete! Simple: {len(simple_list)}, Complex: {len(complex_list)}, Unknown: {len(unknown_list)}")
    return {
        "simple": simple_list,
        "complex": complex_list,
        "unknown": unknown_list
    }

if __name__ == '__main__':
    classify_targets()
