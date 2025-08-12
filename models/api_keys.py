"""
API Keys Management Model
نموذج إدارة مفاتيح الـ API

This module handles secure storage and management of API keys for external services.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, List
from cryptography.fernet import Fernet
from src.models.base import db


class APIKey(db.Model):
    """Model for storing encrypted API keys"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False, unique=True)
    api_key = db.Column(db.Text, nullable=False)  # Encrypted
    api_secret = db.Column(db.Text)  # Encrypted (optional)
    endpoint_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    rate_limit_per_minute = db.Column(db.Integer, default=60)
    rate_limit_per_day = db.Column(db.Integer, default=1000)
    monthly_quota = db.Column(db.Integer)
    quota_used = db.Column(db.Integer, default=0)
    quota_reset_date = db.Column(db.DateTime)
    extra_metadata = db.Column(db.Text)  # JSON string for additional config
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<APIKey {self.service_name}>'
    
    def get_metadata(self) -> Dict:
        """Get metadata as dictionary"""
        if self.extra_metadata:
            try:
                return json.loads(self.extra_metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata(self, metadata: Dict):
        """Set metadata from dictionary"""
        self.extra_metadata = json.dumps(metadata)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (without sensitive data)"""
        return {
            'id': self.id,
            'service_name': self.service_name,
            'endpoint_url': self.endpoint_url,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_day': self.rate_limit_per_day,
            'monthly_quota': self.monthly_quota,
            'quota_used': self.quota_used,
            'quota_reset_date': self.quota_reset_date.isoformat() if self.quota_reset_date else None,
            'extra_metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class APIUsageLog(db.Model):
    """Model for logging API usage"""
    __tablename__ = 'api_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    request_type = db.Column(db.String(50), nullable=False)  # image, video, audio, text
    request_data = db.Column(db.Text)  # JSON string of request parameters
    response_status = db.Column(db.String(20), nullable=False)  # success, error, timeout
    response_time_ms = db.Column(db.Integer)
    tokens_used = db.Column(db.Integer, default=0)
    cost_credits = db.Column(db.Float, default=0.0)
    error_message = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    api_key = db.relationship('APIKey', backref='usage_logs')
    user = db.relationship('User', backref='api_usage_logs')
    
    def __repr__(self):
        return f'<APIUsageLog {self.request_type} - {self.response_status}>'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'api_key_id': self.api_key_id,
            'user_id': self.user_id,
            'request_type': self.request_type,
            'request_data': json.loads(self.request_data) if self.request_data else {},
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'tokens_used': self.tokens_used,
            'cost_credits': self.cost_credits,
            'error_message': self.error_message,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat()
        }


class APIKeyManager:
    """Manager class for API keys with encryption support"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Free services configuration
        self.free_services_config = {
            'google_gemini': {
                'name': 'Google Gemini API',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta',
                'rate_limit_per_minute': 15,
                'rate_limit_per_day': 1500,
                'monthly_quota': 50000,
                'services': ['text_generation', 'image_generation', 'text_to_speech'],
                'free_tier': True
            },
            'huggingface': {
                'name': 'Hugging Face Inference API',
                'endpoint': 'https://api-inference.huggingface.co/models',
                'rate_limit_per_minute': 10,
                'rate_limit_per_day': 1000,
                'monthly_quota': 30000,
                'services': ['text_generation', 'image_generation', 'text_to_speech'],
                'free_tier': True
            },
            'google_tts': {
                'name': 'Google Text-to-Speech',
                'endpoint': 'https://texttospeech.googleapis.com/v1',
                'rate_limit_per_minute': 100,
                'rate_limit_per_day': 10000,
                'monthly_quota': 1000000,
                'services': ['text_to_speech'],
                'free_tier': True
            }
        }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API keys"""
        key_file = 'api_encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key"""
        return self.cipher_suite.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
    
    def add_api_key(self, service_name: str, api_key: str, api_secret: str = None, 
                   endpoint_url: str = None, metadata: Dict = None) -> APIKey:
        """Add new API key"""
        
        # Check if service already exists
        existing_key = APIKey.query.filter_by(service_name=service_name).first()
        if existing_key:
            # Update existing key
            existing_key.api_key = self.encrypt_api_key(api_key)
            if api_secret:
                existing_key.api_secret = self.encrypt_api_key(api_secret)
            if endpoint_url:
                existing_key.endpoint_url = endpoint_url
            if metadata:
                existing_key.set_metadata(metadata)
            existing_key.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_key
        
        # Get service configuration
        service_config = self.free_services_config.get(service_name, {})
        
        # Create new API key
        new_key = APIKey(
            service_name=service_name,
            api_key=self.encrypt_api_key(api_key),
            api_secret=self.encrypt_api_key(api_secret) if api_secret else None,
            endpoint_url=endpoint_url or service_config.get('endpoint'),
            rate_limit_per_minute=service_config.get('rate_limit_per_minute', 60),
            rate_limit_per_day=service_config.get('rate_limit_per_day', 1000),
            monthly_quota=service_config.get('monthly_quota'),
            quota_reset_date=datetime.utcnow().replace(day=1)  # Reset monthly
        )
        
        if metadata:
            new_key.set_metadata(metadata)
        
        db.session.add(new_key)
        db.session.commit()
        
        return new_key
    
    def get_api_key(self, service_name: str) -> Optional[Dict]:
        """Get decrypted API key for service"""
        
        api_key_record = APIKey.query.filter_by(
            service_name=service_name, 
            is_active=True
        ).first()
        
        if not api_key_record:
            # Try to get from environment variables
            env_key = os.getenv(f'{service_name.upper()}_API_KEY')
            if env_key:
                return {
                    'api_key': env_key,
                    'api_secret': os.getenv(f'{service_name.upper()}_API_SECRET'),
                    'endpoint_url': self.free_services_config.get(service_name, {}).get('endpoint'),
                    'source': 'environment'
                }
            return None
        
        try:
            decrypted_key = self.decrypt_api_key(api_key_record.api_key)
            decrypted_secret = None
            
            if api_key_record.api_secret:
                decrypted_secret = self.decrypt_api_key(api_key_record.api_secret)
            
            return {
                'api_key': decrypted_key,
                'api_secret': decrypted_secret,
                'endpoint_url': api_key_record.endpoint_url,
                'metadata': api_key_record.get_metadata(),
                'source': 'database'
            }
        
        except Exception as e:
            print(f"Error decrypting API key for {service_name}: {str(e)}")
            return None
    
    def update_api_key_usage(self, service_name: str, tokens_used: int = 1):
        """Update API key usage statistics"""
        
        api_key_record = APIKey.query.filter_by(
            service_name=service_name, 
            is_active=True
        ).first()
        
        if api_key_record:
            api_key_record.usage_count += 1
            api_key_record.quota_used += tokens_used
            api_key_record.last_used = datetime.utcnow()
            db.session.commit()
    
    def log_api_usage(self, service_name: str, user_id: Optional[int] = None,
                     request_type: str = 'unknown', request_data: Dict = None,
                     response_status: str = 'success', response_time_ms: int = 0,
                     tokens_used: int = 1, cost_credits: float = 0.0,
                     error_message: str = None, ip_address: str = None,
                     user_agent: str = None):
        """Log API usage"""
        
        api_key_record = APIKey.query.filter_by(service_name=service_name).first()
        
        if not api_key_record:
            # Create a placeholder record for environment-based keys
            api_key_record = self.add_api_key(service_name, 'env_key')
        
        usage_log = APIUsageLog(
            api_key_id=api_key_record.id,
            user_id=user_id,
            request_type=request_type,
            request_data=json.dumps(request_data) if request_data else None,
            response_status=response_status,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            cost_credits=cost_credits,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(usage_log)
        
        # Update usage statistics
        if response_status == 'success':
            self.update_api_key_usage(service_name, tokens_used)
        
        db.session.commit()
    
    def get_usage_statistics(self, service_name: str = None, 
                           start_date: datetime = None, 
                           end_date: datetime = None) -> Dict:
        """Get usage statistics"""
        
        query = APIUsageLog.query
        
        if service_name:
            api_key_record = APIKey.query.filter_by(service_name=service_name).first()
            if api_key_record:
                query = query.filter_by(api_key_id=api_key_record.id)
        
        if start_date:
            query = query.filter(APIUsageLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(APIUsageLog.created_at <= end_date)
        
        logs = query.all()
        
        stats = {
            'total_requests': len(logs),
            'successful_requests': len([log for log in logs if log.response_status == 'success']),
            'failed_requests': len([log for log in logs if log.response_status == 'error']),
            'total_tokens_used': sum(log.tokens_used for log in logs),
            'total_cost_credits': sum(log.cost_credits for log in logs),
            'average_response_time': sum(log.response_time_ms for log in logs) / len(logs) if logs else 0,
            'request_types': {}
        }
        
        # Group by request type
        for log in logs:
            request_type = log.request_type
            if request_type not in stats['request_types']:
                stats['request_types'][request_type] = {
                    'count': 0,
                    'tokens_used': 0,
                    'cost_credits': 0.0
                }
            
            stats['request_types'][request_type]['count'] += 1
            stats['request_types'][request_type]['tokens_used'] += log.tokens_used
            stats['request_types'][request_type]['cost_credits'] += log.cost_credits
        
        return stats
    
    def get_all_api_keys(self) -> List[Dict]:
        """Get all API keys (without sensitive data)"""
        
        api_keys = APIKey.query.all()
        return [key.to_dict() for key in api_keys]
    
    def deactivate_api_key(self, service_name: str) -> bool:
        """Deactivate API key"""
        
        api_key_record = APIKey.query.filter_by(service_name=service_name).first()
        
        if api_key_record:
            api_key_record.is_active = False
            api_key_record.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
    
    def activate_api_key(self, service_name: str) -> bool:
        """Activate API key"""
        
        api_key_record = APIKey.query.filter_by(service_name=service_name).first()
        
        if api_key_record:
            api_key_record.is_active = True
            api_key_record.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
    
    def check_quota_limits(self, service_name: str) -> Dict:
        """Check quota limits for service"""
        
        api_key_record = APIKey.query.filter_by(service_name=service_name).first()
        
        if not api_key_record:
            return {'within_limits': True, 'message': 'No quota limits configured'}
        
        # Check monthly quota
        if api_key_record.monthly_quota and api_key_record.quota_used >= api_key_record.monthly_quota:
            return {
                'within_limits': False,
                'message': f'Monthly quota exceeded: {api_key_record.quota_used}/{api_key_record.monthly_quota}'
            }
        
        # Check daily limits (simplified - would need more complex logic for real implementation)
        today_usage = APIUsageLog.query.filter(
            APIUsageLog.api_key_id == api_key_record.id,
            APIUsageLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        if today_usage >= api_key_record.rate_limit_per_day:
            return {
                'within_limits': False,
                'message': f'Daily limit exceeded: {today_usage}/{api_key_record.rate_limit_per_day}'
            }
        
        return {
            'within_limits': True,
            'monthly_usage': api_key_record.quota_used,
            'monthly_quota': api_key_record.monthly_quota,
            'daily_usage': today_usage,
            'daily_limit': api_key_record.rate_limit_per_day
        }
    
    def reset_monthly_quota(self, service_name: str = None):
        """Reset monthly quota for service(s)"""
        
        query = APIKey.query
        if service_name:
            query = query.filter_by(service_name=service_name)
        
        api_keys = query.all()
        
        for api_key in api_keys:
            api_key.quota_used = 0
            api_key.quota_reset_date = datetime.utcnow().replace(day=1)
            api_key.updated_at = datetime.utcnow()
        
        db.session.commit()
    
    def get_free_services_info(self) -> Dict:
        """Get information about free services"""
        
        return {
            'services': self.free_services_config,
            'total_services': len(self.free_services_config),
            'configured_services': len(self.get_all_api_keys()),
            'active_services': len([key for key in self.get_all_api_keys() if key['is_active']])
        }


# Global instance
api_key_manager = APIKeyManager()

