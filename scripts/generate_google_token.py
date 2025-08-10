#!/usr/bin/env python3
"""
Generate Google Drive token.json for GitHub Actions
Run this locally to authenticate and generate the token file
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def generate_token():
    """Generate token.json for GitHub Actions"""
    
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("Please download your Google OAuth2 credentials and save as 'credentials.json'")
        print("Get them from: https://console.cloud.google.com/")
        return
    
    print("🔐 Starting Google Drive authentication...")
    print("This will open a browser window for authentication.")
    
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token for future use
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("✅ Authentication successful!")
    print("📄 token.json created")
    
    # Show the contents for GitHub Secrets
    print("\n" + "="*60)
    print("COPY THESE FOR GITHUB SECRETS:")
    print("="*60)
    
    print("\n1. GOOGLE_CREDENTIALS_JSON:")
    print("-" * 30)
    with open('credentials.json', 'r') as f:
        print(f.read().strip())
    
    print("\n2. GOOGLE_TOKEN_JSON:")
    print("-" * 30)
    with open('token.json', 'r') as f:
        print(f.read().strip())
    
    print("\n" + "="*60)
    print("Add these as GitHub Secrets in:")
    print("https://github.com/hwalker146/HarryCollectiveIntelligience/settings/secrets/actions")

if __name__ == "__main__":
    generate_token()