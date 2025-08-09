"""
Report Generator for RSS Intelligence System
Generates structured daily reports from analyzed articles
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates structured reports from analyzed articles"""
    
    def __init__(self, config):
        self.config = config
    
    async def generate_report(self, articles) -> Dict[str, Any]:
        """Generate comprehensive daily report"""
        if not articles:
            return self._generate_empty_report()
        
        logger.info(f"📊 Generating report for {len(articles)} articles")
        
        # Group articles by source
        articles_by_source = self._group_by_source(articles)
        
        # Extract key insights
        key_insights = self._extract_key_insights(articles)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(articles)
        
        # Create report structure
        report = {
            'date': datetime.now().isoformat(),
            'total_articles': len(articles),
            'sources_count': len(articles_by_source),
            'executive_summary': executive_summary,
            'key_insights': key_insights,
            'articles_by_source': articles_by_source,
            'full_articles': [article.to_dict() for article in articles]
        }
        
        return report
    
    def _generate_empty_report(self) -> Dict[str, Any]:
        """Generate report when no articles are found"""
        return {
            'date': datetime.now().isoformat(),
            'total_articles': 0,
            'sources_count': 0,
            'executive_summary': "No new articles found today. All monitored sources have been checked.",
            'key_insights': [],
            'articles_by_source': {},
            'full_articles': []
        }
    
    def _group_by_source(self, articles) -> Dict[str, List[Dict]]:
        """Group articles by their RSS source"""
        grouped = defaultdict(list)
        
        for article in articles:
            article_summary = {
                'title': article.title,
                'url': article.url,
                'published': article.published.strftime('%Y-%m-%d %H:%M'),
                'analysis': article.analysis,
                'content_preview': article.content[:200] + "..." if len(article.content) > 200 else article.content
            }
            grouped[article.source].append(article_summary)
        
        # Sort articles within each source by publication date (newest first)
        for source in grouped:
            grouped[source].sort(key=lambda x: x['published'], reverse=True)
        
        return dict(grouped)
    
    def _extract_key_insights(self, articles) -> List[str]:
        """Extract key insights from all analyses"""
        insights = []
        
        # Collect all analyses
        all_analyses = [article.analysis for article in articles if article.analysis]
        
        if not all_analyses:
            return ["No analyses available for insight extraction."]
        
        # Look for common themes and important keywords
        insight_keywords = {
            'investment': ['investment', 'funding', 'capital', 'financing', 'IPO', 'acquisition', 'merger'],
            'infrastructure': ['infrastructure', 'construction', 'development', 'project', 'facility'],
            'technology': ['AI', 'artificial intelligence', 'technology', 'innovation', 'digital', 'automation'],
            'market': ['market', 'trend', 'growth', 'decline', 'opportunity', 'risk'],
            'regulation': ['regulation', 'policy', 'government', 'regulatory', 'compliance', 'law'],
            'energy': ['energy', 'renewable', 'power', 'electricity', 'grid', 'carbon', 'sustainability']
        }
        
        # Count keyword occurrences
        theme_counts = defaultdict(int)
        theme_examples = defaultdict(list)
        
        for analysis in all_analyses:
            analysis_lower = analysis.lower()
            for theme, keywords in insight_keywords.items():
                for keyword in keywords:
                    if keyword in analysis_lower:
                        theme_counts[theme] += 1
                        # Extract sentence containing the keyword
                        sentences = analysis.split('.')
                        for sentence in sentences:
                            if keyword.lower() in sentence.lower():
                                theme_examples[theme].append(sentence.strip())
                                break
                        break
        
        # Generate insights for top themes
        for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 2:  # Only include themes mentioned in multiple articles
                example = theme_examples[theme][0] if theme_examples[theme] else ""
                insights.append(f"**{theme.title()} Focus**: Mentioned in {count} articles. {example}")
        
        # Add general insights
        if len(articles) > 5:
            insights.append(f"**High Activity Day**: {len(articles)} articles analyzed across {len(set(a.source for a in articles))} sources")
        
        # Look for urgent/breaking news indicators
        urgent_keywords = ['breaking', 'urgent', 'alert', 'crisis', 'emergency', 'immediately']
        urgent_articles = []
        for article in articles:
            content_lower = (article.title + " " + article.analysis).lower()
            if any(keyword in content_lower for keyword in urgent_keywords):
                urgent_articles.append(article.title)
        
        if urgent_articles:
            insights.append(f"**Urgent Attention**: {len(urgent_articles)} articles may require immediate attention")
        
        return insights[:5]  # Return top 5 insights
    
    def _generate_executive_summary(self, articles) -> str:
        """Generate executive summary of the day's intelligence"""
        if not articles:
            return "No new articles found today."
        
        sources = set(article.source for article in articles)
        
        summary_parts = [
            f"Daily intelligence briefing for {datetime.now().strftime('%B %d, %Y')}.",
            f"Analyzed {len(articles)} articles from {len(sources)} sources."
        ]
        
        # Identify top sources by article count
        source_counts = defaultdict(int)
        for article in articles:
            source_counts[article.source] += 1
        
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_sources:
            top_source_text = ", ".join([f"{source} ({count})" for source, count in top_sources])
            summary_parts.append(f"Most active sources: {top_source_text}.")
        
        # Look for high-priority keywords in analyses
        priority_keywords = ['opportunity', 'risk', 'investment', 'urgent', 'breaking', 'significant', 'major']
        priority_count = 0
        
        for article in articles:
            content_lower = article.analysis.lower()
            if any(keyword in content_lower for keyword in priority_keywords):
                priority_count += 1
        
        if priority_count > 0:
            summary_parts.append(f"{priority_count} articles contain high-priority investment or market signals.")
        
        # Time-based summary
        recent_hours = sum(1 for article in articles 
                          if (datetime.now() - article.published).total_seconds() < 6*3600)  # Last 6 hours
        if recent_hours > len(articles) * 0.3:  # If more than 30% are very recent
            summary_parts.append("Significant news activity in the last 6 hours.")
        
        return " ".join(summary_parts)
    
    def generate_email_body(self, report: Dict[str, Any]) -> str:
        """Generate email body from report"""
        if report['total_articles'] == 0:
            return self._generate_empty_email_body()
        
        email_body = f"""📊 DAILY INTELLIGENCE BRIEFING
{datetime.now().strftime('%A, %B %d, %Y')}

{report['executive_summary']}

🔥 KEY INSIGHTS:
"""
        
        for i, insight in enumerate(report['key_insights'], 1):
            email_body += f"{i}. {insight}\n"
        
        email_body += f"""

📑 ARTICLES BY SOURCE:
{'='*50}

"""
        
        for source, articles in report['articles_by_source'].items():
            email_body += f"📰 {source.upper()} ({len(articles)} articles)\n"
            email_body += "-" * 40 + "\n"
            
            for article in articles:
                email_body += f"📄 {article['title']}\n"
                email_body += f"   🕒 {article['published']}\n"
                email_body += f"   🔗 {article['url']}\n"
                email_body += f"   📊 ANALYSIS: {article['analysis'][:150]}...\n\n"
            
            email_body += "\n"
        
        email_body += f"""
📈 SUMMARY STATISTICS:
• Total Articles Analyzed: {report['total_articles']}
• Sources Monitored: {report['sources_count']}
• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 Generated by RSS Intelligence System
"""
        
        return email_body
    
    def _generate_empty_email_body(self) -> str:
        """Generate email body when no articles found"""
        return f"""📊 DAILY INTELLIGENCE BRIEFING
{datetime.now().strftime('%A, %B %d, %Y')}

📧 STATUS: No new articles found today

✅ SYSTEM STATUS: All RSS feeds monitored successfully
📊 Sources Checked: {len(self.config.rss_feeds)} RSS feeds
🕒 Last Check: {datetime.now().strftime('%H:%M:%S')}

All monitored sources are up to date. The system will continue monitoring for new content.

🤖 Generated by RSS Intelligence System
"""
    
    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown report for Google Drive storage"""
        if report['total_articles'] == 0:
            return self._generate_empty_markdown_report()
        
        md_content = f"""# Daily Intelligence Report
