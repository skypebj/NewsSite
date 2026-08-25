import os
from playwright.sync_api import sync_playwright
from common import URLS, get_timestamp

def screenshot_page(url, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=30000)
            # 等待页面加载
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # 处理可能的弹窗（Cookie同意等）
            # 尝试点击常见的Accept按钮
            accept_selectors = [
                'button:has-text("Accept")',
                'button:has-text("同意")',
                'button:has-text("Allow")',
                'button:has-text("OK")',
                'button:has-text("继续")',
                '#onetrust-accept-btn-handler',
                '.cookie-accept',
                '[aria-label="Close"]',
                '.modal-close'
            ]
            for selector in accept_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click()
                        page.wait_for_timeout(1000)  # 等待弹窗消失
                        break
                except:
                    pass
            
            # 滚动到底部，触发懒加载
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(3000)  # 等待内容加载
            # 再次滚动到底部，确保所有懒加载触发
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(2000)
            # 滚动回顶部
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(500)
            
            # 全屏截图
            page.screenshot(path=output_path, full_page=True)
        except Exception as e:
            print(f"截图过程中出错: {e}")
            # 即便出错，也尝试截图当前视口
            page.screenshot(path=output_path, full_page=False)
        finally:
            browser.close()

def main():
    enable = os.environ.get('ENABLE_SCREENSHOT', 'true').lower() == 'true'
    if not enable:
        print("⚠️ 截图功能已禁用 (ENABLE_SCREENSHOT=false)")
        return
    print("=== 截图任务开始 ===")
    timestamp = get_timestamp()
    output_dir = 'docs/screenshots'
    os.makedirs(output_dir, exist_ok=True)
    for name, url in URLS.items():
        try:
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            print(f"正在截图 {name} ...")
            screenshot_page(url, filepath)
            print(f"✅ {name} 截图保存至 {filepath}")
        except Exception as e:
            print(f"❌ {name} 截图失败: {e}")

if __name__ == '__main__':
    main()
