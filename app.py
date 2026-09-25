"""Job Hunt Copilot — Streamlit dashboard.

Run with: streamlit run app.py
"""
import json

import pandas as pd
import streamlit as st

from src import applications, db, rag
from src.excel_export import export_jobs_to_excel
from src.generator import generate_for_job
from src.graph import run_pipeline
from src.job_sources import manual_url
from src.resume_parser import extract_text, parse_profile
from src.skill_gap import analyze as analyze_skill_gap

st.set_page_config(page_title="Job Hunt Copilot", page_icon="🎯", layout="wide")
db.init_db()

st.markdown(
    """
    <style>
      :root {
        --ink: #172033;
        --muted: #61708a;
        --navy: #12233f;
        --surface: rgba(255, 255, 255, 0.88);
        --border: #e5eaf3;
      }
      .stApp {
        background:
          radial-gradient(circle at 88% -8%, #dce7ff 0, transparent 27rem),
          radial-gradient(circle at -8% 20%, #d8fbef 0, transparent 24rem),
          #f6f8fc;
        color: var(--ink);
      }
      .block-container { max-width: 1380px; padding-top: 2.2rem; padding-bottom: 3.5rem; }
      h1, h2, h3 { color: var(--navy) !important; letter-spacing: -0.035em; }
      h1 { font-size: clamp(2.25rem, 4vw, 3.45rem) !important; font-weight: 780 !important; }
      h2 { font-size: 1.55rem !important; margin-top: .5rem !important; }
      [data-testid="stCaptionContainer"] { color: var(--muted); font-size: 1rem; }
      [data-testid="stTabs"] { margin-top: 1.25rem; }
      [data-testid="stTabs"] button {
        border-radius: 999px; color: #68748a; font-weight: 650; padding: .55rem .9rem;
      }
      [data-testid="stTabs"] button[aria-selected="true"] {
        background: #e8eeff; color: #294fc5; border-bottom-color: transparent !important;
      }
      [data-testid="stMetric"] {
        background: var(--surface); border: 1px solid var(--border); border-radius: 18px;
        padding: .8rem 1rem; box-shadow: 0 10px 28px rgba(31, 55, 97, .06);
      }
      [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 650; }
      [data-testid="stMetricValue"] { color: var(--navy); }
      .stButton > button, [data-testid="stDownloadButton"] > button {
        background: #ffffff !important; color: #172033 !important; border-radius: 10px;
        border: 1px solid #b7c4d8; font-weight: 750; min-height: 2.65rem;
        transition: transform .15s ease, box-shadow .15s ease;
      }
      .stButton > button *, [data-testid="stDownloadButton"] > button * { color: inherit !important; }
      .stButton > button[kind="primary"] {
        background: #1747c7 !important; color: #ffffff !important; border: 1px solid #1747c7 !important;
        box-shadow: 0 8px 16px rgba(23, 71, 199, .20);
      }
      .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover { transform: translateY(-1px); }
      [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, .72); border: 1px dashed #b8c5dd; border-radius: 16px; padding: .55rem;
      }
      [data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }
      [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
      .hero-panel {
        margin: 1.35rem 0 .3rem; padding: 1.25rem 1.45rem; border: 1px solid #dbe4fa;
        border-radius: 20px; background: linear-gradient(120deg, rgba(255,255,255,.9), rgba(234,241,255,.85));
        box-shadow: 0 14px 36px rgba(31, 55, 97, .07);
      }
      .hero-panel strong { color: #2547a6; }
      .hero-panel span { color: var(--muted); }
      [data-testid="stSidebar"] { background: rgba(247, 249, 253, .96); border-right: 1px solid var(--border); }
      .sidebar-title { color: #7b879c; font-size: .72rem; font-weight: 800; letter-spacing: .11em; margin-bottom: .65rem; }
      .sidebar-step { color: #4a5870; padding: .42rem 0; border-bottom: 1px solid #e9edf4; font-size: .92rem; }
      .topline { display: flex; align-items: center; gap: .7rem; margin: .15rem 0 1.2rem; }
      .brand-mark {
        width: 2.3rem; height: 2.3rem; display: grid; place-items: center; border-radius: 11px;
        background: linear-gradient(135deg, #2e57d0, #6d89ff); color: #fff; font-size: .78rem;
        font-weight: 850; letter-spacing: -.04em; box-shadow: 0 8px 20px rgba(46, 87, 208, .24);
      }
      .brand-name { color: #172033; font-size: 1rem; font-weight: 820; letter-spacing: -.025em; }
      .brand-meta { margin-left: auto; color: #60708a; font-size: .82rem; font-weight: 650; }
      .dashboard-hero {
        position: relative; overflow: hidden; display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(250px, .7fr);
        gap: 2rem; min-height: 285px; padding: 2.5rem 2.7rem; border-radius: 26px;
        background: linear-gradient(125deg, #101d39 0%, #17336d 56%, #3763d5 135%);
        box-shadow: 0 24px 52px rgba(22, 48, 103, .22);
      }
      .dashboard-hero:before, .dashboard-hero:after {
        content: ""; position: absolute; border-radius: 50%; pointer-events: none;
      }
      .dashboard-hero:before { width: 28rem; height: 28rem; right: -12rem; top: -16rem; border: 1px solid rgba(255,255,255,.15); }
      .dashboard-hero:after { width: 19rem; height: 19rem; right: 4rem; bottom: -15rem; background: rgba(101, 157, 255, .16); }
      .hero-copy, .hero-insight { position: relative; z-index: 1; }
      .hero-kicker { color: #b8c9ff; font-size: .72rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
      .hero-copy h1 { max-width: 640px; margin: .65rem 0 .8rem; color: #fff !important; font-size: clamp(2.4rem, 5vw, 4.25rem) !important; line-height: .98; }
      .hero-copy h1 em { color: #9cc4ff; font-style: normal; }
      .hero-copy p { max-width: 610px; margin: 0; color: #d6e2ff; font-size: 1.05rem; line-height: 1.55; }
      .hero-insight { align-self: end; padding: 1.15rem; border: 1px solid rgba(255,255,255,.18); border-radius: 18px; background: rgba(8, 21, 51, .28); backdrop-filter: blur(10px); }
      .hero-insight-label { color: #aec5ff; font-size: .71rem; font-weight: 780; letter-spacing: .1em; text-transform: uppercase; }
      .hero-insight strong { display: block; margin: .38rem 0 .25rem; color: #fff; font-size: 1.15rem; }
      .hero-insight span { color: #d3e0ff; font-size: .87rem; line-height: 1.4; }
      .action-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: .7rem; margin: 1rem 0 .2rem; }
      .action-chip { padding: .85rem 1rem; border: 1px solid #e4e9f3; border-radius: 14px; background: rgba(255,255,255,.8); box-shadow: 0 6px 16px rgba(30,52,90,.04); }
      .action-chip b { display: block; color: #223252; font-size: .88rem; }
      .action-chip span { color: #71809a; font-size: .78rem; }
      .stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
        background: #ffffff !important; border: 1px solid #cbd6e7 !important; border-radius: 11px !important;
        box-shadow: 0 3px 10px rgba(36, 57, 96, .03) !important;
      }
      [data-testid="stTabs"] [role="tablist"] { gap: .35rem; padding: .36rem; border: 1px solid #e1e7f1; border-radius: 16px; background: rgba(255,255,255,.75); }
      @media (max-width: 760px) {
        .dashboard-hero { grid-template-columns: 1fr; padding: 1.8rem; }
        .hero-insight { align-self: auto; }
        .action-strip { grid-template-columns: 1fr; }
        .brand-meta { display: none; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("<div class='sidebar-title'>YOUR JOB-SEARCH WORKFLOW</div>", unsafe_allow_html=True)
    for step in ["1. Upload your resume", "2. Find matching roles", "3. Tailor your application", "4. Track your progress"]:
        st.markdown(f"<div class='sidebar-step'>{step}</div>", unsafe_allow_html=True)
    st.divider()
    active_sidebar_resume = db.get_active_resume()
    if active_sidebar_resume:
        st.success(f"Resume ready: {active_sidebar_resume['filename']}")
    else:
        st.info("Start by uploading a resume.")

st.markdown(
    """
    <div class="topline">
      <div class="brand-mark">JH</div>
      <div class="brand-name">Job Hunt Copilot</div>
      <div class="brand-meta">Your focused career workspace</div>
    </div>
    <section class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-kicker">Career intelligence, simplified</div>
        <h1>Career moves,<br><em>made sharper.</em></h1>
        <p>Turn your real experience into a focused job search, clearer applications, and a simple view of every next step.</p>
      </div>
      <div class="hero-insight">
        <div class="hero-insight-label">Built around your evidence</div>
        <strong>Experience first</strong>
        <span>Each match, skill gap, and document stays grounded in your resume and project history.</span>
      </div>
    </section>
    <div class="action-strip">
      <div class="action-chip"><b>01 &nbsp; Build your profile</b><span>Upload a resume and verify your experience.</span></div>
      <div class="action-chip"><b>02 &nbsp; Find the right roles</b><span>Rank openings using real job requirements.</span></div>
      <div class="action-chip"><b>03 &nbsp; Apply with confidence</b><span>Tailor documents and track every move.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_resume, tab_fetch, tab_dashboard, tab_tracker, tab_rag = st.tabs(
    ["📄 Resume", "🔍 Fetch Jobs", "📊 Dashboard", "🗂️ Applications & Analytics", "🧠 Career RAG"]
)

# ---------------------------------------------------------------- Resume tab
with tab_resume:
    st.subheader("Upload your resume")
    st.caption("Start here. Your resume is used to rank jobs and keep generated content grounded in your real experience.")
    uploaded = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])

    active = db.get_active_resume()
    if uploaded is not None:
        with st.spinner("Extracting and structuring your profile..."):
            raw_text = extract_text(uploaded.read(), uploaded.name)
            profile = parse_profile(raw_text)
            db.save_resume(uploaded.name, raw_text, json.dumps(profile))
        st.success(f"Parsed and saved: {uploaded.name}")
        active = db.get_active_resume()

    if active:
        profile = json.loads(active["profile_json"])
        st.markdown(f"**Active resume:** {active['filename']}")
        st.json(profile, expanded=False)
    else:
        st.info("No resume uploaded yet.")

