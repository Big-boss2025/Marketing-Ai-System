from src.models.base import db, BaseModel
from datetime import datetime
import json

from src.models.base import db, BaseModel
import json


class FeatureToggle(BaseModel):
    """Feature toggle model for enabling/disabling system features"""
    __tablename__ = 'feature_toggles'
    
    # Feature Details
    feature_key = db.Column(db.String(100), nullable=False, unique=True)
    feature_name = db.Column(db.String(200), nullable=False)
    feature_name_ar = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    
    # Feature Status
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    is_beta = db.Column(db.Boolean, default=False, nullable=False)
    is_premium = db.Column(db.Boolean, default=False, nullable=False)
    
    # Feature Category
    category = db.Column(db.String(50), nullable=False)  # ai, social_media, analytics, etc.
    
    # Configuration (JSON)
    configuration = db.Column(db.Text, nullable=True)  # JSON with feature-specific config
    
    # Usage Restrictions
    min_subscription_level = db.Column(db.String(20), nullable=True)  # free, basic, premium, enterprise
    max_daily_usage = db.Column(db.Integer, nullable=True)  # Max daily usage per user
    max_monthly_usage = db.Column(db.Integer, nullable=True)  # Max monthly usage per user
    
    # Rollout Control
    rollout_percentage = db.Column(db.Integer, default=100, nullable=False)  # 0-100
    target_user_groups = db.Column(db.Text, nullable=True)  # JSON array of user groups
    
    # Dependencies
    depends_on_features = db.Column(db.Text, nullable=True)  # JSON array of feature keys
    
    def get_configuration(self):
        """Get configuration as dictionary"""
        if self.configuration:
            try:
                return json.loads(self.configuration)
            except:
                return {}
        return {}
    
    def set_configuration(self, config_dict):
        """Set configuration from dictionary"""
        self.configuration = json.dumps(config_dict)
    
    def get_target_user_groups(self):
        """Get target user groups as list"""
        if self.target_user_groups:
            try:
                return json.loads(self.target_user_groups)
            except:
                return []
        return []
    
    def set_target_user_groups(self, groups_list):
        """Set target user groups from list"""
        self.target_user_groups = json.dumps(groups_list)
    
    def get_depends_on_features(self):
        """Get dependent features as list"""
        if self.depends_on_features:
            try:
                return json.loads(self.depends_on_features)
            except:
                return []
        return []
    
    def set_depends_on_features(self, features_list):
        """Set dependent features from list"""
        self.depends_on_features = json.dumps(features_list)
    
    def is_enabled_for_user(self, user):
        """Check if feature is enabled for specific user"""
        if not self.is_enabled:
            return False
        
        # Check subscription level if required
        if self.min_subscription_level and user.subscription_level:
            subscription_levels = ['free', 'basic', 'premium', 'enterprise']
            required_level_index = subscription_levels.index(self.min_subscription_level)
            user_level_index = subscription_levels.index(user.subscription_level)
            if user_level_index < required_level_index:
                return False
        
        # Check rollout percentage
        if self.rollout_percentage < 100:
            # Use user ID hash to determine if user is in rollout percentage
            import hashlib
            user_hash = int(hashlib.md5(str(user.id).encode()).hexdigest()[:8], 16)
            if (user_hash % 100) >= self.rollout_percentage:
                return False
        
        return True
    depends_on_features = db.Column(db.Text, nullable=True)  # JSON array of feature keys
    
    # Metrics
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    error_count = db.Column(db.Integer, default=0, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    def get_configuration(self):
        """Get configuration as dictionary"""
        if self.configuration:
            try:
                return json.loads(self.configuration)
            except:
                return {}
        return {}
    
    def set_configuration(self, config_dict):
        """Set configuration from dictionary"""
        self.configuration = json.dumps(config_dict)
    
    def get_target_user_groups(self):
        """Get target user groups as list"""
        if self.target_user_groups:
            try:
                return json.loads(self.target_user_groups)
            except:
                return []
        return []
    
    def set_target_user_groups(self, groups_list):
        """Set target user groups from list"""
        self.target_user_groups = json.dumps(groups_list)
    
    def get_depends_on_features(self):
        """Get dependency features as list"""
        if self.depends_on_features:
            try:
                return json.loads(self.depends_on_features)
            except:
                return []
        return []
    
    def set_depends_on_features(self, features_list):
        """Set dependency features from list"""
        self.depends_on_features = json.dumps(features_list)
    
    def is_available_for_user(self, user):
        """Check if feature is available for a specific user"""
        # Check if feature is enabled
        if not self.is_enabled:
            return False
        
        # Check subscription level
        if self.min_subscription_level:
            subscription_levels = ['free', 'basic', 'premium', 'enterprise']
            user_level_index = subscription_levels.index(user.subscription_status) if user.subscription_status in subscription_levels else 0
            required_level_index = subscription_levels.index(self.min_subscription_level)
            
            if user_level_index < required_level_index:
                return False
        
        # Check premium requirement
        if self.is_premium and not user.has_active_subscription():
            return False
        
        # Check rollout percentage (simple hash-based approach)
        if self.rollout_percentage < 100:
            user_hash = hash(user.id) % 100
            if user_hash >= self.rollout_percentage:
                return False
        
        # Check target user groups (if specified)
        target_groups = self.get_target_user_groups()
        if target_groups:
            # This would need to be implemented based on your user grouping logic
            # For now, we'll assume all users are in the 'general' group
            if 'general' not in target_groups:
                return False
        
        # Check dependencies
        dependencies = self.get_depends_on_features()
        if dependencies:
            for dep_feature_key in dependencies:
                dep_feature = FeatureToggle.get_by_key(dep_feature_key)
                if not dep_feature or not dep_feature.is_available_for_user(user):
                    return False
        
        return True
    
    def can_user_use_feature(self, user, usage_type='daily'):
        """Check if user can use the feature based on usage limits"""
        if not self.is_available_for_user(user):
            return False
        
        # Check usage limits
        if usage_type == 'daily' and self.max_daily_usage:
            daily_usage = FeatureUsage.get_user_daily_usage(user.id, self.feature_key)
            if daily_usage >= self.max_daily_usage:
                return False
        
        if usage_type == 'monthly' and self.max_monthly_usage:
            monthly_usage = FeatureUsage.get_user_monthly_usage(user.id, self.feature_key)
            if monthly_usage >= self.max_monthly_usage:
                return False
        
        return True
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def increment_error(self):
        """Increment error counter"""
        self.error_count += 1
    
    def get_success_rate(self):
        """Calculate success rate"""
        if self.usage_count == 0:
            return 100.0
        
        success_count = self.usage_count - self.error_count
        return (success_count / self.usage_count) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['configuration'] = self.get_configuration()
        data['target_user_groups'] = self.get_target_user_groups()
        data['depends_on_features'] = self.get_depends_on_features()
        data['success_rate'] = self.get_success_rate()
        return data
    
    @classmethod
    def get_by_key(cls, feature_key):
        """Get feature toggle by key"""
        return cls.query.filter_by(feature_key=feature_key).first()
    
    @classmethod
    def is_feature_enabled(cls, feature_key, user=None):
        """Check if a feature is enabled, optionally for a specific user"""
        feature = cls.get_by_key(feature_key)
        if not feature:
            return False
        
        if user:
            return feature.is_available_for_user(user)
        
        return feature.is_enabled
    
    @classmethod
    def get_enabled_features(cls, category=None, user=None):
        """Get all enabled features, optionally filtered by category and user"""
        query = cls.query.filter_by(is_enabled=True)
        
        if category:
            query = query.filter_by(category=category)
        
        features = query.all()
        
        if user:
            features = [f for f in features if f.is_available_for_user(user)]
        
        return features
    
    @classmethod
    def get_features_by_category(cls, category):
        """Get all features in a specific category"""
        return cls.query.filter_by(category=category).all()
    
    def __repr__(self):
        return f'<FeatureToggle {self.feature_key} - {"Enabled" if self.is_enabled else "Disabled"}>'


class FeatureUsage(BaseModel):
    """Feature usage tracking for individual users"""
    __tablename__ = 'feature_usage'
    
    # User & Feature
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    feature_key = db.Column(db.String(100), nullable=False)
    
    # Usage Details
    usage_date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    usage_count = db.Column(db.Integer, default=1, nullable=False)
    
    # Context
    context = db.Column(db.Text, nullable=True)  # JSON with usage context
    
    # Performance
    success_count = db.Column(db.Integer, default=0, nullable=False)
    error_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='feature_usage')
    
    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_user_feature_date', 'user_id', 'feature_key', 'usage_date'),
    )
    
    def get_context(self):
        """Get context as dictionary"""
        if self.context:
            try:
                return json.loads(self.context)
            except:
                return {}
        return {}
    
    def set_context(self, context_dict):
        """Set context from dictionary"""
        self.context = json.dumps(context_dict)
    
    def increment_usage(self, success=True):
        """Increment usage counters"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_success_rate(self):
        """Calculate success rate"""
        if self.usage_count == 0:
            return 100.0
        
        return (self.success_count / self.usage_count) * 100
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['context'] = self.get_context()
        data['success_rate'] = self.get_success_rate()
        return data
    
    @classmethod
    def record_usage(cls, user_id, feature_key, success=True, context=None):
        """Record feature usage for a user"""
        today = datetime.utcnow().date()
        
        # Try to find existing record for today
        usage = cls.query.filter_by(
            user_id=user_id,
            feature_key=feature_key,
            usage_date=today
        ).first()
        
        if usage:
            usage.increment_usage(success)
        else:
            usage = cls(
                user_id=user_id,
                feature_key=feature_key,
                usage_date=today,
                success_count=1 if success else 0,
                error_count=0 if success else 1
            )
        
        if context:
            usage.set_context(context)
        
        usage.save()
        
        # Also update the feature toggle usage counter
        feature = FeatureToggle.get_by_key(feature_key)
        if feature:
            if success:
                feature.increment_usage()
            else:
                feature.increment_error()
            feature.save()
        
        return usage
    
    @classmethod
    def get_user_daily_usage(cls, user_id, feature_key, date=None):
        """Get user's daily usage for a feature"""
        if not date:
            date = datetime.utcnow().date()
        
        usage = cls.query.filter_by(
            user_id=user_id,
            feature_key=feature_key,
            usage_date=date
        ).first()
        
        return usage.usage_count if usage else 0
    
    @classmethod
    def get_user_monthly_usage(cls, user_id, feature_key, year=None, month=None):
        """Get user's monthly usage for a feature"""
        if not year:
            year = datetime.utcnow().year
        if not month:
            month = datetime.utcnow().month
        
        from sqlalchemy import extract
        
        result = cls.query.filter_by(user_id=user_id, feature_key=feature_key)\
                         .filter(extract('year', cls.usage_date) == year)\
                         .filter(extract('month', cls.usage_date) == month)\
                         .with_entities(db.func.sum(cls.usage_count))\
                         .scalar()
        
        return result if result else 0
    
    @classmethod
    def get_feature_usage_stats(cls, feature_key, days=30):
        """Get usage statistics for a feature"""
        from datetime import timedelta
        
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        usages = cls.query.filter_by(feature_key=feature_key)\
                         .filter(cls.usage_date >= start_date)\
                         .all()
        
        stats = {
            'total_usage': sum(u.usage_count for u in usages),
            'total_success': sum(u.success_count for u in usages),
            'total_errors': sum(u.error_count for u in usages),
            'unique_users': len(set(u.user_id for u in usages)),
            'average_daily_usage': 0,
            'success_rate': 0
        }
        
        if usages:
            stats['average_daily_usage'] = stats['total_usage'] / days
            if stats['total_usage'] > 0:
                stats['success_rate'] = (stats['total_success'] / stats['total_usage']) * 100
        
        return stats
    
    def __repr__(self):
        return f'<FeatureUsage {self.user_id} - {self.feature_key} - {self.usage_date}>'

