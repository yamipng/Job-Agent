"""
Cover letter generator powered by Claude (Anthropic API).
Customizes your base cover letter for each specific job listing.
"""

import anthropic
import json
import os
from dataclasses import dataclass


@dataclass
class CoverLetterResult:
    job_id: str
    company: str
    title: str
    cover_letter: str
    tone_used: str
    keywords_matched: list[str]


BASE_COVER_LETTER = """[DATE]

[Hiring Manager's Name]
[Hiring Manager's Job Title]
[Company Name]
[Company Address]

Dear [Hiring Manager's Name],

Dear [Company Name] Team,

I am writing to express my interest in the [Job Title] position at [Company Name]. I am graduating in May 2026 with a Bachelor of Technology in Information Technology from SUNY Cobleskill, and I am eager to bring my technical foundation, my enthusiasm for learning, and my strong work ethic to a team where I can grow and make a real contribution.

Throughout my time at SUNY Cobleskill, I have built hands-on academic experience across a range of IT disciplines including Python programming, Linux operating systems, database concepts, network security, web development, and artificial intelligence. I have also completed coursework in AI ethics, systems analysis, and project management, which has given me a broader perspective on how technology functions within organizations and teams. What excites me most right now is continuing to develop in areas like software development and modern IT workflows — I am the kind of person who genuinely enjoys picking up new skills and figuring out how things work.

I have also developed strong practical experience working with AI tools — Claude is my primary tool for research, problem-solving, and development workflows, and I use ChatGPT regularly as well. I built my personal portfolio website independently, using these tools to accelerate my learning and work through challenges in real time. I believe fluency with AI tools is increasingly valuable in any technical role, and it is something I am already putting to use every day.

Beyond my technical background, I bring several years of customer-facing work experience across multiple retail and service environments. These roles have sharpened my communication skills, taught me how to stay composed and focused under pressure, and reinforced my ability to work as part of a team.

I am reliable, I show up ready to work, and I take pride in doing things the right way.

I would love the opportunity to speak with you about how I can contribute to [Company Name]. I am open to learning whatever tools, systems, or processes your team uses, and I am genuinely excited about the possibility of starting my career in a hands-on environment.

Thank you for your time and consideration. I look forward to hearing from you soon.

Sincerely,

Jules Sejour
Email: yamijpg@proton.me
Phone: (856) 353-0412
"""


SYSTEM_PROMPT = """You are customizing a cover letter for Jules Sejour, a graduating IT student applying for internships and entry-level roles in IT Support and Web Development.

Jules's actual background (from resume):
- Bachelor of Technology, Information Technology — SUNY Cobleskill (graduating May 2026), Concentration: Information Systems, Honorable Mention Spring & Fall 2024
- A.A. Liberal Arts — Rockland Community College (2023)
- Coursework: Python, Linux OS, Windows OS, Database Concepts, Network Security, Web Development (HTML/CSS/JS), AI, AI Ethics, Systems Analysis, Project Management, System Administration
- Technical skills: Python, Linux, HTML/CSS, JavaScript, SQL, Network Security, Database Design, Version Control, IT Support Workflows, Cloud Computing, Git, Microsoft 365, JIRA, Confluence
- AI tools: Claude (primary workflow tool), ChatGPT (prompt engineering & research)
- Projects: Personal portfolio website (HTML/CSS/JS), Photography Expo Website, Job automation agent (Python/Playwright/Anthropic API)
- Work: Dollar General — Sales Associate (Aug 2025–Present), Stop & Shop — Cashier/Sales Associate (Jan 2024–Aug 2025), 7-Eleven (2021–2023), PDI NicePak — Warehouse Associate (2020–2021), ShopRite (2019–2020)
- Contact: yamijpg@proton.me | (856) 353-0412

Your task is to customize the base cover letter by:
1. Replacing [DATE] with today's date in format "Month Day, Year"
2. Replacing [Company Name] in the salutation and body with the actual company name
3. Replacing [Job Title] with the actual job title
4. Leaving [Hiring Manager's Name], [Hiring Manager's Job Title], [Company Address] as-is (user fills these manually before sending)
5. Tweaking the body paragraphs to naturally reference 2-3 keywords from the job description
6. Adjusting emphasis based on role type:
   - IT Support: highlight Linux/Windows, troubleshooting, IT support workflows, customer service composure
   - Web Dev: highlight HTML/CSS/JS, portfolio site, automation projects, Python
   - Mixed: balance both
7. Keep Jules's authentic voice — direct, genuine, not over-formal
8. Do NOT add fake experiences or skills Jules doesn't have
9. Return ONLY the final cover letter text, ready to copy-paste. No preamble or explanation.
"""


