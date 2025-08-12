import google.generativeai as genai
import requests
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import subprocess
import tempfile
import uuid
from src.models.content import Content
from src.models.task import Task
from src.services.credit_manager import credit_manager
from src.services.external_api_integration import api_integration

logger = logging.getLogger(__name__)

class AIContentGenerator:
    """Advanced AI Content Generator with Google Gemini API integration"""
    
    def __init__(self):
        # Google Gemini Configuration
        self.gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        
        # Hugging Face Configuration (Free Alternative)
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        self.hf_api_url = 'https://api-inference.huggingface.co/models'
        
        # Marketing Strategies Database
        self.marketing_strategies = {
            'content_marketing': {
                'focus': 'valuable_content',
                'tone': 'educational_helpful',
                'cta_style': 'soft_educational',
                'content_types': ['blog_posts', 'tutorials', 'guides', 'infographics']
            },
            'social_media_marketing': {
                'focus': 'engagement_community',
                'tone': 'conversational_friendly',
                'cta_style': 'interactive_engaging',
                'content_types': ['posts', 'stories', 'reels', 'polls']
            },
            'influencer_marketing': {
                'focus': 'authenticity_trust',
                'tone': 'personal_relatable',
                'cta_style': 'recommendation_based',
                'content_types': ['testimonials', 'reviews', 'collaborations']
            },
            'email_marketing': {
                'focus': 'personalization_value',
                'tone': 'direct_personal',
                'cta_style': 'clear_actionable',
                'content_types': ['newsletters', 'promotions', 'sequences']
            },
            'seo_marketing': {
                'focus': 'search_optimization',
                'tone': 'informative_authoritative',
                'cta_style': 'keyword_optimized',
                'content_types': ['articles', 'landing_pages', 'meta_content']
            },
            'paid_advertising': {
                'focus': 'conversion_roi',
                'tone': 'persuasive_urgent',
                'cta_style': 'strong_direct',
                'content_types': ['ad_copy', 'headlines', 'descriptions']
            },
            'viral_marketing': {
                'focus': 'shareability_emotion',
                'tone': 'entertaining_memorable',
                'cta_style': 'share_encouraging',
                'content_types': ['memes', 'challenges', 'trending_content']
            },
            'brand_storytelling': {
                'focus': 'narrative_emotion',
                'tone': 'inspiring_authentic',
                'cta_style': 'journey_based',
                'content_types': ['stories', 'case_studies', 'testimonials']
            }
        }
        
        # Language-specific prompts and styles
        self.language_styles = {
            'ar': {
                'formal_tone': 'استخدم أسلوباً رسمياً ومهنياً',
                'casual_tone': 'استخدم أسلوباً ودوداً وقريباً من القارئ',
                'persuasive_tone': 'استخدم أسلوباً مقنعاً ومؤثراً',
                'educational_tone': 'استخدم أسلوباً تعليمياً وواضحاً',
                'emotional_tone': 'استخدم أسلوباً عاطفياً ومؤثراً',
                'cta_phrases': ['اكتشف المزيد', 'ابدأ الآن', 'احجز مكانك', 'لا تفوت الفرصة', 'انضم إلينا']
            },
            'en': {
                'formal_tone': 'Use a formal and professional tone',
                'casual_tone': 'Use a friendly and approachable tone',
                'persuasive_tone': 'Use a persuasive and compelling tone',
                'educational_tone': 'Use an educational and clear tone',
                'emotional_tone': 'Use an emotional and touching tone',
                'cta_phrases': ['Learn More', 'Get Started', 'Book Now', 'Don\'t Miss Out', 'Join Us']
            },
            'fr': {
                'formal_tone': 'Utilisez un ton formel et professionnel',
                'casual_tone': 'Utilisez un ton amical et accessible',
                'persuasive_tone': 'Utilisez un ton persuasif et convaincant',
                'educational_tone': 'Utilisez un ton éducatif et clair',
                'emotional_tone': 'Utilisez un ton émotionnel et touchant',
                'cta_phrases': ['En Savoir Plus', 'Commencer', 'Réserver', 'Ne Ratez Pas', 'Rejoignez-Nous']
            },
            'es': {
                'formal_tone': 'Usa un tono formal y profesional',
                'casual_tone': 'Usa un tono amigable y cercano',
                'persuasive_tone': 'Usa un tono persuasivo y convincente',
                'educational_tone': 'Usa un tono educativo y claro',
                'emotional_tone': 'Usa un tono emocional y conmovedor',
                'cta_phrases': ['Saber Más', 'Empezar', 'Reservar', 'No Te Pierdas', 'Únete']
            },
            'de': {
                'formal_tone': 'Verwenden Sie einen formellen und professionellen Ton',
                'casual_tone': 'Verwenden Sie einen freundlichen und zugänglichen Ton',
                'persuasive_tone': 'Verwenden Sie einen überzeugenden Ton',
                'educational_tone': 'Verwenden Sie einen lehrreichen und klaren Ton',
                'emotional_tone': 'Verwenden Sie einen emotionalen und berührenden Ton',
                'cta_phrases': ['Mehr Erfahren', 'Jetzt Starten', 'Buchen', 'Verpassen Sie Nicht', 'Mitmachen']
            }
        }
    
    async def generate_marketing_content(self, task_data: Dict) -> Dict:
        """Generate marketing content based on strategy and requirements"""
        
        try:
            strategy = task_data.get('strategy', 'content_marketing')
            content_type = task_data.get('content_type', 'social_post')
            language = task_data.get('language', 'ar')
            business_type = task_data.get('business_type', '')
            target_audience = task_data.get('target_audience', '')
            product_service = task_data.get('product_service', '')
            tone = task_data.get('tone', 'casual_tone')
            platform = task_data.get('platform', 'facebook')
            
            # Get strategy configuration
            strategy_config = self.marketing_strategies.get(strategy, self.marketing_strategies['content_marketing'])
            language_config = self.language_styles.get(language, self.language_styles['en'])
            
            # Build comprehensive prompt
            prompt = self.build_content_prompt(
                strategy_config, language_config, content_type, language,
                business_type, target_audience, product_service, tone, platform
            )
            
            # Generate content using Gemini
            content = await self.generate_text_content(prompt, language)
            
            if not content:
                return {'success': False, 'error': 'Failed to generate content'}
            
            # Generate hashtags
            hashtags = await self.generate_hashtags(product_service, target_audience, language, platform)
            
            # Generate image if needed
            image_url = None
            if task_data.get('include_image', True):
                image_result = await self.generate_content_image(content, product_service, language)
                if image_result['success']:
                    image_url = image_result['image_url']
            
            return {
                'success': True,
                'content': {
                    'text': content,
                    'hashtags': hashtags,
                    'image_url': image_url,
                    'strategy': strategy,
                    'language': language,
                    'platform': platform,
                    'content_type': content_type
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating marketing content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def build_content_prompt(self, strategy_config, language_config, content_type, language,
                           business_type, target_audience, product_service, tone, platform):
        """Build comprehensive content generation prompt"""
        
        if language == 'ar':
            base_prompt = f"""أنت خبير تسويق محترف متخصص في استراتيجية {strategy_config['focus']}.

مهمتك: إنشاء {content_type} تسويقي احترافي

معلومات المشروع:
- نوع العمل: {business_type}
- المنتج/الخدمة: {product_service}
- الجمهور المستهدف: {target_audience}
- المنصة: {platform}
- الاستراتيجية: {strategy_config['focus']}

متطلبات المحتوى:
- {language_config[tone]}
- ركز على {strategy_config['focus']}
- استخدم أسلوب {strategy_config['cta_style']}
- اجعل المحتوى مناسب لـ {platform}

إرشادات إضافية:
- استخدم كلمات مفتاحية قوية
- اجعل المحتوى جذاباً وقابلاً للمشاركة
- أضف دعوة واضحة للعمل
- تأكد من أن المحتوى يحفز التفاعل

اكتب المحتوى الآن:"""

        else:  # English
            base_prompt = f"""You are a professional marketing expert specializing in {strategy_config['focus']} strategy.

Task: Create professional {content_type} marketing content

Project Information:
- Business Type: {business_type}
- Product/Service: {product_service}
- Target Audience: {target_audience}
- Platform: {platform}
- Strategy: {strategy_config['focus']}

Content Requirements:
- {language_config[tone]}
- Focus on {strategy_config['focus']}
- Use {strategy_config['cta_style']} approach
- Make content suitable for {platform}

Additional Guidelines:
- Use powerful keywords
- Make content engaging and shareable
- Include clear call-to-action
- Ensure content encourages interaction

Write the content now:"""
        
        return base_prompt
    
    async def generate_text_content(self, prompt: str, language: str = 'ar') -> Optional[str]:
        """Generate text content using Google Gemini"""
        
        try:
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                return result['data'].get('text', '')
            else:
                logger.error(f"Error generating text content: {result.get('error')}")
                return None
            
        except Exception as e:
            logger.error(f"Error generating text content: {str(e)}")
            return None
    
    async def generate_hashtags(self, product_service: str, target_audience: str, 
                         language: str = 'ar', platform: str = 'facebook') -> List[str]:
        """Generate relevant hashtags"""
        
        try:
            if language == 'ar':
                prompt = f"""أنشئ 15 هاشتاج مناسب لـ:
المنتج/الخدمة: {product_service}
الجمهور المستهدف: {target_audience}
المنصة: {platform}

متطلبات الهاشتاجات:
- مزيج من الهاشتاجات الشائعة والمتخصصة
- باللغة العربية والإنجليزية
- مناسبة للمنصة المحددة
- تساعد في الوصول للجمهور المستهدف

اكتب الهاشتاجات فقط، كل هاشتاج في سطر منفصل:"""
            else:
                prompt = f"""Generate 15 relevant hashtags for:
Product/Service: {product_service}
Target Audience: {target_audience}
Platform: {platform}

Hashtag Requirements:
- Mix of popular and niche hashtags
- Suitable for the specified platform
- Help reach the target audience
- Include trending and evergreen tags

Write only hashtags, one per line:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=300,
                temperature=0.6,
                service='google_gemini'
            )
            
            if result['success']:
                hashtags_text = result['data'].get('text', '')
                hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip()]
                
                # Ensure hashtags start with #
                hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
                
                return hashtags[:15]  # Limit to 15 hashtags
            else:
                return ['#marketing', '#business', '#success']
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {str(e)}")
            return ['#marketing', '#business', '#success']
    
    async def generate_content_image(self, content: str, product_service: str, language: str = 'ar') -> Dict:
        """Generate image for content using Google Gemini or Hugging Face"""
        
        try:
            # Create image prompt based on content
            if language == 'ar':
                image_prompt = f"""صورة تسويقية احترافية لـ {product_service}، 
تصميم حديث وجذاب، ألوان زاهية، جودة عالية، 
مناسبة لوسائل التواصل الاجتماعي، تصميم مينيمال"""
            else:
                image_prompt = f"""Professional marketing image for {product_service}, 
modern and attractive design, vibrant colors, high quality, 
suitable for social media, minimal design"""
            
            # Try Google Gemini first
            result = await api_integration.generate_image(
                prompt=image_prompt,
                width=1024,
                height=1024,
                service='google_gemini'
            )
            
            if result['success']:
                # Save image
                image_data = base64.b64decode(result['data']['content'])
                image_filename = f"generated_image_{uuid.uuid4().hex}.png"
                image_path = os.path.join('src/static/generated_images', image_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                return {
                    'success': True,
                    'image_url': f"/static/generated_images/{image_filename}",
                    'image_path': image_path
                }
            
            # Fallback to Hugging Face
            return await self.generate_with_huggingface(image_prompt)
            
        except Exception as e:
            logger.error(f"Error generating content image: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_with_huggingface(self, prompt: str) -> Dict:
        """Generate image using Hugging Face"""
        
        try:
            result = await api_integration.generate_image(
                prompt=prompt,
                width=1024,
                height=1024,
                service='huggingface'
            )
            
            if result['success']:
                # Save image
                image_data = base64.b64decode(result['data']['content'])
                image_filename = f"generated_image_{uuid.uuid4().hex}.png"
                image_path = os.path.join('src/static/generated_images', image_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                return {
                    'success': True,
                    'image_url': f"/static/generated_images/{image_filename}",
                    'image_path': image_path
                }
            
            return {'success': False, 'error': 'Hugging Face API failed'}
            
        except Exception as e:
            logger.error(f"Error with Hugging Face: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_content_video(self, content: str, product_service: str, language: str = 'ar') -> Dict:
        """Generate video content (placeholder - video generation is complex)"""
        
        try:
            # For now, return a placeholder
            # Video generation would require more complex setup
            return {
                'success': False,
                'error': 'Video generation not implemented yet'
            }
            
        except Exception as e:
            logger.error(f"Error generating content video: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def optimize_content_for_platform(self, content: str, platform: str, language: str = 'ar') -> str:
        """Optimize content for specific platform"""
        
        platform_limits = {
            'twitter': 280,
            'instagram': 2200,
            'facebook': 63206,
            'linkedin': 3000,
            'tiktok': 150,
            'youtube': 5000
        }
        
        max_length = platform_limits.get(platform, 1000)
        
        if len(content) > max_length:
            # Truncate content while preserving meaning
            sentences = content.split('.')
            optimized_content = ""
            
            for sentence in sentences:
                if len(optimized_content + sentence + '.') <= max_length - 50:  # Leave space for CTA
                    optimized_content += sentence + '.'
                else:
                    break
            
            # Add platform-specific CTA
            if language == 'ar':
                cta_map = {
                    'twitter': 'تابعنا للمزيد',
                    'instagram': 'اكتشف المزيد في البايو',
                    'facebook': 'شاركنا رأيك في التعليقات',
                    'linkedin': 'تواصل معنا للمزيد من التفاصيل',
                    'tiktok': 'تابع للمزيد',
                    'youtube': 'اشترك في القناة'
                }
            else:
                cta_map = {
                    'twitter': 'Follow for more',
                    'instagram': 'Link in bio for more',
                    'facebook': 'Share your thoughts in comments',
                    'linkedin': 'Connect for more details',
                    'tiktok': 'Follow for more',
                    'youtube': 'Subscribe to our channel'
                }
            
            cta = cta_map.get(platform, 'Learn more')
            optimized_content += f"\n\n{cta}"
            
            return optimized_content
        
        return content
    
    def analyze_content_performance(self, content_data: Dict) -> Dict:
        """Analyze content performance metrics"""
        
        try:
            # Basic content analysis
            text = content_data.get('text', '')
            hashtags = content_data.get('hashtags', [])
            
            analysis = {
                'readability_score': self.calculate_readability(text),
                'engagement_potential': self.predict_engagement(text, hashtags),
                'seo_score': self.calculate_seo_score(text, hashtags),
                'sentiment_score': self.analyze_sentiment(text),
                'recommendations': []
            }
            
            # Generate recommendations
            if analysis['readability_score'] < 60:
                analysis['recommendations'].append('Consider simplifying the language for better readability')
            
            if analysis['engagement_potential'] < 70:
                analysis['recommendations'].append('Add more engaging elements like questions or calls-to-action')
            
            if len(hashtags) < 5:
                analysis['recommendations'].append('Consider adding more relevant hashtags')
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {str(e)}")
            return {'error': str(e)}
    
    def calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified)"""
        
        try:
            words = len(text.split())
            sentences = len([s for s in text.split('.') if s.strip()])
            
            if sentences == 0:
                return 0
            
            avg_words_per_sentence = words / sentences
            
            # Simple readability formula
            score = 100 - (avg_words_per_sentence * 2)
            return max(0, min(100, score))
            
        except:
            return 50  # Default score
    
    def predict_engagement(self, text: str, hashtags: List[str]) -> float:
        """Predict engagement potential (simplified)"""
        
        try:
            engagement_keywords = [
                'اكتشف', 'تعلم', 'شارك', 'احجز', 'انضم', 'ابدأ',
                'discover', 'learn', 'share', 'book', 'join', 'start',
                'new', 'free', 'exclusive', 'limited', 'now', 'today'
            ]
            
            score = 50  # Base score
            
            # Check for engagement keywords
            text_lower = text.lower()
            for keyword in engagement_keywords:
                if keyword in text_lower:
                    score += 5
            
            # Check hashtag count
            if len(hashtags) >= 5:
                score += 10
            
            # Check for questions
            if '?' in text:
                score += 15
            
            # Check for emojis (simplified check)
            emoji_indicators = ['😊', '🎉', '💡', '🔥', '❤️', '👍']
            for emoji in emoji_indicators:
                if emoji in text:
                    score += 5
            
            return min(100, score)
            
        except:
            return 50  # Default score
    
    def calculate_seo_score(self, text: str, hashtags: List[str]) -> float:
        """Calculate SEO score (simplified)"""
        
        try:
            score = 50  # Base score
            
            # Check text length
            word_count = len(text.split())
            if 50 <= word_count <= 300:
                score += 20
            
            # Check hashtag relevance
            if len(hashtags) >= 3:
                score += 15
            
            # Check for keywords repetition (avoid over-optimization)
            words = text.lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Penalize over-repetition
            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.1:  # More than 10% repetition
                score -= 10
            
            return min(100, max(0, score))
            
        except:
            return 50  # Default score
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment (simplified)"""
        
        try:
            positive_words = [
                'رائع', 'ممتاز', 'جيد', 'مفيد', 'مذهل', 'أحب',
                'great', 'excellent', 'good', 'useful', 'amazing', 'love',
                'best', 'perfect', 'wonderful', 'fantastic', 'awesome'
            ]
            
            negative_words = [
                'سيء', 'فظيع', 'مشكلة', 'صعب', 'مستحيل',
                'bad', 'terrible', 'problem', 'difficult', 'impossible',
                'hate', 'worst', 'awful', 'horrible', 'disappointing'
            ]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total_words = len(text.split())
            
            if total_words == 0:
                return 0.5  # Neutral
            
            sentiment_score = (positive_count - negative_count) / total_words
            
            # Normalize to 0-1 scale
            return max(0, min(1, 0.5 + sentiment_score))
            
        except:
            return 0.5  # Neutral


# Global instance
ai_content_generator = AIContentGenerator()

