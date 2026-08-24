import hashlib
import os
from datetime import datetime
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

URLS = {
    'bbc': 'https://www.bbc.com/news',
    'fox': 'https://www.foxnews.com/',
    'cnn': 'https://www.cnn.com/',
    'nytimes': 'https://www.nytimes.com/',
    'reuters': 'https://www.reuters.com/',
    'theguardian': 'https://www.theguardian.com/international',
    'washingtonpost': 'https://www.washingtonpost.com/',
    'nbcnews': 'https://www.nbcnews.com/',
    'apnews': 'https://apnews.com/'
}

def get_timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def get_date_str():
    return datetime.now().strftime('%Y%m%d')

def hash_text(text):
    """安全哈希，处理 None 和空字符串"""
    if text is None:
        text = ''
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def translate_text(text, src='en', dest='zh-cn'):
    """使用 googletrans 翻译，失败时返回原文"""
    if not text or not isinstance(text, str):
        return text
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src=src, dest=dest)
        return result.text
    except Exception:
        return text  # 回退原文

def load_state():
    state_path = 'docs/state.json'
    if os.path.exists(state_path):
        import json
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'last_run': None, 'last_date': None, 'failure_count': {}, 'seen_hashes': []}

def save_state(state):
    import json
    os.makedirs('docs', exist_ok=True)
    with open('docs/state.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
