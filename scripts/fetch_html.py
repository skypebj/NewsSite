import os
import requests
from common import URLS, HEADERS, get_timestamp

def save_html(content, source_name):
    output_dir = 'docs/html'
    os.makedirs(output_dir, exist_ok=True)
    timestamp = get_timestamp()
    filename = f"{source_name}_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def main():
    print("=== 下载HTML源码 ===")
    for name, url in URLS.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            filepath = save_html(resp.text, name)
            print(f"✅ {name} 源码保存至 {filepath}")
        except Exception as e:
            print(f"❌ {name} 下载失败: {e}")
            # 记录失败状态（由外层脚本统一处理）

if __name__ == '__main__':
    main()
