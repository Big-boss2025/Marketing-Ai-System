from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from src.services.credit_scheduler import credit_scheduler
from src.models.credit_schedule import CreditSchedule, CreditScheduleExecution

logger = logging.getLogger(__name__)

credit_schedule_bp = Blueprint('credit_schedule', __name__, url_prefix='/api/credit-schedule')

@credit_schedule_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the automatic credit scheduler"""
    try:
        result = credit_scheduler.start_scheduler()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the automatic credit scheduler"""
    try:
        result = credit_scheduler.stop_scheduler()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get scheduler status and statistics"""
    try:
        result = credit_scheduler.get_scheduler_status()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/create', methods=['POST'])
def create_schedule():
    """Create a new credit schedule"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Schedule data is required'
            }), 400
        
        result = credit_scheduler.create_schedule(data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/update/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an existing credit schedule"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Update data is required'
            }), 400
        
        result = credit_scheduler.update_schedule(schedule_id, data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/delete/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a credit schedule"""
    try:
        result = credit_scheduler.delete_schedule(schedule_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/toggle/<int:schedule_id>', methods=['POST'])
def toggle_schedule(schedule_id):
    """Enable or disable a credit schedule"""
    try:
        data = request.get_json() or {}
        is_active = data.get('is_active', True)
        
        result = credit_scheduler.toggle_schedule(schedule_id, is_active)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error toggling schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/execute/<int:schedule_id>', methods=['POST'])
def execute_schedule_now(schedule_id):
    """Execute a schedule immediately"""
    try:
        result = credit_scheduler.execute_schedule_now(schedule_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error executing schedule: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/list', methods=['GET'])
def get_schedule_list():
    """Get list of credit schedules"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'all')
        
        if status not in ['all', 'active', 'inactive']:
            return jsonify({
                'success': False,
                'error': 'Invalid status. Must be: all, active, or inactive'
            }), 400
        
        result = credit_scheduler.get_schedule_list(page, per_page, status)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting schedule list: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/details/<int:schedule_id>', methods=['GET'])
def get_schedule_details(schedule_id):
    """Get detailed information about a specific schedule"""
    try:
        result = credit_scheduler.get_schedule_details(schedule_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting schedule details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/analytics/<int:schedule_id>', methods=['GET'])
def get_schedule_analytics(schedule_id):
    """Get analytics for a specific schedule"""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days must be between 1 and 365'
            }), 400
        
        result = credit_scheduler.get_schedule_analytics(schedule_id, days)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting schedule analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/templates', methods=['GET'])
def get_templates():
    """Get available schedule templates"""
    try:
        result = credit_scheduler.get_templates()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/create-from-template', methods=['POST'])
def create_from_template():
    """Create a schedule from a template"""
    try:
        data = request.get_json()
        
        if not data or 'template_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Template name is required'
            }), 400
        
        template_name = data['template_name']
        custom_settings = data.get('custom_settings', {})
        
        result = credit_scheduler.create_from_template(template_name, custom_settings)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating from template: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/quick-setup', methods=['POST'])
