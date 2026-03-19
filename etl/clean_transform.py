import json
import os
import re
import psycopg2
import spacy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "database": "jobmarket",
    "user":     "postgres",
    "password": "Kumar@2805",
    "port":     "5432"
}

# ─────────────────────────────────────────
# SKILLS LIST — What we look for in job tags
# ─────────────────────────────────────────
SKILLS = [
    # Programming Languages
    "python", "javascript", "typescript", "java", "scala",
    "go", "rust", "c++", "ruby", "php", "swift", "kotlin",
    "matlab", "perl", "bash", "shell",

    # Data & ML
    "sql", "nosql", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "keras", "spark", "hadoop",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data science", "data analysis", "data engineering",
    "statistics", "analytics", "tableau", "power bi",
    "looker", "dbt", "airflow", "kafka", "flink",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes",
    "terraform", "jenkins", "git", "linux", "bash",
    "ci/cd", "devops", "cloud", "serverless",

    # Databases
    "postgresql", "mysql", "mongodb", "redis",
    "elasticsearch", "snowflake", "bigquery",
    "dynamodb", "cassandra", "sqlite",

    # Web & API
    "react", "nodejs", "django", "fastapi", "flask",
    "rest", "graphql", "microservices", "api",
    "html", "css", "vue", "angular",

    # Security
    "security", "cybersecurity", "penetration testing",
    "cryptography", "blockchain", "web3",

    # Other Tech
    "testing", "qa", "agile", "scrum",
    "system design", "distributed systems",

    # Domain Skills
    "finance", "crypto", "defi", "bitcoin",
    "healthcare", "medical", "legal",
    "marketing", "seo", "content",
    "sales", "crm", "erp",

    # Soft/Role Skills (valuable for job market analysis)
    "leadership", "strategy", "growth",
    "product management", "project management",
    "customer support", "operations",
    "training", "coaching", "design",
    "digital nomad", "remote"
]

# ─────────────────────────────────────────
# STEP 1 — CONNECT TO DATABASE
# ─────────────────────────────────────────
def connect_db():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("Connected!")
    return conn

