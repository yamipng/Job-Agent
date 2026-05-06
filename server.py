"""
Flask server — serves the dashboard and exposes API endpoints
for the Python scraper + cover letter agent.

Usage:
    python server.py
    Then open http://localhost:5000 in your browser.
"""

from flask import Flask, jsonify, request, send_from_directory
import asyncio
import json
import os
from agent.scraper import JobScraper
from agent.cover_letter import CoverLetterAgent

app = Flask(__name__, static_folder="dashboard", static_url_path="")

# Load config
def load_config():
    if os.path.exists("config.json"):
        with open("config.json") as f:
            return json.load(f)
    return {}

# ─── Serve dashboard ──────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("dashboard", "index.html")

# ─── Jobs API ─────────────────────────────────────────────────
@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    if os.path.exists("data/jobs.json"):
        with open("data/jobs.json") as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route("/api/applications", methods=["GET"])
def get_applications():
    if os.path.exists("data/applications.json"):
        with open("data/applications.json") as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route("/api/applications/<job_id>", methods=["PATCH"])
def update_application_status(job_id):
    data = request.json
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    apps = []
    if os.path.exists("data/applications.json"):
        with open("data/applications.json") as f:
            apps = json.load(f)

    updated = False
    for app_record in apps:
        if app_record["job_id"] == job_id:
            app_record["status"] = new_status
            updated = True
            break

    if updated:
        with open("data/applications.json", "w") as f:
            json.dump(apps, f, indent=2)
        return jsonify({"ok": True})

    return jsonify({"error": "not found"}), 404

# ─── Scrape trigger ───────────────────────────────────────────
@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    body = request.json or {}
    keywords = body.get("keywords", "IT Support internship")
    location = body.get("location", "Remote")
    max_jobs = body.get("max", 10)

    config = load_config()
    scraper = JobScraper(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    jobs = loop.run_until_complete(scraper.scrape_all(keywords, location, max_per_platform=max_jobs))
    loop.close()

    scraper.save_results("data/jobs.json")
    return jsonify({"found": len(jobs), "jobs": [j.__dict__ for j in jobs]})

# ─── Cover letter via backend ─────────────────────────────────
@app.route("/api/cover-letter", methods=["POST"])
def generate_cover_letter():
    body = request.json or {}
    config = load_config()
    agent = CoverLetterAgent(api_key=config.get("anthropic_api_key"))

    result = agent.generate(
        job_title=body.get("title", ""),
        company=body.get("company", ""),
        job_description=body.get("description", ""),
        platform=body.get("platform", "")
    )

    return jsonify({
        "cover_letter": result.cover_letter,
        "tone": result.tone_used,
        "keywords": result.keywords_matched
    })

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("sessions", exist_ok=True)
    print("\n[Server] Dashboard running at http://localhost:5000\n")
    app.run(debug=True, port=5000)
