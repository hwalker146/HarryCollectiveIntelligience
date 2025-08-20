#!/usr/bin/env python3
"""
Test email functionality with Gmail
"""
import smtplib
import os
from email.mime.text import MIMEText

def test_gmail():
    sender_email = "aipodcastdigest@gmail.com"
    sender_password = "yaxqzzxxskqecdhc"
    recipient = "hwalker146@outlook.com"
    
    print("🧪 Testing Gmail SMTP connection...")
    print(f"📧 From: {sender_email}")
    print(f"📧 To: {recipient}")
    
    try:
        # Create test message
        msg = MIMEText("Test email from Canary Media aggregator script")
        msg['Subject'] = "Test - Canary Media Script"
        msg['From'] = sender_email
        msg['To'] = recipient
        
        # Connect to Gmail SMTP
        print("🔗 Connecting to Gmail SMTP...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            print("🔒 Starting TLS...")
            server.starttls()
            
            print("🔑 Logging in...")
            server.login(sender_email, sender_password)
            
            print("📤 Sending test email...")
            server.send_message(msg)
            
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

if __name__ == "__main__":
    test_gmail()