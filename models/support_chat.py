from datetime import datetime
from src.models.base import db

class SupportChat(db.Model):
    """Support chat sessions model"""
    __tablename__ = 'support_chats'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    visitor_id = db.Column(db.String(100), nullable=True)  # For anonymous visitors
    
    # Chat details
    status = db.Column(db.String(20), default='active')  # active, closed, transferred
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    category = db.Column(db.String(50), nullable=True)  # technical, billing, general, etc.
    language = db.Column(db.String(10), default='ar')
    
    # Contact info (for anonymous users)
    visitor_name = db.Column(db.String(100), nullable=True)
    visitor_email = db.Column(db.String(100), nullable=True)
    visitor_phone = db.Column(db.String(20), nullable=True)
    
    # Chat metadata
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # AI and human support
    ai_handled = db.Column(db.Boolean, default=True)
    human_agent_id = db.Column(db.Integer, nullable=True)
    transferred_at = db.Column(db.DateTime, nullable=True)
    
    # Satisfaction and feedback
    satisfaction_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)
    
    # Analytics
    total_messages = db.Column(db.Integer, default=0)
    ai_resolution_attempts = db.Column(db.Integer, default=0)
    resolution_time_minutes = db.Column(db.Integer, nullable=True)
    
    # Relationships
    messages = db.relationship('SupportMessage', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'visitor_id': self.visitor_id,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'language': self.language,
            'visitor_name': self.visitor_name,
            'visitor_email': self.visitor_email,
            'visitor_phone': self.visitor_phone,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'ai_handled': self.ai_handled,
            'human_agent_id': self.human_agent_id,
            'transferred_at': self.transferred_at.isoformat() if self.transferred_at else None,
            'satisfaction_rating': self.satisfaction_rating,
            'feedback': self.feedback,
            'total_messages': self.total_messages,
            'ai_resolution_attempts': self.ai_resolution_attempts,
            'resolution_time_minutes': self.resolution_time_minutes
        }

class SupportMessage(db.Model):
    """Support chat messages model"""
    __tablename__ = 'support_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('support_chats.id'), nullable=False)
    
    # Message details
    message_type = db.Column(db.String(20), nullable=False)  # user, ai, agent, system
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='ar')
    
    # Sender info
    sender_name = db.Column(db.String(100), nullable=True)
    agent_id = db.Column(db.Integer, nullable=True)
    
    # Message metadata
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # AI processing
    ai_confidence = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    ai_intent = db.Column(db.String(50), nullable=True)
    ai_entities = db.Column(db.Text, nullable=True)  # JSON string
    
    # Message actions
    triggered_action = db.Column(db.String(100), nullable=True)
    action_result = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_type': self.message_type,
            'content': self.content,
            'language': self.language,
            'sender_name': self.sender_name,
            'agent_id': self.agent_id,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'ai_confidence': self.ai_confidence,
            'ai_intent': self.ai_intent,
            'ai_entities': self.ai_entities,
            'triggered_action': self.triggered_action,
            'action_result': self.action_result
        }

class SupportKnowledgeBase(db.Model):
    """Knowledge base for AI support responses"""
    __tablename__ = 'support_knowledge_base'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Question and answer
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    # Language support
    language = db.Column(db.String(10), default='ar')
    
    # Keywords for matching
    keywords = db.Column(db.Text, nullable=True)  # Comma-separated
    intent = db.Column(db.String(50), nullable=True)
    
    # Usage statistics
    usage_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    
    # Management
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)  # Higher number = higher priority
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'language': self.language,
            'keywords': self.keywords,
            'intent': self.intent,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'is_active': self.is_active,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SupportAgent(db.Model):
    """Human support agents model"""
    __tablename__ = 'support_agents'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Agent details
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Agent status
    is_active = db.Column(db.Boolean, default=True)
    is_online = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='available')  # available, busy, away, offline
    
    # Agent capabilities
    languages = db.Column(db.String(100), default='ar,en')  # Comma-separated
    specialties = db.Column(db.String(200), nullable=True)  # Comma-separated
    max_concurrent_chats = db.Column(db.Integer, default=5)
    
    # Performance metrics
    total_chats_handled = db.Column(db.Integer, default=0)
    average_response_time = db.Column(db.Integer, default=0)  # seconds
    satisfaction_rating = db.Column(db.Float, default=0.0)
    
    # Timestamps
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_online': self.is_online,
            'status': self.status,
            'languages': self.languages.split(',') if self.languages else [],
            'specialties': self.specialties.split(',') if self.specialties else [],
            'max_concurrent_chats': self.max_concurrent_chats,
            'total_chats_handled': self.total_chats_handled,
            'average_response_time': self.average_response_time,
            'satisfaction_rating': self.satisfaction_rating,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SupportAnalytics(db.Model):
    """Support analytics and metrics"""
    __tablename__ = 'support_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Date and period
    date = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    
    # Chat metrics
    total_chats = db.Column(db.Integer, default=0)
    ai_resolved_chats = db.Column(db.Integer, default=0)
    human_resolved_chats = db.Column(db.Integer, default=0)
    unresolved_chats = db.Column(db.Integer, default=0)
    
    # Response times
    average_first_response_time = db.Column(db.Integer, default=0)  # seconds
    average_resolution_time = db.Column(db.Integer, default=0)  # minutes
    
    # Satisfaction
    total_ratings = db.Column(db.Integer, default=0)
    average_satisfaction = db.Column(db.Float, default=0.0)
    
    # Categories
    technical_issues = db.Column(db.Integer, default=0)
    billing_issues = db.Column(db.Integer, default=0)
    general_inquiries = db.Column(db.Integer, default=0)
    feature_requests = db.Column(db.Integer, default=0)
    
    # Languages
    arabic_chats = db.Column(db.Integer, default=0)
    english_chats = db.Column(db.Integer, default=0)
    other_language_chats = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'period_type': self.period_type,
            'total_chats': self.total_chats,
            'ai_resolved_chats': self.ai_resolved_chats,
            'human_resolved_chats': self.human_resolved_chats,
            'unresolved_chats': self.unresolved_chats,
            'average_first_response_time': self.average_first_response_time,
            'average_resolution_time': self.average_resolution_time,
            'total_ratings': self.total_ratings,
            'average_satisfaction': self.average_satisfaction,
            'technical_issues': self.technical_issues,
            'billing_issues': self.billing_issues,
            'general_inquiries': self.general_inquiries,
            'feature_requests': self.feature_requests,
            'arabic_chats': self.arabic_chats,
            'english_chats': self.english_chats,
            'other_language_chats': self.other_language_chats,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

