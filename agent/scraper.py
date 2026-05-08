"""
Job scraper module for LinkedIn, Indeed, and Handshake.
Uses Playwright for browser automation.
Runs in non-headless (visible) mode to bypass bot detection.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass, asdict


@dataclass
class JobListing:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    platform: str
    date_found: str
    job_type: str = "Unknown"
    salary: str = "Not listed"
    status: str = "found"


class JobScraper:
    def __init__(self, config: dict):
        self.config = config
        self.results: list[JobListing] = []

    async def scrape_linkedin(self, keywords: str, location: str, max_jobs: int = 50) -> list[JobListing]:
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=50)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            try:
                # Load saved session
                try:
                    with open("sessions/linkedin_cookies.json", "r") as f:
                        cookies = json.load(f)
                        await context.add_cookies(cookies)
                    print("[LinkedIn] Session loaded.")
                except FileNotFoundError:
                    print("[LinkedIn] No saved session. Run auth.py --platform linkedin first.")
                    await browser.close()
                    return jobs

                search_url = (
                    f"https://www.linkedin.com/jobs/search/"
                    f"?keywords={keywords.replace(' ', '%20')}"
                    f"&location={location.replace(' ', '%20')}"
                    f"&f_TP=1%2C2&f_JT=I%2CF"
                )
                print(f"[LinkedIn] Loading search page...")
                await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

                # Wait for job cards to appear in DOM
                print("[LinkedIn] Waiting for job cards to load...")
                try:
                    await page.wait_for_selector(".job-search-card", timeout=15000)
                except PlaywrightTimeoutError:
                    print("[LinkedIn] Job cards did not appear — session may have expired. Re-run auth.py.")
                    await browser.close()
                    return jobs

                # Extra wait to make sure all cards render
                await page.wait_for_timeout(2000)

                job_cards = await page.query_selector_all(".job-search-card")
                print(f"[LinkedIn] Found {len(job_cards)} job cards")

                for i, card in enumerate(job_cards[:max_jobs]):
                    try:
                        title_el    = await card.query_selector(".base-search-card__title")
                        company_el  = await card.query_selector(".base-search-card__subtitle")
                        location_el = await card.query_selector(".job-search-card__location")
                        link_el     = await card.query_selector("a.base-card__full-link")

                        title         = await title_el.inner_text()    if title_el    else "Unknown"
                        company       = await company_el.inner_text()  if company_el  else "Unknown"
                        location_text = await location_el.inner_text() if location_el else location
                        url           = await link_el.get_attribute("href") if link_el else ""

                        description = ""
                        if url:
                            try:
                                detail_page = await context.new_page()
                                await detail_page.goto(url, timeout=30000, wait_until="domcontentloaded")
                                await detail_page.wait_for_timeout(2000)
                                desc_el = await detail_page.query_selector(".show-more-less-html__markup")
                                if desc_el:
                                    description = await desc_el.inner_text()
                                await detail_page.close()
                            except Exception as e:
                                description = "Description unavailable"

                        jobs.append(JobListing(
                            id=f"linkedin_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            title=title.strip(),
                            company=company.strip(),
                            location=location_text.strip(),
                            description=description[:2000],
                            url=url,
                            platform="LinkedIn",
                            date_found=datetime.now().isoformat(),
                        ))
                        print(f"[LinkedIn] {i+1}. {title.strip()} @ {company.strip()}")
                    except Exception as e:
                        print(f"[LinkedIn] Error parsing card {i}: {e}")
                        continue

            except PlaywrightTimeoutError:
                print("[LinkedIn] Page load timed out")
            except Exception as e:
                print(f"[LinkedIn] Unexpected error: {e}")
            finally:
                await browser.close()

        print(f"[LinkedIn] Done — {len(jobs)} jobs scraped")
        return jobs

    async def scrape_indeed(self, keywords: str, location: str, max_jobs: int = 50) -> list[JobListing]:
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=50)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            try:
                try:
                    with open("sessions/indeed_cookies.json", "r") as f:
                        cookies = json.load(f)
                        await context.add_cookies(cookies)
                except FileNotFoundError:
                    pass

                search_url = (
                    f"https://www.indeed.com/jobs?q={keywords.replace(' ', '+')}"
                    f"&l={location.replace(' ', '+')}&jt=internship"
                )
                print(f"[Indeed] Loading search page...")
                await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

                print("[Indeed] Waiting for job cards...")
                try:
                    await page.wait_for_selector(".job_seen_beacon", timeout=15000)
                except PlaywrightTimeoutError:
                    print("[Indeed] Job cards did not appear.")
                    await browser.close()
                    return jobs

                await page.wait_for_timeout(2000)

                job_cards = await page.query_selector_all(".job_seen_beacon")
                print(f"[Indeed] Found {len(job_cards)} job cards")

                for i, card in enumerate(job_cards[:max_jobs]):
                    try:
                        title_el    = await card.query_selector("[data-testid='jobTitle'] span")
                        company_el  = await card.query_selector("[data-testid='company-name']")
                        location_el = await card.query_selector("[data-testid='text-location']")
                        link_el     = await card.query_selector("a[data-jk]")

                        title         = await title_el.inner_text()    if title_el    else "Unknown"
                        company       = await company_el.inner_text()  if company_el  else "Unknown"
                        location_text = await location_el.inner_text() if location_el else location
                        job_id        = await link_el.get_attribute("data-jk") if link_el else str(i)
                        url           = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else ""

                        jobs.append(JobListing(
                            id=f"indeed_{job_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            title=title.strip(),
                            company=company.strip(),
                            location=location_text.strip(),
                            description="",
                            url=url,
                            platform="Indeed",
                            date_found=datetime.now().isoformat(),
                        ))
                        print(f"[Indeed] {i+1}. {title.strip()} @ {company.strip()}")
                    except Exception as e:
                        print(f"[Indeed] Error parsing card {i}: {e}")
                        continue

            except PlaywrightTimeoutError:
                print("[Indeed] Page load timed out")
            except Exception as e:
                print(f"[Indeed] Unexpected error: {e}")
            finally:
                await browser.close()

        print(f"[Indeed] Done — {len(jobs)} jobs scraped")
        return jobs

    async def scrape_handshake(self, keywords: str, max_jobs: int = 50) -> list[JobListing]:
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=50)
            context = await browser.new_context()

            try:
                with open("sessions/handshake_cookies.json", "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                print("[Handshake] Session loaded.")
            except FileNotFoundError:
                print("[Handshake] No saved session. Run auth.py first.")
                await browser.close()
                return jobs

            page = await context.new_page()
            try:
                search_url = f"https://app.joinhandshake.com/stu/postings?search={keywords.replace(' ', '+')}&job_type=internship"
                print(f"[Handshake] Loading search page...")
                await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

                print("[Handshake] Waiting for job cards...")
                try:
                    await page.wait_for_selector("[data-hook='job-card']", timeout=15000)
                except PlaywrightTimeoutError:
                    print("[Handshake] Job cards did not appear — session may have expired.")
                    await browser.close()
                    return jobs

                await page.wait_for_timeout(2000)

                job_cards = await page.query_selector_all("[data-hook='job-card']")
                print(f"[Handshake] Found {len(job_cards)} job cards")

                for i, card in enumerate(job_cards[:max_jobs]):
                    try:
                        title_el    = await card.query_selector("[data-hook='job-title']")
                        company_el  = await card.query_selector("[data-hook='employer-name']")
                        location_el = await card.query_selector("[data-hook='job-location']")
                        link_el     = await card.query_selector("a")

                        title         = await title_el.inner_text()    if title_el    else "Unknown"
                        company       = await company_el.inner_text()  if company_el  else "Unknown"
                        location_text = await location_el.inner_text() if location_el else "Remote/On-site"
                        href          = await link_el.get_attribute("href") if link_el else ""
                        url           = f"https://app.joinhandshake.com{href}" if href.startswith("/") else href

                        jobs.append(JobListing(
                            id=f"handshake_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            title=title.strip(),
                            company=company.strip(),
                            location=location_text.strip(),
                            description="",
                            url=url,
                            platform="Handshake",
                            date_found=datetime.now().isoformat(),
                        ))
                        print(f"[Handshake] {i+1}. {title.strip()} @ {company.strip()}")
                    except Exception as e:
                        print(f"[Handshake] Error parsing card {i}: {e}")
                        continue

            except PlaywrightTimeoutError:
                print("[Handshake] Page load timed out")
            except Exception as e:
                print(f"[Handshake] Unexpected error: {e}")
            finally:
                await browser.close()

        print(f"[Handshake] Done — {len(jobs)} jobs scraped")
        return jobs

    async def scrape_all(self, keywords: str, locations: list[str] = None, max_per_platform: int = 50) -> list[JobListing]:
        if locations is None:
            locations = ["Remote"]

        all_jobs = []
        seen_urls: set[str] = set()

        for location in locations:
            print(f"\n[Agent] Scraping: '{keywords}' in '{location}'")
            for coro in [
                self.scrape_linkedin(keywords, location, max_per_platform),
                self.scrape_indeed(keywords, location, max_per_platform),
                self.scrape_handshake(keywords, max_per_platform),
            ]:
                try:
                    result = await coro
                    for job in result:
                        key = job.url if job.url else f"{job.company}_{job.title}"
                        if key not in seen_urls:
                            seen_urls.add(key)
                            all_jobs.append(job)
                except Exception as e:
                    print(f"[Agent] Platform error: {e}")

        self.results = all_jobs
        print(f"\n[Agent] Found {len(all_jobs)} unique jobs across {len(locations)} location(s)")
        return all_jobs

    def save_results(self, filepath: str = "data/jobs.json"):
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump([asdict(job) for job in self.results], f, indent=2)
        print(f"[Agent] Saved {len(self.results)} jobs to {filepath}")
