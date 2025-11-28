import csv
import io
from typing import List, Dict

def to_csv_string(results: List[Dict]) -> str:
    if not results:
        return ""
    fieldnames = ['filename', 'Score', 'Fit', 'Rationale', 'Matched Skills', 'Missing Skills', 'Top Qualifications', 'Quantifiable Achievements']
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue()

def format_score_color(score):
    try:
        score_val = float(score)
        if score_val >= 8.0:
            return "score-high"
        elif score_val >= 5.5:
            return "score-medium"
        else:
            return "score-low"
    except:
        return "score-medium"

def truncate_text(text, max_length=100):
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
