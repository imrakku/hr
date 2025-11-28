import re
from typing import Dict, List, Tuple

def compute_fallback_score(foundational_data: Dict, cv_text: str, weights: Dict, critical_skills_list: List[str]) -> Tuple[float, str, str]:
    matched = foundational_data.get("matched_skills_full", []) or []
    missing = foundational_data.get("missing_skills_full", []) or []
    top_quals = foundational_data.get("top_qualifications_full", []) or []
    quant_ach = foundational_data.get("quantifiable_achievements_full", []) or []
    exp_summary = (foundational_data.get("relevant_experience_summary") or "").lower()
    years_exp = foundational_data.get("years_of_experience", 0) or 0
    education = foundational_data.get("education_level", "").lower()

    matched_count = len(matched)
    missing_count = len(missing)
    total_skill_candidates = matched_count + missing_count
    matched_ratio = (matched_count / total_skill_candidates) if total_skill_candidates > 0 else 0.0

    qual_score = min(1.0, len(top_quals) / 2.0)
    ach_score = min(1.0, len(quant_ach) / 2.0)
    exp_presence = 1.0 if exp_summary.strip() else 0.0

    seniority_keywords = ["senior", "lead", "manager", "principal", "head", "director", "vp", "vice president", "cto", "ceo"]
    seniority_score = 1.0 if any(k in exp_summary for k in seniority_keywords) else 0.0

    years_score = min(1.0, years_exp / 10.0)

    edu_score = 0.5
    if "phd" in education or "doctorate" in education:
        edu_score = 1.0
    elif "master" in education or "mba" in education:
        edu_score = 0.85
    elif "bachelor" in education:
        edu_score = 0.7

    cv_len = len(cv_text or "")
    if cv_len > 2000:
        cv_clarity_score = 1.0
    elif cv_len > 800:
        cv_clarity_score = 0.7
    elif cv_len > 300:
        cv_clarity_score = 0.4
    else:
        cv_clarity_score = 0.15

    mw = weights.get("matched_skills_w", 50) / 100.0
    ew = weights.get("experience_relevance_w", 20) / 100.0
    qw = weights.get("qualifications_w", 15) / 100.0
    sw = weights.get("seniority_w", 10) / 100.0
    cw = weights.get("cv_clarity_w", 5) / 100.0

    comp_matched = matched_ratio
    comp_exp = (exp_presence * 0.4) + (years_score * 0.6)
    comp_qual = (qual_score * 0.5) + (ach_score * 0.3) + (edu_score * 0.2)
    comp_sen = seniority_score
    comp_clar = cv_clarity_score

    weighted_percent = (comp_matched * mw) + (comp_exp * ew) + (comp_qual * qw) + (comp_sen * sw) + (comp_clar * cw)
    score = 1.0 + weighted_percent * 9.0

    penalty_per_missing = 0.4
    max_penalty = 2.5
    miss_penalty = min(max_penalty, missing_count * penalty_per_missing)
    score -= miss_penalty

    if critical_skills_list:
        missing_criticals = []
        crit_lower = [c.strip().lower() for c in critical_skills_list if c.strip()]
        for crit in crit_lower:
            if not any(crit in (s.lower()) for s in matched):
                missing_criticals.append(crit)
        if missing_criticals:
            score = min(score, 4.5)

    score = max(0.0, min(10.0, score))

    if score >= 8.0:
        fit = "High"
    elif score >= 5.5:
        fit = "Medium"
    else:
        fit = "Low"

    rationale_parts = []
    rationale_parts.append(f"Matched {matched_count}/{total_skill_candidates} JD skills ({int(round(matched_ratio*100))}%).")
    if years_exp > 0:
        rationale_parts.append(f"{years_exp} years experience.")
    if education != "unknown":
        rationale_parts.append(f"Education: {education}.")
    if top_quals:
        rationale_parts.append(f"{len(top_quals)} qualifications.")
    if quant_ach:
        rationale_parts.append(f"{len(quant_ach)} quantifiable achievements.")
    if missing_count:
        rationale_parts.append(f"Penalty for {missing_count} missing skills.")
    if critical_skills_list and missing_criticals:
        rationale_parts.append(f"Critical skills missing: {', '.join(missing_criticals)} - score capped.")

    rationale = " ".join(rationale_parts)

    return score, fit, rationale


def parse_markdown_table(table_string: str, filename: str) -> Dict:
    if not isinstance(table_string, str):
        return {"filename": filename, "error": "No table string provided."}

    txt = table_string.strip()
    if not txt:
        return {"filename": filename, "error": "Empty string."}

    txt = re.sub(r'^\s*```[a-zA-Z0-9]*\s*', '', txt)
    txt = re.sub(r'\s*```\s*$', '', txt)

    lines = [ln.rstrip() for ln in txt.splitlines() if ln.strip()]

    header_idx = None
    for i, line in enumerate(lines):
        if '|' in line and 'Score' in line:
            header_idx = i
            break

    if header_idx is None or header_idx + 2 >= len(lines):
        return {"filename": filename, "error": "No valid markdown table found."}

    header_line = lines[header_idx]
    data_line = lines[header_idx + 2] if (header_idx + 2) < len(lines) else ""

    headers = [h.strip() for h in header_line.split('|') if h.strip()]
    data_row = [d.strip() for d in data_line.split('|') if d.strip()]

    if len(headers) != len(data_row):
        if len(data_row) < len(headers):
            data_row += [""] * (len(headers) - len(data_row))
        else:
            data_row = data_row[:len(headers)]

    result = dict(zip(headers, data_row))
    result['filename'] = filename

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
