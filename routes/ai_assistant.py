from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from src.models.base import db
from src.models.user import User
from src.models.task import Task
from src.models.content import Content
from src.models.credit_transaction import CreditTransaction
from src.models.subscription import UserSubscription
from src.services.credit_manager import credit_manager
from src.services.task_pricing import pricing_engine
import json
import uuid
from datetime import datetime, timedelta
import logging
import openai
import os

ai_assistant_bp = Blueprint('ai_assistant', __name__)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

class AIAssistant:
    """AI Assistant for handling user queries and automating marketing tasks"""
    
    def __init__(self):
        self.supported_languages = {
            'ar': 'العربية',
            'en': 'English', 
            'fr': 'Français',
            'es': 'Español',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語'
        }
        
        self.marketing_strategies = {
            'content_marketing': {
                'name_ar': 'تسويق المحتوى',
                'name_en': 'Content Marketing',
                'description_ar': 'إنشاء محتوى قيم وجذاب لجذب العملاء',
                'description_en': 'Creating valuable and engaging content to attract customers'
            },
            'social_media_marketing': {
                'name_ar': 'التسويق عبر وسائل التواصل الاجتماعي',
                'name_en': 'Social Media Marketing',
                'description_ar': 'استخدام منصات التواصل للوصول للجمهور المستهدف',
                'description_en': 'Using social platforms to reach target audience'
            },
            'influencer_marketing': {
                'name_ar': 'التسويق عبر المؤثرين',
                'name_en': 'Influencer Marketing',
                'description_ar': 'التعاون مع المؤثرين للترويج للمنتجات',
                'description_en': 'Collaborating with influencers to promote products'
            },
            'email_marketing': {
                'name_ar': 'التسويق عبر البريد الإلكتروني',
                'name_en': 'Email Marketing',
                'description_ar': 'إرسال رسائل مخصصة للعملاء المحتملين',
                'description_en': 'Sending personalized messages to potential customers'
            },
            'seo_marketing': {
                'name_ar': 'تحسين محركات البحث',
                'name_en': 'SEO Marketing',
                'description_ar': 'تحسين المحتوى للظهور في نتائج البحث',
                'description_en': 'Optimizing content for search engine visibility'
            },
            'paid_advertising': {
                'name_ar': 'الإعلانات المدفوعة',
                'name_en': 'Paid Advertising',
                'description_ar': 'إنشاء حملات إعلانية مستهدفة',
                'description_en': 'Creating targeted advertising campaigns'
            },
            'viral_marketing': {
                'name_ar': 'التسويق الفيروسي',
                'name_en': 'Viral Marketing',
                'description_ar': 'إنشاء محتوى قابل للانتشار السريع',
                'description_en': 'Creating content designed to spread rapidly'
            },
            'brand_storytelling': {
                'name_ar': 'سرد قصة العلامة التجارية',
                'name_en': 'Brand Storytelling',
                'description_ar': 'بناء هوية العلامة التجارية من خلال القصص',
                'description_en': 'Building brand identity through storytelling'
            }
        }
    
    def detect_language(self, text):
        """Detect the language of the input text"""
        # Simple language detection based on common words and characters
        arabic_chars = len([c for c in text if '\u0600' <= c <= '\u06FF'])
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return 'en'
        
        arabic_ratio = arabic_chars / total_chars
        
        if arabic_ratio > 0.3:
            return 'ar'
        
        # Check for other language indicators
        if any(word in text.lower() for word in ['the', 'and', 'is', 'are', 'this', 'that']):
            return 'en'
        elif any(word in text.lower() for word in ['le', 'la', 'et', 'est', 'sont', 'ce', 'cette']):
            return 'fr'
        elif any(word in text.lower() for word in ['el', 'la', 'y', 'es', 'son', 'este', 'esta']):
            return 'es'
        elif any(word in text.lower() for word in ['der', 'die', 'das', 'und', 'ist', 'sind', 'dieser']):
            return 'de'
        
        return 'en'  # Default to English
    
    def get_system_prompt(self, language='ar', user_context=None):
        """Get system prompt based on language and user context"""
        
        if language == 'ar':
            base_prompt = """أنت مساعد ذكي متخصص في التسويق الآلي. مهمتك هي مساعدة المستخدمين في:

1. إنشاء محتوى تسويقي (نصوص، صور، فيديوهات)
2. إدارة حملات التسويق عبر منصات التواصل الاجتماعي
3. تحليل الأداء وتقديم التوصيات
4. اقتراح استراتيجيات تسويقية مناسبة
5. إنشاء هاشتاجات وكلمات مفتاحية
6. تحديد أفضل أوقات النشر
7. اكتشاف التريندات الحالية

الاستراتيجيات التسويقية المتاحة:
- تسويق المحتوى
- التسويق عبر وسائل التواصل الاجتماعي  
- التسويق عبر المؤثرين
- التسويق عبر البريد الإلكتروني
- تحسين محركات البحث
- الإعلانات المدفوعة
- التسويق الفيروسي
- سرد قصة العلامة التجارية

المنصات المدعومة: فيسبوك، انستجرام، تيك توك، يوتيوب، تويتر، لينكد إن

اللغات المدعومة: العربية، الإنجليزية، الفرنسية، الإسبانية، الألمانية، الإيطالية، البرتغالية، الروسية، الصينية، اليابانية

كن مفيداً ومحترفاً في ردودك."""

        else:  # English
            base_prompt = """You are an intelligent marketing automation assistant. Your role is to help users with:

1. Creating marketing content (text, images, videos)
2. Managing social media marketing campaigns
3. Analyzing performance and providing recommendations
4. Suggesting appropriate marketing strategies
5. Creating hashtags and keywords
6. Determining optimal posting times
7. Discovering current trends

Available Marketing Strategies:
- Content Marketing
- Social Media Marketing
- Influencer Marketing
- Email Marketing
- SEO Marketing
- Paid Advertising
- Viral Marketing
- Brand Storytelling

Supported Platforms: Facebook, Instagram, TikTok, YouTube, Twitter, LinkedIn

Supported Languages: Arabic, English, French, Spanish, German, Italian, Portuguese, Russian, Chinese, Japanese

Be helpful and professional in your responses."""

        if user_context:
            context_info = f"\n\nUser Context:\n"
            if user_context.get('business_type'):
                context_info += f"Business Type: {user_context['business_type']}\n"
            if user_context.get('target_audience'):
                context_info += f"Target Audience: {user_context['target_audience']}\n"
            if user_context.get('preferred_platforms'):
                context_info += f"Preferred Platforms: {', '.join(user_context['preferred_platforms'])}\n"
            if user_context.get('budget_range'):
                context_info += f"Budget Range: {user_context['budget_range']}\n"
            
            base_prompt += context_info
        
        return base_prompt
    
    async def process_message(self, message, user_id=None, session_id=None, language=None):
        """Process user message and generate appropriate response"""
        
        try:
            # Detect language if not provided
            if not language:
                language = self.detect_language(message)
            
            # Get user context if user_id provided
            user_context = None
            if user_id:
                user = User.get_by_id(user_id)
                if user:
                    user_context = {
                        'business_type': user.business_type,
                        'target_audience': user.target_audience,
                        'preferred_platforms': user.get_preferred_platforms(),
                        'subscription_status': user.subscription_status
                    }
            
            # Check if this is a task creation request
            task_intent = self.analyze_task_intent(message, language)
            
            if task_intent:
                return await self.handle_task_creation(task_intent, user_id, language)
            
            # Generate AI response
            system_prompt = self.get_system_prompt(language, user_context)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Add suggestions for common actions
            suggestions = self.get_action_suggestions(message, language)
            
            return {
                'success': True,
                'response': ai_response,
                'language': language,
                'suggestions': suggestions,
                'session_id': session_id or str(uuid.uuid4())
            }
            
        except Exception as e:
            logger.error(f"Error processing AI message: {str(e)}")
            
            error_message = "عذراً، حدث خطأ في معالجة رسالتك. يرجى المحاولة مرة أخرى." if language == 'ar' else "Sorry, there was an error processing your message. Please try again."
            
            return {
                'success': False,
                'error': error_message,
                'language': language
            }
    
    def analyze_task_intent(self, message, language):
        """Analyze if the message contains a task creation intent"""
        
        task_keywords = {
            'ar': {
                'content_creation': ['أنشئ', 'اكتب', 'صمم', 'محتوى', 'منشور', 'إعلان'],
                'image_generation': ['صورة', 'تصميم', 'لوجو', 'بانر', 'جرافيك'],
                'video_creation': ['فيديو', 'مقطع', 'ريل', 'قصة'],
                'campaign_creation': ['حملة', 'استراتيجية', 'خطة تسويقية'],
                'hashtag_generation': ['هاشتاج', 'علامة', 'كلمات مفتاحية'],
                'analysis': ['حلل', 'تحليل', 'إحصائيات', 'أداء']
            },
            'en': {
                'content_creation': ['create', 'write', 'design', 'content', 'post', 'ad'],
                'image_generation': ['image', 'design', 'logo', 'banner', 'graphic'],
                'video_creation': ['video', 'clip', 'reel', 'story'],
                'campaign_creation': ['campaign', 'strategy', 'marketing plan'],
                'hashtag_generation': ['hashtag', 'tag', 'keywords'],
                'analysis': ['analyze', 'analysis', 'statistics', 'performance']
            }
        }
        
        keywords = task_keywords.get(language, task_keywords['en'])
        message_lower = message.lower()
        
        for task_type, words in keywords.items():
            if any(word in message_lower for word in words):
                return {
                    'type': task_type,
                    'message': message,
                    'language': language
                }
        
        return None
    
    async def handle_task_creation(self, task_intent, user_id, language):
        """Handle automatic task creation based on user intent"""
        
        if not user_id:
            return {
                'success': False,
                'error': 'يجب تسجيل الدخول لإنشاء المهام' if language == 'ar' else 'Login required to create tasks',
                'login_required': True
            }
        
        # Estimate task cost
        task_data = {
            'content': task_intent['message'],
            'language': language,
            'platforms': ['facebook', 'instagram']  # Default platforms
        }
        
        cost_estimate = pricing_engine.calculate_task_cost(task_intent['type'], task_data, user_id)
        
        if not cost_estimate['success']:
            return {
                'success': False,
                'error': 'خطأ في تقدير تكلفة المهمة' if language == 'ar' else 'Error estimating task cost'
            }
        
        # Check user credits
        credit_check = credit_manager.check_user_credits(user_id, cost_estimate['final_cost'])
        
        if not credit_check['has_enough_credits']:
            return {
                'success': False,
                'error': f"رصيد غير كافي. المطلوب: {cost_estimate['final_cost']} كريديت" if language == 'ar' else f"Insufficient credits. Required: {cost_estimate['final_cost']} credits",
                'required_credits': cost_estimate['final_cost'],
                'current_balance': credit_check['current_balance'],
                'credit_shortage': True
            }
        
        # Create task
        task = Task(
            user_id=user_id,
            title=f"مهمة {task_intent['type']}" if language == 'ar' else f"{task_intent['type']} Task",
            description=task_intent['message'],
            task_type=task_intent['type'],
            category='ai_generated',
            estimated_credits=cost_estimate['final_cost'],
            priority='medium'
        )
        
        task.set_input_data(task_data)
        task.save()
        
        # Deduct credits
        credit_result = credit_manager.deduct_credits(
            user_id=user_id,
            amount=cost_estimate['final_cost'],
            description=f"AI Assistant Task: {task_intent['type']}",
            category='task_execution',
            task_id=task.id
        )
        
        if not credit_result['success']:
            # Delete task if credit deduction failed
            db.session.delete(task)
            db.session.commit()
            
            return {
                'success': False,
                'error': 'فشل في خصم الكريديت' if language == 'ar' else 'Failed to deduct credits'
            }
        
        response_text = f"تم إنشاء المهمة بنجاح! سيتم تنفيذها قريباً.\nرقم المهمة: {task.id}\nالتكلفة: {cost_estimate['final_cost']} كريديت" if language == 'ar' else f"Task created successfully! It will be executed soon.\nTask ID: {task.id}\nCost: {cost_estimate['final_cost']} credits"
        
        return {
            'success': True,
            'response': response_text,
            'task_created': True,
            'task_id': task.id,
            'cost': cost_estimate['final_cost'],
            'new_balance': credit_result['new_balance']
        }
    
    def get_action_suggestions(self, message, language):
        """Get action suggestions based on message content"""
        
        suggestions = []
        message_lower = message.lower()
        
        if language == 'ar':
            if any(word in message_lower for word in ['محتوى', 'منشور', 'كتابة']):
                suggestions.extend([
                    {'text': 'إنشاء محتوى لفيسبوك', 'action': 'create_facebook_content'},
                    {'text': 'إنشاء محتوى لانستجرام', 'action': 'create_instagram_content'},
                    {'text': 'إنشاء محتوى لتيك توك', 'action': 'create_tiktok_content'}
                ])
            
            if any(word in message_lower for word in ['صورة', 'تصميم', 'لوجو']):
                suggestions.extend([
                    {'text': 'توليد صورة بالذكاء الاصطناعي', 'action': 'generate_image'},
                    {'text': 'تصميم لوجو', 'action': 'design_logo'},
                    {'text': 'إنشاء بانر إعلاني', 'action': 'create_banner'}
                ])
            
            if any(word in message_lower for word in ['فيديو', 'مقطع', 'ريل']):
                suggestions.extend([
                    {'text': 'إنشاء فيديو قصير', 'action': 'create_short_video'},
                    {'text': 'إنشاء فيديو ترويجي', 'action': 'create_promo_video'}
                ])
            
            if any(word in message_lower for word in ['هاشتاج', 'كلمات', 'مفتاحية']):
                suggestions.extend([
                    {'text': 'توليد هاشتاجات', 'action': 'generate_hashtags'},
                    {'text': 'بحث كلمات مفتاحية', 'action': 'keyword_research'}
                ])
        
        else:  # English
            if any(word in message_lower for word in ['content', 'post', 'write']):
                suggestions.extend([
                    {'text': 'Create Facebook content', 'action': 'create_facebook_content'},
                    {'text': 'Create Instagram content', 'action': 'create_instagram_content'},
                    {'text': 'Create TikTok content', 'action': 'create_tiktok_content'}
                ])
            
            if any(word in message_lower for word in ['image', 'design', 'logo']):
                suggestions.extend([
                    {'text': 'Generate AI image', 'action': 'generate_image'},
                    {'text': 'Design logo', 'action': 'design_logo'},
                    {'text': 'Create banner', 'action': 'create_banner'}
                ])
            
            if any(word in message_lower for word in ['video', 'clip', 'reel']):
                suggestions.extend([
                    {'text': 'Create short video', 'action': 'create_short_video'},
                    {'text': 'Create promo video', 'action': 'create_promo_video'}
                ])
            
            if any(word in message_lower for word in ['hashtag', 'keywords', 'tags']):
                suggestions.extend([
                    {'text': 'Generate hashtags', 'action': 'generate_hashtags'},
                    {'text': 'Keyword research', 'action': 'keyword_research'}
                ])
        
        return suggestions[:5]  # Limit to 5 suggestions