def quick_setup():
    """Quick setup for common credit schedules"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Setup data is required'
            }), 400
        
        setup_type = data.get('setup_type')
        
        if setup_type == 'daily_welcome':
            # Daily welcome credits for new users
            schedule_data = {
                'name': 'Daily Welcome Credits',
                'name_ar': 'كريديت ترحيبي يومي',
                'description': 'Daily credits for new users (registered in last 7 days)',
                'description_ar': 'كريديت يومي للمستخدمين الجدد (المسجلين في آخر 7 أيام)',
                'schedule_type': 'daily',
                'start_date': datetime.utcnow(),
                'credit_amount': data.get('credit_amount', 5.0),
                'credit_type': 'welcome',
                'target_new_users_only': True,
                'max_days_since_registration': 7,
                'execution_time': data.get('execution_time', '09:00:00'),
                'max_users_per_execution': data.get('max_users_per_execution', 100)
            }
            
        elif setup_type == 'weekly_loyalty':
            # Weekly loyalty bonus for active users
            schedule_data = {
                'name': 'Weekly Loyalty Bonus',
                'name_ar': 'مكافأة الولاء الأسبوعية',
                'description': 'Weekly bonus for active users',
                'description_ar': 'مكافأة أسبوعية للمستخدمين النشطين',
                'schedule_type': 'weekly',
                'start_date': datetime.utcnow(),
                'credit_amount': data.get('credit_amount', 10.0),
                'credit_type': 'loyalty',
                'target_active_users_only': True,
                'max_days_since_last_activity': 7,
                'days_of_week': data.get('days_of_week', '[5]'),  # Friday
                'execution_time': data.get('execution_time', '18:00:00')
            }
            
        elif setup_type == 'monthly_bonus':
            # Monthly bonus for all users
            schedule_data = {
                'name': 'Monthly Bonus',
                'name_ar': 'مكافأة شهرية',
                'description': 'Monthly bonus for all users',
                'description_ar': 'مكافأة شهرية لجميع المستخدمين',
                'schedule_type': 'monthly',
                'start_date': datetime.utcnow(),
                'credit_amount': data.get('credit_amount', 25.0),
                'credit_type': 'bonus',
                'target_all_users': True,
                'day_of_month': data.get('day_of_month', 1),
                'execution_time': data.get('execution_time', '12:00:00')
            }
            
        elif setup_type == 'custom':
            # Custom schedule
            schedule_data = data.get('schedule_data', {})
            if 'start_date' not in schedule_data:
                schedule_data['start_date'] = datetime.utcnow()
                
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid setup_type. Must be: daily_welcome, weekly_loyalty, monthly_bonus, or custom'
            }), 400
        
        result = credit_scheduler.create_schedule(schedule_data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in quick setup: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@credit_schedule_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get credit schedule dashboard data"""
    try:
        # Get scheduler status
        scheduler_status = credit_scheduler.get_scheduler_status()
        
        # Get recent executions across all schedules
        recent_executions = CreditScheduleExecution.query.order_by(
            CreditScheduleExecution.execution_time.desc()
        ).limit(10).all()
        
        # Get top performing schedules
        top_schedules = CreditSchedule.query.order_by(
            CreditSchedule.total_credits_distributed.desc()
        ).limit(5).all()
        
        # Calculate total statistics
        total_credits_distributed = CreditSchedule.query.with_entities(
            db.func.sum(CreditSchedule.total_credits_distributed)
        ).scalar() or 0
        
        total_users_credited = CreditSchedule.query.with_entities(
            db.func.sum(CreditSchedule.total_users_credited)
        ).scalar() or 0
        
        dashboard_data = {
            'success': True,
            'scheduler_status': scheduler_status,
            'statistics': {
                'total_credits_distributed': float(total_credits_distributed),
                'total_users_credited': int(total_users_credited),
                'active_schedules': scheduler_status.get('active_schedules', 0),
                'total_schedules': scheduler_status.get('total_schedules', 0)
            },
            'recent_executions': [execution.to_dict() for execution in recent_executions],
            'top_schedules': [schedule.to_dict() for schedule in top_schedules],
            'quick_actions': [
                {
                    'action': 'create_daily_welcome',
                    'title': 'إنشاء كريديت ترحيبي يومي',
                    'description': 'كريديت يومي للمستخدمين الجدد'
                },
                {
                    'action': 'create_weekly_loyalty',
                    'title': 'إنشاء مكافأة ولاء أسبوعية',
                    'description': 'مكافأة أسبوعية للمستخدمين النشطين'
                },
                {
                    'action': 'create_monthly_bonus',
                    'title': 'إنشاء مكافأة شهرية',
                    'description': 'مكافأة شهرية لجميع المستخدمين'
                }
            ]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

