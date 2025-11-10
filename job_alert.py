#!/usr/bin/env python3
"""
Job Finder Automation Script
Fetches entry-level jobs using SerpApi Google Jobs engine,
filters them by role and relevance, and emails clickable links.
"""

import os
import requests
import smtplib
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil import parser as dateparser

# Load environment variables
load_dotenv()

# --- Config ---
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
EMAIL_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USERNAME")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO", EMAIL_USER)
JOB_QUERY_TERMS = os.getenv("JOB_QUERY_TERMS", "entry level Full Stack Developer;entry level AI ML engineer;Django developer").split(";")
LOCATIONS = os.getenv("LOCATIONS", "Remote;India").split(";")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 25))
MIN_DAYS_OLD = int(os.getenv("MIN_DAYS_OLD", 4))
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"

ENTRY_KEYWORDS = ["entry level", "junior", "fresher", "new grad", "0-2 years"]
AI_ML_KEYWORDS = ["machine learning", "ml engineer", "ai engineer", "deep learning"]
DJANGO_KEYWORDS = ["django", "python", "drf", "django rest"]
FULLSTACK_KEYWORDS = ["full stack", "backend", "frontend", "software engineer"]

def search_jobs(query, location):
    params = {
        "engine": "google_jobs",
        "q": f"{query} in {location}",
        "api_key": SERPAPI_KEY,
    }
    r = requests.get(SERPAPI_SEARCH_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("jobs_results", [])

def matches_interest(job):
    text = " ".join([
        job.get("title", ""),
        job.get("company_name", ""),
        job.get("description", "")
    ]).lower()
    return (
        any(k in text for k in ENTRY_KEYWORDS)
        and any(k in text for k in (AI_ML_KEYWORDS + DJANGO_KEYWORDS + FULLSTACK_KEYWORDS))
    )

def build_email_html(jobs):
    if not jobs:
        return "<p>No new relevant jobs found today.</p>"

    html_content = [
        "<h2>🚀 Job Finder Results</h2>",
        "<p>Click the job title to open the application link in your browser.</p>",
        "<ul>"
    ]

    for j in jobs:
    title = html.escape(j.get("title", "N/A"))
    company = html.escape(j.get("company_name", ""))
    location = html.escape(j.get("location", ""))
    date_posted = j.get("detected_extensions", {}).get("posted_at", "N/A")

    # Prefer real apply link, fallback to Google redirect link
    link = j.get("apply_link") or j.get("link")
    if not link or not link.startswith("http"):
        # skip empty/broken links
        continue

    safe_link = html.escape(link, quote=True)
    snippet = html.escape(j.get("description", "")[:250])

    html_content.append(f"""
    <li>
      <strong><a href="{safe_link}" target="_blank" rel="noopener noreferrer">{title}</a></strong><br/>
      <em>Company:</em> {company}<br/>
      <em>Location:</em> {location}<br/>
      <em>Posted:</em> {date_posted}<br/>
      <p>{snippet}</p><br/>
    </li>
    """)

    html_content.append("</ul>")
    return "\n".join(html_content)

def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, [EMAIL_TO], msg.as_string())

def main():
    if not SERPAPI_KEY:
        raise RuntimeError("❌ Missing SERPAPI_API_KEY in environment.")
    
    jobs_collected = []
    for query in JOB_QUERY_TERMS:
        for loc in LOCATIONS:
            try:
                results = search_jobs(query, loc)
                for j in results:
                    if matches_interest(j):
                        jobs_collected.append(j)
            except Exception as e:
                print(f"Error fetching {query} in {loc}: {e}")

    html_body = build_email_html(jobs_collected)
    subject = f"[Job Alert] {len(jobs_collected)} jobs found — {datetime.utcnow().strftime('%Y-%m-%d')}"
    send_email(subject, html_body)
    print(f"✅ Email sent with {len(jobs_collected)} job(s).")

if __name__ == "__main__":
    main()
