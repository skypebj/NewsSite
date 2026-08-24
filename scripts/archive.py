import os
import zipfile
from datetime import datetime, timedelta
import re

def archive_previous_month():
    now = datetime.utcnow()
    if now.day != 1:
        print("不是本月第一天，跳过归档")
        return
    first_day = now.replace(day=1)
    last_month = first_day - timedelta(days=1)
    year_month = last_month.strftime('%Y%m')
    screenshot_dir = 'docs/screenshots'
    archive_dir = 'docs/archives'
    if not os.path.exists(screenshot_dir):
        print("截图目录不存在")
        return
    files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    pattern = re.compile(r'^(\w+)_(\d{8})_(\d{6})\.png$')
    archive_files = []
    for f in files:
        match = pattern.match(f)
        if match and match.group(2).startswith(year_month):
            archive_files.append(f)
    if not archive_files:
        print(f"没有找到 {year_month} 的截图")
        return
    os.makedirs(archive_dir, exist_ok=True)
    zip_path = os.path.join(archive_dir, f"{year_month}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in archive_files:
            file_path = os.path.join(screenshot_dir, f)
            zipf.write(file_path, f)
            os.remove(file_path)
    print(f"✅ 已归档 {len(archive_files)} 个文件到 {zip_path}")

if __name__ == '__main__':
    archive_previous_month()
