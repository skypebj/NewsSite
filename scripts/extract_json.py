import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
from common import URLS, get_date_str, hash_text, translate_text, load_state, save_state

# 导入各站提取器（这里只列出BBC和Fox，其他可类似添加）
def extract_bbc(html):
    soup = BeautifulSoup(html, 'lxml')
    articles = soup.select('div[data-testid="card-text-wrapper"]')
    results = []
    for art in articles[:20]:
        try:
            title = art.select_one('h2[data-testid="card-headline"]').get_text(strip=True)
            link = art.select_one('a[data-testid="internal-link"]').get('href')
            if link and not link.startswith('http'):
                link = 'https://www.bbc.com' + link
            summary = art.select_one('p[data-testid="card-description"]').get_text(strip=True) if art.select_one('p[data-testid="card-description"]') else ""
            published = art.select_one('span[data-testid="card-metadata"]').get_text(strip=True) if art.select_one('span[data-testid="card-metadata"]') else ""
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
            title = art.select_one('h2.title, h3.title, .title').get_text(strip=True)
            link = art.select_one('a[href*="/story/"], a[href*="/article/"]')
            if link:
                link = link.get('href')
                if link and not link.startswith('http'):
                    link = 'https://www.foxnews.com' + link
            summary = art.select_one('.dek, .description, .content p').get_text(strip=True) if art.select_one('.dek, .description, .content p') else ""
            published = art.select_one('.time, .timestamp, .date').get_text(strip=True) if art.select_one('.time, .timestamp, .date') else ""
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
            href = link.get('href')
            if href:
                results.append({'title': title, 'link': href, 'summary': '', 'published': ''})
    return results[:20]

EXTRACTORS = {
    'bbc': extract_bbc,
    'fox': extract_fox,
    # 其他网站可添加映射，默认使用generic
}

def main():
    state = load_state()
    date_str = get_date_str()
    seen_hashes = set(state.get('seen_hashes', []))
    new_hashes = []
    all_entries = []
    success_count = 0
    failure_count = 0
    site_stats = {}

    html_dir = 'docs/html'
    json_dir = 'docs/json'
    os.makedirs(json_dir, exist_ok=True)

    # 获取今天的所有HTML文件
    for filename in os.listdir(html_dir):
        if not filename.endswith('.html'):
            continue
        # 提取网站名
        parts = filename.split('_')
        if len(parts) < 3:
            continue
        site = parts[0]
        # 读取HTML
        html_path = os.path.join(html_dir, filename)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        # 提取
        extractor = EXTRACTORS.get(site, extract_generic)
        try:
            entries = extractor(html_content)
        except Exception as e:
            print(f"❌ 提取 {site} 失败: {e}")
            failure_count += 1
            site_stats[site] = {'status': 'fail', 'entries': 0, 'error': str(e)}
            continue
        success_count += 1
        # 去重（基于标题+链接哈希）
        unique_entries = []
        for entry in entries:
            identifier = entry.get('link', entry.get('title', ''))
            h = hash_text(identifier)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            new_hashes.append(h)
            unique_entries.append(entry)
        # 翻译（标题和摘要）
        for entry in unique_entries:
            if entry.get('title'):
                entry['title_zh'] = translate_text(entry['title'])
            if entry.get('summary'):
                entry['summary_zh'] = translate_text(entry['summary'])
        all_entries.extend(unique_entries)
        site_stats[site] = {'status': 'ok', 'entries': len(unique_entries)}

    # 更新状态
    state['last_run'] = datetime.now().isoformat()
    state['last_date'] = date_str
    state['seen_hashes'] = list(seen_hashes)
    # 连续失败计数（按网站）
    for site in URLS.keys():
        if site not in site_stats:
            state['failure_count'][site] = state['failure_count'].get(site, 0) + 1
        else:
            if site_stats[site]['status'] == 'fail':
                state['failure_count'][site] = state['failure_count'].get(site, 0) + 1
            else:
                state['failure_count'][site] = 0
    save_state(state)

    # 保存今日JSON（全量）
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

        # 同时生成发布频率统计（按小时）
        freq = {}
        for entry in all_entries:
            pub = entry.get('published', '')
            # 尝试解析时间（简单处理，可改进）
            hour = '00'
            if 'hour' in pub or 'minute' in pub:
                # 粗略：若包含 'hour ago' 则推算
                pass
            # 这里简化：从published中提取小时，若无则用当前小时
            from datetime import datetime
            hour_str = datetime.now().strftime('%H')
            freq[hour_str] = freq.get(hour_str, 0) + 1
        # 保存频率数据供前端图表使用
        freq_path = 'docs/freq.json'
        with open(freq_path, 'w', encoding='utf-8') as f:
            json.dump(freq, f)

    # 生成健康状态JSON
    health = {
        'last_run': state['last_run'],
        'last_date': state['last_date'],
        'sites': site_stats,
        'failure_counts': state['failure_count']
    }
    with open('docs/health.json', 'w', encoding='utf-8') as f:
        json.dump(health, f)

    print("✅ 数据提取、翻译、去重完成")

if __name__ == '__main__':
    main()
