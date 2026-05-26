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
    print("\n===== 🚀 g4f.gg 自动续期 (双击破盾版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 🔥 核心修正 1：必须开启 uc=True。
        # 坚决不用旧的 headless=True（会泄露特征），改用混淆能力极强的 headless2=True。
        # 如果是在服务器（Linux）上跑，强烈建议把 headless2=True 换成 xvfb=True。
        with SB(uc=True, headless2=True, window_size="1920,1080") as sb:
            
            print("🌐 正在通过反检测通道打开网页...")
            sb.uc_open_with_disconnect(TARGET_URL) 
            sb.sleep(12)  # 给足页面初始加载时间

            # 你的原生选择器，保留使用
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            # ==========================================
            # 🛑 阶段一：【第一次点击】—— 触发验证弹窗
            # ==========================================
            print("🔍 正在执行【第一次点击】以唤醒 Cloudflare 验证...")
            clicked_first = False
            used_selector = None
            
            for selector in selectors:
                try:
                    # 使用 uc_click 模拟无痕原生点击，防止点击瞬间被拉黑
                    sb.uc_click(selector, timeout=10)
                    print(f"✅ 第一次点击成功 (选择器: {selector})")
                    clicked_first = True
                    used_selector = selector # 记录下成功的选择器，一会儿第二次点击直接用
                    break
                except Exception:
                    continue 

            if not clicked_first:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能定位并完成初次点击", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已触发点击，等待 5 秒让 Cloudflare 验证码弹窗完全加载...")
            sb.sleep(5)

            # ==========================================
            # 🛑 阶段二：【穿透验证】—— 搞定弹窗内的真实人验证
            # ==========================================
            cf_iframe = "iframe[src*='challenges.cloudflare.com']"
            if sb.is_element_present(cf_iframe):
                print("🛡️ 警报：检测到 Cloudflare Turnstile 验证框！开始穿透...")
                
                # 1. 潜入验证码所在的 iframe 内部上下文
                sb.switch_to_frame(cf_iframe)
                sb.sleep(1.5)
                
                # 2. 尝试无痕点击复选框
                try:
                    print("🔘 尝试点击验证复选框...")
                    sb.uc_click("input[type='checkbox']", timeout=5)
                except Exception:
                    try:
                        sb.uc_click("#challenge-stage", timeout=5)
                    except Exception:
                        sb.uc_click("body", timeout=5) # 保底策略：直接敲击验证框主体
                
                # 3. 🔥 关键：点击完必须立刻爬回最外层主页面，否则接下来的点击会找不到元素
                sb.switch_to_default_content()
                
                # 4. 原地死等 12 秒，给 Cloudflare 足够的时间在后台写入放行 Token
                print("⏳ 验证点击完成，原地静止 12 秒等待 Token 释放...")
                sb.sleep(12)
            else:
                print("✨ 提示：未检测到弹窗验证，可能已被系统直接放行。")

            # ==========================================
            # 🛑 阶段三：【第二次点击】—— 再次点击续期按钮，真正成功
            # ==========================================
            print("🚀 正在执行【第二次点击】进行最终续期确认...")
            clicked_second = False
            
            # 优先使用第一阶段成功过的选择器
            final_selectors = [used_selector] + selectors if used_selector else selectors
            for selector in final_selectors:
                if not selector: continue
                try:
                    sb.uc_click(selector, timeout=10)
                    print(f"🎉 第二次确认点击成功！续期指令已正式提交。")
                    clicked_second = True
                    break
                except Exception:
                    continue

            if not clicked_second:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：通过验证后，第二次确认点击失败", SCREENSHOT_PATH)
                sys.exit(1)

            print("⏳ 提交成功，等待 10 秒让面板刷新剩余时间...")
            sb.sleep(10)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 续期成功！\n最新剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
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
