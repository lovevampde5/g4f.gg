import os, sys, time
from seleniumbase import SB
from selenium.webdriver.common.by import By
import requests

# ==========================================
# 核心配置（和你 workflow 里的环境变量保持一致）
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

# ✅ 发送带截图的 Telegram 通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的 Telegram 通知...")
    print(f"   TG_TOKEN: {'已设置' if TG_TOKEN else '空'}")
    print(f"   TG_CHAT_ID: {TG_CHAT_ID}")

    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN 或 TG_CHAT_ID 为空")
        return

    if not os.path.exists(screenshot_path):
        print(f"⚠️ 截图文件不存在：{screenshot_path}，只发送文字消息")
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F 自动续期\n{text}"}
            r = requests.post(url, json=data, timeout=10)
            print(f"✅ 文字消息发送结果：状态码 {r.status_code}")
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return

    # 发送带图片的消息
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        files = {"photo": open(screenshot_path, "rb")}
        data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F 自动续期\n{text}"}
        r = requests.post(url, files=files, data=data, timeout=15)
        print(f"✅ 带截图通知发送结果：状态码 {r.status_code}")
        if r.status_code != 200:
            print(f"❌ 错误详情：{r.text}")
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 =====")

    # 先删除旧截图
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)

    try:
        with SB(headless=True, window_size="1920,1080") as sb:
            sb.open(TARGET_URL)
            sb.sleep(15)

            # 找续期按钮
            renew_button = None
            all_buttons = sb.find_elements(By.XPATH, "//button")
            for btn in all_buttons:
                try:
                    if btn.is_displayed() and "add" in btn.text.lower():
                        renew_button = btn
                        print(f"✅ 找到续期按钮：{btn.text.strip()}")
                        break
                except:
                    pass

            if not renew_button:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未找到续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            # 点击续期
            sb.driver.execute_script("arguments[0].scrollIntoView(true);", renew_button)
            sb.sleep(2)
            sb.driver.execute_script("arguments[0].click();", renew_button)
            sb.sleep(15)

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

            # 发送带截图的通知
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
