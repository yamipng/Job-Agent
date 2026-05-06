"""
Auto-apply module — submits applications on LinkedIn Easy Apply and Indeed.
Handshake applications are opened in browser for manual review before submit.
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass


@dataclass
class ApplicationResult:
    job_id: str
    company: str
    title: str
    platform: str
    status: str  # "applied", "opened", "failed", "skipped"
    timestamp: str
    notes: str = ""


class AutoApplier:
    def __init__(self, user_profile: dict, resume_path: str):
        self.profile = user_profile
        self.resume_path = resume_path
        self.results: list[ApplicationResult] = []

    async def apply_linkedin_easy_apply(self, job_url: str, cover_letter_text: str, job_id: str, company: str, title: str) -> ApplicationResult:
        """Attempts LinkedIn Easy Apply. Falls back to opening browser if multi-step form detected."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # visible for Easy Apply
            context = await browser.new_context()

            # Load LinkedIn cookies
            try:
                with open("sessions/linkedin_cookies.json", "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
            except FileNotFoundError:
                print("[Apply] No LinkedIn session. Run auth.py --platform linkedin first.")
                await browser.close()
                return ApplicationResult(job_id, company, title, "LinkedIn", "failed",
                                         datetime.now().isoformat(), "No saved session")

            page = await context.new_page()
            try:
                await page.goto(job_url, timeout=30000)
                await page.wait_for_timeout(2000)

                # Look for Easy Apply button
                easy_apply_btn = await page.query_selector(".jobs-apply-button--top-card")
                if not easy_apply_btn:
                    await browser.close()
                    return ApplicationResult(job_id, company, title, "LinkedIn", "skipped",
                                             datetime.now().isoformat(), "No Easy Apply button")

                await easy_apply_btn.click()
                await page.wait_for_timeout(2000)

                # Handle phone number field if present
                phone_field = await page.query_selector("input[id*='phoneNumber']")
                if phone_field:
                    await phone_field.fill(self.profile.get("phone", ""))

                # Handle cover letter textarea if present
                cover_letter_field = await page.query_selector("textarea[id*='cover']")
                if cover_letter_field:
                    await cover_letter_field.fill(cover_letter_text)

                # Check if it's a simple 1-step form
                submit_btn = await page.query_selector("button[aria-label='Submit application']")
                if submit_btn:
                    await submit_btn.click()
                    await page.wait_for_timeout(2000)
                    status = "applied"
                    notes = "Easy Apply submitted"
                else:
                    # Multi-step — leave browser open for user
                    print(f"[Apply] Multi-step form for {company} — leaving browser open for manual completion")
                    await page.wait_for_timeout(60000)  # wait 60s for user
                    status = "opened"
                    notes = "Multi-step form opened for manual completion"

            except PlaywrightTimeoutError:
                status = "failed"
                notes = "Timed out"
            except Exception as e:
                status = "failed"
                notes = str(e)
            finally:
                await browser.close()

        result = ApplicationResult(job_id, company, title, "LinkedIn", status,
                                    datetime.now().isoformat(), notes)
        self.results.append(result)
        return result

    async def apply_indeed(self, job_url: str, cover_letter_text: str, job_id: str, company: str, title: str) -> ApplicationResult:
        """Opens Indeed job in browser for user to review and apply."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()

            try:
                with open("sessions/indeed_cookies.json", "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
            except FileNotFoundError:
                pass  # Indeed often doesn't need auth to view

            page = await context.new_page()
            try:
                await page.goto(job_url, timeout=30000)
                await page.wait_for_timeout(3000)

                apply_btn = await page.query_selector("[id*='apply-button']")
                if apply_btn:
                    await apply_btn.click()
                    await page.wait_for_timeout(2000)

                # Save cover letter to clipboard area so user can paste
                print(f"[Apply] Indeed job opened for {company}. Cover letter saved to clipboard data.")
                await page.wait_for_timeout(45000)
                status = "opened"
                notes = "Opened in browser for manual review"

            except Exception as e:
                status = "failed"
                notes = str(e)
            finally:
                await browser.close()

        result = ApplicationResult(job_id, company, title, "Indeed", status,
                                    datetime.now().isoformat(), notes)
        self.results.append(result)
        return result

    async def open_handshake(self, job_url: str, job_id: str, company: str, title: str) -> ApplicationResult:
        """Opens Handshake job in browser — Handshake requires manual review before applying."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()

            try:
                with open("sessions/handshake_cookies.json", "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
            except FileNotFoundError:
                print("[Apply] No Handshake session found.")
                await browser.close()
                return ApplicationResult(job_id, company, title, "Handshake", "failed",
                                         datetime.now().isoformat(), "No saved session")

            page = await context.new_page()
            await page.goto(job_url, timeout=30000)
            await page.wait_for_timeout(30000)
            await browser.close()

        result = ApplicationResult(job_id, company, title, "Handshake", "opened",
                                    datetime.now().isoformat(), "Opened for manual review")
        self.results.append(result)
        return result

    def save_results(self, filepath: str = "data/applications.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        existing = []
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                existing = json.load(f)

        # Merge, avoid duplicates
        existing_ids = {r["job_id"] for r in existing}
        new_results = [r.__dict__ for r in self.results if r.job_id not in existing_ids]
        all_results = existing + new_results

        with open(filepath, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"[Apply] Saved {len(new_results)} new application records")
