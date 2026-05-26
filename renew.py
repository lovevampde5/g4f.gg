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
    print("\n===== 🚀 g4f.gg 自动续期 (两次点击破盾版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # uc=True 开启反检测模式
        # 提示：Linux 服务器运行建议保持 headless2=True 或改为 xvfb=True；本地调试可改为 headless=False
        with SB(uc=True, headless2=True, window_size="1920,1080") as sb:
            
            print("🌐 正在打开目标网页...")
            sb.uc_open_with_disconnect(TARGET_URL) 
            sb.sleep(10)  # 等待初始页面加载

            # 定义续期按钮的选择器
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]

            # ==========================================
            # 🔥 步骤 1：【第一次点击】—— 用来唤醒/触发验证码
            # ==========================================
            print("🔍 正在执行【第一次】续期点击（触发验证弹窗）...")
            clicked_first = False
            used_selector = None
            
            for selector in selectors:
                try:
                    sb.uc_click(selector, timeout=10)
                    print(f"✅ 第一次点击成功 (选择器: {selector})")
                    clicked_first = True
                    used_selector = selector  # 记录成功点击的选择器
                    break
                except Exception:
                    continue 

            if not clicked_first:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能完成第一次按钮点击", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已触发点击，等待 5 秒检测是否弹出验证框...")
            sb.sleep(5)

            # ==========================================
            # 🔥 步骤 2：【穿透验证】—— 解决 Cloudflare 拦截
            # ==========================================
            cf_iframe = "iframe[src*='challenges.cloudflare.com']"
            if sb.is_element_present(cf_iframe):
                print("🛡️ 检测到 Cloudflare 验证弹窗！开始穿透...")
                
                # 切入验证码 iframe
                sb.switch_to_frame(cf_iframe)
                sb.sleep(1)
                
                try:
                    print("🔘 正在模拟原生点击验证复选框...")
                    sb.uc_click("input[type='checkbox']", timeout=5)
                except Exception:
                    try:
                        sb.uc_click("#challenge-stage", timeout=5)
                    except Exception:
                        sb.uc_click("body", timeout=5)
                
                # 必须切回主页面
                sb.switch_to_default_content()
                
                print("⏳ 验证点击完成，留出 12 秒让环境稳定、解除锁定...")
                sb.sleep(12)
            else:
                print("✨ 提示：未检测到验证弹窗，可能环境安全已直接放行。")

            # ==========================================
            # 🔥 步骤 3：【第二次点击】—— 验证通过后再次点击，真正成功续期
            # ==========================================
            print("🚀 正在执行【第二次】续期点击（真正提交续期）...")
            clicked_second = False
            
            # 优先使用第一次成功过的选择器
            target_selectors = [used_selector] + selectors if used_selector else selectors
            for selector in target_selectors:
                if not selector: continue
                try:
                    sb.uc_click(selector, timeout=10)
                    print(f"🎉 第二次点击成功！续期请求已正式发出。")
                    clicked_second = True
                    break
                except Exception:
                    continue

            if not clicked_second:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：验证后无法进行第二次点击确认", SCREENSHOT_PATH)
                sys.exit(1)

            print("⏳ 等待 10 秒让服务器处理并刷新数据...")
            sb.sleep(10)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 续期操作成功完成！\n最新服务器剩余时间：{remaining}"
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
