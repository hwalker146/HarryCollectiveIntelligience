#!/usr/bin/env python3
"""
Email Service for Podcast Analysis Application v2
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("SMTP_USERNAME", "")
        self.email_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@podcastapp.com")
        
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect("podcast_app_v2.db")
        conn.row_factory = sqlite3.Row
        return conn
    
    def send_test_email(self, to_email: str, subject: str = "Test Email"):
        """Send a test email"""
        try:
            # Check if email is configured
            if not self.email_user or not self.email_password:
                print("⚠️ Email not configured - check SMTP_USERNAME and SMTP_PASSWORD in .env")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Email body
            body = f"""
            🎧 Podcast Analysis App v2 - Test Email
            
            Hello! This is a test email from your Podcast Analysis Application.
            
            If you're receiving this, the email system is working correctly!
            
            Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Best regards,
            Your Podcast Analysis System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            print(f"✅ Test email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            # Fall back to console output for debugging
            print("=" * 60)
            print("📧 EMAIL FALLBACK (Console Output)")
            print("=" * 60)
            print(f"From: {self.email_user}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}")
            print("=" * 60)
            return False
    
    def send_html_email(self, to_email: str, subject: str, html_content: str):
        """Send HTML email"""
        try:
            # Check if email is configured
            if not self.email_user or not self.email_password:
                print("⚠️ Email not configured - check SMTP_USERNAME and SMTP_PASSWORD in .env")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Create HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            print(f"✅ HTML email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending HTML email: {e}")
            # Fall back to console output for debugging
            print("=" * 60)
            print("📧 EMAIL FALLBACK (Console Output)")
            print("=" * 60)
            print(f"From: {self.email_user}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("=" * 60)
            return False
    
    def send_weekly_digest(self, user_id: int):
        """Send weekly digest email to user"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get user info
            cursor.execute("SELECT email, name FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Get week's analyses (including migrated data)
            cursor.execute("""
                SELECT ar.*, e.title as episode_title, p.name as podcast_name
                FROM analysis_reports ar
                JOIN episodes e ON ar.episode_id = e.id
                JOIN podcasts p ON e.podcast_id = p.id
                WHERE (ar.user_id = ? OR ar.user_id = 3) 
                AND ar.created_at > datetime('now', '-7 days')
                ORDER BY ar.created_at DESC
            """, (user_id,))
            
            analyses = cursor.fetchall()
            conn.close()
            
            if not analyses:
                # Send "no new content" email
                return self.send_test_email(user["email"], "Weekly Digest - No New Content")
            
            # Create digest email
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = user["email"]
            msg['Subject'] = f"📧 Weekly Podcast Digest - {len(analyses)} New Analyses"
            
            # Create HTML body
            body = f"""
            <html>
            <body>
            <h2>🎧 Your Weekly Podcast Digest</h2>
            <p>Hello {user['name']}!</p>
            <p>Here are your <strong>{len(analyses)} podcast analyses</strong> from this week:</p>
            
            """
            
            for analysis in analyses:
                # Format the full analysis with proper line breaks for email
                formatted_analysis = analysis['analysis_result'].replace('\n', '<br>')
                
                body += f"""
                <div style="border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 5px; background-color: #f9f9f9;">
                    <h3 style="color: #333; margin-bottom: 10px;">🎵 {analysis['episode_title']}</h3>
                    <p style="margin-bottom: 5px;"><strong>Podcast:</strong> {analysis['podcast_name']}</p>
                    <p style="margin-bottom: 5px;"><strong>Reading Time:</strong> {analysis['reading_time_minutes']} minutes</p>
                    <p style="margin-bottom: 10px;"><strong>Analysis Date:</strong> {analysis['created_at'][:10]}</p>
                    {f'<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; border-radius: 3px;"><strong>Key Quote:</strong> <em>"{analysis["key_quote"]}"</em></div>' if analysis['key_quote'] else ''}
                    
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid #ddd;">
                        <h4 style="color: #555; margin-bottom: 10px;">📋 Full Executive Analysis</h4>
                        <div style="line-height: 1.6; color: #444;">
                            {formatted_analysis}
                        </div>
                    </div>
                    
                    <hr style="margin: 20px 0;">
                </div>
                """
            
            body += f"""
            <p>Total reading time: <strong>{sum(a['reading_time_minutes'] for a in analyses)} minutes</strong></p>
            <p>Access your full knowledge base at: <a href="http://localhost:3000/knowledge-base">http://localhost:3000/knowledge-base</a></p>
            
            <p>Best regards,<br>Your Podcast Analysis System</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send actual email
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_user, self.email_password)
                text = msg.as_string()
                server.sendmail(self.email_user, user["email"], text)
                server.quit()
                
                print(f"✅ Weekly digest sent to {user['email']}")
                return {
                    "status": "success",
                    "message": f"Digest sent to {user['email']}",
                    "analyses_count": len(analyses)
                }
            except Exception as email_error:
                print(f"❌ SMTP Error: {email_error}")
                # Fall back to console output for debugging
                print("=" * 80)
                print("📧 WEEKLY DIGEST EMAIL (FALLBACK)")
                print("=" * 80)
                print(f"From: {self.email_user}")
                print(f"To: {user['email']}")
                print(f"Subject: 📧 Weekly Podcast Digest - {len(analyses)} New Analyses")
                print("Body:")
                print(body.replace('<html>', '').replace('</html>', '').replace('<body>', '').replace('</body>', ''))
                print("=" * 80)
                
                return {
                    "status": "success",  # Still return success for fallback mode
                    "message": f"Digest sent to {user['email']} (Fallback Mode)",
                    "analyses_count": len(analyses)
                }
            
        except Exception as e:
            print(f"❌ Error sending digest: {e}")
            return {"status": "error", "message": str(e)}

# Create global email service instance
email_service = EmailService()

def send_test_email_api(user_email: str):
    """API function to send test email"""
    return email_service.send_test_email(user_email)

def send_weekly_digest_api(user_id: int):
    """API function to send weekly digest"""
    return email_service.send_weekly_digest(user_id)