from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import db
import uuid
import hashlib

class ReferralCode(db.Model):
    """Referral codes for users"""
    __tablename__ = 'referral_codes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    max_usage = Column(Integer, default=100)  # Maximum number of uses
    reward_type = Column(String(20), default='credits')  # credits, percentage, fixed_amount
    reward_value = Column(Float, default=10.0)  # 10 credits or 10% discount
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="referral_codes")
    referrals = relationship("Referral", back_populates="referral_code")
    
    def __init__(self, user_id, reward_type='credits', reward_value=10.0, max_usage=100):
        self.user_id = user_id
        self.code = self.generate_unique_code()
        self.reward_type = reward_type
        self.reward_value = reward_value
        self.max_usage = max_usage
    
    def generate_unique_code(self):
        """Generate unique referral code"""
        # Create a unique code based on user_id and timestamp
        unique_string = f"{self.user_id}_{datetime.utcnow().timestamp()}_{uuid.uuid4().hex[:8]}"
        hash_object = hashlib.md5(unique_string.encode())
        return hash_object.hexdigest()[:8].upper()
    
    def is_valid(self):
        """Check if referral code is valid for use"""
        if not self.is_active:
            return False
        
        if self.usage_count >= self.max_usage:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def use_code(self):
        """Use the referral code (increment usage count)"""
        if self.is_valid():
            self.usage_count += 1
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def save(self):
        """Save referral code to database"""
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'code': self.code,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'max_usage': self.max_usage,
            'reward_type': self.reward_type,
            'reward_value': self.reward_value,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Referral(db.Model):
    """Referral tracking and rewards"""
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # User who referred
    referred_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # User who was referred
    referral_code_id = Column(Integer, ForeignKey('referral_codes.id'), nullable=False)
    
    # Referral status
    status = Column(String(20), default='pending')  # pending, completed, cancelled
    
    # Rewards
    referrer_reward_type = Column(String(20), default='credits')
    referrer_reward_value = Column(Float, default=10.0)
    referrer_reward_given = Column(Boolean, default=False)
    
    referred_reward_type = Column(String(20), default='credits')
    referred_reward_value = Column(Float, default=5.0)
    referred_reward_given = Column(Boolean, default=False)
    
    # Tracking
    conversion_event = Column(String(50))  # signup, first_purchase, subscription
    conversion_value = Column(Float, default=0.0)  # Value of the conversion
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamps
    referred_at = Column(DateTime, default=datetime.utcnow)
    converted_at = Column(DateTime, nullable=True)
    rewards_given_at = Column(DateTime, nullable=True)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")
    referral_code = relationship("ReferralCode", back_populates="referrals")
    
    def complete_referral(self, conversion_event='signup', conversion_value=0.0):
        """Complete the referral and give rewards"""
        if self.status != 'pending':
            return False
        
        self.status = 'completed'
        self.conversion_event = conversion_event
        self.conversion_value = conversion_value
        self.converted_at = datetime.utcnow()
        
        # Give rewards
        self.give_rewards()
        
        return True
    
    def give_rewards(self):
        """Give rewards to both referrer and referred users"""
        from src.services.credit_manager import credit_manager
        
        # Give reward to referrer
        if not self.referrer_reward_given:
            if self.referrer_reward_type == 'credits':
                credit_result = credit_manager.add_credits(
                    self.referrer_id, 
                    self.referrer_reward_value, 
                    'referral_reward'
                )
                if credit_result['success']:
                    self.referrer_reward_given = True
        
        # Give reward to referred user
        if not self.referred_reward_given:
            if self.referred_reward_type == 'credits':
                credit_result = credit_manager.add_credits(
                    self.referred_id, 
                    self.referred_reward_value, 
                    'referral_welcome_bonus'
                )
                if credit_result['success']:
                    self.referred_reward_given = True
        
        # Update timestamp if both rewards given
        if self.referrer_reward_given and self.referred_reward_given:
            self.rewards_given_at = datetime.utcnow()
    
    def save(self):
        """Save referral to database"""
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'referrer_id': self.referrer_id,
            'referred_id': self.referred_id,
            'referral_code_id': self.referral_code_id,
            'status': self.status,
            'referrer_reward_type': self.referrer_reward_type,
            'referrer_reward_value': self.referrer_reward_value,
            'referrer_reward_given': self.referrer_reward_given,
            'referred_reward_type': self.referred_reward_type,
            'referred_reward_value': self.referred_reward_value,
            'referred_reward_given': self.referred_reward_given,
            'conversion_event': self.conversion_event,
            'conversion_value': self.conversion_value,
            'referred_at': self.referred_at.isoformat(),
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'rewards_given_at': self.rewards_given_at.isoformat() if self.rewards_given_at else None
        }

