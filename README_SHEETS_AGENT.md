# 🤖 Google Sheets Q&A Agent

An AI-powered agent that fetches data from Google Sheets and answers natural language questions about the data using Google's Gemini AI.

## 🌟 Features

- **Easy Authentication**: Supports both Service Account and OAuth 2.0 authentication
- **Smart Data Fetching**: Retrieves data from any Google Sheet with caching support
- **Natural Language Q&A**: Ask questions in plain English about your data
- **Interactive Mode**: User-friendly CLI interface for exploring data
- **Data Summaries**: Automatic generation of dataset overviews
- **Error Handling**: Robust error handling with helpful messages

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- Google Sheets API enabled
- API credentials (Service Account or OAuth 2.0)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Sheets API

#### Option A: Service Account (Recommended for automation)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and click "Create"
   - Grant the service account appropriate roles (e.g., "Viewer")
   - Click "Done"
5. Create and Download Key:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Download the file and save it as `credentials.json` in the project directory
6. **Important**: Copy the service account email (looks like `name@project-id.iam.gserviceaccount.com`)
7. Share your Google Sheet with this email address (give at least "Viewer" access)

#### Option B: OAuth 2.0 (For personal use)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API** (same as above)
4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials file
   - Save it as `credentials.json` in the project directory
5. On first run, you'll be prompted to authorize the application in your browser

### 3. Run the Agent

```bash
python sheets_agent.py
```

## 💻 Usage

### Interactive Mode

Run the agent and follow the prompts:

```bash
python sheets_agent.py
```

The agent will:
1. Authenticate with Google Sheets API
2. Ask for your Google Sheet ID or URL
3. Optionally ask for a specific worksheet name
4. Fetch and display a data summary
5. Enter Q&A mode where you can ask questions

### Example Session

```
🤖 Google Sheets Q&A Agent - Interactive Mode
============================================================

✓ Service account credentials valid
✓ Authenticated using service account

📋 Enter Google Sheet information:
Sheet ID or URL: https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit
Worksheet name (press Enter for first sheet): 

📥 Fetching data from Google Sheets...
✓ Fetched 150 rows and 5 columns
✓ Columns: Name, Age, Department, Salary, Join Date

============================================================
📊 DATA SUMMARY
============================================================
Dataset: 1ABC...XYZ_default
Rows: 150
Columns: 5

Column Names: Name, Age, Department, Salary, Join Date

First 3 rows:
     Name  Age Department  Salary   Join Date
0  John Doe   28        IT   75000  2020-01-15
1  Jane Smith 32        HR   68000  2019-06-20
2  Bob Johnson 45   Finance   92000  2018-03-10

============================================================
💬 Ask questions about the data (type 'quit' to exit)
============================================================

------------------------------------------------------------
❓ Your question: What is the average salary by department?

🤔 Thinking...

💡 Answer:
Based on the data, here are the average salaries by department:

- IT: $76,500
- HR: $65,200
- Finance: $88,300
- Marketing: $71,800

The Finance department has the highest average salary, while HR has the lowest.

------------------------------------------------------------
❓ Your question: How many employees joined in 2020?

🤔 Thinking...

💡 Answer:
According to the Join Date column, 42 employees joined in 2020.

------------------------------------------------------------
❓ Your question: quit

👋 Goodbye!
```

### Special Commands

While in Q&A mode, you can use these special commands:

- `summary` - Display the data summary again
- `refresh` - Refresh data from the Google Sheet (clears cache)
- `quit` or `exit` or `q` - Exit the agent

## 🔧 Configuration

### Using Environment Variables

You can configure the agent using environment variables:

```bash
export GOOGLE_CREDENTIALS_FILE="/path/to/credentials.json"
export GOOGLE_TOKEN_FILE="/path/to/token.json"
python sheets_agent.py
```

### Programmatic Usage

You can also use the agent in your own Python scripts:

