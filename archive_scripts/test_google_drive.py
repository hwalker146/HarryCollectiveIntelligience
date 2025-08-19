#!/usr/bin/env python3
"""
Test Google Drive connection and authentication
"""
import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google_drive_sync import GoogleDriveSync

def test_google_drive():
    """Test Google Drive authentication and basic operations"""
    
    print("🔍 Testing Google Drive connection...")
    print("=" * 50)
    
    # Check if credential files exist
    print("📋 Checking credential files:")
    if os.path.exists('credentials.json'):
        print("  ✅ credentials.json found")
        try:
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
                if 'installed' in creds:
                    print("  ✅ Valid credentials.json format")
                else:
                    print("  ❌ Invalid credentials.json format - missing 'installed' key")
        except Exception as e:
            print(f"  ❌ Error reading credentials.json: {e}")
    else:
        print("  ❌ credentials.json NOT FOUND")
    
    if os.path.exists('token.json'):
        print("  ✅ token.json found")
        try:
            with open('token.json', 'r') as f:
                token = json.load(f)
                if 'token' in token:
                    print("  ✅ Valid token.json format")
                else:
                    print("  ❌ Invalid token.json format - missing 'token' key")
        except Exception as e:
            print(f"  ❌ Error reading token.json: {e}")
    else:
        print("  ❌ token.json NOT FOUND")
    
    # Test authentication
    print("\n🔐 Testing authentication:")
    try:
        sync = GoogleDriveSync()
        auth_result = sync.authenticate()
        
        if auth_result:
            print("  ✅ Authentication successful!")
            
            # Test folder creation
            print("\n📁 Testing folder operations:")
            try:
                folder_result = sync.create_folder_structure()
                if folder_result:
                    print("  ✅ Folder structure created successfully!")
                else:
                    print("  ❌ Folder structure creation failed")
            except Exception as e:
                print(f"  ❌ Folder creation error: {e}")
                
        else:
            print("  ❌ Authentication failed!")
            
    except Exception as e:
        print(f"  ❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_google_drive()