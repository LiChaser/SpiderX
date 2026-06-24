import os
import json
import threading
from datetime import datetime
import config
import classifier
import cracker_simple
import cracker_complex
from utils import logger, load_file

class LichAuto:
    def __init__(self):
        os.makedirs(config.LISTDIR_PATH, exist_ok=True)
        self._ensure_default_files()

    def _ensure_default_files(self):
        if not os.path.exists(config.USERNAME_FILE):
            with open(config.USERNAME_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(config.DEFAULT_USERNAMES) + '\n')
        if not os.path.exists(config.PASSWORD_FILE):
            with open(config.PASSWORD_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(config.DEFAULT_PASSWORDS) + '\n')

    def run(self, urls):
        if isinstance(urls, str):
            urls = [urls]
        
        logger.info(f"Starting LichAuto for {len(urls)} URLs...")
        
        with open(config.URL_LIST_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(urls) + '\n')
        
        logger.info("Step 1: Classifying targets...")
        classifier.STOP_FLAG = False
        classify_result = classifier.classify_targets()
        
        all_results = []
        
        simple_targets = classify_result.get("simple", [])
        if simple_targets:
            logger.info(f"Step 2: Running simple crack for {len(simple_targets)} targets...")
            cracker_simple.STOP_FLAG = False
            simple_results = cracker_simple.run_simple_crack()
            all_results.extend(simple_results)
        
        complex_targets = classify_result.get("complex", [])
        if complex_targets:
            logger.info(f"Step 3: Running complex crack for {len(complex_targets)} targets...")
            cracker_complex.STOP_FLAG = False
            complex_results = cracker_complex.run_complex_crack()
            all_results.extend(complex_results)
        
        logger.info(f"Done! Found {len(all_results)} valid credentials.")
        
        return {
            "success": True,
            "classification": classify_result,
            "results": all_results,
            "count": len(all_results)
        }

    def get_results(self):
        results = []
        if os.path.exists(config.RESULTS_FILE):
            with open(config.RESULTS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 2:
                            url = parts[0].strip()
                            cred = parts[1].strip()
                            if ':' in cred:
                                username, password = cred.split(':', 1)
                                results.append({
                                    "url": url,
                                    "username": username,
                                    "password": password
                                })
        return {"results": results, "count": len(results)}

    def clear_results(self):
        if os.path.exists(config.RESULTS_FILE):
            os.remove(config.RESULTS_FILE)
        logger.info("Results cleared")
        return {"success": True}

    def stop(self):
        classifier.STOP_FLAG = True
        cracker_simple.STOP_FLAG = True
        cracker_complex.STOP_FLAG = True
        logger.info("Stop signal sent")
        return {"success": True}

def auto_crack(url):
    lich = LichAuto()
    return lich.run(url)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = auto_crack(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python lichauto.py <url>")
