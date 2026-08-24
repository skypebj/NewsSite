import os
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from common import get_date_str
import jieba

def generate_wordcloud():
    date_str = get_date_str()
    json_path = f'docs/json/{date_str}.json'
    if not os.path.exists(json_path):
        print(f"❌ 没有找到 {date_str} 的JSON数据，跳过词云生成")
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    text = ' '.join([entry.get('title', '') for entry in data.get('entries', [])])
    if not text:
        print("没有标题文字，跳过词云")
        return
    # 中文分词
    words = jieba.cut(text)
    text = ' '.join(words)
    wc = WordCloud(font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', width=800, height=400, background_color='white').generate(text)
    output_dir = 'docs/images'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'wordcloud_{date_str}.png')
    plt.figure(figsize=(10,5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(output_path, dpi=100)
    plt.close()
    print(f"✅ 词云保存至 {output_path}")

if __name__ == '__main__':
    generate_wordcloud()
