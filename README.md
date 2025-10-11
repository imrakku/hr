🧠 HR Candidate Evaluation Tool
AI-Powered Candidate Screening Solution for IIM Sirmaur
🌟 Overview

The HR Candidate Evaluation Tool is a professional, AI-driven application built to streamline the candidate screening process for placements at IIM Sirmaur.

It uses a two-phase, heuristic-based evaluation system to extract, analyze, and score candidate resumes with precision — helping recruiters identify the best-fit candidates for a given job description.

🚀 Key Features
⚙️ Two-Phase Evaluation System

Phase 1 – Data Extraction:
The AI intelligently parses each candidate’s resume, extracting all relevant details — education, experience, skills, achievements — with zero bias or scoring.

Phase 2 – Heuristic-Based Scoring:
Using a predefined set of strategic heuristics, the tool:

Prioritizes full-time experience

Penalizes missing critical skills

Balances academic and professional attributes

Generates a comprehensive final score with reasoning

🧭 Intuitive User Interface (UI)

Built using Streamlit with a clean, IIM Sirmaur-themed interface

Simple drag-and-drop upload for resumes and job descriptions

Real-time progress feedback and visualized scoring output

📊 Comprehensive Reporting

Each candidate’s evaluation includes:

Score and ranking

Detailed rationale

Strengths and weaknesses analysis

All results are presented in a sortable table and can be exported to CSV for further use.

💾 Automated CSV Generation

After processing all resumes, the tool automatically generates a downloadable CSV report summarizing each candidate’s performance metrics.

🧱 Robust File Handling

Supports .pdf and .txt formats

Gracefully handles corrupted, empty, or encrypted files

Provides clear user feedback for problematic uploads

🛠️ Getting Started
✅ Prerequisites

Python 3.8+

Google AI Studio API Key

⚡ Installation

Clone the Repository

git clone https://github.com/imrakku/hr.git
cd hr


Set Up Your API Key
Replace the placeholder API_KEY in app.py with your actual Google AI Studio API key.

Install Dependencies

pip install -r requirements.txt

🧩 How to Use

Run the Application

streamlit run app.py


Upload Files

Upload your Job Description (JD)

Upload one or more Candidate CVs

Run Evaluation

Click "Run Evaluation"

Watch as the tool processes each resume and displays results live

View & Download Reports

Review scores, reasoning, and candidate rankings

Click "Download CSV Report" to save the full evaluation

📁 Example Output
Candidate Name	Score	Key Strengths	Improvement Areas	Final Verdict
John Doe	87	Strong domain fit, good experience	Missing advanced Python	Recommended
Jane Smith	78	Great analytical skills	Lacks leadership roles	Consider
🧩 Tech Stack

Frontend: Streamlit

Backend: Python

AI Model: Google AI Studio API

Data Handling: Pandas

Reporting: CSV export

🧑‍💼 Developed For

Indian Institute of Management (IIM) Sirmaur
Placement & Career Development Cell