class CoverLetterAgent:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def generate(self, job_title: str, company: str, job_description: str, platform: str = "") -> CoverLetterResult:
        """Generate a customized cover letter for a specific job listing."""

        # Detect role type from title + description
        role_type = self._detect_role_type(job_title, job_description)

        from datetime import date
        today = date.today().strftime("%B %d, %Y")

        prompt = f"""Here is the job listing Jules is applying to:

Company: {company}
Job Title: {job_title}
Platform: {platform}
Today's date: {today}
Job Description:
{job_description[:3000] if job_description else "(No description provided — use the company name and job title to customize)"}

Role type detected: {role_type}

Base cover letter to customize:
{BASE_COVER_LETTER}

Customize this cover letter for this specific job. Replace all bracketed placeholders except [Hiring Manager's Name], [Hiring Manager's Job Title], and [Company Address] — leave those as-is for the user to fill in manually. Weave in 2-3 relevant keywords from the job description naturally."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        cover_letter_text = message.content[0].text
        keywords = self._extract_keywords(job_description)

        return CoverLetterResult(
            job_id=f"{company}_{job_title}".replace(" ", "_").lower()[:50],
            company=company,
            title=job_title,
            cover_letter=cover_letter_text,
            tone_used=role_type,
            keywords_matched=keywords
        )

    def _detect_role_type(self, title: str, description: str) -> str:
        title_lower = title.lower()
        desc_lower = description.lower()

        it_support_signals = ["help desk", "it support", "technical support", "desktop support",
                               "helpdesk", "service desk", "troubleshoot", "ticketing"]
        web_dev_signals = ["web developer", "frontend", "front-end", "html", "css", "javascript",
                           "react", "portfolio", "ui/ux", "full stack", "fullstack"]

        it_score = sum(1 for s in it_support_signals if s in title_lower or s in desc_lower)
        web_score = sum(1 for s in web_dev_signals if s in title_lower or s in desc_lower)

        if it_score > web_score:
            return "IT Support"
        elif web_score > it_score:
            return "Web Development"
        else:
            return "IT Support + Web Development"

    def _extract_keywords(self, description: str) -> list[str]:
        """Pull relevant tech keywords from the job description."""
        tech_keywords = [
            "python", "javascript", "html", "css", "sql", "react", "node",
            "git", "linux", "windows", "azure", "aws", "networking", "vpn",
            "active directory", "ticketing", "help desk", "troubleshooting",
            "playwright", "api", "rest", "database", "agile", "jira"
        ]
        desc_lower = description.lower()
        return [kw for kw in tech_keywords if kw in desc_lower]

    def batch_generate(self, jobs: list[dict]) -> list[CoverLetterResult]:
        """Generate cover letters for a list of job dicts."""
        results = []
        for job in jobs:
            print(f"[CoverLetter] Generating for {job.get('company')} — {job.get('title')}")
            try:
                result = self.generate(
                    job_title=job.get("title", ""),
                    company=job.get("company", ""),
                    job_description=job.get("description", ""),
                    platform=job.get("platform", "")
                )
                results.append(result)
            except Exception as e:
                print(f"[CoverLetter] Error for {job.get('company')}: {e}")
        return results

    def save_cover_letters(self, results: list[CoverLetterResult], output_dir: str = "data/cover_letters"):
        os.makedirs(output_dir, exist_ok=True)
        for result in results:
            safe_name = f"{result.company}_{result.title}".replace(" ", "_").replace("/", "-")[:60]
            filepath = f"{output_dir}/{safe_name}.txt"
            with open(filepath, "w") as f:
                f.write(f"Company: {result.company}\n")
                f.write(f"Role: {result.title}\n")
                f.write(f"Tone: {result.tone_used}\n")
                f.write(f"Keywords matched: {', '.join(result.keywords_matched)}\n")
                f.write("\n" + "="*60 + "\n\n")
                f.write(result.cover_letter)
            print(f"[CoverLetter] Saved: {filepath}")
