import os
import sys
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
    print("\n===== 🚀 g4f.gg 自动续期 (Cloudflare 强力破盾版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 🔥 核心修正：
        # uc=True: 开启防检测
        # xvfb=True: 如果在 Linux 服务器运行，这会启动虚拟桌面运行“真·有头模式”，比 headless 稳一万倍。
        # 如果是在 Windows/Mac 本地测试，可以把 xvfb=True 改为 headless=False 观察点击过程。
        with SB(uc=True, xvfb=True, window_size="1920,1080") as sb:
            
            print("🌐 正在安全打开目标网页...")
            sb.uc_open_with_disconnect(TARGET_URL) # 使用断开连接的方式开网页，防止开局被抓
            sb.sleep(12) 

            print("🔍 正在定位续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    # 🔥 使用 uc_click 代替普通 click，断开 CDP 连接进行原生点击
                    sb.uc_click(selector, timeout=10)
                    print(f"✅ 成功点击按钮 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能在规定时间内定位并点击按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已点击续期按钮，检测是否弹出人类验证...")
            sb.sleep(6)
            
            # ==========================================
            # 🛡️ Cloudflare Turnstile 破盾核心
            # ==========================================
            cf_iframe = "iframe[src*='challenges.cloudflare.com']"
            if sb.is_element_present(cf_iframe):
                print("🛡️ 警报：检测到 Cloudflare 验证弹窗！正在尝试穿透...")
                
                # 切换进验证码的 iframe
                sb.switch_to_frame(cf_iframe)
                sb.sleep(2)
                
                try:
                    # 优先尝试点击复选框，同样用 uc_click
                    print("🔘 尝试模拟原生点击验证复选框...")
                    sb.uc_click("input[type='checkbox']", timeout=4)
                except Exception:
                    # 如果找不到 checkbox，直接点击验证框的 body 区域通常也能触发
                    print("🔘 尝试点击验证框空白区域触发...")
                    sb.uc_click("body", timeout=4)
                
                # 切回主页面
                sb.switch_to_default_content()
                print("⏳ 验证指令已发送，给 Cloudflare 15 秒生成 Token...")
                sb.sleep(15)
            else:
                print("✨ 运气不错，未检测到验证弹窗或已自动通过。")

            print("⏳ 正在等待最终页面刷新...")
            sb.sleep(10)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 续期完成！\n剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期异常失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
