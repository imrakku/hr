HR Candidate Evaluation Tool
A Professional AI-Powered Candidate Screening Solution for IIM Sirmaur
This project is a sophisticated, AI-driven tool designed to streamline the candidate screening process for placements. It uses a two-phase, heuristic-based evaluation system to analyze resumes and identify the best-fit candidates for a given job description.

Key Features 🚀
Two-Phase Evaluation: The tool uses a highly accurate, two-step process:

Phase 1 (Data Extraction): The AI meticulously extracts all relevant information from a candidate's CV without any scoring or judgment.

Phase 2 (Heuristic-Based Scoring): The AI then applies a set of predefined, strategic heuristics to the extracted data to calculate a fair and accurate score. This process prioritizes full-time experience, penalizes missing critical skills, and provides a nuanced final rating.

Intuitive User Interface (UI): The application features a professional, IIM Sirmaur-themed front end built with Streamlit, providing a clean and easy-to-use experience.

Comprehensive Reporting: It generates a detailed report for each candidate, including a score, rationale, and an analysis of their strengths and weaknesses.

Automated CSV Generation: After evaluating all candidates, the tool creates a downloadable CSV report for easy data management and further analysis.

Robust File Handling: The tool is designed to handle common file types (.pdf, .txt) and includes error handling for corrupted, empty, or encrypted files.

Getting Started
Prerequisites
Python 3.8 or higher

An active Google AI Studio API Key.

Installation
Clone the Repository:

Bash

git clone https://github.com/imrakku/hr.git
cd hr
Set Up Your API Key:
Replace the placeholder API_KEY in the app.py file with your actual API key.

Install Dependencies:
Run the following command in your terminal to install the necessary libraries:

Bash

pip install -r requirements.txt
How to Use 📖
Run the Application:
Launch the Streamlit application from your terminal:

Bash

streamlit run app.py
Upload Files:
The application will open in your web browser.

Upload the Job Description file in the designated section.

Upload one or more Candidate CVs in the second section.

Run Evaluation:
Click the "Run Evaluation" button. The tool will process each CV, providing real-time feedback and displaying the results on the page.

View and Download Report:
After all evaluations are complete, a final report table will be displayed, which you can sort. You can also click the "Download CSV Report" button to save the full report.
