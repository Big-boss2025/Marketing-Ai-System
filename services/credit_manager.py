from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from src.models.user import User
from src.models.credit_transaction import CreditTransaction, TaskCreditCost, CreditPackage
from src.models.subscription import UserSubscription
from src.models.task import Task
from src.models.base import db

logger = logging.getLogger(__name__)

class CreditManager:
    """Centralized credit management system"""
    
    def __init__(self):
        self.task_costs_cache = {}  # Cache for task costs
        self.last_cache_update = None
    
    def _update_task_costs_cache(self):
        """Update task costs cache"""
        if (not self.last_cache_update or 
            datetime.utcnow() - self.last_cache_update > timedelta(minutes=30)):
            
            costs = TaskCreditCost.get_all_active_costs()
            self.task_costs_cache = {cost.task_type: cost for cost in costs}
            self.last_cache_update = datetime.utcnow()
    
    def get_task_cost(self, task_type: str, **parameters) -> int:
        """Get credit cost for a specific task type"""
        self._update_task_costs_cache()
        
        if task_type in self.task_costs_cache:
            return self.task_costs_cache[task_type].calculate_cost(**parameters)
        
        # Default costs for common tasks if not configured
        default_costs = {
            'text_generation': 1,
            'image_generation': 3,
            'video_generation': 10,
            'social_media_post': 2,
            'content_analysis': 1,
            'hashtag_generation': 1,
            'trend_analysis': 2,
            'campaign_creation': 5,
            'performance_analysis': 2
        }
        
        return default_costs.get(task_type, 1)
    
    def check_user_credits(self, user_id: str, required_credits: int) -> Dict[str, Any]:
        """Check if user has enough credits"""
        user = User.get_by_id(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        has_enough = user.credits_balance >= required_credits
        
        return {
            'success': True,
            'has_enough_credits': has_enough,
            'current_balance': user.credits_balance,
            'required_credits': required_credits,
            'shortage': max(0, required_credits - user.credits_balance)
        }
    
    def deduct_credits(self, user_id: str, amount: int, description: str, 
                      category: str = 'task_execution', task_id: str = None,
                      metadata: Dict = None) -> Dict[str, Any]:
        """Deduct credits from user account"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if user.credits_balance < amount:
                return {
                    'success': False, 
                    'error': 'Insufficient credits',
                    'current_balance': user.credits_balance,
                    'required': amount
                }
            
            # Create transaction record
            transaction = CreditTransaction.create_transaction(
                user_id=user_id,
                amount=-amount,  # Negative for deduction
                description=description,
                category=category,
                related_task_id=task_id
            )
            
            if metadata:
                transaction.set_metadata(metadata)
                transaction.save()
            
            logger.info(f"Deducted {amount} credits from user {user_id}. New balance: {user.credits_balance}")
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'previous_balance': transaction.balance_before,
                'new_balance': transaction.balance_after,
                'amount_deducted': amount
            }
            
        except Exception as e:
            logger.error(f"Error deducting credits for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def add_credits(self, user_id: str, amount: int, description: str,
                   category: str = 'purchase', admin_user_id: str = None,
                   metadata: Dict = None) -> Dict[str, Any]:
        """Add credits to user account"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Create transaction record
            transaction = CreditTransaction.create_transaction(
                user_id=user_id,
                amount=amount,  # Positive for addition
                description=description,
                category=category,
                admin_user_id=admin_user_id
            )
            
            if metadata:
                transaction.set_metadata(metadata)
                transaction.save()
            
            logger.info(f"Added {amount} credits to user {user_id}. New balance: {user.credits_balance}")
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'previous_balance': transaction.balance_before,
                'new_balance': transaction.balance_after,
                'amount_added': amount
            }
            
        except Exception as e:
            logger.error(f"Error adding credits for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_subscription_credits(self, user_id: str) -> Dict[str, Any]:
        """Add monthly credits based on user's subscription"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get active subscription
            subscription = UserSubscription.get_active_subscription(user_id)
            if not subscription or not subscription.plan:
                return {'success': False, 'error': 'No active subscription found'}
            
            monthly_credits = subscription.plan.monthly_credits
            if monthly_credits <= 0:
                return {'success': False, 'error': 'Subscription plan has no monthly credits'}
            
            # Add credits
            result = self.add_credits(
                user_id=user_id,
                amount=monthly_credits,
                description=f"Monthly credits from {subscription.plan.name} subscription",
                category='subscription',
                metadata={
                    'subscription_id': subscription.id,
                    'plan_name': subscription.plan.name,
                    'billing_cycle': subscription.billing_cycle
                }
            )
            
            if result['success']:
                logger.info(f"Added {monthly_credits} monthly credits to user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing subscription credits for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_referral_credits(self, referrer_user_id: str, referred_user_id: str,
                               referral_type: str = 'signup') -> Dict[str, Any]:
        """Process referral credits for both referrer and referred user"""
        try:
            # Define referral credit amounts
            referral_credits = {
                'signup': {'referrer': 50, 'referred': 25},
                'first_purchase': {'referrer': 100, 'referred': 0},
                'subscription': {'referrer': 200, 'referred': 0}
            }
            
            if referral_type not in referral_credits:
                return {'success': False, 'error': 'Invalid referral type'}
            
            credits_config = referral_credits[referral_type]
            results = {}
            
            # Add credits to referrer
            if credits_config['referrer'] > 0:
                referrer_result = self.add_credits(
                    user_id=referrer_user_id,
                    amount=credits_config['referrer'],
                    description=f"Referral bonus - {referral_type}",
                    category='referral',
                    metadata={
                        'referral_type': referral_type,
                        'referred_user_id': referred_user_id
                    }
                )
                results['referrer'] = referrer_result
                
                # Update referrer's referral stats
                referrer = User.get_by_id(referrer_user_id)
                if referrer:
                    referrer.referral_credits_earned += credits_config['referrer']
                    referrer.save()
            
            # Add credits to referred user
            if credits_config['referred'] > 0:
                referred_result = self.add_credits(
                    user_id=referred_user_id,
                    amount=credits_config['referred'],
                    description=f"Welcome bonus - {referral_type}",
                    category='referral',
                    metadata={
                        'referral_type': referral_type,
                        'referrer_user_id': referrer_user_id
                    }
                )
                results['referred'] = referred_result
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"Error processing referral credits: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def estimate_task_cost(self, task_type: str, task_data: Dict) -> Dict[str, Any]:
        """Estimate credit cost for a task before execution"""
        try:
            # Extract parameters for cost calculation
            parameters = {}
            
            if task_type == 'image_generation':
                parameters['count'] = task_data.get('image_count', 1)
                parameters['resolution'] = task_data.get('resolution', 'standard')
            
            elif task_type == 'video_generation':
                parameters['duration'] = task_data.get('duration_seconds', 30)
                parameters['quality'] = task_data.get('quality', 'standard')
            
            elif task_type == 'social_media_post':
                parameters['platforms'] = len(task_data.get('platforms', []))
                parameters['has_media'] = bool(task_data.get('media_files'))
            
            elif task_type == 'content_analysis':
                parameters['content_length'] = len(task_data.get('content', ''))
                parameters['analysis_depth'] = task_data.get('analysis_depth', 'basic')
            
            cost = self.get_task_cost(task_type, **parameters)
            
            return {
                'success': True,
                'estimated_cost': cost,
                'task_type': task_type,
                'parameters': parameters
            }
            
        except Exception as e:
            logger.error(f"Error estimating task cost: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_user_credit_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive credit summary for a user"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get credit transactions
            transactions = CreditTransaction.get_user_transactions(user_id, limit=100)
            
            # Calculate statistics
            total_earned = CreditTransaction.get_total_credits_earned(user_id)
            total_used = CreditTransaction.get_total_credits_used(user_id)
            
            # Get usage by category
            categories = ['task_execution', 'subscription', 'referral', 'purchase', 'admin_adjustment']
            usage_by_category = {}
            
            for category in categories:
                earned = CreditTransaction.get_total_credits_earned(user_id, category)
                used = CreditTransaction.get_total_credits_used(user_id, category)
                usage_by_category[category] = {
                    'earned': earned,
                    'used': used,
                    'net': earned - used
                }
            
            # Get recent activity
            recent_transactions = transactions[:10]  # Last 10 transactions
            
            return {
                'success': True,
                'current_balance': user.credits_balance,
                'total_earned': total_earned,
                'total_used': total_used,
                'usage_by_category': usage_by_category,
                'recent_transactions': [tx.to_dict() for tx in recent_transactions],
                'referral_credits_earned': user.referral_credits_earned
            }
            
        except Exception as e:
            logger.error(f"Error getting credit summary for user {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_credit_packages(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get available credit packages for purchase"""
        packages = CreditPackage.get_active_packages()
        
        result = []
        for package in packages:
            package_data = package.to_dict()
            
            # Add user-specific information if user_id provided
            if user_id:
                user = User.get_by_id(user_id)
                if user and package.max_purchases_per_user:
                    # Count how many times user has purchased this package
                    purchases = CreditTransaction.query.filter_by(
                        user_id=user_id,
                        category='purchase'
                    ).filter(
                        CreditTransaction.description.contains(package.name)
                    ).count()
                    
                    package_data['user_purchases'] = purchases
                    package_data['can_purchase'] = purchases < package.max_purchases_per_user
                else:
                    package_data['can_purchase'] = True
            
            result.append(package_data)
        
        return result
    
    def process_credit_purchase(self, user_id: str, package_id: str, 
                               payment_transaction_id: str = None) -> Dict[str, Any]:
        """Process credit package purchase"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            package = CreditPackage.get_by_id(package_id)
            if not package or not package.is_active:
                return {'success': False, 'error': 'Package not found or inactive'}
            
            # Check purchase limits
            if package.max_purchases_per_user:
                purchases = CreditTransaction.query.filter_by(
                    user_id=user_id,
                    category='purchase'
                ).filter(
                    CreditTransaction.description.contains(package.name)
                ).count()
                
                if purchases >= package.max_purchases_per_user:
                    return {'success': False, 'error': 'Purchase limit exceeded for this package'}
            
            # Add credits (base + bonus)
            total_credits = package.total_credits()
            
            result = self.add_credits(
                user_id=user_id,
                amount=total_credits,
                description=f"Credit package purchase: {package.name}",
                category='purchase',
                metadata={
                    'package_id': package_id,
                    'package_name': package.name,
                    'base_credits': package.credits_amount,
                    'bonus_credits': package.bonus_credits,
                    'payment_transaction_id': payment_transaction_id
                }
            )
            
            if result['success']:
                # Update package usage
                package.increment_usage()
                package.save()
                
                logger.info(f"User {user_id} purchased credit package {package.name} - {total_credits} credits")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing credit purchase: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_low_credit_users(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Get users with low credit balance"""
        users = User.query.filter(
            User.credits_balance <= threshold,
            User.is_active == True
        ).all()
        
        return [
            {
                'user_id': user.id,
                'email': user.email,
                'credits_balance': user.credits_balance,
                'subscription_status': user.subscription_status,
                'last_activity': user.last_activity_at.isoformat() if user.last_activity_at else None
            }
            for user in users
        ]

# Global credit manager instance
credit_manager = CreditManager()

