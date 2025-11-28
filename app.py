# app.py — IIM Sirmaur HR Tool (Gemini v1, balanced scoring)

import streamlit as st
import os
import json
import time
import requests
import csv
import io
import re
import traceback
import pandas as pd
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# ---------- Config ----------
# Prefer env var in production; for local quick-and-dirty, you can paste your key below.
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # <- replace with your key if not using env var

BASE_URL = "https://generativelanguage.googleapis.com"
API_VERSION = "v1"  # IMPORTANT: v1, not v1beta
MODEL_NAME = "gemini-1.5-flash"  # or "gemini-1.5-flash-latest"

API_URL = f"{BASE_URL}/{API_VERSION}/models/{MODEL_NAME}:generateContent?key={API_KEY}"
CV_EXTENSIONS = (".txt", ".pdf")

# ---------- Prompts ----------
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

# ---------- Helpers ----------
def safe_file_type(uploaded_file):
    """Return a safe mime type; fall back to extension when needed."""
    try:
        t = getattr(uploaded_file, "type", None)
        if t:
            return t
        name = getattr(uploaded_file, "name", "")
        ext = os.path.splitext(name)[1].lower()
        if ext == ".txt":
            return "text/plain"
        if ext == ".pdf":
            return "application/pdf"
        return None
    except Exception:
        return None


@st.cache_data
def read_uploaded_file(uploaded_file):
    """Reads TXT or PDF file; returns string or None on error."""
    try:
        ftype = safe_file_type(uploaded_file)
        if ftype == "text/plain":
            raw = uploaded_file.read()
            if isinstance(raw, bytes):
                return raw.decode("utf-8", errors="ignore")
            return str(raw)

        elif ftype == "application/pdf":
            reader = PdfReader(uploaded_file)
            if reader.is_encrypted:
                st.warning(f"PDF '{uploaded_file.name}' is encrypted. Skipping.")
                return None
            if not reader.pages:
                st.warning(f"PDF '{uploaded_file.name}' contains no readable pages.")
                return None
            text = ""
            for page in reader.pages:
                try:
                    pt = page.extract_text() or ""
                except Exception:
                    pt = ""
                text += pt + "\n"
            return text.strip()

        # fallback: try to read as text safely
        raw = uploaded_file.read()
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="ignore")
        return str(raw)

    except PdfReadError as e:
        st.error(f"PDF read error '{uploaded_file.name}': {e}")
        return None
    except Exception as e:
        st.error(f"Error reading file '{getattr(uploaded_file, 'name', '')}': {e}")
        return None


