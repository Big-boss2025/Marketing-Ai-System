from datetime import datetime
from src.models.base import db, BaseModel
from sqlalchemy.dialects.sqlite import JSON
import json

class MarketingStrategy(db.Model):
    __tablename__ = 'marketing_strategies'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_ar = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)

    # Strategy Classification
    category = db.Column(db.String(50), nullable=False)  # content, social, paid_ads, seo, etc.
    difficulty_level = db.Column(db.String(20), default='medium', nullable=False)  # easy, medium, hard
    effectiveness_score = db.Column(db.Float, default=50.0, nullable=False)  # 0-100
    cost_level = db.Column(db.String(20), default='medium', nullable=False)  # low, medium, high
    time_to_results = db.Column(db.String(50), nullable=True)  # "1-2 weeks", "1-3 months", etc.

    # Target Information
    target_audience = db.Column(db.Text, nullable=True)  # JSON
    suitable_platforms = db.Column(db.Text, nullable=True)  # JSON array
    required_resources = db.Column(db.Text, nullable=True)  # JSON

    # Strategy Content
    success_metrics = db.Column(db.Text, nullable=True)  # JSON array
    implementation_steps = db.Column(db.Text, nullable=True)  # JSON array
    best_practices = db.Column(db.Text, nullable=True)  # JSON array
    common_mistakes = db.Column(db.Text, nullable=True)  # JSON array
    case_studies = db.Column(db.Text, nullable=True)  # JSON array

    # Tags and Status
    tags = db.Column(db.Text, nullable=True)  # JSON array
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MarketingStrategy {self.name}>'

    def get_target_audience(self):
        """Get target audience as dictionary"""
        if self.target_audience:
            try:
                return json.loads(self.target_audience)
            except:
                return {}
        return {}

    def set_target_audience(self, audience_dict):
        """Set target audience from dictionary"""
        self.target_audience = json.dumps(audience_dict)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'category': self.category,
            'difficulty_level': self.difficulty_level,
            'effectiveness_score': self.effectiveness_score,
            'cost_level': self.cost_level,
            'time_to_results': self.time_to_results,
            'target_audience': self.target_audience,
            'suitable_platforms': self.suitable_platforms,
            'required_resources': self.required_resources,
            'success_metrics': self.success_metrics,
            'implementation_steps': self.implementation_steps,
            'best_practices': self.best_practices,
            'common_mistakes': self.common_mistakes,
            'case_studies': self.case_studies,
            'tags': self.tags,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # Relationships
    executions = db.relationship('StrategyExecution', backref='strategy', lazy=True, cascade='all, delete-orphan')


