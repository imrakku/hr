# app.py (full — includes robust parsing + normalization for Score/Fit)

# --- 1. Import Libraries ---
import streamlit as st
import os
import json
import time
import requests
import csv
import io
import re
import pandas as pd
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# --- 2. Configuration ---
API_KEY = "AIzaSyCLbK8gHVZ5OtIkbAefprWTBYSILVIHMng"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
CV_EXTENSIONS = ('.txt', '.pdf')

# --- Prompts ---
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
4.  `quantifiable_achievements_full`: **Find and list all achievements with numbers, percentages, currency, or metrics.**
5.  `relevant_experience_summary`: Provide a 1-2 paragraph summary of the candidate's work history as it relates directly to the JD's requirements.

**JD:**
{jd_text}

**CV:**
{cv_text}
"""

STRENGTHS_WEAKNESSES_PROMPT = """
You are an expert HR analyst. Based on the following candidate data and JD, provide a concise, professional analysis of the candidate's strengths and weaknesses.

**Instructions:**
* **Strengths:** Write a single paragraph (2-3 sentences) summarizing the candidate's top strengths.
* **Weaknesses:** Write a single paragraph (2-3 sentences) summarizing their key weaknesses.

**Candidate Data:**
{candidate_data_json}

**JD:**
{jd_text}
"""

# --- Helper Functions ---
@st.cache_data
def read_uploaded_file(uploaded_file):
    """Reads the content of an uploaded file (TXT or PDF)."""
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
    Returns parsed JSON or raw text. On persistent failure returns a string starting with "API/Network Error:".
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
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
                time.sleep(2**i)
            else:
                return f"API/Network Error: {e}"
    return "API call failed after max retries."

def strip_code_fences(text):
    """Remove triple-backtick code fences (and optional language tags)."""
    return re.sub(r"```(?:[\s\S]*?)```", lambda m: m.group(0).strip("`"), text, flags=re.MULTILINE)

def find_first_markdown_table_block(lines):
    """
    Find first contiguous markdown-table block (header, separator, data...).
    Returns tuple(start_index, end_index) or (None, None).
    """
    for i in range(len(lines) - 2):
        header = lines[i].strip()
        sep = lines[i+1].strip()
        if '|' not in header:
            continue
        if re.fullmatch(r'[|\s:-]+', sep):
            j = i + 2
            while j < len(lines) and '|' in lines[j]:
                j += 1
            return i, j
    return None, None

def parse_markdown_table(table_string, filename):
    """
    Robustly parse the first markdown-style table found in table_string.
    Returns a dict mapping expected CSV-friendly keys, with 'filename' included.
    """
    if not isinstance(table_string, str):
        return {"filename": filename, "error": "No table string provided."}

    txt = table_string.strip()
    if not txt:
        return {"filename": filename, "error": "Empty string."}

    # Remove surrounding triple backticks if present
    txt = re.sub(r'^\s*```[a-zA-Z0-9]*\s*', '', txt)
    txt = re.sub(r'\s*```\s*$', '', txt)
    txt = strip_code_fences(txt)

    lines = [ln.rstrip() for ln in txt.splitlines() if ln.strip() != ""]
    start, end = find_first_markdown_table_block(lines)
    if start is None:
        # fallback: try to use first 3 non-empty lines if they look table-ish
        if len(lines) >= 3 and '|' in lines[0] and '|' in lines[2]:
            header_line = lines[0]
            data_line = lines[2]
        else:
            return {"filename": filename, "error": "No markdown table found."}
    else:
        header_line = lines[start]
        data_line = lines[start+2] if (start + 2) < end else ""

    headers = [h.strip() for h in header_line.split('|') if h.strip()]
    data_row = [d.strip() for d in data_line.split('|') if d.strip()]

    # Align lengths: pad or trim
    if len(headers) != len(data_row):
        if len(data_row) < len(headers):
            data_row += [""] * (len(headers) - len(data_row))
        else:
            data_row = data_row[:len(headers)]

    result = dict(zip(headers, data_row))
    result['filename'] = filename

    # Normalize header keys into expected CSV keys
    normalized = {}
    for k, v in result.items():
        norm_k = re.sub(r'[^A-Za-z0-9 ]', '', k).strip()
        normalized[norm_k] = v

    mapped = {
        'filename': filename,
        'Score': normalized.get('Score', normalized.get('score', '')),
        'Fit': normalized.get('Fit', normalized.get('fit', '')),
        'Rationale': normalized.get('Rationale', normalized.get('rationale', '')),
        'Matched Skills': normalized.get('Matched Skills', normalized.get('MatchedSkills', '')),
        'Missing Skills': normalized.get('Missing Skills', normalized.get('MissingSkills', '')),
        'Top Qualifications': normalized.get('Top Qualifications', normalized.get('TopQualifications', '')),
        'Quantifiable Achievements': normalized.get('Quantifiable Achievements', normalized.get('QuantifiableAchievements', '')),
    }

    return mapped

def to_csv_string(results):
    if not results:
        return ""
    fieldnames = ['filename', 'Score', 'Fit', 'Rationale', 'Matched Skills', 'Missing Skills', 'Top Qualifications', 'Quantifiable Achievements']
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue()

# --- App UI ---
st.set_page_config(page_title="IIM Sirmaur HR Tool", layout="wide", page_icon="🏛️")
# optional CSS omitted for brevity
st.markdown("<div class='iim-header'><h1>IIM Sirmaur</h1><p>AI-Powered HR Evaluation Tool</p></div>", unsafe_allow_html=True)

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
        critical_skills = st.text_input("Enter Critical Skills (comma-separated)", placeholder="e.g., Python, SQL, Project Management")
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

                    # LLM template — double braces so LLM placeholders remain literal after .format
                    final_eval_template_template = """
