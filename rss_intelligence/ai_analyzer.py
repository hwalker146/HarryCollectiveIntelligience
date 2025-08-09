"""
AI Analyzer for RSS Intelligence System
Handles article analysis using Claude or OpenAI APIs
"""
import asyncio
import logging
from typing import Optional
import aiohttp
import json

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """Analyzes articles using AI APIs"""
    
    def __init__(self, config):
        self.config = config
        self.provider = config.ai_settings['provider']
        self.prompt_template = config.analysis_prompt
        
        if self.provider == 'claude':
            self.api_key = config.ai_settings['claude_api_key']
            self.model = config.ai_settings.get('model', 'claude-3-5-sonnet-20241022')
            self.api_url = 'https://api.anthropic.com/v1/messages'
        elif self.provider == 'openai':
            self.api_key = config.ai_settings['openai_api_key']
            self.model = config.ai_settings.get('model', 'gpt-4o')
            self.api_url = 'https://api.openai.com/v1/chat/completions'
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def analyze_article(self, article_content: str) -> str:
        """Analyze article content using AI"""
        if not article_content or len(article_content.strip()) < 50:
            return "Content too short for analysis"
        
        try:
            if self.provider == 'claude':
                return await self._analyze_with_claude(article_content)
            elif self.provider == 'openai':
                return await self._analyze_with_openai(article_content)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def _analyze_with_claude(self, article_content: str) -> str:
        """Analyze article using Claude API"""
        prompt = self.prompt_template.format(article_content=article_content)
        
        headers = {
            'x-api-key': self.api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': self.model,
            'max_tokens': 1000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Claude API error {response.status}: {error_text}")
                
                result = await response.json()
                
                if 'content' in result and result['content']:
                    return result['content'][0]['text']
                else:
                    raise Exception(f"Unexpected Claude response format: {result}")
    
    async def _analyze_with_openai(self, article_content: str) -> str:
        """Analyze article using OpenAI API"""
        prompt = self.prompt_template.format(article_content=article_content)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert financial and infrastructure analyst.'
                },
                {
                    'role': 'user', 
                    'content': prompt
                }
            ],
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                
                result = await response.json()
                
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"Unexpected OpenAI response format: {result}")
    
    async def batch_analyze(self, articles_content: list) -> list:
        """Analyze multiple articles in parallel with rate limiting"""
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def analyze_with_limit(content):
            async with semaphore:
                await asyncio.sleep(0.5)  # Rate limiting
                return await self.analyze_article(content)
        
        tasks = [analyze_with_limit(content) for content in articles_content]
        return await asyncio.gather(*tasks, return_exceptions=True)