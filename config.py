import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LISTDIR_PATH = os.path.join(BASE_DIR, 'listdir')

URL_LIST_FILE = os.path.join(LISTDIR_PATH, 'url.txt')
SIMPLE_LIST_FILE = os.path.join(LISTDIR_PATH, 'simple_list.txt')
COMPLEX_LIST_FILE = os.path.join(LISTDIR_PATH, 'complex_list.txt')
UNKNOWN_LIST_FILE = os.path.join(LISTDIR_PATH, 'unknown_list.txt')
USERNAME_FILE = os.path.join(LISTDIR_PATH, 'usernames.txt')
PASSWORD_FILE = os.path.join(LISTDIR_PATH, 'passwords.txt')
RESULTS_FILE = os.path.join(BASE_DIR, 'results.txt')

DEFAULT_USERNAMES = ['admin', 'root', 'user', 'test']
DEFAULT_PASSWORDS = ['123456', 'password', 'admin123', '12345678']

ENCRYPTION_KEYWORDS = [
    'encrypt', 'rsa', 'aes', 'md5', 'crypto', 
    'security.js', 'jsencrypt', 'login.js'
]

TIMEOUT = 10
THREADS = 6

HEADLESS = True
FORCE_COMPLEX_MODE = False

STOP_ON_SUCCESS = True

ERROR_KEYWORDS = ['error', 'fail', 'incorrect', 'invalid', '重试', '错误', '失败', '账号', '密码', '密码错误', '登录失败']
SUCCESS_KEYWORDS = ['success', 'welcome', 'admin', 'dashboard', '成功', '欢迎', '退出', 'logout']
