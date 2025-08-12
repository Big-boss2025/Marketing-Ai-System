import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
import json
import asyncio
import random
from textblob import TextBlob
from src.services.viral_engine import viral_engine
from src.services.free_ai_generator import free_ai_generator
from src.models.content import Content

logger = logging.getLogger(__name__)

class AutoResponder:
    """Intelligent Auto-Response System for Social Media Comments"""
    
    def __init__(self):
        # Response timing settings
        self.response_timing = {
            'immediate': (1, 3),    # 1-3 minutes
            'quick': (3, 10),       # 3-10 minutes
            'normal': (10, 30),     # 10-30 minutes
            'delayed': (30, 120)    # 30-120 minutes
        }
        
        # Platform-specific settings
        self.platform_settings = {
            'tiktok': {
                'max_response_length': 150,
                'emoji_frequency': 'high',
                'response_style': 'casual',
                'priority_response_time': 'immediate'
            },
            'instagram': {
                'max_response_length': 200,
                'emoji_frequency': 'medium',
                'response_style': 'friendly',
                'priority_response_time': 'quick'
            },
            'youtube': {
                'max_response_length': 300,
                'emoji_frequency': 'low',
                'response_style': 'professional',
                'priority_response_time': 'normal'
            },
            'twitter': {
                'max_response_length': 280,
                'emoji_frequency': 'medium',
                'response_style': 'witty',
                'priority_response_time': 'immediate'
            },
            'facebook': {
                'max_response_length': 250,
                'emoji_frequency': 'low',
                'response_style': 'professional',
                'priority_response_time': 'quick'
            }
        }
        
        # Sentiment analysis keywords
        self.sentiment_keywords = {
            'arabic': {
                'positive': [
                    'رائع', 'ممتاز', 'جميل', 'مفيد', 'شكراً', 'أحب', 'مذهل', 'عظيم',
                    'مبدع', 'ملهم', 'قوي', 'مؤثر', 'جيد', 'حلو', 'كويس', 'تمام'
                ],
                'negative': [
                    'سيء', 'لا أحب', 'خطأ', 'مشكلة', 'صعب', 'معقد', 'مش عاجبني',
                    'غلط', 'وحش', 'مش كويس', 'مش حلو', 'مش مفيد'
                ],
                'neutral': [
                    'ممكن', 'ربما', 'لا أعرف', 'مش متأكد', 'عادي', 'مقبول'
                ]
            },
            'english': {
                'positive': [
                    'great', 'awesome', 'amazing', 'love', 'thanks', 'excellent', 'wonderful',
                    'fantastic', 'brilliant', 'perfect', 'good', 'nice', 'cool', 'helpful'
                ],
                'negative': [
                    'bad', 'hate', 'wrong', 'problem', 'difficult', 'complicated', 'terrible',
                    'awful', 'horrible', 'worst', 'sucks', 'disappointing'
                ],
                'neutral': [
                    'maybe', 'perhaps', 'not sure', 'okay', 'fine', 'acceptable'
                ]
            }
        }
        
        # Spam detection patterns
        self.spam_patterns = [
            r'follow.*back',
            r'check.*my.*profile',
            r'dm.*me',
            r'click.*link',
            r'free.*money',
            r'win.*prize',
            r'congratulations.*winner',
            r'urgent.*reply',
            r'limited.*time.*offer'
        ]
        
        # Response templates for different scenarios
        self.response_templates = {
            'arabic': {
                'first_time_commenter': [
                    'أهلاً بك في مجتمعنا! 🎉',
                    'مرحباً! سعيد بانضمامك لنا 😊',
                    'أهلاً وسهلاً! نورت المكان ✨'
                ],
                'regular_commenter': [
                    'شكراً لتفاعلك المستمر! 🙏',
                    'دائماً متفاعل معنا، أقدر ذلك! 💪',
                    'من المتابعين المميزين! شكراً لك ❤️'
                ],
                'question_follow_up': [
                    'هل هذا يجيب على سؤالك؟ 🤔',
                    'أتمنى أن تكون الإجابة واضحة! 💭',
                    'إذا كان لديك أسئلة أخرى، لا تتردد! 📝'
                ],
                'engagement_booster': [
                    'ما رأيك في هذا الموضوع؟ 💬',
                    'شاركنا تجربتك! 📖',
                    'هل جربت هذا من قبل؟ 🎯'
                ],
                'content_promotion': [
                    'تابع للمزيد من النصائح المفيدة! 🔔',
                    'احفظ هذا المنشور للرجوع إليه 📌',
                    'شارك مع من يحتاج هذه المعلومة 🔄'
                ]
            },
            'english': {
                'first_time_commenter': [
                    'Welcome to our community! 🎉',
                    'Hello! Great to have you here 😊',
                    'Welcome! Thanks for joining us ✨'
                ],
                'regular_commenter': [
                    'Thanks for your continued engagement! 🙏',
                    'Always engaging with us, appreciate it! 💪',
                    'One of our amazing followers! Thank you ❤️'
                ],
                'question_follow_up': [
                    'Does this answer your question? 🤔',
                    'Hope this clarifies things! 💭',
                    'Feel free to ask if you have more questions! 📝'
                ],
                'engagement_booster': [
                    'What do you think about this? 💬',
                    'Share your experience! 📖',
                    'Have you tried this before? 🎯'
                ],
                'content_promotion': [
                    'Follow for more useful tips! 🔔',
                    'Save this post for later reference 📌',
                    'Share with someone who needs this! 🔄'
                ]
            }
        }
    
    def analyze_comment_sentiment(self, comment_text: str, language: str = 'ar') -> Dict:
        """Analyze sentiment of a comment"""
        try:
            comment_lower = comment_text.lower()
            
            # Get language-specific keywords
            keywords = self.sentiment_keywords.get(language, self.sentiment_keywords['english'])
            
            positive_score = 0
            negative_score = 0
            
            # Count positive keywords
            for word in keywords['positive']:
                if word in comment_lower:
                    positive_score += 1
            
            # Count negative keywords
            for word in keywords['negative']:
                if word in comment_lower:
                    negative_score += 1
            
            # Determine sentiment
            if positive_score > negative_score:
                sentiment = 'positive'
                confidence = min(positive_score / (positive_score + negative_score + 1), 0.9)
            elif negative_score > positive_score:
                sentiment = 'negative'
                confidence = min(negative_score / (positive_score + negative_score + 1), 0.9)
            else:
                sentiment = 'neutral'
                confidence = 0.5
            
            # Use TextBlob for English sentiment analysis as backup
            if language == 'en' and confidence < 0.7:
                try:
                    blob = TextBlob(comment_text)
                    polarity = blob.sentiment.polarity
                    
                    if polarity > 0.1:
                        sentiment = 'positive'
                        confidence = min(polarity, 0.9)
                    elif polarity < -0.1:
                        sentiment = 'negative'
                        confidence = min(abs(polarity), 0.9)
                    else:
                        sentiment = 'neutral'
                        confidence = 0.5
                except:
                    pass
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'positive_score': positive_score,
                'negative_score': negative_score
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'positive_score': 0,
                'negative_score': 0
            }
    
    def detect_spam(self, comment_text: str, commenter_info: Dict = None) -> bool:
        """Detect if a comment is spam"""
        try:
            comment_lower = comment_text.lower()
            
            # Check against spam patterns
            for pattern in self.spam_patterns:
                if re.search(pattern, comment_lower):
                    return True
            
            # Check for excessive links
            link_count = len(re.findall(r'http[s]?://|www\.', comment_text))
            if link_count > 1:
                return True
            
            # Check for excessive emojis
            emoji_count = len(re.findall(r'[😀-🙏]', comment_text))
            if emoji_count > 10:
                return True
            
            # Check for repeated characters
            if re.search(r'(.)\1{4,}', comment_text):
                return True
            
            # Check commenter info if available
            if commenter_info:
                # New account with suspicious activity
                if commenter_info.get('account_age_days', 365) < 7:
                    if commenter_info.get('follower_count', 100) < 10:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting spam: {str(e)}")
            return False
    
    def categorize_comment(self, comment_text: str, language: str = 'ar') -> str:
        """Categorize the type of comment"""
        comment_lower = comment_text.lower()
        
        # Question indicators
        question_indicators = {
            'ar': ['كيف', 'ماذا', 'متى', 'أين', 'لماذا', 'هل', 'ما', '؟'],
            'en': ['how', 'what', 'when', 'where', 'why', 'can', 'could', 'would', '?']
        }
        
        # Compliment indicators
        compliment_indicators = {
            'ar': ['شكراً', 'رائع', 'ممتاز', 'أحب', 'مفيد', 'جميل'],
            'en': ['thanks', 'great', 'love', 'amazing', 'awesome', 'helpful']
        }
        
        # Criticism indicators
        criticism_indicators = {
            'ar': ['لا أحب', 'سيء', 'خطأ', 'مشكلة', 'غلط'],
            'en': ['hate', 'bad', 'wrong', 'problem', 'terrible']
        }
        
        # Request indicators
        request_indicators = {
            'ar': ['ممكن', 'أريد', 'طلب', 'عايز', 'محتاج'],
            'en': ['please', 'can you', 'could you', 'want', 'need']
        }
        
        indicators = question_indicators.get(language, [])
        if any(indicator in comment_lower for indicator in indicators):
            return 'question'
        
        indicators = compliment_indicators.get(language, [])
        if any(indicator in comment_lower for indicator in indicators):
            return 'compliment'
        
        indicators = criticism_indicators.get(language, [])
        if any(indicator in comment_lower for indicator in indicators):
            return 'criticism'
        
        indicators = request_indicators.get(language, [])
        if any(indicator in comment_lower for indicator in indicators):
            return 'request'
        
        return 'general'
    
    def generate_personalized_response(self, comment_data: Dict) -> Dict:
        """Generate a personalized response to a comment"""
        try:
            comment_text = comment_data['text']
            platform = comment_data['platform']
            language = comment_data.get('language', 'ar')
            commenter_info = comment_data.get('commenter_info', {})
            content_context = comment_data.get('content_context', '')
            
            # Check if spam
            if self.detect_spam(comment_text, commenter_info):
                return {
                    'success': True,
                    'action': 'delete_and_block',
                    'response': None,
                    'reason': 'Spam detected'
                }
            
            # Analyze sentiment
            sentiment_analysis = self.analyze_comment_sentiment(comment_text, language)
            
            # Categorize comment
            comment_category = self.categorize_comment(comment_text, language)
            
            # Generate response using viral engine
            response_result = viral_engine.generate_smart_response(
                comment_text, language, sentiment_analysis['sentiment'], content_context
            )
            
            if not response_result['success']:
                # Fallback to template response
                response_text = self.get_template_response(
                    comment_category, sentiment_analysis['sentiment'], language, commenter_info
                )
            else:
                response_text = response_result['response']
            
            # Customize response for platform
            response_text = self.customize_for_platform(response_text, platform)
            
            # Add personalization
            response_text = self.add_personalization(response_text, commenter_info, language)
            
            # Determine response timing
            response_timing = self.calculate_response_timing(
                sentiment_analysis['sentiment'], comment_category, platform
            )
            
            return {
                'success': True,
                'action': 'respond',
                'response': response_text,
                'timing': response_timing,
                'sentiment': sentiment_analysis['sentiment'],
                'category': comment_category,
                'confidence': sentiment_analysis['confidence'],
                'should_pin': self.should_pin_comment(comment_category, sentiment_analysis),
                'follow_up_actions': self.get_follow_up_actions(comment_category, sentiment_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized response: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_template_response(self, category: str, sentiment: str, language: str, 
                            commenter_info: Dict) -> str:
        """Get template response based on comment category and sentiment"""
        templates = self.response_templates.get(language, {})
        
        # Determine if first-time or regular commenter
        is_first_time = commenter_info.get('previous_comments', 0) == 0
        
        if category == 'question':
            base_responses = [
                'شكراً للسؤال! سأجيب عليه قريباً 🤔',
                'سؤال ممتاز! دعني أوضح لك 💭'
            ] if language == 'ar' else [
                'Thanks for the question! I\'ll answer soon 🤔',
                'Great question! Let me clarify 💭'
            ]
        elif category == 'compliment':
            if is_first_time:
                base_responses = templates.get('first_time_commenter', [])
            else:
                base_responses = templates.get('regular_commenter', [])
        elif category == 'criticism':
            base_responses = [
                'أقدر ملاحظتك، سأحاول التحسين 🙏',
                'شكراً للتوضيح، نقطة مهمة 💭'
            ] if language == 'ar' else [
                'I appreciate your feedback, will try to improve 🙏',
                'Thanks for clarifying, important point 💭'
            ]
        else:
            base_responses = templates.get('engagement_booster', [])
        
        return random.choice(base_responses) if base_responses else 'شكراً لتفاعلك! 😊'
    
    def customize_for_platform(self, response: str, platform: str) -> str:
        """Customize response for specific platform"""
        settings = self.platform_settings.get(platform, {})
        max_length = settings.get('max_response_length', 200)
        emoji_freq = settings.get('emoji_frequency', 'medium')
        
        # Truncate if too long
        if len(response) > max_length:
            response = response[:max_length-3] + '...'
        
        # Adjust emoji usage
        if emoji_freq == 'low':
            # Remove some emojis
            response = re.sub(r'[😀-🙏]{2,}', lambda m: m.group()[0], response)
        elif emoji_freq == 'high':
            # Add more emojis if needed
            if not re.search(r'[😀-🙏]', response):
                response += ' 😊'
        
        return response
    
    def add_personalization(self, response: str, commenter_info: Dict, language: str) -> str:
        """Add personalization to response"""
        if not commenter_info:
            return response
        
        name = commenter_info.get('name', '').split()[0] if commenter_info.get('name') else ''
        
        # Add name if available and appropriate
        if name and len(name) < 15 and name.isalpha():
            if language == 'ar':
                response = f"{name}، {response}"
            else:
                response = f"{name}, {response}"
        
        return response
    
    def calculate_response_timing(self, sentiment: str, category: str, platform: str) -> Dict:
        """Calculate optimal response timing"""
        settings = self.platform_settings.get(platform, {})
        priority_timing = settings.get('priority_response_time', 'normal')
        
        # Adjust timing based on sentiment and category
        if sentiment == 'negative' or category == 'criticism':
            timing_type = 'immediate'  # Respond quickly to negative comments
        elif category == 'question':
            timing_type = 'quick'  # Questions need quick responses
        elif sentiment == 'positive':
            timing_type = priority_timing  # Use platform default for positive
        else:
            timing_type = 'normal'
        
        timing_range = self.response_timing.get(timing_type, (10, 30))
        
        return {
            'type': timing_type,
            'min_minutes': timing_range[0],
            'max_minutes': timing_range[1],
            'scheduled_time': datetime.utcnow() + timedelta(
                minutes=random.randint(timing_range[0], timing_range[1])
            )
        }
    
    def should_pin_comment(self, category: str, sentiment_analysis: Dict) -> bool:
        """Determine if comment should be pinned"""
        # Pin positive questions or very positive comments
        if category == 'question' and sentiment_analysis['sentiment'] == 'positive':
            return True
        
        if sentiment_analysis['sentiment'] == 'positive' and sentiment_analysis['confidence'] > 0.8:
            return True
        
        return False
    
    def get_follow_up_actions(self, category: str, sentiment_analysis: Dict) -> List[str]:
        """Get follow-up actions for the comment"""
        actions = []
        
        if category == 'question':
            actions.append('create_content_about_topic')
            actions.append('add_to_faq')
        
        if sentiment_analysis['sentiment'] == 'positive':
            actions.append('encourage_sharing')
            actions.append('invite_to_community')
        
        if sentiment_analysis['sentiment'] == 'negative':
            actions.append('follow_up_privately')
            actions.append('improve_content')
        
        return actions
    
    def process_comment_batch(self, comments: List[Dict]) -> Dict:
        """Process multiple comments in batch"""
        try:
            results = []
            
            for comment in comments:
                result = self.generate_personalized_response(comment)
                results.append({
                    'comment_id': comment.get('id'),
                    'result': result
                })
            
            # Calculate batch statistics
            total_comments = len(comments)
            successful_responses = len([r for r in results if r['result']['success']])
            spam_detected = len([r for r in results if r['result'].get('action') == 'delete_and_block'])
            
            return {
                'success': True,
                'total_processed': total_comments,
                'successful_responses': successful_responses,
                'spam_detected': spam_detected,
                'results': results,
                'processing_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing comment batch: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_response_analytics(self, timeframe_days: int = 7) -> Dict:
        """Get analytics for auto-responses"""
        try:
            # This would typically query the database for actual metrics
            # For now, we'll return simulated analytics
            
            return {
                'success': True,
                'timeframe_days': timeframe_days,
                'analytics': {
                    'total_comments_processed': 1250,
                    'responses_sent': 1100,
                    'spam_blocked': 150,
                    'response_rate': 88.0,
                    'average_response_time_minutes': 8.5,
                    'sentiment_breakdown': {
                        'positive': 65,
                        'neutral': 25,
                        'negative': 10
                    },
                    'category_breakdown': {
                        'questions': 30,
                        'compliments': 40,
                        'general': 25,
                        'criticism': 5
                    },
                    'platform_breakdown': {
                        'instagram': 35,
                        'tiktok': 30,
                        'youtube': 20,
                        'twitter': 10,
                        'facebook': 5
                    },
                    'engagement_impact': {
                        'comments_generated': 450,
                        'likes_on_responses': 890,
                        'follow_rate_increase': 12.5
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting response analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_response_settings(self, settings: Dict) -> Dict:
        """Update auto-response settings"""
        try:
            # Update timing settings
            if 'response_timing' in settings:
                self.response_timing.update(settings['response_timing'])
            
            # Update platform settings
            if 'platform_settings' in settings:
                for platform, platform_settings in settings['platform_settings'].items():
                    if platform in self.platform_settings:
                        self.platform_settings[platform].update(platform_settings)
            
            # Update response templates
            if 'response_templates' in settings:
                for language, templates in settings['response_templates'].items():
                    if language in self.response_templates:
                        self.response_templates[language].update(templates)
            
            return {
                'success': True,
                'message': 'Auto-response settings updated successfully',
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating response settings: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global auto responder instance
auto_responder = AutoResponder()

