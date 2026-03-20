from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add project path so imports work inside Docker
sys.path.insert(0, '/opt/airflow')

default_args = {
    "owner":            "ganesh",
    "retries":          1,
    "retry_delay":      timedelta(minutes=2),
    "email_on_failure": False,
    "email_on_retry":   False,
}

# ─────────────────────────────────────────
# TASK FUNCTIONS
# ─────────────────────────────────────────
def run_remoteok_scraper():
    import requests
    import json
    import os
    from datetime import datetime

    print("Starting RemoteOK scraper...")
    URL     = "https://remoteok.com/api"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch RemoteOK: {response.status_code}")

    data = response.json()
    jobs = [job for job in data if isinstance(job, dict) and "position" in job]

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

    os.makedirs("/opt/airflow/raw_data", exist_ok=True)
    today    = datetime.now().strftime("%Y-%m-%d")
    filename = f"/opt/airflow/raw_data/remoteok_{today}.json"

    with open(filename, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Saved {len(cleaned)} jobs to {filename}")

def run_arbeitnow_scraper():
    import requests
    import json
    import os
    from datetime import datetime

    print("Starting Arbeitnow scraper...")
    all_jobs = []

    for page in range(1, 4):
        url      = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
        response = requests.get(url)

        if response.status_code == 200:
            jobs = response.json().get("data", [])
            for job in jobs:
                all_jobs.append({
                    "title":       job.get("title", "N/A"),
                    "company":     job.get("company_name", "N/A"),
                    "location":    job.get("location", "Remote"),
                    "tags":        job.get("tags", []),
                    "salary_min":  None,
                    "salary_max":  None,
                    "job_url":     job.get("url", "N/A"),
                    "posted_date": str(job.get("created_at", "N/A")),
                    "source":      "arbeitnow",
                    "scraped_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    os.makedirs("/opt/airflow/raw_data", exist_ok=True)
    today    = datetime.now().strftime("%Y-%m-%d")
    filename = f"/opt/airflow/raw_data/arbeitnow_{today}.json"

    with open(filename, "w") as f:
        json.dump(all_jobs, f, indent=2)

    print(f"Saved {len(all_jobs)} jobs to {filename}")

def run_load_to_db():
    import json
    import os
    import psycopg2
    from datetime import datetime

    print("Loading data to database...")

    DB_CONFIG = {
        "host":     "host.docker.internal",
        "database": "jobmarket",
        "user":     "postgres",
        "password": "Kumar@2805",
        "port":     "5432"
    }

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    today  = datetime.now().strftime("%Y-%m-%d")

    files = [
        f"/opt/airflow/raw_data/remoteok_{today}.json",
        f"/opt/airflow/raw_data/arbeitnow_{today}.json",
    ]

    total_inserted = 0

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"Skipping {filepath} — not found")
            continue

        with open(filepath, "r") as f:
            jobs = json.load(f)

        for job in jobs:
            try:
                cursor.execute("""
                    INSERT INTO jobs (
                        title, company, location, tags,
                        salary_min, salary_max, job_url,
                        posted_date, source, scraped_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (job_url) DO NOTHING
                """, (
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("tags"),
                    job.get("salary_min"),
                    job.get("salary_max"),
                    job.get("job_url"),
                    job.get("posted_date"),
                    job.get("source"),
                    job.get("scraped_at"),
                ))
                if cursor.rowcount > 0:
                    total_inserted += 1
            except Exception as e:
                print(f"Error inserting job: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Total inserted: {total_inserted}")

def run_etl_cleaner():
    import json
    import re
    import os
    from datetime import datetime

    print("Running ETL cleaner...")

    SKILLS = [
        "python", "javascript", "typescript", "java", "scala",
        "go", "rust", "c++", "ruby", "php", "swift", "kotlin",
        "sql", "pandas", "numpy", "tensorflow", "pytorch",
        "spark", "hadoop", "machine learning", "deep learning",
        "nlp", "data science", "aws", "azure", "gcp",
        "docker", "kubernetes", "git", "linux", "cloud",
        "postgresql", "mysql", "mongodb", "redis", "react",
        "nodejs", "django", "fastapi", "flask", "security",
        "blockchain", "web3", "testing", "agile", "finance",
        "crypto", "marketing", "sales", "design", "remote"
    ]

    today = datetime.now().strftime("%Y-%m-%d")
    cleaned_jobs = []

    files = [
        f"/opt/airflow/raw_data/remoteok_{today}.json",
        f"/opt/airflow/raw_data/arbeitnow_{today}.json",
    ]

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"Skipping {filepath}")
            continue

        with open(filepath, "r") as f:
            jobs = json.load(f)

        for job in jobs:
            title    = job.get("title", "")
            location = job.get("location", "")
            tags     = job.get("tags", [])
            sal_min  = job.get("salary_min")
            sal_max  = job.get("salary_max")
            posted   = job.get("posted_date", "")

            if not title or title.strip() == "":
                continue

            clean_loc     = "Remote" if not location or location.strip() == "" else location.strip().title()
            clean_sal_min = None if not sal_min or sal_min == 0 else sal_min
            clean_sal_max = None if not sal_max or sal_max == 0 else sal_max
            title         = re.sub(r'[^\w\s\-&/]', '', " ".join(title.split())).strip()
            clean_tags    = [t.lower().strip() for t in (tags or [])]
            skills        = [s for s in SKILLS if s.lower() in clean_tags]

            clean_date = None
            if posted and posted != "N/A":
                try:
                    clean_date = str(posted).split("T")[0]
                except:
                    clean_date = None

            cleaned_jobs.append({
                "title_clean":       title,
                "company":           job.get("company", "N/A"),
                "location_clean":    clean_loc,
                "salary_min_clean":  clean_sal_min,
                "salary_max_clean":  clean_sal_max,
                "skills_extracted":  skills,
                "posted_date_clean": clean_date,
                "job_url":           job.get("job_url", "N/A"),
                "source":            job.get("source", "N/A"),
                "scraped_at":        job.get("scraped_at", "N/A"),
            })

    os.makedirs("/opt/airflow/raw_data", exist_ok=True)
    output = f"/opt/airflow/raw_data/cleaned_{today}.json"
    with open(output, "w") as f:
        json.dump(cleaned_jobs, f, indent=2)

    print(f"Cleaned {len(cleaned_jobs)} jobs saved to {output}")
    return True

def pipeline_success():
    print("=" * 50)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

# ─────────────────────────────────────────
# DAG
# ─────────────────────────────────────────
with DAG(
    dag_id="job_market_daily_pipeline",
    description="Daily job market data pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["job_market", "etl", "scraper"],
) as dag:

    task_remoteok = PythonOperator(
        task_id="scrape_remoteok",
        python_callable=run_remoteok_scraper,
    )
    task_arbeitnow = PythonOperator(
        task_id="scrape_arbeitnow",
        python_callable=run_arbeitnow_scraper,
    )
    task_load = PythonOperator(
        task_id="load_to_database",
        python_callable=run_load_to_db,
    )
    task_etl = PythonOperator(
        task_id="run_etl_cleaner",
        python_callable=run_etl_cleaner,
    )
    task_success = PythonOperator(
        task_id="pipeline_success",
        python_callable=pipeline_success,
    )

    [task_remoteok, task_arbeitnow] >> task_load >> task_etl >> task_success