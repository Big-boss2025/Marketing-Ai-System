import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
import json
import random
from collections import Counter
from src.services.free_ai_generator import free_ai_generator
from src.services.keyword_manager import keyword_manager

logger = logging.getLogger(__name__)

class ViralEngine:
    """Advanced Viral Content Engine - Guarantees Trending Content"""
    
    def __init__(self):
        # Platform-specific viral strategies
        self.platform_strategies = {
            'tiktok': {
                'optimal_length': (15, 30),  # seconds
                'hook_time': 3,  # first 3 seconds critical
                'trending_sounds': True,
                'hashtag_count': (3, 8),
                'posting_times': ['18:00', '19:00', '20:00', '21:00'],  # Peak hours
                'viral_elements': ['trending_audio', 'quick_cuts', 'text_overlay', 'trending_effects'],
                'engagement_triggers': ['questions', 'challenges', 'duets', 'stitches']
            },
            'instagram': {
                'optimal_length': (15, 60),  # seconds for reels
                'hook_time': 3,
                'trending_sounds': True,
                'hashtag_count': (8, 15),
                'posting_times': ['11:00', '13:00', '17:00', '19:00'],
                'viral_elements': ['trending_audio', 'story_structure', 'carousel_posts', 'reels'],
                'engagement_triggers': ['save_worthy', 'shareable', 'relatable', 'educational']
            },
            'youtube': {
                'optimal_length': (60, 600),  # seconds
                'hook_time': 15,
                'trending_sounds': False,
                'hashtag_count': (3, 5),
                'posting_times': ['14:00', '15:00', '16:00', '17:00'],
                'viral_elements': ['compelling_thumbnail', 'strong_title', 'good_retention', 'end_screens'],
                'engagement_triggers': ['subscribe_reminder', 'like_reminder', 'comment_questions', 'community_posts']
            },
            'twitter': {
                'optimal_length': (15, 140),  # characters for video tweets
                'hook_time': 5,
                'trending_sounds': False,
                'hashtag_count': (1, 3),
                'posting_times': ['09:00', '12:00', '15:00', '18:00'],
                'viral_elements': ['trending_topics', 'threads', 'polls', 'spaces'],
                'engagement_triggers': ['retweet_worthy', 'controversial', 'timely', 'newsworthy']
            },
            'facebook': {
                'optimal_length': (60, 180),  # seconds
                'hook_time': 10,
                'trending_sounds': False,
                'hashtag_count': (1, 5),
                'posting_times': ['13:00', '15:00', '19:00', '20:00'],
                'viral_elements': ['native_video', 'live_video', 'stories', 'groups'],
                'engagement_triggers': ['shareable', 'emotional', 'family_friendly', 'local_content']
            }
        }
        
        # Viral content patterns
        self.viral_patterns = {
            'arabic': {
                'hooks': [
                    'لن تصدق ما حدث!',
                    'هذا ما لا يخبرونك عنه',
                    'السر الذي يخفيه الخبراء',
                    'في 30 ثانية ستتغير حياتك',
                    'هذا ما فعلته في يوم واحد',
                    'الطريقة التي غيرت كل شيء',
                    'لماذا لا يعرف أحد هذا؟',
                    'هذا ما تعلمته بالطريقة الصعبة'
                ],
                'emotional_triggers': [
                    'مذهل', 'لا يصدق', 'صادم', 'مؤثر', 'ملهم', 'مضحك', 'مفاجئ', 'رائع',
                    'عبقري', 'بسيط', 'سهل', 'سريع', 'فعال', 'مجاني', 'حصري', 'جديد'
                ],
                'call_to_actions': [
                    'شارك رأيك في التعليقات',
                    'احفظ هذا المنشور',
                    'شارك مع أصدقائك',
                    'تابع للمزيد',
                    'اضغط لايك إذا أعجبك',
                    'ما رأيك؟ أخبرني',
                    'جرب هذا وأخبرني بالنتيجة',
                    'هل تريد المزيد من هذا المحتوى؟'
                ]
            },
            'english': {
                'hooks': [
                    'You won\'t believe what happened!',
                    'This is what they don\'t tell you',
                    'The secret experts hide',
                    'Your life will change in 30 seconds',
                    'This is what I did in one day',
                    'The method that changed everything',
                    'Why doesn\'t anyone know this?',
                    'This is what I learned the hard way'
                ],
                'emotional_triggers': [
                    'amazing', 'unbelievable', 'shocking', 'touching', 'inspiring', 'funny', 'surprising', 'awesome',
                    'genius', 'simple', 'easy', 'quick', 'effective', 'free', 'exclusive', 'new'
                ],
                'call_to_actions': [
                    'Share your thoughts in comments',
                    'Save this post',
                    'Share with friends',
                    'Follow for more',
                    'Like if you agree',
                    'What do you think? Tell me',
                    'Try this and let me know',
                    'Want more content like this?'
                ]
            }
        }
        
        # Trending audio/music categories
        self.trending_audio = {
            'motivational': ['upbeat', 'inspiring', 'energetic'],
            'emotional': ['touching', 'dramatic', 'heartfelt'],
            'funny': ['comedy', 'meme', 'viral_sound'],
            'educational': ['calm', 'professional', 'clear'],
            'lifestyle': ['trendy', 'modern', 'popular']
        }
        
        # Comment response templates
        self.comment_responses = {
            'arabic': {
                'positive': [
                    'شكراً لك! سعيد أن المحتوى أعجبك ❤️',
                    'أقدر تفاعلك الجميل! 🙏',
                    'تعليقك أسعدني كثيراً! 😊',
                    'شكراً للدعم المستمر! 💪',
                    'كلامك يحفزني للمزيد! 🔥'
                ],
                'questions': [
                    'سؤال ممتاز! سأجيب عليه في فيديو قادم 🎥',
                    'شكراً للسؤال! إليك الإجابة: ',
                    'سؤال مهم! دعني أوضح لك: ',
                    'أحب هذا السؤال! الإجابة هي: ',
                    'سؤال رائع! سأعمل محتوى مخصص عنه 📝'
                ],
                'negative': [
                    'أقدر رأيك، وسأحاول التحسين 🙏',
                    'شكراً للملاحظة، نقطة مهمة 💭',
                    'أفهم وجهة نظرك، شكراً للتوضيح 🤝',
                    'تعليق بناء، أشكرك عليه 📈',
                    'سأأخذ رأيك بعين الاعتبار 👍'
                ],
                'engagement': [
                    'ما رأيك في هذا الموضوع؟ 🤔',
                    'هل جربت هذا من قبل؟ 💭',
                    'شاركني تجربتك! 📝',
                    'أي جزء أعجبك أكثر؟ ⭐',
                    'هل تريد المزيد من هذا المحتوى؟ 🎯'
                ],
                'promotional': [
                    'تابع للمزيد من النصائح المفيدة! 🔔',
                    'احفظ هذا المنشور للرجوع إليه 📌',
                    'شارك مع من يحتاج هذه المعلومة 🔄',
                    'زر الرابط في البايو للمزيد 🔗',
                    'انضم لمجتمعنا للحصول على المزيد 👥'
                ]
            },
            'english': {
                'positive': [
                    'Thank you! So glad you enjoyed it ❤️',
                    'Appreciate your lovely feedback! 🙏',
                    'Your comment made my day! 😊',
                    'Thanks for the continued support! 💪',
                    'Your words motivate me to do more! 🔥'
                ],
                'questions': [
                    'Great question! I\'ll answer in an upcoming video 🎥',
                    'Thanks for asking! Here\'s the answer: ',
                    'Important question! Let me clarify: ',
                    'Love this question! The answer is: ',
                    'Excellent question! I\'ll create content about it 📝'
                ],
                'negative': [
                    'I appreciate your feedback, will try to improve 🙏',
                    'Thanks for the note, important point 💭',
                    'I understand your perspective, thanks for clarifying 🤝',
                    'Constructive comment, thank you 📈',
                    'I\'ll take your opinion into consideration 👍'
                ],
                'engagement': [
                    'What do you think about this topic? 🤔',
                    'Have you tried this before? 💭',
                    'Share your experience! 📝',
                    'Which part did you like most? ⭐',
                    'Want more content like this? 🎯'
                ],
                'promotional': [
                    'Follow for more useful tips! 🔔',
                    'Save this post for later reference 📌',
                    'Share with someone who needs this info 🔄',
                    'Check the link in bio for more 🔗',
                    'Join our community for more content 👥'
                ]
            }
        }
    
    def create_viral_content_strategy(self, content_type: str, platform: str, 
                                    target_audience: Dict, language: str = 'ar') -> Dict:
        """Create a comprehensive viral content strategy"""
        try:
            strategy = self.platform_strategies.get(platform, {})
            patterns = self.viral_patterns.get(language, {})
            
            # Generate viral elements
            viral_strategy = {
                'platform': platform,
                'language': language,
                'content_type': content_type,
                'target_audience': target_audience,
                
                # Timing strategy
                'optimal_posting_times': strategy.get('posting_times', []),
                'best_days': self.get_best_posting_days(platform, target_audience),
                
                # Content structure
                'hook_strategy': self.generate_hook_strategy(content_type, language),
                'content_length': strategy.get('optimal_length', (30, 60)),
                'viral_elements': strategy.get('viral_elements', []),
                
                # Hashtag strategy
                'hashtag_strategy': self.generate_hashtag_strategy(platform, content_type, language),
                
                # Engagement strategy
                'engagement_triggers': strategy.get('engagement_triggers', []),
                'call_to_action': random.choice(patterns.get('call_to_actions', ['تفاعل معنا'])),
                
                # Algorithm optimization
                'algorithm_hacks': self.get_algorithm_hacks(platform),
                
                # Trending elements
                'trending_topics': self.get_current_trending_topics(language),
                'trending_sounds': self.get_trending_sounds(platform, content_type) if strategy.get('trending_sounds') else None,
                
                # Success metrics
                'target_metrics': self.calculate_viral_targets(platform, target_audience),
                
                # Auto-response strategy
                'comment_response_strategy': self.create_comment_response_strategy(language, content_type)
            }
            
            return {
                'success': True,
                'viral_strategy': viral_strategy,
                'confidence_score': self.calculate_viral_confidence(viral_strategy),
                'estimated_reach': self.estimate_viral_reach(viral_strategy)
            }
            
        except Exception as e:
            logger.error(f"Error creating viral strategy: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_hook_strategy(self, content_type: str, language: str = 'ar') -> Dict:
        """Generate compelling hook strategy for viral content"""
        patterns = self.viral_patterns.get(language, {})
        hooks = patterns.get('hooks', [])
        triggers = patterns.get('emotional_triggers', [])
        
        return {
            'opening_hook': random.choice(hooks),
            'emotional_trigger': random.choice(triggers),
            'hook_duration': 3,  # seconds
            'hook_elements': [
                'visual_impact',
                'emotional_trigger',
                'curiosity_gap',
                'immediate_value'
            ],
            'hook_templates': [
                f"في {random.randint(10, 60)} ثانية ستتعلم...",
                f"هذا السر الذي يخفيه...",
                f"لن تصدق ما اكتشفته...",
                f"الطريقة التي غيرت حياتي..."
            ] if language == 'ar' else [
                f"In {random.randint(10, 60)} seconds you'll learn...",
                f"This secret that experts hide...",
                f"You won't believe what I discovered...",
                f"The method that changed my life..."
            ]
        }
    
    def generate_hashtag_strategy(self, platform: str, content_type: str, language: str = 'ar') -> Dict:
        """Generate optimized hashtag strategy for viral reach"""
        strategy = self.platform_strategies.get(platform, {})
        hashtag_count = strategy.get('hashtag_count', (5, 10))
        
        # Get trending hashtags
        trending_hashtags = keyword_manager.get_trending_hashtags(platform, language, limit=5)
        
        # Get content-specific hashtags
        content_hashtags = self.get_content_specific_hashtags(content_type, language)
        
        # Get niche hashtags
        niche_hashtags = self.get_niche_hashtags(content_type, language)
        
        return {
            'total_hashtags': random.randint(hashtag_count[0], hashtag_count[1]),
            'hashtag_mix': {
                'trending': trending_hashtags[:2],  # 2 trending
                'content_specific': content_hashtags[:3],  # 3 content-specific
                'niche': niche_hashtags[:3],  # 3 niche
                'branded': self.get_branded_hashtags(language)[:2]  # 2 branded
            },
            'hashtag_placement': 'caption' if platform in ['instagram', 'tiktok'] else 'description',
            'hashtag_timing': 'immediate' if platform == 'twitter' else 'first_comment'
        }
    
    def get_algorithm_hacks(self, platform: str) -> List[str]:
        """Get platform-specific algorithm optimization hacks"""
        hacks = {
            'tiktok': [
                'Post during peak hours (6-10 PM)',
                'Use trending sounds within first 24 hours',
                'Create content that encourages rewatches',
                'Engage with comments within first hour',
                'Use trending effects and filters',
                'Keep viewers watching till the end',
                'Post consistently (1-3 times daily)',
                'Collaborate with other creators'
            ],
            'instagram': [
                'Post when your audience is most active',
                'Use all 10 hashtags in first comment',
                'Create save-worthy content',
                'Encourage shares to stories',
                'Use Instagram Reels for maximum reach',
                'Engage with your audience quickly',
                'Cross-promote on other platforms',
                'Use location tags for local reach'
            ],
            'youtube': [
                'Optimize thumbnail for high CTR',
                'Front-load value in first 15 seconds',
                'Use end screens and cards',
                'Encourage comments and engagement',
                'Create playlists for session time',
                'Use trending keywords in title',
                'Post consistently on schedule',
                'Engage with community tab'
            ],
            'twitter': [
                'Tweet during peak engagement hours',
                'Use trending hashtags and topics',
                'Create tweetstorms for more visibility',
                'Engage with trending conversations',
                'Use polls and questions',
                'Retweet and quote tweet strategically',
                'Join Twitter Spaces',
                'Use Twitter threads for longer content'
            ],
            'facebook': [
                'Post native videos for better reach',
                'Use Facebook Live for real-time engagement',
                'Create shareable content',
                'Post in relevant groups',
                'Use Facebook Stories',
                'Encourage meaningful conversations',
                'Cross-post to Instagram',
                'Use Facebook Events for promotion'
            ]
        }
        
        return hacks.get(platform, [])
    
    def get_current_trending_topics(self, language: str = 'ar') -> List[str]:
        """Get current trending topics"""
        # This would typically fetch from external APIs
        # For now, we'll return simulated trending topics
        
        trending_topics = {
            'ar': [
                'الذكاء الاصطناعي',
                'ريادة الأعمال',
                'التسويق الرقمي',
                'الصحة النفسية',
                'التطوير الشخصي',
                'التكنولوجيا',
                'الاستثمار',
                'التعليم الإلكتروني'
            ],
            'en': [
                'artificial intelligence',
                'entrepreneurship',
                'digital marketing',
                'mental health',
                'personal development',
                'technology',
                'investment',
                'online learning'
            ]
        }
        
        return trending_topics.get(language, [])
    
    def get_trending_sounds(self, platform: str, content_type: str) -> Dict:
        """Get trending sounds/music for the platform"""
        if platform not in ['tiktok', 'instagram']:
            return None
        
        # This would typically fetch from platform APIs
        # For now, we'll return simulated trending sounds
        
        return {
            'trending_sounds': [
                {
                    'name': 'Trending Sound 1',
                    'usage_count': 1500000,
                    'trend_score': 95,
                    'category': 'motivational'
                },
                {
                    'name': 'Trending Sound 2',
                    'usage_count': 1200000,
                    'trend_score': 88,
                    'category': 'funny'
                }
            ],
            'recommendation': 'Use trending sound within first 24 hours of trend',
            'optimal_usage': 'Full track for maximum algorithm boost'
        }
    
    def calculate_viral_targets(self, platform: str, target_audience: Dict) -> Dict:
        """Calculate target metrics for viral success"""
        base_metrics = {
            'tiktok': {
                'views': 100000,
                'likes': 10000,
                'shares': 1000,
                'comments': 500,
                'completion_rate': 80
            },
            'instagram': {
                'views': 50000,
                'likes': 5000,
                'shares': 500,
                'comments': 300,
                'saves': 1000
            },
            'youtube': {
                'views': 10000,
                'likes': 1000,
                'shares': 100,
                'comments': 200,
                'watch_time': 60
            },
            'twitter': {
                'views': 25000,
                'likes': 2500,
                'retweets': 500,
                'comments': 250,
                'engagement_rate': 5
            },
            'facebook': {
                'views': 20000,
                'likes': 2000,
                'shares': 400,
                'comments': 300,
                'reach': 50000
            }
        }
        
        return base_metrics.get(platform, {})
    
    def create_comment_response_strategy(self, language: str, content_type: str) -> Dict:
        """Create intelligent comment response strategy"""
        responses = self.comment_responses.get(language, {})
        
        return {
            'auto_response_enabled': True,
            'response_delay': (2, 10),  # minutes
            'response_templates': responses,
            'sentiment_analysis': True,
            'personalization': True,
            'engagement_boost': True,
            'response_rules': {
                'positive_comments': {
                    'response_rate': 80,
                    'templates': responses.get('positive', []),
                    'add_emoji': True,
                    'promote_content': True
                },
                'questions': {
                    'response_rate': 95,
                    'templates': responses.get('questions', []),
                    'provide_value': True,
                    'create_content': True
                },
                'negative_comments': {
                    'response_rate': 100,
                    'templates': responses.get('negative', []),
                    'professional_tone': True,
                    'turn_positive': True
                },
                'spam_comments': {
                    'response_rate': 0,
                    'action': 'delete_and_block',
                    'auto_moderate': True
                }
            }
        }
    
    def generate_smart_response(self, comment_text: str, language: str, 
                              sentiment: str, content_context: str) -> Dict:
        """Generate intelligent response to comments"""
        try:
            responses = self.comment_responses.get(language, {})
            
            # Analyze comment type
            comment_type = self.analyze_comment_type(comment_text, language)
            
            # Get appropriate response template
            if sentiment == 'positive':
                base_responses = responses.get('positive', [])
            elif sentiment == 'negative':
                base_responses = responses.get('negative', [])
            elif comment_type == 'question':
                base_responses = responses.get('questions', [])
            else:
                base_responses = responses.get('engagement', [])
            
            # Select and customize response
            base_response = random.choice(base_responses)
            
            # Generate AI-enhanced response
            if comment_type == 'question':
                ai_response = self.generate_ai_answer(comment_text, content_context, language)
                if ai_response['success']:
                    response = base_response + ai_response['answer']
                else:
                    response = base_response
            else:
                response = base_response
            
            # Add personalization
            if 'شكراً' in comment_text or 'thanks' in comment_text.lower():
                response = self.add_gratitude_response(response, language)
            
            return {
                'success': True,
                'response': response,
                'response_type': comment_type,
                'sentiment': sentiment,
                'engagement_score': self.calculate_response_engagement_score(response),
                'should_pin': comment_type == 'question' and sentiment == 'positive'
            }
            
        except Exception as e:
            logger.error(f"Error generating smart response: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_comment_type(self, comment_text: str, language: str) -> str:
        """Analyze the type of comment"""
        comment_lower = comment_text.lower()
        
        # Question indicators
        question_words = {
            'ar': ['كيف', 'ماذا', 'متى', 'أين', 'لماذا', 'هل', 'ما', '؟'],
            'en': ['how', 'what', 'when', 'where', 'why', 'can', 'could', 'would', '?']
        }
        
        # Positive indicators
        positive_words = {
            'ar': ['رائع', 'ممتاز', 'جميل', 'مفيد', 'شكراً', 'أحب', 'مذهل'],
            'en': ['great', 'awesome', 'amazing', 'love', 'thanks', 'excellent', 'wonderful']
        }
        
        # Negative indicators
        negative_words = {
            'ar': ['سيء', 'لا أحب', 'خطأ', 'مشكلة', 'صعب', 'معقد'],
            'en': ['bad', 'hate', 'wrong', 'problem', 'difficult', 'complicated']
        }
        
        words = question_words.get(language, [])
        if any(word in comment_lower for word in words):
            return 'question'
        
        words = positive_words.get(language, [])
        if any(word in comment_lower for word in words):
            return 'positive'
        
        words = negative_words.get(language, [])
        if any(word in comment_lower for word in words):
            return 'negative'
        
        return 'neutral'
    
    def generate_ai_answer(self, question: str, content_context: str, language: str) -> Dict:
        """Generate AI-powered answer to questions"""
        try:
            if language == 'ar':
                prompt = f"""
                أجب على هذا السؤال بناءً على السياق المعطى:
                
                السؤال: {question}
                السياق: {content_context}
                
                اكتب إجابة مفيدة ومختصرة (50 كلمة كحد أقصى) باللغة العربية.
                """
            else:
                prompt = f"""
                Answer this question based on the given context:
                
                Question: {question}
                Context: {content_context}
                
                Write a helpful and concise answer (50 words maximum) in English.
                """
            
            ai_result = free_ai_generator.generate_text(prompt, max_length=100)
            
            if ai_result['success']:
                return {
                    'success': True,
                    'answer': ai_result['text'].strip()
                }
            
            return {'success': False, 'error': 'AI generation failed'}
            
        except Exception as e:
            logger.error(f"Error generating AI answer: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def add_gratitude_response(self, response: str, language: str) -> str:
        """Add gratitude elements to response"""
        gratitude_additions = {
            'ar': [' 🙏', ' أقدر تفاعلك', ' شكراً لك'],
            'en': [' 🙏', ' appreciate you', ' thank you']
        }
        
        additions = gratitude_additions.get(language, [])
        return response + random.choice(additions)
    
    def calculate_response_engagement_score(self, response: str) -> float:
        """Calculate potential engagement score for response"""
        score = 50.0  # Base score
        
        # Length score
        word_count = len(response.split())
        if 5 <= word_count <= 20:
            score += 20
        elif word_count > 20:
            score -= 10
        
        # Emoji score
        emoji_count = len(re.findall(r'[😀-🙏]', response))
        score += min(emoji_count * 5, 15)
        
        # Question score (encourages more engagement)
        if '؟' in response or '?' in response:
            score += 15
        
        # Call to action score
        cta_words = ['تابع', 'شارك', 'احفظ', 'follow', 'share', 'save']
        if any(word in response.lower() for word in cta_words):
            score += 10
        
        return min(score, 100.0)
    
    def calculate_viral_confidence(self, viral_strategy: Dict) -> float:
        """Calculate confidence score for viral success"""
        score = 0.0
        
        # Platform optimization score
        if viral_strategy.get('algorithm_hacks'):
            score += 25
        
        # Timing score
        if viral_strategy.get('optimal_posting_times'):
            score += 20
        
        # Content structure score
        if viral_strategy.get('hook_strategy'):
            score += 20
        
        # Hashtag strategy score
        hashtag_strategy = viral_strategy.get('hashtag_strategy', {})
        if hashtag_strategy.get('hashtag_mix'):
            score += 15
        
        # Trending elements score
        if viral_strategy.get('trending_topics'):
            score += 10
        
        # Engagement strategy score
        if viral_strategy.get('comment_response_strategy'):
            score += 10
        
        return min(score, 100.0)
    
    def estimate_viral_reach(self, viral_strategy: Dict) -> Dict:
        """Estimate potential viral reach"""
        platform = viral_strategy.get('platform', 'instagram')
        confidence = self.calculate_viral_confidence(viral_strategy)
        
        base_reach = {
            'tiktok': 50000,
            'instagram': 25000,
            'youtube': 10000,
            'twitter': 15000,
            'facebook': 20000
        }
        
        platform_reach = base_reach.get(platform, 25000)
        
        # Adjust based on confidence
        multiplier = confidence / 100 * 5  # Up to 5x multiplier
        estimated_reach = int(platform_reach * multiplier)
        
        return {
            'estimated_views': estimated_reach,
            'estimated_engagement': int(estimated_reach * 0.1),
            'viral_probability': confidence,
            'time_to_viral': '2-6 hours' if confidence > 80 else '6-24 hours'
        }
    
    def get_content_specific_hashtags(self, content_type: str, language: str) -> List[str]:
        """Get hashtags specific to content type"""
        hashtags = {
            'ar': {
                'educational': ['تعليم', 'تعلم', 'معرفة', 'نصائح', 'مهارات'],
                'entertainment': ['ترفيه', 'مرح', 'كوميديا', 'تسلية', 'فكاهة'],
                'business': ['أعمال', 'ريادة', 'نجاح', 'استثمار', 'تطوير'],
                'lifestyle': ['حياة', 'نمط_حياة', 'صحة', 'جمال', 'موضة'],
                'technology': ['تقنية', 'تكنولوجيا', 'ذكاء_اصطناعي', 'ابتكار', 'رقمي']
            },
            'en': {
                'educational': ['education', 'learning', 'knowledge', 'tips', 'skills'],
                'entertainment': ['entertainment', 'fun', 'comedy', 'funny', 'humor'],
                'business': ['business', 'entrepreneur', 'success', 'investment', 'growth'],
                'lifestyle': ['lifestyle', 'life', 'health', 'beauty', 'fashion'],
                'technology': ['technology', 'tech', 'ai', 'innovation', 'digital']
            }
        }
        
        return hashtags.get(language, {}).get(content_type, [])
    
    def get_niche_hashtags(self, content_type: str, language: str) -> List[str]:
        """Get niche hashtags for targeted reach"""
        # These would be smaller, more targeted hashtags
        niche_hashtags = {
            'ar': ['محتوى_عربي', 'مبدعين_عرب', 'تطوير_ذاتي', 'نصائح_يومية'],
            'en': ['contentcreator', 'smallbusiness', 'dailytips', 'motivation']
        }
        
        return niche_hashtags.get(language, [])
    
    def get_branded_hashtags(self, language: str) -> List[str]:
        """Get branded hashtags for the system"""
        branded = {
            'ar': ['نظام_التسويق_الذكي', 'تسويق_آلي', 'ذكاء_تسويقي'],
            'en': ['smartmarketing', 'automarketing', 'marketingai']
        }
        
        return branded.get(language, [])
    
    def get_best_posting_days(self, platform: str, target_audience: Dict) -> List[str]:
        """Get best days for posting based on platform and audience"""
        best_days = {
            'tiktok': ['Tuesday', 'Thursday', 'Friday'],
            'instagram': ['Tuesday', 'Wednesday', 'Friday'],
            'youtube': ['Thursday', 'Friday', 'Saturday'],
            'twitter': ['Tuesday', 'Wednesday', 'Thursday'],
            'facebook': ['Wednesday', 'Thursday', 'Friday']
        }
        
        return best_days.get(platform, ['Tuesday', 'Wednesday', 'Thursday'])

# Global viral engine instance
viral_engine = ViralEngine()

