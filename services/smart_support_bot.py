import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.models.support_chat import SupportChat, SupportMessage, SupportKnowledgeBase
from src.models.user import User
from src.models.subscription import SubscriptionPlan as Subscription
from src.models.base import db

logger = logging.getLogger(__name__)

class SmartSupportBot:
    """Smart AI support bot for customer service"""
    
    def __init__(self):
        self.intents = {
            'greeting': ['مرحبا', 'السلام عليكم', 'أهلا', 'hello', 'hi', 'hey'],
            'pricing': ['سعر', 'تكلفة', 'كم', 'price', 'cost', 'how much', 'باقة', 'اشتراك'],
            'features': ['ميزات', 'خصائص', 'يعمل ايه', 'features', 'what does', 'capabilities'],
            'technical': ['مشكلة', 'خطأ', 'لا يعمل', 'error', 'problem', 'issue', 'bug'],
            'billing': ['فاتورة', 'دفع', 'payment', 'billing', 'invoice', 'charge'],
            'account': ['حساب', 'تسجيل', 'دخول', 'account', 'login', 'register', 'profile'],
            'integration': ['ربط', 'تكامل', 'integration', 'connect', 'odoo', 'api'],
            'support': ['مساعدة', 'دعم', 'help', 'support', 'assistance'],
            'goodbye': ['شكرا', 'وداع', 'مع السلامة', 'thanks', 'bye', 'goodbye']
        }
        
        self.responses = {
            'ar': {
                'greeting': [
                    'مرحباً بك! 👋 أنا مساعدك الذكي في نظام التسويق الآلي. كيف يمكنني مساعدتك اليوم؟',
                    'أهلاً وسهلاً! 😊 أنا هنا لمساعدتك في أي استفسار حول النظام. ما الذي تحتاج إليه؟',
                    'السلام عليكم ورحمة الله! 🌟 كيف يمكنني خدمتك اليوم؟'
                ],
                'pricing': [
                    'بخصوص الأسعار والباقات، يمكنك مراجعة جميع الخطط المتاحة في صفحة الباقات الرسمية. هل تريد أن أوجهك إليها؟',
                    'لدينا باقات متنوعة تناسب جميع الاحتياجات. للاطلاع على الأسعار الحالية، يرجى زيارة صفحة الباقات أو التواصل مع فريق المبيعات.',
                    'الأسعار تختلف حسب الباقة والميزات المطلوبة. هل تريد أن أساعدك في اختيار الباقة المناسبة لاحتياجاتك؟'
                ],
                'features': [
                    'نظامنا يوفر العديد من الميزات الرائعة:\n• إنشاء المحتوى بالذكاء الاصطناعي\n• النشر التلقائي على جميع المنصات\n• تحليل الأداء والتحسين\n• نظام الكريديت المرن\n• دعم 10 لغات\n\nأي ميزة تريد معرفة المزيد عنها؟',
                    'يمكن للنظام أن يساعدك في:\n✅ إنشاء صور وفيديوهات احترافية\n✅ كتابة محتوى تسويقي جذاب\n✅ النشر على فيسبوك وانستجرام وتيك توك ويوتيوب\n✅ تتبع النتائج وتحسين الأداء\n\nهل تريد تجربة مجانية؟'
                ],
                'technical': [
                    'أعتذر عن أي مشكلة تواجهها. يمكنني مساعدتك في حل المشاكل الشائعة. ما هي المشكلة تحديداً؟',
                    'دعني أساعدك في حل هذه المشكلة. هل يمكنك وصف ما يحدث بالتفصيل؟',
                    'سأحاول مساعدتك فوراً. ما هي الخطوات التي قمت بها قبل حدوث المشكلة؟'
                ],
                'billing': [
                    'بخصوص الفواتير والمدفوعات، يمكنك مراجعة حسابك أو التواصل مع قسم المحاسبة للحصول على مساعدة مفصلة.',
                    'لأي استفسارات حول الفواتير، يرجى التواصل مع فريق المحاسبة الذي سيساعدك في حل أي مشكلة متعلقة بالدفع.',
                    'يمكنني توجيهك لقسم المحاسبة للحصول على مساعدة دقيقة حول فاتورتك. هل تريد أن أحولك إليهم؟'
                ],
                'account': [
                    'يمكنني مساعدتك في مسائل الحساب. ما الذي تحتاج إليه تحديداً؟ تسجيل دخول، إنشاء حساب جديد، أم تحديث البيانات؟',
                    'بخصوص حسابك، يمكنني مساعدتك في معظم الأمور. ما هو استفسارك؟',
                    'أنا هنا لمساعدتك في إدارة حسابك. ما الذي تريد القيام به؟'
                ],
                'integration': [
                    'نعم، نظامنا يتكامل بسهولة مع Odoo وأنظمة أخرى عبر APIs آمنة. هل تحتاج مساعدة في عملية الربط؟',
                    'التكامل مع الأنظمة الأخرى سهل وآمن. يمكنني توجيهك للدليل التقني أو ربطك بفريق التطوير للمساعدة.',
                    'لدينا APIs قوية للتكامل مع معظم الأنظمة. ما هو النظام الذي تريد ربطه؟'
                ],
                'support': [
                    'أنا هنا لمساعدتك! ما هو استفسارك أو المشكلة التي تواجهها؟',
                    'بالطبع سأساعدك. يرجى توضيح ما تحتاج إليه وسأبذل قصارى جهدي لمساعدتك.',
                    'أخبرني كيف يمكنني مساعدتك وسأقوم بذلك فوراً!'
                ],
                'goodbye': [
                    'شكراً لك! إذا احتجت أي مساعدة أخرى، أنا هنا دائماً. 😊',
                    'كان من دواعي سروري مساعدتك! لا تتردد في العودة إذا احتجت أي شيء.',
                    'أتمنى أن أكون قد ساعدتك. وداعاً وأراك قريباً! 👋'
                ],
                'unknown': [
                    'أعتذر، لم أفهم استفسارك بوضوح. هل يمكنك إعادة صياغته أو اختيار من الخيارات التالية؟',
                    'يمكنني مساعدتك بشكل أفضل إذا وضحت استفسارك أكثر. ما الذي تحتاج إليه تحديداً؟',
                    'دعني أساعدك بطريقة أفضل. هل استفسارك حول: الأسعار، الميزات، المشاكل التقنية، أم شيء آخر؟'
                ]
            },
            'en': {
                'greeting': [
                    'Hello! 👋 I\'m your smart assistant for the Marketing Automation System. How can I help you today?',
                    'Welcome! 😊 I\'m here to help you with any questions about our system. What do you need?',
                    'Hi there! 🌟 How can I assist you today?'
                ],
                'pricing': [
                    'For pricing and plans, please check our official pricing page for all available packages. Would you like me to direct you there?',
                    'We have various packages to suit all needs. For current pricing, please visit our pricing page or contact our sales team.',
                    'Pricing varies based on the package and required features. Would you like me to help you choose the right plan for your needs?'
                ],
                'features': [
                    'Our system offers many amazing features:\n• AI-powered content creation\n• Automatic posting to all platforms\n• Performance analysis and optimization\n• Flexible credit system\n• Support for 10 languages\n\nWhich feature would you like to know more about?',
                    'The system can help you with:\n✅ Creating professional images and videos\n✅ Writing engaging marketing content\n✅ Posting to Facebook, Instagram, TikTok, and YouTube\n✅ Tracking results and improving performance\n\nWould you like a free trial?'
                ],
                'technical': [
                    'I apologize for any issues you\'re experiencing. I can help you solve common problems. What exactly is the issue?',
                    'Let me help you resolve this problem. Can you describe what\'s happening in detail?',
                    'I\'ll try to help you right away. What steps did you take before the problem occurred?'
                ],
                'billing': [
                    'For billing and payment inquiries, you can check your account or contact our accounting department for detailed assistance.',
                    'For any billing questions, please contact our accounting team who will help you resolve any payment-related issues.',
                    'I can direct you to our accounting department for accurate help with your billing. Would you like me to transfer you?'
                ],
                'account': [
                    'I can help you with account matters. What specifically do you need? Login, creating a new account, or updating information?',
                    'Regarding your account, I can help with most things. What\'s your question?',
                    'I\'m here to help you manage your account. What would you like to do?'
                ],
                'integration': [
                    'Yes, our system integrates easily with Odoo and other systems via secure APIs. Do you need help with the integration process?',
                    'Integration with other systems is easy and secure. I can direct you to the technical guide or connect you with our development team.',
                    'We have powerful APIs for integration with most systems. Which system do you want to connect?'
                ],
                'support': [
                    'I\'m here to help! What\'s your question or the issue you\'re facing?',
                    'Of course I\'ll help you. Please clarify what you need and I\'ll do my best to assist you.',
                    'Tell me how I can help you and I\'ll do it right away!'
                ],
                'goodbye': [
                    'Thank you! If you need any other help, I\'m always here. 😊',
                    'It was my pleasure helping you! Don\'t hesitate to come back if you need anything.',
                    'I hope I was able to help you. Goodbye and see you soon! 👋'
                ],
                'unknown': [
                    'I apologize, I didn\'t understand your question clearly. Can you rephrase it or choose from the following options?',
                    'I can help you better if you clarify your question more. What exactly do you need?',
                    'Let me help you better. Is your question about: pricing, features, technical issues, or something else?'
                ]
            }
        }

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        # Simple language detection based on character patterns
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))
        
        if total_chars == 0:
            return 'ar'  # Default to Arabic
            
        arabic_ratio = arabic_chars / total_chars
        return 'ar' if arabic_ratio > 0.3 else 'en'

    def detect_intent(self, text: str) -> str:
        """Detect the intent of the user message"""
        text_lower = text.lower()
        
        # Check each intent
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return intent
        
        return 'unknown'

    def get_user_context(self, user_id: Optional[int]) -> Dict:
        """Get user context for personalized responses"""
        context = {
            'is_registered': False,
            'subscription_status': 'none',
            'credits_balance': 0,
            'last_activity': None,
            'preferred_language': 'ar'
        }
        
        if user_id:
            try:
                user = User.query.get(user_id)
                if user:
                    context.update({
                        'is_registered': True,
                        'name': user.name,
                        'email': user.email,
                        'credits_balance': user.credits_balance,
                        'last_activity': user.last_activity,
                        'preferred_language': user.preferred_language or 'ar'
                    })
                    
                    # Get subscription info
                    subscription = Subscription.query.filter_by(user_id=user_id, is_active=True).first()
                    if subscription:
                        context['subscription_status'] = subscription.plan_type
                        context['subscription_expires'] = subscription.expires_at
                        
            except Exception as e:
                logger.error(f"Error getting user context: {str(e)}")
        
        return context

    def search_knowledge_base(self, query: str, language: str) -> Optional[str]:
        """Search the knowledge base for relevant answers"""
        try:
            # First, try exact keyword matching
            kb_entries = SupportKnowledgeBase.query.filter(
                SupportKnowledgeBase.language == language,
                SupportKnowledgeBase.is_active == True
            ).all()
            
            query_lower = query.lower()
            best_match = None
            best_score = 0
            
            for entry in kb_entries:
                if entry.keywords:
                    keywords = [k.strip().lower() for k in entry.keywords.split(',')]
                    score = sum(1 for keyword in keywords if keyword in query_lower)
                    
                    if score > best_score:
                        best_score = score
                        best_match = entry
            
            if best_match and best_score > 0:
                # Update usage statistics
                best_match.usage_count += 1
                db.session.commit()
                return best_match.answer
                
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
        
        return None

    def generate_response(self, message: str, user_id: Optional[int] = None, 
                         session_id: Optional[str] = None) -> Dict:
        """Generate AI response to user message"""
        try:
            # Detect language and intent
            language = self.detect_language(message)
            intent = self.detect_intent(message)
            
            # Get user context
            user_context = self.get_user_context(user_id)
            
            # Search knowledge base first
            kb_answer = self.search_knowledge_base(message, language)
            if kb_answer:
                return {
                    'success': True,
                    'response': kb_answer,
                    'intent': intent,
                    'language': language,
                    'confidence': 0.9,
                    'source': 'knowledge_base',
                    'suggested_actions': self.get_suggested_actions(intent, user_context)
                }
            
            # Generate response based on intent
            if intent in self.responses[language]:
                import random
                response = random.choice(self.responses[language][intent])
                
                # Personalize response if user is registered
                if user_context['is_registered'] and 'name' in user_context:
                    if intent == 'greeting':
                        response = f"مرحباً {user_context['name']}! " + response if language == 'ar' else f"Hello {user_context['name']}! " + response
                
                return {
                    'success': True,
                    'response': response,
                    'intent': intent,
                    'language': language,
                    'confidence': 0.8,
                    'source': 'predefined',
                    'suggested_actions': self.get_suggested_actions(intent, user_context)
                }
            else:
                # Unknown intent
                import random
                response = random.choice(self.responses[language]['unknown'])
                
                return {
                    'success': True,
                    'response': response,
                    'intent': 'unknown',
                    'language': language,
                    'confidence': 0.3,
                    'source': 'fallback',
                    'suggested_actions': self.get_common_actions(language)
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': 'أعتذر، حدث خطأ. يرجى المحاولة مرة أخرى.' if language == 'ar' else 'Sorry, an error occurred. Please try again.'
            }

    def get_suggested_actions(self, intent: str, user_context: Dict) -> List[Dict]:
        """Get suggested actions based on intent and user context"""
        actions = []
        
        if intent == 'pricing':
            actions.extend([
                {'type': 'view_pricing', 'label': 'عرض الباقات' if user_context.get('preferred_language', 'ar') == 'ar' else 'View Pricing'},
                {'type': 'contact_sales', 'label': 'التواصل مع المبيعات' if user_context.get('preferred_language', 'ar') == 'ar' else 'Contact Sales'},
                {'type': 'free_trial', 'label': 'تجربة مجانية' if user_context.get('preferred_language', 'ar') == 'ar' else 'Free Trial'}
            ])
        
        elif intent == 'features':
            actions.extend([
                {'type': 'demo', 'label': 'عرض توضيحي' if user_context.get('preferred_language', 'ar') == 'ar' else 'Demo'},
                {'type': 'documentation', 'label': 'الدليل' if user_context.get('preferred_language', 'ar') == 'ar' else 'Documentation'},
                {'type': 'free_trial', 'label': 'تجربة مجانية' if user_context.get('preferred_language', 'ar') == 'ar' else 'Free Trial'}
            ])
        
        elif intent == 'technical':
            actions.extend([
                {'type': 'troubleshooting', 'label': 'دليل حل المشاكل' if user_context.get('preferred_language', 'ar') == 'ar' else 'Troubleshooting Guide'},
                {'type': 'contact_support', 'label': 'التواصل مع الدعم' if user_context.get('preferred_language', 'ar') == 'ar' else 'Contact Support'},
                {'type': 'system_status', 'label': 'حالة النظام' if user_context.get('preferred_language', 'ar') == 'ar' else 'System Status'}
            ])
        
        elif intent == 'billing':
            actions.extend([
                {'type': 'view_billing', 'label': 'عرض الفواتير' if user_context.get('preferred_language', 'ar') == 'ar' else 'View Billing'},
                {'type': 'contact_billing', 'label': 'التواصل مع المحاسبة' if user_context.get('preferred_language', 'ar') == 'ar' else 'Contact Billing'},
                {'type': 'payment_methods', 'label': 'طرق الدفع' if user_context.get('preferred_language', 'ar') == 'ar' else 'Payment Methods'}
            ])
        
        elif intent == 'account':
            if not user_context['is_registered']:
                actions.extend([
                    {'type': 'register', 'label': 'إنشاء حساب' if user_context.get('preferred_language', 'ar') == 'ar' else 'Create Account'},
                    {'type': 'login', 'label': 'تسجيل الدخول' if user_context.get('preferred_language', 'ar') == 'ar' else 'Login'}
                ])
            else:
                actions.extend([
                    {'type': 'account_settings', 'label': 'إعدادات الحساب' if user_context.get('preferred_language', 'ar') == 'ar' else 'Account Settings'},
                    {'type': 'subscription_status', 'label': 'حالة الاشتراك' if user_context.get('preferred_language', 'ar') == 'ar' else 'Subscription Status'}
                ])
        
        return actions

    def get_common_actions(self, language: str) -> List[Dict]:
        """Get common actions for unknown intents"""
        if language == 'ar':
            return [
                {'type': 'view_pricing', 'label': 'الأسعار والباقات'},
                {'type': 'features', 'label': 'ميزات النظام'},
                {'type': 'contact_support', 'label': 'التواصل مع الدعم'},
                {'type': 'free_trial', 'label': 'تجربة مجانية'}
            ]
        else:
            return [
                {'type': 'view_pricing', 'label': 'Pricing & Plans'},
                {'type': 'features', 'label': 'System Features'},
                {'type': 'contact_support', 'label': 'Contact Support'},
                {'type': 'free_trial', 'label': 'Free Trial'}
            ]

    def should_transfer_to_human(self, intent: str, confidence: float, 
                                conversation_length: int) -> bool:
        """Determine if conversation should be transferred to human agent"""
        # Transfer conditions
        if confidence < 0.5:  # Low confidence
            return True
        
        if intent in ['billing', 'technical'] and conversation_length > 3:  # Complex issues
            return True
        
        if conversation_length > 10:  # Long conversations
            return True
        
        return False

    def log_interaction(self, session_id: str, user_message: str, 
                       bot_response: Dict, user_id: Optional[int] = None):
        """Log the interaction for analytics and improvement"""
        try:
            # Find or create chat session
            chat = SupportChat.query.filter_by(session_id=session_id).first()
            if not chat:
                chat = SupportChat(
                    session_id=session_id,
                    user_id=user_id,
                    language=bot_response.get('language', 'ar'),
                    status='active'
                )
                db.session.add(chat)
                db.session.flush()
            
            # Update chat activity
            chat.last_activity = datetime.utcnow()
            chat.total_messages += 2  # User message + bot response
            
            # Log user message
            user_msg = SupportMessage(
                chat_id=chat.id,
                message_type='user',
                content=user_message,
                language=bot_response.get('language', 'ar'),
                sent_at=datetime.utcnow()
            )
            db.session.add(user_msg)
            
            # Log bot response
            bot_msg = SupportMessage(
                chat_id=chat.id,
                message_type='ai',
                content=bot_response.get('response', ''),
                language=bot_response.get('language', 'ar'),
                ai_confidence=bot_response.get('confidence', 0.0),
                ai_intent=bot_response.get('intent', 'unknown'),
                sent_at=datetime.utcnow()
            )
            db.session.add(bot_msg)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            db.session.rollback()

# Initialize the bot
smart_support_bot = SmartSupportBot()

