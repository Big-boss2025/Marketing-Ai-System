import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import logging
from src.models.api_config import APIConfig, APIUsageLog
from src.models.base import db

logger = logging.getLogger(__name__)

class APIManager:
    """Centralized API management for external services"""
    
    def __init__(self):
        self.rate_limits = {}  # Track rate limits per service
        self.last_requests = {}  # Track last request times
    
    def get_service_config(self, service_name: str) -> Optional[APIConfig]:
        """Get API configuration for a service"""
        return APIConfig.get_by_service(service_name)
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if service is available and not rate limited"""
        config = self.get_service_config(service_name)
        if not config or not config.is_active or not config.is_available:
            return False
        
        return not config.is_rate_limited()
    
    def make_request(self, service_name: str, endpoint: str, method: str = 'GET', 
                    data: Dict = None, headers: Dict = None, user_id: str = None,
                    task_id: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Make an API request with proper logging and error handling"""
        
        config = self.get_service_config(service_name)
        if not config:
            raise ValueError(f"Service {service_name} not configured")
        
        if not self.is_service_available(service_name):
            raise ValueError(f"Service {service_name} is not available or rate limited")
        
        # Prepare request
        url = f"{config.api_endpoint.rstrip('/')}/{endpoint.lstrip('/')}"
        request_headers = headers or {}
        
        # Add authentication headers
        if config.get_api_key():
            request_headers['Authorization'] = f"Bearer {config.get_api_key()}"
        elif config.get_access_token():
            request_headers['Authorization'] = f"Bearer {config.get_access_token()}"
        
        # Add content type for POST/PUT requests
        if method.upper() in ['POST', 'PUT', 'PATCH'] and 'Content-Type' not in request_headers:
            request_headers['Content-Type'] = 'application/json'
        
        # Prepare request data
        request_data = None
        if data and method.upper() in ['POST', 'PUT', 'PATCH']:
            request_data = json.dumps(data) if isinstance(data, dict) else data
        
        # Log request start
        start_time = time.time()
        log_entry = APIUsageLog(
            api_config_id=config.id,
            service_name=service_name,
            endpoint=endpoint,
            method=method.upper(),
            user_id=user_id,
            task_id=task_id
        )
        
        try:
            # Make the request
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                data=request_data,
                timeout=timeout
            )
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Update log entry
            log_entry.status_code = response.status_code
            log_entry.response_time_ms = response_time_ms
            log_entry.request_size = len(request_data) if request_data else 0
            log_entry.response_size = len(response.content) if response.content else 0
            
            # Update API config usage
            config.increment_usage(config.cost_per_request)
            
            # Check if response is successful
            if response.status_code >= 400:
                error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                log_entry.error_message = error_message
                log_entry.error_code = str(response.status_code)
                config.log_error(error_message)
                
                # Save log entry
                log_entry.save()
                config.save()
                
                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status_code,
                    'response_time_ms': response_time_ms
                }
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Save successful log entry
            log_entry.cost = config.cost_per_request
            log_entry.save()
            config.save()
            
            return {
                'success': True,
                'data': response_data,
                'status_code': response.status_code,
                'response_time_ms': response_time_ms,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.Timeout:
            error_message = f"Request timeout after {timeout} seconds"
            log_entry.error_message = error_message
            log_entry.error_code = 'TIMEOUT'
            log_entry.save()
            config.log_error(error_message)
            config.save()
            
            return {
                'success': False,
                'error': error_message,
                'status_code': 408
            }
            
        except requests.exceptions.ConnectionError:
            error_message = "Connection error - service unavailable"
            log_entry.error_message = error_message
            log_entry.error_code = 'CONNECTION_ERROR'
            log_entry.save()
            config.log_error(error_message)
            config.save()
            
            return {
                'success': False,
                'error': error_message,
                'status_code': 503
            }
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            log_entry.error_message = error_message
            log_entry.error_code = 'UNEXPECTED_ERROR'
            log_entry.save()
            config.log_error(error_message)
            config.save()
            
            return {
                'success': False,
                'error': error_message,
                'status_code': 500
            }
    
    def test_service_connection(self, service_name: str) -> Dict[str, Any]:
        """Test connection to a service"""
        config = self.get_service_config(service_name)
        if not config:
            return {'success': False, 'error': 'Service not configured'}
        
        # Define test endpoints for different service types
        test_endpoints = {
            'ai': '/models',  # Common AI service endpoint
            'social_media': '/me',  # Common social media endpoint
            'payment': '/account',  # Common payment service endpoint
            'analytics': '/reports'  # Common analytics endpoint
        }
        
        test_endpoint = test_endpoints.get(config.service_type, '/')
        
        try:
            result = self.make_request(service_name, test_endpoint, method='GET')
            return {
                'success': result['success'],
                'message': 'Connection successful' if result['success'] else result.get('error', 'Connection failed'),
                'response_time_ms': result.get('response_time_ms', 0)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection test failed: {str(e)}"
            }
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get detailed status of a service"""
        config = self.get_service_config(service_name)
        if not config:
            return {'error': 'Service not configured'}
        
        # Get recent usage stats
        recent_logs = APIUsageLog.query.filter_by(service_name=service_name)\
                                      .filter(APIUsageLog.created_at >= datetime.utcnow() - timedelta(hours=24))\
                                      .all()
        
        successful_requests = len([log for log in recent_logs if log.is_successful()])
        failed_requests = len([log for log in recent_logs if log.is_error()])
        total_requests = len(recent_logs)
        
        avg_response_time = 0
        if recent_logs:
            response_times = [log.response_time_ms for log in recent_logs if log.response_time_ms]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'service_name': service_name,
            'display_name': config.service_display_name,
            'is_active': config.is_active,
            'is_available': config.is_available,
            'is_rate_limited': config.is_rate_limited(),
            'last_request_at': config.last_request_at.isoformat() if config.last_request_at else None,
            'last_error_at': config.last_error_at.isoformat() if config.last_error_at else None,
            'last_error_message': config.last_error_message,
            'total_requests': config.total_requests,
            'requests_today': config.requests_today,
            'total_cost': config.total_cost,
            'recent_stats': {
                'total_requests_24h': total_requests,
                'successful_requests_24h': successful_requests,
                'failed_requests_24h': failed_requests,
                'success_rate_24h': (successful_requests / total_requests * 100) if total_requests > 0 else 100,
                'avg_response_time_ms': avg_response_time
            }
        }
    
    def get_all_services_status(self) -> List[Dict[str, Any]]:
        """Get status of all configured services"""
        services = APIConfig.query.all()
        return [self.get_service_status(service.service_name) for service in services]
    
    def reset_daily_counters(self):
        """Reset daily counters for all services (should be called daily)"""
        services = APIConfig.query.all()
        for service in services:
            service.reset_daily_counters()
            service.save()
    
    def disable_failing_services(self, error_threshold: int = 10, time_window_hours: int = 1):
        """Automatically disable services with too many errors"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        services = APIConfig.query.filter_by(is_active=True).all()
        
        for service in services:
            error_count = APIUsageLog.query.filter_by(service_name=service.service_name)\
                                          .filter(APIUsageLog.created_at >= cutoff_time)\
                                          .filter(APIUsageLog.status_code >= 400)\
                                          .count()
            
            if error_count >= error_threshold:
                service.is_available = False
                service.log_error(f"Service automatically disabled due to {error_count} errors in {time_window_hours} hours")
                service.save()
                
                logger.warning(f"Service {service.service_name} automatically disabled due to high error rate")

# Global API manager instance
api_manager = APIManager()

