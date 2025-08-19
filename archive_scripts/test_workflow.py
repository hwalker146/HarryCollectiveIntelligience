#!/usr/bin/env python3
"""
Test script for GitHub Actions workflow
Validates all components without doing actual processing
"""
import os
import sys
from datetime import datetime

def test_environment():
    """Test that all environment variables are available"""
    print("🧪 Testing GitHub Actions environment...")
    
    required_secrets = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY', 
        'EMAIL_USER',
        'EMAIL_PASSWORD'
    ]
    
    missing_secrets = []
    for secret in required_secrets:
        if not os.getenv(secret):
            missing_secrets.append(secret)
        else:
            print(f"✅ {secret}: Available")
    
    if missing_secrets:
        print(f"❌ Missing secrets: {missing_secrets}")
        return False
    
    return True

def test_file_structure():
    """Test that the organized file structure exists"""
    print("\n📂 Testing file structure...")
    
    required_dirs = [
        'podcast_files',
        'podcast_files/individual_transcripts',
        'podcast_files/individual_analysis', 
        'podcast_files/master_files',
        'podcast_files/daily_reports'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}: Exists")
        else:
            print(f"❌ {dir_path}: Missing")
            os.makedirs(dir_path, exist_ok=True)
            print(f"  📁 Created {dir_path}")
    
    return True

def test_google_credentials():
    """Test Google Drive credentials"""
    print("\n🔐 Testing Google Drive credentials...")
    
    if os.path.exists('credentials.json'):
        print("✅ credentials.json: Available")
        creds_valid = True
    else:
        print("❌ credentials.json: Missing")
        creds_valid = False
        
    if os.path.exists('token.json'):
        print("✅ token.json: Available")
        token_valid = True
    else:
        print("❌ token.json: Missing")  
        token_valid = False
        
    return creds_valid and token_valid

def test_podcast_files():
    """Test that organized podcast files exist"""
    print("\n📄 Testing podcast files...")
    
    transcript_dir = 'podcast_files/individual_transcripts'
    if os.path.exists(transcript_dir):
        files = [f for f in os.listdir(transcript_dir) if f.endswith('.md')]
        print(f"✅ Found {len(files)} transcript files")
        for file in files[:3]:  # Show first 3
            print(f"  📝 {file}")
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more files")
    else:
        print("❌ No transcript files found")
    
    return True

def test_dependencies():
    """Test that required Python packages are available"""
    print("\n📦 Testing Python dependencies...")
    
    try:
        import anthropic
        print("✅ anthropic: Available")
    except ImportError:
        print("❌ anthropic: Missing")
        
    try:
        import openai
        print("✅ openai: Available")
    except ImportError:
        print("❌ openai: Missing")
        
    try:
        from google.oauth2.credentials import Credentials
        print("✅ google-api-python-client: Available")
    except ImportError:
        print("❌ google-api-python-client: Missing")
    
    return True

def main():
    """Run all tests"""
    print("🚀 GITHUB ACTIONS WORKFLOW TEST")
    print("=" * 50)
    print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = 0
    total_tests = 5
    
    if test_environment():
        tests_passed += 1
        
    if test_file_structure():
        tests_passed += 1
        
    if test_google_credentials():
        tests_passed += 1
        
    if test_podcast_files():
        tests_passed += 1
        
    if test_dependencies():
        tests_passed += 1
    
    print(f"\n📊 TEST RESULTS: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! Workflow environment is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())