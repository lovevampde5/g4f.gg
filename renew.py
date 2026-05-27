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

def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送 Telegram 通知...")
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

def parse_time_to_seconds(time_str):
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (Iframe 穿透版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try: os.remove(SCREENSHOT_PATH)
        except: pass

    try:
        with SB(uc=True, test=True, locale_code="en", window_size="1920,1080") as sb:
            sb.uc_open_with_reconnect(TARGET_URL, 10)
            sb.sleep(6)
            sb.maximize_window()

            # 1. 记录点击前的初始时间
            time_before_str = "无法获取"
            time_before_secs = 0
            try:
                time_before_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_before_secs = parse_time_to_seconds(time_before_str)
                print(f"⏱️ 点击前服务器剩余时间: {time_before_str}")
            except Exception as e:
                print(f"⚠️ 无法读取初始时间: {e}")

            print("🔍 正在定位续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            target_selector = None
            for selector in selectors:
                if sb.is_element_visible(selector):
                    target_selector = selector
                    break

            if not target_selector:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能定位到续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print(f"🎯 发现目标按钮，正在滚动并聚焦...")
            sb.scroll_to_element(target_selector)
            sb.sleep(2)

            print("👇 触发标准点击...")
            sb.click(target_selector) 
            sb.sleep(3)

            # 如果没动静，用 JS 强补一刀
            if not sb.is_text_visible("VERIFY YOU'RE HUMAN") and not ("hours added" in sb.get_page_source().lower()):
                print("⚠️ 标准点击未响应，改用 JavaScript 强行注入点击...")
                sb.js_click(target_selector)
                sb.sleep(3)

            # ✨ 2. 核心升级：强力攻克 Cloudflare Turnstile 验证框
            cf_iframe_selector = "iframe[src*='challenges.cloudflare.com']"
            
            if sb.is_element_visible(cf_iframe_selector) or sb.is_text_visible("VERIFY YOU'RE HUMAN"):
                print("⚠️ [检测成功] 发现 Cloudflare Turnstile 验证弹窗，启动精准穿透攻坚...")
                
                # ─── 突破策略 A：切入 Iframe 内部直接点击核心微件 ───
                try:
                    print("🔄 [策略 A] 正在将视口切换至 Cloudflare 内部空间...")
                    sb.wait_for_element(cf_iframe_selector, timeout=5)
                    sb.switch_to_frame(cf_iframe_selector) # 穿透进入 Iframe
                    sb.sleep(1.5)
                    
                    # Turnstile 内部复选框可能使用的复合选择器
                    inner_selectors = [
                        "#challenge-stage", 
                        "input[type='checkbox']", 
                        ".ct-checkbox-label", 
                        "span.mark",
                        "label.cb-lb"
                    ]
                    
                    for inner_sel in inner_selectors:
                        try:
                            if sb.is_element_visible(inner_sel):
                                print(f"🎯 找到验证核心组件: {inner_sel}，正在执行深层点击...")
                                sb.click(inner_sel)
                                sb.sleep(1)
                                break
                        except:
                            continue
                    
                    # 无论成功与否，必须切回主页面顶层
                    sb.switch_to_default_content()
                    print("🚀 已从内部空间返回主页面，等待验证结果流转...")
                    sb.sleep(6)
                except Exception as iframe_err:
                    print(f"ℹ️ 策略 A 运行异常 (可能已自动跳过): {iframe_err}")
                    sb.switch_to_default_content()

                # ─── 突破策略 B：如果弹窗还在，启用原本的 GUI 盲点作为终极兜底 ───
                if sb.is_element_visible(cf_iframe_selector):
                    print("🔄 [策略 B] 弹窗依然存在，启动系统级 GUI 模拟点击轰炸...")
                    for i in range(2):
                        sb.uc_gui_click_captcha()
                        sb.sleep(5)
                        if not sb.is_element_visible(cf_iframe_selector):
                            print("🎉 弹窗消失，兜底策略生效！")
                            break
            else:
                print("ℹ️ 未检测到验证码阻挡，可能已直接通过。")

            print("⏳ 预留缓冲时间，等待服务器刷新数据...")
            sb.sleep(8)
            sb.save_screenshot(SCREENSHOT_PATH)

            # 3. 记录点击后的时间并严格比对
            time_after_str = "无法获取"
            time_after_secs = 0
            try:
                time_after_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_after_secs = parse_time_to_seconds(time_after_str)
                print(f"⏱️ 点击后服务器剩余时间: {time_after_str}")
            except:
                pass

            page_source = sb.get_page_source().lower()
            has_success_toast = "hours added" in page_source or "已延长" in page_source
            time_increased = (time_after_secs - time_before_secs) > 3600 

            if has_success_toast or time_increased:
                success_msg = f"✅ 续期成功！验证码已完美击破！\n当前剩余时间：{time_after_str}"
                print(f"\n🎉 {success_msg}")
                send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)
            else:
                fail_msg = f"❌ 续期失败：虽然成功呼出了验证码，但最终未能通过校验。\n点击前: {time_before_str}\n点击后: {time_after_str}"
                print(f"\n{fail_msg}")
                send_tg_with_screenshot(fail_msg, SCREENSHOT_PATH)
                sys.exit(1)

    except Exception as e:
        error_msg = f"❌ 💥 脚本运行异常：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
