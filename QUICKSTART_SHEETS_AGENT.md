# 🚀 Quick Start Guide - Google Sheets Q&A Agent

Get up and running with the Google Sheets Q&A Agent in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `gspread` - Google Sheets API client
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth support
- `google-auth-httplib2` - HTTP transport
- `pandas` - Data manipulation
- `requests` - HTTP requests

## Step 2: Set Up Google Sheets API

### Option A: Service Account (Recommended)

**Best for:** Automation, server applications, accessing sheets programmatically

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create/Select Project**
   - Click "Select a project" → "New Project"
   - Name it (e.g., "Sheets Agent")
   - Click "Create"

3. **Enable Google Sheets API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click on it and press "Enable"

4. **Create Service Account**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Enter name (e.g., "sheets-agent")
   - Click "Create and Continue"
   - Skip optional steps, click "Done"

5. **Create Key**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose "JSON"
   - Click "Create" - file will download

6. **Save Credentials**
   - Rename downloaded file to `credentials.json`
   - Move it to your project directory (`/vercel/sandbox/`)

7. **Share Your Sheet**
   - Open your Google Sheet
   - Click "Share" button
   - Copy the service account email (from credentials.json, looks like: `name@project-id.iam.gserviceaccount.com`)
   - Paste it in the share dialog
   - Give "Viewer" access (or "Editor" if you plan to write data)
   - Click "Send"

### Option B: OAuth 2.0

**Best for:** Personal use, desktop applications

1. Follow steps 1-3 from Option A
2. **Create OAuth Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen first
   - Choose "Desktop app" as application type
   - Name it (e.g., "Sheets Agent Desktop")
   - Click "Create"
3. **Download Credentials**
   - Click the download icon next to your OAuth client
   - Save as `credentials.json` in project directory
4. **First Run**
   - When you run the agent, it will open a browser
   - Sign in with your Google account
   - Grant permissions
   - Token will be saved for future use

## Step 3: Run the Agent

```bash
python3 sheets_agent.py
```

Or with Python:
```bash
python sheets_agent.py
```

## Step 4: Use the Agent

1. **Enter Sheet Information**
   ```
   Sheet ID or URL: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
   Worksheet name (press Enter for first sheet): 
   ```

2. **View Data Summary**
   - The agent will display rows, columns, and sample data

3. **Ask Questions**
   ```
   ❓ Your question: What is the average salary?
   ❓ Your question: How many employees are in the IT department?
   ❓ Your question: Show me the top 5 performers
   ```

4. **Special Commands**
   - `summary` - Show data summary again
   - `refresh` - Reload data from sheet
   - `quit` - Exit the agent

## Example Session

```
🤖 Google Sheets Q&A Agent - Interactive Mode
============================================================

✓ Service account credentials valid
✓ Authenticated using service account

📋 Enter Google Sheet information:
Sheet ID or URL: https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit
Worksheet name (press Enter for first sheet): 

📥 Fetching data from Google Sheets...
✓ Fetched 100 rows and 4 columns
✓ Columns: Name, Department, Salary, Join Date

============================================================
📊 DATA SUMMARY
============================================================
Dataset: 1ABC...XYZ_default
Rows: 100
Columns: 4

Column Names: Name, Department, Salary, Join Date

First 3 rows:
        Name Department  Salary   Join Date
0   John Doe         IT   75000  2020-01-15
1  Jane Smith         HR   68000  2019-06-20
2 Bob Johnson    Finance   92000  2018-03-10

============================================================
💬 Ask questions about the data (type 'quit' to exit)
============================================================

------------------------------------------------------------
❓ Your question: What is the average salary?

🤔 Thinking...

💡 Answer:
Based on the data, the average salary across all 100 employees is $76,450.

------------------------------------------------------------
❓ Your question: quit

👋 Goodbye!
```

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the same directory as `sheets_agent.py`
- Check the filename is exactly `credentials.json` (case-sensitive)

### "Spreadsheet not found"
- Verify the sheet ID/URL is correct
- For service accounts: Make sure you shared the sheet with the service account email
- For OAuth: Make sure you have access to the sheet with your Google account

### "Module not found" errors
- Run: `pip install -r requirements.txt`
- Make sure you're using the correct Python version (3.8+)

### Authentication issues
- Delete `token.json` and try again
- Check your credentials.json is valid JSON
- Verify Google Sheets API is enabled in your project

## Next Steps

- Read the full documentation: `README_SHEETS_AGENT.md`
- Check example code: `example_usage.py`
- Integrate with your own scripts
- Try different types of questions

## Common Questions to Try

**Statistical:**
- "What is the average/sum/max/min of column X?"
- "Calculate the standard deviation"
- "Show me the distribution"

**Filtering:**
- "How many rows have X greater than Y?"
- "Find all entries where status is 'active'"
- "Show me records from 2023"

**Comparison:**
- "Compare department A vs department B"
- "What's the difference between Q1 and Q2?"
- "Which category has the highest value?"

**Analysis:**
- "What trends do you see in the data?"
- "Are there any outliers?"
- "What insights can you provide?"
- "Summarize the key findings"

## Support

For more help:
- Check `README_SHEETS_AGENT.md` for detailed documentation
- Review `example_usage.py` for code examples
- Visit Google Sheets API documentation: https://developers.google.com/sheets/api

---

**Happy analyzing! 📊🤖**
