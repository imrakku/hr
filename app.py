# app.py

# --- 1. Import Libraries ---
import streamlit as st
import os
import json
import time
import requests
import csv
import io
import pandas as pd
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# --- 2. Configuration ---
# NOTE: In a real-world app, store API keys securely (e.g., in Streamlit secrets)
API_KEY = "AIzaSyCLbK8gHVZ5OtIkbAefprWTBYSILVIHMng"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
CV_EXTENSIONS = ('.txt', '.pdf')

# --- Foundational Analysis & Extraction Prompt ---
FOUNDATIONAL_ANALYSIS_PROMPT = """
You are a meticulous data extraction assistant. Your task is to analyze a candidate's CV against a job description (JD) and extract every single piece of relevant information. Do not perform any scoring or filtering. Your output must be a single, complete JSON object.

**JSON Schema:**
`{{
  "matched_skills_full": [STRING],
  "missing_skills_full": [STRING],
  "top_qualifications_full": [STRING],
  "quantifiable_achievements_full": [STRING],
  "relevant_experience_summary": STRING
}}`

**Instructions:**
1.  `matched_skills_full`: List all skills from the JD present in the CV.
2.  `missing_skills_full`: List all skills from the JD not present in the CV.
3.  `top_qualifications_full`: List all relevant degrees, certifications, and licenses.
4.  `quantifiable_achievements_full`: **Find and list all achievements with numbers, percentages, currency, or metrics (e.g., "managed a team of 10", "increased revenue by 15%", "led a project", "budgeted 5 crore", "drove growth").**
5.  `relevant_experience_summary`: Provide a 1-2 paragraph summary of the candidate's work history as it relates directly to the JD's requirements.

**JD:**
{jd_text}

**CV:**
{cv_text}
"""

# --- New Prompt for Strengths & Weaknesses Analysis ---
STRENGTHS_WEAKNESSES_PROMPT = """
You are an expert HR analyst. Based on the following candidate data and JD, provide a concise, professional analysis of the candidate's strengths and weaknesses.

**Instructions:**
* **Strengths:** Write a single paragraph (2-3 sentences) summarizing the candidate's top strengths. Focus on their most relevant skills, experience, and quantifiable achievements.
* **Weaknesses:** Write a single paragraph (2-3 sentences) summarizing their key weaknesses. Focus on critical missing skills, lack of relevant experience for the role, or other significant gaps.

**Candidate Data:**
{candidate_data_json}

**JD:**
{jd_text}
"""
# --- Helper Functions ---
@st.cache_data
def read_uploaded_file(uploaded_file):
    """Reads the content of an uploaded file."""
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        try:
            reader = PdfReader(uploaded_file)
            if reader.is_encrypted:
                st.warning(f"PDF '{uploaded_file.name}' is encrypted. Skipping.")
                return None
            if not reader.pages:
                st.warning(f"PDF '{uploaded_file.name}' contains no readable pages.")
                return None
            
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except PdfReadError as e:
            st.error(f"Corrupted PDF file '{uploaded_file.name}': {e}")
            return None
        except Exception as e:
            st.error(f"General error reading PDF file '{uploaded_file.name}': {e}")
            return None
    return None

def call_gemini_api(prompt, response_mime_type=None, response_schema=None):
    """
    Handles API calls with exponential backoff and specified output format.
    Returns parsed JSON or raw text.
    """
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if response_mime_type and response_schema:
        payload["generationConfig"] = {
            "responseMimeType": response_mime_type,
            "responseSchema": response_schema
        }

    MAX_RETRIES = 5
    for i in range(MAX_RETRIES):
        try:
            response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            content_part = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
            
            if not content_part:
                raise ValueError("API response lacked expected content.")
            
            if response_mime_type == "application/json":
                return json.loads(content_part)
            return content_part

        except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
            if i < MAX_RETRIES - 1:
                delay = 2**i * 1
                time.sleep(delay)
            else:
                return f"API/Network Error: {e}"
    return "API call failed after max retries."
    
