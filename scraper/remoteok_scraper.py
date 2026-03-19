import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
URL = "https://remoteok.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
OUTPUT_FOLDER = "raw_data"

# ─────────────────────────────────────────
# STEP 1 — FETCH DATA FROM REMOTEOK API
# ─────────────────────────────────────────
def fetch_jobs():
    print("Fetching jobs from RemoteOK...")
    response = requests.get(URL, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        # First item is always a legal notice, skip it
        jobs = [job for job in data if isinstance(job, dict) and "position" in job]
        print(f"Found {len(jobs)} jobs!")
        return jobs
    else:
        print(f"Failed to fetch. Status code: {response.status_code}")
        return []

# ─────────────────────────────────────────
# STEP 2 — CLEAN THE DATA
# ─────────────────────────────────────────
def clean_jobs(jobs):
    print("Cleaning data...")
    cleaned = []

    for job in jobs:
        cleaned.append({
            "title":       job.get("position", "N/A"),
            "company":     job.get("company", "N/A"),
            "location":    job.get("location", "Remote"),
            "tags":        job.get("tags", []),
            "salary_min":  job.get("salary_min", None),
            "salary_max":  job.get("salary_max", None),
            "job_url":     f"https://remoteok.com/remote-jobs/{job.get('slug', '')}",
            "posted_date": job.get("date", "N/A"),
            "source":      "remoteok",
            "scraped_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    print(f"Cleaned {len(cleaned)} jobs!")
    return cleaned

# ─────────────────────────────────────────
# STEP 3 — SAVE TO JSON FILE
# ─────────────────────────────────────────
def save_jobs(jobs):
    # Create raw_data folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Save with today's date in filename
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{OUTPUT_FOLDER}/remoteok_{today}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(jobs)} jobs to {filename}")
    return filename

# ─────────────────────────────────────────
# MAIN — RUN EVERYTHING
# ─────────────────────────────────────────
if __name__ == "__main__":
    jobs       = fetch_jobs()
    clean      = clean_jobs(jobs)
    saved_file = save_jobs(clean)

    print("\n--- SAMPLE JOB ---")
    if clean:
        print(json.dumps(clean[0], indent=2))