# Global AI Assistant instance
ai_assistant = AIAssistant()

@ai_assistant_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for AI Assistant"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        language = data.get('language')
        
        # Process message asynchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            ai_assistant.process_message(message, user_id, session_id, language)
        )
        
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_assistant_bp.route('/quick-action', methods=['POST'])
def quick_action():
    """Handle quick action buttons"""
    try:
        data = request.get_json()
        action = data.get('action')
        user_id = data.get('user_id')
        language = data.get('language', 'ar')
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400
        
        # Map actions to task types
        action_mapping = {
            'create_facebook_content': 'social_media_post',
            'create_instagram_content': 'social_media_post',
            'create_tiktok_content': 'social_media_post',
            'generate_image': 'image_generation',
            'design_logo': 'logo_design',
            'create_banner': 'banner_creation',
            'create_short_video': 'video_generation',
            'create_promo_video': 'promotional_video',
            'generate_hashtags': 'hashtag_generation',
            'keyword_research': 'hashtag_research'
        }
        
        task_type = action_mapping.get(action)
        if not task_type:
            return jsonify({
                'success': False,
                'error': 'Invalid action'
            }), 400
        
        # Create task intent
        task_intent = {
            'type': task_type,
            'message': f"Quick action: {action}",
            'language': language
        }
        
        # Process task creation
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            ai_assistant.handle_task_creation(task_intent, user_id, language)
        )
        
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in quick action endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_assistant_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages"""
    return jsonify({
        'success': True,
        'languages': ai_assistant.supported_languages
    })

@ai_assistant_bp.route('/strategies', methods=['GET'])
def get_marketing_strategies():
    """Get list of available marketing strategies"""
    language = request.args.get('language', 'ar')
    
    strategies = {}
    for key, strategy in ai_assistant.marketing_strategies.items():
        strategies[key] = {
            'name': strategy.get(f'name_{language}', strategy['name_en']),
            'description': strategy.get(f'description_{language}', strategy['description_en'])
        }
    
    return jsonify({
        'success': True,
        'strategies': strategies
    })

@ai_assistant_bp.route('/user-context', methods=['POST'])
@jwt_required()
def update_user_context():
    """Update user context for better AI responses"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        
        # Update user profile with context
        if 'business_type' in data:
            user.business_type = data['business_type']
        
        if 'target_audience' in data:
            user.target_audience = data['target_audience']
        
        if 'preferred_platforms' in data:
            user.set_preferred_platforms(data['preferred_platforms'])
        
        if 'marketing_goals' in data:
            user.set_marketing_goals(data['marketing_goals'])
        
        user.save()
        
        return jsonify({
            'success': True,
            'message': 'User context updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating user context: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_assistant_bp.route('/session/<session_id>/history', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        # In a real implementation, you would store chat history in database
        # For now, return empty history
        return jsonify({
            'success': True,
            'history': [],
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

