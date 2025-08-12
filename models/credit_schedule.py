from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from src.models.base import db
import json

class CreditSchedule(db.Model):
    """Scheduled credit distribution system"""
    __tablename__ = 'credit_schedules'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    description = Column(Text)
    description_ar = Column(Text)
    
    # Schedule settings
    is_active = Column(Boolean, default=True)
    schedule_type = Column(String(20), nullable=False)  # daily, weekly, monthly, once, event_based
    
    # Timing settings
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # None for ongoing schedules
    execution_time = Column(String(8), default='09:00:00')  # HH:MM:SS format
    
    # Weekly settings (for weekly schedules)
    days_of_week = Column(String(20))  # JSON array of days: [1,2,3,4,5] (Monday=1)
    
    # Monthly settings (for monthly schedules)
    day_of_month = Column(Integer, default=1)  # Day of month (1-31)
    
    # Credit settings
    credit_amount = Column(Float, nullable=False)
    credit_type = Column(String(20), default='bonus')  # bonus, welcome, loyalty, event, activity
    
    # Target audience settings
    target_all_users = Column(Boolean, default=True)
    target_new_users_only = Column(Boolean, default=False)  # Users registered in last N days
    target_active_users_only = Column(Boolean, default=False)  # Users active in last N days
    target_subscription_types = Column(Text)  # JSON array of subscription types
    target_user_tiers = Column(Text)  # JSON array of user tiers
    min_days_since_registration = Column(Integer, default=0)
    max_days_since_registration = Column(Integer, nullable=True)
    min_days_since_last_activity = Column(Integer, default=0)
    max_days_since_last_activity = Column(Integer, nullable=True)
    
    # Limits
    max_credits_per_user = Column(Float, nullable=True)  # Max credits per user for this schedule
    max_total_credits = Column(Float, nullable=True)  # Max total credits to distribute
    max_users_per_execution = Column(Integer, nullable=True)  # Max users to give credits to per execution
    
    # Execution tracking
    total_executions = Column(Integer, default=0)
    total_credits_distributed = Column(Float, default=0.0)
    total_users_credited = Column(Integer, default=0)
    last_execution_at = Column(DateTime, nullable=True)
    next_execution_at = Column(DateTime, nullable=True)
    
    # Conditions (JSON)
    conditions = Column(Text)  # JSON object with custom conditions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("CreditScheduleExecution", back_populates="schedule")
    
    def __init__(self, name, name_ar, schedule_type, start_date, credit_amount, **kwargs):
        self.name = name
        self.name_ar = name_ar
        self.schedule_type = schedule_type
        self.start_date = start_date
        self.credit_amount = credit_amount
        
        # Set optional parameters
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Calculate next execution
        self.calculate_next_execution()
    
    def calculate_next_execution(self):
        """Calculate the next execution time"""
        if not self.is_active or (self.end_date and datetime.utcnow() > self.end_date):
            self.next_execution_at = None
            return
        
        now = datetime.utcnow()
        
        if self.schedule_type == 'once':
            if self.last_execution_at is None and self.start_date > now:
                self.next_execution_at = self.start_date
            else:
                self.next_execution_at = None
                
        elif self.schedule_type == 'daily':
            # Calculate next daily execution
            base_date = max(now, self.start_date)
            execution_time = datetime.strptime(self.execution_time, '%H:%M:%S').time()
            next_execution = datetime.combine(base_date.date(), execution_time)
            
            if next_execution <= now:
                next_execution += timedelta(days=1)
            
            self.next_execution_at = next_execution
            
        elif self.schedule_type == 'weekly':
            # Calculate next weekly execution
            days_of_week = json.loads(self.days_of_week) if self.days_of_week else [1]  # Default to Monday
            execution_time = datetime.strptime(self.execution_time, '%H:%M:%S').time()
            
            # Find next execution day
            current_weekday = now.weekday() + 1  # Convert to 1-7 format
            next_execution = None
            
            for day in sorted(days_of_week):
                days_ahead = (day - current_weekday) % 7
                if days_ahead == 0:
                    # Today - check if time has passed
                    today_execution = datetime.combine(now.date(), execution_time)
                    if today_execution > now:
                        next_execution = today_execution
                        break
                else:
                    candidate_date = now + timedelta(days=days_ahead)
                    next_execution = datetime.combine(candidate_date.date(), execution_time)
                    break
            
            if next_execution is None:
                # Next week
                days_ahead = (days_of_week[0] - current_weekday + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                candidate_date = now + timedelta(days=days_ahead)
                next_execution = datetime.combine(candidate_date.date(), execution_time)
            
            self.next_execution_at = next_execution
            
        elif self.schedule_type == 'monthly':
            # Calculate next monthly execution
            execution_time = datetime.strptime(self.execution_time, '%H:%M:%S').time()
            
            # Try current month first
            try:
                current_month_execution = datetime.combine(
                    now.replace(day=self.day_of_month).date(),
                    execution_time
                )
                if current_month_execution > now:
                    self.next_execution_at = current_month_execution
                    return
            except ValueError:
                pass  # Invalid day for current month
            
            # Try next month
            next_month = now.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            try:
                next_month_execution = datetime.combine(
                    next_month.replace(day=self.day_of_month).date(),
                    execution_time
                )
                self.next_execution_at = next_month_execution
            except ValueError:
                # Invalid day for next month, use last day of month
                next_month_last_day = (next_month.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                self.next_execution_at = datetime.combine(next_month_last_day.date(), execution_time)
    
    def should_execute_now(self):
        """Check if schedule should execute now"""
        if not self.is_active:
            return False
        
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        
        if self.next_execution_at is None:
            return False
        
        return datetime.utcnow() >= self.next_execution_at
    
    def get_target_users(self):
        """Get list of users that match the target criteria"""
        from src.models.user import User
        from src.models.subscription import Subscription
        
        query = User.query
        
        # Target specific user groups
        if not self.target_all_users:
            conditions = []
            
            if self.target_new_users_only:
                cutoff_date = datetime.utcnow() - timedelta(days=self.max_days_since_registration or 7)
                conditions.append(User.created_at >= cutoff_date)
            
            if self.target_active_users_only:
                cutoff_date = datetime.utcnow() - timedelta(days=self.max_days_since_last_activity or 30)
                conditions.append(User.last_activity_at >= cutoff_date)
            
            if self.min_days_since_registration > 0:
                cutoff_date = datetime.utcnow() - timedelta(days=self.min_days_since_registration)
                conditions.append(User.created_at <= cutoff_date)
            
            if self.max_days_since_registration:
                cutoff_date = datetime.utcnow() - timedelta(days=self.max_days_since_registration)
                conditions.append(User.created_at >= cutoff_date)
            
            # Apply conditions
            for condition in conditions:
                query = query.filter(condition)
        
        # Apply user limits
        if self.max_users_per_execution:
            query = query.limit(self.max_users_per_execution)
        
        return query.all()
    
    def execute_schedule(self):
        """Execute the credit distribution"""
        if not self.should_execute_now():
            return {'success': False, 'error': 'Schedule not ready for execution'}
        
        # Check total credit limits
        if self.max_total_credits and self.total_credits_distributed >= self.max_total_credits:
            return {'success': False, 'error': 'Maximum total credits reached'}
        
        # Get target users
        target_users = self.get_target_users()
        
        if not target_users:
            return {'success': False, 'error': 'No target users found'}
        
        # Execute credit distribution
        from src.services.credit_manager import credit_manager
        
        execution = CreditScheduleExecution(
            schedule_id=self.id,
            execution_time=datetime.utcnow(),
            target_user_count=len(target_users)
        )
        
        successful_credits = 0
        total_credits_given = 0.0
        
        for user in target_users:
            # Check per-user credit limit
            if self.max_credits_per_user:
                user_total_credits = CreditScheduleExecution.query.join(
                    CreditScheduleExecution.distributions
                ).filter(
                    CreditScheduleExecution.schedule_id == self.id,
                    CreditDistribution.user_id == user.id
                ).with_entities(
                    db.func.sum(CreditDistribution.credit_amount)
                ).scalar() or 0
                
                if user_total_credits >= self.max_credits_per_user:
                    continue
            
            # Give credits
            credit_result = credit_manager.add_credits(
                user.id,
                self.credit_amount,
                f'scheduled_{self.credit_type}',
                f'Scheduled credit: {self.name}'
            )
            
            if credit_result['success']:
                # Record distribution
                distribution = CreditDistribution(
                    execution_id=execution.id,
                    user_id=user.id,
                    credit_amount=self.credit_amount,
                    status='completed'
                )
                distribution.save()
                
                successful_credits += 1
                total_credits_given += self.credit_amount
        
        # Update execution record
        execution.successful_distributions = successful_credits
        execution.total_credits_distributed = total_credits_given
        execution.status = 'completed'
        execution.save()
        
        # Update schedule statistics
        self.total_executions += 1
        self.total_credits_distributed += total_credits_given
        self.total_users_credited += successful_credits
        self.last_execution_at = datetime.utcnow()
        
        # Calculate next execution
        self.calculate_next_execution()
        self.save()
        
        return {
            'success': True,
            'execution_id': execution.id,
            'users_credited': successful_credits,
            'total_credits_distributed': total_credits_given,
            'next_execution': self.next_execution_at.isoformat() if self.next_execution_at else None
        }
    
    def save(self):
        """Save schedule to database"""
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
            'schedule_type': self.schedule_type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'execution_time': self.execution_time,
            'days_of_week': json.loads(self.days_of_week) if self.days_of_week else None,
            'day_of_month': self.day_of_month,
            'credit_amount': self.credit_amount,
            'credit_type': self.credit_type,
            'target_all_users': self.target_all_users,
            'target_new_users_only': self.target_new_users_only,
            'target_active_users_only': self.target_active_users_only,
            'max_credits_per_user': self.max_credits_per_user,
            'max_total_credits': self.max_total_credits,
            'max_users_per_execution': self.max_users_per_execution,
            'total_executions': self.total_executions,
            'total_credits_distributed': self.total_credits_distributed,
            'total_users_credited': self.total_users_credited,
            'last_execution_at': self.last_execution_at.isoformat() if self.last_execution_at else None,
            'next_execution_at': self.next_execution_at.isoformat() if self.next_execution_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CreditScheduleExecution(db.Model):
    """Record of credit schedule executions"""
    __tablename__ = 'credit_schedule_executions'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('credit_schedules.id'), nullable=False)
    execution_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='pending')  # pending, completed, failed
    
    # Execution results
    target_user_count = Column(Integer, default=0)
    successful_distributions = Column(Integer, default=0)
    failed_distributions = Column(Integer, default=0)
    total_credits_distributed = Column(Float, default=0.0)
    
    # Error tracking
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    schedule = relationship("CreditSchedule", back_populates="executions")
    distributions = relationship("CreditDistribution", back_populates="execution")
    
    def save(self):
        """Save execution to database"""
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'execution_time': self.execution_time.isoformat(),
            'status': self.status,
            'target_user_count': self.target_user_count,
            'successful_distributions': self.successful_distributions,
            'failed_distributions': self.failed_distributions,
            'total_credits_distributed': self.total_credits_distributed,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }

class CreditDistribution(db.Model):
    """Individual credit distributions to users"""
    __tablename__ = 'credit_distributions'
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('credit_schedule_executions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    credit_amount = Column(Float, nullable=False)
    status = Column(String(20), default='pending')  # pending, completed, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    execution = relationship("CreditScheduleExecution", back_populates="distributions")
    user = relationship("User")
    
    def save(self):
        """Save distribution to database"""
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'user_id': self.user_id,
            'credit_amount': self.credit_amount,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }

