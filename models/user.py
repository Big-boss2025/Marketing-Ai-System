from src.models.base import db, BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(BaseModel):
    """User model for managing system users"""
    __tablename__ = 'users'
    
    # Basic Information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Business Information
    business_name = db.Column(db.String(200), nullable=True)
    business_type = db.Column(db.String(100), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    
    # Location & Language
    country = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), default='ar', nullable=False)
    timezone = db.Column(db.String(50), default='Africa/Cairo', nullable=False)
    
    # Credits & Subscription
    credits_balance = db.Column(db.Integer, default=0, nullable=False)
    subscription_status = db.Column(db.String(20), default='free', nullable=False)  # free, basic, premium, enterprise
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Odoo Integration
    odoo_user_id = db.Column(db.String(100), nullable=True, unique=True)
    odoo_access_token = db.Column(db.Text, nullable=True)
    odoo_refresh_token = db.Column(db.Text, nullable=True)
    odoo_instance_url = db.Column(db.String(500), nullable=True)
    
    # Social Media Accounts (JSON field to store multiple accounts)
    social_accounts = db.Column(db.Text, nullable=True)  # JSON string
    
    # Referral System
    referral_code = db.Column(db.String(20), unique=True, nullable=True)
    referred_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    total_referrals = db.Column(db.Integer, default=0, nullable=False)
    referral_credits_earned = db.Column(db.Integer, default=0, nullable=False)
    
    # Settings & Preferences
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    sms_notifications = db.Column(db.Boolean, default=False, nullable=False)
    auto_post_enabled = db.Column(db.Boolean, default=True, nullable=False)
    content_language = db.Column(db.String(10), default='ar', nullable=False)
    
    # Timestamps
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_activity_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    referrer = db.relationship('User', remote_side=[id], backref='referred_users')
    
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_social_accounts(self):
        """Get social media accounts as dictionary"""
        if self.social_accounts:
            try:
                return json.loads(self.social_accounts)
            except:
                return {}
        return {}
    
    def set_social_accounts(self, accounts_dict):
        """Set social media accounts from dictionary"""
        self.social_accounts = json.dumps(accounts_dict)
    
    def add_social_account(self, platform, account_data):
        """Add or update a social media account"""
        accounts = self.get_social_accounts()
        accounts[platform] = account_data
        self.set_social_accounts(accounts)
    
    def remove_social_account(self, platform):
        """Remove a social media account"""
        accounts = self.get_social_accounts()
        if platform in accounts:
            del accounts[platform]
            self.set_social_accounts(accounts)
    
    def has_active_subscription(self):
        """Check if user has active subscription"""
        if self.subscription_status == 'free':
            return False
        if self.subscription_expires_at and self.subscription_expires_at < datetime.utcnow():
            return False
        return True
    
    def can_use_credits(self, amount):
        """Check if user has enough credits"""
        return self.credits_balance >= amount
    
    def deduct_credits(self, amount, description=""):
        """Deduct credits from user balance"""
        if self.can_use_credits(amount):
            self.credits_balance -= amount
            # Create credit transaction record (will be implemented later)
            return True
        return False
    
    def add_credits(self, amount, description=""):
        """Add credits to user balance"""
        self.credits_balance += amount
        # Create credit transaction record (will be implemented later)
        return True
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary, optionally excluding sensitive data"""
        data = super().to_dict()
        
        # Remove sensitive fields unless explicitly requested
        if not include_sensitive:
            sensitive_fields = ['password_hash', 'odoo_access_token', 'odoo_refresh_token']
            for field in sensitive_fields:
                data.pop(field, None)
        
        # Parse social accounts
        data['social_accounts'] = self.get_social_accounts()
        
        # Add computed fields
        data['has_active_subscription'] = self.has_active_subscription()
        data['subscription_days_remaining'] = None
        if self.subscription_expires_at:
            remaining = self.subscription_expires_at - datetime.utcnow()
            data['subscription_days_remaining'] = max(0, remaining.days)
        
        return data
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_by_odoo_id(cls, odoo_user_id):
        """Get user by Odoo user ID"""
        return cls.query.filter_by(odoo_user_id=odoo_user_id).first()
    
    @classmethod
    def get_by_referral_code(cls, referral_code):
        """Get user by referral code"""
        return cls.query.filter_by(referral_code=referral_code).first()
    
    def __repr__(self):
        return f'<User {self.email}>'