You are a strict HR evaluation engine. Your task is to evaluate a candidate based on a complete set of extracted data and provide a final, summarized evaluation in a Markdown table.
Apply heuristics to ensure the score is highly accurate and does not miss any critical connections.

**Evaluation Rubric:**
* **Scoring (1-10):**
    * All Matched Skills ({matched_skills_w}%)
    * Experience Summary Relevance ({experience_relevance_w}%)
    * All Qualifications & Achievements ({qualifications_w}%)
    * Overall Depth & Seniority ({seniority_w}%)
    * CV Clarity ({cv_clarity_w}%)

**Candidate Data:**
{{candidate_data_json}}

**Output Table:**
You must produce a single Markdown table with the following headers in this exact order: `Score`, `Fit`, `Rationale`, `Matched Skills`, `Missing Skills`, `Top Qualifications`, `Quantifiable Achievements`.

| Score | Fit | Rationale | Matched Skills | Missing Skills | Top Qualifications | Quantifiable Achievements |
|---|---|---|---|---|---|---|
| {{score}} | {{fit}} | {{rationale}} | {{matched_skills}} | {{missing_skills}} | {{top_qualifications}} | {{quantifiable_achievements}} |
"""
                    final_eval_template = final_eval_template_template.format(
                        matched_skills_w=matched_skills_w,
                        experience_relevance_w=experience_relevance_w,
                        qualifications_w=qualifications_w,
                        seniority_w=seniority_w,
                        cv_clarity_w=cv_clarity_w,
                    )

                    if critical_skills:
                        final_eval_template += f"""
