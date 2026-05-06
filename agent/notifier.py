"""
Email notification module — sends you a daily digest of applications sent,
and alerts when an application status changes.
Uses Gmail SMTP (app password required).
"""

import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date


class EmailNotifier:
    def __init__(self, sender_email: str, app_password: str, recipient_email: str):
        self.sender = sender_email
        self.password = app_password
        self.recipient = recipient_email

    def _send(self, subject: str, html_body: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipient, msg.as_string())
            print(f"[Email] Sent: {subject}")
        except Exception as e:
            print(f"[Email] Failed to send: {e}")

    def send_daily_digest(self, applications: list[dict]):
        today_apps = [
            a for a in applications
            if a.get("timestamp", "").startswith(date.today().isoformat())
        ]

        applied = [a for a in today_apps if a["status"] == "applied"]
        opened = [a for a in today_apps if a["status"] == "opened"]
        failed = [a for a in today_apps if a["status"] == "failed"]

        rows = ""
        for app in today_apps:
            status_color = {"applied": "#22c55e", "opened": "#f59e0b", "failed": "#ef4444"}.get(app["status"], "#6b7280")
            rows += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #1e293b;">{app['company']}</td>
                <td style="padding:8px;border-bottom:1px solid #1e293b;">{app['title']}</td>
                <td style="padding:8px;border-bottom:1px solid #1e293b;">{app['platform']}</td>
                <td style="padding:8px;border-bottom:1px solid #1e293b;color:{status_color};font-weight:600;">{app['status'].upper()}</td>
            </tr>
            """

        html = f"""
        <html><body style="background:#0f172a;color:#e2e8f0;font-family:monospace;padding:24px;">
        <h2 style="color:#38bdf8;">📋 Job Agent Daily Digest — {date.today().strftime('%B %d, %Y')}</h2>
        <div style="display:flex;gap:24px;margin-bottom:24px;">
            <div style="background:#1e293b;padding:16px;border-radius:8px;">
                <div style="font-size:28px;font-weight:700;color:#22c55e;">{len(applied)}</div>
                <div style="color:#94a3b8;">Applied</div>
            </div>
            <div style="background:#1e293b;padding:16px;border-radius:8px;">
                <div style="font-size:28px;font-weight:700;color:#f59e0b;">{len(opened)}</div>
                <div style="color:#94a3b8;">Opened</div>
            </div>
            <div style="background:#1e293b;padding:16px;border-radius:8px;">
                <div style="font-size:28px;font-weight:700;color:#ef4444;">{len(failed)}</div>
                <div style="color:#94a3b8;">Failed</div>
            </div>
        </div>
        <table style="width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;">
            <thead>
                <tr style="color:#38bdf8;text-align:left;">
                    <th style="padding:10px;">Company</th>
                    <th style="padding:10px;">Role</th>
                    <th style="padding:10px;">Platform</th>
                    <th style="padding:10px;">Status</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="color:#64748b;margin-top:24px;font-size:12px;">Sent by your Job Automation Agent · Jules Sejour</p>
        </body></html>
        """

        self._send(f"Job Agent Digest — {len(today_apps)} applications today", html)

    def send_status_alert(self, company: str, title: str, old_status: str, new_status: str):
        html = f"""
        <html><body style="background:#0f172a;color:#e2e8f0;font-family:monospace;padding:24px;">
        <h2 style="color:#38bdf8;">🔔 Application Status Update</h2>
        <div style="background:#1e293b;padding:20px;border-radius:8px;margin-top:16px;">
            <p><strong>Company:</strong> {company}</p>
            <p><strong>Role:</strong> {title}</p>
            <p><strong>Status changed:</strong>
                <span style="color:#ef4444;">{old_status.upper()}</span>
                → <span style="color:#22c55e;">{new_status.upper()}</span>
            </p>
        </div>
        </body></html>
        """
        self._send(f"Status Update: {company} — {title}", html)
