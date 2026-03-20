import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="JobRadar — Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
def load_css(dark_mode):
    if dark_mode:
        bg        = "#0F1117"
        card_bg   = "#1A1D27"
        text      = "#EAEAEA"
        subtext   = "#8B8FA8"
        accent    = "#4F8EF7"
        accent2   = "#F75F7A"
        border    = "#2A2D3E"
        metric_bg = "#1E2130"
    else:
        bg        = "#F4F6FB"
        card_bg   = "#FFFFFF"
        text      = "#1A1D27"
        subtext   = "#6B7280"
        accent    = "#2563EB"
        accent2   = "#E11D48"
        border    = "#E5E7EB"
        metric_bg = "#EFF6FF"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
        background-color: {bg};
        color: {text};
    }}
    .main {{ background-color: {bg}; }}
    .block-container {{ padding: 1.5rem 2.5rem; }}
    h1,h2,h3 {{ font-family: 'Syne', sans-serif !important; color: {text} !important; }}

    .metric-card {{
        background: {metric_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }}
    .metric-value {{
        font-family: 'Syne', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: {accent};
        line-height: 1;
    }}
    .metric-label {{
        font-size: 0.75rem;
        color: {subtext};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }}
    .metric-delta {{
        font-size: 0.75rem;
        color: #34D399;
        margin-top: 2px;
    }}

    .section-header {{
        font-family: 'Syne', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: {text};
        border-left: 3px solid {accent};
        padding-left: 10px;
        margin: 20px 0 12px;
    }}

    .hero {{
        background: linear-gradient(135deg, {accent}22, {accent2}11);
        border: 1px solid {border};
        border-radius: 18px;
        padding: 24px 32px;
        margin-bottom: 24px;
    }}
    .hero-title {{
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: {text};
        margin: 0;
    }}
    .hero-sub {{
        color: {subtext};
        font-size: 0.88rem;
        margin-top: 6px;
    }}

    .insight-box {{
        background: {card_bg};
        border: 1px solid {border};
        border-left: 4px solid {accent};
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
        font-size: 0.85rem;
        color: {subtext};
    }}
    .insight-box strong {{ color: {text}; }}

    section[data-testid="stSidebar"] {{
        background: {card_bg};
        border-right: 1px solid {border};
    }}
    .sidebar-logo {{
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 800;
        color: {accent};
        margin-bottom: 2px;
    }}
    .sidebar-sub {{
        font-size: 0.72rem;
        color: {subtext};
        margin-bottom: 20px;
    }}

    div[data-testid="stExpander"] {{
        border: 1px solid {border} !important;
        border-radius: 10px !important;
        background: {card_bg} !important;
        margin-bottom: 8px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="jobmarket",
        user="postgres",
        password="Kumar@2805",
        port="5432"
    )

@st.cache_data(ttl=300)
def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">📊 JobRadar</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Job Market Intelligence Platform</div>', unsafe_allow_html=True)
        dark_mode = st.toggle("🌙 Dark Mode", value=True)
        st.divider()
        st.markdown("**Filters**")
        source_filter = st.multiselect(
            "Data Source",
            ["remoteok", "arbeitnow"],
            default=["remoteok", "arbeitnow"]
        )
        top_n = st.slider("Top N results", 5, 20, 10)
        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%b %d, %Y %H:%M')}")
    return dark_mode, source_filter, top_n

# ─────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────
def load_metrics(source_str):
    total       = run_query(f"SELECT COUNT(*) as c FROM jobs WHERE source IN ('{source_str}')")
    companies   = run_query(f"SELECT COUNT(DISTINCT company) as c FROM jobs WHERE source IN ('{source_str}')")
    locations   = run_query(f"SELECT COUNT(DISTINCT location_clean) as c FROM jobs WHERE source IN ('{source_str}') AND is_cleaned=TRUE")
    with_salary = run_query(f"SELECT COUNT(*) as c FROM jobs WHERE source IN ('{source_str}') AND salary_min_clean IS NOT NULL")
    return {
        "total":      int(total["c"][0]),
        "companies":  int(companies["c"][0]),
        "locations":  int(locations["c"][0]),
        "salary":     int(with_salary["c"][0]),
    }

def render_metrics(m):
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, m["total"],     "Total Jobs",         "↑ Live data"),
        (c2, m["companies"], "Companies Hiring",    "across all sources"),
        (c3, m["locations"], "Locations",           "cities & remote"),
        (c4, m["salary"],    "Jobs With Salary",    "disclosed salary"),
    ]
    for col, val, label, delta in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val:,}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-delta">{delta}</div>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# PLOT HELPERS
