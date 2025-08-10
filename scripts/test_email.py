#!/usr/bin/env python3
"""
Test email sending functionality
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_email():
    """Test sending email with current configuration"""
    
    sender_email = os.getenv('EMAIL_USER', 'aipodcastdigest@gmail.com')
    sender_password = os.getenv('EMAIL_PASSWORD')
    recipient_email = 'hwalker146@outlook.com'
    
    print(f"📧 Testing email from {sender_email} to {recipient_email}")
    
    if not sender_password:
        print("❌ EMAIL_PASSWORD not found - check your GitHub secrets")
        return False
    
    # Create test message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"TEST - Podcast System Email Test {datetime.now().strftime('%H:%M')}"
    
    test_content = f"""
# Email Test Successful! 

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test email from your automated podcast processing system.

If you received this email, the email system is working correctly!

## Next Steps:
- Daily emails will arrive at 6 AM EDT
- Check GitHub Actions for workflow status
- Your system is monitoring for new podcast episodes

---
*Automated test from GitHub Actions*
"""
    
    msg.attach(MIMEText(test_content, 'plain'))
    
    try:
        print("🔐 Connecting to Gmail SMTP...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        print("📤 Sending test email...")
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"✅ Test email sent successfully to {recipient_email}")
        print("   Check your email (and spam folder) for the test message")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_email()
    if success:
        print("\n🎉 Email system is working!")
    else:
        print("\n💥 Email system needs debugging")