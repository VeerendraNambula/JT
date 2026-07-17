import streamlit as st
import urllib.parse
import sys
import os

# Append project root to path to ensure src modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.linkedin.scraper import LinkedInScraper
from src.linkedin.job_detector import JobDetector
from src.linkedin.job_parser import JobParser
from src.linkedin.matcher import JobMatcher
from src.linkedin.ingest import LinkedInPost

# 1. Page Configuration
st.set_page_config(
    page_title="LinkedIn Job Tracker & Finder",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Theme Toggle State
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"

# 3. CSS Variables & Custom Theme Injection
bg = "#09090b" if IS_DARK else "#ffffff"
bg_subtle = "#0c0c0f" if IS_DARK else "#f9fafb"
card = "#0c0c0f" if IS_DARK else "#ffffff"
card_hover = "#131316" if IS_DARK else "#f4f4f5"
border = "#1e1e24" if IS_DARK else "#e4e4e7"
border_subtle = "#16161a" if IS_DARK else "#f0f0f2"
text = "#fafafa" if IS_DARK else "#09090b"
text_muted = "#71717a"
text_dim = "#52525b" if IS_DARK else "#a1a1aa"
accent = "#2563eb"
accent_muted = "#1d4ed8"
green = "#22c55e" if IS_DARK else "#16a34a"
green_muted = "rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"
shadow = "none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"

css = f"""
<style>
:root {{
    --bg: {bg};
    --bg-subtle: {bg_subtle};
    --card: {card};
    --card-hover: {card_hover};
    --border: {border};
    --border-subtle: {border_subtle};
    --text: {text};
    --text-muted: {text_muted};
    --text-dim: {text_dim};
    --accent: {accent};
    --accent-muted: {accent_muted};
    --green: {green};
    --green-muted: {green_muted};
    --shadow: {shadow};
    --radius: 10px;
}}

/* Hide Streamlit default chrome components */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* App Container */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}
.block-container {{
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1360px !important;
}}

/* Custom Job Cards */
.job-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow);
    transition: transform 0.2s, border-color 0.2s;
}}
.job-card:hover {{
    border-color: var(--accent);
    transform: translateY(-2px);
}}
.job-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
}}
.job-role {{
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
}}
.job-company {{
    font-size: 0.95rem;
    color: var(--text-muted);
    font-weight: 500;
}}
.job-meta-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-top: 0.8rem;
    font-size: 0.85rem;
    color: var(--text-muted);
}}
.job-meta-item {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}
.badge {{
    display: inline-block;
    padding: 2px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 500;
}}
.badge-green {{
    color: var(--green);
    background: var(--green-muted);
}}
.apply-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background-color: var(--accent);
    color: white !important;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 600;
    transition: background-color 0.2s;
}}
.apply-btn:hover {{
    background-color: var(--accent-muted);
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# 4. Initialize Session States
if "all_jobs" not in st.session_state:
    st.session_state.all_jobs = []
if "searched" not in st.session_state:
    st.session_state.searched = False

# 5. Header Section
head_left, head_right = st.columns([9, 1])
with head_left:
    st.markdown("""
    <div style='margin-bottom: 1.5rem;'>
        <h1 style='margin: 0; font-size: 2.25rem; font-weight: 800; letter-spacing: -0.04em;'>◆ Job Finder & Tracker</h1>
        <p style='margin: 0.25rem 0 0; color: var(--text-muted); font-size: 0.95rem;'>Search LinkedIn posts in real time, parse contact details, and filter by role & experience requirements</p>
    </div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Light" if IS_DARK else "🌙 Dark"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

# 6. Main Columns
col_left, col_right = st.columns([1, 2.2])

with col_left:
    st.markdown("### 🔍 Filter Settings")
    target_role = st.text_input("Target Job Role", value="Software Engineer", help="Filters the matching results by role title (case-insensitive substring check).")
    target_exp = st.number_input("Your Experience (Years)", min_value=0.0, max_value=25.0, value=2.0, step=0.5, help="Checks if your experience falls within the job description requirements.")
    
    st.markdown("---")
    st.markdown("### 🕸️ LinkedIn Scraper Settings")
    search_query = st.text_input("LinkedIn Post Search Keywords", value='hiring "email"', help="Search query parameters used to find posts on LinkedIn.")
    limit = st.slider("Target Number of Job Openings", min_value=1, max_value=15, value=3, help="Tells the crawler how many corporate job announcements to collect before stopping.")
    
    use_llm = st.checkbox("Use Gemini LLM Parser", value=False, help="Use Gemini to extract entities. Defaults to local heuristic rules.")
    
    search_btn = st.button("Fetch & Filter Jobs", type="primary", use_container_width=True)

with col_right:
    st.markdown("### 💼 Matching Job Opportunities")
    
    if search_btn:
        st.session_state.searched = True
        st.session_state.all_jobs = []
        
        # Build search page URL
        encoded_query = urllib.parse.quote(search_query)
        target_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}"
        
        status_box = st.empty()
        status_box.info("Initiating Playwright crawler & navigating to search results...")
        
        try:
            # Initialize components
            detector = JobDetector(use_llm=use_llm)
            parser = JobParser()
            
            # Run scraper
            raw_posts = LinkedInScraper.fetch_posts(
                target_url,
                limit=limit,
                headless=True,
                job_detector_cb=detector.is_job_opening,
                target_jobs=limit
            )
            
            if not raw_posts:
                status_box.warning("No job announcements matching the official email criteria were found on LinkedIn.")
            else:
                status_box.info(f"Scraped {len(raw_posts)} raw job updates. Processing details...")
                
                # Parse all updates
                for p in raw_posts:
                    details = parser.parse_job_details(p)
                    st.session_state.all_jobs.append({
                        "post": p,
                        "details": details
                    })
                
                status_box.empty()
        except Exception as e:
            status_box.error(f"Live scraping or parsing failed: {e}")
            
    if st.session_state.searched:
        # Run matcher on session cache
        matched_results = []
        for item in st.session_state.all_jobs:
            details = item["details"]
            if JobMatcher.match_job(details, target_role, target_exp):
                matched_results.append(item)
                
        if not matched_results:
            st.info("No scraped jobs matched your role and experience filters. Try widening your filters on the left.")
        else:
            st.success(f"Showing {len(matched_results)} matching jobs out of {len(st.session_state.all_jobs)} parsed postings.")
            
            for item in matched_results:
                details = item["details"]
                post = item["post"]
                
                # Render modern card layout
                st.markdown(f"""
                <div class="job-card">
                    <div class="job-header">
                        <div>
                            <div class="job-role">💼 {details.role or 'Software Engineer'}</div>
                            <div class="job-company">🏢 {details.company or 'Unspecified'}</div>
                        </div>
                        <span class="badge badge-green">Matched</span>
                    </div>
                    <div style="font-size: 0.9rem; margin: 0.6rem 0 1rem 0; line-height: 1.6; color: var(--text);">
                        📍 <strong>Location:</strong> {details.location or 'India'}<br>
                        💼 <strong>Required Experience:</strong> {details.experience_level or 'Not Specified'}<br>
                        💰 <strong>Salary Budget:</strong> {details.salary or 'Not Specified'}
                    </div>
                    <div class="job-meta-row">
                        <div class="job-meta-item">👤 Author: {post.author_name}</div>
                        <div class="job-meta-item">🕒 Posted: {post.posted_date}</div>
                    </div>
                    <div style="margin-top: 1.25rem; display: flex; gap: 0.75rem;">
                        <a class="apply-btn" href="{details.apply_link or '#'}" target="_blank">✉️ Apply via Mail</a>
                        <a class="apply-btn" style="background-color: var(--bg-subtle); color: var(--text) !important; border: 1px solid var(--border);" href="{post.post_url}" target="_blank">🔗 View Original Post</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Show original LinkedIn post text"):
                    st.text(post.text_content)
    else:
        st.info("Enter your parameters in the search panel and click 'Fetch & Filter Jobs' to scan live posts.")