# ─────────────────────────────────────────
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#8B8FA8"),
    margin=dict(l=10, r=40, t=10, b=10),
)

def hbar(df, x, y, colorscale="Blues", h=380):
    fig = go.Figure(go.Bar(
        x=df[x], y=df[y], orientation="h",
        marker=dict(color=df[x], colorscale=colorscale, showscale=False),
        text=df[x], textposition="outside",
    ))
    fig.update_layout(**LAYOUT, height=h,
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
    )
    return fig

# ─────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────
def tab_overview(source_str, top_n, dark_mode):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-header">Top Skills in Demand</div>', unsafe_allow_html=True)
        df = run_query(f"""
            SELECT skill, COUNT(*) as count
            FROM jobs, unnest(skills_extracted) as skill
            WHERE source IN ('{source_str}') AND is_cleaned=TRUE
            GROUP BY skill ORDER BY count DESC LIMIT {top_n}
        """)
        if not df.empty:
            st.plotly_chart(hbar(df, "count", "skill"), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Jobs by Source</div>', unsafe_allow_html=True)
        df = run_query(f"""
            SELECT source, COUNT(*) as count FROM jobs
            WHERE source IN ('{source_str}') GROUP BY source
        """)
        if not df.empty:
            fig = px.pie(df, values="count", names="source",
                color_discrete_sequence=["#4F8EF7","#F75F7A"],
                hole=0.55)
            fig.update_layout(**LAYOUT, height=320,
                legend=dict(orientation="h", y=-0.1))
            fig.update_traces(textposition="outside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    # Insights box
    if not df.empty:
        top_source = df.loc[df["count"].idxmax(), "source"]
        st.markdown(f"""
        <div class="insight-box">
            <strong>Quick Insight:</strong> Most jobs are from
            <strong>{top_source}</strong> in your current filter.
            Add more data sources to get a broader market view.
        </div>""", unsafe_allow_html=True)

    # Expanders for extra overview charts
    with st.expander("📍 Jobs by Location (Treemap)"):
        df = run_query(f"""
            SELECT location_clean, COUNT(*) as count FROM jobs
            WHERE source IN ('{source_str}') AND is_cleaned=TRUE
            AND location_clean IS NOT NULL
            GROUP BY location_clean ORDER BY count DESC LIMIT 20
        """)
        if not df.empty:
            fig = px.treemap(df, path=["location_clean"], values="count",
                color="count", color_continuous_scale="Blues")
            fig.update_layout(**LAYOUT, height=380)
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("🌐 Remote vs Onsite Ratio"):
        df = run_query(f"""
            SELECT
                CASE WHEN LOWER(location_clean) LIKE '%remote%'
                     THEN 'Remote' ELSE 'Onsite' END as work_type,
                COUNT(*) as count
            FROM jobs WHERE source IN ('{source_str}') AND is_cleaned=TRUE
            GROUP BY work_type
        """)
        if not df.empty:
            fig = px.pie(df, values="count", names="work_type",
                color_discrete_sequence=["#4F8EF7","#34D399"], hole=0.6)
            fig.update_layout(**LAYOUT, height=340,
                legend=dict(orientation="h", y=-0.1))
            fig.update_traces(textposition="outside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 2 — SKILLS
# ─────────────────────────────────────────
def tab_skills(source_str, top_n, dark_mode):
    st.markdown('<div class="section-header">Skills by Job Source</div>', unsafe_allow_html=True)
    df = run_query(f"""
        SELECT source, skill, COUNT(*) as count
        FROM jobs, unnest(skills_extracted) as skill
        WHERE source IN ('{source_str}') AND is_cleaned=TRUE
        GROUP BY source, skill ORDER BY count DESC LIMIT 40
    """)
    if not df.empty:
        top_skills = df.groupby("skill")["count"].sum().nlargest(8).index.tolist()
        df = df[df["skill"].isin(top_skills)]
        fig = px.bar(df, x="skill", y="count", color="source",
            barmode="group",
            color_discrete_sequence=["#4F8EF7","#F75F7A"])
        fig.update_layout(**LAYOUT, height=380,
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    # Expanders
    with st.expander("🔗 Skills Co-occurrence — Which Skills Appear Together"):
        df = run_query(f"""
            SELECT a.skill as skill1, b.skill as skill2, COUNT(*) as count
            FROM
                (SELECT id, unnest(skills_extracted) as skill FROM jobs
                 WHERE source IN ('{source_str}') AND is_cleaned=TRUE) a
            JOIN
                (SELECT id, unnest(skills_extracted) as skill FROM jobs
                 WHERE source IN ('{source_str}') AND is_cleaned=TRUE) b
            ON a.id = b.id AND a.skill < b.skill
            GROUP BY a.skill, b.skill HAVING COUNT(*) > 1
            ORDER BY count DESC LIMIT 25
        """)
        if not df.empty:
            fig = px.scatter(df, x="skill1", y="skill2",
                size="count", color="count",
                color_continuous_scale="Blues", size_max=40)
            fig.update_layout(**LAYOUT, height=420,
                xaxis=dict(gridcolor="rgba(128,128,128,0.1)", tickangle=-30),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
                coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough co-occurrence data yet.")

    with st.expander("☁️ Skills Word Cloud"):
        df = run_query(f"""
            SELECT skill, COUNT(*) as count
            FROM jobs, unnest(skills_extracted) as skill
            WHERE source IN ('{source_str}') AND is_cleaned=TRUE
            GROUP BY skill
        """)
        if not df.empty:
            word_freq = dict(zip(df["skill"], df["count"]))
            wc = WordCloud(
                width=1200, height=400,
                background_color="black" if dark_mode else "white",
                colormap="Blues", max_words=80,
                prefer_horizontal=0.9,
            ).generate_from_frequencies(word_freq)
            fig_wc, ax = plt.subplots(figsize=(14, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            fig_wc.patch.set_facecolor("black" if dark_mode else "white")
            st.pyplot(fig_wc)
            plt.close()

# ─────────────────────────────────────────
# TAB 3 — SALARY
# ─────────────────────────────────────────
def tab_salary(source_str, dark_mode):
    st.markdown('<div class="section-header">Salary Range by Job Title</div>', unsafe_allow_html=True)
    df = run_query(f"""
        SELECT title_clean, company,
               salary_min_clean, salary_max_clean,
               (salary_min_clean + salary_max_clean)/2 as avg_salary
        FROM jobs
        WHERE source IN ('{source_str}')
        AND salary_min_clean IS NOT NULL
        AND salary_min_clean > 0
        ORDER BY avg_salary DESC LIMIT 20
    """)
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Min", x=df["title_clean"],
            y=df["salary_min_clean"], marker_color="#4F8EF7"))
        fig.add_trace(go.Bar(name="Max", x=df["title_clean"],
            y=df["salary_max_clean"], marker_color="#F75F7A"))
        fig.update_layout(**LAYOUT, barmode="group", height=420,
            xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No salary data available in current filter.")

    with st.expander("📊 Salary Distribution Histogram"):
        df = run_query(f"""
            SELECT salary_min_clean as salary FROM jobs
            WHERE source IN ('{source_str}')
            AND salary_min_clean IS NOT NULL
            AND salary_min_clean > 0
            AND salary_min_clean < 500000
        """)
        if not df.empty:
            fig = px.histogram(df, x="salary", nbins=20,
                color_discrete_sequence=["#4F8EF7"])
            fig.update_layout(**LAYOUT, height=360,
                xaxis=dict(title="Salary (USD/year)",
                    gridcolor="rgba(128,128,128,0.1)"),
                yaxis=dict(title="Number of Jobs",
                    gridcolor="rgba(128,128,128,0.1)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough salary data for histogram.")

# ─────────────────────────────────────────
# TAB 4 — COMPANIES
# ─────────────────────────────────────────
def tab_companies(source_str, top_n, dark_mode):
    st.markdown('<div class="section-header">Top Hiring Companies</div>', unsafe_allow_html=True)
    df = run_query(f"""
        SELECT company, COUNT(*) as count FROM jobs
        WHERE source IN ('{source_str}')
        AND company != 'N/A' AND company IS NOT NULL
        GROUP BY company ORDER BY count DESC LIMIT {top_n}
    """)
    if not df.empty:
        st.plotly_chart(hbar(df, "count", "company", "Teal", 420),
            use_container_width=True)

    with st.expander("👤 Experience Level Breakdown"):
        df = run_query(f"""
            SELECT
                CASE
                    WHEN LOWER(title_clean) LIKE '%senior%'
                      OR LOWER(title_clean) LIKE '%sr.%' THEN 'Senior'
                    WHEN LOWER(title_clean) LIKE '%junior%'
                      OR LOWER(title_clean) LIKE '%jr.%' THEN 'Junior'
                    WHEN LOWER(title_clean) LIKE '%lead%'
                      OR LOWER(title_clean) LIKE '%principal%' THEN 'Lead'
                    WHEN LOWER(title_clean) LIKE '%manager%'
                      OR LOWER(title_clean) LIKE '%director%' THEN 'Manager'
                    WHEN LOWER(title_clean) LIKE '%intern%' THEN 'Intern'
                    ELSE 'Mid-Level'
                END as level,
                COUNT(*) as count
            FROM jobs
            WHERE source IN ('{source_str}')
            AND is_cleaned=TRUE AND title_clean IS NOT NULL
            GROUP BY level ORDER BY count DESC
        """)
        if not df.empty:
            fig = px.bar(df, x="level", y="count", color="level",
                color_discrete_sequence=[
                    "#4F8EF7","#F75F7A","#34D399",
                    "#FBBF24","#A78BFA","#FB923C"],
                text="count")
            fig.update_traces(textposition="outside")
            fig.update_layout(**LAYOUT, height=380, showlegend=False,
                xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"))
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("💼 Top Job Titles in Demand"):
        df = run_query(f"""
            SELECT title_clean, COUNT(*) as count FROM jobs
            WHERE source IN ('{source_str}')
            AND is_cleaned=TRUE AND title_clean IS NOT NULL
            GROUP BY title_clean ORDER BY count DESC LIMIT 15
        """)
        if not df.empty:
            st.plotly_chart(
                hbar(df, "count", "title_clean", "Purples", 420),
                use_container_width=True)

# ─────────────────────────────────────────
# TAB 5 — TRENDS
# ─────────────────────────────────────────
def tab_trends(source_str, dark_mode):
    st.markdown('<div class="section-header">Hiring Trends Over Time</div>', unsafe_allow_html=True)
    df = run_query(f"""
        SELECT posted_date_clean as date, COUNT(*) as count
        FROM jobs WHERE source IN ('{source_str}')
        AND posted_date_clean IS NOT NULL
        GROUP BY posted_date_clean ORDER BY posted_date_clean ASC
    """)
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["count"],
            mode="lines+markers",
            line=dict(color="#4F8EF7", width=2.5),
            marker=dict(size=6, color="#4F8EF7"),
            fill="tozeroy",
            fillcolor="rgba(79,142,247,0.1)",
        ))
        fig.update_layout(**LAYOUT, height=360,
            xaxis=dict(gridcolor="rgba(128,128,128,0.1)"),
            yaxis=dict(gridcolor="rgba(128,128,128,0.1)"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough date data for trend chart yet.")

    with st.expander("📅 This Week vs Last Week"):
        today     = datetime.now().date()
        this_week = today - timedelta(days=7)
        last_week = today - timedelta(days=14)
        df = run_query(f"""
            SELECT
                CASE
                    WHEN posted_date_clean >= '{this_week}' THEN 'This Week'
                    WHEN posted_date_clean >= '{last_week}'
                     AND posted_date_clean < '{this_week}' THEN 'Last Week'
                END as period,
                COUNT(*) as count
            FROM jobs WHERE source IN ('{source_str}')
            AND posted_date_clean IS NOT NULL
            AND posted_date_clean >= '{last_week}'
            GROUP BY period ORDER BY period
        """)
        if not df.empty:
            fig = px.bar(df, x="period", y="count", color="period",
                color_discrete_sequence=["#4F8EF7","#34D399"],
                text="count")
            fig.update_traces(textposition="outside")
            fig.update_layout(**LAYOUT, height=340, showlegend=False,
                xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                yaxis=dict(gridcolor="rgba(128,128,128,0.1)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough date data for weekly comparison.")

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    dark_mode, source_filter, top_n = render_sidebar()
    load_css(dark_mode)

    if not source_filter:
        st.warning("Select at least one data source from the sidebar.")
        return

    source_str = "','".join(source_filter)
    metrics    = load_metrics(source_str)

    # Hero
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">📊 JobRadar</div>
        <div class="hero-sub">
            Real-time insights from {metrics['total']:,} job listings
            across {metrics['companies']:,} companies
            — {datetime.now().strftime("%b %d, %Y")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    render_metrics(metrics)
    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview",
        "🛠 Skills",
        "💰 Salary",
        "🏢 Companies",
        "📈 Trends"
    ])

    with tab1:
        tab_overview(source_str, top_n, dark_mode)
    with tab2:
        tab_skills(source_str, top_n, dark_mode)
    with tab3:
        tab_salary(source_str, dark_mode)
    with tab4:
        tab_companies(source_str, top_n, dark_mode)
    with tab5:
        tab_trends(source_str, dark_mode)

    st.divider()
    st.caption("JobRadar — Built with Python, PostgreSQL, Streamlit & Plotly")

if __name__ == "__main__":
    main()