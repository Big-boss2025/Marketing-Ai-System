"""
API Management Routes
مسارات إدارة الواجهات البرمجية

This module provides routes for managing API keys, monitoring usage,
and controlling external service integrations.
"""

from flask import Blueprint, request, jsonify, render_template, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.models.user import User
from src.models.api_keys import api_key_manager, APIKey, APIUsageLog
from src.services.external_api_integration import external_api
from src.services.cache_manager import cache_manager
from src.services.queue_manager import queue_manager
from src.services.rate_limiter import rate_limit_manager, rate_limit
from src.models.base import db

logger = logging.getLogger(__name__)

api_management_bp = Blueprint('api_management', __name__, url_prefix='/api/management')


def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({
                'error': 'Admin privileges required',
                'message': 'You need admin privileges to access this resource'
            }), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


@api_management_bp.route('/dashboard')
@jwt_required()
@admin_required
def dashboard():
    """Render admin dashboard"""
    return render_template('admin/api_dashboard.html')


@api_management_bp.route('/api-keys', methods=['GET'])
@jwt_required()
@admin_required
@rate_limit('per_user')
def list_api_keys():
    """List all API keys"""
    try:
        api_keys = api_key_manager.list_api_keys()
        
        return jsonify({
            'success': True,
            'api_keys': api_keys,
            'total': len(api_keys)
        })
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve API keys'
        }), 500


@api_management_bp.route('/api-keys', methods=['POST'])
@jwt_required()
@admin_required
@rate_limit('expensive')
def add_api_key():
    """Add or update API key"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        required_fields = ['service_name', 'api_key']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        result = api_key_manager.add_api_key(
            service_name=data['service_name'],
            api_key=data['api_key'],
            api_secret=data.get('api_secret'),
            endpoint_url=data.get('endpoint_url'),
            rate_limit_per_minute=data.get('rate_limit_per_minute', 60),
            rate_limit_per_day=data.get('rate_limit_per_day', 1000),
            monthly_quota=data.get('monthly_quota'),
            extra_config=data.get('extra_config')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to add API key: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to add API key'
        }), 500


@api_management_bp.route('/api-keys/<service_name>', methods=['PUT'])
@jwt_required()
@admin_required
@rate_limit('expensive')
def update_api_key(service_name):
    """Update API key"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get existing key
        existing_key = api_key_manager.get_api_key(service_name)
        if not existing_key:
            return jsonify({
                'success': False,
                'error': 'API key not found'
            }), 404
        
        # Update with new data
        result = api_key_manager.add_api_key(
            service_name=service_name,
            api_key=data.get('api_key', existing_key['api_key']),
            api_secret=data.get('api_secret', existing_key['api_secret']),
            endpoint_url=data.get('endpoint_url', existing_key['endpoint_url']),
            rate_limit_per_minute=data.get('rate_limit_per_minute', existing_key['rate_limit_per_minute']),
            rate_limit_per_day=data.get('rate_limit_per_day', existing_key['rate_limit_per_day']),
            monthly_quota=data.get('monthly_quota', existing_key['monthly_quota']),
            extra_config=data.get('extra_config', existing_key['extra_config'])
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to update API key: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update API key'
        }), 500


@api_management_bp.route('/api-keys/<service_name>', methods=['DELETE'])
@jwt_required()
@admin_required
@rate_limit('expensive')
def delete_api_key(service_name):
    """Delete API key"""
    try:
        result = api_key_manager.delete_api_key(service_name)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete API key'
        }), 500


