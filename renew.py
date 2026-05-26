import os
import sys
import time
import requests
from seleniumbase import SB

TARGET_URL = "https://g4f.gg/wufuyang"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

SCREENSHOT_PATH = "renew_result.png"


def send_tg(text):

    if not TG_TOKEN or not TG_CHAT_ID:
        return

    try:

        if os.path.exists(SCREENSHOT_PATH):

            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"

            with open(SCREENSHOT_PATH,"rb") as f:

                requests.post(
                    url,
                    files={"photo":f},
                    data={
                        "chat_id":TG_CHAT_ID,
                        "caption":text
                    },
                    timeout=20
                )

        else:

            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={
                    "chat_id":TG_CHAT_ID,
                    "text":text
                },
                timeout=20
            )

    except Exception as e:
        print(e)


print("===== G4F 自动续期 =====")

try:

    with SB(
        uc=True,
        headless=False,
        window_size="1920,1080"
    ) as sb:

        sb.open(TARGET_URL)

        print("等待页面加载...")
        sb.sleep(10)

        # Cloudflare检测
        try:

            page = sb.get_page_source()

            if (
                "Verify you are human" in page
                or "Cloudflare" in page
            ):

                print("发现 Cloudflare 验证")

                for i in range(180):

                    page = sb.get_page_source()

                    if "Verify you are human" not in page:

                        print("验证完成")
                        break

                    print(f"等待验证 {i+1}/180")
                    sb.sleep(1)

        except Exception:
            pass

        print("开始点击续期按钮")

        selectors = [

            "//button[contains(.,'ADD 3 HOURS')]",
            "//button[contains(.,'ADD')]"

        ]

        clicked = False

        for selector in selectors:

            try:

                sb.click(selector, timeout=20)

                clicked = True

                print("点击成功")

                break

            except Exception as e:

                print(e)

        if not clicked:

            raise Exception("找不到 ADD 3 HOURS 按钮")

        sb.sleep(15)

        sb.save_screenshot(SCREENSHOT_PATH)

        print("续期完成")

        send_tg("✅ G4F续期成功")

except Exception as e:

    print(e)

    try:
        sb.save_screenshot(SCREENSHOT_PATH)
    except:
        pass

    send_tg(f"❌ 续期失败\n{str(e)}")

    sys.exit(1)

print("===== 完成 =====")
