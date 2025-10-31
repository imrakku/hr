"""
Demo script for Google Sheets Q&A Agent
Shows the agent's capabilities without requiring actual Google Sheets credentials
"""

import pandas as pd
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample employee data for demonstration"""
    departments = ['IT', 'HR', 'Finance', 'Marketing', 'Sales']
    names = [
        'John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams', 'Charlie Brown',
        'Diana Prince', 'Eve Davis', 'Frank Miller', 'Grace Lee', 'Henry Wilson',
        'Ivy Chen', 'Jack Taylor', 'Kate Anderson', 'Leo Martinez', 'Mia Garcia'
    ]
    
    data = []
    base_date = datetime(2018, 1, 1)
    
    for i, name in enumerate(names):
        dept = random.choice(departments)
        age = random.randint(25, 55)
        
        # Salary based on department and age
        base_salary = {
            'IT': 70000,
            'HR': 60000,
            'Finance': 80000,
            'Marketing': 65000,
            'Sales': 75000
        }[dept]
        
        salary = base_salary + (age - 25) * 1000 + random.randint(-5000, 10000)
        join_date = base_date + timedelta(days=random.randint(0, 1825))
        
        data.append({
            'Name': name,
            'Age': age,
            'Department': dept,
            'Salary': salary,
            'Join Date': join_date.strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(data)


def simulate_agent_response(question, df):
    """Simulate AI responses for common questions"""
    question_lower = question.lower()
    
    # Statistical questions
    if 'average salary' in question_lower or 'mean salary' in question_lower:
        avg_salary = df['Salary'].mean()
        return f"The average salary across all {len(df)} employees is ${avg_salary:,.2f}."
    
    if 'total' in question_lower and 'salary' in question_lower:
        total = df['Salary'].sum()
        return f"The total salary expenditure is ${total:,.2f}."
    
    if 'highest salary' in question_lower or 'maximum salary' in question_lower:
        max_row = df.loc[df['Salary'].idxmax()]
        return f"The highest salary is ${max_row['Salary']:,} earned by {max_row['Name']} in the {max_row['Department']} department."
    
    # Department questions
    if 'department' in question_lower and 'average' in question_lower:
        dept_avg = df.groupby('Department')['Salary'].mean().sort_values(ascending=False)
        result = "Average salary by department:\n"
        for dept, avg in dept_avg.items():
            result += f"  • {dept}: ${avg:,.2f}\n"
        return result.strip()
    
    if 'how many' in question_lower and 'department' in question_lower:
        dept_counts = df['Department'].value_counts()
        result = "Employee count by department:\n"
        for dept, count in dept_counts.items():
            result += f"  • {dept}: {count} employees\n"
        return result.strip()
    
    # Age questions
    if 'average age' in question_lower:
        avg_age = df['Age'].mean()
        return f"The average age of employees is {avg_age:.1f} years."
    
    # Join date questions
    if 'joined' in question_lower and '2020' in question_lower:
        count = len(df[df['Join Date'].str.startswith('2020')])
        return f"{count} employees joined in 2020."
    
    # General insights
    if 'insight' in question_lower or 'summary' in question_lower:
        return f"""Here are some key insights from the data:

• Total Employees: {len(df)}
• Average Salary: ${df['Salary'].mean():,.2f}
• Salary Range: ${df['Salary'].min():,} - ${df['Salary'].max():,}
• Departments: {', '.join(df['Department'].unique())}
• Average Age: {df['Age'].mean():.1f} years
• Most common department: {df['Department'].mode()[0]} ({df['Department'].value_counts().iloc[0]} employees)
"""
    
    # Default response
    return f"I can help you analyze this data. The dataset contains {len(df)} rows and {len(df.columns)} columns: {', '.join(df.columns)}. Try asking about averages, totals, or specific departments!"


def demo_interactive_mode():
    """Run a demo of the interactive mode"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🤖 Google Sheets Q&A Agent - DEMO MODE              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

This is a demonstration of the agent's capabilities using sample data.
In real usage, the agent would connect to your actual Google Sheets.
    """)
    
    print("\n" + "="*60)
    print("📊 Loading Sample Data...")
    print("="*60)
    
    # Create sample data
    df = create_sample_data()
    
    print(f"\n✓ Loaded sample employee data")
    print(f"✓ {len(df)} rows and {len(df.columns)} columns")
    print(f"✓ Columns: {', '.join(df.columns)}")
    
    # Show data summary
    print("\n" + "="*60)
    print("📊 DATA SUMMARY")
    print("="*60)
    print(f"\nDataset: Sample Employee Data")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"\nColumn Names: {', '.join(df.columns)}")
    print(f"\nFirst 5 rows:")
    print(df.head().to_string(index=False))
    
    # Q&A Demo
    print("\n" + "="*60)
    print("💬 DEMO Q&A SESSION")
    print("="*60)
    print("\nTry these example questions (or type your own):")
    print("  1. What is the average salary?")
    print("  2. Show me the average salary by department")
    print("  3. How many employees are in each department?")
    print("  4. Who has the highest salary?")
    print("  5. What insights can you provide?")
    print("  6. quit - Exit demo")
    
    example_questions = [
        "What is the average salary?",
        "Show me the average salary by department",
        "How many employees are in each department?",
        "Who has the highest salary?",
        "What insights can you provide?"
    ]
    
    while True:
        print("\n" + "-"*60)
        user_input = input("❓ Your question (or number 1-6): ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', 'q', '6']:
            print("\n👋 Demo completed! To use with real Google Sheets:")
            print("   1. Set up credentials (see QUICKSTART_SHEETS_AGENT.md)")
            print("   2. Run: python3 sheets_agent.py")
            break
        
        # Handle numbered input
        if user_input.isdigit():
            num = int(user_input)
            if 1 <= num <= 5:
                question = example_questions[num - 1]
                print(f"   Selected: {question}")
            else:
                print("   Invalid number. Please choose 1-6.")
                continue
        else:
            question = user_input
        
        # Simulate thinking
        print("\n🤔 Analyzing data...")
        
        # Get answer
        answer = simulate_agent_response(question, df)
        print(f"\n💡 Answer:\n{answer}")


def demo_programmatic_usage():
    """Demo programmatic usage"""
    print("\n" + "="*60)
    print("💻 PROGRAMMATIC USAGE DEMO")
    print("="*60)
    
    df = create_sample_data()
    
    print("\nExample code:")
    print("""
from sheets_agent import GoogleSheetsAgent

# Initialize and authenticate
agent = GoogleSheetsAgent()
agent.authenticate()

# Fetch data
df = agent.fetch_sheet_data("YOUR_SHEET_ID")

# Ask questions
answer = agent.answer_question("What is the average salary?")
print(answer)
    """)
    
    print("\nSimulated output:")
    questions = [
        "What is the average salary?",
        "How many employees are in each department?",
        "What insights can you provide?"
    ]
    
    for q in questions:
        print(f"\n❓ Question: {q}")
        answer = simulate_agent_response(q, df)
        print(f"💡 Answer: {answer[:150]}...")


def main():
    """Main demo function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--programmatic':
        demo_programmatic_usage()
    else:
        demo_interactive_mode()


if __name__ == "__main__":
    main()