# ------------------------------------------------------------------ Fetch tab
with tab_fetch:
    st.subheader("Fetch matching jobs")
    st.caption("Choose a few clear search terms and sources. Results are ranked against your saved profile.")
    active = db.get_active_resume()
    if not active:
        st.warning("Upload a resume first — matching is based on your profile, not just keywords.")
    else:
        profile = json.loads(active["profile_json"])
        default_roles = [
            "GenAI Engineer",
            "Machine Learning Engineer",
            "Data Scientist",
            "AI Engineer",
            "AI/ML Engineer",
            "Applied AI Engineer",
        ]
        profile_titles = [title for title in profile.get("target_titles", []) if title]
        default_queries = ", ".join(dict.fromkeys(default_roles + profile_titles))

        queries_input = st.text_input("Search terms (comma-separated)", value=default_queries)
        st.info(
            "Jobs are not ranked by title alone. Each job's full description and requirements are "
            "compared semantically with your summary, skills, roles, and every saved experience bullet."
        )
        countries = st.multiselect(
            "Countries (Adzuna)", ["Ireland", "Germany", "UK"], default=["Ireland", "Germany"]
        )
        sources = st.multiselect(
            "Sources",
            ["adzuna", "arbeitnow", "remotive", "greenhouse", "lever"],
            default=["adzuna", "arbeitnow", "remotive"],
        )

        with st.expander("Greenhouse / Lever company list (optional)"):
            st.caption(
                "These two APIs are per-company (no cross-company search). "
                "Enter company board slugs, e.g. the 'stripe' in careers.greenhouse.io/stripe."
            )
            gh_tokens_input = st.text_input("Greenhouse company tokens (comma-separated)", value="")
            lever_slugs_input = st.text_input("Lever company slugs (comma-separated)", value="")

        if st.button("Run fetch pipeline", type="primary"):
            queries = [q.strip() for q in queries_input.split(",") if q.strip()]
            gh_tokens = [t.strip() for t in gh_tokens_input.split(",") if t.strip()] or None
            lever_slugs = [s.strip() for s in lever_slugs_input.split(",") if s.strip()] or None
            with st.spinner("Running fetch → score → store pipeline..."):
                result = run_pipeline(
                    queries=queries,
                    countries=countries,
                    profile=profile,
                    sources=sources,
                    greenhouse_tokens=gh_tokens,
                    lever_slugs=lever_slugs,
                )
            st.success(f"Stored {result.get('stored_count', 0)} new jobs.")
            with st.expander("Pipeline log"):
                st.write(result.get("log", []))

        st.divider()
        st.markdown("**Or paste a specific job URL**")
        url = st.text_input("Job posting URL")
        if st.button("Fetch this job"):
            with st.spinner("Fetching and parsing job page..."):
                job = manual_url.fetch_and_parse(url)
                from src.matcher import score_jobs

                scored = score_jobs(profile, [job])
                new_id = db.upsert_job(scored[0])
            if new_id:
                st.success(f"Added: {job['title']} at {job['company']}")
            else:
                st.info("Already have this job saved.")

