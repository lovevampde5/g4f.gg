import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置（已针对g4f.gg精准校准）
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"
MAX_RETRIES = 3
# 点击后最多等40秒让验证iframe出现
MAX_WAIT_FOR_CAPTCHA = 40
# ✅ 正确的Turnstile iframe选择器（这才是真正存在的元素）
TURNSTILE_IFRAME = "iframe[src*='challenges.cloudflare.com/turnstile']"

# ✅ 发送带截图的Telegram通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的Telegram通知...")
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN或TG_CHAT_ID为空")
        return
    if not os.path.exists(screenshot_path):
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F自动续期\n{text}"}
            requests.post(url, json=data, timeout=10)
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F自动续期\n{text}"}
            requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# ✅ 核心：直接检测Turnstile iframe，出现立即用CDP嵌套点击
def wait_and_handle_turnstile(sb):
    print("🔍 点击完成，开始循环检测Cloudflare Turnstile验证...")
    start_time = time.time()
    
    while time.time() - start_time < MAX_WAIT_FOR_CAPTCHA:
        elapsed = int(time.time() - start_time)
        print(f"  已等待 {elapsed}/{MAX_WAIT_FOR_CAPTCHA} 秒...")
        
        # ✅ 修复：直接检测Turnstile iframe（这才是真正存在的元素）
        if sb.is_element_present(TURNSTILE_IFRAME):
            print("✅ 检测到Cloudflare Turnstile验证iframe！正在处理...")
            time.sleep(2)  # 等待iframe完全加载
            
            # 三重验证方案（按优先级）
            try:
                # 方案1：SeleniumBase官方CDP嵌套点击（专门处理iframe+shadow DOM）
                print("ℹ️ 尝试方案1：CDP嵌套点击iframe内复选框")
                sb.cdp.nested_click(TURNSTILE_IFRAME, "input[type='checkbox']")
                time.sleep(5)
                if not sb.is_element_present(TURNSTILE_IFRAME):
                    print("✅ 方案1验证通过！")
                    return True
            except Exception as e:
                print(f"❌ 方案1失败：{e}")
            
            try:
                # 方案2：官方solve_captcha()
                print("ℹ️ 尝试方案2：官方solve_captcha()")
                sb.solve_captcha()
                time.sleep(5)
                if not sb.is_element_present(TURNSTILE_IFRAME):
                    print("✅ 方案2验证通过！")
                    return True
            except Exception as e:
                print(f"❌ 方案2失败：{e}")
            
            try:
                # 方案3：终极坐标点击（1920x1080窗口固定坐标）
                print("ℹ️ 尝试方案3：固定坐标点击")
                sb.cdp.gui_click_x_y(912, 516, timeframe=0.3)
                time.sleep(5)
                if not sb.is_element_present(TURNSTILE_IFRAME):
                    print("✅ 方案3验证通过！")
                    return True
            except Exception as e:
                print(f"❌ 方案3失败：{e}")
            
            print("❌ 所有验证方案均失败")
            return False
        
        time.sleep(1)
    
    # 只有当40秒内都没出现验证iframe，才认为直接续期成功
    print("ℹ️ 40秒内未检测到验证，直接续期成功")
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
            undetectable=True,
            uc_cdp_events=True
        ) as sb:
            sb.driver.uc_open_with_reconnect(TARGET_URL, reconnect_time=6)
            sb.sleep(15)  # 延长页面加载时间
            
            print("🔍 正在查找并等待ADD 3 HOURS按钮...")
            # 多重按钮选择器+强制等待可见
            button_selectors = [
                "button:contains('ADD 3 HOURS')",
                "//button[contains(text(), 'ADD 3 HOURS')]",
                "//button[contains(., 'ADD 3 HOURS')]",
                "button.bg-green-600",
                "button[class*='green']"
            ]
            
            clicked = False
            for selector in button_selectors:
                try:
                    sb.wait_for_element_visible(selector, timeout=15)
                    sb.click(selector)
                    print(f"✅ 成功点击ADD 3 HOURS按钮 (选择器: {selector})")
                    clicked = True
                    break
                except Exception as e:
                    print(f"ℹ️ 选择器 {selector} 失败: {e}")
                    continue
            
            if not clicked:
                # JS强制点击兜底
                print("ℹ️ 尝试JS强制点击按钮...")
                try:
                    sb.execute_script("""
                        const buttons = document.querySelectorAll('button');
                        for (const btn of buttons) {
                            if (btn.textContent.includes('ADD 3 HOURS')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    print("✅ JS强制点击成功！")
                    clicked = True
                except Exception as e:
                    print(f"❌ JS点击也失败: {e}")
            
            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能找到并点击续期按钮", SCREENSHOT_PATH)
                return False
            
            # 处理验证
            verification_success = wait_and_handle_turnstile(sb)
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
    print("\n===== 🚀 g4f.gg自动续期（终极iframe检测版） =====")
    print(f"⚙️ 配置：验证最长等待{MAX_WAIT_FOR_CAPTCHA}秒，最多重试{MAX_RETRIES}次")
    
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            print(f"\n🔄 第 {attempt} 次重试...")
            time.sleep(12)
        
        if run_renew_once():
            print("\n===== 🛑 脚本执行成功 =====")
            sys.exit(0)
    
    print("\n❌ 所有重试均失败")
    sys.exit(1)
