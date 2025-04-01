#!/usr/bin/env python3
"""
Single script for Raycast to send clipboard content via Gmail and log to Git
"""

import os
import sys
import base64
import json
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
import time

# These imports will fail on first run, but succeed after restart with venv
google_imports_successful = False
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    google_imports_successful = True
except ImportError:
    pass  # Will be handled by restart_with_venv

def setup_environment():
    """Set up the virtual environment and install dependencies"""
    script_dir = Path(__file__).resolve().parent
    venv_dir = script_dir / "venv"
    
    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Get the Python interpreter from the virtual environment
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python3"
    
    if not venv_python.exists():
        print("Error: Virtual environment Python not found")
        sys.exit(1)
    
    # Install dependencies if needed
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", 
                       "google-auth-oauthlib", "google-auth-httplib2", 
                       "google-api-python-client", "pyobjc"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
    
    return venv_python

def restart_with_venv():
    """Restart the script using the virtual environment's Python"""
    if not google_imports_successful:
        venv_python = setup_environment()
        if os.environ.get("CLIPMAIL_RESTARTED") != "1":
            os.environ["CLIPMAIL_RESTARTED"] = "1"
            os.execv(str(venv_python), [str(venv_python), __file__])
        else:
            print("Error: Failed to import Google packages even after restarting with virtual environment")
            sys.exit(1)

def get_clipboard_text():
    """Get text from stdin (passed from shell script)"""
    try:
        text = sys.stdin.read()
        if text:
            print(f"Debug: Got text from stdin (length: {len(text)})")
            print(f"Debug: Text contains {text.count('\n')} newlines")
            print(f"Debug: First line: {text.split('\n')[0]}")
            return text
        print("Debug: No text received from stdin")
    except Exception as e:
        print(f"Debug: Error reading from stdin: {e}")
    
    print("Error: Could not get text from stdin")
    return ""

def validate_config(config):
    """Validate the configuration"""
    if not config.get("credentials_file"):
        print("Error: credentials_file is required in config")
        return False
    if not config.get("token_file"):
        print("Error: token_file is required in config")
        return False
    if not config.get("recipient_emails"):
        print("Error: recipient_emails is required in config")
        return False
    if not config.get("git_repo_path"):
        print("Error: git_repo_path is required in config")
        return False
    return True

def authenticate_gmail(credentials_file, token_file):
    """Authenticate with Gmail API"""
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    
    try:
        creds = None
        token_file = os.path.expanduser(token_file)
        credentials_file = os.path.expanduser(credentials_file)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    print(f"Error: OAuth credentials file not found at {credentials_file}")
                    print("Please download your OAuth credentials from Google Cloud Console:")
                    print("1. Go to https://console.cloud.google.com")
                    print("2. Create a new project or select an existing one")
                    print("3. Enable the Gmail API")
                    print("4. Create OAuth 2.0 credentials")
                    print("5. Download the credentials and save them to the path you specified")
                    sys.exit(1)
                    
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
                with open(token_file, "w") as token:
                    token.write(creds.to_json())
        
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"Authentication error: {e}")
        print("Full error details:")
        traceback.print_exc()
        raise

def send_email(service, sender, recipients, subject, message_text):
    """Send email using Gmail API"""
    try:
        message = MIMEText(message_text)
        message["to"] = recipients
        message["from"] = sender
        message["subject"] = subject
        
        raw_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
        service.users().messages().send(userId="me", body=raw_message).execute()
    except Exception as e:
        print(f"Error sending email: {e}")
        print("Full error details:")
        traceback.print_exc()
        raise

def log_and_git_commit(git_repo_path, recipients, message_text):
    """Log the sent email and commit to Git"""
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        git_repo = Path(os.path.expanduser(git_repo_path))
        
        # Create clipmail-logs directory if it doesn't exist
        logs_dir = git_repo / "clipmail-logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Write log to clipmail-logs directory
        log_file = logs_dir / f"sent_email_log_{date_str}.txt"
        with open(log_file, "a") as log:
            log.write(f"[{now.isoformat()}] Email sent to {recipients}\n{message_text[:200]}\n\n")

        # Change to the Git repo directory for Git operations
        original_dir = os.getcwd()
        os.chdir(str(git_repo))
        
        try:
            # Check if we're in a Git repository
            subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
            
            # Add and commit the log file
            subprocess.run(["git", "add", str(log_file)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", f"Log email sent on {now.isoformat()}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Try to push, but don't fail if it doesn't work
            try:
                subprocess.run(["git", "push"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Git push failed: {e}")
                print("Email was sent but changes were not pushed to remote.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Git operations failed: {e}")
            print("Email was sent but logging to Git failed.")
        finally:
            # Always change back to the original directory
            os.chdir(original_dir)
            
    except Exception as e:
        print(f"Error in Git operations: {e}")
        print("Full error details:")
        traceback.print_exc()

def main():
    try:
        # Restart using virtual environment's Python if needed
        restart_with_venv()
        
        # Load configuration from JSON file
        config_file = Path.home() / ".clipmail_config.json"
        
        if not config_file.exists():
            print("Configuration file not found. Creating one...")
            config = {
                "credentials_file": input("Enter path to Gmail OAuth credentials file (e.g. ~/.credentials/client_secret.json): "),
                "token_file": input("Enter path for OAuth token file (e.g. ~/.credentials/gmail_token.json): "),
                "recipient_emails": input("Enter recipient email(s) (comma-separated): "),
                "git_repo_path": input("Enter Git repo path for logging: ")
            }
            
            if not validate_config(config):
                print("Invalid configuration. Please try again.")
                return
            
            # Ensure config directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
                print(f"Configuration saved to {config_file}")
        else:
            with open(config_file) as f:
                config = json.load(f)
                if not validate_config(config):
                    print("Invalid configuration. Please delete ~/.clipmail_config.json and try again.")
                    return

        # Get clipboard content
        text = get_clipboard_text()
        if not text:
            print("Clipboard is empty!")
            return

        # Send email
        service = authenticate_gmail(config["credentials_file"], config["token_file"])
        send_email(
            service=service,
            sender=config["recipient_emails"].split(",")[0],
            recipients=config["recipient_emails"],
            subject="ClipMail: Clipboard Content",
            message_text=text
        )
        
        # Log to Git
        log_and_git_commit(
            git_repo_path=config["git_repo_path"],
            recipients=config["recipient_emails"],
            message_text=text
        )
        
        print("Success! Clipboard content sent and logged.")
    
    except Exception as e:
        print(f"Error: {e}")
        print("Full error details:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 