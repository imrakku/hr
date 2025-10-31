"""
Example usage of the Google Sheets Q&A Agent

This file demonstrates how to use the agent programmatically in your own scripts.
"""

from sheets_agent import GoogleSheetsAgent
from sheets_config import SheetsConfig

def example_basic_usage():
    """Basic usage example"""
    print("="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    # Initialize the agent
    agent = GoogleSheetsAgent()
    
    # Authenticate
    if not agent.authenticate():
        print("Authentication failed. Please check your credentials.")
        return
    
    # Fetch data from a Google Sheet
    # Replace with your actual sheet ID or URL
    sheet_id = "YOUR_SHEET_ID_HERE"
    df = agent.fetch_sheet_data(sheet_id)
    
    if df is not None:
        # Display data summary
        print("\n" + agent.get_data_summary())
        
        # Ask questions
        questions = [
            "What is the total number of rows?",
            "What are the column names?",
            "Can you summarize the data?"
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            answer = agent.answer_question(question)
            print(f"💡 Answer: {answer}")


def example_custom_config():
    """Example with custom configuration"""
    print("\n" + "="*60)
    print("Example 2: Custom Configuration")
    print("="*60)
    
    # Create custom configuration
    config = SheetsConfig(
        credentials_file="path/to/your/credentials.json",
        token_file="path/to/your/token.json"
    )
    
    # Initialize agent with custom config
    agent = GoogleSheetsAgent(config=config)
    
    # Rest of the code is the same as basic usage
    print("Agent initialized with custom configuration")


def example_multiple_sheets():
    """Example of working with multiple sheets"""
    print("\n" + "="*60)
    print("Example 3: Multiple Worksheets")
    print("="*60)
    
    agent = GoogleSheetsAgent()
    
    if not agent.authenticate():
        return
    
    sheet_id = "YOUR_SHEET_ID_HERE"
    
    # Fetch data from different worksheets
    worksheets = ["Sheet1", "Sheet2", "Summary"]
    
    for worksheet_name in worksheets:
        print(f"\n📊 Fetching data from: {worksheet_name}")
        df = agent.fetch_sheet_data(sheet_id, worksheet_name=worksheet_name)
        
        if df is not None:
            print(f"✓ Loaded {len(df)} rows from {worksheet_name}")
            
            # Ask a question about this specific worksheet
            answer = agent.answer_question(
                f"What is unique about the data in {worksheet_name}?",
                df=df
            )
            print(f"💡 {answer}")


def example_data_analysis():
    """Example of data analysis tasks"""
    print("\n" + "="*60)
    print("Example 4: Data Analysis")
    print("="*60)
    
    agent = GoogleSheetsAgent()
    
    if not agent.authenticate():
        return
    
    sheet_id = "YOUR_SHEET_ID_HERE"
    df = agent.fetch_sheet_data(sheet_id)
    
    if df is None:
        return
    
    # Common data analysis questions
    analysis_questions = [
        "What is the average value in the numeric columns?",
        "Are there any missing values in the dataset?",
        "What is the distribution of values in the first column?",
        "Can you identify any outliers or unusual patterns?",
        "What insights can you derive from this data?"
    ]
    
    print("\n🔍 Performing data analysis...")
    
    for i, question in enumerate(analysis_questions, 1):
        print(f"\n{i}. {question}")
        answer = agent.answer_question(question)
        print(f"   → {answer[:200]}...")  # Print first 200 chars


def example_with_pandas():
    """Example showing integration with pandas"""
    print("\n" + "="*60)
    print("Example 5: Integration with Pandas")
    print("="*60)
    
    agent = GoogleSheetsAgent()
    
    if not agent.authenticate():
        return
    
    sheet_id = "YOUR_SHEET_ID_HERE"
    df = agent.fetch_sheet_data(sheet_id)
    
    if df is None:
        return
    
    # Now you can use pandas operations on the DataFrame
    print("\n📊 Pandas Operations:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # You can also perform pandas operations and then ask questions
    # For example, filter the data
    # filtered_df = df[df['column_name'] > 100]
    # answer = agent.answer_question("Analyze this filtered data", df=filtered_df)


def example_error_handling():
    """Example with proper error handling"""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)
    
    agent = GoogleSheetsAgent()
    
    try:
        # Authenticate
        if not agent.authenticate():
            raise Exception("Authentication failed")
        
        # Try to fetch data
        sheet_id = "YOUR_SHEET_ID_HERE"
        df = agent.fetch_sheet_data(sheet_id)
        
        if df is None:
            raise Exception("Failed to fetch data")
        
        # Ask question
        answer = agent.answer_question("What is this data about?")
        
        if answer.startswith("❌"):
            raise Exception("Failed to get answer from AI")
        
        print(f"✓ Success: {answer}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Please check:")
        print("  - Your credentials are valid")
        print("  - The sheet ID is correct")
        print("  - The sheet is shared with your service account")
        print("  - You have internet connectivity")


def main():
    """Run all examples"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Google Sheets Q&A Agent - Usage Examples            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

This file contains several examples of how to use the agent.
Before running, make sure to:

1. Install dependencies: pip install -r requirements.txt
2. Set up Google Sheets API credentials
3. Replace 'YOUR_SHEET_ID_HERE' with your actual sheet ID

Note: These examples won't run without proper setup.
They are meant to demonstrate the API usage.
    """)
    
    print("\nAvailable examples:")
    print("1. Basic Usage")
    print("2. Custom Configuration")
    print("3. Multiple Worksheets")
    print("4. Data Analysis")
    print("5. Integration with Pandas")
    print("6. Error Handling")
    
    print("\nTo run an example, uncomment the corresponding function call below:")
    print("(Currently all examples are commented out to prevent errors)")
    
    # Uncomment the example you want to run:
    # example_basic_usage()
    # example_custom_config()
    # example_multiple_sheets()
    # example_data_analysis()
    # example_with_pandas()
    # example_error_handling()


if __name__ == "__main__":
    main()
