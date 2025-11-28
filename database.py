from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    def save_evaluation(self, job_title, candidate_name, evaluation_data):
        try:
            data = {
                "job_title": job_title,
                "candidate_name": candidate_name,
                "score": float(evaluation_data.get("Score", 0)),
                "fit_level": evaluation_data.get("Fit", ""),
                "rationale": evaluation_data.get("Rationale", ""),
                "matched_skills": evaluation_data.get("Matched Skills", ""),
                "missing_skills": evaluation_data.get("Missing Skills", ""),
                "qualifications": evaluation_data.get("Top Qualifications", ""),
                "achievements": evaluation_data.get("Quantifiable Achievements", ""),
                "evaluated_at": datetime.utcnow().isoformat()
            }

            result = self.client.table("candidate_evaluations").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Database save error: {e}")
            return None

    def get_evaluations_by_job(self, job_title):
        try:
            result = self.client.table("candidate_evaluations").select("*").eq("job_title", job_title).order("score", desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Database fetch error: {e}")
            return []

    def get_all_evaluations(self, limit=100):
        try:
            result = self.client.table("candidate_evaluations").select("*").order("evaluated_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"Database fetch error: {e}")
            return []

    def get_top_candidates(self, job_title=None, limit=10):
        try:
            query = self.client.table("candidate_evaluations").select("*")
            if job_title:
                query = query.eq("job_title", job_title)
            result = query.order("score", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"Database fetch error: {e}")
            return []
