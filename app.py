# app.py (full) - deterministic fallback + missing-skill penalty

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

FINAL_EVALUATION_TEMPLATE = """
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
You must produce a single Markdown table with headers: `Score`, `Fit`, `Rationale`, `Matched Skills`, `Missing Skills`, `Top Qualifications`, `Quantifiable Achievements`.

| Score | Fit | Rationale | Matched Skills | Missing Skills | Top Qualifications | Quantifiable Achievements |
|---|---|---|---|---|---|---|
| {{score}} | {{fit}} | {{rationale}} | {{matched_skills}} | {{missing_skills}} | {{top_qualifications}} | {{quantifiable_achievements}} |
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

# --- Deterministic fallback scoring (used when LLM table missing or malformed) ---
def compute_fallback_score(foundational_data, cv_text, weights, critical_skills_list):
    """
    Compute a deterministic score (0-10) and rationale from foundational_data when LLM output is missing.
    - weights: dict with percentage weights: matched_skills_w, experience_relevance_w, qualifications_w, seniority_w, cv_clarity_w
    - critical_skills_list: list of critical skills strings (case-insensitive)
    Returns: (score_float, fit_string, rationale_string)
    """
    # Extract fields
    matched = foundational_data.get("matched_skills_full", []) or []
    missing = foundational_data.get("missing_skills_full", []) or []
    top_quals = foundational_data.get("top_qualifications_full", []) or []
    quant_ach = foundational_data.get("quantifiable_achievements_full", []) or []
    exp_summary = (foundational_data.get("relevant_experience_summary") or "").lower()

    matched_count = len(matched)
    missing_count = len(missing)
    total_skill_candidates = matched_count + missing_count
    matched_ratio = (matched_count / total_skill_candidates) if total_skill_candidates > 0 else 0.0

    # proxies for other components
    qual_score = min(1.0, len(top_quals) / 2.0)   # 0..1, 2+ quals => full
    ach_score = min(1.0, len(quant_ach) / 2.0)    # 0..1
    exp_presence = 1.0 if exp_summary.strip() else 0.0

    # simple seniority proxy: check for senior keywords
    seniority_keywords = ["senior", "lead", "manager", "principal", "head", "director"]
    seniority_score = 1.0 if any(k in exp_summary for k in seniority_keywords) else 0.0

    # CV clarity proxy: length of CV text
    cv_len = len(cv_text or "")
    if cv_len > 2000:
        cv_clarity_score = 1.0
    elif cv_len > 800:
        cv_clarity_score = 0.7
    elif cv_len > 300:
        cv_clarity_score = 0.4
    else:
        cv_clarity_score = 0.15

    # Weights provided as percentages; convert to 0..1 fraction
    mw = weights.get("matched_skills_w", 50) / 100.0
    ew = weights.get("experience_relevance_w", 20) / 100.0
    qw = weights.get("qualifications_w", 15) / 100.0
    sw = weights.get("seniority_w", 10) / 100.0
    cw = weights.get("cv_clarity_w", 5) / 100.0

    # Component contributions (0..1 each)
    comp_matched = matched_ratio
    comp_exp = exp_presence
    comp_qual = qual_score
    comp_sen = seniority_score
    comp_clar = cv_clarity_score

    # Weighted percent (0..1)
    weighted_percent = (comp_matched * mw) + (comp_exp * ew) + (comp_qual * qw) + (comp_sen * sw) + (comp_clar * cw)

    # Convert to 1..10 scale
    score = 1.0 + weighted_percent * 9.0  # maps 0->1, 1->10

    # Missing-skills penalty: subtract 0.5 points per missing skill, up to 3.0 points
    penalty_per_missing = 0.5
    max_pen_
