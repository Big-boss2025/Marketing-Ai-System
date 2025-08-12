from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from src.models.credit_transaction import TaskCreditCost
from src.models.user import User
from src.models.subscription import UserSubscription

logger = logging.getLogger(__name__)

class TaskPricingEngine:
    """Advanced task pricing engine with dynamic pricing"""
    
    def __init__(self):
        self.base_costs = {
            # Content Generation
            'text_generation': 1,
            'blog_post_generation': 3,
            'product_description': 2,
            'social_caption': 1,
            
            # Image Generation
            'image_generation': 5,
            'logo_design': 8,
            'banner_creation': 6,
            'product_image': 4,
            
            # Video Generation
            'video_generation': 15,
            'promotional_video': 20,
            'product_demo': 18,
            'social_video': 12,
            
            # Social Media
            'social_media_post': 2,
            'story_creation': 3,
            'carousel_post': 4,
            'social_campaign': 10,
            
            # Analysis & Research
            'content_analysis': 2,
            'competitor_analysis': 5,
            'trend_analysis': 3,
            'performance_analysis': 4,
            
            # Marketing Strategy
            'campaign_strategy': 8,
            'content_calendar': 6,
            'hashtag_research': 2,
            'audience_analysis': 4,
            
            # Automation
            'auto_posting': 1,
            'scheduled_campaign': 5,
            'bulk_content_creation': 10,
            'cross_platform_posting': 3
        }
        
        self.platform_multipliers = {
            'facebook': 1.0,
            'instagram': 1.0,
            'tiktok': 1.2,  # Higher cost due to video focus
            'youtube': 1.5,  # Higher cost due to complexity
            'twitter': 0.8,  # Lower cost due to simplicity
            'linkedin': 1.1,
            'pinterest': 0.9
        }
        
        self.quality_multipliers = {
            'basic': 0.8,
            'standard': 1.0,
            'premium': 1.5,
            'enterprise': 2.0
        }
        
        self.subscription_discounts = {
            'free': 0.0,
            'basic': 0.1,    # 10% discount
            'premium': 0.2,   # 20% discount
            'enterprise': 0.3 # 30% discount
        }
    
    def calculate_base_cost(self, task_type: str) -> int:
        """Get base cost for a task type"""
        return self.base_costs.get(task_type, 1)
    
    def calculate_platform_cost(self, platforms: List[str]) -> float:
        """Calculate cost multiplier based on platforms"""
        if not platforms:
            return 1.0
        
        total_multiplier = 0
        for platform in platforms:
            multiplier = self.platform_multipliers.get(platform.lower(), 1.0)
            total_multiplier += multiplier
        
        # Average multiplier for multiple platforms
        return total_multiplier / len(platforms)
    
    def calculate_content_complexity_cost(self, task_data: Dict) -> float:
        """Calculate cost based on content complexity"""
        complexity_multiplier = 1.0
        
        # Text length factor
        if 'text_content' in task_data:
            text_length = len(task_data['text_content'])
            if text_length > 1000:
                complexity_multiplier += 0.5
            elif text_length > 500:
                complexity_multiplier += 0.2
        
        # Media count factor
        if 'media_count' in task_data:
            media_count = task_data['media_count']
            if media_count > 5:
                complexity_multiplier += 0.8
            elif media_count > 2:
                complexity_multiplier += 0.3
        
        # Custom requirements
        if task_data.get('custom_requirements'):
            complexity_multiplier += 0.4
        
        # Urgency factor
        if task_data.get('priority') == 'urgent':
            complexity_multiplier += 0.5
        elif task_data.get('priority') == 'high':
            complexity_multiplier += 0.2
        
        return complexity_multiplier
    
    def calculate_ai_model_cost(self, task_type: str, model_config: Dict) -> float:
        """Calculate cost based on AI model usage"""
        model_costs = {
            'gpt-4': 2.0,
            'gpt-3.5-turbo': 1.0,
            'claude-3': 1.8,
            'gemini-pro': 1.2,
            'stable-diffusion': 1.0,
            'midjourney': 1.5,
            'dall-e-3': 2.0,
            'whisper': 0.5
        }
        
        model_name = model_config.get('model', 'default')
        base_multiplier = model_costs.get(model_name, 1.0)
        
        # Quality settings
        quality = model_config.get('quality', 'standard')
        quality_multiplier = self.quality_multipliers.get(quality, 1.0)
        
        return base_multiplier * quality_multiplier
    
    def calculate_subscription_discount(self, user_id: str) -> float:
        """Calculate discount based on user subscription"""
        user = User.get_by_id(user_id)
        if not user:
            return 0.0
        
        subscription = UserSubscription.get_active_subscription(user_id)
        if not subscription:
            subscription_level = user.subscription_status
        else:
            subscription_level = subscription.plan.name.lower()
        
        return self.subscription_discounts.get(subscription_level, 0.0)
    
    def calculate_bulk_discount(self, quantity: int) -> float:
        """Calculate discount for bulk operations"""
        if quantity >= 50:
            return 0.3  # 30% discount for 50+ items
        elif quantity >= 20:
            return 0.2  # 20% discount for 20+ items
        elif quantity >= 10:
            return 0.1  # 10% discount for 10+ items
        
        return 0.0
    
    def calculate_task_cost(self, task_type: str, task_data: Dict, 
                           user_id: str = None) -> Dict[str, Any]:
        """Calculate comprehensive cost for a task"""
        try:
            # Get base cost
            base_cost = self.calculate_base_cost(task_type)
            
            # Calculate various multipliers
            platform_multiplier = 1.0
            if 'platforms' in task_data:
                platform_multiplier = self.calculate_platform_cost(task_data['platforms'])
            
            complexity_multiplier = self.calculate_content_complexity_cost(task_data)
            
            ai_model_multiplier = 1.0
            if 'ai_config' in task_data:
                ai_model_multiplier = self.calculate_ai_model_cost(task_type, task_data['ai_config'])
            
            # Calculate raw cost
            raw_cost = base_cost * platform_multiplier * complexity_multiplier * ai_model_multiplier
            
            # Apply discounts
            subscription_discount = 0.0
            bulk_discount = 0.0
            
            if user_id:
                subscription_discount = self.calculate_subscription_discount(user_id)
            
            if 'quantity' in task_data:
                bulk_discount = self.calculate_bulk_discount(task_data['quantity'])
            
            # Calculate final cost
            total_discount = subscription_discount + bulk_discount
            final_cost = max(1, int(raw_cost * (1 - total_discount)))
            
            return {
                'success': True,
                'base_cost': base_cost,
                'raw_cost': int(raw_cost),
                'final_cost': final_cost,
                'breakdown': {
                    'platform_multiplier': platform_multiplier,
                    'complexity_multiplier': complexity_multiplier,
                    'ai_model_multiplier': ai_model_multiplier,
                    'subscription_discount': subscription_discount,
                    'bulk_discount': bulk_discount,
                    'total_discount': total_discount
                },
                'savings': int(raw_cost) - final_cost
            }
            
        except Exception as e:
            logger.error(f"Error calculating task cost: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'final_cost': self.calculate_base_cost(task_type)
            }
    
    def get_pricing_estimate(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Get pricing estimate for multiple tasks"""
        total_cost = 0
        task_estimates = []
        
        for task in tasks:
            task_type = task.get('type')
            task_data = task.get('data', {})
            user_id = task.get('user_id')
            
            estimate = self.calculate_task_cost(task_type, task_data, user_id)
            task_estimates.append({
                'task_type': task_type,
                'estimate': estimate
            })
            
            if estimate['success']:
                total_cost += estimate['final_cost']
        
        return {
            'total_estimated_cost': total_cost,
            'task_estimates': task_estimates,
            'currency': 'credits'
        }
    
    def create_pricing_plan(self, plan_name: str, tasks: List[str], 
                           discount: float = 0.0) -> Dict[str, Any]:
        """Create a custom pricing plan for specific tasks"""
        plan_costs = {}
        total_base_cost = 0
        
        for task_type in tasks:
            base_cost = self.calculate_base_cost(task_type)
            discounted_cost = max(1, int(base_cost * (1 - discount)))
            
            plan_costs[task_type] = {
                'base_cost': base_cost,
                'plan_cost': discounted_cost,
                'savings': base_cost - discounted_cost
            }
            
            total_base_cost += base_cost
        
        total_plan_cost = sum(cost['plan_cost'] for cost in plan_costs.values())
        
        return {
            'plan_name': plan_name,
            'tasks': plan_costs,
            'total_base_cost': total_base_cost,
            'total_plan_cost': total_plan_cost,
            'total_savings': total_base_cost - total_plan_cost,
            'discount_percentage': discount * 100
        }
    
    def get_recommended_packages(self, user_usage_history: List[Dict]) -> List[Dict]:
        """Recommend credit packages based on user usage history"""
        if not user_usage_history:
            return self._get_default_packages()
        
        # Analyze usage patterns
        monthly_usage = self._analyze_monthly_usage(user_usage_history)
        common_tasks = self._get_common_tasks(user_usage_history)
        
        recommendations = []
        
        # Basic package for light users
        if monthly_usage <= 50:
            recommendations.append({
                'package_name': 'Starter Pack',
                'credits': 100,
                'bonus_credits': 20,
                'price': 9.99,
                'suitable_for': 'Light usage, occasional content creation',
                'estimated_duration': '2-3 months'
            })
        
        # Standard package for regular users
        elif monthly_usage <= 200:
            recommendations.append({
                'package_name': 'Professional Pack',
                'credits': 500,
                'bonus_credits': 100,
                'price': 39.99,
                'suitable_for': 'Regular content creation and social media management',
                'estimated_duration': '2-3 months'
            })
        
        # Premium package for heavy users
        else:
            recommendations.append({
                'package_name': 'Enterprise Pack',
                'credits': 1500,
                'bonus_credits': 500,
                'price': 99.99,
                'suitable_for': 'Heavy usage, multiple campaigns, team collaboration',
                'estimated_duration': '2-3 months'
            })
        
        return recommendations
    
    def _analyze_monthly_usage(self, usage_history: List[Dict]) -> int:
        """Analyze average monthly credit usage"""
        if not usage_history:
            return 0
        
        total_credits = sum(record.get('credits_used', 0) for record in usage_history)
        months = len(set(record.get('month') for record in usage_history))
        
        return int(total_credits / max(1, months))
    
    def _get_common_tasks(self, usage_history: List[Dict]) -> List[str]:
        """Get most common task types from usage history"""
        task_counts = {}
        
        for record in usage_history:
            task_type = record.get('task_type')
            if task_type:
                task_counts[task_type] = task_counts.get(task_type, 0) + 1
        
        # Sort by frequency and return top 5
        sorted_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)
        return [task[0] for task in sorted_tasks[:5]]
    
    def _get_default_packages(self) -> List[Dict]:
        """Get default package recommendations for new users"""
        return [
            {
                'package_name': 'Trial Pack',
                'credits': 50,
                'bonus_credits': 10,
                'price': 4.99,
                'suitable_for': 'First-time users, testing the platform',
                'estimated_duration': '1 month'
            },
            {
                'package_name': 'Starter Pack',
                'credits': 200,
                'bonus_credits': 50,
                'price': 19.99,
                'suitable_for': 'Small businesses, personal brands',
                'estimated_duration': '2 months'
            },
            {
                'package_name': 'Growth Pack',
                'credits': 800,
                'bonus_credits': 200,
                'price': 69.99,
                'suitable_for': 'Growing businesses, marketing agencies',
                'estimated_duration': '3 months'
            }
        ]

# Global pricing engine instance
pricing_engine = TaskPricingEngine()

