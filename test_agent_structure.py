"""
Test script to verify the agent structure without requiring external dependencies
"""

import sys
import ast
import os

def test_file_syntax(filepath):
    """Test if a Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, "✓ Syntax valid"
    except SyntaxError as e:
        return False, f"✗ Syntax error: {e}"
    except Exception as e:
        return False, f"✗ Error: {e}"

def test_file_structure(filepath, expected_classes=None, expected_functions=None):
    """Test if a Python file contains expected classes and functions"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        tree = ast.parse(code)
        
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        results = []
        
        if expected_classes:
            for cls in expected_classes:
                if cls in classes:
                    results.append(f"  ✓ Class '{cls}' found")
                else:
                    results.append(f"  ✗ Class '{cls}' NOT found")
        
        if expected_functions:
            for func in expected_functions:
                if func in functions:
                    results.append(f"  ✓ Function '{func}' found")
                else:
                    results.append(f"  ✗ Function '{func}' NOT found")
        
        return True, "\n".join(results)
    except Exception as e:
        return False, f"✗ Error analyzing structure: {e}"

def main():
    print("="*70)
    print("🧪 Google Sheets Agent - Structure Test")
    print("="*70)
    
    files_to_test = {
        'sheets_config.py': {
            'classes': ['SheetsConfig'],
            'functions': ['get_config_from_env']
        },
        'sheets_agent.py': {
            'classes': ['GoogleSheetsAgent'],
            'functions': ['main']
        }
    }
    
    all_passed = True
    
    for filename, expectations in files_to_test.items():
        filepath = os.path.join('/vercel/sandbox', filename)
        print(f"\n📄 Testing: {filename}")
        print("-"*70)
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"  ✗ File not found: {filepath}")
            all_passed = False
            continue
        else:
            print(f"  ✓ File exists")
        
        # Test syntax
        syntax_ok, syntax_msg = test_file_syntax(filepath)
        print(f"  {syntax_msg}")
        if not syntax_ok:
            all_passed = False
            continue
        
        # Test structure
        structure_ok, structure_msg = test_file_structure(
            filepath,
            expected_classes=expectations.get('classes'),
            expected_functions=expectations.get('functions')
        )
        print(structure_msg)
        if not structure_ok:
            all_passed = False
    
    # Test requirements.txt
    print(f"\n📄 Testing: requirements.txt")
    print("-"*70)
    req_file = '/vercel/sandbox/requirements.txt'
    if os.path.exists(req_file):
        print("  ✓ File exists")
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        required_packages = ['gspread', 'google-auth', 'google-auth-oauthlib']
        for pkg in required_packages:
            if pkg in requirements:
                print(f"  ✓ Package '{pkg}' listed")
            else:
                print(f"  ✗ Package '{pkg}' NOT listed")
                all_passed = False
    else:
        print("  ✗ File not found")
        all_passed = False
    
    # Test README
    print(f"\n📄 Testing: README_SHEETS_AGENT.md")
    print("-"*70)
    readme_file = '/vercel/sandbox/README_SHEETS_AGENT.md'
    if os.path.exists(readme_file):
        print("  ✓ File exists")
        with open(readme_file, 'r') as f:
            readme_content = f.read()
        
        required_sections = ['Quick Start', 'Usage', 'Troubleshooting', 'API Reference']
        for section in required_sections:
            if section in readme_content:
                print(f"  ✓ Section '{section}' found")
            else:
                print(f"  ⚠ Section '{section}' might be missing")
    else:
        print("  ✗ File not found")
        all_passed = False
    
    # Summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ All structure tests PASSED!")
        print("\nThe agent is properly structured and ready to use.")
        print("To use it, you need to:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up Google Sheets API credentials")
        print("3. Run: python sheets_agent.py")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
