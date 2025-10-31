"""
Google Sheets Q&A Agent
Fetches data from Google Sheets and answers questions using AI
"""

import gspread
import pandas as pd
import json
import requests
import sys
import time
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from pathlib import Path
from sheets_config import SheetsConfig, get_config_from_env

# Gemini API Configuration
API_KEY = "AIzaSyCLbK8gHVZ5OtIkbAefprWTBYSILVIHMng"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"


class GoogleSheetsAgent:
    """Agent for fetching and querying Google Sheets data"""
    
    def __init__(self, config=None):
        """
        Initialize the Google Sheets Agent
        
        Args:
            config: SheetsConfig instance (optional, will use env config if not provided)
        """
        self.config = config or get_config_from_env()
        self.client = None
        self.current_sheet_data = None
        self.current_sheet_name = None
        self.data_cache = {}
        
    def authenticate(self):
        """
        Authenticate with Google Sheets API
        Supports both service account and OAuth authentication
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Check if credentials file exists
            if not self.config.credentials_exist():
                print(f"❌ Credentials file not found: {self.config.credentials_file}")
                print("\nPlease follow these steps:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing one")
                print("3. Enable Google Sheets API")
                print("4. Create credentials (Service Account or OAuth 2.0)")
                print("5. Download the JSON file and save as 'credentials.json'")
                return False
            
            # Validate credentials format
            is_valid, message = self.config.validate_credentials()
            if not is_valid:
                print(f"❌ {message}")
                return False
            
            print(f"✓ {message}")
            
            # Try service account authentication first
            try:
                creds = Credentials.from_service_account_file(
                    self.config.get_credentials_path(),
                    scopes=self.config.scopes
                )
                self.client = gspread.authorize(creds)
                print("✓ Authenticated using service account")
                return True
            except Exception as sa_error:
                print(f"Service account auth failed: {sa_error}")
                
            # Fall back to OAuth authentication
            try:
                creds = None
                token_path = self.config.get_token_path()
                
                # Load existing token if available
                if Path(token_path).exists():
                    with open(token_path, 'rb') as token:
                        creds = pickle.load(token)
                
                # Refresh or create new credentials
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.config.get_credentials_path(),
                            self.config.scopes
                        )
                        creds = flow.run_local_server(port=0)
                    
                    # Save credentials for future use
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                
                self.client = gspread.authorize(creds)
                print("✓ Authenticated using OAuth")
                return True
                
            except Exception as oauth_error:
                print(f"❌ OAuth authentication failed: {oauth_error}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def extract_sheet_id(self, sheet_input):
        """
        Extract sheet ID from URL or return as-is if already an ID
        
        Args:
            sheet_input: Google Sheets URL or ID
            
        Returns:
            str: Sheet ID
        """
        if "docs.google.com/spreadsheets" in sheet_input:
            # Extract ID from URL
            parts = sheet_input.split("/")
            for i, part in enumerate(parts):
                if part == "d" and i + 1 < len(parts):
                    return parts[i + 1]
        return sheet_input
    
    def fetch_sheet_data(self, sheet_id_or_url, worksheet_name=None, use_cache=True):
        """
        Fetch data from Google Sheet
        
        Args:
            sheet_id_or_url: Google Sheets ID or URL
            worksheet_name: Name of specific worksheet (optional, uses first sheet if not provided)
            use_cache: Whether to use cached data if available
            
        Returns:
            pandas.DataFrame: Sheet data as DataFrame, or None on error
        """
        try:
            sheet_id = self.extract_sheet_id(sheet_id_or_url)
            cache_key = f"{sheet_id}_{worksheet_name or 'default'}"
            
            # Check cache
            if use_cache and cache_key in self.data_cache:
                print(f"✓ Using cached data for sheet: {cache_key}")
                self.current_sheet_data = self.data_cache[cache_key]
                self.current_sheet_name = cache_key
                return self.current_sheet_data
            
            # Ensure authenticated
            if not self.client:
                if not self.authenticate():
                    return None
            
            print(f"📥 Fetching data from Google Sheets...")
            
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Get worksheet
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            # Get all values
            data = worksheet.get_all_values()
            
            if not data:
                print("⚠️  Sheet is empty")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Cache the data
            self.data_cache[cache_key] = df
            self.current_sheet_data = df
            self.current_sheet_name = cache_key
            
            print(f"✓ Fetched {len(df)} rows and {len(df.columns)} columns")
            print(f"✓ Columns: {', '.join(df.columns.tolist())}")
            
            return df
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Spreadsheet not found. Make sure:")
            print("   1. The sheet ID/URL is correct")
            print("   2. The sheet is shared with your service account email")
            print("   3. Or the sheet is accessible with your OAuth account")
            return None
        except gspread.exceptions.WorksheetNotFound:
            print(f"❌ Worksheet '{worksheet_name}' not found")
            return None
        except Exception as e:
            print(f"❌ Error fetching sheet data: {e}")
            return None
    
    def get_data_summary(self, df=None):
        """
        Get a summary of the current sheet data
        
        Args:
            df: DataFrame to summarize (uses current_sheet_data if not provided)
            
        Returns:
            str: Formatted summary of the data
        """
        if df is None:
            df = self.current_sheet_data
        
        if df is None:
            return "No data loaded"
        
        summary = []
        summary.append(f"Dataset: {self.current_sheet_name or 'Unknown'}")
        summary.append(f"Rows: {len(df)}")
        summary.append(f"Columns: {len(df.columns)}")
        summary.append(f"\nColumn Names: {', '.join(df.columns.tolist())}")
        
        # Sample data
        summary.append(f"\nFirst 3 rows:")
        summary.append(df.head(3).to_string())
        
        # Data types
        summary.append(f"\nData types:")
        for col in df.columns:
            summary.append(f"  - {col}: {df[col].dtype}")
        
        return "\n".join(summary)
    
    def call_gemini_api(self, prompt, max_retries=3):
        """
        Call Gemini API to answer questions
        
        Args:
            prompt: Question or prompt for the AI
            max_retries: Maximum number of retry attempts
            
        Returns:
            str: AI response or error message
        """
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    API_URL,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload),
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract text from response
                content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
                if content:
                    return content
                else:
                    return "❌ No response from AI"
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️  API call failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return f"❌ API Error: {e}"
            except Exception as e:
                return f"❌ Error: {e}"
        
        return "❌ Failed to get response after retries"
    
    def answer_question(self, question, df=None):
        """
        Answer a question about the sheet data using AI
        
        Args:
            question: Natural language question about the data
            df: DataFrame to query (uses current_sheet_data if not provided)
            
        Returns:
            str: Answer to the question
        """
        if df is None:
            df = self.current_sheet_data
        
        if df is None:
            return "❌ No data loaded. Please fetch sheet data first."
        
        # Prepare context for AI
        data_context = self.get_data_summary(df)
        
        # Create prompt
        prompt = f"""You are a data analysis assistant. You have access to the following dataset:

{data_context}

User Question: {question}

Please analyze the data and provide a clear, concise answer to the question. If the question requires calculations or filtering, explain your reasoning. If the data doesn't contain enough information to answer the question, say so clearly.

Answer:"""
        
        print(f"\n🤔 Thinking...")
        answer = self.call_gemini_api(prompt)
        return answer
    
    def interactive_mode(self):
        """Run the agent in interactive Q&A mode"""
        print("\n" + "="*60)
        print("🤖 Google Sheets Q&A Agent - Interactive Mode")
        print("="*60)
        
        # Authenticate
        if not self.authenticate():
            return
        
        # Get sheet information
        print("\n📋 Enter Google Sheet information:")
        sheet_input = input("Sheet ID or URL: ").strip()
        
        if not sheet_input:
            print("❌ No sheet ID/URL provided")
            return
        
        worksheet_name = input("Worksheet name (press Enter for first sheet): ").strip() or None
        
        # Fetch data
        df = self.fetch_sheet_data(sheet_input, worksheet_name)
        
        if df is None:
            return
        
        # Show data summary
        print("\n" + "="*60)
        print("📊 DATA SUMMARY")
        print("="*60)
        print(self.get_data_summary(df))
        
        # Q&A loop
        print("\n" + "="*60)
        print("💬 Ask questions about the data (type 'quit' to exit)")
        print("="*60)
        
        while True:
            print("\n" + "-"*60)
            question = input("❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Special commands
            if question.lower() == 'summary':
                print("\n" + self.get_data_summary(df))
                continue
            
            if question.lower() == 'refresh':
                print("\n🔄 Refreshing data...")
                df = self.fetch_sheet_data(sheet_input, worksheet_name, use_cache=False)
                if df is not None:
                    print("✓ Data refreshed")
                continue
            
            # Answer question
            answer = self.answer_question(question, df)
            print(f"\n💡 Answer:\n{answer}")


def main():
    """Main entry point for the agent"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🤖 Google Sheets Q&A Agent                        ║
║        Powered by AI                                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("""
Usage: python sheets_agent.py [OPTIONS]

Options:
  -h, --help     Show this help message
  
Interactive Mode:
  Simply run: python sheets_agent.py
  
  The agent will:
  1. Authenticate with Google Sheets API
  2. Ask for sheet ID/URL
  3. Fetch and display data summary
  4. Answer your questions about the data
  
Special Commands:
  summary  - Show data summary again
  refresh  - Refresh data from sheet
  quit     - Exit the agent
  
Setup:
  1. Create Google Cloud project
  2. Enable Google Sheets API
  3. Create credentials (Service Account or OAuth)
  4. Save credentials as 'credentials.json'
  
For detailed setup instructions, see README_SHEETS_AGENT.md
            """)
            return
    
    # Run interactive mode
    agent = GoogleSheetsAgent()
    agent.interactive_mode()


if __name__ == "__main__":
    main()
