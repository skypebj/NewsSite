#!/usr/bin/env python3
"""
生成两个页面：
- docs/index.html   : 主页，显示所有HTML源码文件列表
- docs/gallery.html : 画廊页，显示截图、词云、图表、健康状态等
"""

import os
import json
import re
from datetime import datetime
from collections import defaultdict

# ---------- 辅助函数 ----------
def parse_html_filename(filename):
    """解析HTML文件名，返回 (站点, 日期时间字符串, 格式化显示) 或 None"""
    parts = filename.split('_')
    if len(parts) >= 3 and parts[-1].endswith('.html'):
        site = parts[0]
        ts = parts[1] + '_' + parts[2].replace('.html', '')
        if re.match(r'^\d{8}_\d{6}$', ts):
            date_part = ts[:8]
            time_part = ts[9:15]
            display = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
            return {'site': site.upper(), 'timestamp': ts, 'display': display, 'filename': filename}
    return None

def generate_homepage():
    """生成新主页 index.html，显示HTML文件列表"""
    print("开始生成主页 index.html...")
    html_dir = 'docs/html'
    html_files = []
    if os.path.exists(html_dir):
        for f in os.listdir(html_dir):
            if f.endswith('.html'):
                parsed = parse_html_filename(f)
                if parsed:
                    html_files.append(parsed)
        html_files.sort(key=lambda x: x['timestamp'], reverse=True)

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output_path = 'docs/index.html'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新闻源码存档</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #f0f2f5; padding: 20px; transition: background 0.3s, color 0.3s; }}
        body.dark {{ background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 20px; }}
        h1 {{ margin: 0; }}
        .nav-link {{ font-size: 18px; background: #007bff; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; }}
        .nav-link:hover {{ background: #0056b3; }}
        .section-title {{ font-size: 24px; margin: 20px 0 15px; border-bottom: 2px solid #ddd; padding-bottom: 8px; }}
        body.dark .section-title {{ border-bottom-color: #444; }}
        .file-grid {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .file-item {{ background: white; border-radius: 6px; padding: 8px 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); display: inline-flex; align-items: center; }}
        body.dark .file-item {{ background: #2a2a4a; }}
        .file-item a {{ text-decoration: none; color: #007bff; }}
        body.dark .file-item a {{ color: #66b0ff; }}
        .file-item .site {{ font-weight: bold; margin-right: 8px; }}
        .file-item .time {{ color: #666; font-size: 0.9em; }}
        body.dark .file-item .time {{ color: #aaa; }}
        .no-data {{ text-align: center; font-size: 18px; color: #999; margin-top: 50px; }}
        .theme-toggle {{ position: fixed; top: 20px; right: 20px; background: rgba(255,255,255,0.8); border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 20px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        body.dark .theme-toggle {{ background: rgba(0,0,0,0.6); color: #fff; }}
        @media (max-width: 600px) {{ .header {{ flex-direction: column; align-items: flex-start; gap: 10px; }} }}
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
    <div class="container">
        <div class="header">
            <h1>📄 新闻源码存档</h1>
            <a class="nav-link" href="./gallery.html">🖼️ 查看截图面板</a>
        </div>
        <div class="info" style="text-align:center; color:#666; margin-bottom:20px;">最后更新: {now_str}</div>

        <div class="section-title">📂 已保存的HTML文件（点击查看）</div>
        <div class="file-grid">
"""
    if not html_files:
        html += '            <div class="no-data">暂无HTML文件</div>'
    else:
        for item in html_files[:200]:
            html += f"""
            <div class="file-item">
                <span class="site">{item['site']}</span>
                <a href="./html/{item['filename']}" target="_blank">{item['display']}</a>
            </div>
        """
        if len(html_files) > 200:
            html += f'            <div class="file-item" style="background:transparent; box-shadow:none;">... 还有 {len(html_files)-200} 个文件</div>'

    html += """
        </div>
    </div>
    <script>
        function toggleTheme() {
            document.body.classList.toggle('dark');
            localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
        }
        if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.body.classList.add('dark');
        }
    </script>
</body>
</html>
"""
    html += f'\n<!-- 生成时间: {datetime.now().isoformat()} -->\n'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 主页已生成: {output_path}")


def generate_gallery():
    """生成画廊页 gallery.html，包含截图、词云、图表、健康状态等"""
    print("开始生成画廊页 gallery.html...")
    screenshot_dir = 'docs/screenshots'
    json_dir = 'docs/json'
    image_dir = 'docs/images'
    epub_dir = 'docs/epub'
    archive_dir = 'docs/archives'
    health_path = 'docs/health.json'
    freq_path = 'docs/freq.json'
    output_path = 'docs/gallery.html'

    # 1. 截图
    date_groups = defaultdict(list)
    if os.path.exists(screenshot_dir):
        for f in os.listdir(screenshot_dir):
            if f.endswith('.png'):
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
    for d in date_groups:
        date_groups[d].sort(key=lambda x: x['timestamp'], reverse=True)
    sorted_dates = sorted(date_groups.keys(), reverse=True)

    # 2. 词云
    wordcloud_images = []
    if os.path.exists(image_dir):
        wc_files = [f for f in os.listdir(image_dir) if f.startswith('wordcloud_') and f.endswith('.png')]
        if wc_files:
            wc_files.sort(reverse=True)
            wordcloud_images = wc_files

    # 3. EPUB
    epub_files = []
    if os.path.exists(epub_dir):
        epub_files = [f for f in os.listdir(epub_dir) if f.endswith('.epub')]
        epub_files.sort(reverse=True)

    # 4. 归档ZIP
    zip_files = []
    if os.path.exists(archive_dir):
        zip_files = [f for f in os.listdir(archive_dir) if f.endswith('.zip')]
        zip_files.sort(reverse=True)

    # 5. 健康状态
    health_data = {}
    if os.path.exists(health_path):
        with open(health_path, 'r', encoding='utf-8') as f:
            health_data = json.load(f)

    # 6. 频率数据
    freq_data = {}
    if os.path.exists(freq_path):
        with open(freq_path, 'r', encoding='utf-8') as f:
            freq_data = json.load(f)
    else:
        print("⚠️ 警告: 未找到 freq.json，使用空数据")

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新闻监控 - 截图面板</title>
    <link rel="manifest" href="./manifest.json">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #f0f2f5; padding: 20px; transition: background 0.3s, color 0.3s; }}
        body.dark {{ background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
        h1 {{ margin: 0; }}
        .nav-link {{ font-size: 16px; background: #28a745; color: white; padding: 6px 14px; border-radius: 4px; text-decoration: none; }}
        .nav-link:hover {{ background: #218838; }}
        .info {{ text-align: center; color: #666; margin-bottom: 20px; }}
        body.dark .info {{ color: #aaa; }}
        .controls {{ text-align: center; margin-bottom: 30px; }}
        select, button {{ padding: 8px 16px; font-size: 16px; border-radius: 4px; border: 1px solid #ccc; margin: 0 5px; background: white; }}
        body.dark select, body.dark button {{ background: #2a2a4a; color: #eee; border-color: #444; }}
        button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        .section {{ margin-bottom: 40px; }}
        .section-title {{ font-size: 24px; margin-bottom: 15px; border-bottom: 2px solid #ddd; padding-bottom: 8px; }}
        body.dark .section-title {{ border-bottom-color: #444; }}
        .gallery {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 15px; max-width: 800px; width: 100%; }}
        body.dark .card {{ background: #2a2a4a; }}
        .card img {{ width: 100%; height: auto; border-radius: 4px; border: 1px solid #ddd; cursor: pointer; }}
        body.dark .card img {{ border-color: #444; }}
        .card .info {{ margin-top: 8px; font-size: 14px; color: #555; text-align: center; }}
        body.dark .card .info {{ color: #ccc; }}
        .no-data {{ text-align: center; font-size: 18px; color: #999; margin-top: 50px; }}
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); }}
        .modal-content {{ margin: auto; display: block; max-width: 90%; max-height: 90%; top: 50%; transform: translateY(50%); }}
        .modal-close {{ position: absolute; right: 40px; top: 20px; color: #fff; font-size: 40px; cursor: pointer; }}
        .downloads a {{ display: inline-block; margin: 5px 10px; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; }}
        .downloads a:hover {{ background: #218838; }}
        .health-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .health-item {{ background: white; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
        body.dark .health-item {{ background: #2a2a4a; }}
        .health-item .status {{ font-weight: bold; }}
        .status.ok {{ color: #28a745; }}
        .status.fail {{ color: #dc3545; }}
        .chart-container {{ max-width: 600px; margin: 0 auto; }}
        .theme-toggle {{ position: fixed; top: 20px; right: 20px; background: rgba(255,255,255,0.8); border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 20px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        body.dark .theme-toggle {{ background: rgba(0,0,0,0.6); color: #fff; }}
        @media (max-width: 600px) {{ .health-grid {{ grid-template-columns: 1fr 1fr; }} .header {{ flex-direction: column; align-items: flex-start; gap: 10px; }} }}
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
    <div class="container">
        <div class="header">
            <h1>📸 监控面板</h1>
            <a class="nav-link" href="./index.html">📄 返回文件列表</a>
        </div>
        <div class="info">最后更新: {now_str}</div>

        <!-- 健康状态 -->
        <div class="section">
            <div class="section-title">🔍 健康状态</div>
            <div class="health-grid">
"""
    sites = health_data.get('sites', {})
    if sites:
        for site, info in sites.items():
            status_class = 'ok' if info.get('status') == 'ok' else 'fail'
            status_text = '✅ 成功' if info.get('status') == 'ok' else '❌ 失败'
            entries = info.get('entries', 0)
            html += f"""
                <div class="health-item">
                    <div><strong>{site.upper()}</strong></div>
                    <div class="status {status_class}">{status_text}</div>
                    <div>条目: {entries}</div>
                </div>
        """
    else:
        html += '<div class="no-data">暂无健康数据</div>'

    html += """
            </div>
        </div>

        <!-- 截图展示 -->
        <div class="section">
            <div class="section-title">📷 页面截图</div>
            <div class="controls">
                <label for="dateSelect">日期：</label>
                <select id="dateSelect" onchange="updateTimeOptions()">
                    <option value="">-- 全部 --</option>
"""
    for date in sorted_dates:
        display = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        html += f'                    <option value="{date}">{display}</option>\n'
    html += """
                </select>
                <label for="timeSelect">时间点：</label>
                <select id="timeSelect" onchange="filterGallery()">
                    <option value="">-- 全部 --</option>
                </select>
                <span id="countInfo"></span>
            </div>
            <div id="gallery" class="gallery">
"""
    all_items = []
    for date in sorted_dates:
        all_items.extend(date_groups[date])
    if not all_items:
        html += '<div class="no-data">暂无截图</div>'
    else:
        for item in all_items:
            date_display = f"{item['date'][:4]}-{item['date'][4:6]}-{item['date'][6:8]}"
            time_display = f"{item['time'][:2]}:{item['time'][2:4]}:{item['time'][4:6]}"
            img_src = f'./screenshots/{item["filename"]}'
            html += f"""
                <div class="card" data-date="{item['date']}" data-time="{item['time']}" data-site="{item['site']}">
                    <img src="{img_src}" alt="{item['site']} 截图" loading="lazy" onclick="openModal(this.src)">
                    <div class="info"><strong>{item['site'].upper()}</strong> - {date_display} {time_display}</div>
                </div>
            """
    html += """
            </div>
        </div>

        <!-- 词云 -->
        <div class="section">
            <div class="section-title">☁️ 热词云</div>
            <div style="text-align:center;">
"""
    if wordcloud_images:
        latest_wc = wordcloud_images[0]
        html += f'                <img src="./images/{latest_wc}" alt="词云" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">'
    else:
        html += '<div class="no-data">暂无词云</div>'
    html += """
            </div>
        </div>

        <!-- 发布频率图表 -->
        <div class="section">
            <div class="section-title">📈 发布频率（按小时）</div>
            <div class="chart-container">
                <canvas id="freqChart" width="600" height="300"></canvas>
            </div>
        </div>

        <!-- 下载区 -->
        <div class="section">
            <div class="section-title">📥 下载</div>
            <div class="downloads">
                <span style="font-weight:bold;">EPUB：</span>
"""
    if epub_files:
        for epub in epub_files[:5]:
            html += f'<a href="./epub/{epub}" download>{epub}</a> '
    else:
        html += '<span>暂无</span>'
    html += """
            </div>
            <div class="downloads" style="margin-top:10px;">
                <span style="font-weight:bold;">历史归档：</span>
"""
    if zip_files:
        for z in zip_files[:5]:
            html += f'<a href="./archives/{z}" download>{z}</a> '
    else:
        html += '<span>暂无</span>'
    html += """
            </div>
            <div class="downloads" style="margin-top:10px;">
                <a href="./latest.json" download>最新JSON</a>
            </div>
        </div>
    </div>

    <!-- 模态框 -->
    <div id="modal" class="modal" onclick="closeModal()">
        <span class="modal-close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // 主题切换
        function toggleTheme() {
            document.body.classList.toggle('dark');
            localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
        }
        if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.body.classList.add('dark');
        }

        // 截图筛选
        const cards = document.querySelectorAll('.card');
        const dateSelect = document.getElementById('dateSelect');
        const timeSelect = document.getElementById('timeSelect');
        const countInfo = document.getElementById('countInfo');

        function updateTimeOptions() {
            const selectedDate = dateSelect.value;
            timeSelect.innerHTML = '<option value="">-- 全部 --</option>';
            if (!selectedDate) { filterGallery(); return; }
            const times = new Set();
            cards.forEach(card => {
                if (card.getAttribute('data-date') === selectedDate) {
                    times.add(card.getAttribute('data-time'));
                }
            });
            const sorted = Array.from(times).sort().reverse();
            sorted.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t.slice(0,2) + ':' + t.slice(2,4) + ':' + t.slice(4,6);
                timeSelect.appendChild(opt);
            });
            if (sorted.length > 0) timeSelect.value = sorted[0];
            filterGallery();
        }

        function filterGallery() {
            const selectedDate = dateSelect.value;
            const selectedTime = timeSelect.value;
            let count = 0;
            cards.forEach(card => {
                const d = card.getAttribute('data-date');
                const t = card.getAttribute('data-time');
                let show = true;
                if (selectedDate && d !== selectedDate) show = false;
                if (selectedTime && t !== selectedTime) show = false;
                card.style.display = show ? 'block' : 'none';
                if (show) count++;
            });
            countInfo.textContent = `显示 ${count} 张截图`;
        }

        function openModal(src) {
            document.getElementById('modal').style.display = 'block';
            document.getElementById('modalImg').src = src;
        }
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }

        // 默认最新日期
        window.onload = function() {
            for (let i = 1; i < dateSelect.options.length; i++) {
                if (dateSelect.options[i].value) {
                    dateSelect.selectedIndex = i;
                    break;
                }
            }
            updateTimeOptions();

            // 绘制频率图表
            const freqData = """ + json.dumps(freq_data) + """;
            const ctx = document.getElementById('freqChart').getContext('2d');
            const hours = Object.keys(freqData).sort();
            const counts = hours.map(h => freqData[h] || 0);
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours.map(h => h + ':00'),
                    datasets: [{
                        label: '新闻发布数',
                        data: counts,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, stepSize: 1 } }
                }
            });
        };
    </script>
</body>
</html>
"""
    html += f'\n<!-- 生成时间: {datetime.now().isoformat()} -->\n'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 画廊页已生成: {output_path}")


# ---------- 主函数 ----------
def main():
    generate_homepage()
    generate_gallery()

if __name__ == '__main__':
    main()
