from src.models.base import db, BaseModel
from datetime import datetime
import json

class CreditTransaction(BaseModel):
    """Credit transaction records for tracking credit usage and additions"""
    __tablename__ = 'credit_transactions'
    
    # User
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Transaction Details
    transaction_type = db.Column(db.String(20), nullable=False)  # debit, credit, bonus, refund, purchase
    amount = db.Column(db.Integer, nullable=False)  # Positive for credit, negative for debit
    balance_before = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    
    # Description & Category
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # task_execution, subscription, referral, purchase, admin_adjustment
    
    # Related Records
    related_task_id = db.Column(db.String(36), nullable=True)  # If related to a task
    related_subscription_id = db.Column(db.String(36), nullable=True)  # If related to subscription
    related_referral_id = db.Column(db.String(36), nullable=True)  # If related to referral
    
    # Additional Data
    transaction_metadata = db.Column(db.Text, nullable=True)  # JSON for additional information
    
    # Admin Info (for manual adjustments)
    admin_user_id = db.Column(db.String(36), nullable=True)  # Admin who made the adjustment
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='credit_transactions')
    
    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.transaction_metadata:
            try:
                return json.loads(self.transaction_metadata)
            except:
                return {}
        return {}
    
    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.transaction_metadata = json.dumps(metadata_dict)
    
    def is_debit(self):
        """Check if transaction is a debit (credit usage)"""
        return self.amount < 0
    
    def is_credit(self):
        """Check if transaction is a credit (credit addition)"""
        return self.amount > 0
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['metadata'] = self.get_metadata()
        data['is_debit'] = self.is_debit()
        data['is_credit'] = self.is_credit()
        data['absolute_amount'] = abs(self.amount)
        return data
    
    @classmethod
    def create_transaction(cls, user_id, amount, description, category, **kwargs):
        """Create a new credit transaction"""
        from src.models.user import User
        
        user = User.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Record balance before transaction
        balance_before = user.credits_balance
        balance_after = balance_before + amount
        
        # Create transaction record
        transaction = cls(
            user_id=user_id,
            transaction_type='credit' if amount > 0 else 'debit',
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            category=category,
            **kwargs
        )
        
        # Update user balance
        user.credits_balance = balance_after
        
        # Save both records
        transaction.save()
        user.save()
        
        return transaction
    
    @classmethod
    def get_user_transactions(cls, user_id, limit=50, offset=0):
        """Get user's credit transactions"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit)\
                       .offset(offset)\
                       .all()
    
    @classmethod
    def get_user_balance_history(cls, user_id, days=30):
        """Get user's balance history for the last N days"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter_by(user_id=user_id)\
                       .filter(cls.created_at >= start_date)\
                       .order_by(cls.created_at.asc())\
                       .all()
    
    @classmethod
    def get_total_credits_used(cls, user_id, category=None):
        """Get total credits used by user, optionally filtered by category"""
        query = cls.query.filter_by(user_id=user_id)\
                        .filter(cls.amount < 0)
        
        if category:
            query = query.filter_by(category=category)
        
        result = query.with_entities(db.func.sum(cls.amount)).scalar()
        return abs(result) if result else 0
    
    @classmethod
    def get_total_credits_earned(cls, user_id, category=None):
        """Get total credits earned by user, optionally filtered by category"""
        query = cls.query.filter_by(user_id=user_id)\
                        .filter(cls.amount > 0)
        
        if category:
            query = query.filter_by(category=category)
        
        result = query.with_entities(db.func.sum(cls.amount)).scalar()
        return result if result else 0
    
    def __repr__(self):
        return f'<CreditTransaction {self.user_id} - {self.amount} credits>'


class CreditPackage(BaseModel):
    """Credit packages that users can purchase"""
    __tablename__ = 'credit_packages'
    
    # Package Details
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    
    # Credits & Pricing
    credits_amount = db.Column(db.Integer, nullable=False)
    bonus_credits = db.Column(db.Integer, default=0, nullable=False)  # Extra credits as bonus
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Package Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_popular = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Limits & Restrictions
    max_purchases_per_user = db.Column(db.Integer, nullable=True)  # Null = unlimited
    valid_for_days = db.Column(db.Integer, nullable=True)  # Null = never expires
    
    def total_credits(self):
        """Get total credits including bonus"""
        return self.credits_amount + self.bonus_credits
    
    def credits_per_dollar(self):
        """Calculate credits per dollar value"""
        if self.price > 0:
            return self.total_credits() / self.price
        return 0
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['total_credits'] = self.total_credits()
        data['credits_per_dollar'] = self.credits_per_dollar()
        return data
    
    @classmethod
    def get_active_packages(cls):
        """Get all active credit packages"""
        return cls.query.filter_by(is_active=True)\
                       .order_by(cls.sort_order, cls.price)\
                       .all()
    
    def __repr__(self):
        return f'<CreditPackage {self.name} - {self.total_credits()} credits>'


class TaskCreditCost(BaseModel):
    """Credit costs for different types of tasks"""
    __tablename__ = 'task_credit_costs'
    
    # Task Type
    task_type = db.Column(db.String(50), nullable=False, unique=True)
    task_name = db.Column(db.String(100), nullable=False)
    task_name_ar = db.Column(db.String(100), nullable=False)
    
    # Credit Costs
    base_cost = db.Column(db.Integer, nullable=False)  # Base cost in credits
    
    # Variable Costs (JSON for flexible pricing)
    variable_costs = db.Column(db.Text, nullable=True)  # JSON string
    
    # Task Details
    description = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def get_variable_costs(self):
        """Get variable costs as dictionary"""
        if self.variable_costs:
            try:
                return json.loads(self.variable_costs)
            except:
                return {}
        return {}
    
    def set_variable_costs(self, costs_dict):
        """Set variable costs from dictionary"""
        self.variable_costs = json.dumps(costs_dict)
    
    def calculate_cost(self, **parameters):
        """Calculate total cost based on parameters"""
        total_cost = self.base_cost
        variable_costs = self.get_variable_costs()
        
        for param, value in parameters.items():
            if param in variable_costs:
                cost_config = variable_costs[param]
                if isinstance(cost_config, dict):
                    # Complex cost calculation
                    if 'per_unit' in cost_config:
                        total_cost += cost_config['per_unit'] * value
                    elif 'tiers' in cost_config:
                        # Tiered pricing
                        for tier in cost_config['tiers']:
                            if value >= tier['min'] and (tier.get('max') is None or value <= tier['max']):
                                total_cost += tier['cost']
                                break
                else:
                    # Simple per-unit cost
                    total_cost += cost_config * value
        
        return max(1, total_cost)  # Minimum 1 credit
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['variable_costs'] = self.get_variable_costs()
        return data
    
    @classmethod
    def get_task_cost(cls, task_type, **parameters):
        """Get cost for a specific task type"""
        task_cost = cls.query.filter_by(task_type=task_type, is_active=True).first()
        if task_cost:
            return task_cost.calculate_cost(**parameters)
        return 1  # Default cost if not found
    
    @classmethod
    def get_all_active_costs(cls):
        """Get all active task costs"""
        return cls.query.filter_by(is_active=True).all()
    
    def __repr__(self):
        return f'<TaskCreditCost {self.task_type} - {self.base_cost} credits>'

