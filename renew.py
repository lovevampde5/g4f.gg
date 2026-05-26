import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置（已针对g4f.gg弹窗验证优化）
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"
MAX_RETRIES = 3
# ✅ 点击后先等15秒（足够弹窗加载）
INITIAL_WAIT_AFTER_CLICK = 15
# ✅ 验证框父容器选择器（你的弹窗就是这个）
CAPTCHA_PARENT_SELECTOR = "div[role='dialog']"

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

# ✅ 专门处理g4f.gg点击后弹出的Turnstile验证
def handle_g4f_turnstile(sb):
    print(f"⏳ 点击完成，等待 {INITIAL_WAIT_AFTER_CLICK} 秒让验证弹窗完全加载...")
    time.sleep(INITIAL_WAIT_AFTER_CLICK)
    
    # 检测验证弹窗是否出现
    if sb.is_element_visible(CAPTCHA_PARENT_SELECTOR):
        print("✅ 检测到验证弹窗，正在处理Cloudflare Turnstile...")
        try:
            # ✅ 核心修复1：显式指定验证框父容器
            # ✅ 核心修复2：断开驱动连接3秒，模拟真人操作（最关键）
            sb.uc_gui_click_captcha(CAPTCHA_PARENT_SELECTOR, reconnect_time=3)
            time.sleep(5)
            
            # 等待验证完成和弹窗消失
            sb.wait_for_element_not_visible(CAPTCHA_PARENT_SELECTOR, timeout=25)
            print("✅ Cloudflare验证通过，弹窗已关闭！")
            return True
            
        except Exception as e:
            print(f"❌ 验证处理失败：{e}")
            # 备用方案：CDP直接点击验证框
            try:
                print("ℹ️ 尝试备用CDP方案...")
                sb.cdp.gui_click_element(f"{CAPTCHA_PARENT_SELECTOR} #cf-turnstile div")
                time.sleep(5)
                sb.wait_for_element_not_visible(CAPTCHA_PARENT_SELECTOR, timeout=20)
                print("✅ 备用方案验证通过！")
                return True
            except Exception as e2:
                print(f"❌ 备用方案也失败：{e2}")
                return False
    else:
        print("ℹ️ 未检测到验证弹窗，直接续期成功")
        return True

# ✅ 单次续期流程
def run_renew_once():
    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass
    
    try:
        with SB(
            uc=True,
            headless=False,
            xvfb=True,
            window_size="1920,1080",
            locale="en",
            incognito=True,
            block_images=False,
            # ✅ 核心修复3：增强反检测
            undetectable=True,
            uc_cdp_events=True
        ) as sb:
            # ✅ 核心修复4：用uc_open_with_reconnect打开页面，断开驱动
            sb.driver.uc_open_with_reconnect(TARGET_URL, reconnect_time=5)
            sb.sleep(10)
            
            print("🔍 正在查找续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    sb.click(selector, timeout=15)
                    print(f"✅ 成功点击 ADD 3 HOURS 按钮")
                    clicked = True
                    break
                except Exception:
                    continue
            
            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能找到并点击续期按钮", SCREENSHOT_PATH)
                return False
            
            # 处理g4f专属的弹窗验证
            verification_success = handle_g4f_turnstile(sb)
            if not verification_success:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：Cloudflare验证未通过", SCREENSHOT_PATH)
                return False
            
            print("👆 验证完成，等待续期结果...")
            sb.sleep(15)
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
            return True
            
    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        return False

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期（弹窗验证专属版） =====")
    print(f"⚙️ 配置：点击后等待{INITIAL_WAIT_AFTER_CLICK}秒，最多重试{MAX_RETRIES}次")
    
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            print(f"\n🔄 第 {attempt} 次重试...")
            time.sleep(10)
        
        if run_renew_once():
            print("\n===== 🛑 脚本执行成功 =====")
            sys.exit(0)
    
    print("\n❌ 所有重试均失败")
    sys.exit(1)
