import os
import sys
import time
from seleniumbase import SB
from selenium.webdriver.common.by import By
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
    print("\n===== 🚀 g4f.gg 自动续期 (特定顺序优化版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 启用 UC 防检测模式
        with SB(uc=True, headless=True, window_size="1920,1080") as sb:
            
            print(f"🌐 正在打开目标网址: {TARGET_URL}")
            sb.uc_open_with_reconnect(TARGET_URL, 4)
            sb.sleep(8)  # 等待初始页面加载

            print("🔍 步骤 1：正在寻找并点击续期按钮...")
            selectors = [
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(., 'ADD')]",
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'RENEW')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    if sb.is_element_visible(selector):
                        sb.click(selector, timeout=5)
                        print(f"✅ 成功点击续期按钮 (匹配选择器: {selector})")
                        clicked = True
                        break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                try:
                    with open("page_source.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())
                except:
                    pass
                send_tg_with_screenshot("❌ 续期失败：未能在初始页面中定位到续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            # 💡 核心修改：点击按钮后，按照你的提示，等待验证码弹窗显现
            print("⏳ 步骤 2：已点击续期按钮，等待 Cloudflare 验证码弹窗浮现...")
            sb.sleep(8)  # 给验证码动画和加载留出 8 秒时间

            # 💡 核心修改：此时再执行破盾，去点击“验证您是真人”
            print("🛡️ 步骤 3：正在检测并点击 Cloudflare Turnstile 真人验证框...")
            try:
                # 尝试使用高级 GUI 验证码点击
                sb.uc_gui_click_captcha()
                print("🔘 已触发自动点击验证框，等待验证通过及页面响应...")
                sb.sleep(12)  # 留出足够时间让 Cloudflare 放行并完成续期后台通信
            except Exception as ce:
                print(f"⚠️ 自动点击验证码时出现提示（若已成功可忽略）: {ce}")
                sb.sleep(5)

            # 续期和验证完成后截图存证
            sb.save_screenshot(SCREENSHOT_PATH)

            print("📊 步骤 4：正在获取续期后的剩余时间...")
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(., 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                try:
                    remaining = sb.get_text("//*[contains(., 'REMAINING') or contains(., '剩余时间')]")
                except:
                    pass

            success_msg = f"✅ 续期流程执行完毕！\n结果参考截图。\n提取到的剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期异常退出：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
