"""
External API Integration Layer
طبقة التكامل مع الواجهات الخارجية

This module handles integration with external APIs for media generation
with error handling, rate limiting, and asynchronous processing.
"""

import asyncio
import aiohttp
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
import base64
import io
from PIL import Image
import google.generativeai as genai

from src.models.api_keys import api_key_manager, APIUsageLog
from src.models.base import db

logger = logging.getLogger(__name__)


class APIIntegrationError(Exception):
    """Custom exception for API integration errors"""
    pass


class RateLimitExceeded(APIIntegrationError):
    """Exception raised when rate limit is exceeded"""
    pass


class APIServiceUnavailable(APIIntegrationError):
    """Exception raised when API service is unavailable"""
    pass


class ExternalAPIIntegration:
    """Main class for handling external API integrations"""
    
    def __init__(self):
        self.session = None
        self.rate_limits = {}  # Track rate limits per service
        
        # Supported services configuration
        self.services_config = {
            'google_gemini': {
                'text_generation': {
                    'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'free_tier': True,
                    'rate_limit': 15  # requests per minute
                },
                'image_generation': {
                    'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:generateImage',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'free_tier': True,
                    'rate_limit': 10
                },
                'text_to_speech': {
                    'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'free_tier': True,
                    'rate_limit': 15
                }
            },
            'huggingface': {
                'image_generation': {
                    'endpoint': 'https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0',
                    'method': 'POST',
                    'headers': {'Authorization': 'Bearer {api_key}'},
                    'free_tier': True,
                    'rate_limit': 10  # requests per minute
                },
                'text_to_speech': {
                    'endpoint': 'https://api-inference.huggingface.co/models/microsoft/speecht5_tts',
                    'method': 'POST',
                    'headers': {'Authorization': 'Bearer {api_key}'},
                    'free_tier': True,
                    'rate_limit': 10
                }
            },
            'google_tts': {
                'text_to_speech': {
                    'endpoint': 'https://texttospeech.googleapis.com/v1/text:synthesize',
                    'method': 'POST',
                    'headers': {'Authorization': 'Bearer {api_key}'},
                    'free_tier': True,
                    'rate_limit': 100
                }
            }
        }
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create async HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close async HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def check_rate_limit(self, service_name: str, operation: str) -> bool:
        """Check if rate limit allows the request"""
        key = f"{service_name}_{operation}"
        current_time = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {'requests': [], 'limit': 60}
        
        # Get service rate limit
        service_config = self.services_config.get(service_name, {}).get(operation, {})
        rate_limit = service_config.get('rate_limit', 60)
        
        # Clean old requests (older than 1 minute)
        self.rate_limits[key]['requests'] = [
            req_time for req_time in self.rate_limits[key]['requests']
            if current_time - req_time < 60
        ]
        
        # Check if we can make the request
        if len(self.rate_limits[key]['requests']) >= rate_limit:
            return False
        
        # Add current request
        self.rate_limits[key]['requests'].append(current_time)
        return True
    
    def get_api_credentials(self, service_name: str) -> Optional[Dict]:
        """Get API credentials for service"""
        return api_key_manager.get_api_key(service_name)
    
    def prepare_headers(self, service_name: str, operation: str, api_key: str) -> Dict:
        """Prepare headers for API request"""
        service_config = self.services_config.get(service_name, {}).get(operation, {})
        headers = service_config.get('headers', {}).copy()
        
        # Replace API key placeholder
        for key, value in headers.items():
            if isinstance(value, str) and '{api_key}' in value:
                headers[key] = value.format(api_key=api_key)
        
        return headers
    
    async def make_api_request(self, service_name: str, operation: str, 
                              payload: Dict, user_id: Optional[int] = None,
                              **kwargs) -> Dict:
        """Make async API request with error handling"""
        start_time = time.time()
        
        try:
            # Check rate limit
            if not self.check_rate_limit(service_name, operation):
                raise RateLimitExceeded(f"Rate limit exceeded for {service_name} {operation}")
            
            # Get API credentials
            credentials = self.get_api_credentials(service_name)
            if not credentials:
                raise APIIntegrationError(f"No API credentials found for {service_name}")
            
            # Get service configuration
            service_config = self.services_config.get(service_name, {}).get(operation, {})
            if not service_config:
                raise APIIntegrationError(f"Service {service_name} operation {operation} not configured")
            
            # Prepare request
            endpoint = service_config['endpoint']
            method = service_config['method']
            headers = self.prepare_headers(service_name, operation, credentials['api_key'])
            
            # Add API key to URL for Google services
            if service_name == 'google_gemini':
                endpoint = f"{endpoint}?key={credentials['api_key']}"
            
            # Add content type if not present
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            session = await self.get_session()
            
            # Make request
            async with session.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=payload,
                **kwargs
            ) as response:
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    if response.content_type == 'application/json':
                        result = await response.json()
                    else:
                        # Handle binary content (images, audio)
                        content = await response.read()
                        result = {
                            'content': base64.b64encode(content).decode(),
                            'content_type': response.content_type,
                            'size': len(content)
                        }
                    
                    # Log successful usage
                    api_key_manager.log_api_usage(
                        service_name=service_name,
                        user_id=user_id,
                        request_type=operation,
                        request_data=payload,
                        response_status='success',
                        response_time_ms=response_time,
                        tokens_used=1,
                        cost_credits=self.calculate_cost(service_name, operation, payload)
                    )
                    
                    return {
                        'success': True,
                        'data': result,
                        'response_time': response_time,
                        'service': service_name
                    }
                
                elif response.status == 429:
                    error_msg = "Rate limit exceeded"
                    raise RateLimitExceeded(error_msg)
                
                elif response.status >= 500:
                    error_msg = f"Service unavailable (HTTP {response.status})"
                    raise APIServiceUnavailable(error_msg)
                
                else:
                    error_text = await response.text()
                    error_msg = f"API request failed (HTTP {response.status}): {error_text}"
                    raise APIIntegrationError(error_msg)
        
        except asyncio.TimeoutError:
            error_msg = "Request timeout"
            response_time = int((time.time() - start_time) * 1000)
        except aiohttp.ClientError as e:
            error_msg = f"Network error: {str(e)}"
            response_time = int((time.time() - start_time) * 1000)
        except Exception as e:
            error_msg = str(e)
            response_time = int((time.time() - start_time) * 1000)
        
        # Log failed usage
        api_key_manager.log_api_usage(
            service_name=service_name,
            user_id=user_id,
            request_type=operation,
            request_data=payload,
            response_status='error',
            response_time_ms=response_time,
            error_message=error_msg
        )
        
        return {
            'success': False,
            'error': error_msg,
            'response_time': response_time,
            'service': service_name
        }
    
    def calculate_cost(self, service_name: str, operation: str, payload: Dict) -> float:
        """Calculate cost in credits for the operation"""
        # Basic cost calculation - can be customized per service
        cost_map = {
            'image_generation': 2.0,
            'video_generation': 5.0,
            'text_to_speech': 1.0,
            'text_generation': 1.0
        }
        
        base_cost = cost_map.get(operation, 1.0)
        
        # Adjust cost based on payload complexity
        if operation == 'image_generation':
            # Higher resolution = higher cost
            if 'width' in payload and 'height' in payload:
                pixels = payload['width'] * payload['height']
                if pixels > 1024 * 1024:
                    base_cost *= 2
        
        return base_cost
    
    async def generate_text(self, prompt: str, user_id: Optional[int] = None,
                           max_tokens: int = 1000, temperature: float = 0.7,
                           service: str = "auto") -> Dict:
        """Generate text using external API"""
        
        # Service selection logic
        if service == "auto":
            services_to_try = ['google_gemini']
        else:
            services_to_try = [service]
        
        for service_name in services_to_try:
            try:
                if service_name == 'google_gemini':
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }],
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens,
                            "topP": 0.8,
                            "topK": 10
                        }
                    }
                
                else:
                    continue
                
                result = await self.make_api_request(
                    service_name=service_name,
                    operation='text_generation',
                    payload=payload,
                    user_id=user_id
                )
                
                if result['success']:
                    # Extract text from Gemini response
                    if service_name == 'google_gemini':
                        candidates = result['data'].get('candidates', [])
                        if candidates:
                            content = candidates[0].get('content', {})
                            parts = content.get('parts', [])
                            if parts:
                                result['data']['text'] = parts[0].get('text', '')
                    
                    return result
                
                # If this service failed, try the next one
                logger.warning(f"Text generation failed with {service_name}: {result.get('error')}")
                continue
                
            except Exception as e:
                logger.error(f"Error with {service_name}: {str(e)}")
                continue
        
        return {
            'success': False,
            'error': 'All text generation services failed',
            'service': 'multiple'
        }
    
    async def generate_image(self, prompt: str, user_id: Optional[int] = None,
                           width: int = 1024, height: int = 1024,
                           style: str = "realistic", service: str = "auto") -> Dict:
        """Generate image using external API"""
        
        # Service selection logic
        if service == "auto":
            # Try free services first
            services_to_try = ['google_gemini', 'huggingface']
        else:
            services_to_try = [service]
        
        for service_name in services_to_try:
            try:
                if service_name == 'google_gemini':
                    payload = {
                        "prompt": {
                            "text": prompt
                        },
                        "safetySettings": [
                            {
                                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "threshold": "BLOCK_LOW_AND_ABOVE"
                            },
                            {
                                "category": "HARM_CATEGORY_HATE_SPEECH",
                                "threshold": "BLOCK_LOW_AND_ABOVE"
                            }
                        ],
                        "personGeneration": "DONT_ALLOW"
                    }
                
                elif service_name == 'huggingface':
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "width": width,
                            "height": height,
                            "num_inference_steps": 20
                        }
                    }
                
                else:
                    continue
                
                result = await self.make_api_request(
                    service_name=service_name,
                    operation='image_generation',
                    payload=payload,
                    user_id=user_id
                )
                
                if result['success']:
                    return result
                
                # If this service failed, try the next one
                logger.warning(f"Image generation failed with {service_name}: {result.get('error')}")
                continue
                
            except Exception as e:
                logger.error(f"Error with {service_name}: {str(e)}")
                continue
        
        return {
            'success': False,
            'error': 'All image generation services failed',
            'service': 'multiple'
        }
    
    async def generate_speech(self, text: str, user_id: Optional[int] = None,
                            voice: str = "en-US-Standard-A", language: str = "en-US",
                            service: str = "auto") -> Dict:
        """Generate speech using external API"""
        
        if service == "auto":
            services_to_try = ['google_tts', 'huggingface']
        else:
            services_to_try = [service]
        
        for service_name in services_to_try:
            try:
                if service_name == 'google_tts':
                    payload = {
                        "input": {"text": text},
                        "voice": {
                            "languageCode": language,
                            "name": voice,
                            "ssmlGender": "NEUTRAL"
                        },
                        "audioConfig": {
                            "audioEncoding": "MP3"
                        }
                    }
                
                elif service_name == 'huggingface':
                    payload = {
                        "inputs": text,
                        "parameters": {
                            "speaker_embeddings": "default"
                        }
                    }
                
                else:
                    continue
                
                result = await self.make_api_request(
                    service_name=service_name,
                    operation='text_to_speech',
                    payload=payload,
                    user_id=user_id
                )
                
                if result['success']:
                    return result
                
                logger.warning(f"Speech generation failed with {service_name}: {result.get('error')}")
                continue
                
            except Exception as e:
                logger.error(f"Error with {service_name}: {str(e)}")
                continue
        
        return {
            'success': False,
            'error': 'All speech generation services failed',
            'service': 'multiple'
        }
    
    def get_service_status(self) -> Dict:
        """Get status of all configured services"""
        status = {}
        
        for service_name, operations in self.services_config.items():
            service_status = {
                'available': True,
                'operations': list(operations.keys()),
                'free_tier': any(op.get('free_tier', False) for op in operations.values()),
                'rate_limits': {}
            }
            
            # Check rate limits
            for operation in operations.keys():
                key = f"{service_name}_{operation}"
                if key in self.rate_limits:
                    remaining = operations[operation].get('rate_limit', 60) - len(self.rate_limits[key]['requests'])
                    service_status['rate_limits'][operation] = max(0, remaining)
                else:
                    service_status['rate_limits'][operation] = operations[operation].get('rate_limit', 60)
            
            status[service_name] = service_status
        
        return status
    
    async def health_check(self) -> Dict:
        """Perform health check on all services"""
        health_status = {}
        
        for service_name in self.services_config.keys():
            try:
                # Simple test request
                if 'text_generation' in self.services_config[service_name]:
                    result = await self.generate_text("Hello", service=service_name)
                    health_status[service_name] = {
                        'status': 'healthy' if result['success'] else 'unhealthy',
                        'response_time': result.get('response_time', 0),
                        'error': result.get('error')
                    }
                else:
                    health_status[service_name] = {
                        'status': 'unknown',
                        'message': 'No test endpoint available'
                    }
            
            except Exception as e:
                health_status[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status


# Global instance
api_integration = ExternalAPIIntegration()

