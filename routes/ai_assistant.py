from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from src.models.base import db
from src.models.user import User
from src.models.task import Task
from src.models.content import Content
from src.models.credit_transaction import CreditTransaction
from src.models.subscription import UserSubscription
from src.services.credit_manager import credit_manager
from src.services.task_pricing import pricing_engine
from src.services.external_api_integration import api_integration
import json
import uuid
from datetime import datetime, timedelta
import logging
import google.generativeai as genai
import os

ai_assistant_bp = Blueprint('ai_assistant', __name__)
logger = logging.getLogger(__name__)

# Configure Google Gemini
gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

class AIAssistant:
    """AI Assistant for handling user queries and automating marketing tasks using Google Gemini"""
    
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
                'description_ar': 'استخدام منصات التواصل الاجتماعي للوصول للعملاء',
                'description_en': 'Using social media platforms to reach customers'
            },
            'email_marketing': {
                'name_ar': 'التسويق عبر البريد الإلكتروني',
                'name_en': 'Email Marketing',
                'description_ar': 'إرسال رسائل تسويقية مستهدفة عبر البريد الإلكتروني',
                'description_en': 'Sending targeted marketing messages via email'
            },
            'influencer_marketing': {
                'name_ar': 'التسويق عبر المؤثرين',
                'name_en': 'Influencer Marketing',
                'description_ar': 'التعاون مع المؤثرين للترويج للمنتجات',
                'description_en': 'Collaborating with influencers to promote products'
            },
            'viral_marketing': {
                'name_ar': 'التسويق الفيروسي',
                'name_en': 'Viral Marketing',
                'description_ar': 'إنشاء محتوى قابل للانتشار السريع',
                'description_en': 'Creating content that spreads rapidly'
            }
        }
        
        self.task_types = {
            'content_generation': {
                'name_ar': 'إنشاء المحتوى',
                'name_en': 'Content Generation',
                'credits_required': 5
            },
            'image_generation': {
                'name_ar': 'إنشاء الصور',
                'name_en': 'Image Generation',
                'credits_required': 10
            },
            'video_generation': {
                'name_ar': 'إنشاء الفيديو',
                'name_en': 'Video Generation',
                'credits_required': 20
            },
            'audio_generation': {
                'name_ar': 'إنشاء الصوت',
                'name_en': 'Audio Generation',
                'credits_required': 8
            },
            'campaign_analysis': {
                'name_ar': 'تحليل الحملة',
                'name_en': 'Campaign Analysis',
                'credits_required': 3
            }
        }
    
    async def process_user_query(self, user_id: int, query: str, language: str = 'ar') -> dict:
        """Process user query and provide intelligent response"""
        
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Analyze query intent
            intent_analysis = await self.analyze_query_intent(query, language)
            
            if not intent_analysis['success']:
                return intent_analysis
            
            intent = intent_analysis['intent']
            entities = intent_analysis['entities']
            
            # Route to appropriate handler
            if intent == 'create_content':
                return await self.handle_content_creation(user_id, entities, language)
            elif intent == 'analyze_campaign':
                return await self.handle_campaign_analysis(user_id, entities, language)
            elif intent == 'get_recommendations':
                return await self.handle_recommendations(user_id, entities, language)
            elif intent == 'schedule_task':
                return await self.handle_task_scheduling(user_id, entities, language)
            elif intent == 'general_question':
                return await self.handle_general_question(user_id, query, language)
            else:
                return await self.handle_general_question(user_id, query, language)
        
        except Exception as e:
            logger.error(f"Error processing user query: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_query_intent(self, query: str, language: str = 'ar') -> dict:
        """Analyze user query to determine intent and extract entities"""
        
        try:
            if language == 'ar':
                prompt = f"""أنت مساعد ذكي لتحليل استعلامات المستخدمين في مجال التسويق الرقمي.

حلل الاستعلام التالي وحدد:
1. النية (intent): create_content, analyze_campaign, get_recommendations, schedule_task, general_question
2. الكيانات (entities): المنتج، الخدمة، المنصة، الجمهور المستهدف، إلخ

الاستعلام: "{query}"

أجب بتنسيق JSON:
{{
    "intent": "النية المحددة",
    "entities": {{
        "product": "المنتج إن وجد",
        "platform": "المنصة إن وجدت",
        "audience": "الجمهور المستهدف إن وجد",
        "content_type": "نوع المحتوى إن وجد"
    }},
    "confidence": 0.95
}}"""
            else:
                prompt = f"""You are an intelligent assistant for analyzing user queries in digital marketing.

Analyze the following query and determine:
1. Intent: create_content, analyze_campaign, get_recommendations, schedule_task, general_question
2. Entities: product, service, platform, target audience, etc.

Query: "{query}"

Respond in JSON format:
{{
    "intent": "determined intent",
    "entities": {{
        "product": "product if found",
        "platform": "platform if found",
        "audience": "target audience if found",
        "content_type": "content type if found"
    }},
    "confidence": 0.95
}}"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
                service='google_gemini'
            )
            
            if result['success']:
                response_text = result['data'].get('text', '{}')
                
                # Try to parse JSON response
                try:
                    analysis = json.loads(response_text)
                    return {
                        'success': True,
                        'intent': analysis.get('intent', 'general_question'),
                        'entities': analysis.get('entities', {}),
                        'confidence': analysis.get('confidence', 0.5)
                    }
                except json.JSONDecodeError:
                    # Fallback to simple keyword analysis
                    return self.simple_intent_analysis(query, language)
            else:
                return self.simple_intent_analysis(query, language)
        
        except Exception as e:
            logger.error(f"Error analyzing query intent: {str(e)}")
            return self.simple_intent_analysis(query, language)
    
    def simple_intent_analysis(self, query: str, language: str) -> dict:
        """Simple keyword-based intent analysis as fallback"""
        
        query_lower = query.lower()
        
        # Arabic keywords
        if language == 'ar':
            if any(word in query_lower for word in ['أنشئ', 'اكتب', 'صمم', 'أعمل']):
                return {
                    'success': True,
                    'intent': 'create_content',
                    'entities': {},
                    'confidence': 0.7
                }
            elif any(word in query_lower for word in ['حلل', 'تحليل', 'إحصائيات']):
                return {
                    'success': True,
                    'intent': 'analyze_campaign',
                    'entities': {},
                    'confidence': 0.7
                }
            elif any(word in query_lower for word in ['اقترح', 'نصائح', 'توصيات']):
                return {
                    'success': True,
                    'intent': 'get_recommendations',
                    'entities': {},
                    'confidence': 0.7
                }
        
        # English keywords
        else:
            if any(word in query_lower for word in ['create', 'write', 'design', 'make', 'generate']):
                return {
                    'success': True,
                    'intent': 'create_content',
                    'entities': {},
                    'confidence': 0.7
                }
            elif any(word in query_lower for word in ['analyze', 'analysis', 'statistics', 'performance']):
                return {
                    'success': True,
                    'intent': 'analyze_campaign',
                    'entities': {},
                    'confidence': 0.7
                }
            elif any(word in query_lower for word in ['suggest', 'recommend', 'advice', 'tips']):
                return {
                    'success': True,
                    'intent': 'get_recommendations',
                    'entities': {},
                    'confidence': 0.7
                }
        
        return {
            'success': True,
            'intent': 'general_question',
            'entities': {},
            'confidence': 0.5
        }
    
    async def handle_content_creation(self, user_id: int, entities: dict, language: str) -> dict:
        """Handle content creation requests"""
        
        try:
            user = User.query.get(user_id)
            
            # Check credits
            required_credits = 5  # Base credits for content creation
            if user.credits < required_credits:
                return {
                    'success': False,
                    'error': 'Insufficient credits' if language == 'en' else 'رصيد غير كافي',
                    'required_credits': required_credits,
                    'user_credits': user.credits
                }
            
            # Create task
            task = Task(
                user_id=user_id,
                task_type='content_generation',
                status='pending',
                priority='medium',
                language=language,
                task_data=json.dumps(entities)
            )
            
            db.session.add(task)
            db.session.commit()
            
            # Deduct credits
            credit_manager.deduct_credits(user_id, required_credits, 'Content creation task')
            
            response_text = (
                f"تم إنشاء مهمة إنشاء المحتوى بنجاح. رقم المهمة: {task.id}"
                if language == 'ar' else
                f"Content creation task created successfully. Task ID: {task.id}"
            )
            
            return {
                'success': True,
                'message': response_text,
                'task_id': task.id,
                'credits_used': required_credits,
                'remaining_credits': user.credits - required_credits
            }
        
        except Exception as e:
            logger.error(f"Error handling content creation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def handle_campaign_analysis(self, user_id: int, entities: dict, language: str) -> dict:
        """Handle campaign analysis requests"""
        
        try:
            user = User.query.get(user_id)
            
            # Check credits
            required_credits = 3
            if user.credits < required_credits:
                return {
                    'success': False,
                    'error': 'Insufficient credits' if language == 'en' else 'رصيد غير كافي',
                    'required_credits': required_credits,
                    'user_credits': user.credits
                }
            
            # Get user's recent campaigns
            recent_tasks = Task.query.filter_by(
                user_id=user_id,
                task_type='content_generation'
            ).order_by(Task.created_at.desc()).limit(5).all()
            
            if not recent_tasks:
                return {
                    'success': False,
                    'error': 'No campaigns found to analyze' if language == 'en' else 'لا توجد حملات للتحليل'
                }
            
            # Generate analysis
            analysis_prompt = self.build_analysis_prompt(recent_tasks, language)
            
            result = await api_integration.generate_text(
                prompt=analysis_prompt,
                max_tokens=800,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                analysis_text = result['data'].get('text', '')
                
                # Deduct credits
                credit_manager.deduct_credits(user_id, required_credits, 'Campaign analysis')
                
                return {
                    'success': True,
                    'analysis': analysis_text,
                    'campaigns_analyzed': len(recent_tasks),
                    'credits_used': required_credits,
                    'remaining_credits': user.credits - required_credits
                }
            else:
                return {'success': False, 'error': result.get('error')}
        
        except Exception as e:
            logger.error(f"Error handling campaign analysis: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def build_analysis_prompt(self, tasks: list, language: str) -> str:
        """Build prompt for campaign analysis"""
        
        task_summaries = []
        for task in tasks:
            task_data = json.loads(task.task_data) if task.task_data else {}
            task_summaries.append({
                'id': task.id,
                'type': task.task_type,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'data': task_data
            })
        
        if language == 'ar':
            prompt = f"""أنت خبير في تحليل الحملات التسويقية.

حلل الحملات التالية وقدم تقريراً شاملاً:

الحملات: {json.dumps(task_summaries, ensure_ascii=False, indent=2)}

قدم تحليلاً يتضمن:
1. أداء الحملات العام
2. نقاط القوة والضعف
3. توصيات للتحسين
4. اتجاهات ملاحظة
5. خطة عمل مقترحة

اكتب التحليل بشكل مفصل ومفيد:"""
        else:
            prompt = f"""You are an expert in marketing campaign analysis.

Analyze the following campaigns and provide a comprehensive report:

Campaigns: {json.dumps(task_summaries, indent=2)}

Provide analysis including:
1. Overall campaign performance
2. Strengths and weaknesses
3. Improvement recommendations
4. Observed trends
5. Suggested action plan

Write detailed and useful analysis:"""
        
        return prompt
    
    async def handle_recommendations(self, user_id: int, entities: dict, language: str) -> dict:
        """Handle recommendation requests"""
        
        try:
            user = User.query.get(user_id)
            
            if language == 'ar':
                prompt = f"""أنت خبير تسويق رقمي. قدم توصيات مخصصة للمستخدم:

معلومات المستخدم:
- عدد المهام المكتملة: {Task.query.filter_by(user_id=user_id, status='completed').count()}
- الاستراتيجيات المستخدمة: {entities}

قدم 5 توصيات عملية لتحسين الأداء التسويقي:"""
            else:
                prompt = f"""You are a digital marketing expert. Provide personalized recommendations:

User Information:
- Completed tasks: {Task.query.filter_by(user_id=user_id, status='completed').count()}
- Used strategies: {entities}

Provide 5 practical recommendations to improve marketing performance:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=600,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                recommendations = result['data'].get('text', '')
                
                return {
                    'success': True,
                    'recommendations': recommendations,
                    'personalized': True
                }
            else:
                return {'success': False, 'error': result.get('error')}
        
        except Exception as e:
            logger.error(f"Error handling recommendations: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def handle_task_scheduling(self, user_id: int, entities: dict, language: str) -> dict:
        """Handle task scheduling requests"""
        
        try:
            # Extract scheduling information from entities
            schedule_time = entities.get('time', 'now')
            task_type = entities.get('task_type', 'content_generation')
            
            # Create scheduled task
            task = Task(
                user_id=user_id,
                task_type=task_type,
                status='scheduled',
                priority='medium',
                language=language,
                task_data=json.dumps(entities),
                scheduled_at=datetime.utcnow() + timedelta(hours=1)  # Default to 1 hour later
            )
            
            db.session.add(task)
            db.session.commit()
            
            response_text = (
                f"تم جدولة المهمة بنجاح. رقم المهمة: {task.id}"
                if language == 'ar' else
                f"Task scheduled successfully. Task ID: {task.id}"
            )
            
            return {
                'success': True,
                'message': response_text,
                'task_id': task.id,
                'scheduled_at': task.scheduled_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error handling task scheduling: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def handle_general_question(self, user_id: int, query: str, language: str) -> dict:
        """Handle general marketing questions"""
        
        try:
            if language == 'ar':
                prompt = f"""أنت خبير تسويق رقمي ومساعد ذكي. أجب على السؤال التالي بشكل مفيد ومفصل:

السؤال: {query}

قدم إجابة شاملة تتضمن:
- معلومات مفيدة ودقيقة
- نصائح عملية قابلة للتطبيق
- أمثلة إن أمكن
- خطوات واضحة إذا كان السؤال يتطلب ذلك

الإجابة:"""
            else:
                prompt = f"""You are a digital marketing expert and intelligent assistant. Answer the following question helpfully and in detail:

Question: {query}

Provide a comprehensive answer including:
- Useful and accurate information
- Practical actionable tips
- Examples if possible
- Clear steps if the question requires them

Answer:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                answer = result['data'].get('text', '')
                
                return {
                    'success': True,
                    'answer': answer,
                    'query': query,
                    'language': language
                }
            else:
                return {'success': False, 'error': result.get('error')}
        
        except Exception as e:
            logger.error(f"Error handling general question: {str(e)}")
            return {'success': False, 'error': str(e)}


# Global instance
ai_assistant = AIAssistant()


@ai_assistant_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_assistant():
    """Chat with AI assistant"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        query = data.get('query', '').strip()
        language = data.get('language', 'ar')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required' if language == 'en' else 'الاستعلام مطلوب'
            }), 400
        
        # Process query
        result = ai_assistant.process_user_query(user_id, query, language)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@ai_assistant_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_suggestions():
    """Get personalized suggestions for user"""
    
    try:
        user_id = get_jwt_identity()
        language = request.args.get('language', 'ar')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get user statistics
        completed_tasks = Task.query.filter_by(user_id=user_id, status='completed').count()
        pending_tasks = Task.query.filter_by(user_id=user_id, status='pending').count()
        
        # Generate suggestions based on user activity
        suggestions = []
        
        if completed_tasks == 0:
            if language == 'ar':
                suggestions.extend([
                    "ابدأ بإنشاء أول محتوى تسويقي لك",
                    "جرب إنشاء منشور لوسائل التواصل الاجتماعي",
                    "اكتشف استراتيجيات التسويق المختلفة"
                ])
            else:
                suggestions.extend([
                    "Start by creating your first marketing content",
                    "Try creating a social media post",
                    "Explore different marketing strategies"
                ])
        
        elif completed_tasks < 5:
            if language == 'ar':
                suggestions.extend([
                    "جرب إنشاء محتوى بصري جذاب",
                    "حلل أداء حملاتك السابقة",
                    "اكتشف جمهورك المستهدف"
                ])
            else:
                suggestions.extend([
                    "Try creating engaging visual content",
                    "Analyze your previous campaigns",
                    "Discover your target audience"
                ])
        
        else:
            if language == 'ar':
                suggestions.extend([
                    "أنشئ استراتيجية تسويق متقدمة",
                    "جدول مهامك التسويقية",
                    "اكتشف الاتجاهات الجديدة في السوق"
                ])
            else:
                suggestions.extend([
                    "Create an advanced marketing strategy",
                    "Schedule your marketing tasks",
                    "Discover new market trends"
                ])
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'user_stats': {
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'credits': user.credits
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@ai_assistant_bp.route('/quick-actions', methods=['GET'])
@jwt_required()
def get_quick_actions():
    """Get quick actions for user"""
    
    try:
        language = request.args.get('language', 'ar')
        
        if language == 'ar':
            quick_actions = [
                {
                    'id': 'create_post',
                    'title': 'إنشاء منشور',
                    'description': 'أنشئ منشور جذاب لوسائل التواصل الاجتماعي',
                    'icon': 'edit',
                    'credits': 5
                },
                {
                    'id': 'generate_image',
                    'title': 'إنشاء صورة',
                    'description': 'أنشئ صورة تسويقية احترافية',
                    'icon': 'image',
                    'credits': 10
                },
                {
                    'id': 'analyze_campaign',
                    'title': 'تحليل الحملة',
                    'description': 'احصل على تحليل مفصل لحملاتك',
                    'icon': 'analytics',
                    'credits': 3
                },
                {
                    'id': 'get_recommendations',
                    'title': 'احصل على توصيات',
                    'description': 'احصل على نصائح مخصصة لتحسين أدائك',
                    'icon': 'lightbulb',
                    'credits': 2
                }
            ]
        else:
            quick_actions = [
                {
                    'id': 'create_post',
                    'title': 'Create Post',
                    'description': 'Create engaging social media post',
                    'icon': 'edit',
                    'credits': 5
                },
                {
                    'id': 'generate_image',
                    'title': 'Generate Image',
                    'description': 'Create professional marketing image',
                    'icon': 'image',
                    'credits': 10
                },
                {
                    'id': 'analyze_campaign',
                    'title': 'Analyze Campaign',
                    'description': 'Get detailed analysis of your campaigns',
                    'icon': 'analytics',
                    'credits': 3
                },
                {
                    'id': 'get_recommendations',
                    'title': 'Get Recommendations',
                    'description': 'Get personalized tips to improve performance',
                    'icon': 'lightbulb',
                    'credits': 2
                }
            ]
        
        return jsonify({
            'success': True,
            'quick_actions': quick_actions
        })
    
    except Exception as e:
        logger.error(f"Error getting quick actions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

