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

# ✅ 运行环境配置（非常关键！）
# 如果你在本地电脑（Windows/Mac）测试：请改为 False。它会弹出真实浏览器，让你亲眼看到破解全过程。
# 如果你在 Linux 服务器/Docker/GitHub Actions 上跑：请保持 True。它会启动虚拟桌面（Xvfb）来完美隐藏自动化痕迹。
IS_SERVER_ENVIRONMENT = True 

# 发送带截图的 Telegram 通知
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

if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (终极抗封锁双击版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try: os.remove(SCREENSHOT_PATH)
        except: pass

    try:
        # 组装高度伪装的浏览器初始化参数
        sb_args = {
            "uc": True,            # 开启 Undetected Chromedriver 反检测
            "incognito": True,     # 开启无痕模式，清除历史指纹特征
            "window_size": "1920,1080"
        }
        
        # 🔥 核心修正：坚决不用 headless/headless2，用真实窗口或 Xvfb 虚拟窗口
        if IS_SERVER_ENVIRONMENT:
            sb_args["xvfb"] = True  # Linux 服务器下开启虚拟桌面
        else:
            sb_args["headless"] = False # 本地看得到界面的真浏览器

        with SB(**sb_args) as sb:
            
            print("🌐 正在通过重连机制隐蔽打开目标网页...")
            # 🔥 换用官方标准的 uc_open_with_reconnect，开局直接斩断 Cloudflare 探测
            sb.uc_open_with_reconnect(TARGET_URL, reconnect_time=5)
            sb.sleep(8) 

            # 定义续期按钮的选择器
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]

            # ==========================================
            # 🛑 阶段一：【第一次点击】触发验证码弹出
            # ==========================================
            print("🔍 正在执行【第一次点击】，激活验证弹窗...")
            clicked_first = False
            used_selector = None
            
            for selector in selectors:
                try:
                    sb.uc_click(selector, timeout=8)
                    print(f"✅ 第一次点击成功 (选择器: {selector})")
                    clicked_first = True
                    used_selector = selector
                    break
                except Exception:
                    continue 

            if not clicked_first:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：无法定位到初始续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            sb.sleep(4) # 等待弹窗完全展开

            # ==========================================
            # 🛑 阶段二：【攻克验证】调用官方终极大招
            # ==========================================
            cf_iframe = "iframe[src*='challenges.cloudflare.com']"
            if sb.is_element_present(cf_iframe):
                print("🛡️ 警报：检测到 Cloudflare Turnstile 验证拦截！")
                
                # 优先尝试 SeleniumBase 官方专门用来击碎 CF 验证的内置核心
                try:
                    print("🤖 策略 A：正在唤醒内置 GUI 验证码绕过引擎...")
                    sb.uc_gui_handle_captcha()
                    print("✅ 策略 A 绕过引擎执行完毕")
                except Exception as e:
                    print(f"⚠️ 策略 A 失败，正在紧急切换至策略 B (Frame强穿透模式): {e}")
                    # 策略 B 保底：穿透 Iframe 强行点击
                    try:
                        sb.switch_to_frame(cf_iframe)
                        sb.sleep(1)
                        if sb.is_element_present("input[type='checkbox']"):
                            sb.uc_click("input[type='checkbox']", timeout=5)
                        else:
                            sb.uc_click("body", timeout=5)
                        sb.switch_to_default_content()
                        print("✅ 策略 B 穿透点击指令发送成功")
                    except Exception as frame_err:
                        print(f"❌ 策略 B 同样受阻: {frame_err}")
                        sb.switch_to_default_content()

                # ⚠️ 关键点：点击完验证后原地死等 15 秒，给 Cloudflare 足够时间给浏览器写入通过 Token
                print("⏳ 验证指令已下发，强行静止 15 秒等待 Token 释放与网络握手...")
                sb.sleep(15)
            else:
                print("✨ 提示：未检测到弹窗拦截，可能已被直接放行。")

            # ==========================================
            # 🛑 阶段三：【第二次点击】真正提交续期
            # ==========================================
            print("🚀 正在执行【第二次点击】，正式提交续期数据...")
            clicked_second = False
            
            # 优先使用前面成功过的那个按钮选择器
            final_selectors = [used_selector] + selectors if used_selector else selectors
            for selector in final_selectors:
                if not selector: continue
                try:
                    sb.uc_click(selector, timeout=8)
                    print(f"🎉 第二次确认点击成功！续期申请已发出。")
                    clicked_second = True
                    break
                except Exception:
                    continue

            if not clicked_second:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：通过验证后，第二次点击提交按钮失败", SCREENSHOT_PATH)
                sys.exit(1)

            print("⏳ 续期已提交，等待 12 秒让面板刷新时间...")
            sb.sleep(12)

            # 最终截图存档
            sb.save_screenshot(SCREENSHOT_PATH)

            # 抓取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 自动续期大功告成！\n当前服务器剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 脚本执行发生异常崩溃：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
