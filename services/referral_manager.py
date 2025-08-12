import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_, desc, func
from src.models.referral import ReferralCode, Referral, ReferralTier, ReferralCampaign
from src.models.user import User
from src.services.credit_manager import credit_manager
from src.services.free_ai_generator import free_ai_generator

logger = logging.getLogger(__name__)

class ReferralManager:
    """Comprehensive Referral System Manager"""
    
    def __init__(self):
        # Default referral tiers
        self.default_tiers = [
            {
                'name': 'Bronze Referrer',
                'name_ar': 'مُحيل برونزي',
                'min_referrals': 0,
                'max_referrals': 4,
                'referrer_reward_multiplier': 1.0,
                'referred_reward_multiplier': 1.0,
                'bonus_credits': 0,
                'benefits': ['Basic referral rewards', 'Standard support'],
                'badge_color': '#CD7F32'
            },
            {
                'name': 'Silver Referrer',
                'name_ar': 'مُحيل فضي',
                'min_referrals': 5,
                'max_referrals': 14,
                'referrer_reward_multiplier': 1.2,
                'referred_reward_multiplier': 1.1,
                'bonus_credits': 50,
                'benefits': ['20% bonus rewards', 'Priority support', 'Exclusive content'],
                'badge_color': '#C0C0C0'
            },
            {
                'name': 'Gold Referrer',
                'name_ar': 'مُحيل ذهبي',
                'min_referrals': 15,
                'max_referrals': 49,
                'referrer_reward_multiplier': 1.5,
                'referred_reward_multiplier': 1.2,
                'bonus_credits': 150,
                'benefits': ['50% bonus rewards', 'VIP support', 'Early access to features', 'Monthly bonus credits'],
                'badge_color': '#FFD700'
            },
            {
                'name': 'Platinum Referrer',
                'name_ar': 'مُحيل بلاتيني',
                'min_referrals': 50,
                'max_referrals': 99,
                'referrer_reward_multiplier': 2.0,
                'referred_reward_multiplier': 1.5,
                'bonus_credits': 500,
                'benefits': ['100% bonus rewards', 'Dedicated account manager', 'Custom features', 'Revenue sharing'],
                'badge_color': '#E5E4E2'
            },
            {
                'name': 'Diamond Referrer',
                'name_ar': 'مُحيل ماسي',
                'min_referrals': 100,
                'max_referrals': None,
                'referrer_reward_multiplier': 3.0,
                'referred_reward_multiplier': 2.0,
                'bonus_credits': 1000,
                'benefits': ['200% bonus rewards', 'Partnership opportunities', 'Co-marketing', 'Revenue sharing'],
                'badge_color': '#B9F2FF'
            }
        ]
        
        # Referral tracking settings
        self.tracking_settings = {
            'cookie_duration_days': 30,  # How long referral tracking lasts
            'conversion_events': ['signup', 'first_purchase', 'subscription', 'credit_purchase'],
            'min_conversion_value': 0.0,
            'fraud_detection_enabled': True
        }
    
    def initialize_default_tiers(self):
        """Initialize default referral tiers if they don't exist"""
        try:
            existing_tiers = ReferralTier.query.count()
            
            if existing_tiers == 0:
                for tier_data in self.default_tiers:
                    tier = ReferralTier(
                        name=tier_data['name'],
                        name_ar=tier_data['name_ar'],
                        min_referrals=tier_data['min_referrals'],
                        max_referrals=tier_data['max_referrals'],
                        referrer_reward_multiplier=tier_data['referrer_reward_multiplier'],
                        referred_reward_multiplier=tier_data['referred_reward_multiplier'],
                        bonus_credits=tier_data['bonus_credits'],
                        benefits=str(tier_data['benefits']),
                        badge_color=tier_data['badge_color']
                    )
                    tier.save()
                
                logger.info("Default referral tiers initialized")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error initializing default tiers: {str(e)}")
            return False
    
    def create_referral_code(self, user_id: int, reward_type: str = 'credits', 
                           reward_value: float = 10.0, max_usage: int = 100) -> Dict:
        """Create a new referral code for a user"""
        try:
            # Check if user exists
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check if user already has an active referral code
            existing_code = ReferralCode.query.filter_by(
                user_id=user_id, 
                is_active=True
            ).first()
            
            if existing_code:
                return {
                    'success': True,
                    'referral_code': existing_code.to_dict(),
                    'message': 'User already has an active referral code'
                }
            
            # Create new referral code
            referral_code = ReferralCode(
                user_id=user_id,
                reward_type=reward_type,
                reward_value=reward_value,
                max_usage=max_usage
            )
            referral_code.save()
            
            return {
                'success': True,
                'referral_code': referral_code.to_dict(),
                'message': 'Referral code created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating referral code: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def use_referral_code(self, code: str, referred_user_id: int, 
                         ip_address: str = None, user_agent: str = None) -> Dict:
        """Use a referral code when a new user signs up"""
        try:
            # Find the referral code
            referral_code = ReferralCode.query.filter_by(code=code.upper()).first()
            
            if not referral_code:
                return {'success': False, 'error': 'Invalid referral code'}
            
            if not referral_code.is_valid():
                return {'success': False, 'error': 'Referral code is expired or reached maximum usage'}
            
            # Check if referred user exists
            referred_user = User.query.get(referred_user_id)
            if not referred_user:
                return {'success': False, 'error': 'Referred user not found'}
            
            # Check if user is trying to refer themselves
            if referral_code.user_id == referred_user_id:
                return {'success': False, 'error': 'Cannot use your own referral code'}
            
            # Check if user was already referred
            existing_referral = Referral.query.filter_by(referred_id=referred_user_id).first()
            if existing_referral:
                return {'success': False, 'error': 'User was already referred'}
            
            # Get current tier for referrer
            referrer_tier = self.get_user_tier(referral_code.user_id)
            
            # Calculate rewards based on tier
            referrer_reward = referral_code.reward_value * referrer_tier['referrer_reward_multiplier']
            referred_reward = referral_code.reward_value * 0.5 * referrer_tier['referred_reward_multiplier']
            
            # Check for active campaigns
            active_campaign = self.get_active_campaign()
            if active_campaign:
                referrer_reward += active_campaign['referrer_bonus_credits']
                referred_reward += active_campaign['referred_bonus_credits']
                referrer_reward *= active_campaign['referrer_bonus_multiplier']
                referred_reward *= active_campaign['referred_bonus_multiplier']
            
            # Create referral record
            referral = Referral(
                referrer_id=referral_code.user_id,
                referred_id=referred_user_id,
                referral_code_id=referral_code.id,
                referrer_reward_type='credits',
                referrer_reward_value=referrer_reward,
                referred_reward_type='credits',
                referred_reward_value=referred_reward,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Complete referral immediately for signup
            referral.complete_referral('signup', 0.0)
            referral.save()
            
            # Use the referral code
            referral_code.use_code()
            referral_code.save()
            
            # Update campaign stats if applicable
            if active_campaign:
                self.update_campaign_stats(active_campaign['id'], 1, 1)
            
            return {
                'success': True,
                'referral': referral.to_dict(),
                'referrer_reward': referrer_reward,
                'referred_reward': referred_reward,
                'message': 'Referral code used successfully'
            }
            
        except Exception as e:
            logger.error(f"Error using referral code: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_user_tier(self, user_id: int) -> Dict:
        """Get user's current referral tier"""
        try:
            # Count successful referrals
            referral_count = Referral.query.filter_by(
                referrer_id=user_id,
                status='completed'
            ).count()
            
            # Find appropriate tier
            tier = ReferralTier.query.filter(
                and_(
                    ReferralTier.min_referrals <= referral_count,
                    or_(
                        ReferralTier.max_referrals.is_(None),
                        ReferralTier.max_referrals >= referral_count
                    )
                )
            ).order_by(desc(ReferralTier.min_referrals)).first()
            
            if not tier:
                # Return default tier if none found
                return {
                    'name': 'Bronze Referrer',
                    'name_ar': 'مُحيل برونزي',
                    'referrer_reward_multiplier': 1.0,
                    'referred_reward_multiplier': 1.0,
                    'current_referrals': referral_count
                }
            
            tier_dict = tier.to_dict()
            tier_dict['current_referrals'] = referral_count
            
            # Calculate progress to next tier
            next_tier = ReferralTier.query.filter(
                ReferralTier.min_referrals > referral_count
            ).order_by(ReferralTier.min_referrals).first()
            
            if next_tier:
                tier_dict['next_tier'] = next_tier.to_dict()
                tier_dict['referrals_to_next_tier'] = next_tier.min_referrals - referral_count
            else:
                tier_dict['next_tier'] = None
                tier_dict['referrals_to_next_tier'] = 0
            
            return tier_dict
            
        except Exception as e:
            logger.error(f"Error getting user tier: {str(e)}")
            return {'error': str(e)}
    
    def get_user_referral_stats(self, user_id: int) -> Dict:
        """Get comprehensive referral statistics for a user"""
        try:
            # Get user's referral code
            referral_code = ReferralCode.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            # Get referral statistics
            total_referrals = Referral.query.filter_by(referrer_id=user_id).count()
            completed_referrals = Referral.query.filter_by(
                referrer_id=user_id,
                status='completed'
            ).count()
            pending_referrals = Referral.query.filter_by(
                referrer_id=user_id,
                status='pending'
            ).count()
            
            # Calculate total rewards earned
            total_rewards = Referral.query.filter_by(
                referrer_id=user_id,
                referrer_reward_given=True
            ).with_entities(func.sum(Referral.referrer_reward_value)).scalar() or 0
            
            # Get recent referrals
            recent_referrals = Referral.query.filter_by(
                referrer_id=user_id
            ).order_by(desc(Referral.referred_at)).limit(10).all()
            
            # Get current tier
            current_tier = self.get_user_tier(user_id)
            
            # Calculate conversion rate
            conversion_rate = (completed_referrals / total_referrals * 100) if total_referrals > 0 else 0
            
            return {
                'success': True,
                'user_id': user_id,
                'referral_code': referral_code.to_dict() if referral_code else None,
                'stats': {
                    'total_referrals': total_referrals,
                    'completed_referrals': completed_referrals,
                    'pending_referrals': pending_referrals,
                    'conversion_rate': round(conversion_rate, 2),
                    'total_rewards_earned': total_rewards,
                    'current_tier': current_tier
                },
                'recent_referrals': [r.to_dict() for r in recent_referrals]
            }
            
        except Exception as e:
            logger.error(f"Error getting user referral stats: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_referral_campaign(self, campaign_data: Dict) -> Dict:
        """Create a new referral campaign"""
        try:
            campaign = ReferralCampaign(
                name=campaign_data['name'],
                name_ar=campaign_data['name_ar'],
                description=campaign_data.get('description', ''),
                description_ar=campaign_data.get('description_ar', ''),
                start_date=datetime.fromisoformat(campaign_data['start_date']),
                end_date=datetime.fromisoformat(campaign_data['end_date']),
                referrer_bonus_credits=campaign_data.get('referrer_bonus_credits', 0),
                referred_bonus_credits=campaign_data.get('referred_bonus_credits', 0),
                referrer_bonus_multiplier=campaign_data.get('referrer_bonus_multiplier', 1.0),
                referred_bonus_multiplier=campaign_data.get('referred_bonus_multiplier', 1.0),
                max_participants=campaign_data.get('max_participants'),
                max_referrals_per_user=campaign_data.get('max_referrals_per_user', 10)
            )
            campaign.save()
            
            return {
                'success': True,
                'campaign': campaign.to_dict(),
                'message': 'Referral campaign created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating referral campaign: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_active_campaign(self) -> Optional[Dict]:
        """Get currently active referral campaign"""
        try:
            campaign = ReferralCampaign.query.filter_by(is_active=True).first()
            
            if campaign and campaign.is_campaign_active():
                return campaign.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting active campaign: {str(e)}")
            return None
    
    def update_campaign_stats(self, campaign_id: int, referrals_increment: int = 0, 
                            conversions_increment: int = 0, rewards_increment: float = 0.0):
        """Update campaign statistics"""
        try:
            campaign = ReferralCampaign.query.get(campaign_id)
            if campaign:
                campaign.total_referrals += referrals_increment
                campaign.total_conversions += conversions_increment
                campaign.total_rewards_given += rewards_increment
                campaign.save()
                
        except Exception as e:
            logger.error(f"Error updating campaign stats: {str(e)}")
    
    def generate_referral_content(self, user_id: int, language: str = 'ar') -> Dict:
        """Generate AI-powered referral content for sharing"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            referral_code = ReferralCode.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if not referral_code:
                return {'success': False, 'error': 'No active referral code found'}
            
            # Get user's tier for personalized content
            user_tier = self.get_user_tier(user_id)
            
            # Generate content based on language
            if language == 'ar':
                content_prompts = [
                    f"🚀 اكتشف أقوى نظام تسويق آلي! استخدم كود الإحالة {referral_code.code} واحصل على {referral_code.reward_value} كريديت مجاناً!",
                    f"💎 انضم لآلاف العملاء الناجحين! كود الإحالة: {referral_code.code} - مكافأة فورية {referral_code.reward_value} كريديت!",
                    f"🎯 نظام تسويق ذكي يعمل لوحده 24/7! ابدأ بـ {referral_code.reward_value} كريديت مجاني - كود: {referral_code.code}",
                    f"⚡ تسويق آلي + ذكاء اصطناعي = نجاح مضمون! استخدم {referral_code.code} واحصل على {referral_code.reward_value} كريديت!"
                ]
                
                hashtags = ['#تسويق_آلي', '#ذكاء_اصطناعي', '#نجاح', '#أعمال', '#ريادة', '#تقنية']
                
            else:
                content_prompts = [
                    f"🚀 Discover the most powerful marketing automation system! Use referral code {referral_code.code} and get {referral_code.reward_value} free credits!",
                    f"💎 Join thousands of successful customers! Referral code: {referral_code.code} - Instant {referral_code.reward_value} credits bonus!",
                    f"🎯 Smart marketing system that works 24/7! Start with {referral_code.reward_value} free credits - Code: {referral_code.code}",
                    f"⚡ Marketing Automation + AI = Guaranteed Success! Use {referral_code.code} and get {referral_code.reward_value} credits!"
                ]
                
                hashtags = ['#MarketingAutomation', '#AI', '#Success', '#Business', '#Entrepreneurship', '#Technology']
            
            # Select random content
            import random
            selected_content = random.choice(content_prompts)
            selected_hashtags = random.sample(hashtags, 4)
            
            # Generate image for the referral post
            image_result = free_ai_generator.generate_content_image(
                selected_content, 
                "Marketing Automation System", 
                language
            )
            
            return {
                'success': True,
                'content': {
                    'text': selected_content,
                    'hashtags': selected_hashtags,
                    'referral_code': referral_code.code,
                    'reward_value': referral_code.reward_value,
                    'user_tier': user_tier['name_ar'] if language == 'ar' else user_tier['name'],
                    'image_url': image_result.get('image_url') if image_result['success'] else None
                },
                'sharing_urls': {
                    'facebook': f"https://www.facebook.com/sharer/sharer.php?u=https://yoursite.com/signup?ref={referral_code.code}",
                    'twitter': f"https://twitter.com/intent/tweet?text={selected_content}&url=https://yoursite.com/signup?ref={referral_code.code}",
                    'whatsapp': f"https://wa.me/?text={selected_content} https://yoursite.com/signup?ref={referral_code.code}",
                    'telegram': f"https://t.me/share/url?url=https://yoursite.com/signup?ref={referral_code.code}&text={selected_content}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating referral content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_leaderboard(self, limit: int = 10, period: str = 'all_time') -> Dict:
        """Get referral leaderboard"""
        try:
            # Calculate date filter based on period
            date_filter = None
            if period == 'this_month':
                date_filter = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == 'this_week':
                date_filter = datetime.now() - timedelta(days=7)
            elif period == 'today':
                date_filter = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Build query
            query = Referral.query.filter_by(status='completed')
            
            if date_filter:
                query = query.filter(Referral.converted_at >= date_filter)
            
            # Group by referrer and count
            leaderboard_data = query.with_entities(
                Referral.referrer_id,
                func.count(Referral.id).label('referral_count'),
                func.sum(Referral.referrer_reward_value).label('total_rewards')
            ).group_by(Referral.referrer_id).order_by(
                desc('referral_count')
            ).limit(limit).all()
            
            # Build leaderboard with user details
            leaderboard = []
            for rank, (user_id, referral_count, total_rewards) in enumerate(leaderboard_data, 1):
                user = User.query.get(user_id)
                user_tier = self.get_user_tier(user_id)
                
                leaderboard.append({
                    'rank': rank,
                    'user_id': user_id,
                    'username': user.username if user else 'Unknown',
                    'referral_count': referral_count,
                    'total_rewards': float(total_rewards or 0),
                    'tier': user_tier['name_ar'],
                    'tier_color': user_tier.get('badge_color', '#3B82F6')
                })
            
            return {
                'success': True,
                'period': period,
                'leaderboard': leaderboard,
                'total_entries': len(leaderboard)
            }
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_referral_analytics(self, days: int = 30) -> Dict:
        """Get referral system analytics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Basic stats
            total_referrals = Referral.query.filter(
                Referral.referred_at >= start_date
            ).count()
            
            completed_referrals = Referral.query.filter(
                and_(
                    Referral.referred_at >= start_date,
                    Referral.status == 'completed'
                )
            ).count()
            
            total_rewards = Referral.query.filter(
                and_(
                    Referral.referred_at >= start_date,
                    Referral.referrer_reward_given == True
                )
            ).with_entities(func.sum(Referral.referrer_reward_value)).scalar() or 0
            
            # Conversion rate
            conversion_rate = (completed_referrals / total_referrals * 100) if total_referrals > 0 else 0
            
            # Top referrers
            top_referrers = Referral.query.filter(
                and_(
                    Referral.referred_at >= start_date,
                    Referral.status == 'completed'
                )
            ).with_entities(
                Referral.referrer_id,
                func.count(Referral.id).label('count')
            ).group_by(Referral.referrer_id).order_by(desc('count')).limit(5).all()
            
            # Daily referral trends
            daily_trends = []
            for i in range(days):
                day = start_date + timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                day_referrals = Referral.query.filter(
                    and_(
                        Referral.referred_at >= day_start,
                        Referral.referred_at < day_end
                    )
                ).count()
                
                daily_trends.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'referrals': day_referrals
                })
            
            return {
                'success': True,
                'period': f'{days} days',
                'analytics': {
                    'total_referrals': total_referrals,
                    'completed_referrals': completed_referrals,
                    'conversion_rate': round(conversion_rate, 2),
                    'total_rewards_given': float(total_rewards),
                    'average_reward_per_referral': float(total_rewards / completed_referrals) if completed_referrals > 0 else 0,
                    'top_referrers': [
                        {'user_id': user_id, 'referrals': count} 
                        for user_id, count in top_referrers
                    ],
                    'daily_trends': daily_trends
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting referral analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global referral manager instance
referral_manager = ReferralManager()

