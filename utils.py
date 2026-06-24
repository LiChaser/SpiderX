import logging
import queue
import logging.handlers
import threading

log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put(msg)
            if log_queue.qsize() > 1000:
                try:
                    log_queue.get_nowait()
                except queue.Empty:
                    pass
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LichAutoAPI')

queue_handler = QueueHandler()
queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(queue_handler)

ocr_engine = None
ocr_lock = threading.Lock()

def init_ocr():
    global ocr_engine
    if ocr_engine is None:
        with ocr_lock:
            if ocr_engine is None:
                try:
                    import ddddocr
                    ocr_engine = ddddocr.DdddOcr(show_ad=False)
                    logger.info("OCR engine initialized")
                except Exception as e:
                    logger.error(f"OCR engine init failed: {e}")

def get_ocr_result(image_bytes):
    global ocr_engine
    if not ocr_engine:
        init_ocr()
    if not ocr_engine:
        return ""
    try:
        res = ocr_engine.classification(image_bytes)
        logger.info(f"OCR result: {res}")
        return res
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

def load_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return []
