import json
import time
from google import genai
from config import GEMINI_API_KEY, MODEL_NAME, MAX_RETRIES, INITIAL_BACKOFF

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def call_gemini_api(self, prompt, response_mime_type=None, response_schema=None):
        contents = [{"parts": [{"text": prompt}]}]

        config = None
        if response_mime_type and response_schema:
            config = {
                "response_mime_type": response_mime_type,
                "response_schema": response_schema
            }

        backoff = INITIAL_BACKOFF
        for attempt in range(MAX_RETRIES):
            try:
                if config:
                    resp = self.client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=config
                    )
                else:
                    resp = self.client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents
                    )

                content_part = getattr(resp, "text", None)
                if not content_part:
                    content_part = str(resp)

                if response_mime_type == "application/json":
                    try:
                        return json.loads(content_part)
                    except Exception:
                        return content_part

                return content_part

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return f"API/Network Error: {e}"

        return "API call failed after max retries."

    def extract_candidate_data(self, jd_text, cv_text):
        prompt = f"""
You are a meticulous data extraction assistant. Your task is to analyze a candidate's CV against a job description (JD) and extract every single piece of relevant information. Do not perform any scoring or filtering. Your output must be a single, complete JSON object.

**JSON Schema:**
{{
  "matched_skills_full": [STRING],
  "missing_skills_full": [STRING],
  "top_qualifications_full": [STRING],
  "quantifiable_achievements_full": [STRING],
  "relevant_experience_summary": STRING,
  "years_of_experience": NUMBER,
  "education_level": STRING
}}

**Instructions:**
1. `matched_skills_full`: List all skills from the JD present in the CV.
2. `missing_skills_full`: List all skills from the JD not present in the CV.
3. `top_qualifications_full`: List all relevant degrees, certifications, and licenses.
4. `quantifiable_achievements_full`: Find and list all achievements with numbers, percentages, currency, or metrics.
5. `relevant_experience_summary`: Provide a 1-2 paragraph summary of the candidate's work history as it relates directly to the JD's requirements.
6. `years_of_experience`: Total years of professional experience (number).
7. `education_level`: Highest degree earned (e.g., Bachelor's, Master's, PhD).

**JD:**
{jd_text}

**CV:**
{cv_text}
"""

        schema = {
            "type": "OBJECT",
            "properties": {
                "matched_skills_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                "missing_skills_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                "top_qualifications_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                "quantifiable_achievements_full": {"type": "ARRAY", "items": {"type": "STRING"}},
                "relevant_experience_summary": {"type": "STRING"},
                "years_of_experience": {"type": "NUMBER"},
                "education_level": {"type": "STRING"}
            }
        }

        result = self.call_gemini_api(prompt, "application/json", schema)
        if isinstance(result, str):
            return {
                "matched_skills_full": [],
                "missing_skills_full": [],
                "top_qualifications_full": [],
                "quantifiable_achievements_full": [],
                "relevant_experience_summary": "",
                "years_of_experience": 0,
                "education_level": "Unknown"
            }
        return result

    def evaluate_candidate(self, candidate_data, weights):
        prompt = f"""
You are a strict HR evaluation engine. Your task is to evaluate a candidate based on a complete set of extracted data and provide a final, summarized evaluation in a Markdown table.

**Evaluation Rubric (Scoring 1-10):**
* Matched Skills ({weights['matched_skills_w']}%)
* Experience Relevance ({weights['experience_relevance_w']}%)
* Qualifications & Achievements ({weights['qualifications_w']}%)
* Depth & Seniority ({weights['seniority_w']}%)
* CV Clarity ({weights['cv_clarity_w']}%)

**Candidate Data:**
{json.dumps(candidate_data, indent=2)}

**Output Table:**
You must produce a single Markdown table with headers: `Score`, `Fit`, `Rationale`, `Matched Skills`, `Missing Skills`, `Top Qualifications`, `Quantifiable Achievements`.

| Score | Fit | Rationale | Matched Skills | Missing Skills | Top Qualifications | Quantifiable Achievements |
|---|---|---|---|---|---|---|
"""

        return self.call_gemini_api(prompt)

    def analyze_strengths_weaknesses(self, candidate_data, jd_text):
        prompt = f"""
You are an expert HR analyst. Based on the following candidate data and JD, provide a concise, professional analysis of the candidate's strengths and weaknesses.

**Instructions:**
* **Strengths:** Write a single paragraph (2-3 sentences) summarizing the candidate's top strengths.
* **Weaknesses:** Write a single paragraph (2-3 sentences) summarizing their key weaknesses.

**Candidate Data:**
{json.dumps(candidate_data, indent=2)}

**JD:**
{jd_text}
"""

        return self.call_gemini_api(prompt)
