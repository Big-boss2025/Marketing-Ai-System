from src.models.base import db, BaseModel
from datetime import datetime
import json

class Task(BaseModel):
    """Task model for tracking user tasks"""
    __tablename__ = 'tasks'

    # Task Details
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Task Status
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, running, completed, failed

    # Task Parameters
    task_parameters = db.Column(db.Text, nullable=True)  # JSON
    result_data = db.Column(db.Text, nullable=True)  # JSON

    # Credits
    credits_cost = db.Column(db.Integer, default=0, nullable=False)

    # Timing
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='tasks')

    def get_parameters(self):
        """Get task parameters as dictionary"""
        if self.task_parameters:
            try:
                return json.loads(self.task_parameters)
            except:
                return {}
        return {}

    def set_parameters(self, params_dict):
        """Set task parameters from dictionary"""
        self.task_parameters = json.dumps(params_dict)

    def get_result_data(self):
        """Get result data as dictionary"""
        if self.result_data:
            try:
                return json.loads(self.result_data)
            except:
                return {}
        return {}

    def set_result_data(self, result_dict):
        """Set result data from dictionary"""
        self.result_data = json.dumps(result_dict)

    def mark_started(self):
        """Mark task as started"""
        self.status = 'running'
        self.started_at = datetime.utcnow()

    def mark_completed(self, result_data=None):
        """Mark task as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if result_data:
            self.set_result_data(result_data)

    def mark_failed(self, error_message=""):
        """Mark task as failed"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        if error_message:
            result = {'error': error_message}
            self.set_result_data(result)

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['parameters'] = self.get_parameters()
        data['result_data'] = self.get_result_data()
        return data

    def __repr__(self):
        return f'<Task {self.id} - {self.task_type}>'


class Campaign(BaseModel):
    """Campaign model for marketing campaigns"""
    __tablename__ = 'campaigns'

    # Campaign Details
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Campaign Status
    status = db.Column(db.String(20), default='draft', nullable=False)  # draft, active, paused, completed

    # Campaign Dates
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    # Campaign Metrics
    budget = db.Column(db.Float, default=0.0, nullable=False)
    spent_amount = db.Column(db.Float, default=0.0, nullable=False)

    # Campaign Settings
    campaign_settings = db.Column(db.Text, nullable=True)  # JSON

    # Relationships
    user = db.relationship('User', backref='campaigns')

    def get_settings(self):
        """Get campaign settings as dictionary"""
        if self.campaign_settings:
            try:
                return json.loads(self.campaign_settings)
            except:
                return {}
        return {}

    def set_settings(self, settings_dict):
        """Set campaign settings from dictionary"""
        self.campaign_settings = json.dumps(settings_dict)

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['settings'] = self.get_settings()
        return data

    def __repr__(self):
        return f'<Campaign {self.id} - {self.name}>'