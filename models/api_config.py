from src.models.base import db, BaseModel
import os
import json
import base64

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("Warning: cryptography package not available. Encryption features will be disabled.")

class APIConfig(BaseModel):
    """API configuration for external services"""
    __tablename__ = 'api_configs'

    # Service Details
    service_name = db.Column(db.String(50), nullable=False, unique=True)
    service_display_name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(30), nullable=False)  # ai, social_media, payment, analytics, etc.

    # API Configuration
    api_endpoint = db.Column(db.String(500), nullable=True)
    api_version = db.Column(db.String(20), nullable=True)

    # Credentials (Encrypted)
    api_key = db.Column(db.Text, nullable=True)  # Encrypted
    api_secret = db.Column(db.Text, nullable=True)  # Encrypted
    access_token = db.Column(db.Text, nullable=True)  # Encrypted
    refresh_token = db.Column(db.Text, nullable=True)  # Encrypted

    # Additional Configuration (JSON)
    additional_config = db.Column(db.Text, nullable=True)  # JSON string

    # Status & Limits
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)  # Service availability
    rate_limit_per_minute = db.Column(db.Integer, nullable=True)
    rate_limit_per_hour = db.Column(db.Integer, nullable=True)
    rate_limit_per_day = db.Column(db.Integer, nullable=True)

    # Usage Tracking
    total_requests = db.Column(db.Integer, default=0, nullable=False)
    requests_today = db.Column(db.Integer, default=0, nullable=False)
    last_request_at = db.Column(db.DateTime, nullable=True)
    last_error_at = db.Column(db.DateTime, nullable=True)
    last_error_message = db.Column(db.Text, nullable=True)

    # Cost Tracking
    cost_per_request = db.Column(db.Float, default=0.0, nullable=False)
    total_cost = db.Column(db.Float, default=0.0, nullable=False)

    @staticmethod
    def _get_encryption_key():
        """Get or create encryption key"""
        if not CRYPTOGRAPHY_AVAILABLE:
            return None
            
        key = os.environ.get('API_ENCRYPTION_KEY')
        if not key:
            # Generate a new key if not exists
            key = Fernet.generate_key()
            # In production, this should be stored securely
            os.environ['API_ENCRYPTION_KEY'] = base64.b64encode(key).decode()
        else:
            key = base64.b64decode(key.encode())
        return key

    def _encrypt_value(self, value):
        """Encrypt a sensitive value"""
        if not value:
            return None

        if not CRYPTOGRAPHY_AVAILABLE:
            # Fallback: store as base64 (not secure but allows functionality)
            return base64.b64encode(value.encode()).decode()

        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()

    def _decrypt_value(self, encrypted_value):
        """Decrypt a sensitive value"""
        if not encrypted_value:
            return None

        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                # Fallback: decode from base64
                return base64.b64decode(encrypted_value.encode()).decode()
                
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(encrypted_value.encode()).decode()
        except:
            return None

    def set_api_key(self, api_key):
        """Set encrypted API key"""
        self.api_key = self._encrypt_value(api_key)

    def get_api_key(self):
        """Get decrypted API key"""
        return self._decrypt_value(self.api_key)

    def set_api_secret(self, api_secret):
        """Set encrypted API secret"""
        self.api_secret = self._encrypt_value(api_secret)

    def get_api_secret(self):
        """Get decrypted API secret"""
        return self._decrypt_value(self.api_secret)

    def set_access_token(self, access_token):
        """Set encrypted access token"""
        self.access_token = self._encrypt_value(access_token)

    def get_access_token(self):
        """Get decrypted access token"""
        return self._decrypt_value(self.access_token)

    def set_refresh_token(self, refresh_token):
        """Set encrypted refresh token"""
        self.refresh_token = self._encrypt_value(refresh_token)

    def get_refresh_token(self):
        """Get decrypted refresh token"""
        return self._decrypt_value(self.refresh_token)

    def get_additional_config(self):
        """Get additional configuration as dictionary"""
        if self.additional_config:
            try:
                return json.loads(self.additional_config)
            except:
                return {}
        return {}

    def set_additional_config(self, config_dict):
        """Set additional configuration from dictionary"""
        self.additional_config = json.dumps(config_dict)

    def update_config(self, config_key, config_value):
        """Update a specific configuration value"""
        config = self.get_additional_config()
        config[config_key] = config_value
        self.set_additional_config(config)

    def increment_usage(self, cost=None):
        """Increment usage counters"""
        from datetime import datetime

        self.total_requests += 1
        self.requests_today += 1
        self.last_request_at = datetime.utcnow()

        if cost:
            self.total_cost += cost

    def log_error(self, error_message):
        """Log an API error"""
        from datetime import datetime

        self.last_error_at = datetime.utcnow()
        self.last_error_message = error_message

    def reset_daily_counters(self):
        """Reset daily usage counters"""
        self.requests_today = 0

    def is_rate_limited(self):
        """Check if API is currently rate limited"""
        from datetime import datetime, timedelta

        now = datetime.utcnow()

        # Check daily limit
        if self.rate_limit_per_day and self.requests_today >= self.rate_limit_per_day:
            return True

        # For minute/hour limits, we'd need more sophisticated tracking
        # This is a simplified version
        return False

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally excluding sensitive data"""
        data = super().to_dict()

        # Remove encrypted fields unless explicitly requested
        if not include_sensitive:
            sensitive_fields = ['api_key', 'api_secret', 'access_token', 'refresh_token']
            for field in sensitive_fields:
                data.pop(field, None)
        else:
            # Decrypt sensitive fields
            data['api_key'] = self.get_api_key()
            data['api_secret'] = self.get_api_secret()
            data['access_token'] = self.get_access_token()
            data['refresh_token'] = self.get_refresh_token()

        # Parse additional config
        data['additional_config'] = self.get_additional_config()

        # Add computed fields
        data['is_rate_limited'] = self.is_rate_limited()

        return data

    @classmethod
    def get_by_service(cls, service_name):
        """Get API config by service name"""
        return cls.query.filter_by(service_name=service_name).first()

    @classmethod
    def get_active_services(cls, service_type=None):
        """Get all active API services, optionally filtered by type"""
        query = cls.query.filter_by(is_active=True, is_available=True)
        if service_type:
            query = query.filter_by(service_type=service_type)
        return query.all()

    @classmethod
    def get_ai_services(cls):
        """Get all active AI services"""
        return cls.get_active_services('ai')

    @classmethod
    def get_social_media_services(cls):
        """Get all active social media services"""
        return cls.get_active_services('social_media')

    def __repr__(self):
        return f'<APIConfig {self.service_name}>'


class APIUsageLog(BaseModel):
    """API usage logging for detailed tracking"""
    __tablename__ = 'api_usage_logs'

    # API Service
    api_config_id = db.Column(db.String(36), db.ForeignKey('api_configs.id'), nullable=False)
    service_name = db.Column(db.String(50), nullable=False)  # Denormalized for faster queries

    # Request Details
    endpoint = db.Column(db.String(500), nullable=True)
    method = db.Column(db.String(10), nullable=False)  # GET, POST, etc.
    request_size = db.Column(db.Integer, nullable=True)  # Request size in bytes
    response_size = db.Column(db.Integer, nullable=True)  # Response size in bytes

    # Response Details
    status_code = db.Column(db.Integer, nullable=True)
    response_time_ms = db.Column(db.Integer, nullable=True)  # Response time in milliseconds

    # User & Task Context
    user_id = db.Column(db.String(36), nullable=True)  # User who triggered the request
    task_id = db.Column(db.String(36), nullable=True)  # Related task if any

    # Cost & Credits
    cost = db.Column(db.Float, default=0.0, nullable=False)
    credits_used = db.Column(db.Integer, default=0, nullable=False)

    # Error Information
    error_message = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)

    # Additional Data
    log_metadata = db.Column(db.Text, nullable=True)  # JSON for additional information

    # Relationships
    api_config = db.relationship('APIConfig', backref='usage_logs')

    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.log_metadata:
            try:
                return json.loads(self.log_metadata)
            except:
                return {}
        return {}

    def set_log_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.log_metadata = json.dumps(metadata_dict)
    def is_successful(self):
        """Check if request was successful"""
        return self.status_code and 200 <= self.status_code < 300

    def is_error(self):
        """Check if request resulted in error"""
        return not self.is_successful()

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data["log_metadata"] = self.get_metadata()
        data['is_successful'] = self.is_successful()
        data['is_error'] = self.is_error()
        return data

    @classmethod
    def log_request(cls, api_config_id, service_name, method, **kwargs):
        """Create a new API usage log entry"""
        log_entry = cls(
            api_config_id=api_config_id,
            service_name=service_name,
            method=method,
            **kwargs
        )
        log_entry.save()
        return log_entry

    @classmethod
    def get_usage_stats(cls, service_name=None, user_id=None, days=30):
        """Get usage statistics"""
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        query = cls.query.filter(cls.created_at >= start_date)

        if service_name:
            query = query.filter_by(service_name=service_name)

        if user_id:
            query = query.filter_by(user_id=user_id)

        logs = query.all()

        stats = {
            'total_requests': len(logs),
            'successful_requests': len([log for log in logs if log.is_successful()]),
            'failed_requests': len([log for log in logs if log.is_error()]),
            'total_cost': sum(log.cost for log in logs),
            'total_credits': sum(log.credits_used for log in logs),
            'average_response_time': 0
        }

        response_times = [log.response_time_ms for log in logs if log.response_time_ms]
        if response_times:
            stats['average_response_time'] = sum(response_times) / len(response_times)

        return stats

    def __repr__(self):
        return f'<APIUsageLog {self.service_name} - {self.method}>'