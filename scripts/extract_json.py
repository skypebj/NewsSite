import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
from common import URLS, get_date_str, hash_text, translate_text, load_state, save_state

# 提取器（仅列出 BBC 和 Fox，其他可扩展）
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
    soup = BeautifulSoup(html, 'lxml')
    results = []
    for h in soup.find_all(['h1', 'h2', 'h3']):
        link = h.find('a')
        if link:
            title = h.get_text(strip=True)
            href = link.get('href') or ''
            if href:
                results.append({'title': title, 'link': href, 'summary': '', 'published': ''})
    return results[:20]

EXTRACTORS = {
    'bbc': extract_bbc,
    'fox': extract_fox,
    # 其他网站可添加映射，默认使用 generic
}

def main():
    state = load_state()
    date_str = get_date_str()
    seen_hashes = set(state.get('seen_hashes', []))
    new_hashes = []
    all_entries = []
    site_stats = {}

    html_dir = 'docs/html'
    json_dir = 'docs/json'
    os.makedirs(json_dir, exist_ok=True)

    # 获取当天所有 HTML 文件（按网站）
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
        except Exception as e:
            print(f"❌ 提取 {site} 失败: {e}")
            site_stats[site] = {'status': 'fail', 'entries': 0, 'error': str(e)}
            continue

        # 去重
        unique_entries = []
        for entry in entries:
            # 确保 identifier 为非空字符串
            identifier = entry.get('link') or entry.get('title') or ''
            if not identifier:
                # 如果连标题都没有，跳过
                continue
            h = hash_text(identifier)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            new_hashes.append(h)
            # 翻译（标题和摘要）
            if entry.get('title'):
                entry['title_zh'] = translate_text(entry['title'])
            if entry.get('summary'):
                entry['summary_zh'] = translate_text(entry['summary'])
            unique_entries.append(entry)

        all_entries.extend(unique_entries)
        site_stats[site] = {'status': 'ok', 'entries': len(unique_entries)}

    # 更新状态
    state['last_run'] = datetime.now().isoformat()
    state['last_date'] = date_str
    state['seen_hashes'] = list(seen_hashes)
    # 更新连续失败计数
    for site in URLS.keys():
        if site in site_stats and site_stats[site]['status'] == 'ok':
            state['failure_count'][site] = 0
        else:
            state['failure_count'][site] = state['failure_count'].get(site, 0) + 1
    save_state(state)

    # 保存今日 JSON（全量）
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

        # 更新 latest.json
        latest_path = 'docs/latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(today_json, f, ensure_ascii=False, indent=2)
        print(f"✅ 最新数据更新至 {latest_path}")

        # 生成发布频率统计（按小时，从 published 提取）
        freq = {}
        for entry in all_entries:
            pub = entry.get('published', '')
            # 尝试提取小时（简化：若包含数字+hour/min，则粗略处理，否则用当前小时）
            import re
            hour_match = re.search(r'(\d+)\s*(hour|hr|h|分钟|minute|min)', pub, re.I)
            if hour_match:
                num = int(hour_match.group(1))
                # 如果是分钟，忽略；如果是小时，计算当前时间减去小时数
                if 'min' in hour_match.group(2).lower():
                    # 忽略分钟
                    pass
                else:
                    # 简单处理：用当前时间减去小时数
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    target_hour = (now - timedelta(hours=num)).strftime('%H')
                    freq[target_hour] = freq.get(target_hour, 0) + 1
            else:
                # 默认使用当前小时
                current_hour = datetime.now().strftime('%H')
                freq[current_hour] = freq.get(current_hour, 0) + 1
        freq_path = 'docs/freq.json'
        with open(freq_path, 'w', encoding='utf-8') as f:
            json.dump(freq, f)
        print(f"✅ 频率数据保存至 {freq_path}")
    else:
        print("⚠️ 没有提取到任何新闻条目")

    # 生成健康状态 JSON
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
