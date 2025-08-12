#!/usr/bin/env python3
"""
Debug email authentication issues
"""
import smtplib
from email.mime.text import MIMEText

def test_gmail_auth():
    """Test Gmail authentication with the provided credentials"""
    
    sender_email = 'aipodcastdigest@gmail.com'
    sender_password = 'yaxqzzxxskqecdhc'  # The app password you provided
    
    print(f"🧪 Testing Gmail authentication...")
    print(f"📧 Email: {sender_email}")
    print(f"🔑 App Password: {sender_password}")
    print(f"📏 Password Length: {len(sender_password)} characters")
    
    try:
        print("🔄 Connecting to Gmail SMTP...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Enable detailed logging
        
        print("🔄 Starting TLS...")
        server.starttls()
        
        print("🔄 Attempting login...")
        server.login(sender_email, sender_password)
        
        print("✅ Login successful!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("\n💡 This usually means:")
        print("1. 2FA is not enabled on aipodcastdigest@gmail.com")
        print("2. App password was generated from a different Gmail account")
        print("3. App password is incorrect or expired")
        return False
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    test_gmail_auth()