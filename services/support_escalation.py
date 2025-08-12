import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from src.models.support_chat import SupportChat, SupportMessage, SupportAgent
from src.models.user import User
from src.models.base import db

logger = logging.getLogger(__name__)

class SupportEscalationManager:
    """Manages escalation of support tickets to human agents"""
    
    def __init__(self):
        # Email configuration - يمكن تخصيصها من إعدادات النظام
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.admin_email = "your-email@gmail.com"  # هنا تضع جيميلك
        self.admin_password = "your-app-password"  # App Password من Google
        self.system_name = "نظام التسويق الآلي الذكي"
        
        # Additional notification emails
        self.notification_emails = [
            "support@yourcompany.com",  # إيميل الدعم الإضافي
            "manager@yourcompany.com"   # إيميل المدير
        ]
        
        # Escalation triggers
        self.escalation_triggers = {
            'low_confidence': 0.3,
            'max_ai_attempts': 3,
            'conversation_length': 8,
            'keywords': ['مشكلة كبيرة', 'عاجل', 'urgent', 'مدير', 'manager', 'شكوى', 'complaint']
        }

    def should_escalate(self, chat: SupportChat, latest_message: str, 
                       bot_confidence: float) -> Dict:
        """Determine if chat should be escalated to human support"""
        escalation_reasons = []
        priority = 'normal'
        
        # Check confidence level
        if bot_confidence < self.escalation_triggers['low_confidence']:
            escalation_reasons.append('ثقة منخفضة في الرد الآلي')
            priority = 'high'
        
        # Check AI resolution attempts
        if chat.ai_resolution_attempts >= self.escalation_triggers['max_ai_attempts']:
            escalation_reasons.append('محاولات متعددة بدون حل')
            priority = 'high'
        
        # Check conversation length
        if chat.total_messages >= self.escalation_triggers['conversation_length']:
            escalation_reasons.append('محادثة طويلة تحتاج تدخل بشري')
            priority = 'medium'
        
        # Check for escalation keywords
        message_lower = latest_message.lower()
        for keyword in self.escalation_triggers['keywords']:
            if keyword.lower() in message_lower:
                escalation_reasons.append(f'كلمة مفتاحية: {keyword}')
                priority = 'urgent'
                break
        
        # Check for direct human request
        human_request_keywords = ['بشري', 'موظف', 'مدير', 'human', 'agent', 'person', 'manager']
        for keyword in human_request_keywords:
            if keyword.lower() in message_lower:
                escalation_reasons.append('طلب مباشر للدعم البشري')
                priority = 'high'
                break
        
        # Check for billing/payment issues
        billing_keywords = ['فاتورة', 'دفع', 'مال', 'billing', 'payment', 'money', 'charge']
        for keyword in billing_keywords:
            if keyword.lower() in message_lower:
                escalation_reasons.append('مشكلة في الفواتير أو الدفع')
                priority = 'high'
                break
        
        should_escalate = len(escalation_reasons) > 0
        
        return {
            'should_escalate': should_escalate,
            'reasons': escalation_reasons,
            'priority': priority,
            'urgency_score': len(escalation_reasons)
        }

    def escalate_to_human(self, chat_id: int, escalation_reason: str, 
                         priority: str = 'normal') -> Dict:
        """Escalate chat to human support"""
        try:
            chat = SupportChat.query.get(chat_id)
            if not chat:
                return {'success': False, 'error': 'Chat not found'}
            
            # Update chat status
            chat.status = 'transferred'
            chat.ai_handled = False
            chat.transferred_at = datetime.utcnow()
            chat.priority = priority
            
            # Get user information
            user_info = self.get_user_info(chat)
            
            # Get conversation history
            conversation_history = self.get_conversation_history(chat_id)
            
            # Send email notification
            email_sent = self.send_escalation_email(
                chat, user_info, conversation_history, escalation_reason, priority
            )
            
            # Add system message to chat
            system_message = SupportMessage(
                chat_id=chat_id,
                message_type='system',
                content=f'تم تحويل المحادثة للدعم البشري - السبب: {escalation_reason}',
                language=chat.language,
                sent_at=datetime.utcnow()
            )
            db.session.add(system_message)
            
            # Find available agent (if any)
            available_agent = self.find_available_agent(chat.language)
            if available_agent:
                chat.human_agent_id = available_agent.id
                
                # Add agent assignment message
                agent_message = SupportMessage(
                    chat_id=chat_id,
                    message_type='system',
                    content=f'تم تعيين {available_agent.name} للمساعدة',
                    language=chat.language,
                    sent_at=datetime.utcnow()
                )
                db.session.add(agent_message)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'تم تحويل المحادثة للدعم البشري بنجاح',
                'email_sent': email_sent,
                'assigned_agent': available_agent.name if available_agent else None,
                'ticket_id': f"TICKET-{chat.id}-{datetime.now().strftime('%Y%m%d')}"
            }
            
        except Exception as e:
            logger.error(f"Error escalating to human: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_user_info(self, chat: SupportChat) -> Dict:
        """Get comprehensive user information"""
        user_info = {
            'name': chat.visitor_name or 'زائر غير مسجل',
            'email': chat.visitor_email or 'غير متاح',
            'phone': chat.visitor_phone or 'غير متاح',
            'user_type': 'زائر',
            'subscription': 'غير مشترك',
            'credits_balance': 0,
            'last_activity': 'غير متاح'
        }
        
        if chat.user_id:
            try:
                user = User.query.get(chat.user_id)
                if user:
                    user_info.update({
                        'name': user.name,
                        'email': user.email,
                        'phone': user.phone or 'غير متاح',
                        'user_type': 'عضو مسجل',
                        'credits_balance': user.credits_balance,
                        'last_activity': user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else 'غير متاح',
                        'registration_date': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'غير متاح'
                    })
                    
                    # Get subscription info
                    from src.models.subscription import Subscription
                    subscription = Subscription.query.filter_by(user_id=user.id, is_active=True).first()
                    if subscription:
                        user_info['subscription'] = f"{subscription.plan_type} - ينتهي في {subscription.expires_at.strftime('%Y-%m-%d') if subscription.expires_at else 'غير محدد'}"
                    
            except Exception as e:
                logger.error(f"Error getting user info: {str(e)}")
        
        return user_info

    def get_conversation_history(self, chat_id: int) -> List[Dict]:
        """Get formatted conversation history"""
        try:
            messages = SupportMessage.query.filter_by(chat_id=chat_id).order_by(SupportMessage.sent_at).all()
            
            history = []
            for msg in messages:
                sender = 'العميل' if msg.message_type == 'user' else \
                        'البوت الذكي' if msg.message_type == 'ai' else \
                        'الموظف' if msg.message_type == 'agent' else 'النظام'
                
                history.append({
                    'sender': sender,
                    'message': msg.content,
                    'time': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S') if msg.sent_at else 'غير محدد',
                    'confidence': msg.ai_confidence if msg.ai_confidence else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    def send_escalation_email(self, chat: SupportChat, user_info: Dict, 
                             conversation_history: List[Dict], reason: str, 
                             priority: str) -> bool:
        """Send escalation email notification"""
        try:
            # Create email content
            subject = f"🚨 تصعيد دعم عاجل - {priority.upper()} - تذكرة #{chat.id}"
            
            # Priority emoji
            priority_emoji = "🔴" if priority == 'urgent' else "🟡" if priority == 'high' else "🟢"
            
            # HTML email template
            html_content = f"""
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; direction: rtl; }}
                    .header {{ background: #f44336; color: white; padding: 20px; text-align: center; }}
                    .priority-urgent {{ background: #f44336; }}
                    .priority-high {{ background: #ff9800; }}
                    .priority-normal {{ background: #4caf50; }}
                    .content {{ padding: 20px; }}
                    .info-box {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                    .conversation {{ background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                    .message {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                    .user-message {{ background: #e8f5e8; }}
                    .ai-message {{ background: #fff3e0; }}
                    .system-message {{ background: #f3e5f5; }}
                    .urgent {{ color: #f44336; font-weight: bold; }}
                    .high {{ color: #ff9800; font-weight: bold; }}
                    .normal {{ color: #4caf50; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header priority-{priority}">
                    <h1>{priority_emoji} تصعيد دعم فني - أولوية {priority.upper()}</h1>
                    <p>تذكرة رقم: TICKET-{chat.id}-{datetime.now().strftime('%Y%m%d')}</p>
                </div>
                
                <div class="content">
                    <div class="info-box">
                        <h3>📋 معلومات العميل:</h3>
                        <p><strong>الاسم:</strong> {user_info['name']}</p>
                        <p><strong>الإيميل:</strong> {user_info['email']}</p>
                        <p><strong>الهاتف:</strong> {user_info['phone']}</p>
                        <p><strong>نوع العضوية:</strong> {user_info['user_type']}</p>
                        <p><strong>الاشتراك:</strong> {user_info['subscription']}</p>
                        <p><strong>رصيد الكريديت:</strong> {user_info['credits_balance']}</p>
                        <p><strong>آخر نشاط:</strong> {user_info['last_activity']}</p>
                    </div>
                    
                    <div class="info-box">
                        <h3>🚨 تفاصيل التصعيد:</h3>
                        <p><strong>السبب:</strong> {reason}</p>
                        <p><strong>الأولوية:</strong> <span class="{priority}">{priority.upper()}</span></p>
                        <p><strong>وقت التصعيد:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>مدة المحادثة:</strong> {chat.total_messages} رسالة</p>
                        <p><strong>محاولات البوت:</strong> {chat.ai_resolution_attempts}</p>
                        <p><strong>اللغة:</strong> {'العربية' if chat.language == 'ar' else 'الإنجليزية'}</p>
                    </div>
                    
                    <div class="conversation">
                        <h3>💬 تاريخ المحادثة:</h3>
            """
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Last 10 messages
                message_class = 'user-message' if msg['sender'] == 'العميل' else \
                               'ai-message' if msg['sender'] == 'البوت الذكي' else 'system-message'
                
                confidence_info = f" (ثقة: {msg['confidence']:.2f})" if msg['confidence'] else ""
                
                html_content += f"""
                        <div class="message {message_class}">
                            <strong>{msg['sender']}</strong> - {msg['time']}{confidence_info}<br>
                            {msg['message']}
                        </div>
                """
            
            html_content += f"""
                    </div>
                    
                    <div class="info-box">
                        <h3>⚡ إجراءات مطلوبة:</h3>
                        <ul>
                            <li>الرد على العميل في أسرع وقت ممكن</li>
                            <li>مراجعة تاريخ المحادثة لفهم المشكلة</li>
                            <li>تحديث حالة التذكرة بعد الحل</li>
                            <li>إضافة الحل لقاعدة المعرفة إذا لزم الأمر</li>
                        </ul>
                    </div>
                    
                    <div class="info-box">
                        <h3>🔗 روابط مفيدة:</h3>
                        <p><a href="http://your-domain.com/admin/support/chat/{chat.id}">عرض المحادثة كاملة</a></p>
                        <p><a href="http://your-domain.com/admin/users/{chat.user_id if chat.user_id else 'guest'}">ملف العميل</a></p>
                        <p><a href="http://your-domain.com/admin/support/dashboard">لوحة تحكم الدعم</a></p>
                    </div>
                </div>
                
                <div style="background: #f5f5f5; padding: 20px; text-align: center; margin-top: 20px;">
                    <p><strong>{self.system_name}</strong></p>
                    <p>تم إرسال هذا الإشعار تلقائياً في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.admin_email
            msg['To'] = self.admin_email
            
            # Add CC recipients
            if self.notification_emails:
                msg['Cc'] = ', '.join(self.notification_emails)
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.admin_email, self.admin_password)
                
                # Send to admin and CC recipients
                recipients = [self.admin_email] + self.notification_emails
                server.send_message(msg, to_addrs=recipients)
            
            logger.info(f"Escalation email sent successfully for chat {chat.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending escalation email: {str(e)}")
            return False

    def find_available_agent(self, language: str) -> Optional[SupportAgent]:
        """Find available human agent for the language"""
        try:
            # Find agents who speak the language and are available
            agents = SupportAgent.query.filter(
                SupportAgent.is_active == True,
                SupportAgent.is_online == True,
                SupportAgent.status == 'available',
                SupportAgent.languages.contains(language)
            ).order_by(SupportAgent.total_chats_handled.asc()).all()
            
            # Return agent with least current workload
            for agent in agents:
                current_chats = SupportChat.query.filter(
                    SupportChat.human_agent_id == agent.id,
                    SupportChat.status.in_(['active', 'transferred'])
                ).count()
                
                if current_chats < agent.max_concurrent_chats:
                    return agent
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding available agent: {str(e)}")
            return None

    def send_resolution_notification(self, chat_id: int, resolution_summary: str):
        """Send notification when issue is resolved"""
        try:
            chat = SupportChat.query.get(chat_id)
            if not chat:
                return False
            
            user_info = self.get_user_info(chat)
            
            subject = f"✅ تم حل المشكلة - تذكرة #{chat_id}"
            
            html_content = f"""
            <html dir="rtl">
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Arial, sans-serif; direction: rtl;">
                <div style="background: #4caf50; color: white; padding: 20px; text-align: center;">
                    <h1>✅ تم حل المشكلة بنجاح</h1>
                    <p>تذكرة رقم: TICKET-{chat.id}-{datetime.now().strftime('%Y%m%d')}</p>
                </div>
                
                <div style="padding: 20px;">
                    <h3>📋 معلومات العميل:</h3>
                    <p><strong>الاسم:</strong> {user_info['name']}</p>
                    <p><strong>الإيميل:</strong> {user_info['email']}</p>
                    
                    <h3>✅ ملخص الحل:</h3>
                    <p>{resolution_summary}</p>
                    
                    <h3>📊 إحصائيات:</h3>
                    <p><strong>وقت الحل:</strong> {chat.resolution_time_minutes or 'غير محدد'} دقيقة</p>
                    <p><strong>عدد الرسائل:</strong> {chat.total_messages}</p>
                    <p><strong>تقييم العميل:</strong> {chat.satisfaction_rating or 'لم يقيم بعد'}/5</p>
                </div>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.admin_email
            msg['To'] = self.admin_email
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.admin_email, self.admin_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending resolution notification: {str(e)}")
            return False

# Initialize the escalation manager
support_escalation_manager = SupportEscalationManager()

