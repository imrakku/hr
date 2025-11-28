import streamlit as st
import pandas as pd
import traceback
from datetime import datetime

from config import GEMINI_API_KEY
from file_handler import read_uploaded_file
from ai_service import AIService
from evaluator import compute_fallback_score, parse_markdown_table
from database import DatabaseManager
from utils import to_csv_string, format_score_color, truncate_text
from styles import get_custom_css

st.set_page_config(
    page_title="IIM Sirmaur HR Tool",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()

if 'ai_service' not in st.session_state:
    st.session_state.ai_service = AIService()

def render_sidebar():
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Select Page",
            ["New Evaluation", "View History", "Analytics"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### About")
        st.info("IIM Sirmaur AI-Powered HR Evaluation Tool for streamlined candidate screening.")

        return page

def render_evaluation_page():
    st.markdown("<div class='iim-header'><h1>IIM Sirmaur</h1><p>AI-Powered HR Evaluation Tool</p></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Upload Job Description")
        jd_file = st.file_uploader(
            "Upload a PDF or TXT file for the Job Description",
            type=["pdf", "txt"],
            key="jd_uploader",
            help="Upload the job description document"
        )
        job_title = st.text_input(
            "Job Title",
            placeholder="e.g., Senior Data Scientist",
            help="Enter the job title for tracking purposes"
        )

    with col2:
        st.subheader("2. Upload Candidate CVs")
        cv_files = st.file_uploader(
            "Upload one or more PDF/TXT files for CVs",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key="cv_uploader",
            help="Upload multiple candidate resumes"
        )

    st.markdown("---")
    st.subheader("3. Customize Evaluation Rubric")

    with st.form(key='weight_form'):
        st.markdown("Adjust the importance of each factor to match your specific job requirements.")

        col1_w, col2_w, col3_w, col4_w, col5_w = st.columns(5)

        with col1_w:
            matched_skills_w = st.slider("Matched Skills (%)", 0, 100, 50, 5)
        with col2_w:
            experience_relevance_w = st.slider("Experience Relevance (%)", 0, 100, 20, 5)
        with col3_w:
            qualifications_w = st.slider("Qualifications (%)", 0, 100, 15, 5)
        with col4_w:
            seniority_w = st.slider("Depth & Seniority (%)", 0, 100, 10, 5)
        with col5_w:
            cv_clarity_w = st.slider("CV Clarity (%)", 0, 100, 5, 5)

        total_weight = matched_skills_w + experience_relevance_w + qualifications_w + seniority_w + cv_clarity_w

        if total_weight != 100:
            st.warning(f"Total weight is {total_weight}%. Consider adjusting to 100% for balanced evaluation.")

        critical_skills = st.text_input(
            "Enter Critical Skills (comma-separated)",
            placeholder="e.g., Python, SQL, Project Management",
            help="Skills that are absolutely required for the position"
        )

        save_to_db = st.checkbox("Save results to database", value=True)

        run_button = st.form_submit_button("Run Evaluation", use_container_width=True)

    if run_button:
        if not jd_file:
            st.error("Please upload a Job Description to begin.")
            return

        if not cv_files:
            st.warning("Please upload at least one CV file.")
            return

        if not job_title:
            st.warning("Please enter a job title for tracking purposes.")
            job_title = "Untitled Position"

        jd_text = read_uploaded_file(jd_file)
        if not jd_text:
            st.error("Could not read the Job Description. Please check the file.")
            return

        evaluated_results = []
        progress_bar = st.progress(0, text="Starting evaluation...")

        weights = {
            "matched_skills_w": matched_skills_w,
            "experience_relevance_w": experience_relevance_w,
            "qualifications_w": qualifications_w,
            "seniority_w": seniority_w,
            "cv_clarity_w": cv_clarity_w
        }
        critical_skills_list = [s.strip() for s in critical_skills.split(",")] if critical_skills else []

        for i, cv_file in enumerate(cv_files):
            try:
                progress_bar.progress((i) / len(cv_files), text=f"Processing {cv_file.name}...")

                cv_text = read_uploaded_file(cv_file)
                if not cv_text:
                    st.warning(f"Skipping {cv_file.name}: could not read content.")
                    continue

                foundational_data = st.session_state.ai_service.extract_candidate_data(jd_text, cv_text)

                final_table_output = st.session_state.ai_service.evaluate_candidate(foundational_data, weights)

                parsed_data = {}
                parsed_from_llm = False

                if isinstance(final_table_output, str) and final_table_output and not final_table_output.startswith("API/Network Error"):
                    parsed_try = parse_markdown_table(final_table_output, cv_file.name)
                    if parsed_try and 'error' not in parsed_try and (parsed_try.get("Score") or parsed_try.get("Fit")):
                        parsed_data = parsed_try
                        parsed_from_llm = True

                if not parsed_from_llm:
                    fb_score, fb_fit, fb_rationale = compute_fallback_score(foundational_data, cv_text, weights, critical_skills_list)
                    score_str = str(int(fb_score)) if float(fb_score).is_integer() else str(round(fb_score, 1))

                    parsed_data = {
                        "filename": cv_file.name,
                        "Score": score_str,
                        "Fit": fb_fit,
                        "Rationale": fb_rationale,
                        "Matched Skills": ", ".join(foundational_data.get("matched_skills_full", []) or []),
                        "Missing Skills": ", ".join(foundational_data.get("missing_skills_full", []) or []),
                        "Top Qualifications": ", ".join(foundational_data.get("top_qualifications_full", []) or []),
                        "Quantifiable Achievements": "; ".join(foundational_data.get("quantifiable_achievements_full", []) or [])
                    }

                score_header = parsed_data.get("Score") or "N/A"
                fit_header = parsed_data.get("Fit") or "N/A"
                score_class = format_score_color(score_header)

                with st.expander(f"**{cv_file.name}** - Score: {score_header} | Fit: {fit_header}"):
                    st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                    st.markdown(f"<span class='{score_class}'>Score: {score_header}/10</span> | Fit: {fit_header}", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown("**Matched Skills**")
                        st.success(parsed_data.get("Matched Skills") or "None identified")

                        st.markdown("**Top Qualifications**")
                        st.info(parsed_data.get("Top Qualifications") or "None identified")

                    with col_b:
                        st.markdown("**Missing Skills**")
                        st.error(parsed_data.get("Missing Skills") or "None identified")

                        st.markdown("**Quantifiable Achievements**")
                        st.success(parsed_data.get("Quantifiable Achievements") or "None identified")

                    st.markdown("**Rationale**")
                    st.write(parsed_data.get("Rationale", ""))

                    analysis_result = st.session_state.ai_service.analyze_strengths_weaknesses(foundational_data, jd_text)

                    if isinstance(analysis_result, str) and not analysis_result.startswith("API/Network Error"):
                        st.markdown("### Strengths & Weaknesses Analysis")
                        st.markdown(analysis_result)

                    with st.expander("View Raw Extracted Data"):
                        st.json(foundational_data)

                evaluated_results.append(parsed_data)

                if save_to_db:
                    candidate_name = cv_file.name.replace('.pdf', '').replace('.txt', '').replace('_', ' ')
                    st.session_state.db.save_evaluation(job_title, candidate_name, parsed_data)

            except Exception as e:
                st.error(f"Error processing {getattr(cv_file,'name', 'file')}: {e}")
                st.text(traceback.format_exc())
                continue

        progress_bar.progress(1.0, text="All files processed!")

        st.markdown("---")
        st.subheader("Final Evaluation Report")

        if evaluated_results:
            df_results = pd.DataFrame(evaluated_results)
            df_results["Score"] = pd.to_numeric(df_results.get("Score", None), errors='coerce')

            if 'filename' in df_results.columns:
                cols = ['filename'] + [c for c in df_results.columns if c != 'filename']
                df_results = df_results[cols]

            df_results = df_results.sort_values(by="Score", ascending=False, na_position='last')

            high_count = len(df_results[df_results['Fit'] == 'High']) if 'Fit' in df_results.columns else 0
            medium_count = len(df_results[df_results['Fit'] == 'Medium']) if 'Fit' in df_results.columns else 0
            low_count = len(df_results[df_results['Fit'] == 'Low']) if 'Fit' in df_results.columns else 0

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Candidates", len(evaluated_results))
            with c2:
                st.metric("High Fit", high_count, delta=None, delta_color="normal")
            with c3:
                st.metric("Medium Fit", medium_count, delta=None)
            with c4:
                st.metric("Low Fit", low_count, delta=None)

            st.dataframe(df_results, use_container_width=True, height=400)

            csv_data = to_csv_string(evaluated_results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            st.download_button(
                "Download CSV Report",
                data=csv_data,
                file_name=f"hr_evaluation_report_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No results to display.")

def render_history_page():
    st.markdown("<div class='iim-header'><h1>Evaluation History</h1><p>View past candidate evaluations</p></div>", unsafe_allow_html=True)

    evaluations = st.session_state.db.get_all_evaluations(limit=200)

    if not evaluations:
        st.info("No evaluation history found. Start by running an evaluation!")
        return

    df = pd.DataFrame(evaluations)

    st.subheader("Filter Options")
    col1, col2 = st.columns(2)

    with col1:
        job_titles = ["All"] + sorted(list(set(df['job_title'].tolist())))
        selected_job = st.selectbox("Filter by Job Title", job_titles)

    with col2:
        fit_levels = ["All", "High", "Medium", "Low"]
        selected_fit = st.selectbox("Filter by Fit Level", fit_levels)

    filtered_df = df.copy()

    if selected_job != "All":
        filtered_df = filtered_df[filtered_df['job_title'] == selected_job]

    if selected_fit != "All":
        filtered_df = filtered_df[filtered_df['fit_level'] == selected_fit]

    st.markdown("---")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Total Evaluations", len(filtered_df))
    with col_b:
        avg_score = filtered_df['score'].mean() if len(filtered_df) > 0 else 0
        st.metric("Average Score", f"{avg_score:.1f}")
    with col_c:
        high_fit_count = len(filtered_df[filtered_df['fit_level'] == 'High'])
        st.metric("High Fit Candidates", high_fit_count)

    st.dataframe(
        filtered_df[['candidate_name', 'job_title', 'score', 'fit_level', 'evaluated_at']].sort_values('score', ascending=False),
        use_container_width=True,
        height=400
    )

    if len(filtered_df) > 0:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "Download Filtered History",
            data=csv_data,
            file_name="evaluation_history.csv",
            mime="text/csv",
            use_container_width=True
        )

def render_analytics_page():
    st.markdown("<div class='iim-header'><h1>Analytics Dashboard</h1><p>Insights from candidate evaluations</p></div>", unsafe_allow_html=True)

    evaluations = st.session_state.db.get_all_evaluations(limit=500)

    if not evaluations or len(evaluations) == 0:
        st.info("No data available for analytics. Run evaluations first!")
        return

    df = pd.DataFrame(evaluations)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Evaluations", len(df))
    with col2:
        avg_score = df['score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}/10")
    with col3:
        high_fit_pct = (len(df[df['fit_level'] == 'High']) / len(df) * 100) if len(df) > 0 else 0
        st.metric("High Fit Rate", f"{high_fit_pct:.1f}%")
    with col4:
        unique_jobs = df['job_title'].nunique()
        st.metric("Job Positions", unique_jobs)

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Score Distribution")
        score_ranges = pd.cut(df['score'], bins=[0, 4, 7, 10], labels=['Low (0-4)', 'Medium (4-7)', 'High (7-10)'])
        score_dist = score_ranges.value_counts().sort_index()
        st.bar_chart(score_dist)

    with col_b:
        st.subheader("Fit Level Distribution")
        fit_dist = df['fit_level'].value_counts()
        st.bar_chart(fit_dist)

    st.markdown("---")
    st.subheader("Top Candidates Across All Positions")

    top_candidates = st.session_state.db.get_top_candidates(limit=10)
    if top_candidates:
        top_df = pd.DataFrame(top_candidates)
        st.dataframe(
            top_df[['candidate_name', 'job_title', 'score', 'fit_level']],
            use_container_width=True
        )

def main():
    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
        return

    page = render_sidebar()

    if page == "New Evaluation":
        render_evaluation_page()
    elif page == "View History":
        render_history_page()
    elif page == "Analytics":
        render_analytics_page()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Fatal error running app. See traceback below.")
        st.text(traceback.format_exc())
