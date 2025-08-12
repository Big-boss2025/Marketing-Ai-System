from src.models.base import db, BaseModel
from datetime import datetime, timedelta
import json

class SubscriptionPlan(BaseModel):
    """Subscription plans model"""
    __tablename__ = 'subscription_plans'
    
    # Plan Details
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    
    # Pricing
    price_monthly = db.Column(db.Float, default=0.0, nullable=False)
    price_yearly = db.Column(db.Float, default=0.0, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Credits & Limits
    monthly_credits = db.Column(db.Integer, default=0, nullable=False)
    max_social_accounts = db.Column(db.Integer, default=1, nullable=False)
    max_posts_per_day = db.Column(db.Integer, default=10, nullable=False)
    max_campaigns = db.Column(db.Integer, default=1, nullable=False)
    
    # Features (JSON field for flexible feature management)
    features = db.Column(db.Text, nullable=True)  # JSON string
    
    # Plan Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_popular = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    def get_features(self):
        """Get features as dictionary"""
        if self.features:
            try:
                return json.loads(self.features)
            except:
                return {}
        return {}
    
    def set_features(self, features_dict):
        """Set features from dictionary"""
        self.features = json.dumps(features_dict)
    
    def has_feature(self, feature_name):
        """Check if plan has specific feature"""
        features = self.get_features()
        return features.get(feature_name, False)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['features'] = self.get_features()
        return data
    
    @classmethod
    def get_active_plans(cls):
        """Get all active subscription plans"""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'


class UserSubscription(BaseModel):
    """User subscription records"""
    __tablename__ = 'user_subscriptions'
    
    # User & Plan
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    
    # Subscription Details
    status = db.Column(db.String(20), default='active', nullable=False)  # active, cancelled, expired, suspended
    billing_cycle = db.Column(db.String(10), default='monthly', nullable=False)  # monthly, yearly
    
    # Dates
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    next_billing_date = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    # Payment Information
    amount_paid = db.Column(db.Float, default=0.0, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)  # paypal, stripe, etc.
    transaction_id = db.Column(db.String(100), nullable=True)
    
    # Auto-renewal
    auto_renew = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='subscriptions')
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')
    
    def is_active(self):
        """Check if subscription is currently active"""
        now = datetime.utcnow()
        return (self.status == 'active' and 
                self.start_date <= now <= self.end_date)
    
    def days_remaining(self):
        """Get days remaining in subscription"""
        if not self.is_active():
            return 0
        remaining = self.end_date - datetime.utcnow()
        return max(0, remaining.days)
    
    def cancel(self, reason=""):
        """Cancel subscription"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        self.auto_renew = False
    
    def renew(self, duration_months=1):
        """Renew subscription"""
        if self.billing_cycle == 'yearly':
            duration_months = 12
        
        self.end_date = self.end_date + timedelta(days=duration_months * 30)
        self.next_billing_date = self.end_date
        self.status = 'active'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['is_active'] = self.is_active()
        data['days_remaining'] = self.days_remaining()
        data['plan_name'] = self.plan.name if self.plan else None
        return data
    
    @classmethod
    def get_active_subscription(cls, user_id):
        """Get user's active subscription"""
        return cls.query.filter_by(
            user_id=user_id,
            status='active'
        ).filter(
            cls.end_date > datetime.utcnow()
        ).first()
    
    def __repr__(self):
        return f'<UserSubscription {self.user_id} - {self.plan.name if self.plan else "Unknown"}>'


class PaymentTransaction(BaseModel):
    """Payment transaction records"""
    __tablename__ = 'payment_transactions'
    
    # User & Subscription
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.String(36), db.ForeignKey('user_subscriptions.id'), nullable=True)
    
    # Transaction Details
    transaction_type = db.Column(db.String(20), nullable=False)  # subscription, credits, refund
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, completed, failed, refunded
    
    # Amount & Currency
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Payment Gateway
    gateway = db.Column(db.String(50), nullable=False)  # paypal, stripe, etc.
    gateway_transaction_id = db.Column(db.String(100), nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)  # JSON response from gateway
    
    # Additional Info
    description = db.Column(db.String(500), nullable=True)
    transaction_metadata = db.Column(db.Text, nullable=True)  # JSON for additional data
    
    # Relationships
    user = db.relationship('User', backref='payment_transactions')
    subscription = db.relationship('UserSubscription', backref='payment_transactions')
    
    def get_gateway_response(self):
        """Get gateway response as dictionary"""
        if self.gateway_response:
            try:
                return json.loads(self.gateway_response)
            except:
                return {}
        return {}
    
    def set_gateway_response(self, response_dict):
        """Set gateway response from dictionary"""
        self.gateway_response = json.dumps(response_dict)
    
    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.transaction_metadata:
            try:
                return json.loads(self.transaction_metadata)
            except:
                return {}
        return {}
    
    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.transaction_metadata = json.dumps(metadata_dict)
    
    def mark_completed(self, gateway_transaction_id=None):
        """Mark transaction as completed"""
        self.status = 'completed'
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id
    
    def mark_failed(self, reason=""):
        """Mark transaction as failed"""
        self.status = 'failed'
        if reason:
            metadata = self.get_metadata()
            metadata['failure_reason'] = reason
            self.set_metadata(metadata)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['gateway_response'] = self.get_gateway_response()
        data['metadata'] = self.get_metadata()
        return data
    
    def __repr__(self):
        return f'<PaymentTransaction {self.id} - {self.amount} {self.currency}>'

