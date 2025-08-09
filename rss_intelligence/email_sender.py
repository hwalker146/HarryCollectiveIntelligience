"""
Email Sender for RSS Intelligence System
Handles sending daily reports via email
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EmailSender:
    """Sends email reports"""
    
    def __init__(self, config):
        self.config = config
        self.smtp_server = config.email_settings['smtp_server']
        self.smtp_port = config.email_settings['smtp_port']
        self.from_email = config.email_settings['from_email']
        self.from_password = config.email_settings['from_password']
        self.to_email = config.email_settings['to_email']
    
    async def send_daily_report(self, report: Dict[str, Any], articles: List) -> bool:
        """Send daily intelligence report via email"""
        try:
            # Import report generator for email formatting
            from report_generator import ReportGenerator
            report_gen = ReportGenerator(self.config)
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            
            # Subject line with article count
            if report['total_articles'] > 0:
                subject = f"📊 Intelligence Briefing: {report['total_articles']} Articles - {datetime.now().strftime('%Y-%m-%d')}"
            else:
                subject = f"📊 Intelligence Briefing: No New Articles - {datetime.now().strftime('%Y-%m-%d')}"
            
            msg['Subject'] = subject
            
            # Generate email body
            email_body = report_gen.generate_email_body(report)
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.from_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Daily report email sent to {self.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send daily report email: {e}")
            return False
    
    async def send_status_email(self, status_message: str) -> bool:
        """Send status email (e.g., no articles found)"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"📊 RSS Intelligence Status - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""🤖 RSS INTELLIGENCE SYSTEM STATUS

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 STATUS: {status_message}

✅ SYSTEM HEALTH: All RSS feeds monitored successfully
📊 Sources Monitored: {len(self.config.rss_feeds)} RSS feeds
🕒 Next Check: Tomorrow at scheduled time

The system is operating normally and will continue monitoring for new articles.

🔗 RSS FEEDS MONITORED:
"""
            
            # Add list of monitored feeds
            for i, (feed_name, feed_url) in enumerate(self.config.rss_feeds.items(), 1):
                body += f"{i:2}. {feed_name}: {feed_url}\n"
            
            body += f"""

🤖 Generated automatically by RSS Intelligence System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.from_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Status email sent to {self.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send status email: {e}")
            return False
    
    async def send_error_email(self, error_message: str) -> bool:
        """Send error notification email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"❌ RSS Intelligence System Error - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""🚨 RSS INTELLIGENCE SYSTEM ERROR

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

❌ ERROR: {error_message}

🔧 TROUBLESHOOTING STEPS:
1. Check internet connection
2. Verify RSS feed URLs are accessible
3. Confirm API keys are valid and have credits
4. Check system logs for detailed error information

📊 SYSTEM CONFIGURATION:
• RSS Feeds: {len(self.config.rss_feeds)} configured
• AI Provider: {self.config.ai_settings['provider']}
• Email: {self.from_email} → {self.to_email}

The system will retry on the next scheduled run.

🤖 Generated automatically by RSS Intelligence System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.from_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Error email sent to {self.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send error email: {e}")
            return False
    
    async def send_test_email(self) -> bool:
        """Send test email to verify email configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"🧪 RSS Intelligence Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = f"""🧪 RSS INTELLIGENCE SYSTEM TEST

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ EMAIL CONFIGURATION TEST SUCCESSFUL!

📊 SYSTEM CONFIGURATION:
• RSS Feeds: {len(self.config.rss_feeds)} configured
• AI Provider: {self.config.ai_settings['provider']}
• From: {self.from_email}
• To: {self.to_email}
• SMTP: {self.smtp_server}:{self.smtp_port}

🎯 WHAT'S NEXT:
The system is ready to send daily intelligence briefings.
You should receive your first automated report during the next scheduled run.

🤖 Generated by RSS Intelligence System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.from_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Test email sent successfully to {self.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send test email: {e}")
            return False