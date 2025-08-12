import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time
import json
from src.models.credit_schedule import CreditSchedule, CreditScheduleExecution, CreditDistribution
from src.models.user import User
from src.services.credit_manager import credit_manager

logger = logging.getLogger(__name__)

class CreditScheduler:
    """Advanced Credit Scheduling System with Full Admin Control"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.check_interval = 60  # Check every minute
        
        # Predefined schedule templates
        self.schedule_templates = {
            'daily_welcome': {
                'name': 'Daily Welcome Credits',
                'name_ar': 'كريديت ترحيبي يومي',
                'description': 'Daily credits for new users',
                'description_ar': 'كريديت يومي للمستخدمين الجدد',
                'schedule_type': 'daily',
                'credit_amount': 5.0,
                'credit_type': 'welcome',
                'target_new_users_only': True,
                'max_days_since_registration': 7,
                'execution_time': '09:00:00'
            },
            'weekly_loyalty': {
                'name': 'Weekly Loyalty Bonus',
                'name_ar': 'مكافأة الولاء الأسبوعية',
                'description': 'Weekly bonus for active users',
                'description_ar': 'مكافأة أسبوعية للمستخدمين النشطين',
                'schedule_type': 'weekly',
                'credit_amount': 10.0,
                'credit_type': 'loyalty',
                'target_active_users_only': True,
                'max_days_since_last_activity': 7,
                'days_of_week': '[5]',  # Friday
                'execution_time': '18:00:00'
            },
            'monthly_premium': {
                'name': 'Monthly Premium Bonus',
                'name_ar': 'مكافأة شهرية مميزة',
                'description': 'Monthly bonus for all users',
                'description_ar': 'مكافأة شهرية لجميع المستخدمين',
                'schedule_type': 'monthly',
                'credit_amount': 25.0,
                'credit_type': 'bonus',
                'target_all_users': True,
                'day_of_month': 1,
                'execution_time': '12:00:00'
            },
            'weekend_boost': {
                'name': 'Weekend Activity Boost',
                'name_ar': 'تعزيز نشاط نهاية الأسبوع',
                'description': 'Weekend credits to boost activity',
                'description_ar': 'كريديت نهاية الأسبوع لتعزيز النشاط',
                'schedule_type': 'weekly',
                'credit_amount': 3.0,
                'credit_type': 'activity',
                'target_all_users': True,
                'days_of_week': '[6,7]',  # Saturday, Sunday
                'execution_time': '10:00:00'
            }
        }
    
    def start_scheduler(self):
        """Start the automatic credit scheduler"""
        if self.is_running:
            return {'success': False, 'error': 'Scheduler is already running'}
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Credit scheduler started")
        return {'success': True, 'message': 'Credit scheduler started successfully'}
    
    def stop_scheduler(self):
        """Stop the automatic credit scheduler"""
        if not self.is_running:
            return {'success': False, 'error': 'Scheduler is not running'}
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Credit scheduler stopped")
        return {'success': True, 'message': 'Credit scheduler stopped successfully'}
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                self.check_and_execute_schedules()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(self.check_interval)
    
    def check_and_execute_schedules(self):
        """Check and execute due schedules"""
        try:
            # Get all active schedules that are due
            due_schedules = CreditSchedule.query.filter(
                CreditSchedule.is_active == True,
                CreditSchedule.next_execution_at <= datetime.utcnow()
            ).all()
            
            for schedule in due_schedules:
                try:
                    result = schedule.execute_schedule()
                    if result['success']:
                        logger.info(f"Successfully executed schedule {schedule.id}: {result}")
                    else:
                        logger.warning(f"Failed to execute schedule {schedule.id}: {result}")
                except Exception as e:
                    logger.error(f"Error executing schedule {schedule.id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error checking schedules: {str(e)}")
    
    def create_schedule(self, schedule_data: Dict) -> Dict:
        """Create a new credit schedule with full admin control"""
        try:
            # Validate required fields
            required_fields = ['name', 'name_ar', 'schedule_type', 'start_date', 'credit_amount']
            for field in required_fields:
                if field not in schedule_data:
                    return {'success': False, 'error': f'Field {field} is required'}
            
            # Parse start_date
            if isinstance(schedule_data['start_date'], str):
                schedule_data['start_date'] = datetime.fromisoformat(schedule_data['start_date'])
            
            # Parse end_date if provided
            if 'end_date' in schedule_data and schedule_data['end_date']:
                if isinstance(schedule_data['end_date'], str):
                    schedule_data['end_date'] = datetime.fromisoformat(schedule_data['end_date'])
            
            # Create schedule
            schedule = CreditSchedule(**schedule_data)
            schedule.save()
            
            logger.info(f"Created credit schedule: {schedule.name} (ID: {schedule.id})")
            
            return {
                'success': True,
                'schedule': schedule.to_dict(),
                'message': 'Credit schedule created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating credit schedule: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_schedule(self, schedule_id: int, update_data: Dict) -> Dict:
        """Update an existing credit schedule"""
        try:
            schedule = CreditSchedule.query.get(schedule_id)
            if not schedule:
                return {'success': False, 'error': 'Schedule not found'}
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(schedule, key):
                    if key in ['start_date', 'end_date'] and isinstance(value, str):
                        value = datetime.fromisoformat(value)
                    setattr(schedule, key, value)
            
            # Recalculate next execution
            schedule.calculate_next_execution()
            schedule.save()
            
            logger.info(f"Updated credit schedule: {schedule.name} (ID: {schedule.id})")
            
            return {
                'success': True,
                'schedule': schedule.to_dict(),
                'message': 'Credit schedule updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating credit schedule: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_schedule(self, schedule_id: int) -> Dict:
        """Delete a credit schedule"""
        try:
            schedule = CreditSchedule.query.get(schedule_id)
            if not schedule:
                return {'success': False, 'error': 'Schedule not found'}
            
            schedule_name = schedule.name
            db.session.delete(schedule)
            db.session.commit()
            
            logger.info(f"Deleted credit schedule: {schedule_name} (ID: {schedule_id})")
            
            return {
                'success': True,
                'message': f'Credit schedule {schedule_name} deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting credit schedule: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def toggle_schedule(self, schedule_id: int, is_active: bool) -> Dict:
        """Enable or disable a credit schedule"""
        try:
            schedule = CreditSchedule.query.get(schedule_id)
            if not schedule:
                return {'success': False, 'error': 'Schedule not found'}
            
            schedule.is_active = is_active
            if is_active:
                schedule.calculate_next_execution()
            else:
                schedule.next_execution_at = None
            
            schedule.save()
            
            status = 'enabled' if is_active else 'disabled'
            logger.info(f"Schedule {schedule.name} (ID: {schedule_id}) {status}")
            
            return {
                'success': True,
                'schedule': schedule.to_dict(),
                'message': f'Schedule {status} successfully'
            }
            
        except Exception as e:
            logger.error(f"Error toggling schedule: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def execute_schedule_now(self, schedule_id: int) -> Dict:
        """Execute a schedule immediately (manual execution)"""
        try:
            schedule = CreditSchedule.query.get(schedule_id)
            if not schedule:
                return {'success': False, 'error': 'Schedule not found'}
            
            # Temporarily override next_execution_at to allow immediate execution
            original_next_execution = schedule.next_execution_at
            schedule.next_execution_at = datetime.utcnow()
            
            result = schedule.execute_schedule()
            
            # Restore original next execution time
            if not result['success']:
                schedule.next_execution_at = original_next_execution
                schedule.save()
            
            logger.info(f"Manual execution of schedule {schedule.name} (ID: {schedule_id}): {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing schedule manually: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_schedule_list(self, page: int = 1, per_page: int = 10, 
                         status: str = 'all') -> Dict:
        """Get list of credit schedules with pagination"""
        try:
            query = CreditSchedule.query
            
            if status == 'active':
                query = query.filter_by(is_active=True)
            elif status == 'inactive':
                query = query.filter_by(is_active=False)
            
            schedules = query.order_by(CreditSchedule.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'schedules': [schedule.to_dict() for schedule in schedules.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': schedules.total,
                    'pages': schedules.pages,
                    'has_next': schedules.has_next,
                    'has_prev': schedules.has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule list: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_schedule_details(self, schedule_id: int) -> Dict:
        """Get detailed information about a specific schedule"""
        try:
            schedule = CreditSchedule.query.get(schedule_id)
            if not schedule:
                return {'success': False, 'error': 'Schedule not found'}
            
            # Get recent executions
            recent_executions = CreditScheduleExecution.query.filter_by(
                schedule_id=schedule_id
            ).order_by(CreditScheduleExecution.execution_time.desc()).limit(10).all()
            
            # Get target user count
            target_users = schedule.get_target_users()
            
            return {
                'success': True,
                'schedule': schedule.to_dict(),
                'target_user_count': len(target_users),
                'recent_executions': [execution.to_dict() for execution in recent_executions],
                'scheduler_status': 'running' if self.is_running else 'stopped'
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule details: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_schedule_analytics(self, schedule_id: int, days: int = 30) -> Dict:
        """Get analytics for a specific schedule"""
        try:
            schedule = CreditSchedule.query.get(schedule_id)
            if not schedule:
                return {'success': False, 'error': 'Schedule not found'}
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get executions in the period
            executions = CreditScheduleExecution.query.filter(
                CreditScheduleExecution.schedule_id == schedule_id,
                CreditScheduleExecution.execution_time >= start_date
            ).all()
            
            # Calculate analytics
            total_executions = len(executions)
            total_credits_distributed = sum(e.total_credits_distributed for e in executions)
            total_users_credited = sum(e.successful_distributions for e in executions)
            
            # Success rate
            successful_executions = len([e for e in executions if e.status == 'completed'])
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Daily breakdown
            daily_stats = {}
            for execution in executions:
                date_key = execution.execution_time.strftime('%Y-%m-%d')
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'executions': 0,
                        'credits_distributed': 0,
                        'users_credited': 0
                    }
                daily_stats[date_key]['executions'] += 1
                daily_stats[date_key]['credits_distributed'] += execution.total_credits_distributed
                daily_stats[date_key]['users_credited'] += execution.successful_distributions
            
            return {
                'success': True,
                'schedule_id': schedule_id,
                'period': f'{days} days',
                'analytics': {
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'success_rate': round(success_rate, 2),
                    'total_credits_distributed': total_credits_distributed,
                    'total_users_credited': total_users_credited,
                    'average_credits_per_execution': round(total_credits_distributed / total_executions, 2) if total_executions > 0 else 0,
                    'average_users_per_execution': round(total_users_credited / total_executions, 2) if total_executions > 0 else 0,
                    'daily_stats': daily_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_from_template(self, template_name: str, custom_settings: Dict = None) -> Dict:
        """Create a schedule from a predefined template"""
        try:
            if template_name not in self.schedule_templates:
                return {'success': False, 'error': 'Template not found'}
            
            template = self.schedule_templates[template_name].copy()
            
            # Apply custom settings
            if custom_settings:
                template.update(custom_settings)
            
            # Set start date if not provided
            if 'start_date' not in template:
                template['start_date'] = datetime.utcnow()
            
            return self.create_schedule(template)
            
        except Exception as e:
            logger.error(f"Error creating schedule from template: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_templates(self) -> Dict:
        """Get available schedule templates"""
        return {
            'success': True,
            'templates': self.schedule_templates
        }
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status and statistics"""
        try:
            # Count active schedules
            active_schedules = CreditSchedule.query.filter_by(is_active=True).count()
            total_schedules = CreditSchedule.query.count()
            
            # Get next execution
            next_schedule = CreditSchedule.query.filter(
                CreditSchedule.is_active == True,
                CreditSchedule.next_execution_at.isnot(None)
            ).order_by(CreditSchedule.next_execution_at).first()
            
            # Get recent activity
            recent_executions = CreditScheduleExecution.query.order_by(
                CreditScheduleExecution.execution_time.desc()
            ).limit(5).all()
            
            return {
                'success': True,
                'scheduler_running': self.is_running,
                'check_interval_seconds': self.check_interval,
                'active_schedules': active_schedules,
                'total_schedules': total_schedules,
                'next_execution': {
                    'schedule_id': next_schedule.id if next_schedule else None,
                    'schedule_name': next_schedule.name if next_schedule else None,
                    'execution_time': next_schedule.next_execution_at.isoformat() if next_schedule else None
                },
                'recent_executions': [execution.to_dict() for execution in recent_executions]
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global credit scheduler instance
credit_scheduler = CreditScheduler()