@api_management_bp.route('/api-keys/<service_name>/toggle', methods=['POST'])
@jwt_required()
@admin_required
@rate_limit('per_user')
def toggle_api_key(service_name):
    """Enable or disable API key"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', True)
        
        result = api_key_manager.toggle_api_key(service_name, is_active)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to toggle API key: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to toggle API key'
        }), 500


@api_management_bp.route('/usage-stats')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_usage_stats():
    """Get API usage statistics"""
    try:
        service_name = request.args.get('service_name')
        days = int(request.args.get('days', 30))
        
        result = api_key_manager.get_usage_stats(service_name, days)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage statistics'
        }), 500


@api_management_bp.route('/usage-logs')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_usage_logs():
    """Get API usage logs"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        service_name = request.args.get('service_name')
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        query = APIUsageLog.query
        
        # Apply filters
        if service_name:
            api_key = APIKey.query.filter_by(service_name=service_name).first()
            if api_key:
                query = query.filter(APIUsageLog.api_key_id == api_key.id)
        
        if user_id:
            query = query.filter(APIUsageLog.user_id == user_id)
        
        if status:
            query = query.filter(APIUsageLog.response_status == status)
        
        # Order by creation time (newest first)
        query = query.order_by(APIUsageLog.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = [log.to_dict() for log in pagination.items]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get usage logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage logs'
        }), 500


@api_management_bp.route('/service-status')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_service_status():
    """Get status of all external services"""
    try:
        status = external_api.get_service_status()
        
        return jsonify({
            'success': True,
            'services': status
        })
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve service status'
        }), 500


@api_management_bp.route('/cache-stats')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = cache_manager.get_stats()
        
        return jsonify({
            'success': True,
            'cache_stats': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve cache statistics'
        }), 500


@api_management_bp.route('/cache/clear', methods=['POST'])
@jwt_required()
@admin_required
@rate_limit('expensive')
def clear_cache():
    """Clear cache"""
    try:
        cache_type = request.json.get('type', 'expired') if request.json else 'expired'
        
        if cache_type == 'all':
            success = cache_manager.clear_all()
            message = 'All cache cleared' if success else 'Failed to clear cache'
        else:
            cleared_count = cache_manager.clear_expired()
            success = True
            message = f'Cleared {cleared_count} expired cache entries'
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache'
        }), 500


@api_management_bp.route('/queue-stats')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_queue_stats():
    """Get queue statistics"""
    try:
        stats = queue_manager.get_stats()
        
        return jsonify({
            'success': True,
            'queue_stats': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve queue statistics'
        }), 500


@api_management_bp.route('/rate-limits')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_rate_limits():
    """Get rate limit information"""
    try:
        user_id = request.args.get('user_id')
        if user_id:
            user_id = int(user_id)
        
        rate_limits = rate_limit_manager.get_all_rate_limit_info(user_id)
        
        return jsonify({
            'success': True,
            'rate_limits': rate_limits
        })
        
    except Exception as e:
        logger.error(f"Failed to get rate limits: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve rate limit information'
        }), 500


