import os
import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from common import URLS, get_date_str, hash_text, translate_text, load_state, save_state

# 提取器（仅列出 BBC 和 Fox，其他使用 generic）
def extract_bbc(html):
    soup = BeautifulSoup(html, 'lxml')
    articles = soup.select('div[data-testid="card-text-wrapper"]')
    results = []
    for art in articles[:20]:
        try:
            title_elem = art.select_one('h2[data-testid="card-headline"]')
            title = title_elem.get_text(strip=True) if title_elem else ''
            link_elem = art.select_one('a[data-testid="internal-link"]')
            link = link_elem.get('href') if link_elem else ''
            if link and not link.startswith('http'):
                link = 'https://www.bbc.com' + link
            summary_elem = art.select_one('p[data-testid="card-description"]')
            summary = summary_elem.get_text(strip=True) if summary_elem else ''
            time_elem = art.select_one('span[data-testid="card-metadata"]')
            published = time_elem.get_text(strip=True) if time_elem else ''
            results.append({'title': title, 'link': link, 'summary': summary, 'published': published})
        except:
            pass
    return results

def extract_fox(html):
    soup = BeautifulSoup(html, 'lxml')
    articles = soup.select('article')
    results = []
    for art in articles[:20]:
        try:
            title_elem = art.select_one('h2.title, h3.title, .title')
            title = title_elem.get_text(strip=True) if title_elem else ''
            link_elem = art.select_one('a[href*="/story/"], a[href*="/article/"]')
            link = ''
            if link_elem:
                link = link_elem.get('href') or ''
                if link and not link.startswith('http'):
                    link = 'https://www.foxnews.com' + link
            summary_elem = art.select_one('.dek, .description, .content p')
            summary = summary_elem.get_text(strip=True) if summary_elem else ''
            time_elem = art.select_one('.time, .timestamp, .date')
            published = time_elem.get_text(strip=True) if time_elem else ''
            results.append({'title': title, 'link': link, 'summary': summary, 'published': published})
        except:
            pass
    return results

def extract_generic(html):
    """通用提取：提取所有h1,h2,h3中的链接文本"""
    soup = BeautifulSoup(html, 'lxml')
    results = []
    for tag in soup.find_all(['h1', 'h2', 'h3']):
        link = tag.find('a')
        if link:
            title = tag.get_text(strip=True)
            href = link.get('href') or ''
            if href:
                if href.startswith('/'):
                    href = 'https://www.example.com' + href  # 占位，实际可能需补全
                results.append({'title': title, 'link': href, 'summary': '', 'published': ''})
    return results[:20]

EXTRACTORS = {
    'bbc': extract_bbc,
    'fox': extract_fox,
}

def main():
    state = load_state()
    date_str = get_date_str()
    seen_hashes = set(state.get('seen_hashes', []))
    all_entries = []
    site_stats = {}

    html_dir = 'docs/html'
    json_dir = 'docs/json'
    os.makedirs(json_dir, exist_ok=True)

    for filename in os.listdir(html_dir):
        if not filename.endswith('.html'):
            continue
        parts = filename.split('_')
        if len(parts) < 3:
            continue
        site = parts[0]
        html_path = os.path.join(html_dir, filename)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        extractor = EXTRACTORS.get(site, extract_generic)
        try:
            entries = extractor(html_content)
            print(f"{site}: 提取到 {len(entries)} 条原始条目")
        except Exception as e:
            print(f"❌ 提取 {site} 失败: {e}")
            site_stats[site] = {'status': 'fail', 'entries': 0, 'error': str(e)}
            continue

        unique_entries = []
        for entry in entries:
            identifier = entry.get('link') or entry.get('title') or ''
            if not identifier:
                continue
            h = hash_text(identifier)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            if entry.get('title'):
                entry['title_zh'] = translate_text(entry['title'])
            if entry.get('summary'):
                entry['summary_zh'] = translate_text(entry['summary'])
            unique_entries.append(entry)

        all_entries.extend(unique_entries)
        site_stats[site] = {'status': 'ok', 'entries': len(unique_entries)}
        print(f"{site}: 去重后 {len(unique_entries)} 条")

    state['last_run'] = datetime.now().isoformat()
    state['last_date'] = date_str
    state['seen_hashes'] = list(seen_hashes)
    for site in URLS.keys():
        if site in site_stats and site_stats[site]['status'] == 'ok':
            state['failure_count'][site] = 0
        else:
            state['failure_count'][site] = state['failure_count'].get(site, 0) + 1
    save_state(state)

    if all_entries:
        today_json = {
            'date': date_str,
            'total': len(all_entries),
            'sources': site_stats,
            'entries': all_entries
        }
        json_path = os.path.join(json_dir, f"{date_str}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(today_json, f, ensure_ascii=False, indent=2)
        print(f"✅ 今日数据保存至 {json_path}")

        latest_path = 'docs/latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(today_json, f, ensure_ascii=False, indent=2)
        print(f"✅ 最新数据更新至 {latest_path}")

        # 频率统计（简化）
        freq = {}
        for entry in all_entries:
            pub = entry.get('published', '')
            hour_match = re.search(r'(\d+)\s*(hour|hr|h|分钟|minute|min)', pub, re.I)
            if hour_match:
                num = int(hour_match.group(1))
                if 'min' in hour_match.group(2).lower():
                    pass
                else:
                    now = datetime.now()
                    target_hour = (now - timedelta(hours=num)).strftime('%H')
                    freq[target_hour] = freq.get(target_hour, 0) + 1
            else:
                current_hour = datetime.now().strftime('%H')
                freq[current_hour] = freq.get(current_hour, 0) + 1
        freq_path = 'docs/freq.json'
        with open(freq_path, 'w', encoding='utf-8') as f:
            json.dump(freq, f)
        print(f"✅ 频率数据保存至 {freq_path}")
    else:
        print("⚠️ 没有提取到任何新闻条目")

    # 健康状态（即使无条目也保存）
    health = {
        'last_run': state['last_run'],
        'last_date': state['last_date'],
        'sites': site_stats,
        'failure_counts': state['failure_count']
    }
    with open('docs/health.json', 'w', encoding='utf-8') as f:
        json.dump(health, f)
    print("✅ 健康状态更新")

    print("✅ 数据提取、翻译、去重完成")

if __name__ == '__main__':
    main()
