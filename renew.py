import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

# ✅ 发送带截图的 Telegram 通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的 Telegram 通知...")
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN 或 TG_CHAT_ID 为空")
        return

    if not os.path.exists(screenshot_path):
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F 自动续期\n{text}"}
            requests.post(url, json=data, timeout=10)
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return

    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F 自动续期\n{text}"}
            requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (GitHub Actions 优化版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 💡 针对 GitHub Actions 的关键配置：启用 uc 反检测，并用 xvfb 虚拟桌面代替纯 headless
        with SB(uc=True, xvfb=True, window_size="1920,1080") as sb:
            
            print("🌐 正在通过反检测模式打开页面...")
            # 瞬间断开控制链路，绕过 Cloudflare 首次扫描
            sb.uc_open_with_disconnect(TARGET_URL)
            sb.sleep(10)  

            # 🛡️ 绕过 Cloudflare Turnstile 验证码的兜底逻辑
            print("🛡️ 检查是否存在 Turnstile 人机验证...")
            try:
                cf_iframe = "iframe[src*='challenges.cloudflare.com']"
                if sb.is_element_visible(cf_iframe):
                    print("⚠️ 探测到验证码弹窗，尝试进行模拟人类点击...")
                    # 切入验证码 iframe 内部
                    sb.switch_to_frame(cf_iframe)
                    # 模拟真人点击复选框区域
                    sb.uc_click("#challenge-stage")
                    # 切回主页面并等待
                    sb.switch_to_default_content()
                    print("⏳ 已点击验证，等待 8 秒...")
                    sb.sleep(8)
                else:
                    print("✅ 未发现显式验证码，可能已无感通过。")
            except Exception as cf_err:
                print(f"ℹ️ 处理验证码时跳过或异常（可能已自动通过）: {cf_err}")
                sb.switch_to_default_content()

            print("🔍 正在执行续期点击...")
            
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 使用 uc_click 避免点击瞬间触发自动化特征检测
                    sb.uc_click(selector, timeout=8)
                    print(f"✅ 成功点击按钮 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能在规定时间内定位并点击按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已点击续期按钮，等待页面刷新...")
            sb.sleep(10)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 续期成功！\n剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_
