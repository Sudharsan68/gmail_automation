from browser_use.llm import ChatGroq
from utils.env_loader import load_env

class GmailAgent:
    def __init__(self, groq_api_key, model="meta-llama/llama-4-maverick-17b-128e-instruct"):
        self.llm = ChatGroq(model=model, api_key=groq_api_key)
        self.env = load_env()

    def login(self, page):
        """Manual Gmail login with Playwright"""
        page.goto("https://mail.google.com/")
        page.fill("input[type='email']", self.env["GMAIL_EMAIL"])
        page.click("text=Next")
        page.wait_for_timeout(2000)
        page.fill("input[type='password']", self.env["GMAIL_PASSWORD"])
        page.click("text=Next")
        page.wait_for_load_state("networkidle")

    def run_task(self, page, task: str):
        """Parse user task with LLM, then execute in browser"""
        # Step 1: Let LLM decide what action to take
        prompt = f"User wants to: {task}. Convert this into a Gmail browser action (e.g. 'compose', 'search email', 'open latest')."
        action = self.llm(prompt)

        # Step 2: Execute with Playwright
        if "compose" in action.lower():
            page.click("div[role='button'][gh='cm']")  # compose button
            return "Opened compose window"
        elif "search" in action.lower():
            search_query = task.replace("search", "").strip()
            page.fill("input[aria-label='Search mail']", search_query)
            page.press("input[aria-label='Search mail']", "Enter")
            return f"Searched for '{search_query}'"
        elif "open latest" in action.lower():
            page.click("table.F.cf.zt tr.zA")  # first email row
            return "Opened latest email"
        else:
            return f"❓ LLM action not supported yet: {action}"
