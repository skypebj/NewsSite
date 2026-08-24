import os
import json
from datetime import datetime
from ebooklib import epub
from common import get_date_str

def generate_epub():
    date_str = get_date_str()
    json_path = f'docs/json/{date_str}.json'
    if not os.path.exists(json_path):
        print(f"❌ 没有找到 {date_str} 的JSON，跳过EPUB生成")
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    entries = data.get('entries', [])
    if not entries:
        print("没有数据，跳过EPUB")
        return
    book = epub.EpubBook()
    book.set_identifier(f'news_{date_str}')
    book.set_title(f'新闻汇总 {date_str}')
    book.set_language('zh')
    book.add_author('自动抓取')
    # 创建章节
    chapters = []
    for idx, entry in enumerate(entries[:50]):  # 限制条数
        title = entry.get('title', '无标题')
        title_zh = entry.get('title_zh', title)
        summary = entry.get('summary', '')
        summary_zh = entry.get('summary_zh', summary)
        content = f"""
        <h2>{title}</h2>
        <p><strong>英文标题：</strong>{title}</p>
        <p><strong>中文标题：</strong>{title_zh}</p>
        <p><strong>摘要原文：</strong>{summary}</p>
        <p><strong>摘要译文：</strong>{summary_zh}</p>
        <hr/>
        """
        c = epub.EpubHtml(title=f"第{idx+1}条", file_name=f'item_{idx}.xhtml', lang='zh')
        c.content = f"<html><body>{content}</body></html>"
        book.add_item(c)
        chapters.append(c)
    # 创建导航
    toc = [(epub.Link('nav.xhtml', '目录', 'nav'), chapters)]
    book.toc = toc
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    # 保存
    epub_dir = 'docs/epub'
    os.makedirs(epub_dir, exist_ok=True)
    epub_path = os.path.join(epub_dir, f'news_{date_str}.epub')
    epub.write_epub(epub_path, book)
    print(f"✅ EPUB 保存至 {epub_path}")

if __name__ == '__main__':
    generate_epub()
