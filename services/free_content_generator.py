import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from src.services.free_ai_services import free_ai
from src.models.content import Content
from src.models.user import User

logger = logging.getLogger(__name__)

class FreeContentGenerator:
    """Comprehensive free content generation service"""
    
    def __init__(self):
        self.content_types = {
            'social_post': {
                'platforms': ['facebook', 'instagram', 'twitter', 'linkedin'],
                'max_length': {'facebook': 2000, 'instagram': 2200, 'twitter': 280, 'linkedin': 3000},
                'hashtag_count': {'facebook': 5, 'instagram': 30, 'twitter': 3, 'linkedin': 5}
            },
            'blog_post': {
                'min_length': 500,
                'max_length': 3000,
                'sections': ['introduction', 'main_content', 'conclusion'],
                'seo_optimized': True
            },
            'product_description': {
                'min_length': 100,
                'max_length': 500,
                'features': ['benefits', 'specifications', 'use_cases']
            },
            'email_campaign': {
                'types': ['welcome', 'promotional', 'newsletter', 'follow_up'],
                'max_length': 1000,
                'personalized': True
            },
            'ad_copy': {
                'platforms': ['google_ads', 'facebook_ads', 'instagram_ads'],
                'max_length': {'google_ads': 90, 'facebook_ads': 125, 'instagram_ads': 125},
                'cta_required': True
            }
        }
        
        self.writing_styles = {
            'professional': 'Professional and formal tone',
            'casual': 'Casual and friendly tone',
            'persuasive': 'Persuasive and compelling tone',
            'informative': 'Informative and educational tone',
            'creative': 'Creative and engaging tone',
            'humorous': 'Light and humorous tone',
            'urgent': 'Urgent and action-oriented tone',
            'empathetic': 'Empathetic and understanding tone'
        }
        
        self.languages = {
            'ar': 'Arabic',
            'en': 'English',
            'fr': 'French',
            'es': 'Spanish',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese'
        }
    
    async def generate_social_post(self, prompt: str, platform: str, 
                                  style: str = 'engaging', language: str = 'en',
                                  include_hashtags: bool = True, 
                                  include_emojis: bool = True) -> Dict[str, Any]:
        """Generate social media post"""
        try:
            if platform not in self.content_types['social_post']['platforms']:
                return {
                    'success': False,
                    'error': f'Platform {platform} not supported'
                }
            
            max_length = self.content_types['social_post']['max_length'][platform]
            hashtag_count = self.content_types['social_post']['hashtag_count'][platform]
            
            # Create enhanced prompt
            enhanced_prompt = f"""
            Create a {style} social media post for {platform} in {language}.
            Topic: {prompt}
            
            Requirements:
            - Maximum {max_length} characters
            - {self.writing_styles.get(style, 'engaging')}
            - Platform-specific best practices for {platform}
            {'- Include relevant emojis' if include_emojis else '- No emojis'}
            {'- Include ' + str(hashtag_count) + ' relevant hashtags' if include_hashtags else '- No hashtags'}
            
            Make it engaging and optimized for {platform}.
            """
            
            result = await free_ai.generate_text(
                prompt=enhanced_prompt,
                language=language,
                style=style,
                max_length=max_length
            )
            
            if result['success']:
                post_content = result['text']
                
                # Extract hashtags if included
                hashtags = []
                if include_hashtags:
                    hashtags = self._extract_hashtags(post_content)
                
                # Generate additional hashtags if needed
                if include_hashtags and len(hashtags) < hashtag_count:
                    additional_hashtags = await self._generate_hashtags(
                        prompt, platform, hashtag_count - len(hashtags), language
                    )
                    hashtags.extend(additional_hashtags)
                
                return {
                    'success': True,
                    'content': post_content,
                    'hashtags': hashtags,
                    'platform': platform,
                    'character_count': len(post_content),
                    'language': language,
                    'style': style,
                    'service_used': result.get('service')
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"Social post generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_blog_post(self, topic: str, target_audience: str,
                                keywords: List[str], language: str = 'en',
                                length: str = 'medium', style: str = 'informative') -> Dict[str, Any]:
        """Generate SEO-optimized blog post"""
        try:
            # Determine length
            length_mapping = {
                'short': 500,
                'medium': 1500,
                'long': 3000
            }
            target_length = length_mapping.get(length, 1500)
            
            # Create comprehensive prompt
            enhanced_prompt = f"""
            Write a comprehensive blog post in {language} about: {topic}
            
            Target audience: {target_audience}
            SEO Keywords to include: {', '.join(keywords)}
            Target length: {target_length} words
            Writing style: {self.writing_styles.get(style, 'informative')}
            
            Structure:
            1. Compelling headline
            2. Introduction (hook the reader)
            3. Main content (detailed, valuable information)
            4. Conclusion (call to action)
            
            Requirements:
            - SEO optimized with natural keyword integration
            - Engaging and valuable content
            - Clear structure with subheadings
            - Actionable insights
            - Professional formatting
            """
            
            result = await free_ai.generate_text(
                prompt=enhanced_prompt,
                language=language,
                style=style,
                max_length=target_length + 500  # Allow some buffer
            )
            
            if result['success']:
                blog_content = result['text']
                
                # Extract title and sections
                sections = self._parse_blog_sections(blog_content)
                
                # Generate meta description
                meta_description = await self._generate_meta_description(
                    topic, keywords, language
                )
                
                return {
                    'success': True,
                    'title': sections.get('title', topic),
                    'content': blog_content,
                    'sections': sections,
                    'meta_description': meta_description,
                    'keywords': keywords,
                    'word_count': len(blog_content.split()),
                    'language': language,
                    'style': style,
                    'service_used': result.get('service')
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"Blog post generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_product_description(self, product_name: str, features: List[str],
                                          benefits: List[str], target_audience: str,
                                          language: str = 'en', style: str = 'persuasive') -> Dict[str, Any]:
        """Generate compelling product description"""
        try:
            enhanced_prompt = f"""
            Write a compelling product description in {language} for: {product_name}
            
            Key features: {', '.join(features)}
            Main benefits: {', '.join(benefits)}
            Target audience: {target_audience}
            Writing style: {self.writing_styles.get(style, 'persuasive')}
            
            Requirements:
            - Highlight unique selling points
            - Focus on benefits over features
            - Include emotional triggers
            - Clear call to action
            - SEO-friendly
            - 200-400 words
            
            Make it compelling and conversion-focused.
            """
            
            result = await free_ai.generate_text(
                prompt=enhanced_prompt,
                language=language,
                style=style,
                max_length=500
            )
            
            if result['success']:
                description = result['text']
                
                # Generate bullet points for features
                feature_bullets = await self._generate_feature_bullets(
                    features, language
                )
                
                return {
                    'success': True,
                    'description': description,
                    'feature_bullets': feature_bullets,
                    'product_name': product_name,
                    'word_count': len(description.split()),
                    'language': language,
                    'style': style,
                    'service_used': result.get('service')
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"Product description generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_email_campaign(self, campaign_type: str, subject: str,
                                     target_audience: str, goal: str,
                                     language: str = 'en', personalized: bool = True) -> Dict[str, Any]:
        """Generate email campaign content"""
        try:
            if campaign_type not in self.content_types['email_campaign']['types']:
                return {
                    'success': False,
                    'error': f'Campaign type {campaign_type} not supported'
                }
            
            enhanced_prompt = f"""
            Write a {campaign_type} email campaign in {language}.
            
            Subject line: {subject}
            Target audience: {target_audience}
            Campaign goal: {goal}
            {'Personalized with merge tags' if personalized else 'Generic content'}
            
            Requirements:
            - Compelling subject line
            - Engaging opening
            - Clear value proposition
            - Strong call to action
            - Mobile-friendly format
            - Professional tone
            - 300-800 words
            
            Include email structure with headers and sections.
            """
            
            result = await free_ai.generate_text(
                prompt=enhanced_prompt,
                language=language,
                style='professional',
                max_length=1000
            )
            
            if result['success']:
                email_content = result['text']
                
                # Parse email sections
                email_sections = self._parse_email_sections(email_content)
                
                # Generate alternative subject lines
                alt_subjects = await self._generate_subject_lines(
                    subject, campaign_type, language
                )
                
                return {
                    'success': True,
                    'subject_line': email_sections.get('subject', subject),
                    'content': email_content,
                    'sections': email_sections,
                    'alternative_subjects': alt_subjects,
                    'campaign_type': campaign_type,
                    'word_count': len(email_content.split()),
                    'language': language,
                    'service_used': result.get('service')
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"Email campaign generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_ad_copy(self, product_service: str, platform: str,
                              target_audience: str, goal: str,
                              language: str = 'en', style: str = 'persuasive') -> Dict[str, Any]:
        """Generate advertising copy"""
        try:
            if platform not in self.content_types['ad_copy']['platforms']:
                return {
                    'success': False,
                    'error': f'Platform {platform} not supported'
                }
            
            max_length = self.content_types['ad_copy']['max_length'][platform]
            
            enhanced_prompt = f"""
            Create compelling ad copy in {language} for {platform}.
            
            Product/Service: {product_service}
            Target audience: {target_audience}
            Campaign goal: {goal}
            Maximum length: {max_length} characters
            Style: {self.writing_styles.get(style, 'persuasive')}
            
            Requirements:
            - Attention-grabbing headline
            - Clear value proposition
            - Strong call to action
            - Platform-specific best practices
            - Conversion-focused
            - Within character limit
            
            Create multiple variations for A/B testing.
            """
            
            result = await free_ai.generate_text(
                prompt=enhanced_prompt,
                language=language,
                style=style,
                max_length=max_length * 3  # Generate multiple variations
            )
            
            if result['success']:
                ad_content = result['text']
                
                # Parse multiple variations
                variations = self._parse_ad_variations(ad_content, max_length)
                
                # Generate headlines and CTAs
                headlines = await self._generate_headlines(
                    product_service, platform, language
                )
                ctas = await self._generate_ctas(goal, language)
                
                return {
                    'success': True,
                    'variations': variations,
                    'headlines': headlines,
                    'ctas': ctas,
                    'platform': platform,
                    'max_length': max_length,
                    'language': language,
                    'style': style,
                    'service_used': result.get('service')
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"Ad copy generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_content_calendar(self, business_type: str, platforms: List[str],
                                       duration_days: int, language: str = 'en') -> Dict[str, Any]:
        """Generate content calendar"""
        try:
            enhanced_prompt = f"""
            Create a {duration_days}-day content calendar in {language} for a {business_type}.
            
            Platforms: {', '.join(platforms)}
            
            Requirements:
            - Diverse content types (posts, stories, videos, etc.)
            - Platform-specific content
            - Engaging topics and themes
            - Optimal posting times
            - Content mix (promotional, educational, entertaining)
            - Hashtag suggestions
            - Visual content ideas
            
            Format as a structured calendar with daily recommendations.
            """
            
            result = await free_ai.generate_text(
                prompt=enhanced_prompt,
                language=language,
                style='professional',
                max_length=2000
            )
            
            if result['success']:
                calendar_content = result['text']
                
                # Parse calendar into structured format
                calendar_data = self._parse_content_calendar(
                    calendar_content, platforms, duration_days
                )
                
                return {
                    'success': True,
                    'calendar': calendar_data,
                    'business_type': business_type,
                    'platforms': platforms,
                    'duration_days': duration_days,
                    'language': language,
                    'service_used': result.get('service')
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"Content calendar generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return [tag.lower() for tag in hashtags]
    
    async def _generate_hashtags(self, topic: str, platform: str, 
                                count: int, language: str) -> List[str]:
        """Generate relevant hashtags"""
        try:
            prompt = f"Generate {count} relevant hashtags for {topic} on {platform} in {language}"
            result = await free_ai.generate_text(prompt, language, 'creative', 200)
            
            if result['success']:
                hashtags = self._extract_hashtags(result['text'])
                return hashtags[:count]
            
            return []
        except:
            return []
    
    def _parse_blog_sections(self, content: str) -> Dict[str, str]:
        """Parse blog content into sections"""
        sections = {}
        lines = content.split('\n')
        
        current_section = 'content'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for title (first line or line starting with #)
            if not sections.get('title') and (line.startswith('#') or len(sections) == 0):
                sections['title'] = line.replace('#', '').strip()
            else:
                current_content.append(line)
        
        sections['content'] = '\n'.join(current_content)
        return sections
    
    async def _generate_meta_description(self, topic: str, keywords: List[str], 
                                        language: str) -> str:
        """Generate SEO meta description"""
        try:
            prompt = f"Write a compelling 150-character meta description for a blog post about {topic} including keywords: {', '.join(keywords[:3])}"
            result = await free_ai.generate_text(prompt, language, 'persuasive', 160)
            
            if result['success']:
                return result['text'][:155] + '...' if len(result['text']) > 155 else result['text']
            
            return f"Learn about {topic} - comprehensive guide with expert insights."
        except:
            return f"Learn about {topic} - comprehensive guide with expert insights."
    
    async def _generate_feature_bullets(self, features: List[str], language: str) -> List[str]:
        """Generate feature bullet points"""
        bullets = []
        for feature in features:
            try:
                prompt = f"Write a compelling bullet point for this product feature: {feature}"
                result = await free_ai.generate_text(prompt, language, 'persuasive', 100)
                
                if result['success']:
                    bullets.append(result['text'].strip())
                else:
                    bullets.append(f"• {feature}")
            except:
                bullets.append(f"• {feature}")
        
        return bullets
    
    def _parse_email_sections(self, content: str) -> Dict[str, str]:
        """Parse email content into sections"""
        sections = {}
        lines = content.split('\n')
        
        # Extract subject line
        for line in lines:
            if 'subject:' in line.lower():
                sections['subject'] = line.split(':', 1)[1].strip()
                break
        
        sections['content'] = content
        return sections
    
    async def _generate_subject_lines(self, original: str, campaign_type: str, 
                                     language: str) -> List[str]:
        """Generate alternative subject lines"""
        try:
            prompt = f"Generate 3 alternative email subject lines for a {campaign_type} campaign. Original: {original}"
            result = await free_ai.generate_text(prompt, language, 'creative', 300)
            
            if result['success']:
                lines = [line.strip() for line in result['text'].split('\n') if line.strip()]
                return lines[:3]
            
            return []
        except:
            return []
    
    def _parse_ad_variations(self, content: str, max_length: int) -> List[str]:
        """Parse ad content into variations"""
        variations = []
        lines = content.split('\n')
        
        current_variation = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_variation:
                    variation_text = ' '.join(current_variation)
                    if len(variation_text) <= max_length:
                        variations.append(variation_text)
                    current_variation = []
            else:
                current_variation.append(line)
        
        # Add last variation
        if current_variation:
            variation_text = ' '.join(current_variation)
            if len(variation_text) <= max_length:
                variations.append(variation_text)
        
        return variations[:3]  # Return top 3 variations
    
    async def _generate_headlines(self, product: str, platform: str, language: str) -> List[str]:
        """Generate ad headlines"""
        try:
            prompt = f"Generate 3 compelling ad headlines for {product} on {platform}"
            result = await free_ai.generate_text(prompt, language, 'persuasive', 200)
            
            if result['success']:
                headlines = [line.strip() for line in result['text'].split('\n') if line.strip()]
                return headlines[:3]
            
            return []
        except:
            return []
    
    async def _generate_ctas(self, goal: str, language: str) -> List[str]:
        """Generate call-to-action phrases"""
        try:
            prompt = f"Generate 5 compelling call-to-action phrases for {goal}"
            result = await free_ai.generate_text(prompt, language, 'persuasive', 200)
            
            if result['success']:
                ctas = [line.strip() for line in result['text'].split('\n') if line.strip()]
                return ctas[:5]
            
            return []
        except:
            return []
    
    def _parse_content_calendar(self, content: str, platforms: List[str], 
                               duration: int) -> Dict[str, Any]:
        """Parse content calendar into structured format"""
        calendar = {}
        
        # This would parse the generated calendar content
        # For now, return a basic structure
        for day in range(1, duration + 1):
            calendar[f'day_{day}'] = {
                'date': f'Day {day}',
                'posts': [],
                'platforms': platforms
            }
        
        return calendar

# Global free content generator instance
free_content_generator = FreeContentGenerator()

