from flask import Blueprint, request, jsonify, session
import logging
import uuid
from datetime import datetime
from src.services.smart_support_bot import smart_support_bot
from src.services.support_escalation import support_escalation_manager
from src.models.support_chat import SupportChat, SupportMessage, SupportKnowledgeBase, SupportAgent
from src.models.user import User
from src.models.base import db

logger = logging.getLogger(__name__)

support_bp = Blueprint('support', __name__, url_prefix='/support')

@support_bp.route('/chat/start', methods=['POST'])
def start_chat():
    """Start a new support chat session"""
    try:
        data = request.get_json() or {}
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Get user info
        user_id = data.get('user_id')
        visitor_name = data.get('visitor_name')
        visitor_email = data.get('visitor_email')
        visitor_phone = data.get('visitor_phone')
        language = data.get('language', 'ar')
        
        # Create chat session
        chat = SupportChat(
            session_id=session_id,
            user_id=user_id,
            visitor_name=visitor_name,
            visitor_email=visitor_email,
            visitor_phone=visitor_phone,
            language=language,
            status='active'
        )
        
        db.session.add(chat)
        db.session.commit()
        
        # Generate welcome message
        welcome_messages = {
            'ar': f"مرحباً {visitor_name or 'بك'}! 👋 أنا مساعدك الذكي في نظام التسويق الآلي. كيف يمكنني مساعدتك اليوم؟",
            'en': f"Hello {visitor_name or 'there'}! 👋 I'm your smart assistant for the Marketing Automation System. How can I help you today?"
        }
        
        welcome_message = welcome_messages.get(language, welcome_messages['ar'])
        
        # Add welcome message to chat
        bot_message = SupportMessage(
            chat_id=chat.id,
            message_type='ai',
            content=welcome_message,
            language=language,
            ai_confidence=1.0,
            sent_at=datetime.utcnow()
        )
        db.session.add(bot_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'chat_id': chat.id,
            'welcome_message': welcome_message,
            'suggested_actions': smart_support_bot.get_common_actions(language)
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting chat: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/chat/message', methods=['POST'])
def send_message():
    """Send message to support chat"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({
                'success': False,
                'error': 'session_id and message are required'
            }), 400
        
        # Find chat session
        chat = SupportChat.query.filter_by(session_id=session_id).first()
        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat session not found'
            }), 404
        
        # Update chat activity
        chat.last_activity = datetime.utcnow()
        chat.total_messages += 1
        
        # Add user message
        user_message = SupportMessage(
            chat_id=chat.id,
            message_type='user',
            content=message,
            language=chat.language,
            sent_at=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # Check if chat is handled by human agent
        if chat.status == 'transferred' and chat.human_agent_id:
            # Notify human agent (in real implementation, this would be via WebSocket)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'تم إرسال رسالتك للموظف المختص' if chat.language == 'ar' else 'Your message has been sent to our support agent',
                'status': 'transferred',
                'agent_name': 'موظف الدعم' if chat.language == 'ar' else 'Support Agent'
            }), 200
        
        # Generate AI response
        bot_response = smart_support_bot.generate_response(
            message, chat.user_id, session_id
        )
        
        if not bot_response.get('success', False):
            return jsonify(bot_response), 500
        
        # Update AI resolution attempts
        chat.ai_resolution_attempts += 1
        
        # Add bot response message
        bot_message = SupportMessage(
            chat_id=chat.id,
            message_type='ai',
            content=bot_response['response'],
            language=bot_response.get('language', 'ar'),
            ai_confidence=bot_response.get('confidence', 0.0),
            ai_intent=bot_response.get('intent', 'unknown'),
            sent_at=datetime.utcnow()
        )
        db.session.add(bot_message)
        
        # Check if escalation is needed
        escalation_check = support_escalation_manager.should_escalate(
            chat, message, bot_response.get('confidence', 0.0)
        )
        
        response_data = {
            'success': True,
            'response': bot_response['response'],
            'intent': bot_response.get('intent'),
            'confidence': bot_response.get('confidence'),
            'suggested_actions': bot_response.get('suggested_actions', []),
            'escalation_suggested': escalation_check['should_escalate'],
            'escalation_reasons': escalation_check.get('reasons', [])
        }
        
        # Auto-escalate if needed
        if escalation_check['should_escalate'] and escalation_check['urgency_score'] >= 2:
            escalation_result = support_escalation_manager.escalate_to_human(
                chat.id, 
                ', '.join(escalation_check['reasons']),
                escalation_check['priority']
            )
            
            if escalation_result['success']:
                response_data.update({
                    'auto_escalated': True,
                    'escalation_message': 'تم تحويل محادثتك للدعم البشري تلقائياً' if chat.language == 'ar' else 'Your chat has been automatically transferred to human support',
                    'ticket_id': escalation_result.get('ticket_id')
                })
        
        db.session.commit()
        
        # Log interaction for analytics
        smart_support_bot.log_interaction(session_id, message, bot_response, chat.user_id)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/chat/escalate', methods=['POST'])
def escalate_chat():
    """Manually escalate chat to human support"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        reason = data.get('reason', 'طلب العميل')
        priority = data.get('priority', 'normal')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400
        
        # Find chat session
        chat = SupportChat.query.filter_by(session_id=session_id).first()
        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat session not found'
            }), 404
        
        # Escalate to human
        result = support_escalation_manager.escalate_to_human(chat.id, reason, priority)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error escalating chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        chat = SupportChat.query.filter_by(session_id=session_id).first()
        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat session not found'
            }), 404
        
        messages = SupportMessage.query.filter_by(chat_id=chat.id).order_by(SupportMessage.sent_at).all()
        
        history = []
        for msg in messages:
            history.append({
                'id': msg.id,
                'type': msg.message_type,
                'content': msg.content,
                'sender_name': msg.sender_name,
                'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                'confidence': msg.ai_confidence,
                'intent': msg.ai_intent
            })
        
        return jsonify({
            'success': True,
            'chat_info': chat.to_dict(),
            'messages': history,
            'total_messages': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/chat/close', methods=['POST'])
def close_chat():
    """Close chat session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        satisfaction_rating = data.get('satisfaction_rating')
        feedback = data.get('feedback')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400
        
        # Find chat session
        chat = SupportChat.query.filter_by(session_id=session_id).first()
        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat session not found'
            }), 404
        
        # Update chat status
        chat.status = 'closed'
        chat.closed_at = datetime.utcnow()
        chat.satisfaction_rating = satisfaction_rating
        chat.feedback = feedback
        
        # Calculate resolution time
        if chat.started_at:
            resolution_time = (datetime.utcnow() - chat.started_at).total_seconds() / 60
            chat.resolution_time_minutes = int(resolution_time)
        
        # Add closing message
        closing_message = SupportMessage(
            chat_id=chat.id,
            message_type='system',
            content='تم إغلاق المحادثة' if chat.language == 'ar' else 'Chat session closed',
            language=chat.language,
            sent_at=datetime.utcnow()
        )
        db.session.add(closing_message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إغلاق المحادثة بنجاح' if chat.language == 'ar' else 'Chat closed successfully',
            'resolution_time_minutes': chat.resolution_time_minutes
        }), 200
        
    except Exception as e:
        logger.error(f"Error closing chat: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/knowledge-base', methods=['GET'])
def get_knowledge_base():
    """Get knowledge base entries"""
    try:
        language = request.args.get('language', 'ar')
        category = request.args.get('category')
        
        query = SupportKnowledgeBase.query.filter(
            SupportKnowledgeBase.language == language,
            SupportKnowledgeBase.is_active == True
        )
        
        if category:
            query = query.filter(SupportKnowledgeBase.category == category)
        
        entries = query.order_by(SupportKnowledgeBase.priority.desc()).all()
        
        return jsonify({
            'success': True,
            'entries': [entry.to_dict() for entry in entries],
            'total': len(entries)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge base: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/knowledge-base', methods=['POST'])
def add_knowledge_base_entry():
    """Add new knowledge base entry"""
    try:
        data = request.get_json()
        
        required_fields = ['question', 'answer', 'category', 'language']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'question, answer, category, and language are required'
            }), 400
        
        entry = SupportKnowledgeBase(
            question=data['question'],
            answer=data['answer'],
            category=data['category'],
            language=data['language'],
            keywords=data.get('keywords'),
            intent=data.get('intent'),
            priority=data.get('priority', 1)
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إضافة الدخول لقاعدة المعرفة بنجاح',
            'entry': entry.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding knowledge base entry: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/agents', methods=['GET'])
def get_support_agents():
    """Get list of support agents"""
    try:
        agents = SupportAgent.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'agents': [agent.to_dict() for agent in agents],
            'total': len(agents)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting support agents: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/analytics/dashboard', methods=['GET'])
def get_support_analytics():
    """Get support analytics dashboard data"""
    try:
        from datetime import date, timedelta
        
        # Get date range
        days = int(request.args.get('days', 7))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Basic metrics
        total_chats = SupportChat.query.filter(
            SupportChat.started_at >= start_date
        ).count()
        
        ai_resolved = SupportChat.query.filter(
            SupportChat.started_at >= start_date,
            SupportChat.ai_handled == True,
            SupportChat.status == 'closed'
        ).count()
        
        human_resolved = SupportChat.query.filter(
            SupportChat.started_at >= start_date,
            SupportChat.ai_handled == False,
            SupportChat.status == 'closed'
        ).count()
        
        active_chats = SupportChat.query.filter(
            SupportChat.status.in_(['active', 'transferred'])
        ).count()
        
        # Average satisfaction
        avg_satisfaction = db.session.query(
            db.func.avg(SupportChat.satisfaction_rating)
        ).filter(
            SupportChat.started_at >= start_date,
            SupportChat.satisfaction_rating.isnot(None)
        ).scalar() or 0
        
        # Response time
        avg_resolution_time = db.session.query(
            db.func.avg(SupportChat.resolution_time_minutes)
        ).filter(
            SupportChat.started_at >= start_date,
            SupportChat.resolution_time_minutes.isnot(None)
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_chats': total_chats,
                'ai_resolved': ai_resolved,
                'human_resolved': human_resolved,
                'active_chats': active_chats,
                'ai_resolution_rate': (ai_resolved / total_chats * 100) if total_chats > 0 else 0,
                'average_satisfaction': round(avg_satisfaction, 2),
                'average_resolution_time_minutes': round(avg_resolution_time, 2),
                'period_days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting support analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/widget/config', methods=['GET'])
def get_widget_config():
    """Get support widget configuration"""
    try:
        config = {
            'enabled': True,
            'position': 'bottom-right',
            'theme': 'blue',
            'languages': ['ar', 'en'],
            'default_language': 'ar',
            'greeting_message': {
                'ar': 'مرحباً! كيف يمكنني مساعدتك؟',
                'en': 'Hello! How can I help you?'
            },
            'quick_actions': [
                {'type': 'pricing', 'label_ar': 'الأسعار', 'label_en': 'Pricing'},
                {'type': 'features', 'label_ar': 'الميزات', 'label_en': 'Features'},
                {'type': 'support', 'label_ar': 'الدعم', 'label_en': 'Support'},
                {'type': 'demo', 'label_ar': 'عرض توضيحي', 'label_en': 'Demo'}
            ]
        }
        
        return jsonify({
            'success': True,
            'config': config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting widget config: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@support_bp.route('/health', methods=['GET'])
def support_health_check():
    """Health check endpoint for support service"""
    return jsonify({
        'success': True,
        'message': 'Support service is healthy',
        'timestamp': str(datetime.utcnow()),
        'services': {
            'smart_bot': 'active',
            'escalation_manager': 'active',
            'knowledge_base': 'active'
        }
    }), 200

