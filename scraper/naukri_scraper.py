import requests
import json
import os
from datetime import datetime

OUTPUT_FOLDER = "raw_data"

# ─────────────────────────────────────────
# Arbeitnow — Free API, no key needed
# ─────────────────────────────────────────
def scrape_arbeitnow():
    print("Fetching jobs from Arbeitnow API...")
    all_jobs = []

    for page in range(1, 6):
        url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            jobs = data.get("data", [])
            print(f"  Page {page} — {len(jobs)} jobs")

            for job in jobs:
                all_jobs.append({
                    "title":       job.get("title", "N/A"),
                    "company":     job.get("company_name", "N/A"),
                    "location":    job.get("location", "Remote"),
                    "tags":        job.get("tags", []),
                    "salary_min":  None,
                    "salary_max":  None,
                    "job_url":     job.get("url", "N/A"),
                    "posted_date": job.get("created_at", "N/A"),
                    "source":      "arbeitnow",
                    "scraped_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        else:
            print(f"  Page {page} failed — stopping")
            break

    return all_jobs

# ─────────────────────────────────────────
# Save to JSON
# ─────────────────────────────────────────
def save_jobs(jobs):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    today    = datetime.now().strftime("%Y-%m-%d")
    filename = f"{OUTPUT_FOLDER}/arbeitnow_{today}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(jobs)} jobs to {filename}")
    return filename

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("   ARBEITNOW JOB SCRAPER")
    print("=" * 50)
    jobs = scrape_arbeitnow()
    save_jobs(jobs)
    print(f"\nDone! {len(jobs)} jobs collected!")
    if jobs:
        print("\n--- SAMPLE JOB ---")
        print(json.dumps(jobs[0], indent=2))