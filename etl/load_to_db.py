import json
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# CONFIG — Database connection details
# ─────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "database": "jobmarket",
    "user":     "postgres",
    "password": "Kumar@2805",
    "port":     "5432"
}

# ─────────────────────────────────────────
# STEP 1 — CONNECT TO DATABASE
# ─────────────────────────────────────────
def connect_db():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("Connected successfully!")
    return conn

# ─────────────────────────────────────────
# STEP 2 — LOAD JSON FILE
# ─────────────────────────────────────────
def load_json(filepath):
    print(f"Loading data from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    print(f"Loaded {len(jobs)} jobs from file!")
    return jobs

# ─────────────────────────────────────────
# STEP 3 — INSERT JOBS INTO DATABASE
# ─────────────────────────────────────────
def insert_jobs(conn, jobs):
    cursor = conn.cursor()
    inserted = 0
    skipped  = 0

    print("Inserting jobs into database...")

    for job in jobs:
        try:
            cursor.execute("""
                INSERT INTO jobs (
                    title, company, location, tags,
                    salary_min, salary_max, job_url,
                    posted_date, source, scraped_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                job.get("scraped_at")
            ))

            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"Error inserting job: {e}")
            skipped += 1

    conn.commit()
    cursor.close()

    print(f"Done! Inserted: {inserted} | Skipped (duplicates): {skipped}")
    return inserted

# ─────────────────────────────────────────
# STEP 4 — VERIFY DATA IN DATABASE
# ─────────────────────────────────────────
def verify_data(conn):
    cursor = conn.cursor()

    # Count total jobs
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]
    print(f"\nTotal jobs in database: {total}")

    # Show 3 sample jobs
    cursor.execute("""
        SELECT title, company, salary_min, salary_max 
        FROM jobs 
        LIMIT 3
    """)
    rows = cursor.fetchall()
    print("\n--- SAMPLE JOBS IN DATABASE ---")
    for row in rows:
        print(f"  {row[0]} at {row[1]} | Salary: {row[2]} - {row[3]}")

    cursor.close()

# ─────────────────────────────────────────
# MAIN — RUN EVERYTHING
# ─────────────────────────────────────────
if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    
    # All data sources — add new ones here anytime
    files = [
        f"raw_data/remoteok_{today}.json",
        f"raw_data/arbeitnow_{today}.json",
    ]

    conn = connect_db()

    for filepath in files:
        if os.path.exists(filepath):
            print(f"\nProcessing {filepath}...")
            jobs = load_json(filepath)
            insert_jobs(conn, jobs)
        else:
            print(f"Skipping {filepath} — file not found")

    verify_data(conn)
    conn.close()
    print("\nAll done!")