**Date:** {datetime.now().strftime('%A, %B %d, %Y')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

{report['executive_summary']}

---

## Key Insights

"""
        
        for i, insight in enumerate(report['key_insights'], 1):
            md_content += f"{i}. {insight}\n"
        
        md_content += f"""
---

## Articles by Source

"""
        
        for source, articles in report['articles_by_source'].items():
            md_content += f"### 📰 {source} ({len(articles)} articles)\n\n"
            
            for article in articles:
                md_content += f"#### {article['title']}\n"
                md_content += f"**Published:** {article['published']}  \n"
                md_content += f"**URL:** [{article['url']}]({article['url']})  \n\n"
                md_content += f"**Analysis:**\n{article['analysis']}\n\n"
                md_content += f"**Content Preview:**\n{article['content_preview']}\n\n"
                md_content += "---\n\n"
        
        md_content += f"""
## Summary Statistics

- **Total Articles Analyzed:** {report['total_articles']}
- **Sources Monitored:** {report['sources_count']}
- **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Generated by RSS Intelligence System*
"""
        
        return md_content
    
    def _generate_empty_markdown_report(self) -> str:
        """Generate markdown report when no articles found"""
        return f"""# Daily Intelligence Report
**Date:** {datetime.now().strftime('%A, %B %d, %Y')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Status

📧 **No new articles found today**

✅ **System Status:** All RSS feeds monitored successfully  
📊 **Sources Checked:** {len(self.config.rss_feeds)} RSS feeds  
🕒 **Last Check:** {datetime.now().strftime('%H:%M:%S')}

All monitored sources are up to date. The system will continue monitoring for new content.

---
*Generated by RSS Intelligence System*
"""