# -------------------------------------------------------------- Dashboard tab
with tab_dashboard:
    st.subheader("All jobs")
    st.caption("Review your strongest matches, export a shortlist, and tailor documents for the roles worth pursuing.")
    min_score = st.slider("Minimum match score", 0.0, 1.0, 0.0, 0.05)
    rows = db.list_jobs(min_score=min_score)

    if not rows:
        st.info("No jobs yet — fetch some in the previous tab.")
    else:
        df = pd.DataFrame([dict(r) for r in rows])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total jobs", len(df))
        col2.metric("Avg match score", f"{df['match_score'].mean():.2f}" if df["match_score"].notna().any() else "—")
        col3.metric("Sources", df["source"].nunique())

        c1, c2 = st.columns(2)
        with c1:
            st.bar_chart(df["country"].value_counts())
        with c2:
            st.bar_chart(df["source"].value_counts())

        st.dataframe(
            df[["id", "title", "company", "location", "country", "source", "match_score", "url"]],
            use_container_width=True,
            hide_index=True,
        )

        if st.button("Export to Excel"):
            path = export_jobs_to_excel(min_score=min_score)
            with open(path, "rb") as f:
                st.download_button("Download jobs_export.xlsx", f, file_name="jobs_export.xlsx")

        st.divider()
        st.subheader("Generate tailored resume + cover letter")
        job_id = st.selectbox("Pick a job", df["id"].tolist(), format_func=lambda i: f"#{i} — {df[df['id']==i]['title'].values[0]}")

        gen_col, gap_col = st.columns(2)
        with gen_col:
            if st.button("Generate tailored docs", type="primary"):
                active = db.get_active_resume()
                if not active:
                    st.warning("Upload a resume first.")
                else:
                    profile = json.loads(active["profile_json"])
                    job = dict(db.get_job(job_id))
                    with st.spinner("Tailoring resume and writing cover letter..."):
                        out = generate_for_job(profile, job, job_id)
                        db.save_generated_docs(job_id, out["resume_path"], out["cover_letter_path"])
                    st.success(f"Done (cache: {out['cache_hit']}).")

                    d1, d2 = st.columns(2)
                    with d1:
                        with open(out["resume_path"], "rb") as f:
                            st.download_button("⬇️ Tailored resume (.docx)", f, file_name=f"resume_job{job_id}.docx")
                    with d2:
                        with open(out["cover_letter_path"], "rb") as f:
                            st.download_button("⬇️ Cover letter (.docx)", f, file_name=f"cover_letter_job{job_id}.docx")

        with gap_col:
            if st.button("Analyze skill gap"):
                active = db.get_active_resume()
                if not active:
                    st.warning("Upload a resume first.")
                else:
                    profile = json.loads(active["profile_json"])
                    job = dict(db.get_job(job_id))
                    with st.spinner("Comparing your profile against this job..."):
                        gap = analyze_skill_gap(profile, job["title"], job.get("description", ""))
                    st.markdown("**Matched:** " + ", ".join(gap.get("matched_skills", [])))
                    st.markdown("**Missing:** " + ", ".join(gap.get("missing_skills", [])))
                    if gap.get("roadmap"):
                        st.markdown("**Roadmap to close the gap:**")
                        for item in gap["roadmap"]:
                            st.markdown(f"- **{item.get('skill')}** ({item.get('estimate')}) — {item.get('note')}")

        st.divider()
        st.subheader("Track this application")
        current = db.get_application(job_id)
        current_stage = current["stage"] if current else "saved"
        stage = st.selectbox(
            "Stage",
            applications.STAGES,
            index=applications.STAGES.index(current_stage),
        )
        notes = st.text_area("Notes", value=current["notes"] if current and current["notes"] else "")
        if st.button("Save application status"):
            applications.set_stage(job_id, stage, notes)
            st.success(f"Marked job #{job_id} as '{stage}'.")