def call_gemini_api(prompt, response_mime_type=None, response_schema=None):
    """
    Call Gemini with retries.
    Returns parsed JSON (if requested) or text; returns string starting with 'API/Network Error:' on persistent failure.
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    if response_mime_type and response_schema:
        payload["generationConfig"] = {
            "responseMimeType": response_mime_type,
            "responseSchema": response_schema,
        }

    MAX_RETRIES = 4
    for i in range(MAX_RETRIES):
        try:
            resp = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30,
            )

            if not resp.ok:
                try:
                    err_body = resp.json()
                except Exception:
                    err_body = resp.text[:500]
                raise RuntimeError(f"Gemini API error {resp.status_code}: {err_body}")

            result = resp.json()
            candidates = result.get("candidates") or []
            if not candidates:
                raise ValueError(f"API response missing candidates: {result}")

            parts = candidates[0].get("content", {}).get("parts") or []
            if not parts or "text" not in parts[0]:
                raise ValueError(f"API response missing content parts: {result}")

            content_part = parts[0]["text"]

            if response_mime_type == "application/json":
                try:
                    return json.loads(content_part)
                except Exception:
                    return content_part

            return content_part

        except Exception as e:
            if i < MAX_RETRIES - 1:
                time.sleep(2 ** i)
                continue
            return f"API/Network Error: {e}"

    return "API call failed after max retries."


def strip_code_fences(text):
    return re.sub(
        r"```(?:[\s\S]*?)```",
        lambda m: m.group(0).strip("`"),
        text,
        flags=re.MULTILINE,
    )


def find_first_markdown_table_block(lines):
    for i in range(len(lines) - 2):
        header = lines[i].strip()
        sep = lines[i + 1].strip()
        if "|" not in header:
            continue
        if re.fullmatch(r"[|\s:-]+", sep):
            j = i + 2
            while j < len(lines) and "|" in lines[j]:
                j += 1
            return i, j
    return None, None


def parse_markdown_table(table_string, filename):
    if not isinstance(table_string, str):
        return {"filename": filename, "error": "No table string provided."}
    txt = table_string.strip()
    if not txt:
        return {"filename": filename, "error": "Empty string."}
    txt = re.sub(r"^\s*```[a-zA-Z0-9]*\s*", "", txt)
    txt = re.sub(r"\s*```\s*$", "", txt)
    txt = strip_code_fences(txt)
    lines = [ln.rstrip() for ln in txt.splitlines() if ln.strip() != ""]
    start, end = find_first_markdown_table_block(lines)

    if start is None:
        if len(lines) >= 3 and "|" in lines[0] and "|" in lines[2]:
            header_line = lines[0]
            data_line = lines[2]
        else:
            return {"filename": filename, "error": "No markdown table found."}
    else:
        header_line = lines[start]
        data_line = lines[start + 2] if (start + 2) < end else ""

    headers = [h.strip() for h in header_line.split("|") if h.strip()]
    data_row = [d.strip() for d in data_line.split("|") if d.strip()]

    if len(headers) != len(data_row):
        if len(data_row) < len(headers):
            data_row += [""] * (len(headers) - len(data_row))
        else:
            data_row = data_row[: len(headers)]

    result = dict(zip(headers, data_row))
    result["filename"] = filename

    normalized = {}
    for k, v in result.items():
        norm_k = re.sub(r"[^A-Za-z0-9 ]", "", k).strip()
        normalized[norm_k] = v

    mapped = {
        "filename": filename,
        "Score": normalized.get("Score", normalized.get("score", "")),
        "Fit": normalized.get("Fit", normalized.get("fit", "")),
        "Rationale": normalized.get("Rationale", normalized.get("rationale", "")),
        "Matched Skills": normalized.get(
            "Matched Skills", normalized.get("MatchedSkills", "")
        ),
        "Missing Skills": normalized.get(
            "Missing Skills", normalized.get("MissingSkills", "")
        ),
        "Top Qualifications": normalized.get(
            "Top Qualifications", normalized.get("TopQualifications", "")
        ),
        "Quantifiable Achievements": normalized.get(
            "Quantifiable Achievements",
            normalized.get("QuantifiableAchievements", ""),
        ),
    }
    return mapped


def to_csv_string(results):
    if not results:
        return ""
    fieldnames = [
        "filename",
        "Score",
        "Fit",
        "Rationale",
        "Matched Skills",
        "Missing Skills",
        "Top Qualifications",
        "Quantifiable Achievements",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue()


# ---------- Deterministic fallback scoring (balanced) ----------
def compute_fallback_score(foundational_data, cv_text, weights, critical_skills_list):
    matched = foundational_data.get("matched_skills_full", []) or []
    missing = foundational_data.get("missing_skills_full", []) or []
    top_quals = foundational_data.get("top_qualifications_full", []) or []
    quant_ach = foundational_data.get("quantifiable_achievements_full", []) or []
    exp_summary = (foundational_data.get("relevant_experience_summary") or "").lower()

    matched_count = len(matched)
    missing_count = len(missing)
    total_skill_candidates = matched_count + missing_count
    matched_ratio = (
        matched_count / total_skill_candidates if total_skill_candidates > 0 else 0.0
    )

    # Presence scores
    qual_score = min(1.0, len(top_quals) / 2.0)
    ach_score = min(1.0, len(quant_ach) / 2.0)
    exp_presence = 1.0 if exp_summary.strip() else 0.0

    seniority_keywords = ["senior", "lead", "manager", "principal", "head", "director"]
    seniority_score = 1.0 if any(k in exp_summary for k in seniority_keywords) else 0.0

    cv_len = len(cv_text or "")
    if cv_len > 2000:
        cv_clarity_score = 1.0
    elif cv_len > 800:
        cv_clarity_score = 0.8
    elif cv_len > 300:
        cv_clarity_score = 0.6
    else:
        cv_clarity_score = 0.3

    mw = weights.get("matched_skills_w", 50) / 100.0
    ew = weights.get("experience_relevance_w", 20) / 100.0
    qw = weights.get("qualifications_w", 15) / 100.0
    sw = weights.get("seniority_w", 10) / 100.0
    cw = weights.get("cv_clarity_w", 5) / 100.0

    comp_matched = matched_ratio
    comp_exp = exp_presence
    comp_qual = (qual_score + ach_score) / 2.0
    comp_sen = seniority_score
    comp_clar = cv_clarity_score

    weighted_percent = (
        comp_matched * mw
        + comp_exp * ew
        + comp_qual * qw
        + comp_sen * sw
        + comp_clar * cw
    )

    # Map 0–1 to 3–10 (never brutal 0–1 unless everything is terrible)
    score = 3.0 + weighted_percent * 7.0

    # Softer penalty for missing skills
    penalty_per_missing = 0.2
    max_penalty = 1.5
    miss_penalty = min(max_penalty, missing_count * penalty_per_missing)
    score -= miss_penalty

    # Critical skills: mild penalty, not hard cap
    critical_penalty = 0.0
    missing_criticals = []
    if critical_skills_list:
        crit_lower = [c.strip().lower() for c in critical_skills_list if c.strip()]
        for crit in crit_lower:
            if not any(crit in (s or "").lower() for s in matched):
                missing_criticals.append(crit)
        if missing_criticals:
            critical_penalty = 1.0
    score -= critical_penalty

    score = max(1.0, min(10.0, score))

    # Softer thresholds
    if score >= 7.5:
        fit = "High"
    elif score >= 5.0:
        fit = "Medium"
    else:
        fit = "Low"

    rationale_parts = []
    if total_skill_candidates > 0:
        rationale_parts.append(
            f"Matched {matched_count} / {total_skill_candidates} JD skills ({int(round(matched_ratio * 100))}%)."
        )
    else:
        rationale_parts.append("No explicit JD skill matches detected.")
    if top_quals:
        rationale_parts.append(f"{len(top_quals)} qualification(s) detected.")
    if quant_ach:
        rationale_parts.append(f"{len(quant_ach)} quantifiable achievement(s).")
    if missing_count:
        rationale_parts.append(f"Soft penalty applied for {missing_count} missing skill(s).")
    if missing_criticals:
        rationale_parts.append(
            f"Additional mild penalty for missing critical skill(s): {', '.join(missing_criticals)}."
        )

    rationale = " ".join(rationale_parts)
    return score, fit, rationale


# ---------- Main app ----------
def main():
    st.set_page_config(
        page_title="IIM Sirmaur HR Tool",
        layout="wide",
        page_icon="🏛️",
    )
    st.markdown(
        "<div class='iim-header'><h1>IIM Sirmaur</h1>"
        "<p>AI-Powered HR Evaluation Tool</p></div>",
        unsafe_allow_html=True,
    )

    main_container = st.container()
    with main_container:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Upload Job Description")
            jd_file = st.file_uploader(
                "Upload a PDF or TXT file for the Job Description",
                type=["pdf", "txt"],
                key="jd_uploader",
            )
        with col2:
            st.subheader("2. Upload Candidate CVs")
            cv_files = st.file_uploader(
                "Upload one or more PDF/TXT files for CVs",
                type=["pdf", "txt"],
                accept_multiple_files=True,
                key="cv_uploader",
            )

        st.markdown("---")
        st.subheader("3. Customize Evaluation Rubric")
        with st.form(key="weight_form"):
            st.markdown(
                "Adjust the importance of each factor to match your specific job requirements."
            )
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
            critical_skills = st.text_input(
                "Enter Critical Skills (comma-separated)",
                placeholder="e.g., Python, SQL, Project Management",
            )
            run_button = st.form_submit_button("🚀 Run Evaluation", use_container_width=True)

        if run_button:
            if not jd_file:
                st.error("Please upload a Job Description to begin.")
                return
            if not cv_files:
                st.warning("Please upload at least one CV file.")
                return

            jd_text = read_uploaded_file(jd_file)
            if not jd_text:
                st.error("Could not read the Job Description. Please check the file.")
                return

            evaluated_results = []
            progress_bar = st.progress(0, text="Starting evaluation...")

            final_eval_template = FINAL_EVALUATION_TEMPLATE.format(
                matched_skills_w=matched_skills_w,
                experience_relevance_w=experience_relevance_w,
                qualifications_w=qualifications_w,
                seniority_w=seniority_w,
                cv_clarity_w=cv_clarity_w,
            )
            if critical_skills:
                final_eval_template += f"\n**Critical Skill Heuristic:**\n* {critical_skills}\n"

            weights = {
                "matched_skills_w": matched_skills_w,
                "experience_relevance_w": experience_relevance_w,
                "qualifications_w": qualifications_w,
                "seniority_w": seniority_w,
                "cv_clarity_w": cv_clarity_w,
            }
            critical_skills_list = (
                [s.strip() for s in critical_skills.split(",")] if critical_skills else []
            )

            for i, cv_file in enumerate(cv_files):
                try:
                    progress_bar.progress(i / len(cv_files), text=f"Processing {cv_file.name}...")
                    cv_text = read_uploaded_file(cv_file)
                    if not cv_text:
                        st.warning(f"Skipping {cv_file.name}: could not read content.")
                        continue

                    # Phase 1: foundational extraction
                    schema = {
                        "type": "OBJECT",
                        "properties": {
                            "matched_skills_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "missing_skills_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "top_qualifications_full": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "quantifiable_achievements_full": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "relevant_experience_summary": {"type": "STRING"},
                        },
                    }

                    full_prompt_p1 = FOUNDATIONAL_ANALYSIS_PROMPT.format(
                        jd_text=jd_text, cv_text=cv_text
                    )
                    foundational_data = call_gemini_api(
                        full_prompt_p1,
                        response_mime_type="application/json",
                        response_schema=schema,
                    )

                    if isinstance(foundational_data, str) and foundational_data.startswith(
                        "API/Network Error"
                    ):
                        st.info(
                            f"Foundational extraction failed for {cv_file.name}; "
                            f"using deterministic fallback scoring.\n\n{foundational_data}"
                        )
                        foundational_data = {
                            "matched_skills_full": [],
                            "missing_skills_full": [],
                            "top_qualifications_full": [],
                            "quantifiable_achievements_full": [],
                            "relevant_experience_summary": "",
                        }

                    candidate_data_string = json.dumps(foundational_data, indent=2)

                    # Phase 2: ask LLM to produce final table
                    final_prompt_with_data = final_eval_template.replace(
                        "{candidate_data_json}", candidate_data_string
                    )
                    final_table_output = call_gemini_api(final_prompt_with_data)

                    parsed_data = {}
                    parsed_from_llm = False
                    if (
                        isinstance(final_table_output, str)
                        and final_table_output
                        and not final_table_output.startswith("API/Network Error")
                    ):
                        parsed_try = parse_markdown_table(final_table_output, cv_file.name)
                        if parsed_try and "error" not in parsed_try and (
                            parsed_try.get("Score") or parsed_try.get("Fit")
                        ):
                            parsed_data = parsed_try
                            parsed_from_llm = True

                    # Fallback deterministic scoring if LLM table is not usable
                    if not parsed_from_llm:
                        fb_score, fb_fit, fb_rationale = compute_fallback_score(
                            foundational_data, cv_text, weights, critical_skills_list
                        )
                        if float(fb_score).is_integer():
                            score_str = str(int(fb_score))
                        else:
                            score_str = str(round(fb_score, 1))

                        parsed_data = {
                            "filename": cv_file.name,
                            "Score": score_str,
                            "Fit": fb_fit,
                            "Rationale": fb_rationale,
                            "Matched Skills": ", ".join(
                                foundational_data.get("matched_skills_full", []) or []
                            ),
                            "Missing Skills": ", ".join(
                                foundational_data.get("missing_skills_full", []) or []
                            ),
                            "Top Qualifications": ", ".join(
                                foundational_data.get("top_qualifications_full", []) or []
                            ),
                            "Quantifiable Achievements": "; ".join(
                                foundational_data.get("quantifiable_achievements_full", [])
                                or []
                            ),
                        }

                        final_table_output = (
                            "| Score | Fit | Rationale | Matched Skills | Missing Skills | Top Qualifications | Quantifiable Achievements |\n"
                            "|---|---|---|---|---|---|---|\n"
                            f"| {parsed_data['Score']} | {parsed_data['Fit']} | {parsed_data['Rationale'][:80]}... | "
                            f"{parsed_data['Matched Skills'][:40]} | {parsed_data['Missing Skills'][:40]} | "
                            f"{parsed_data['Top Qualifications'][:40]} | {parsed_data['Quantifiable Achievements'][:40]} |"
                        )

                    score_header = parsed_data.get("Score") or "N/A"
                    fit_header = parsed_data.get("Fit") or "N/A"

                    with st.expander(
                        f"**{cv_file.name}** - Score: {score_header} | Fit: {fit_header}"
                    ):
                        st.markdown(final_table_output, unsafe_allow_html=True)

                        analysis_prompt = STRENGTHS_WEAKNESSES_PROMPT.format(
                            candidate_data_json=candidate_data_string, jd_text=jd_text
                        )
                        analysis_result = call_gemini_api(analysis_prompt)

                        st.markdown(f"**Parsed summary for:** {parsed_data.get('filename')}")
                        st.write(f"Score: {parsed_data.get('Score')}")
                        st.write(f"Fit: {parsed_data.get('Fit')}")
                        st.write("Matched Skills:", parsed_data.get("Matched Skills"))
                        st.write("Missing Skills:", parsed_data.get("Missing Skills"))
                        st.write("Top Qualifications:", parsed_data.get("Top Qualifications"))
                        st.write(
                            "Quantifiable Achievements:",
                            parsed_data.get("Quantifiable Achievements"),
                        )

                        st.subheader("Strengths & Weaknesses Analysis")
                        if isinstance(analysis_result, str) and analysis_result.startswith(
                            "API/Network Error"
                        ):
                            st.warning("Could not generate detailed analysis.")
                        else:
                            st.markdown(analysis_result)

                        st.markdown("### Raw Data Extracted")
                        st.json(foundational_data)

                    evaluated_results.append(
                        {
                            "filename": parsed_data.get("filename", cv_file.name),
                            "Score": parsed_data.get("Score", ""),
                            "Fit": parsed_data.get("Fit", ""),
                            "Rationale": parsed_data.get("Rationale", ""),
                            "Matched Skills": parsed_data.get("Matched Skills", ""),
                            "Missing Skills": parsed_data.get("Missing Skills", ""),
                            "Top Qualifications": parsed_data.get("Top Qualifications", ""),
                            "Quantifiable Achievements": parsed_data.get(
                                "Quantifiable Achievements", ""
                            ),
                        }
                    )

                except Exception as e:
                    st.error(f"Error processing {getattr(cv_file, 'name', 'file')}: {e}")
                    st.text(traceback.format_exc())
                    continue

                progress_bar.progress((i + 1) / len(cv_files), text="All files processed!")

            # Final report
            st.markdown("---")
            st.subheader("Final Evaluation Report")
            if evaluated_results:
                df_results = pd.DataFrame(evaluated_results)
                df_results["Score"] = pd.to_numeric(
                    df_results.get("Score", None), errors="coerce"
                )
                if "filename" in df_results.columns:
                    cols = ["filename"] + [c for c in df_results.columns if c != "filename"]
                    df_results = df_results[cols]
                df_results = df_results.sort_values(
                    by="Score", ascending=False, na_position="last"
                )

                high_count = (
                    len(df_results[df_results["Fit"] == "High"])
                    if "Fit" in df_results.columns
                    else 0
                )
                medium_count = (
                    len(df_results[df_results["Fit"] == "Medium"])
                    if "Fit" in df_results.columns
                    else 0
                )
                low_count = (
                    len(df_results[df_results["Fit"] == "Low"])
                    if "Fit" in df_results.columns
                    else 0
                )

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("High Fit", high_count)
                with c2:
                    st.metric("Medium Fit", medium_count)
                with c3:
                    st.metric("Low Fit", low_count)

                st.dataframe(df_results, use_container_width=True)
                st.download_button(
                    "Download CSV Report",
                    data=to_csv_string(evaluated_results),
                    file_name="hr_evaluation_report.csv",
                    mime="text/csv",
                )
            else:
                st.info("No results to display (no CVs processed).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Fatal error running app. See traceback below.")
        st.text(traceback.format_exc())