# ─────────────────────────────────────────
# STEP 2 — FETCH RAW JOBS FROM DATABASE
# ─────────────────────────────────────────
def fetch_jobs(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, company, location, 
               tags, salary_min, salary_max, 
               posted_date, source
        FROM jobs
    """)
    rows = cursor.fetchall()
    cursor.close()
    print(f"Fetched {len(rows)} jobs from database!")
    return rows

# ─────────────────────────────────────────
# STEP 3 — CLEAN SALARY
# ─────────────────────────────────────────
def clean_salary(salary):
    # If salary is 0 or None — return NULL
    if not salary or salary == 0:
        return None
    # If salary looks too small (probably wrong data)
    if salary < 1000:
        return None
    return salary

# ─────────────────────────────────────────
# STEP 4 — CLEAN LOCATION
# ─────────────────────────────────────────
def clean_location(location):
    if not location or location.strip() == "":
        return "Remote"
    # Remove extra spaces
    location = location.strip()
    # Capitalize properly
    location = location.title()
    return location

# ─────────────────────────────────────────
# STEP 5 — CLEAN TITLE
# ─────────────────────────────────────────
def clean_title(title):
    if not title or title.strip() == "":
        return None
    # Remove extra spaces
    title = " ".join(title.split())
    # Remove weird characters
    title = re.sub(r'[^\w\s\-&/]', '', title)
    return title.strip()
# ─────────────────────────────────────────
# STEP 6 — EXTRACT SKILLS FROM TAGS
# ─────────────────────────────────────────
def extract_skills(tags):
    if not tags:
        return []

    found_skills = []

    # Clean tags — lowercase each tag individually
    clean_tags = [tag.lower().strip() for tag in tags]

    for skill in SKILLS:
        skill_lower = skill.lower()
        # Exact match only — skill must match a whole tag
        if skill_lower in clean_tags:
            found_skills.append(skill)
        # Also check multi-word skills as substring of tags
        elif len(skill_lower.split()) > 1:
            tags_text = " ".join(clean_tags)
            if skill_lower in tags_text:
                found_skills.append(skill)

    return found_skills

# ─────────────────────────────────────────
# STEP 7 — CLEAN POSTED DATE
# ─────────────────────────────────────────
def clean_date(posted_date):
    if not posted_date or posted_date == "N/A":
        return None
    try:
        # Handle Unix timestamp (Arbeitnow format)
        # e.g. 1773934933
        if isinstance(posted_date, int) or str(posted_date).isdigit():
            from datetime import datetime
            return datetime.fromtimestamp(int(posted_date)).strftime("%Y-%m-%d")

        # Handle ISO format (RemoteOK format)
        # e.g. "2026-03-17T15:31:09+00:00"
        if "T" in str(posted_date):
            return str(posted_date).split("T")[0]

        # Already a plain date string
        return str(posted_date)[:10]

    except:
        return None

# ─────────────────────────────────────────
# STEP 8 — ADD CLEANED COLUMNS TO DB
# ─────────────────────────────────────────
def add_cleaned_columns(conn):
    cursor = conn.cursor()
    print("Adding cleaned columns to database...")

    # Add new columns if they don't exist
    queries = [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min_clean INTEGER",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max_clean INTEGER",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location_clean VARCHAR(255)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title_clean VARCHAR(255)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS skills_extracted TEXT[]",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_date_clean DATE",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_cleaned BOOLEAN DEFAULT FALSE"
    ]

    for query in queries:
        cursor.execute(query)

    conn.commit()
    cursor.close()
    print("Columns added successfully!")

# ─────────────────────────────────────────
# STEP 9 — UPDATE CLEANED DATA IN DB
# ─────────────────────────────────────────
def update_cleaned_jobs(conn, jobs):
    cursor = conn.cursor()
    updated = 0
    skipped = 0
    print("Cleaning and updating jobs...")

    for job in jobs:
        job_id      = job[0]
        title       = job[1]
        location    = job[3]
        tags        = job[4]
        salary_min  = job[5]
        salary_max  = job[6]
        posted_date = job[7]

        if not title or title.strip() == "":
            skipped += 1
            continue

        # Clean each field
        clean_sal_min  = clean_salary(salary_min)
        clean_sal_max  = clean_salary(salary_max)
        clean_loc      = clean_location(location)
        clean_tit      = clean_title(title)
        skills         = extract_skills(tags)
        clean_dt       = clean_date(posted_date)

        # Update the record in database
        cursor.execute("""
            UPDATE jobs SET
                salary_min_clean  = %s,
                salary_max_clean  = %s,
                location_clean    = %s,
                title_clean       = %s,
                skills_extracted  = %s,
                posted_date_clean = %s,
                is_cleaned        = TRUE
            WHERE id = %s
        """, (
            clean_sal_min,
            clean_sal_max,
            clean_loc,
            clean_tit,
            skills,
            clean_dt,
            job_id
        ))
        updated += 1

    conn.commit()
    cursor.close()
    print(f"Updated {updated} jobs with cleaned data!")

# ─────────────────────────────────────────
# STEP 10 — SHOW RESULTS
# ─────────────────────────────────────────
def show_results(conn):
    cursor = conn.cursor()

    print("\n--- CLEANING RESULTS ---")

    # Show salary fix results
    cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE salary_min_clean IS NOT NULL
    """)
    with_salary = cursor.fetchone()[0]
    print(f"Jobs with valid salary:    {with_salary}")

    # Show location fix results
    cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE location_clean = 'Remote'
    """)
    remote_jobs = cursor.fetchone()[0]
    print(f"Jobs marked as Remote:     {remote_jobs}")

    # Show top skills
    cursor.execute("""
        SELECT skill, COUNT(*) as count
        FROM jobs, unnest(skills_extracted) as skill
        GROUP BY skill
        ORDER BY count DESC
        LIMIT 10
    """)
    skills = cursor.fetchall()
    print("\n--- TOP 10 SKILLS IN DEMAND ---")
    for skill, count in skills:
        bar = "█" * count
        print(f"  {skill:<20} {bar} ({count})")

    # Show sample cleaned job
    cursor.execute("""
        SELECT title_clean, company, location_clean, 
               salary_min_clean, salary_max_clean, skills_extracted
        FROM jobs
        WHERE is_cleaned = TRUE
        LIMIT 3
    """)
    rows = cursor.fetchall()
    print("\n--- SAMPLE CLEANED JOBS ---")
    for row in rows:
        print(f"\n  Title:    {row[0]}")
        print(f"  Company:  {row[1]}")
        print(f"  Location: {row[2]}")
        print(f"  Salary:   {row[3]} - {row[4]}")
        print(f"  Skills:   {row[5]}")

    cursor.close()

# ─────────────────────────────────────────
# MAIN — RUN EVERYTHING
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("   JOB MARKET ETL CLEANER")
    print("=" * 50)

    conn = connect_db()
    add_cleaned_columns(conn)
    jobs = fetch_jobs(conn)
    update_cleaned_jobs(conn, jobs)
    show_results(conn)
    conn.close()

    print("\n" + "=" * 50)
    print("   ETL CLEANING COMPLETE!")
    print("=" * 50)