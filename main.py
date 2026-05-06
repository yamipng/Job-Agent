"""
Job Automation Agent — Main Runner
===================================
Runs the full pipeline:
1. Scrape jobs from LinkedIn, Indeed, Handshake
2. Generate custom cover letters via Claude API
3. Auto-apply or open jobs in browser
4. Save results and send email digest

Usage:
    python main.py                        # Run with defaults from config.json
    python main.py --keywords "IT Support" --location "Remote" --max 10
    python main.py --dry-run              # Scrape only, no applications sent
"""

import asyncio
import argparse
import json
import os
from agent.scraper import JobScraper
from agent.cover_letter import CoverLetterAgent
from agent.applier import AutoApplier
from agent.notifier import EmailNotifier


def load_config(path: str = "config.json") -> dict:
    if not os.path.exists(path):
        print(f"[Main] config.json not found. Copy config.example.json to config.json and fill it in.")
        exit(1)
    with open(path) as f:
        return json.load(f)


async def run(keywords: str, location: str, max_jobs: int, dry_run: bool, config: dict):
    print("\n" + "="*60)
    print("  JOB AUTOMATION AGENT — Jules Sejour")
    print("="*60 + "\n")

    # 1. Scrape
    scraper = JobScraper(config)
    jobs = await scraper.scrape_all(keywords, location, max_per_platform=max_jobs)

    if not jobs:
        print("[Main] No jobs found. Try different keywords or check your sessions.")
        return

    scraper.save_results("data/jobs.json")

    if dry_run:
        print(f"\n[Main] Dry run complete. Found {len(jobs)} jobs. No applications sent.")
        return

    # 2. Generate cover letters
    cl_agent = CoverLetterAgent(api_key=config.get("anthropic_api_key"))
    cl_results = cl_agent.batch_generate([j.__dict__ for j in jobs])
    cl_agent.save_cover_letters(cl_results)

    # Map cover letters by company+title for lookup
    cl_map = {(r.company, r.title): r.cover_letter for r in cl_results}

    # 3. Apply
    user_profile = config.get("user_profile", {})
    resume_path = config.get("resume_path", "")
    applier = AutoApplier(user_profile, resume_path)

    for job in jobs:
        cover_letter = cl_map.get((job.company, job.title), "")
        if job.platform == "LinkedIn":
            await applier.apply_linkedin_easy_apply(
                job.url, cover_letter, job.id, job.company, job.title
            )
        elif job.platform == "Indeed":
            await applier.apply_indeed(
                job.url, cover_letter, job.id, job.company, job.title
            )
        elif job.platform == "Handshake":
            await applier.open_handshake(job.url, job.id, job.company, job.title)

        # Small delay between applications
        await asyncio.sleep(2)

    applier.save_results("data/applications.json")

    # 4. Email digest
    if config.get("email_notifications", {}).get("enabled"):
        email_cfg = config["email_notifications"]
        notifier = EmailNotifier(
            sender_email=email_cfg["sender"],
            app_password=email_cfg["app_password"],
            recipient_email=email_cfg["recipient"]
        )
        with open("data/applications.json") as f:
            all_apps = json.load(f)
        notifier.send_daily_digest(all_apps)

    print(f"\n[Main] Done. {len(applier.results)} applications processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Automation Agent")
    parser.add_argument("--keywords", default=None, help="Job search keywords")
    parser.add_argument("--location", default=None, help="Job location (e.g., 'Remote', 'New York')")
    parser.add_argument("--max", type=int, default=None, help="Max jobs per platform")
    parser.add_argument("--dry-run", action="store_true", help="Scrape only, don't apply")
    args = parser.parse_args()

    config = load_config()
    keywords = args.keywords or config.get("default_keywords", "IT Support internship")
    location = args.location or config.get("default_location", "Remote")
    max_jobs = args.max or config.get("max_jobs_per_platform", 10)

    asyncio.run(run(keywords, location, max_jobs, args.dry_run, config))