```python
from sheets_agent import GoogleSheetsAgent

# Initialize agent
agent = GoogleSheetsAgent()

# Authenticate
if agent.authenticate():
    # Fetch data
    df = agent.fetch_sheet_data("YOUR_SHEET_ID_OR_URL")
    
    # Ask questions
    answer = agent.answer_question("What is the total revenue?")
    print(answer)
    
    # Get data summary
    summary = agent.get_data_summary()
    print(summary)
```

## 📊 Example Questions You Can Ask

- "What is the average value in column X?"
- "How many rows have Y greater than 100?"
- "Which department has the highest sales?"
- "Show me the top 5 products by revenue"
- "What percentage of customers are from California?"
- "Compare the performance between Q1 and Q2"
- "Find all entries where status is 'pending'"
- "What is the total sum of column Z?"

## 🛠️ Troubleshooting

### "Credentials file not found"

Make sure you have downloaded the credentials JSON file and saved it as `credentials.json` in the project directory.

### "Spreadsheet not found"

This error occurs when:
1. The sheet ID/URL is incorrect
2. The sheet is not shared with your service account email
3. The sheet doesn't exist or was deleted

**Solution**: 
- Verify the sheet ID/URL
- Share the sheet with your service account email (for service accounts)
- Ensure you have access to the sheet (for OAuth)

### "Worksheet not found"

The specified worksheet name doesn't exist in the spreadsheet.

**Solution**: 
- Check the worksheet name (it's case-sensitive)
- Leave the worksheet name blank to use the first sheet

### "API Error" or "Network Error"

Network connectivity issues or API quota exceeded.

**Solution**:
- Check your internet connection
- Verify your API key is valid
- Check Google Cloud Console for API quota limits

### Authentication Issues

If OAuth authentication fails:
1. Delete the `token.json` file
2. Run the agent again
3. Complete the authorization flow in your browser

## 🔐 Security Best Practices

1. **Never commit credentials**: Add `credentials.json` and `token.json` to `.gitignore`
2. **Restrict API access**: Use the principle of least privilege for service accounts
3. **Rotate keys regularly**: Periodically create new service account keys
4. **Use environment variables**: For production, use environment variables instead of files
5. **Monitor API usage**: Keep track of API calls in Google Cloud Console

## 📝 File Structure

```
.
├── sheets_agent.py          # Main agent implementation
├── sheets_config.py         # Configuration management
├── credentials.json         # Google API credentials (not in repo)
├── token.json              # OAuth token (not in repo)
├── requirements.txt        # Python dependencies
└── README_SHEETS_AGENT.md  # This file
```

## 🤝 Integration with Existing Project

This agent is designed to work alongside the existing HR Candidate Evaluation Tool. You can:

1. Use it to analyze candidate data stored in Google Sheets
2. Export evaluation results to Google Sheets and query them
3. Integrate it into the Streamlit app for live data analysis

## 📚 API Reference

### GoogleSheetsAgent Class

#### Methods

- `authenticate()` - Authenticate with Google Sheets API
- `fetch_sheet_data(sheet_id_or_url, worksheet_name=None, use_cache=True)` - Fetch data from sheet
- `answer_question(question, df=None)` - Answer a question about the data
- `get_data_summary(df=None)` - Get a formatted summary of the data
- `interactive_mode()` - Run the agent in interactive CLI mode

### SheetsConfig Class

#### Methods

- `credentials_exist()` - Check if credentials file exists
- `validate_credentials()` - Validate credentials format
- `get_credentials_path()` - Get absolute path to credentials
- `get_token_path()` - Get absolute path to token file

## 🎯 Future Enhancements

- [ ] Support for writing data back to sheets
- [ ] Advanced data visualization
- [ ] Multi-sheet analysis
- [ ] Export answers to PDF/CSV
- [ ] Web interface using Streamlit
- [ ] Scheduled data refresh
- [ ] Custom AI model selection

## 📄 License

This project is part of the IIM Sirmaur HR Evaluation Tool.

## 🙋 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Google Sheets API documentation
3. Check Google Cloud Console for API status

---

**Built with ❤️ for IIM Sirmaur**
