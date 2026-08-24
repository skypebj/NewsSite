#!/usr/bin/env python3
import os
import json
import re
from datetime import datetime
from collections import defaultdict

def generate_index():
    # 读取各数据文件
    health = {}
    if os.path.exists('docs/health.json'):
        with open('docs/health.json', 'r', encoding='utf-8') as f:
            health = json.load(f)
    freq = {}
    if os.path.exists('docs/freq.json'):
        with open('docs/freq.json', 'r', encoding='utf-8') as f:
            freq = json.load(f)
    # 获取最新词云图片
    wordcloud_files = []
    if os.path.exists('docs/images'):
        wordcloud_files = [f for f in os.listdir('docs/images') if f.startswith('wordcloud_') and f.endswith('.png')]
        wordcloud_files.sort(reverse=True)
    latest_wordcloud = wordcloud_files[0] if wordcloud_files else None

    # 获取截图列表
    screenshot_files = []
    if os.path.exists('docs/screenshots'):
        screenshot_files = [f for f in os.listdir('docs/screenshots') if f.endswith('.png')]
    # 按日期和时间分组
    date_groups = defaultdict(list)
    for f in screenshot_files:
        match = re.match(r'^(\w+)_(\d{8})_(\d{6})\.png$', f)
        if match:
            site, date_str, time_str = match.groups()
            date_groups[date_str].append({
                'site': site,
                'date': date_str,
                'time': time_str,
                'filename': f,
                'timestamp': f"{date_str}_{time_str}"
            })
    sorted_dates = sorted(date_groups.keys(), reverse=True)
    for d in date_groups:
        date_groups[d].sort(key=lambda x: x['timestamp'], reverse=True)

    # 获取EPUB列表
    epub_files = []
    if os.path.exists('docs/epub'):
        epub_files = [f for f in os.listdir('docs/epub') if f.endswith('.epub')]
        epub_files.sort(reverse=True)

    # 获取ZIP列表
    zip_files = []
    if os.path.exists('docs/archives'):
        zip_files = [f for f in os.listdir('docs/archives') if f.endswith('.zip')]
        zip_files.sort(reverse=True)

    # 构建HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新闻监控仪表板</title>
    <link rel="manifest" href="./manifest.json">
    <style>
        :root {{
            --bg-color: #f0f2f5;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #dddddd;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #1a1a2e;
                --card-bg: #16213e;
                --text-color: #eeeeee;
                --border-color: #444444;
            }}
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: Arial, sans-serif; background: var(--bg-color); color: var(--text-color); padding: 20px; transition: background 0.3s, color 0.3s; }}
        h1 {{ text-align: center; margin-bottom: 10px; }}
        .info {{ text-align: center; color: #888; margin-bottom: 20px; }}
        .health-panel {{ background: var(--card-bg); border-radius: 8px; padding: 15px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .health-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }}
        .health-item {{ padding: 10px; border-radius: 4px; background: var(--bg-color); text-align: center; }}
        .health-item.ok {{ border-left: 4px solid #28a745; }}
        .health-item.fail {{ border-left: 4px solid #dc3545; }}
        .health-item .status {{ font-weight: bold; }}
        .controls {{ text-align: center; margin-bottom: 30px; }}
        select, button {{ padding: 8px 16px; font-size: 16px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--card-bg); color: var(--text-color); margin: 0 5px; }}
        button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        .gallery {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
        .card {{ background: var(--card-bg); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 15px; max-width: 800px; width: 100%; }}
        .card img {{ width: 100%; height: auto; border-radius: 4px; border: 1px solid var(--border-color); cursor: pointer; }}
        .card .info {{ margin-top: 8px; font-size: 14px; text-align: center; }}
        .no-data {{ text-align: center; font-size: 18px; color: #999; margin-top: 50px; }}
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); }}
        .modal-content {{ margin: auto; display: block; max-width: 90%; max-height: 90%; top: 50%; transform: translateY(50%); }}
        .modal-close {{ position: absolute; right: 40px; top: 20px; color: #fff; font-size: 40px; cursor: pointer; }}
        .downloads {{ margin-top: 40px; text-align: center; }}
        .downloads a {{ display: inline-block; margin: 5px 10px; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; }}
        .downloads a:hover {{ background: #218838; }}
        .chart-container {{ background: var(--card-bg); border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .wordcloud-container {{ text-align: center; margin: 20px 0; }}
        .wordcloud-container img {{ max-width: 100%; border-radius: 8px; }}
        @media (max-width: 600px) {{
            .health-grid {{ grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }}
            .card {{ max-width: 100%; }}
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>📰 新闻监控仪表板</h1>
    <div class="info">最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

    <!-- 健康面板 -->
    <div class="health-panel">
        <h3>📊 抓取状态</h3>
        <div class="health-grid">
            {''.join([f"""
            <div class="health-item {site_stats.get('status', 'ok')}" title="失败计数: {health.get('failure_counts', {}).get(site, 0)}">
                <strong>{site.upper()}</strong><br>
                <span class="status">{site_stats.get('status', 'unknown')}</span><br>
                <span>条目: {site_stats.get('entries', 0)}</span>
            </div>
            """ for site, site_stats in health.get('sites', {}).items()])}
        </div>
        <p style="margin-top:10px; font-size:14px; color: #888;">失败计数: {', '.join([f"{k}: {v}" for k,v in health.get('failure_counts', {}).items() if v > 0]) or '无'}</p>
    </div>

    <!-- 词云 -->
    <div class="wordcloud-container">
        <h3>☁️ 今日热词</h3>
        {f'<img src="./images/{latest_wordcloud}" alt="词云">' if latest_wordcloud else '<p>暂无词云</p>'}
    </div>

    <!-- 发布频率图表 -->
    <div class="chart-container">
        <h3>📈 各小时发布频率</h3>
        <canvas id="freqChart" width="800" height="400"></canvas>
    </div>

    <!-- 截图筛选和展示 -->
    <div class="controls">
        <label for="dateSelect">日期：</label>
        <select id="dateSelect" onchange="updateTimeOptions()">
            <option value="">-- 全部 --</option>
            {''.join([f'<option value="{date}">{date[:4]}-{date[4:6]}-{date[6:8]}</option>' for date in sorted_dates])}
        </select>
        <label for="timeSelect">时间点：</label>
        <select id="timeSelect" onchange="filterGallery()">
            <option value="">-- 全部 --</option>
        </select>
        <span id="countInfo"></span>
    </div>
    <div id="gallery" class="gallery">
        {''.join([f"""
        <div class="card" data-date="{item['date']}" data-time="{item['time']}" data-site="{item['site']}">
            <img src="./screenshots/{item['filename']}" alt="{item['site']} 截图" loading="lazy" onclick="openModal(this.src)">
            <div class="info"><strong>{item['site'].upper()}</strong> - {item['date'][:4]}-{item['date'][4:6]}-{item['date'][6:8]} {item['time'][:2]}:{item['time'][2:4]}:{item['time'][4:6]}</div>
        </div>
        """ for item in [item for date in sorted_dates for item in date_groups[date]]]) or '<div class="no-data">暂无截图</div>'}
    </div>

    <!-- 下载区域 -->
    <div class="downloads">
        <h3>📥 下载</h3>
        <a href="./latest.json">最新JSON数据</a>
        {''.join([f'<a href="./epub/{f}">EPUB: {f}</a>' for f in epub_files[:3]]) if epub_files else ''}
        {''.join([f'<a href="./archives/{f}">归档: {f}</a>' for f in zip_files[:5]]) if zip_files else ''}
        <a href="./health.json">健康状态</a>
    </div>

    <!-- 模态框 -->
    <div id="modal" class="modal" onclick="closeModal()">
        <span class="modal-close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>

    <script>
        // 数据：频率
        const freqData = {json.dumps(freq)};
        const labels = Object.keys(freqData).sort();
        const data = labels.map(h => freqData[h]);
        // 绘制图表
        const ctx = document.getElementById('freqChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [{{
                    label: '新闻数量',
                    data: data,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0,123,255,0.1)',
                    fill: true,
                    tension: 0.3
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    x: {{ title: {{ display: true, text: '小时' }} }},
                    y: {{ title: {{ display: true, text: '数量' }}, beginAtZero: true }}
                }}
            }}
        }});

        // 截图筛选逻辑（与之前相同）
        const cards = document.querySelectorAll('.card');
        const dateSelect = document.getElementById('dateSelect');
        const timeSelect = document.getElementById('timeSelect');
        const countInfo = document.getElementById('countInfo');

        function updateTimeOptions() {{
            const selectedDate = dateSelect.value;
            timeSelect.innerHTML = '<option value="">-- 全部 --</option>';
            if (!selectedDate) {{
                filterGallery();
                return;
            }}
            const times = new Set();
            cards.forEach(card => {{
                if (card.getAttribute('data-date') === selectedDate) {{
                    times.add(card.getAttribute('data-time'));
                }}
            }});
            const sorted = Array.from(times).sort().reverse();
            sorted.forEach(t => {{
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t.slice(0,2) + ':' + t.slice(2,4) + ':' + t.slice(4,6);
                timeSelect.appendChild(opt);
            }});
            if (sorted.length) timeSelect.value = sorted[0];
            filterGallery();
        }}

        function filterGallery() {{
            const selectedDate = dateSelect.value;
            const selectedTime = timeSelect.value;
            let count = 0;
            cards.forEach(card => {{
                const cardDate = card.getAttribute('data-date');
                const cardTime = card.getAttribute('data-time');
                let show = true;
                if (selectedDate && cardDate !== selectedDate) show = false;
                if (selectedTime && cardTime !== selectedTime) show = false;
                card.style.display = show ? 'block' : 'none';
                if (show) count++;
            }});
            countInfo.textContent = `显示 ${{count}} 张截图`;
        }}

        function openModal(src) {{
            document.getElementById('modal').style.display = 'block';
            document.getElementById('modalImg').src = src;
        }}

        function closeModal() {{
            document.getElementById('modal').style.display = 'none';
        }}

        // 默认加载最新日期和时间
        window.onload = function() {{
            for (let i = 1; i < dateSelect.options.length; i++) {{
                if (dateSelect.options[i].value) {{
                    dateSelect.selectedIndex = i;
                    break;
                }}
            }}
            updateTimeOptions();
        }};
    </script>
</body>
</html>
"""

    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ 仪表板生成成功: docs/index.html")

if __name__ == '__main__':
    generate_index()
