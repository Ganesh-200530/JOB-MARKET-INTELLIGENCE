# 📊 Job Market Intelligence Platform

> An end-to-end automated data pipeline that scrapes 
> 600+ job listings daily from multiple sources, 
> processes them with NLP, stores in PostgreSQL, 
> and visualizes hiring trends via a live dashboard.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![Airflow](https://img.shields.io/badge/Apache-Airflow-green)
![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20S3%20%7C%20RDS-orange)

---

## 🏗 Architecture
```
Data Sources          Pipeline              Storage & Output
─────────────         ────────              ────────────────
RemoteOK API    →                     →     PostgreSQL DB
Arbeitnow API   →   ETL Pipeline      →     AWS S3 (raw)
(More coming)   →   (Apache Airflow)  →     Streamlit Dashboard
                                      →     Power BI / Tableau
```

---

## ✨ Features

- **Multi-source scraping** — RemoteOK, Arbeitnow APIs
- **Automated ETL pipeline** — cleans, transforms, loads daily
- **NLP skill extraction** — extracts 50+ tech skills from job data
- **PostgreSQL database** — structured storage with deduplication
- **Interactive dashboard** — 10+ charts with dark/light mode
- **Apache Airflow** — fully automated daily scheduling
- **AWS deployment** — EC2, S3, RDS for production hosting

---

## 📊 Dashboard Preview

> Coming soon — screenshots after deployment

---

## 🛠 Tech Stack

| Category | Tools |
|---|---|
| Language | Python 3.13 |
| Scraping | Requests, BeautifulSoup, Scrapy |
| Processing | Pandas, spaCy, NLTK |
| Database | PostgreSQL 18, SQLAlchemy |
| Orchestration | Apache Airflow |
| Dashboard | Streamlit, Plotly |
| Cloud | AWS EC2, S3, RDS |
| Containerization | Docker |
| BI Tools | Power BI, Tableau Public |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 16+
- Docker (optional)

### Installation
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/job-market-intelligence.git
cd job-market-intelligence

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### Run the Scraper
```bash
python scraper/remoteok_scraper.py
python scraper/naukri_scraper.py
```

### Run ETL Pipeline
```bash
python etl/load_to_db.py
python etl/clean_transform.py
```

### Launch Dashboard
```bash
streamlit run dashboard/app.py
```

---

## 📁 Project Structure
```
job-market-intelligence/
├── scraper/
│   ├── remoteok_scraper.py    # RemoteOK API scraper
│   └── naukri_scraper.py      # Arbeitnow API scraper
├── etl/
│   ├── load_to_db.py          # Load JSON to PostgreSQL
│   └── clean_transform.py     # Clean + NLP extraction
├── database/
│   └── schema.sql             # Database schema
├── airflow/
│   └── dags/                  # Airflow DAGs
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── tests/                     # Unit tests
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 📈 Sample Insights

- **Top skill in demand:** Git (28 jobs)
- **Most remote-friendly:** 49% of jobs are fully remote
- **596 jobs** collected from 2 sources in first run

---

## 🗺 Roadmap

- [x] RemoteOK scraper
- [x] Arbeitnow scraper
- [x] PostgreSQL database
- [x] ETL pipeline
- [x] Streamlit dashboard
- [ ] Apache Airflow automation
- [ ] AWS deployment
- [ ] Power BI dashboard
- [ ] Tableau Public dashboard
- [ ] LinkedIn scraper

---

## 👨‍💻 Author

Built by **[Your Name]** as a portfolio project demonstrating
end-to-end data engineering skills.

---

## 📄 License

MIT License
```

---

### Step 4 — Update requirements.txt

Open `requirements.txt` and paste:
```
scrapy==2.11.0
selenium==4.18.0
requests==2.31.0
beautifulsoup4==4.12.3
pandas==2.2.0
spacy==3.7.4
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
streamlit==1.32.0
plotly==5.19.0
boto3==1.34.0
python-dotenv==1.0.1
fake-useragent==1.5.1
wordcloud==1.9.3
matplotlib==3.8.3
apache-airflow==2.8.2