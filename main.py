from playwright.sync_api import sync_playwright
from utils.env_loader import load_env
from agents.gmail_agent import GmailAgent
from datetime import datetime
import json, os, time

def save_screenshot(page, label="after_action"):
    os.makedirs("screens", exist_ok=True)
    path = f"screens/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{label}.png"
    page.screenshot(path=path)
    return path

def login(page, env):
    page.goto("https://mail.google.com", wait_until="domcontentloaded")
    page.wait_for_selector("div[gh='cm']", timeout=120_000)
    page.wait_for_selector("div[role='main']", timeout=60_000)
    print("✅ Gmail session loaded via Chrome profile")

def parse_email_json(instructions: str):
    data = json.loads(instructions)
    for k in ["to", "subject", "body"]:
        if k not in data or not isinstance(data[k], str) or not data[k].strip():
            raise ValueError(f"Missing or invalid field: {k}")
    if "@" not in data["to"]:
        raise ValueError("Invalid 'to' address.")
    return data

def send_email(page, email_data):
    print("📩 Sending email:", {"to": email_data["to"], "subject": email_data["subject"]})
    try:
        page.click("div[gh='cm']", timeout=10_000)
        page.wait_for_selector("div[role='dialog']", timeout=15_000)

        # Robustly focus the To field: Gmail exposes it as a textbox with accessible name "To"
        # Prefer role-based selectors since accessible names are more stable than raw attributes.
        # Then fall back to common contenteditable/textbox patterns.
        to_locator = page.get_by_role("textbox", name="To")
        try:
            to_locator.wait_for(state="visible", timeout=7_000)
        except:
            # Fallbacks: chips container/editor Gmail uses during rollout changes
            candidates = [
                "div[aria-label='To'] div[contenteditable='true']",
                "div[aria-label='To']",
                "div[role='textbox'][aria-label='To']",
                "textarea[name='to']",
                "input[aria-label='To']",
            ]
            found = None
            for sel in candidates:
                loc = page.locator(sel)
                try:
                    loc.wait_for(state="visible", timeout=2_000)
                    found = loc
                    break
                except:
                    continue
            to_locator = found if found else to_locator

        # Ensure focus, then type the recipient
        to_locator.click()
        page.keyboard.type(email_data["to"])
        page.keyboard.press("Enter")  # create chip so subject becomes focusable

        # Subject: keep your selector, with a small wait as Gmail sometimes delays it
        page.wait_for_selector("input[name='subjectbox']", timeout=10_000)
        page.fill("input[name='subjectbox']", email_data["subject"])

        # Body: your existing logic with small resilience
        body = page.locator("div[aria-label='Message Body']").first
        if not body.count():
            body = page.locator("div[role='textbox'][aria-label]").first
        body.wait_for(state="visible", timeout=10_000)
        body.click()
        body.type(email_data["body"], delay=5)

        # Send
        # Click by role/name (handles tooltip/aria-label variations)
        # If the above fails, fall back to visible text
        page.get_by_text("Send", exact=True).click(timeout=10_000)
        page.wait_for_selector("span.bAq", timeout=10_000)


        print("✅ Email sent!")
    except Exception as e:
        print(f"⚠️ Error sending email: {e}")
        raise



if __name__ == "__main__":
    env = load_env()
    agent = GmailAgent(groq_api_key=env["GROQ_API_KEY"])

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="C:/Users/Sudharsan/AppData/Local/Google/Chrome/User Data/GmailAutomation",
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        page = browser.new_page()
        login(page, env)

        print("\nGmail Assistant is ready. Example command:")
        print("👉 Send an email to test@example.com with subject 'Hi' and body 'Hello there!'")

        try:
            while True:
                task = input("\nYour command (type 'quit' to exit): ")
                if task.lower() in ["quit", "exit"]:
                    print("Exiting Gmail Assistant…")
                    break
                instructions = agent.parse_task(task)
                print("🧠 LLM Instructions:", instructions)
                try:
                    email_data = parse_email_json(instructions)
                    send_email(page, email_data)
                except Exception as e:
                    print("⚠️ Failed to parse/send email:", e)
                path = save_screenshot(page, label="post_action")
                print(f"📸 Screenshot saved at: {path}")
        finally:
            try:
                browser.close()
            except:
                pass
