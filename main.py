from playwright.sync_api import sync_playwright
from agents.gmail_agent import GmailAgent
from utils.env_loader import load_env

if __name__ == "__main__":
    env = load_env()
    agent = GmailAgent(groq_api_key=env["GROQ_API_KEY"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,slow_mo=50)
        context = browser.new_context()
        page = context.new_page()

        print("🔑 Logging in to Gmail...")
        agent.login(page)   # ✅ pass page here
        print("✅ Logged in successfully!")

        try:
            while True:
                task = input("\nYour command (type 'quit' to exit): ")
                if task.lower() in ["quit", "exit"]:
                    print("Exiting Gmail Assistant…")
                    break
                result = agent.run_task(page, task)   # ✅ pass page here
                print("Task finished:", result)
        except Exception as e:
            print("Error:", e)
        finally:
            browser.close()
