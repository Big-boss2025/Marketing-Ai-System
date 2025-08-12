
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from src.models.user import User
from src.models.subscription import SubscriptionPlan as Subscription
from src.services.odoo_complete_integration import odoo_integration
from src.services.credit_manager import credit_manager
logger = logging.getLogger(__name__)

class SubscriptionChecker:
    """Comprehensive Subscription Checker and Manager"""
    
    def __init__(self):
        # Subscription plans configuration
        self.subscription_plans = {
            'free': {
                'name': 'Free Plan',
                'credits_per_month': 100,
                'max_credits': 100,
                'features': ['basic_ai', 'limited_posting'],
                'price': 0,
                'limitations': {
                    'posts_per_day': 3,
                    'platforms': ['facebook', 'instagram'],
                    'ai_generations': 10
                }
            },
            'basic': {
                'name': 'Basic Plan',
                'credits_per_month': 500,
                'max_credits': 1000,
                'features': ['basic_ai', 'social_posting', 'basic_analytics'],
                'price': 29.99,
                'limitations': {
                    'posts_per_day': 10,
                    'platforms': ['facebook', 'instagram', 'twitter'],
                    'ai_generations': 50
                }
            },
            'pro': {
                'name': 'Pro Plan',
                'credits_per_month': 1500,
                'max_credits': 3000,
                'features': ['advanced_ai', 'all_platforms', 'advanced_analytics', 'priority_support'],
                'price': 79.99,
                'limitations': {
                    'posts_per_day': 25,
                    'platforms': ['facebook', 'instagram', 'twitter', 'tiktok', 'youtube'],
                    'ai_generations': 150
                }
            },
            'enterprise': {
                'name': 'Enterprise Plan',
                'credits_per_month': 5000,
                'max_credits': 10000,
                'features': ['unlimited_ai', 'white_label', 'custom_integrations', 'dedicated_support'],
                'price': 199.99,
                'limitations': {
                    'posts_per_day': 100,
                    'platforms': ['facebook', 'instagram', 'twitter', 'tiktok', 'youtube'],
                    'ai_generations': 500
                }
            }
        }
        
        # Credit costs for different operations
        self.credit_costs = {
            'text_generation': 2,
            'image_generation': 5,
            'video_generation': 15,
            'social_post': 1,
            'analytics_report': 3,
            'trend_analysis': 4,
            'auto_response': 1
        }
        
        # Grace period for expired subscriptions (days)
        self.grace_period_days = 7
    
    def check_user_subscription_status(self, user_id: int) -> Dict:
        """Check comprehensive subscription status for user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found',
                    'status': 'user_not_found'
                }
            
            # Get active subscription
            active_subscription = Subscription.query.filter_by(
                user_id=user_id,
                status='active'
            ).order_by(Subscription.created_at.desc()).first()
            
            # Check Odoo subscription status
            odoo_status = self.check_odoo_subscription_status(user_id)
            
            # Determine current plan
            current_plan = 'free'  # Default
            subscription_valid = False
            subscription_expires = None
            
            if active_subscription:
                current_plan = active_subscription.plan_type
                subscription_valid = True
                subscription_expires = active_subscription.next_billing_date
                
                # Check if subscription is expired
                if subscription_expires and subscription_expires < datetime.utcnow():
                    # Check grace period
                    grace_end = subscription_expires + timedelta(days=self.grace_period_days)
                    if datetime.utcnow() > grace_end:
                        subscription_valid = False
                        current_plan = 'free'
                        
                        # Update subscription status
                        active_subscription.status = 'expired'
                        from src.models.base import db
                        db.session.commit()
            
            # Get plan details
            plan_details = self.subscription_plans.get(current_plan, self.subscription_plans['free'])
            
            # Check credits balance
            credits_balance = user.credits_balance or 0
            credits_status = self.analyze_credits_status(user_id, credits_balance, plan_details)
            
            # Check usage limits
            usage_status = self.check_usage_limits(user_id, current_plan)
            
            # Generate recommendations
            recommendations = self.generate_subscription_recommendations(
                user_id, current_plan, credits_balance, usage_status
            )
            
            return {
                'success': True,
                'user_id': user_id,
                'subscription_status': {
                    'is_subscribed': subscription_valid,
                    'current_plan': current_plan,
                    'plan_name': plan_details['name'],
                    'expires_at': subscription_expires.isoformat() if subscription_expires else None,
                    'in_grace_period': self.is_in_grace_period(subscription_expires) if subscription_expires else False,
                    'odoo_status': odoo_status
                },
                'credits_status': credits_status,
                'usage_status': usage_status,
                'plan_details': plan_details,
                'recommendations': recommendations,
                'actions_required': self.get_required_actions(subscription_valid, credits_balance, usage_status)
            }
            
        except Exception as e:
            logger.error(f"Error checking subscription status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'check_failed'
            }
    
    def check_odoo_subscription_status(self, user_id: int) -> Dict:
        """Check subscription status from Odoo"""
        try:
            result = odoo_integration.get_user_subscription_status(user_id)
            
            if result['success']:
                return {
                    'has_odoo_subscription': result['has_active_subscription'],
                    'subscriptions': result['subscriptions'],
                    'last_checked': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'has_odoo_subscription': False,
                    'error': result.get('error'),
                    'last_checked': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error checking Odoo subscription: {str(e)}")
            return {
                'has_odoo_subscription': False,
                'error': str(e),
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def analyze_credits_status(self, user_id: int, credits_balance: int, plan_details: Dict) -> Dict:
        """Analyze user's credits status"""
        try:
            max_credits = plan_details.get('max_credits', 100)
            monthly_credits = plan_details.get('credits_per_month', 100)
            
            # Calculate credits usage this month
            from src.models.credit_transaction import CreditTransaction
            
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            monthly_usage = CreditTransaction.query.filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.transaction_type.in_(['deduct', 'task_cost']),
                CreditTransaction.created_at >= month_start
            ).with_entities(
                CreditTransaction.amount
            ).all()
            
            total_used = sum([abs(transaction.amount) for transaction in monthly_usage])
            
            # Calculate percentages
            balance_percentage = (credits_balance / max_credits) * 100 if max_credits > 0 else 0
            usage_percentage = (total_used / monthly_credits) * 100 if monthly_credits > 0 else 0
            
            # Determine status
            if credits_balance <= 0:
                status = 'depleted'
                urgency = 'critical'
            elif credits_balance < 50:
                status = 'low'
                urgency = 'high'
            elif balance_percentage < 25:
                status = 'moderate'
                urgency = 'medium'
            else:
                status = 'good'
                urgency = 'low'
            
            return {
                'current_balance': credits_balance,
                'max_credits': max_credits,
                'monthly_allowance': monthly_credits,
                'used_this_month': total_used,
                'balance_percentage': round(balance_percentage, 2),
                'usage_percentage': round(usage_percentage, 2),
                'status': status,
                'urgency': urgency,
                'estimated_days_remaining': self.estimate_credits_duration(user_id, credits_balance)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing credits status: {str(e)}")
            return {
                'current_balance': credits_balance,
                'status': 'unknown',
                'error': str(e)
            }
    
    def check_usage_limits(self, user_id: int, plan_type: str) -> Dict:
        """Check usage against plan limitations"""
        try:
            plan_limits = self.subscription_plans.get(plan_type, {}).get('limitations', {})
            
            # Check daily posts limit
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            from src.models.content import Content
            posts_today = Content.query.filter(
                Content.user_id == user_id,
                Content.created_at >= today_start,
                Content.status == 'published'
            ).count()
            
            daily_limit = plan_limits.get('posts_per_day', 999)
            
            # Check AI generations this month
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            from src.models.credit_transaction import CreditTransaction
            ai_generations = CreditTransaction.query.filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.transaction_type.in_(['text_generation', 'image_generation', 'video_generation']),
                CreditTransaction.created_at >= month_start
            ).count()
            
            ai_limit = plan_limits.get('ai_generations', 999)
            
            # Check platform access
            allowed_platforms = plan_limits.get('platforms', ['facebook', 'instagram', 'twitter', 'tiktok', 'youtube'])
            
            return {
                'daily_posts': {
                    'used': posts_today,
                    'limit': daily_limit,
                    'remaining': max(0, daily_limit - posts_today),
                    'percentage': (posts_today / daily_limit) * 100 if daily_limit > 0 else 0,
                    'exceeded': posts_today >= daily_limit
                },
                'ai_generations': {
                    'used': ai_generations,
                    'limit': ai_limit,
                    'remaining': max(0, ai_limit - ai_generations),
                    'percentage': (ai_generations / ai_limit) * 100 if ai_limit > 0 else 0,
                    'exceeded': ai_generations >= ai_limit
                },
                'platforms': {
                    'allowed': allowed_platforms,
                    'total_allowed': len(allowed_platforms)
                },
                'overall_status': 'within_limits' if posts_today < daily_limit and ai_generations < ai_limit else 'limits_exceeded'
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {str(e)}")
            return {
                'overall_status': 'check_failed',
                'error': str(e)
            }
    
    def estimate_credits_duration(self, user_id: int, current_balance: int) -> Optional[int]:
        """Estimate how many days credits will last"""
        try:
            if current_balance <= 0:
                return 0
            
            # Calculate average daily usage from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            from src.models.credit_transaction import CreditTransaction
            
            recent_usage = CreditTransaction.query.filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.transaction_type.in_(['deduct', 'task_cost']),
                CreditTransaction.created_at >= thirty_days_ago
            ).with_entities(
                CreditTransaction.amount
            ).all()
            
            if not recent_usage:
                return None  # No usage history
            
            total_used = sum([abs(transaction.amount) for transaction in recent_usage])
            daily_average = total_used / 30
            
            if daily_average <= 0:
                return None  # No usage
            
            estimated_days = int(current_balance / daily_average)
            return min(estimated_days, 365)  # Cap at 1 year
            
        except Exception as e:
            logger.error(f"Error estimating credits duration: {str(e)}")
            return None
    
    def is_in_grace_period(self, expiration_date: datetime) -> bool:
        """Check if subscription is in grace period"""
        if not expiration_date:
            return False
        
        grace_end = expiration_date + timedelta(days=self.grace_period_days)
        return expiration_date < datetime.utcnow() <= grace_end
    
    def generate_subscription_recommendations(self, user_id: int, current_plan: str, 
                                           credits_balance: int, usage_status: Dict) -> List[Dict]:
        """Generate subscription recommendations"""
        try:
            recommendations = []
            
            # Low credits recommendation
            if credits_balance < 50:
                recommendations.append({
                    'type': 'credits_low',
                    'priority': 'high',
                    'title': 'Credits Running Low',
                    'message': f'You have only {credits_balance} credits remaining.',
                    'actions': [
                        {'type': 'buy_credits', 'label': 'Buy More Credits'},
                        {'type': 'upgrade_plan', 'label': 'Upgrade Plan'}
                    ]
                })
            
            # Usage limits exceeded
            if usage_status.get('overall_status') == 'limits_exceeded':
                recommendations.append({
                    'type': 'limits_exceeded',
                    'priority': 'high',
                    'title': 'Usage Limits Exceeded',
                    'message': 'You have reached your plan limits for today.',
                    'actions': [
                        {'type': 'upgrade_plan', 'label': 'Upgrade Plan'},
                        {'type': 'wait', 'label': 'Wait for Reset Tomorrow'}
                    ]
                })
            
            # Plan upgrade recommendations
            if current_plan == 'free':
                recommendations.append({
                    'type': 'upgrade_suggestion',
                    'priority': 'medium',
                    'title': 'Unlock More Features',
                    'message': 'Upgrade to Basic plan for more credits and platforms.',
                    'actions': [
                        {'type': 'upgrade_to_basic', 'label': 'Upgrade to Basic ($29.99/month)'}
                    ]
                })
            elif current_plan == 'basic':
                daily_posts = usage_status.get('daily_posts', {})
                if daily_posts.get('percentage', 0) > 80:
                    recommendations.append({
                        'type': 'upgrade_suggestion',
                        'priority': 'medium',
                        'title': 'Consider Pro Plan',
                        'message': 'You are using most of your daily post limit.',
                        'actions': [
                            {'type': 'upgrade_to_pro', 'label': 'Upgrade to Pro ($79.99/month)'}
                        ]
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def get_required_actions(self, subscription_valid: bool, credits_balance: int, usage_status: Dict) -> List[str]:
        """Get list of required actions"""
        actions = []
        
        if not subscription_valid:
            actions.append('renew_subscription')
        
        if credits_balance <= 0:
            actions.append('buy_credits')
        
        if usage_status.get('overall_status') == 'limits_exceeded':
            actions.append('upgrade_plan_or_wait')
        
        return actions
    
    def can_perform_action(self, user_id: int, action_type: str, cost: Optional[int] = None) -> Dict:
        """Check if user can perform a specific action"""
        try:
            # Get subscription status
            status = self.check_user_subscription_status(user_id)
            
            if not status['success']:
                return status
            
            subscription_status = status['subscription_status']
            credits_status = status['credits_status']
            usage_status = status['usage_status']
            plan_details = status['plan_details']
            
            # Check subscription validity
            if not subscription_status['is_subscribed'] and action_type not in ['text_generation', 'social_post']:
                return {
                    'success': False,
                    'can_perform': False,
                    'reason': 'subscription_required',
                    'message': 'Active subscription required for this action',
                    'required_action': 'subscribe'
                }
            
            # Check credits
            action_cost = cost or self.credit_costs.get(action_type, 1)
            current_balance = credits_status['current_balance']
            
            if current_balance < action_cost:
                return {
                    'success': True,
                    'can_perform': False,
                    'reason': 'insufficient_credits',
                    'message': f'Insufficient credits. Need {action_cost}, have {current_balance}',
                    'required_action': 'buy_credits',
                    'cost': action_cost,
                    'balance': current_balance
                }
            
            # Check usage limits
            if action_type == 'social_post':
                daily_posts = usage_status.get('daily_posts', {})
                if daily_posts.get('exceeded', False):
                    return {
                        'success': True,
                        'can_perform': False,
                        'reason': 'daily_limit_exceeded',
                        'message': f'Daily post limit exceeded ({daily_posts.get("used", 0)}/{daily_posts.get("limit", 0)})',
                        'required_action': 'upgrade_plan_or_wait'
                    }
            
            elif action_type in ['text_generation', 'image_generation', 'video_generation']:
                ai_generations = usage_status.get('ai_generations', {})
                if ai_generations.get('exceeded', False):
                    return {
                        'success': True,
                        'can_perform': False,
                        'reason': 'ai_limit_exceeded',
                        'message': f'Monthly AI generation limit exceeded ({ai_generations.get("used", 0)}/{ai_generations.get("limit", 0)})',
                        'required_action': 'upgrade_plan'
                    }
            
            # All checks passed
            return {
                'success': True,
                'can_perform': True,
                'cost': action_cost,
                'remaining_balance': current_balance - action_cost,
                'message': 'Action can be performed'
            }
            
        except Exception as e:
            logger.error(f"Error checking action permission: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'can_perform': False
            }
    
    def add_monthly_credits_if_due(self, user_id: int) -> Dict:
        """Add monthly credits if subscription is due for renewal"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get active subscription
            subscription = Subscription.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            if not subscription:
                return {'success': False, 'error': 'No active subscription'}
            
            # Check if credits are due
            if subscription.next_billing_date and subscription.next_billing_date <= datetime.utcnow():
                plan_details = self.subscription_plans.get(subscription.plan_type, {})
                monthly_credits = plan_details.get('credits_per_month', 0)
                
                if monthly_credits > 0:
                    # Add monthly credits
                    result = credit_manager.add_credits(
                        user_id=user_id,
                        amount=monthly_credits,
                        transaction_type='monthly_subscription',
                        description=f'Monthly credits for {subscription.plan_type} plan'
                    )
                    
                    if result['success']:
                        # Update next billing date
                        subscription.next_billing_date = subscription.next_billing_date + timedelta(days=30)
                        from src.models.base import db
                        db.session.commit()
                        
                        return {
                            'success': True,
                            'message': 'Monthly credits added',
                            'credits_added': monthly_credits,
                            'next_billing_date': subscription.next_billing_date.isoformat()
                        }
                    else:
                        return result
            
            return {'success': True, 'message': 'No credits due at this time'}
            
        except Exception as e:
            logger.error(f"Error adding monthly credits: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_upgrade_options(self, user_id: int) -> Dict:
        """Get available upgrade options for user"""
        try:
            status = self.check_user_subscription_status(user_id)
            
            if not status['success']:
                return status
            
            current_plan = status['subscription_status']['current_plan']
            
            # Available upgrades
            plan_hierarchy = ['free', 'basic', 'pro', 'enterprise']
            current_index = plan_hierarchy.index(current_plan) if current_plan in plan_hierarchy else 0
            
            upgrade_options = []
            for i in range(current_index + 1, len(plan_hierarchy)):
                plan_type = plan_hierarchy[i]
                plan_details = self.subscription_plans[plan_type]
                
                upgrade_options.append({
                    'plan_type': plan_type,
                    'name': plan_details['name'],
                    'price': plan_details['price'],
                    'credits_per_month': plan_details['credits_per_month'],
                    'features': plan_details['features'],
                    'limitations': plan_details['limitations']
                })
            
            return {
                'success': True,
                'current_plan': current_plan,
                'upgrade_options': upgrade_options
            }
            
        except Exception as e:
            logger.error(f"Error getting upgrade options: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global subscription checker instance
subscription_checker = SubscriptionChecker()