@api_management_bp.route('/rate-limits/reset', methods=['POST'])
@jwt_required()
@admin_required
@rate_limit('expensive')
def reset_rate_limits():
    """Reset rate limits for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 400
        
        # Reset various rate limits for the user
        identifier = f"user:{user_id}"
        success = True
        
        # Reset different types of rate limits
        for limit_type in ['', ':generation', ':expensive']:
            full_identifier = f"{identifier}{limit_type}"
            if not rate_limit_manager.rate_limiter.reset_rate_limit(full_identifier):
                success = False
        
        return jsonify({
            'success': success,
            'message': f'Rate limits reset for user {user_id}' if success else 'Failed to reset some rate limits'
        })
        
    except Exception as e:
        logger.error(f"Failed to reset rate limits: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset rate limits'
        }), 500


@api_management_bp.route('/system-health')
@jwt_required()
@admin_required
@rate_limit('per_user')
def get_system_health():
    """Get overall system health status"""
    try:
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        # Check database
        try:
            db.session.execute('SELECT 1')
            health_status['components']['database'] = {
                'status': 'healthy',
                'message': 'Database connection OK'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Check cache
        try:
            cache_stats = cache_manager.get_stats()
            if 'error' in cache_stats:
                health_status['components']['cache'] = {
                    'status': 'unhealthy',
                    'message': cache_stats['error']
                }
                health_status['status'] = 'degraded'
            else:
                health_status['components']['cache'] = {
                    'status': 'healthy',
                    'message': f"Cache type: {cache_stats.get('cache_type', 'unknown')}"
                }
        except Exception as e:
            health_status['components']['cache'] = {
                'status': 'unhealthy',
                'message': f'Cache error: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Check queue
        try:
            queue_stats = queue_manager.get_stats()
            if 'error' in queue_stats:
                health_status['components']['queue'] = {
                    'status': 'unhealthy',
                    'message': queue_stats['error']
                }
                health_status['status'] = 'degraded'
            else:
                health_status['components']['queue'] = {
                    'status': 'healthy',
                    'message': f"Queue type: {queue_stats.get('queue_type', 'unknown')}"
                }
        except Exception as e:
            health_status['components']['queue'] = {
                'status': 'unhealthy',
                'message': f'Queue error: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Check external services
        try:
            service_status = external_api.get_service_status()
            configured_services = sum(1 for s in service_status.values() if s['configured'])
            active_services = sum(1 for s in service_status.values() if s['active'])
            
            health_status['components']['external_apis'] = {
                'status': 'healthy' if active_services > 0 else 'warning',
                'message': f'{active_services}/{configured_services} services active'
            }
            
            if active_services == 0:
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['components']['external_apis'] = {
                'status': 'unhealthy',
                'message': f'External API check failed: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system health'
        }), 500


@api_management_bp.route('/test-api/<service_name>', methods=['POST'])
@jwt_required()
@admin_required
@rate_limit('expensive')
def test_api_service(service_name):
    """Test API service connection"""
    try:
        data = request.get_json() or {}
        test_type = data.get('type', 'image')  # image, video, speech
        
        if test_type == 'image':
            result = external_api.generate_image(
                prompt="Test image generation",
                user_id=g.current_user.id,
                width=512,
                height=512,
                service=service_name
            )
        elif test_type == 'video':
            result = external_api.generate_video(
                prompt="Test video generation",
                user_id=g.current_user.id,
                duration=3,
                service=service_name
            )
        elif test_type == 'speech':
            result = external_api.generate_speech(
                text="Test speech generation",
                user_id=g.current_user.id,
                service=service_name
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid test type'
            }), 400
        
        return jsonify({
            'success': True,
            'test_result': result
        })
        
    except Exception as e:
        logger.error(f"Failed to test API service: {e}")
        return jsonify({
            'success': False,
            'error': f'API test failed: {str(e)}'
        }), 500


@api_management_bp.route('/export-logs')
@jwt_required()
@admin_required
@rate_limit('expensive')
def export_logs():
    """Export usage logs as CSV"""
    try:
        import csv
        import io
        from flask import make_response
        
        service_name = request.args.get('service_name')
        days = int(request.args.get('days', 30))
        
        # Get logs
        query = APIUsageLog.query
        
        if service_name:
            api_key = APIKey.query.filter_by(service_name=service_name).first()
            if api_key:
                query = query.filter(APIUsageLog.api_key_id == api_key.id)
        
        # Filter by date
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(APIUsageLog.created_at >= start_date)
        
        logs = query.order_by(APIUsageLog.created_at.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Service', 'User ID', 'Request Type', 'Status',
            'Response Time (ms)', 'Tokens Used', 'Cost Credits',
            'Error Message', 'IP Address', 'Created At'
        ])
        
        # Write data
        for log in logs:
            api_key = APIKey.query.get(log.api_key_id)
            service_name = api_key.service_name if api_key else 'Unknown'
            
            writer.writerow([
                log.id,
                service_name,
                log.user_id or '',
                log.request_type,
                log.response_status,
                log.response_time_ms or '',
                log.tokens_used,
                log.cost_credits,
                log.error_message or '',
                log.ip_address or '',
                log.created_at.isoformat()
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=api_usage_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to export logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to export logs'
        }), 500