def parse_markdown_table(table_string, filename):
    """Parses a Markdown table string into a dictionary."""
    lines = table_string.strip().split('\n')
    if len(lines) < 3:
        return {"filename": filename, "error": "Table is too short or malformed."}
    
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    data_row = [d.strip() for d in lines[2].split('|') if d.strip()]
    
    if len(headers) != len(data_row):
        return {"filename": filename, "error": "Table headers and data columns do not match."}
    
    result = dict(zip(headers, data_row))
    result['filename'] = filename
    return result

def to_csv_string(results):
    """Converts a list of dicts to a CSV string."""
    if not results:
        return ""
    
    fieldnames = ['filename', 'Score', 'Fit', 'Rationale', 'Matched Skills', 'Missing Skills', 'Top Qualifications', 'Quantifiable Achievements']
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue()


# --- Main Streamlit App ---

st.set_page_config(page_title="IIM Sirmaur HR Tool", layout="wide", page_icon="🏛️")

# Custom CSS for a professional look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
    }
    .st-emotion-cache-18ni2y2 {
        background: rgba(0, 0, 0, 0.0);
        padding: 0;
    }
    .st-emotion-cache-h4y6m4 {
        padding-top: 2rem;
    }
    .iim-header {
        text-align: center;
        font-family: 'Roboto', sans-serif;
        color: #004b8d; /* IIM Blue */
        margin-bottom: 0.5em;
    }
    .iim-header h1 {
        font-size: 3em;
        font-weight: 700;
        margin-bottom: 0.1em;
    }
    .iim-header p {
        font-size: 1.2em;
        color: #666;
    }
    .st-emotion-cache-16j0h4c {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .st-emotion-cache-1v03n4r {
        border-radius: 10px;
    }
    .reportview-container .main .block-container{
        padding-top: 5rem;
        padding-right: 5rem;
        padding-left: 5rem;
        padding-bottom: 5rem;
    }
    .st-expanderHeader {
        font-size: 1.1em;
        font-weight: bold;
        color: #004b8d;
    }
    .st-expanderContent {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 15px;
        margin-top: 5px;
    }
    .stButton>button {
        color: #fff;
        background-color: #004b8d;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 1.1em;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
    }
    .stDataFrame {
        border-radius: 10px;
    }
    .st-emotion-cache-r4239k {
        font-size: 1.2em;
        font-weight: bold;
    }
    
    /* Custom badges for fit */
    .badge-high {
        background-color: #4CAF50; /* Green */
        color: white;
        padding: 4px 8px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
    .badge-medium {
        background-color: #FFC107; /* Amber */
        color: #333;
        padding: 4px 8px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
    .badge-low {
        background-color: #F44336; /* Red */
        color: white;
        padding: 4px 8px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Main App Header with IIM Sirmaur branding
st.markdown("<div class='iim-header'><h1>IIM Sirmaur</h1><p>AI-Powered HR Evaluation Tool</p></div>", unsafe_allow_html=True)

# Main container for the app
main_container = st.container()

with main_container:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Job Description")
        jd_file = st.file_uploader("Upload a PDF or TXT file for the Job Description", type=["pdf", "txt"], key="jd_uploader")

    with col2:
        st.subheader("2. Upload Candidate CVs")
        cv_files = st.file_uploader("Upload one or more PDF/TXT files for CVs", type=["pdf", "txt"], accept_multiple_files=True, key="cv_uploader")

    st.markdown("---")
    
    # New: Dynamic Weighting Form
    st.subheader("3. Customize Evaluation Rubric")
    with st.form(key='weight_form'):
        st.markdown("Adjust the importance of each factor to match your specific job requirements.")
        
        col1_w, col2_w, col3_w, col4_w, col5_w = st.columns(5)
        
        with col1_w:
            matched_skills_w = st.slider("Matched Skills (%)", min_value=0, max_value=100, value=50, step=5)
        with col2_w:
            experience_relevance_w = st.slider("Experience Relevance (%)", min_value=0, max_value=100, value=20, step=5)
        with col3_w:
            qualifications_w = st.slider("Qualifications (%)", min_value=0, max_value=100, value=15, step=5)
        with col4_w:
            seniority_w = st.slider("Depth & Seniority (%)", min_value=0, max_value=100, value=10, step=5)
        with col5_w:
            cv_clarity_w = st.slider("CV Clarity (%)", min_value=0, max_value=100, value=5, step=5)
            
        # New: Input for Critical Skills
        critical_skills = st.text_input(
            "Enter Critical Skills (comma-separated)",
            placeholder="e.g., Python, SQL, Project Management"
        )
        
        # New: Button to run the evaluation within the form
        run_button = st.form_submit_button("🚀 Run Evaluation", use_container_width=True)

    if run_button:
        if not jd_file:
            st.error("Please upload a Job Description to begin.")
        elif not cv_files:
            st.warning("Please upload at least one CV file.")
        else:
            with st.spinner("Evaluating candidates..."):
                jd_text = read_uploaded_file(jd_file)
                if not jd_text:
                    st.error("Could not read the Job Description. Please check the file.")
                else:
                    evaluated_results = []
                    progress_bar = st.progress(0, text="Starting evaluation...")

                    # Create a dynamic prompt based on user inputs
                    dynamic_eval_prompt = f"""
You are a strict HR evaluation engine. Your task is to evaluate a candidate based on a complete set of extracted data and provide a final, summarized evaluation in a Markdown table.
Apply heuristics to ensure the score is highly accurate and does not miss any critical connections.

**Evaluation Hierarchy Heuristic:**
1.  **Prioritize Full-Time Experience:** Evaluate and score the candidate's full-time work experience first. This is the most important factor.
2.  **Next, Consider Internships:** After full-time experience, evaluate relevant internships.
3.  **Finally, Consider Projects and Certifications:** Use live projects, open-source work, and certifications as supporting evidence for skills and qualifications.

**Evaluation Rubric:**
* **Scoring (1-10):** Based on the provided data, apply a final weighted score. The score should reflect the overall balance between matched and missing skills, penalizing the absence of key skills but not disproportionately if a candidate is strong in other areas. The weighting is as follows:
    * All Matched Skills ({matched_skills_w}%)
    * Experience Summary Relevance ({experience_relevance_w}%)
    * All Qualifications & Achievements ({qualifications_w}%)
    * Overall Depth & Seniority ({seniority_w}%)
    * CV Clarity ({cv_clarity_w}%)
* **Fit:** High (>=8), Medium (5-7), Low (<=4).
* **Rationale:** A single, concise, and factual sentence that **directly explains why the score is high or low**. For high scores, mention key strengths (e.g., matched skills, experience). For low scores, explicitly state which significant skills are missing.
* **Matched Skills:** A summarized list of the top 3-5 most important matched skills.
* **Missing Skills:** A summarized list of the top 3-5 most critical missing skills.
* **Top Qualifications:** A summarized list of the top 2 most impressive qualifications.
* **Quantifiable Achievements:** A summarized list of the top 2-3 most impactful achievements.

**Candidate Data:**
{{candidate_data_json}}

**Output Table:**
You must produce a single Markdown table with the following headers in this exact order: `Score`, `Fit`, `Rationale`, `Matched Skills`, `Missing Skills`, `Top Qualifications`, `Quantifiable Achievements`.

| Score | Fit | Rationale | Matched Skills | Missing Skills | Top Qualifications | Quantifiable Achievements |
|---|---|---|---|---|---|---|
| {{score}} | {{fit}} | {{rationale}} | {{matched_skills}} | {{missing_skills}} | {{top_qualifications}} | {{quantifiable_achievements}} |
"""
                    # Adding a critical skill heuristic to the prompt
                    if critical_skills:
                        dynamic_eval_prompt += f"""
**Critical Skill Heuristic:**
* A candidate missing any of the following skills must have their score severely penalized, regardless of other factors. The score must be 4 or lower if any of these are missing: **{critical_skills}**.
"""

                    for i, cv_file in enumerate(cv_files):
                        progress_text = f"Processing `{cv_file.name}`..."
                        progress_bar.progress((i) / len(cv_files), text=progress_text)
                        
                        cv_text = read_uploaded_file(cv_file)
                        if not cv_text or not cv_text.strip():
                            continue
                        
                        # --- PHASE 1: Foundational Analysis ---
                        foundational_data_json_schema = {
                            "type": "OBJECT",
                            "properties": {
                                "matched_skills_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "missing_skills_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "top_qualifications_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "quantifiable_achievements_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "relevant_experience_summary": {"type": "STRING"}
                            }
                        }
                        
                        full_prompt_p1 = FOUNDATIONAL_ANALYSIS_PROMPT.format(jd_text=jd_text, cv_text=cv_text)
                        foundational_data = call_gemini_api(full_prompt_p1, "application/json", foundational_data_json_schema)
                        
                        if isinstance(foundational_data, str):
                            st.error(f"Foundational Analysis for {cv_file.name} failed: {foundational_data}")
                            continue
                        
                        # --- PHASE 2: Final Evaluation and Reporting ---
                        candidate_data_string = json.dumps(foundational_data, indent=2)
                        final_table_output = call_gemini_api(dynamic_eval_prompt.format(candidate_data_json=candidate_data_string, matched_skills_w=matched_skills_w, experience_relevance_w=experience_relevance_w, qualifications_w=qualifications_w, seniority_w=seniority_w, cv_clarity_w=cv_clarity_w))

                        if isinstance(final_table_output, str) and "API/Network Error" in final_table_output:
                            st.error(f"Final Evaluation for {cv_file.name} failed: {final_table_output}")
                        else:
                            st.success(f"Evaluation Complete for {cv_file.name}!")
                            
                            # New Feature: Strengths and Weaknesses Analysis
                            analysis_prompt = STRENGTHS_WEAKNESSES_PROMPT.format(
                                candidate_data_json=candidate_data_string,
                                jd_text=jd_text
                            )
                            analysis_result = call_gemini_api(analysis_prompt)
                            
                            parsed_data = parse_markdown_table(final_table_output, cv_file.name)
                            evaluated_results.append(parsed_data)

                            with st.expander(f"**{parsed_data.get('filename')}** - Score: {parsed_data.get('Score')} | Fit: {parsed_data.get('Fit')}"):
                                st.markdown(final_table_output, unsafe_allow_html=True)
                                
                                st.subheader("Strengths & Weaknesses Analysis")
                                if isinstance(analysis_result, str) and "API/Network Error" in analysis_result:
                                    st.warning("Could not generate detailed analysis.")
                                else:
                                    st.markdown(analysis_result)
                                
                                # Show raw data in a simple JSON block
                                st.markdown("### Raw Data Extracted")
                                st.json(foundational_data)
                                
                        progress_bar.progress((i + 1) / len(cv_files), text="All files processed!")

                st.markdown("---")
                st.subheader("Final Evaluation Report")
                
                if evaluated_results:
                    df_results = pd.DataFrame(evaluated_results)
                    df_results["Score"] = pd.to_numeric(df_results["Score"], errors='coerce')
                    
                    # Ensure filename is the first column
                    cols = ['filename'] + [col for col in df_results if col != 'filename']
                    df_results = df_results[cols]
                    
                    # Sort results by score, descending
                    df_results = df_results.sort_values(by="Score", ascending=False)
                    
                    # Display summary counts
                    high_count = len(df_results[df_results['Fit'] == 'High'])
                    medium_count = len(df_results[df_results['Fit'] == 'Medium'])
                    low_count = len(df_results[df_results['Fit'] == 'Low'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="High Fit", value=high_count)
                    with col2:
                        st.metric(label="Medium Fit", value=medium_count)
                    with col3:
                        st.metric(label="Low Fit", value=low_count)

                    # Display the DataFrame
                    st.dataframe(df_results, use_container_width=True)

                    # Download button
                    csv_string = to_csv_string(evaluated_results)
                    st.download_button(
                        label="Download CSV Report",
                        data=csv_string,
                        file_name="hr_evaluation_report.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