**Critical Skill Heuristic:**
* A candidate missing any of the following skills must have their score severely penalized: **{critical_skills}**.
"""

                    # helper normalization functions (used per-CV)
                    def extract_numeric_score(text):
                        """Extract first numeric score 0-10 (integer or decimal) from text. Returns float or None."""
                        if not text or not isinstance(text, str):
                            return None
                        m = re.search(r'\b(?:10(?:\.0+)?|[0-9](?:\.\d+)?)\b', text)
                        if m:
                            try:
                                val = float(m.group(0))
                                if 0 <= val <= 10:
                                    return val
                            except:
                                return None
                        return None

                    def normalize_fit_from_text(text):
                        """Return 'High'|'Medium'|'Low' if the text contains hints, else None."""
                        if not text or not isinstance(text, str):
                            return None
                        t = text.lower()
                        if 'high' in t:
                            return 'High'
                        if 'medium' in t:
                            return 'Medium'
                        if 'low' in t:
                            return 'Low'
                        return None

                    for i, cv_file in enumerate(cv_files):
                        progress_text = f"Processing `{cv_file.name}`..."
                        progress_bar.progress((i) / len(cv_files), text=progress_text)

                        cv_text = read_uploaded_file(cv_file)
                        if not cv_text or not cv_text.strip():
                            continue

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

                        candidate_data_string = json.dumps(foundational_data, indent=2)
                        final_prompt_with_data = final_eval_template.replace("{candidate_data_json}", candidate_data_string)
                        final_table_output = call_gemini_api(final_prompt_with_data)

                        if isinstance(final_table_output, str) and "API/Network Error" in final_table_output:
                            st.error(f"Final Evaluation for {cv_file.name} failed: {final_table_output}")
                            continue

                        # --- PARSE TABLE FIRST (robustly), normalize Score/Fit, then create expander with real score/fit ---
                        parsed_data = {}
                        if isinstance(final_table_output, str):
                            parsed_data = parse_markdown_table(final_table_output, cv_file.name)

                        # If parsing failed, fallback to minimal structure
                        if not parsed_data or 'filename' not in parsed_data:
                            parsed_data = {
                                "filename": cv_file.name,
                                "Score": "",
                                "Fit": "",
                                "Rationale": "",
                                "Matched Skills": "",
                                "Missing Skills": "",
                                "Top Qualifications": "",
                                "Quantifiable Achievements": ""
                            }

                        # --- Normalization logic ---
                        score_num = extract_numeric_score(parsed_data.get('Score', '') or "")
                        if score_num is None:
                            score_num = extract_numeric_score(final_table_output)

                        fit_norm = normalize_fit_from_text(parsed_data.get('Fit', '') or "")
                        if not fit_norm and score_num is not None:
                            if score_num >= 8.0:
                                fit_norm = 'High'
                            elif score_num >= 5.0:
                                fit_norm = 'Medium'
                            else:
                                fit_norm = 'Low'

                        # Final string representations for display and CSV
                        score_display = None
                        if score_num is not None:
                            # display integer where appropriate, else 1 decimal
                            if float(score_num).is_integer():
                                score_display = str(int(score_num))
                            else:
                                score_display = str(round(score_num, 1))
                        else:
                            # try to keep whatever the LLM provided if present
                            score_display = parsed_data.get('Score', '') or ""

                        fit_display = fit_norm if fit_norm is not None else (parsed_data.get('Fit', '') or "")

                        parsed_data['Score'] = score_display
                        parsed_data['Fit'] = fit_display

                        score_header = parsed_data.get('Score') or "N/A"
                        fit_header = parsed_data.get('Fit') or "N/A"

                        # Single outer expander per CV, title uses parsed/normalized values
                        with st.expander(f"**{cv_file.name}** - Score: {score_header} | Fit: {fit_header}"):
                            # show raw LLM output
                            st.markdown(final_table_output, unsafe_allow_html=True)

                            # Strengths & Weaknesses Analysis (LLM)
                            analysis_prompt = STRENGTHS_WEAKNESSES_PROMPT.format(
                                candidate_data_json=candidate_data_string,
                                jd_text=jd_text
                            )
                            analysis_result = call_gemini_api(analysis_prompt)

                            # Show normalized parsed summary and analysis
                            st.markdown(f"**Parsed summary for:** {parsed_data.get('filename')}")
                            st.write(f"Score: {parsed_data.get('Score')}")
                            st.write(f"Fit: {parsed_data.get('Fit')}")
                            st.write("Matched Skills:", parsed_data.get("Matched Skills"))
                            st.write("Missing Skills:", parsed_data.get("Missing Skills"))
                            st.write("Top Qualifications:", parsed_data.get("Top Qualifications"))
                            st.write("Quantifiable Achievements:", parsed_data.get("Quantifiable Achievements"))

                            st.subheader("Strengths & Weaknesses Analysis")
                            if isinstance(analysis_result, str) and "API/Network Error" in analysis_result:
                                st.warning("Could not generate detailed analysis.")
                            else:
                                st.markdown(analysis_result)

                            st.markdown("### Raw Data Extracted")
                            st.json(foundational_data)

                        # append normalized data for CSV/report (guaranteed keys)
                        evaluated_results.append({
                            "filename": parsed_data.get("filename", cv_file.name),
                            "Score": parsed_data.get("Score", ""),
                            "Fit": parsed_data.get("Fit", ""),
                            "Rationale": parsed_data.get("Rationale", ""),
                            "Matched Skills": parsed_data.get("Matched Skills", ""),
                            "Missing Skills": parsed_data.get("Missing Skills", ""),
                            "Top Qualifications": parsed_data.get("Top Qualifications", ""),
                            "Quantifiable Achievements": parsed_data.get("Quantifiable Achievements", "")
                        })

                        progress_bar.progress((i + 1) / len(cv_files), text="All files processed!")

                st.markdown("---")
                st.subheader("Final Evaluation Report")

                if evaluated_results:
                    df_results = pd.DataFrame(evaluated_results)
                    df_results["Score"] = pd.to_numeric(df_results.get("Score", None), errors='coerce')

                    # Ensure filename is first column if present
                    if 'filename' in df_results.columns:
                        cols = ['filename'] + [c for c in df_results.columns if c != 'filename']
                        df_results = df_results[cols]

                    df_results = df_results.sort_values(by="Score", ascending=False, na_position='last')

                    high_count = len(df_results[df_results['Fit'] == 'High']) if 'Fit' in df_results.columns else 0
                    medium_count = len(df_results[df_results['Fit'] == 'Medium']) if 'Fit' in df_results.columns else 0
                    low_count = len(df_results[df_results['Fit'] == 'Low']) if 'Fit' in df_results.columns else 0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="High Fit", value=high_count)
                    with col2:
                        st.metric(label="Medium Fit", value=medium_count)
                    with col3:
                        st.metric(label="Low Fit", value=low_count)

                    st.dataframe(df_results, use_container_width=True)

                    csv_string = to_csv_string(evaluated_results)
                    st.download_button(
                        label="Download CSV Report",
                        data=csv_string,
                        file_name="hr_evaluation_report.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