class ReferralTier(db.Model):
    """Referral tiers with different rewards based on performance"""
    __tablename__ = 'referral_tiers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    name_ar = Column(String(50), nullable=False)
    min_referrals = Column(Integer, default=0)
    max_referrals = Column(Integer, nullable=True)
    
    # Rewards
    referrer_reward_multiplier = Column(Float, default=1.0)  # Multiply base reward
    referred_reward_multiplier = Column(Float, default=1.0)
    bonus_credits = Column(Integer, default=0)  # Bonus credits for reaching tier
    
    # Tier benefits
    benefits = Column(Text)  # JSON string of benefits
    badge_icon = Column(String(100))  # Icon for the tier
    badge_color = Column(String(20), default='#3B82F6')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __init__(self, name, name_ar, min_referrals, max_referrals=None, 
                 referrer_reward_multiplier=1.0, referred_reward_multiplier=1.0, 
                 bonus_credits=0, benefits=None):
        self.name = name
        self.name_ar = name_ar
        self.min_referrals = min_referrals
        self.max_referrals = max_referrals
        self.referrer_reward_multiplier = referrer_reward_multiplier
        self.referred_reward_multiplier = referred_reward_multiplier
        self.bonus_credits = bonus_credits
        self.benefits = benefits or '[]'
    
    def save(self):
        """Save tier to database"""
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'min_referrals': self.min_referrals,
            'max_referrals': self.max_referrals,
            'referrer_reward_multiplier': self.referrer_reward_multiplier,
            'referred_reward_multiplier': self.referred_reward_multiplier,
            'bonus_credits': self.bonus_credits,
            'benefits': json.loads(self.benefits) if self.benefits else [],
            'badge_icon': self.badge_icon,
            'badge_color': self.badge_color,
            'created_at': self.created_at.isoformat()
        }

class ReferralCampaign(db.Model):
    """Special referral campaigns with limited time offers"""
    __tablename__ = 'referral_campaigns'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    description = Column(Text)
    description_ar = Column(Text)
    
    # Campaign settings
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Enhanced rewards during campaign
    referrer_bonus_credits = Column(Integer, default=0)
    referred_bonus_credits = Column(Integer, default=0)
    referrer_bonus_multiplier = Column(Float, default=1.0)
    referred_bonus_multiplier = Column(Float, default=1.0)
    
    # Campaign limits
    max_participants = Column(Integer, nullable=True)
    current_participants = Column(Integer, default=0)
    max_referrals_per_user = Column(Integer, default=10)
    
    # Campaign tracking
    total_referrals = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_rewards_given = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_campaign_active(self):
        """Check if campaign is currently active"""
        now = datetime.utcnow()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and
                (self.max_participants is None or self.current_participants < self.max_participants))
    
    def join_campaign(self):
        """Join the campaign (increment participants)"""
        if self.is_campaign_active() and (self.max_participants is None or self.current_participants < self.max_participants):
            self.current_participants += 1
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def save(self):
        """Save campaign to database"""
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'referrer_bonus_credits': self.referrer_bonus_credits,
            'referred_bonus_credits': self.referred_bonus_credits,
            'referrer_bonus_multiplier': self.referrer_bonus_multiplier,
            'referred_bonus_multiplier': self.referred_bonus_multiplier,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'max_referrals_per_user': self.max_referrals_per_user,
            'total_referrals': self.total_referrals,
            'total_conversions': self.total_conversions,
            'total_rewards_given': self.total_rewards_given,
            'is_campaign_active': self.is_campaign_active(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

