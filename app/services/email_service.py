"""
Enhanced email service with knowledge base highlights and improved templates
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
from datetime import datetime, timedelta
from jinja2 import Template
from sqlalchemy.orm import Session

from app.models import User, AnalysisReport, KnowledgeBaseEntry, Episode, Podcast
from app.core.config import settings
from app.services.user_service import UserService


class EmailService:
    def __init__(self):
        self.smtp_config = {
            'host': settings.smtp_host,
            'port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'from_email': settings.from_email,
            'use_tls': True
        }
        self.user_service = UserService()
    
    def create_weekly_digest_content(self, db: Session, user: User) -> Dict[str, Any]:
        """Create weekly digest content with knowledge base highlights"""
        # Get analysis reports from the last week
        week_ago = datetime.now() - timedelta(days=7)
        
        reports = db.query(AnalysisReport).join(Episode).join(Podcast).filter(
            AnalysisReport.user_id == user.id,
            AnalysisReport.created_at >= week_ago
        ).order_by(AnalysisReport.created_at.desc()).all()
        
        if not reports:
            return None
        
        # Get knowledge base entries from the last week
        kb_entries = db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.user_id == user.id,
            KnowledgeBaseEntry.created_at >= week_ago
        ).all()
        
        # Organize reports by category
        categorized_reports = {}
        total_reading_time = 0
        best_quotes = []
        
        for report in reports:
            episode = report.episode
            podcast = episode.podcast
            
            # Find knowledge base entry for this report
            kb_entry = next((kb for kb in kb_entries if kb.analysis_report_id == report.id), None)
            category = kb_entry.podcast_category if kb_entry else "Uncategorized"
            
            if category not in categorized_reports:
                categorized_reports[category] = []
            
            report_data = {
                "report": report,
                "episode": episode,
                "podcast": podcast,
                "kb_entry": kb_entry,
                "reading_time": report.reading_time_minutes or 0,
                "key_quote": report.key_quote
            }
            
            categorized_reports[category].append(report_data)
            total_reading_time += report.reading_time_minutes or 0
            
            # Collect best quotes
            if report.key_quote:
                best_quotes.append({
                    "quote": report.key_quote,
                    "podcast": podcast.name,
                    "episode": episode.title
                })
        
        # Sort quotes by length/quality (simple heuristic)
        best_quotes.sort(key=lambda x: len(x["quote"]), reverse=True)
        
        return {
            "user": user,
            "categorized_reports": categorized_reports,
            "total_reports": len(reports),
            "total_reading_time": total_reading_time,
            "best_quotes": best_quotes[:3],  # Top 3 quotes
            "kb_entries_count": len(kb_entries),
            "week_start": week_ago.strftime("%B %d"),
            "week_end": datetime.now().strftime("%B %d, %Y")
        }
    
    def render_weekly_digest_html(self, content: Dict[str, Any]) -> str:
        """Render HTML email template for weekly digest"""
        html_template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Podcast Digest</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #212529;
        }
        .email-container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 300;
        }
        .stats-summary {
            background-color: #f8f9fa;
            padding: 25px 30px;
            margin: 0;
            border-bottom: 1px solid #dee2e6;
        }
        .stats-grid {
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        .stat-item {
            flex: 1;
        }
        .stat-number {
            font-size: 24px;
            font-weight: 600;
            color: #495057;
            display: block;
        }
        .stat-label {
            font-size: 13px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .quotes-section {
            background-color: #fff3cd;
            padding: 30px;
            margin: 0;
            border-left: 4px solid #ffc107;
        }
        .quote-item {
            margin-bottom: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 8px;
            border-left: 3px solid #ffc107;
        }
        .quote-text {
            font-style: italic;
            font-size: 16px;
            color: #495057;
            margin-bottom: 10px;
        }
        .quote-source {
            font-size: 14px;
            color: #6c757d;
        }
        .category-section {
            padding: 30px;
            border-bottom: 1px solid #e9ecef;
        }
        .category-header {
            font-size: 20px;
            font-weight: 600;
            color: #495057;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }
        .report-item {
            margin-bottom: 25px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .report-title {
            font-size: 18px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 8px;
        }
        .report-meta {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 15px;
        }
        .reading-time {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .report-preview {
            color: #495057;
            line-height: 1.7;
        }
        .kb-highlight {
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
            border-left: 3px solid #007bff;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>📚 Your Weekly Knowledge Digest</h1>
            <p>{{ content.week_start }} - {{ content.week_end }}</p>
            <p>Hello {{ content.user.name or content.user.email }}!</p>
        </div>
        
        <div class="stats-summary">
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">{{ content.total_reports }}</span>
                    <span class="stat-label">New Analyses</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{{ content.total_reading_time }}</span>
                    <span class="stat-label">Minutes Reading</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{{ content.kb_entries_count }}</span>
                    <span class="stat-label">Knowledge Base Entries</span>
                </div>
            </div>
        </div>
        
        {% if content.best_quotes %}
        <div class="quotes-section">
            <h2 style="margin: 0 0 20px 0; font-size: 22px; color: #495057;">💡 Week's Best Insights</h2>
            {% for quote in content.best_quotes %}
            <div class="quote-item">
                <div class="quote-text">"{{ quote.quote }}"</div>
                <div class="quote-source">— {{ quote.podcast }}: {{ quote.episode[:50] }}{% if quote.episode|length > 50 %}...{% endif %}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% for category, reports in content.categorized_reports.items() %}
        <div class="category-section">
            <div class="category-header">
                📂 {{ category }}
            </div>
            
            {% for report_data in reports %}
            <div class="report-item">
                <div class="report-title">{{ report_data.episode.title }}</div>
                <div class="report-meta">
                    <strong>{{ report_data.podcast.name }}</strong> • 
                    {{ report_data.episode.published_date.strftime('%B %d') if report_data.episode.published_date else 'Unknown Date' }} • 
                    <span class="reading-time">{{ report_data.reading_time }} min read</span>
                </div>
                
                <div class="report-preview">
                    {{ report_data.report.analysis_result[:300] }}{% if report_data.report.analysis_result|length > 300 %}...{% endif %}
                </div>
                
                {% if report_data.kb_entry and report_data.kb_entry.personal_notes %}
                <div class="kb-highlight">
                    <strong>📝 Your Notes:</strong> {{ report_data.kb_entry.personal_notes[:200] }}{% if report_data.kb_entry.personal_notes|length > 200 %}...{% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        
        <div class="footer">
            <p><strong>🎧 Personal Podcast Knowledge System</strong></p>
            <p>Building your learning repository, one episode at a time</p>
            <p style="margin-top: 15px; font-size: 12px; opacity: 0.7;">
                <a href="{{ unsubscribe_link }}" style="color: #6c757d;">Unsubscribe</a> from weekly digests
            </p>
        </div>
    </div>
</body>
</html>
        ''')
        
        return html_template.render(content=content, unsubscribe_link="#")  # TODO: Implement unsubscribe
    
    def render_weekly_digest_text(self, content: Dict[str, Any]) -> str:
        """Render plain text email template for weekly digest"""
        text_template = Template('''
📚 YOUR WEEKLY KNOWLEDGE DIGEST
{{ "=" * 50 }}

Hello {{ content.user.name or content.user.email }}!

Week of {{ content.week_start }} - {{ content.week_end }}

📊 WEEK SUMMARY:
• {{ content.total_reports }} new analyses
• {{ content.total_reading_time }} minutes of reading
• {{ content.kb_entries_count }} knowledge base entries

{% if content.best_quotes %}
💡 WEEK'S BEST INSIGHTS:
{{ "-" * 30 }}
{% for quote in content.best_quotes %}

"{{ quote.quote }}"
— {{ quote.podcast }}: {{ quote.episode[:50] }}{% if quote.episode|length > 50 %}...{% endif %}
{% endfor %}
{% endif %}

📂 YOUR LEARNING BY CATEGORY:
{{ "=" * 50 }}

{% for category, reports in content.categorized_reports.items() %}

{{ category.upper() }}
{{ "-" * 30 }}
{% for report_data in reports %}

📰 {{ report_data.episode.title }}
🎧 {{ report_data.podcast.name }} • {{ report_data.episode.published_date.strftime('%B %d') if report_data.episode.published_date else 'Unknown Date' }} • {{ report_data.reading_time }} min read

{{ report_data.report.analysis_result[:200] }}...
{% if report_data.kb_entry and report_data.kb_entry.personal_notes %}

📝 Your Notes: {{ report_data.kb_entry.personal_notes[:100] }}...
{% endif %}

{% endfor %}
{% endfor %}

{{ "=" * 50 }}
🎧 Personal Podcast Knowledge System
Building your learning repository, one episode at a time
        ''')
        
        return text_template.render(content=content)
    
    def send_weekly_digest(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Send weekly digest to user"""
        # Get user
        user = self.user_service.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return {"success": False, "error": "User not found or inactive"}
        
        # Create digest content
        content = self.create_weekly_digest_content(db, user)
        if not content:
            return {"success": False, "error": "No content available for digest"}
        
        # Render email templates
        html_content = self.render_weekly_digest_html(content)
        text_content = self.render_weekly_digest_text(content)
        
        # Create subject
        subject = f"📚 Your Weekly Podcast Digest - {content['total_reports']} New Insights"
        
        # Send email
        try:
            result = self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Log email
            self.user_service.log_email_sent(
                db=db,
                user_id=user_id,
                email_type="weekly_report",
                subject=subject,
                content_preview=text_content[:200],
                status="sent" if result else "failed"
            )
            
            return {"success": result, "total_reports": content['total_reports']}
            
        except Exception as e:
            # Log failed email
            self.user_service.log_email_sent(
                db=db,
                user_id=user_id,
                email_type="weekly_report",
                subject=subject,
                content_preview="Failed to send",
                status="failed"
            )
            
            return {"success": False, "error": str(e)}
    
    def send_welcome_email(self, db: Session, user_id: int) -> bool:
        """Send welcome email to new user"""
        user = self.user_service.get_user_by_id(db, user_id)
        if not user:
            return False
        
        subject = "Welcome to Your Personal Podcast Knowledge System! 🎧"
        
        html_content = f"""
        <h1>Welcome to the future of podcast learning!</h1>
        <p>Hi {user.name or user.email.split('@')[0]},</p>
        <p>You're all set up with your personal podcast analysis and knowledge management system.</p>
        <p>Here's what you can do:</p>
        <ul>
            <li>📚 Subscribe to podcasts and get AI-powered analysis</li>
            <li>🧠 Build your personal knowledge base with insights and notes</li>
            <li>📧 Receive weekly digests with your best learnings</li>
            <li>🔍 Search and organize your podcast insights</li>
        </ul>
        <p>Ready to start learning? <a href="{settings.base_url}/dashboard">Visit your dashboard</a></p>
        """
        
        text_content = f"""
        Welcome to Your Personal Podcast Knowledge System!
        
        Hi {user.name or user.email.split('@')[0]},
        
        You're all set up with your personal podcast analysis and knowledge management system.
        
        Here's what you can do:
        • Subscribe to podcasts and get AI-powered analysis
        • Build your personal knowledge base with insights and notes  
        • Receive weekly digests with your best learnings
        • Search and organize your podcast insights
        
        Ready to start learning? Visit: {settings.base_url}/dashboard
        """
        
        try:
            result = self._send_email(user.email, subject, html_content, text_content)
            
            # Log email
            self.user_service.log_email_sent(
                db=db,
                user_id=user_id,
                email_type="signup",
                subject=subject,
                content_preview=text_content[:200],
                status="sent" if result else "failed"
            )
            
            return result
            
        except Exception as e:
            return False
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Attach text and HTML versions
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            
            if self.smtp_config['use_tls']:
                server.starttls()
            
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_weekly_digests_to_all_users(self, db: Session) -> Dict[str, Any]:
        """Send weekly digests to all active users"""
        users = self.user_service.get_active_users(db)
        
        results = {
            "total_users": len(users),
            "sent_successfully": 0,
            "failed": 0,
            "no_content": 0,
            "errors": []
        }
        
        for user in users:
            try:
                result = self.send_weekly_digest(db, user.id)
                if result["success"]:
                    results["sent_successfully"] += 1
                elif "No content available" in result.get("error", ""):
                    results["no_content"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"User {user.email}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"User {user.email}: {str(e)}")
        
        return results