class StrategyExecution(db.Model):
    __tablename__ = 'strategy_executions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    # Strategy & User
    strategy_id = db.Column(db.Integer, db.ForeignKey('marketing_strategies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Campaign Details
    campaign_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='planning', nullable=False)  # planning, active, paused, completed, cancelled

    # Timeline
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    # Budget & Performance
    budget = db.Column(db.Float, default=0.0, nullable=False)
    spent_amount = db.Column(db.Float, default=0.0, nullable=False)

    # Metrics (JSON fields)
    target_metrics = db.Column(db.Text, nullable=True)  # JSON
    actual_metrics = db.Column(db.Text, nullable=True)  # JSON

    # Execution Details
    platforms_used = db.Column(db.Text, nullable=True)  # JSON array
    content_created = db.Column(db.Integer, default=0, nullable=False)
    audience_reached = db.Column(db.Integer, default=0, nullable=False)
    engagement_rate = db.Column(db.Float, default=0.0, nullable=False)
    conversion_rate = db.Column(db.Float, default=0.0, nullable=False)
    roi = db.Column(db.Float, default=0.0, nullable=False)

    # Analysis
    success_score = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    lessons_learned = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    next_steps = db.Column(db.Text, nullable=True)

    # Template
    is_template = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StrategyExecution {self.campaign_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'user_id': self.user_id,
            'campaign_name': self.campaign_name,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'budget': self.budget,
            'spent_amount': self.spent_amount,
            'target_metrics': self.target_metrics,
            'actual_metrics': self.actual_metrics,
            'platforms_used': self.platforms_used,
            'content_created': self.content_created,
            'audience_reached': self.audience_reached,
            'engagement_rate': self.engagement_rate,
            'conversion_rate': self.conversion_rate,
            'roi': self.roi,
            'success_score': self.success_score,
            'lessons_learned': self.lessons_learned,
            'recommendations': self.recommendations,
            'next_steps': self.next_steps,
            'is_template': self.is_template,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_roi(self):
        """Calculate ROI based on budget and results"""
        if self.budget > 0:
            return ((self.spent_amount - self.budget) / self.budget) * 100
        return 0.0

    def get_target_metrics(self):
        """Get target metrics as dictionary"""
        if self.target_metrics:
            try:
                return json.loads(self.target_metrics)
            except:
                return {}
        return {}

    def set_target_metrics(self, metrics_dict):
        """Set target metrics from dictionary"""
        self.target_metrics = json.dumps(metrics_dict)

    def get_actual_metrics(self):
        """Get actual metrics as dictionary"""
        if self.actual_metrics:
            try:
                return json.loads(self.actual_metrics)
            except:
                return {}
        return {}

    def set_actual_metrics(self, metrics_dict):
        """Set actual metrics from dictionary"""
        self.actual_metrics = json.dumps(metrics_dict)

    def get_platforms_used(self):
        """Get platforms used as list"""
        if self.platforms_used:
            try:
                return json.loads(self.platforms_used)
            except:
                return []
        return []

    def set_platforms_used(self, platforms_list):
        """Set platforms used from list"""
        self.platforms_used = json.dumps(platforms_list)

    def update_success_score(self):
        """Calculate and update success score based on performance"""
        score = 0

        # ROI contribution (40%)
        if self.roi > 20:
            score += 40
        elif self.roi > 0:
            score += 20

        # Engagement rate contribution (30%)
        if self.engagement_rate > 5:
            score += 30
        elif self.engagement_rate > 2:
            score += 15

        # Conversion rate contribution (30%)
        if self.conversion_rate > 3:
            score += 30
        elif self.conversion_rate > 1:
            score += 15

        self.success_score = min(score, 100)
        return self.success_score
    
    def to_dict(self):
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'user_id': self.user_id,
            'campaign_name': self.campaign_name,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'budget': self.budget,
            'spent_amount': self.spent_amount,
            'target_metrics': self.target_metrics,
            'actual_metrics': self.actual_metrics,
            'platforms_used': self.platforms_used,
            'content_created': self.content_created,
            'audience_reached': self.audience_reached,
            'engagement_rate': self.engagement_rate,
            'conversion_rate': self.conversion_rate,
            'roi': self.roi,
            'success_score': self.success_score,
            'lessons_learned': self.lessons_learned,
            'recommendations': self.recommendations,
            'next_steps': self.next_steps,
            'is_template': self.is_template,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StrategyTemplate(db.Model):
    """Pre-built strategy templates for different business types"""
    __tablename__ = 'strategy_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(50), nullable=False)  # restaurant, ecommerce, service, etc.
    industry = db.Column(db.String(50))
    target_audience_size = db.Column(db.String(20))  # small, medium, large, enterprise
    budget_range = db.Column(db.String(20))  # free, low, medium, high
    time_commitment = db.Column(db.String(20))  # minimal, moderate, intensive
    strategies_included = db.Column(JSON)  # List of strategy IDs
    execution_order = db.Column(JSON)  # Recommended order of execution
    timeline = db.Column(JSON)  # Suggested timeline for each strategy
    expected_results = db.Column(JSON)  # Expected outcomes
    success_stories = db.Column(JSON)  # Case studies for this template
    customization_options = db.Column(JSON)  # Areas that can be customized
    is_featured = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    average_success_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'business_type': self.business_type,
            'industry': self.industry,
            'target_audience_size': self.target_audience_size,
            'budget_range': self.budget_range,
            'time_commitment': self.time_commitment,
            'strategies_included': self.strategies_included,
            'execution_order': self.execution_order,
            'timeline': self.timeline,
            'expected_results': self.expected_results,
            'success_stories': self.success_stories,
            'customization_options': self.customization_options,
            'is_featured': self.is_featured,
            'usage_count': self.usage_count,
            'average_success_rate': self.average_success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StrategyRecommendation(db.Model):
    """AI-generated strategy recommendations for users"""
    __tablename__ = 'strategy_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('marketing_strategies.id'), nullable=False)
    recommendation_score = db.Column(db.Float, nullable=False)  # 0-10 confidence score
    reasoning = db.Column(db.Text)  # Why this strategy was recommended
    reasoning_ar = db.Column(db.Text)
    customization_suggestions = db.Column(JSON)  # Suggested modifications
    expected_outcome = db.Column(JSON)  # Predicted results
    risk_assessment = db.Column(JSON)  # Potential risks and mitigation
    priority_level = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    estimated_effort = db.Column(db.String(20))  # hours/week required
    estimated_cost = db.Column(db.Float, default=0.0)
    estimated_timeline = db.Column(db.String(50))
    prerequisites = db.Column(JSON)  # What needs to be done first
    success_probability = db.Column(db.Float, default=0.0)  # 0-100%
    is_viewed = db.Column(db.Boolean, default=False)
    is_accepted = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    feedback_rating = db.Column(db.Integer)  # 1-5 user rating
    feedback_comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Recommendations can expire
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'recommendation_score': self.recommendation_score,
            'reasoning': self.reasoning,
            'reasoning_ar': self.reasoning_ar,
            'customization_suggestions': self.customization_suggestions,
            'expected_outcome': self.expected_outcome,
            'risk_assessment': self.risk_assessment,
            'priority_level': self.priority_level,
            'estimated_effort': self.estimated_effort,
            'estimated_cost': self.estimated_cost,
            'estimated_timeline': self.estimated_timeline,
            'prerequisites': self.prerequisites,
            'success_probability': self.success_probability,
            'is_viewed': self.is_viewed,
            'is_accepted': self.is_accepted,
            'is_dismissed': self.is_dismissed,
            'feedback_rating': self.feedback_rating,
            'feedback_comment': self.feedback_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class StrategyPerformance(db.Model):
    """Track performance metrics for strategies across all users"""
    __tablename__ = 'strategy_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey('marketing_strategies.id'), nullable=False)
    month_year = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    total_executions = db.Column(db.Integer, default=0)
    successful_executions = db.Column(db.Integer, default=0)
    average_roi = db.Column(db.Float, default=0.0)
    average_engagement_rate = db.Column(db.Float, default=0.0)
    average_conversion_rate = db.Column(db.Float, default=0.0)
    average_success_score = db.Column(db.Float, default=0.0)
    total_audience_reached = db.Column(db.Integer, default=0)
    total_budget_spent = db.Column(db.Float, default=0.0)
    most_successful_platform = db.Column(db.String(50))
    common_success_factors = db.Column(JSON)
    common_failure_reasons = db.Column(JSON)
    improvement_suggestions = db.Column(JSON)
    trend_direction = db.Column(db.String(20))  # improving, declining, stable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'month_year': self.month_year,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'success_rate': (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0,
            'average_roi': self.average_roi,
            'average_engagement_rate': self.average_engagement_rate,
            'average_conversion_rate': self.average_conversion_rate,
            'average_success_score': self.average_success_score,
            'total_audience_reached': self.total_audience_reached,
            'total_budget_spent': self.total_budget_spent,
            'most_successful_platform': self.most_successful_platform,
            'common_success_factors': self.common_success_factors,
            'common_failure_reasons': self.common_failure_reasons,
            'improvement_suggestions': self.improvement_suggestions,
            'trend_direction': self.trend_direction,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

