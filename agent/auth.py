"""
Auth helper — saves browser session cookies for LinkedIn, Indeed, and Handshake.
Run this ONCE per platform before using the agent.

Usage:
    python agent/auth.py --platform linkedin
    python agent/auth.py --platform indeed
    python agent/auth.py --platform handshake
"""

import asyncio
import argparse
import json
import os
from playwright.async_api import async_playwright

PLATFORM_URLS = {
    "linkedin": "https://www.linkedin.com/login",
    "indeed": "https://secure.indeed.com/auth",
    "handshake": "https://app.joinhandshake.com/login",
}

SESSION_DIR = "sessions"


async def save_session(platform: str):
    os.makedirs(SESSION_DIR, exist_ok=True)
    url = PLATFORM_URLS.get(platform)
    if not url:
        print(f"Unknown platform: {platform}")
        return

    print(f"\n[Auth] Opening {platform.capitalize()} login page...")
    print("[Auth] Log in manually in the browser. The session will be saved automatically after you're logged in.")
    print("[Auth] You have 120 seconds.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)

        # Wait for user to log in
        await page.wait_for_timeout(120000)

        cookies = await context.cookies()
        cookie_path = f"{SESSION_DIR}/{platform}_cookies.json"
        with open(cookie_path, "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"[Auth] Session saved to {cookie_path}")
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save browser session for job platforms")
    parser.add_argument("--platform", required=True, choices=["linkedin", "indeed", "handshake"],
                        help="Platform to authenticate")
    args = parser.parse_args()
    asyncio.run(save_session(args.platform))
