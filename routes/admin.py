from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.base import db
from src.models.user import User
from src.models.subscription import SubscriptionPlan, UserSubscription, PaymentTransaction
from src.models.credit_transaction import CreditTransaction, CreditPackage, TaskCreditCost
from src.models.api_config import APIConfig, APIUsageLog
from src.models.task import Task, Campaign
from src.models.content import Content, ContentTemplate
from src.models.feature_toggle import FeatureToggle, FeatureUsage
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin privileges"""
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.get_by_id(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        new_users_today = User.query.filter(
            User.created_at >= datetime.utcnow().date()
        ).count()
        
        # Subscription statistics
        active_subscriptions = UserSubscription.query.filter_by(status='active').count()
        total_revenue = PaymentTransaction.query.filter_by(status='completed')\
                                               .with_entities(db.func.sum(PaymentTransaction.amount))\
                                               .scalar() or 0
        
        # Task statistics
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status='completed').count()
        pending_tasks = Task.query.filter_by(status='pending').count()
        failed_tasks = Task.query.filter_by(status='failed').count()
        
        # Content statistics
        total_content = Content.query.count()
        published_content = Content.query.filter_by(status='published').count()
        
        # Credit statistics
        total_credits_used = CreditTransaction.query.filter(CreditTransaction.amount < 0)\
                                                   .with_entities(db.func.sum(CreditTransaction.amount))\
                                                   .scalar() or 0
        total_credits_used = abs(total_credits_used)
        
        # API usage statistics
        total_api_requests = APIUsageLog.query.count()
        api_errors = APIUsageLog.query.filter(APIUsageLog.status_code >= 400).count()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'new_today': new_users_today
            },
            'subscriptions': {
                'active': active_subscriptions,
                'total_revenue': total_revenue
            },
            'tasks': {
                'total': total_tasks,
                'completed': completed_tasks,
                'pending': pending_tasks,
                'failed': failed_tasks
            },
            'content': {
                'total': total_content,
                'published': published_content
            },
            'credits': {
                'total_used': total_credits_used
            },
            'api': {
                'total_requests': total_api_requests,
                'errors': api_errors,
                'success_rate': ((total_api_requests - api_errors) / total_api_requests * 100) if total_api_requests > 0 else 100
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.email.contains(search),
                    User.full_name.contains(search),
                    User.business_name.contains(search)
                )
            )
        
        users = query.order_by(User.created_at.desc())\
                    .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@admin_required
def get_user_details(user_id):
    """Get detailed user information"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's subscription
        subscription = UserSubscription.get_active_subscription(user_id)
        
        # Get user's recent tasks
        recent_tasks = Task.get_user_tasks(user_id, limit=10)
        
        # Get user's credit history
        credit_history = CreditTransaction.get_user_transactions(user_id, limit=10)
        
        # Get user's content
        recent_content = Content.get_user_content(user_id, limit=10)
        
        return jsonify({
            'user': user.to_dict(),
            'subscription': subscription.to_dict() if subscription else None,
            'recent_tasks': [task.to_dict() for task in recent_tasks],
            'credit_history': [tx.to_dict() for tx in credit_history],
            'recent_content': [content.to_dict() for content in recent_content]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>/credits', methods=['POST'])
@admin_required
def adjust_user_credits(user_id):
    """Adjust user's credit balance"""
    try:
        data = request.get_json()
        amount = data.get('amount', 0)
        description = data.get('description', 'Admin adjustment')
        
        current_user_id = get_jwt_identity()
        
        if amount == 0:
            return jsonify({'error': 'Amount cannot be zero'}), 400
        
        # Create credit transaction
        transaction = CreditTransaction.create_transaction(
            user_id=user_id,
            amount=amount,
            description=description,
            category='admin_adjustment',
            admin_user_id=current_user_id,
            admin_notes=data.get('notes', '')
        )
        
        return jsonify({
            'message': 'Credits adjusted successfully',
            'transaction': transaction.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api-configs', methods=['GET'])
@admin_required
def get_api_configs():
    """Get all API configurations"""
    try:
        configs = APIConfig.query.all()
        return jsonify({
            'api_configs': [config.to_dict() for config in configs]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api-configs', methods=['POST'])
@admin_required
def create_api_config():
    """Create new API configuration"""
    try:
        data = request.get_json()
        
        config = APIConfig(
            service_name=data['service_name'],
            service_display_name=data['service_display_name'],
            service_type=data['service_type'],
            api_endpoint=data.get('api_endpoint'),
            api_version=data.get('api_version'),
            is_active=data.get('is_active', True),
            rate_limit_per_minute=data.get('rate_limit_per_minute'),
            rate_limit_per_hour=data.get('rate_limit_per_hour'),
            rate_limit_per_day=data.get('rate_limit_per_day'),
            cost_per_request=data.get('cost_per_request', 0.0)
        )
        
        # Set encrypted credentials
        if data.get('api_key'):
            config.set_api_key(data['api_key'])
        if data.get('api_secret'):
            config.set_api_secret(data['api_secret'])
        if data.get('access_token'):
            config.set_access_token(data['access_token'])
        if data.get('refresh_token'):
            config.set_refresh_token(data['refresh_token'])
        
        # Set additional configuration
        if data.get('additional_config'):
            config.set_additional_config(data['additional_config'])
        
        config.save()
        
        return jsonify({
            'message': 'API configuration created successfully',
            'config': config.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api-configs/<config_id>', methods=['PUT'])
@admin_required
def update_api_config(config_id):
    """Update API configuration"""
    try:
        config = APIConfig.get_by_id(config_id)
        if not config:
            return jsonify({'error': 'API configuration not found'}), 404
        
        data = request.get_json()
        
        # Update basic fields
        for field in ['service_display_name', 'service_type', 'api_endpoint', 'api_version', 
                     'is_active', 'is_available', 'rate_limit_per_minute', 'rate_limit_per_hour', 
                     'rate_limit_per_day', 'cost_per_request']:
            if field in data:
                setattr(config, field, data[field])
        
        # Update encrypted credentials
        if data.get('api_key'):
            config.set_api_key(data['api_key'])
        if data.get('api_secret'):
            config.set_api_secret(data['api_secret'])
        if data.get('access_token'):
            config.set_access_token(data['access_token'])
        if data.get('refresh_token'):
            config.set_refresh_token(data['refresh_token'])
        
        # Update additional configuration
        if data.get('additional_config'):
            config.set_additional_config(data['additional_config'])
        
        config.save()
        
        return jsonify({
            'message': 'API configuration updated successfully',
            'config': config.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/feature-toggles', methods=['GET'])
@admin_required
def get_feature_toggles():
    """Get all feature toggles"""
    try:
        features = FeatureToggle.query.all()
        return jsonify({
            'features': [feature.to_dict() for feature in features]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/feature-toggles/<feature_id>', methods=['PUT'])
@admin_required
def update_feature_toggle(feature_id):
    """Update feature toggle"""
    try:
        feature = FeatureToggle.get_by_id(feature_id)
        if not feature:
            return jsonify({'error': 'Feature not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['is_enabled', 'is_beta', 'is_premium', 'rollout_percentage', 
                     'max_daily_usage', 'max_monthly_usage', 'min_subscription_level']:
            if field in data:
                setattr(feature, field, data[field])
        
        # Update configuration
        if data.get('configuration'):
            feature.set_configuration(data['configuration'])
        
        feature.save()
        
        return jsonify({
            'message': 'Feature toggle updated successfully',
            'feature': feature.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/subscription-plans', methods=['GET'])
@admin_required
def get_subscription_plans():
    """Get all subscription plans"""
    try:
        plans = SubscriptionPlan.query.order_by(SubscriptionPlan.sort_order).all()
        return jsonify({
            'plans': [plan.to_dict() for plan in plans]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/credit-packages', methods=['GET'])
@admin_required
def get_credit_packages():
    """Get all credit packages"""
    try:
        packages = CreditPackage.query.order_by(CreditPackage.sort_order).all()
        return jsonify({
            'packages': [package.to_dict() for package in packages]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/task-credit-costs', methods=['GET'])
@admin_required
def get_task_credit_costs():
    """Get all task credit costs"""
    try:
        costs = TaskCreditCost.get_all_active_costs()
        return jsonify({
            'costs': [cost.to_dict() for cost in costs]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/task-credit-costs/<cost_id>', methods=['PUT'])
@admin_required
def update_task_credit_cost(cost_id):
    """Update task credit cost"""
    try:
        cost = TaskCreditCost.get_by_id(cost_id)
        if not cost:
            return jsonify({'error': 'Task credit cost not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['base_cost', 'is_active']:
            if field in data:
                setattr(cost, field, data[field])
        
        # Update variable costs
        if data.get('variable_costs'):
            cost.set_variable_costs(data['variable_costs'])
        
        cost.save()
        
        return jsonify({
            'message': 'Task credit cost updated successfully',
            'cost': cost.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/usage', methods=['GET'])
@admin_required
def get_usage_analytics():
    """Get system usage analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get feature usage stats
        features = FeatureToggle.query.all()
        feature_stats = {}
        
        for feature in features:
            stats = FeatureUsage.get_feature_usage_stats(feature.feature_key, days)
            feature_stats[feature.feature_key] = {
                'name': feature.feature_name,
                'stats': stats
            }
        
        # Get API usage stats
        api_stats = {}
        api_configs = APIConfig.query.all()
        
        for config in api_configs:
            stats = APIUsageLog.get_usage_stats(config.service_name, days=days)
            api_stats[config.service_name] = {
                'display_name': config.service_display_name,
                'stats': stats
            }
        
        return jsonify({
            'feature_usage': feature_stats,
            'api_usage': api_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system/health', methods=['GET'])
@admin_required
def get_system_health():
    """Get system health status"""
    try:
        # Check database connection
        db_healthy = True
        try:
            db.session.execute('SELECT 1')
        except:
            db_healthy = False
        
        # Check API services
        api_services = APIConfig.get_active_services()
        service_health = {}
        
        for service in api_services:
            # Simple health check based on recent errors
            recent_errors = APIUsageLog.query.filter_by(service_name=service.service_name)\
                                            .filter(APIUsageLog.created_at >= datetime.utcnow() - timedelta(hours=1))\
                                            .filter(APIUsageLog.status_code >= 400)\
                                            .count()
            
            service_health[service.service_name] = {
                'healthy': recent_errors < 10,  # Less than 10 errors in the last hour
                'recent_errors': recent_errors,
                'last_request': service.last_request_at.isoformat() if service.last_request_at else None
            }
        
        # Overall system health
        overall_healthy = db_healthy and all(s['healthy'] for s in service_health.values())
        
        return jsonify({
            'overall_healthy': overall_healthy,
            'database_healthy': db_healthy,
            'services': service_health,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