# ---------------------------------------------------------- Tracker/Analytics
with tab_tracker:
    st.subheader("Application funnel")
    st.caption("A quick view of where every application stands and how your search is progressing.")
    stats = applications.get_analytics()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tracked", stats["total_tracked"])
    m2.metric("Applied+", stats["applied_count"])
    m3.metric("Offers", stats["offers"])
    m4.metric(
        "Acceptance rate",
        f"{stats['acceptance_rate']*100:.0f}%" if stats["applied_count"] else "—",
    )

    if stats["stage_counts"]:
        st.bar_chart(pd.Series(stats["stage_counts"]))

    if stats["top_companies"]:
        st.markdown("**Top companies applied to:** " + ", ".join(f"{c} ({n})" for c, n in stats["top_companies"]))

    st.divider()
    st.subheader("All tracked applications")
    apps = db.list_applications()
    if not apps:
        st.info("Nothing tracked yet — set a stage from the Dashboard tab.")
    else:
        apps_df = pd.DataFrame([dict(a) for a in apps])
        st.dataframe(
            apps_df[["job_id", "title", "company", "stage", "match_score", "updated_at"]],
            use_container_width=True,
            hide_index=True,
        )

# ------------------------------------------------------------------- RAG tab
with tab_rag:
    st.subheader("Ask about your career history")
    st.caption("Search your project notes for accurate details to use in applications and interviews.")
    st.caption(
        "Grounded in your detailed project write-ups in data/career_docs/ — "
        "the same corpus used to add richer context when tailoring resumes."
    )

    if st.button("(Re)build career RAG index"):
        with st.spinner("Indexing career_docs/..."):
            rag.build_index()
        st.success("Index built.")

    question = st.text_input("e.g. 'Which of my projects mention RAGAS or faithfulness scores?'")
    if st.button("Ask", type="primary") and question:
        with st.spinner("Retrieving and answering..."):
            try:
                result = rag.answer(question)
            except FileNotFoundError:
                st.warning("No index yet — click '(Re)build career RAG index' above first.")
            else:
                st.markdown(result["answer"])
                st.caption("Sources: " + ", ".join(result["sources"]))
