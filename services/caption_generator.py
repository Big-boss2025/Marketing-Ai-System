from datetime import datetime
from typing import Dict, List, Optional, Any
import random
import re
import logging
import google.generativeai as genai
import os
from src.services.free_ai_generator import free_ai_generator
from src.services.external_api_integration import api_integration

logger = logging.getLogger(__name__)

class CaptionGenerator:
    """Advanced Marketing Caption Generator using Google Gemini API"""
    
    def __init__(self):
        # Google Gemini Configuration
        self.gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        
        # Caption templates by style and language
        self.caption_templates = {
            'arabic': {
                'professional': [
                    "نقدم لكم {product} بأعلى معايير الجودة والاحترافية",
                    "اكتشفوا {product} الذي يلبي جميع احتياجاتكم",
                    "تجربة استثنائية مع {product} - جودة لا تُضاهى",
                    "استثمروا في {product} واحصلوا على أفضل النتائج"
                ],
                'casual': [
                    "جربوا {product} وشوفوا الفرق بنفسكم! 😊",
                    "ده {product} اللي كنتوا بتدوروا عليه! 🔥",
                    "مش هتصدقوا قد إيه {product} ده هيغير حياتكم",
                    "تعالوا نجرب {product} سوا ونشوف السحر! ✨"
                ],
                'urgent': [
                    "عرض محدود! احصلوا على {product} قبل نفاد الكمية",
                    "آخر فرصة للحصول على {product} بهذا السعر!",
                    "سارعوا! {product} متاح لفترة محدودة فقط",
                    "لا تفوتوا الفرصة - {product} بخصم يصل إلى {discount}%"
                ],
                'emotional': [
                    "لأنكم تستحقون الأفضل، نقدم لكم {product} ❤️",
                    "حققوا أحلامكم مع {product} - أنتم تستحقون ذلك",
                    "من القلب إلى القلب، {product} صُنع خصيصاً لكم",
                    "استثمروا في أنفسكم مع {product} - أنتم الأهم"
                ],
                'educational': [
                    "هل تعلمون أن {product} يمكن أن يحسن من {benefit}؟",
                    "تعلموا كيف يساعدكم {product} في تحقيق أهدافكم",
                    "اكتشفوا الطريقة الصحيحة لاستخدام {product}",
                    "نصائح مهمة حول {product} - معلومات قيمة لكم"
                ]
            },
            'english': {
                'professional': [
                    "Discover {product} with the highest standards of quality and professionalism",
                    "Experience {product} that meets all your needs",
                    "Exceptional experience with {product} - unmatched quality",
                    "Invest in {product} and get the best results"
                ],
                'casual': [
                    "Try {product} and see the difference yourself! 😊",
                    "This is the {product} you've been looking for! 🔥",
                    "You won't believe how {product} will change your life",
                    "Let's try {product} together and see the magic! ✨"
                ],
                'urgent': [
                    "Limited offer! Get {product} before it runs out",
                    "Last chance to get {product} at this price!",
                    "Hurry! {product} available for limited time only",
                    "Don't miss out - {product} with up to {discount}% off"
                ],
                'emotional': [
                    "Because you deserve the best, we present {product} ❤️",
                    "Achieve your dreams with {product} - you deserve it",
                    "From heart to heart, {product} made especially for you",
                    "Invest in yourself with {product} - you matter most"
                ],
                'educational': [
                    "Did you know that {product} can improve your {benefit}?",
                    "Learn how {product} helps you achieve your goals",
                    "Discover the right way to use {product}",
                    "Important tips about {product} - valuable information for you"
                ]
            }
        }
        
        # Platform-specific requirements
        self.platform_specs = {
            'instagram': {
                'max_length': 2200,
                'hashtag_limit': 30,
                'emoji_friendly': True,
                'line_breaks': True
            },
            'facebook': {
                'max_length': 63206,
                'hashtag_limit': 10,
                'emoji_friendly': True,
                'line_breaks': True
            },
            'twitter': {
                'max_length': 280,
                'hashtag_limit': 5,
                'emoji_friendly': True,
                'line_breaks': False
            },
            'linkedin': {
                'max_length': 3000,
                'hashtag_limit': 5,
                'emoji_friendly': False,
                'line_breaks': True
            },
            'tiktok': {
                'max_length': 150,
                'hashtag_limit': 10,
                'emoji_friendly': True,
                'line_breaks': False
            },
            'youtube': {
                'max_length': 5000,
                'hashtag_limit': 15,
                'emoji_friendly': True,
                'line_breaks': True
            }
        }
        
        # Emoji collections by category
        self.emojis = {
            'positive': ['😊', '😍', '🥰', '😎', '🤩', '✨', '🌟', '💫', '🎉', '🎊'],
            'business': ['💼', '📈', '💰', '🏆', '🎯', '🚀', '💡', '⚡', '🔥', '💪'],
            'hearts': ['❤️', '💙', '💚', '💛', '🧡', '💜', '🖤', '🤍', '💖', '💕'],
            'hands': ['👍', '👏', '🙌', '👌', '✋', '🤝', '💪', '🤲', '👐', '🙏'],
            'arrows': ['➡️', '⬆️', '⬇️', '↗️', '↘️', '🔄', '🔃', '🔁', '🔀', '⤴️']
        }
    
    async def generate_caption(self, caption_data: Dict) -> Dict:
        """Generate marketing caption using AI"""
        
        try:
            product = caption_data.get('product', '')
            style = caption_data.get('style', 'professional')
            language = caption_data.get('language', 'ar')
            platform = caption_data.get('platform', 'instagram')
            target_audience = caption_data.get('target_audience', '')
            call_to_action = caption_data.get('call_to_action', '')
            include_hashtags = caption_data.get('include_hashtags', True)
            include_emojis = caption_data.get('include_emojis', True)
            
            # Build AI prompt
            prompt = self.build_caption_prompt(
                product, style, language, platform, target_audience, call_to_action
            )
            
            # Generate caption using Gemini
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.8,
                service='google_gemini'
            )
            
            if result['success']:
                generated_caption = result['data'].get('text', '')
                
                # Optimize for platform
                optimized_caption = self.optimize_for_platform(
                    generated_caption, platform, language
                )
                
                # Add emojis if requested
                if include_emojis and self.platform_specs[platform]['emoji_friendly']:
                    optimized_caption = self.add_emojis(optimized_caption, style)
                
                # Generate hashtags if requested
                hashtags = []
                if include_hashtags:
                    hashtags = await self.generate_hashtags(product, target_audience, platform, language)
                
                # Combine caption and hashtags
                final_caption = self.combine_caption_and_hashtags(
                    optimized_caption, hashtags, platform
                )
                
                return {
                    'success': True,
                    'caption': final_caption,
                    'caption_only': optimized_caption,
                    'hashtags': hashtags,
                    'platform': platform,
                    'language': language,
                    'style': style,
                    'character_count': len(final_caption),
                    'within_limit': len(final_caption) <= self.platform_specs[platform]['max_length']
                }
            else:
                # Fallback to template-based generation
                return self.generate_template_caption(caption_data)
            
        except Exception as e:
            logger.error(f"Error generating caption: {str(e)}")
            return self.generate_template_caption(caption_data)
    
    def build_caption_prompt(self, product: str, style: str, language: str, 
                           platform: str, target_audience: str, call_to_action: str) -> str:
        """Build AI prompt for caption generation"""
        
        if language == 'ar':
            prompt = f"""أنت خبير في كتابة المحتوى التسويقي لوسائل التواصل الاجتماعي.

اكتب كابشن تسويقي جذاب:

المنتج/الخدمة: {product}
الأسلوب: {style}
المنصة: {platform}
الجمهور المستهدف: {target_audience}
دعوة للعمل: {call_to_action}

متطلبات الكابشن:
- يجب أن يكون جذاباً ومؤثراً
- مناسب لمنصة {platform}
- يخاطب {target_audience}
- يستخدم أسلوب {style}
- يتضمن دعوة واضحة للعمل
- لا يتجاوز {self.platform_specs[platform]['max_length']} حرف

اكتب الكابشن فقط بدون هاشتاجات:"""
        else:
            prompt = f"""You are an expert in writing marketing content for social media.

Write an engaging marketing caption:

Product/Service: {product}
Style: {style}
Platform: {platform}
Target Audience: {target_audience}
Call to Action: {call_to_action}

Caption Requirements:
- Must be engaging and impactful
- Suitable for {platform}
- Addresses {target_audience}
- Uses {style} style
- Includes clear call to action
- Does not exceed {self.platform_specs[platform]['max_length']} characters

Write only the caption without hashtags:"""
        
        return prompt
    
    def generate_template_caption(self, caption_data: Dict) -> Dict:
        """Generate caption using templates as fallback"""
        
        try:
            product = caption_data.get('product', '')
            style = caption_data.get('style', 'professional')
            language = caption_data.get('language', 'ar')
            platform = caption_data.get('platform', 'instagram')
            target_audience = caption_data.get('target_audience', '')
            
            # Get language key
            lang_key = 'arabic' if language == 'ar' else 'english'
            
            # Get templates for style
            templates = self.caption_templates[lang_key].get(style, 
                self.caption_templates[lang_key]['professional'])
            
            # Select random template
            template = random.choice(templates)
            
            # Format template
            caption = template.format(
                product=product,
                discount=random.choice(['20', '30', '40', '50']),
                benefit=random.choice(['الأداء', 'الجودة', 'الكفاءة'] if language == 'ar' 
                                    else ['performance', 'quality', 'efficiency'])
            )
            
            # Add emojis
            if self.platform_specs[platform]['emoji_friendly']:
                caption = self.add_emojis(caption, style)
            
            # Generate hashtags
            hashtags = self.generate_template_hashtags(product, target_audience, language)
            
            # Combine
            final_caption = self.combine_caption_and_hashtags(caption, hashtags, platform)
            
            return {
                'success': True,
                'caption': final_caption,
                'caption_only': caption,
                'hashtags': hashtags,
                'platform': platform,
                'language': language,
                'style': style,
                'character_count': len(final_caption),
                'within_limit': len(final_caption) <= self.platform_specs[platform]['max_length'],
                'method': 'template'
            }
            
        except Exception as e:
            logger.error(f"Error generating template caption: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def optimize_for_platform(self, caption: str, platform: str, language: str) -> str:
        """Optimize caption for specific platform"""
        
        max_length = self.platform_specs[platform]['max_length']
        
        # Truncate if too long
        if len(caption) > max_length:
            # Find good breaking point
            if language == 'ar':
                truncated = caption[:max_length-20] + "... المزيد في التعليقات"
            else:
                truncated = caption[:max_length-20] + "... more in comments"
            caption = truncated
        
        # Platform-specific formatting
        if platform == 'twitter':
            # Remove line breaks for Twitter
            caption = caption.replace('\n', ' ')
        
        elif platform == 'linkedin':
            # More professional tone for LinkedIn
            caption = caption.replace('😊', '').replace('🔥', '').replace('✨', '')
        
        return caption.strip()
    
    def add_emojis(self, caption: str, style: str) -> str:
        """Add appropriate emojis to caption"""
        
        try:
            # Select emoji category based on style
            if style == 'professional':
                emoji_categories = ['business']
            elif style == 'casual':
                emoji_categories = ['positive', 'hands']
            elif style == 'urgent':
                emoji_categories = ['business', 'arrows']
            elif style == 'emotional':
                emoji_categories = ['hearts', 'positive']
            else:
                emoji_categories = ['positive']
            
            # Add 1-3 emojis
            num_emojis = random.randint(1, 3)
            selected_emojis = []
            
            for _ in range(num_emojis):
                category = random.choice(emoji_categories)
                emoji = random.choice(self.emojis[category])
                if emoji not in selected_emojis:
                    selected_emojis.append(emoji)
            
            # Add emojis to caption
            if selected_emojis:
                caption += ' ' + ' '.join(selected_emojis)
            
            return caption
            
        except Exception as e:
            logger.error(f"Error adding emojis: {str(e)}")
            return caption
    
    async def generate_hashtags(self, product: str, target_audience: str, 
                              platform: str, language: str) -> List[str]:
        """Generate relevant hashtags using AI"""
        
        try:
            hashtag_limit = self.platform_specs[platform]['hashtag_limit']
            
            if language == 'ar':
                prompt = f"""أنشئ {hashtag_limit} هاشتاج مناسب لـ:
المنتج: {product}
الجمهور: {target_audience}
المنصة: {platform}

الهاشتاجات يجب أن تكون:
- مناسبة للمنتج والجمهور
- شائعة ومفيدة للوصول
- مزيج من العربية والإنجليزية
- مناسبة لمنصة {platform}

اكتب الهاشتاجات فقط، كل واحد في سطر منفصل:"""
            else:
                prompt = f"""Generate {hashtag_limit} relevant hashtags for:
Product: {product}
Audience: {target_audience}
Platform: {platform}

Hashtags should be:
- Relevant to product and audience
- Popular and useful for reach
- Suitable for {platform}
- Mix of broad and niche tags

Write only hashtags, one per line:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=200,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                hashtags_text = result['data'].get('text', '')
                hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip()]
                
                # Ensure hashtags start with #
                hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
                
                return hashtags[:hashtag_limit]
            else:
                return self.generate_template_hashtags(product, target_audience, language)
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {str(e)}")
            return self.generate_template_hashtags(product, target_audience, language)
    
    def generate_template_hashtags(self, product: str, target_audience: str, language: str) -> List[str]:
        """Generate hashtags using templates"""
        
        if language == 'ar':
            base_hashtags = ['#تسويق', '#أعمال', '#نجاح', '#جودة', '#خدمات']
        else:
            base_hashtags = ['#marketing', '#business', '#success', '#quality', '#services']
        
        # Add product-related hashtags
        product_words = product.lower().split()
        for word in product_words[:2]:  # Take first 2 words
            if len(word) > 3:
                base_hashtags.append(f'#{word}')
        
        # Add audience-related hashtags
        if target_audience:
            audience_words = target_audience.lower().split()
            for word in audience_words[:1]:  # Take first word
                if len(word) > 3:
                    base_hashtags.append(f'#{word}')
        
        return base_hashtags[:10]  # Limit to 10
    
    def combine_caption_and_hashtags(self, caption: str, hashtags: List[str], platform: str) -> str:
        """Combine caption and hashtags appropriately for platform"""
        
        if not hashtags:
            return caption
        
        hashtag_string = ' '.join(hashtags)
        
        if platform in ['instagram', 'facebook', 'youtube']:
            # Add hashtags on new lines
            return f"{caption}\n\n{hashtag_string}"
        
        elif platform == 'twitter':
            # Add hashtags inline if space allows
            combined = f"{caption} {hashtag_string}"
            if len(combined) <= 280:
                return combined
            else:
                # Reduce hashtags to fit
                reduced_hashtags = hashtags[:3]
                return f"{caption} {' '.join(reduced_hashtags)}"
        
        elif platform == 'linkedin':
            # Add hashtags at the end
            return f"{caption}\n\n{hashtag_string}"
        
        else:
            return f"{caption} {hashtag_string}"
    
    async def generate_multiple_captions(self, caption_data: Dict, count: int = 3) -> Dict:
        """Generate multiple caption variations"""
        
        try:
            captions = []
            
            for i in range(count):
                # Vary the style for different captions
                styles = ['professional', 'casual', 'urgent', 'emotional', 'educational']
                caption_data_copy = caption_data.copy()
                caption_data_copy['style'] = styles[i % len(styles)]
                
                result = await self.generate_caption(caption_data_copy)
                if result['success']:
                    captions.append({
                        'caption': result['caption'],
                        'style': caption_data_copy['style'],
                        'character_count': result['character_count'],
                        'within_limit': result['within_limit']
                    })
            
            return {
                'success': True,
                'captions': captions,
                'count': len(captions)
            }
            
        except Exception as e:
            logger.error(f"Error generating multiple captions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_caption_performance(self, caption: str, platform: str) -> Dict:
        """Analyze caption for potential performance"""
        
        try:
            analysis = {
                'character_count': len(caption),
                'word_count': len(caption.split()),
                'hashtag_count': len(re.findall(r'#\w+', caption)),
                'emoji_count': len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', caption)),
                'within_platform_limit': len(caption) <= self.platform_specs[platform]['max_length'],
                'engagement_score': 0,
                'recommendations': []
            }
            
            # Calculate engagement score
            score = 50  # Base score
            
            # Length optimization
            optimal_length = self.platform_specs[platform]['max_length'] * 0.7
            if len(caption) <= optimal_length:
                score += 10
            
            # Hashtag optimization
            if analysis['hashtag_count'] >= 3:
                score += 15
            
            # Emoji usage
            if analysis['emoji_count'] >= 1 and self.platform_specs[platform]['emoji_friendly']:
                score += 10
            
            # Call to action detection
            cta_keywords = ['اكتشف', 'جرب', 'احجز', 'اشترك', 'تابع', 'شارك',
                           'discover', 'try', 'book', 'subscribe', 'follow', 'share']
            if any(keyword in caption.lower() for keyword in cta_keywords):
                score += 15
            
            analysis['engagement_score'] = min(100, score)
            
            # Generate recommendations
            if analysis['character_count'] > self.platform_specs[platform]['max_length']:
                analysis['recommendations'].append('Caption is too long for this platform')
            
            if analysis['hashtag_count'] < 3:
                analysis['recommendations'].append('Consider adding more relevant hashtags')
            
            if analysis['emoji_count'] == 0 and self.platform_specs[platform]['emoji_friendly']:
                analysis['recommendations'].append('Consider adding emojis to increase engagement')
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing caption: {str(e)}")
            return {'error': str(e)}


# Global instance
caption_generator = CaptionGenerator()

