"""
Configuration module for Google Sheets Agent
Handles authentication and connection setup for Google Sheets API
"""

import os
import json
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "credentials_file": "credentials.json",
    "token_file": "token.json",
    "scopes": [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
}

class SheetsConfig:
    """Configuration manager for Google Sheets API"""
    
    def __init__(self, credentials_file=None, token_file=None):
        """
        Initialize configuration
        
        Args:
            credentials_file: Path to Google API credentials JSON file
            token_file: Path to store OAuth token
        """
        self.credentials_file = credentials_file or DEFAULT_CONFIG["credentials_file"]
        self.token_file = token_file or DEFAULT_CONFIG["token_file"]
        self.scopes = DEFAULT_CONFIG["scopes"]
        
    def credentials_exist(self):
        """Check if credentials file exists"""
        return Path(self.credentials_file).exists()
    
    def token_exists(self):
        """Check if token file exists"""
        return Path(self.token_file).exists()
    
    def get_credentials_path(self):
        """Get absolute path to credentials file"""
        return str(Path(self.credentials_file).absolute())
    
    def get_token_path(self):
        """Get absolute path to token file"""
        return str(Path(self.token_file).absolute())
    
    def validate_credentials(self):
        """
        Validate that credentials file is properly formatted
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.credentials_exist():
            return False, f"Credentials file not found: {self.credentials_file}"
        
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
                
            # Check for service account credentials
            if "type" in creds_data and creds_data["type"] == "service_account":
                required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
                missing = [f for f in required_fields if f not in creds_data]
                if missing:
                    return False, f"Missing required fields in service account credentials: {', '.join(missing)}"
                return True, "Service account credentials valid"
            
            # Check for OAuth credentials
            elif "installed" in creds_data or "web" in creds_data:
                return True, "OAuth credentials valid"
            
            else:
                return False, "Unknown credentials format. Expected service account or OAuth credentials."
                
        except json.JSONDecodeError:
            return False, "Credentials file is not valid JSON"
        except Exception as e:
            return False, f"Error validating credentials: {str(e)}"
    
    def __repr__(self):
        return f"SheetsConfig(credentials='{self.credentials_file}', token='{self.token_file}')"


# Environment variable support
def get_config_from_env():
    """
    Create configuration from environment variables
    
    Environment variables:
        GOOGLE_CREDENTIALS_FILE: Path to credentials JSON
        GOOGLE_TOKEN_FILE: Path to token file
    
    Returns:
        SheetsConfig instance
    """
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", DEFAULT_CONFIG["credentials_file"])
    token_file = os.getenv("GOOGLE_TOKEN_FILE", DEFAULT_CONFIG["token_file"])
    return SheetsConfig(creds_file, token_file)
