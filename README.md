# 🤖 Job Automation Agent

A full-stack job application automation tool that scrapes internship and entry-level listings from **LinkedIn**, **Indeed**, and **Handshake**, generates **AI-customized cover letters** via the Anthropic Claude API, and tracks all applications in a **Kanban-style dashboard**.

Built by Jules Sejour — IT & Web Development student, SUNY Cobleskill (graduating May 2026).

---

## Features

- **Multi-platform scraping** — LinkedIn, Indeed, and Handshake via Playwright browser automation
- **AI cover letter generation** — Claude detects the role type (IT Support vs Web Dev) and customizes each letter to the company, job description, and keywords
- **Auto-apply** — LinkedIn Easy Apply automation; Indeed and Handshake open in browser for review
- **Kanban dashboard** — drag-and-drop pipeline: Found → Applied → Interview → Rejected
- **Email digest** — daily summary of applications sent via Gmail SMTP
- **Flask API** — Python backend serves the dashboard and exposes REST endpoints
- **Session-based auth** — save browser sessions once with `auth.py`, reuse them across runs

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Scraping / Automation | Python, Playwright |
| AI | Anthropic Claude API (claude-sonnet) |
| Backend | Flask |
| Frontend | Vanilla HTML/CSS/JS |
| Email | smtplib (Gmail SMTP) |
| Storage | JSON flat files |

---

## Project Structure

```
job-agent/
├── agent/
│   ├── scraper.py          # LinkedIn, Indeed, Handshake scrapers
│   ├── cover_letter.py     # AI cover letter generator
│   ├── applier.py          # Auto-apply via Playwright
│   ├── notifier.py         # Email digest
│   └── auth.py             # Save browser sessions
├── dashboard/
│   └── index.html          # Kanban dashboard + in-browser cover letter generator
├── data/                   # Generated at runtime (gitignored)
├── sessions/               # Browser cookies (gitignored)
├── server.py               # Flask server
├── main.py                 # CLI runner
├── config.example.json     # Config template
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp config.example.json config.json
```

Edit `config.json` with your Anthropic API key, email settings, and profile info.

### 3. Authenticate platforms (one-time)

```bash
python agent/auth.py --platform linkedin
python agent/auth.py --platform indeed
python agent/auth.py --platform handshake
```

A browser will open — log in manually. Your session is saved automatically.

### 4. Run

**Dashboard (recommended):**
```bash
python server.py
# Open http://localhost:5000
```

**CLI:**
```bash
python main.py --keywords "IT Support intern" --location "Remote" --max 10
python main.py --dry-run   # scrape only, no applications
```

---

## Dashboard

Open `dashboard/index.html` directly in a browser for the standalone frontend (uses Anthropic API directly from the browser for cover letter generation).

The full-stack version via `server.py` adds scraping and auto-apply through the Python backend.

---

## Notes

- **Handshake** requires a university SSO login. Run `auth.py --platform handshake` from your campus network or VPN if needed.
- **LinkedIn Easy Apply** is automated. Multi-step applications open in a browser for manual completion.
- Sessions are stored in `sessions/` — this folder is gitignored. Never commit your cookies.
- `config.json` is gitignored. Never commit your API keys.

---

## License

MIT — free to use and adapt.
