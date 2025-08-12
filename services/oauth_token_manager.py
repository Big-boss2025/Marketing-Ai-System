import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import base64
import secrets
from cryptography.fernet import Fernet
from src.models.base import db
from src.models.user import User
from typing import List, Dict


logger = logging.getLogger(__name__)

class OAuthToken(db.Model):
    """OAuth Token model for storing encrypted tokens"""
    __tablename__ = 'oauth_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # facebook, instagram, tiktok, youtube, twitter
    access_token = db.Column(db.Text, nullable=False)  # Encrypted
    refresh_token = db.Column(db.Text)  # Encrypted
    token_type = db.Column(db.String(20), default='Bearer')
    expires_at = db.Column(db.DateTime)
    scope = db.Column(db.Text)
    platform_user_id = db.Column(db.String(100))
    platform_username = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='oauth_tokens')

class OAuthTokenManager:
    """OAuth Token Manager for handling social media platform tokens"""
    
    def __init__(self):
        # Encryption key for tokens
        self.encryption_key = self.get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Platform configurations
        self.platform_configs = {
            'facebook': {
                'client_id': 'YOUR_FACEBOOK_APP_ID',
                'client_secret': 'YOUR_FACEBOOK_APP_SECRET',
                'redirect_uri': 'https://your-domain.com/auth/facebook/callback',
                'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'scopes': ['pages_manage_posts', 'pages_read_engagement', 'instagram_basic', 'instagram_content_publish'],
                'token_expires': True
            },
            'instagram': {
                'client_id': 'YOUR_INSTAGRAM_APP_ID',
                'client_secret': 'YOUR_INSTAGRAM_APP_SECRET',
                'redirect_uri': 'https://your-domain.com/auth/instagram/callback',
                'auth_url': 'https://api.instagram.com/oauth/authorize',
                'token_url': 'https://api.instagram.com/oauth/access_token',
                'scopes': ['user_profile', 'user_media'],
                'token_expires': True
            },
            'tiktok': {
                'client_key': 'YOUR_TIKTOK_CLIENT_KEY',
                'client_secret': 'YOUR_TIKTOK_CLIENT_SECRET',
                'redirect_uri': 'https://your-domain.com/auth/tiktok/callback',
                'auth_url': 'https://www.tiktok.com/auth/authorize/',
                'token_url': 'https://open-api.tiktok.com/oauth/access_token/',
                'scopes': ['user.info.basic', 'video.list', 'video.upload'],
                'token_expires': True
            },
            'youtube': {
                'client_id': 'YOUR_YOUTUBE_CLIENT_ID',
                'client_secret': 'YOUR_YOUTUBE_CLIENT_SECRET',
                'redirect_uri': 'https://your-domain.com/auth/youtube/callback',
                'auth_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'scopes': ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly'],
                'token_expires': True
            },
            'twitter': {
                'client_id': 'YOUR_TWITTER_CLIENT_ID',
                'client_secret': 'YOUR_TWITTER_CLIENT_SECRET',
                'redirect_uri': 'https://your-domain.com/auth/twitter/callback',
                'auth_url': 'https://twitter.com/i/oauth2/authorize',
                'token_url': 'https://api.twitter.com/2/oauth2/token',
                'scopes': ['tweet.read', 'tweet.write', 'users.read'],
                'token_expires': True
            }
        }
    
    def get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for tokens"""
        try:
            # In production, store this securely (environment variable, key management service)
            key_file = '/tmp/oauth_encryption_key'
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except FileNotFoundError:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                return key
        except Exception as e:
            logger.error(f"Error managing encryption key: {str(e)}")
            return Fernet.generate_key()
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for storage"""
        try:
            return self.cipher_suite.encrypt(token.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting token: {str(e)}")
            return token
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage"""
        try:
            return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting token: {str(e)}")
            return encrypted_token
    
    def generate_auth_url(self, platform: str, user_id: int, state: Optional[str] = None) -> Dict:
        """Generate OAuth authorization URL"""
        try:
            if platform not in self.platform_configs:
                return {'success': False, 'error': f'Unsupported platform: {platform}'}
            
            config = self.platform_configs[platform]
            
            # Generate state parameter for security
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Store state in session or database for verification
            self.store_oauth_state(user_id, platform, state)
            
            # Build authorization URL
            params = {
                'response_type': 'code',
                'client_id': config.get('client_id') or config.get('client_key'),
                'redirect_uri': config['redirect_uri'],
                'scope': ' '.join(config['scopes']),
                'state': f"{user_id}:{platform}:{state}"
            }
            
            # Platform-specific parameters
            if platform == 'tiktok':
                params['client_key'] = config['client_key']
                del params['client_id']
            
            # Build URL
            auth_url = config['auth_url']
            query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
            full_url = f"{auth_url}?{query_string}"
            
            return {
                'success': True,
                'auth_url': full_url,
                'state': state,
                'platform': platform
            }
            
        except Exception as e:
            logger.error(f"Error generating auth URL for {platform}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def exchange_code_for_token(self, platform: str, code: str, state: str) -> Dict:
        """Exchange authorization code for access token"""
        try:
            if platform not in self.platform_configs:
                return {'success': False, 'error': f'Unsupported platform: {platform}'}
            
            # Verify state parameter
            state_parts = state.split(':')
            if len(state_parts) != 3:
                return {'success': False, 'error': 'Invalid state parameter'}
            
            user_id, platform_from_state, state_token = state_parts
            if platform_from_state != platform:
                return {'success': False, 'error': 'Platform mismatch in state'}
            
            if not self.verify_oauth_state(int(user_id), platform, state_token):
                return {'success': False, 'error': 'Invalid or expired state'}
            
            config = self.platform_configs[platform]
            
            # Prepare token request
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': config['redirect_uri']
            }
            
            # Platform-specific token request
            if platform in ['facebook', 'instagram']:
                token_data.update({
                    'client_id': config['client_id'],
                    'client_secret': config['client_secret']
                })
                response = requests.post(config['token_url'], data=token_data, timeout=30)
                
            elif platform == 'tiktok':
                token_data.update({
                    'client_key': config['client_key'],
                    'client_secret': config['client_secret']
                })
                response = requests.post(config['token_url'], json=token_data, timeout=30)
                
            elif platform in ['youtube', 'twitter']:
                # Use basic auth for Google/Twitter
                auth_header = base64.b64encode(
                    f"{config['client_id']}:{config['client_secret']}".encode()
                ).decode()
                
                headers = {
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                response = requests.post(config['token_url'], data=token_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_info = response.json()
                
                # Extract token information
                access_token = token_info.get('access_token')
                refresh_token = token_info.get('refresh_token')
                expires_in = token_info.get('expires_in')
                token_type = token_info.get('token_type', 'Bearer')
                scope = token_info.get('scope', ' '.join(config['scopes']))
                
                if not access_token:
                    return {'success': False, 'error': 'No access token received'}
                
                # Calculate expiration time
                expires_at = None
                if expires_in:
                    expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
                
                # Get platform user info
                user_info = self.get_platform_user_info(platform, access_token)
                
                # Store token
                result = self.store_token(
                    user_id=int(user_id),
                    platform=platform,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type=token_type,
                    expires_at=expires_at,
                    scope=scope,
                    platform_user_id=user_info.get('id'),
                    platform_username=user_info.get('username')
                )
                
                if result['success']:
                    return {
                        'success': True,
                        'message': f'{platform} account connected successfully',
                        'platform': platform,
                        'platform_username': user_info.get('username'),
                        'expires_at': expires_at.isoformat() if expires_at else None
                    }
                else:
                    return result
            else:
                logger.error(f"Token exchange failed for {platform}: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Token exchange failed: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error exchanging code for token ({platform}): {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_platform_user_info(self, platform: str, access_token: str) -> Dict:
        """Get user info from platform"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            if platform == 'facebook':
                response = requests.get(
                    'https://graph.facebook.com/v18.0/me?fields=id,name,email',
                    headers=headers,
                    timeout=30
                )
            elif platform == 'instagram':
                response = requests.get(
                    'https://graph.instagram.com/me?fields=id,username',
                    headers=headers,
                    timeout=30
                )
            elif platform == 'tiktok':
                response = requests.get(
                    'https://open-api.tiktok.com/user/info/',
                    headers=headers,
                    timeout=30
                )
            elif platform == 'youtube':
                response = requests.get(
                    'https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',
                    headers=headers,
                    timeout=30
                )
            elif platform == 'twitter':
                response = requests.get(
                    'https://api.twitter.com/2/users/me',
                    headers=headers,
                    timeout=30
                )
            else:
                return {}
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract user info based on platform
                if platform == 'facebook':
                    return {
                        'id': data.get('id'),
                        'username': data.get('name'),
                        'email': data.get('email')
                    }
                elif platform == 'instagram':
                    return {
                        'id': data.get('id'),
                        'username': data.get('username')
                    }
                elif platform == 'tiktok':
                    user_data = data.get('data', {}).get('user', {})
                    return {
                        'id': user_data.get('open_id'),
                        'username': user_data.get('display_name')
                    }
                elif platform == 'youtube':
                    items = data.get('items', [])
                    if items:
                        channel = items[0]
                        return {
                            'id': channel.get('id'),
                            'username': channel.get('snippet', {}).get('title')
                        }
                elif platform == 'twitter':
                    user_data = data.get('data', {})
                    return {
                        'id': user_data.get('id'),
                        'username': user_data.get('username')
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting platform user info ({platform}): {str(e)}")
            return {}
    
    def store_token(self, user_id: int, platform: str, access_token: str,
                   refresh_token: Optional[str] = None, token_type: str = 'Bearer',
                   expires_at: Optional[datetime] = None, scope: Optional[str] = None,
                   platform_user_id: Optional[str] = None, platform_username: Optional[str] = None) -> Dict:
        """Store OAuth token in database"""
        try:
            # Check if token already exists
            existing_token = OAuthToken.query.filter_by(
                user_id=user_id,
                platform=platform
            ).first()
            
            if existing_token:
                # Update existing token
                existing_token.access_token = self.encrypt_token(access_token)
                existing_token.refresh_token = self.encrypt_token(refresh_token) if refresh_token else None
                existing_token.token_type = token_type
                existing_token.expires_at = expires_at
                existing_token.scope = scope
                existing_token.platform_user_id = platform_user_id
                existing_token.platform_username = platform_username
                existing_token.is_active = True
                existing_token.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Token updated successfully',
                    'token_id': existing_token.id
                }
            else:
                # Create new token
                new_token = OAuthToken(
                    user_id=user_id,
                    platform=platform,
                    access_token=self.encrypt_token(access_token),
                    refresh_token=self.encrypt_token(refresh_token) if refresh_token else None,
                    token_type=token_type,
                    expires_at=expires_at,
                    scope=scope,
                    platform_user_id=platform_user_id,
                    platform_username=platform_username,
                    is_active=True
                )
                
                db.session.add(new_token)
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Token stored successfully',
                    'token_id': new_token.id
                }
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error storing token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_valid_token(self, user_id: int, platform: str) -> Optional[str]:
        """Get valid access token for user and platform"""
        try:
            token_record = OAuthToken.query.filter_by(
                user_id=user_id,
                platform=platform,
                is_active=True
            ).first()
            
            if not token_record:
                return None
            
            # Check if token is expired
            if token_record.expires_at and token_record.expires_at <= datetime.utcnow():
                # Try to refresh token
                if token_record.refresh_token:
                    refresh_result = self.refresh_token(user_id, platform)
                    if refresh_result['success']:
                        # Get updated token
                        updated_token = OAuthToken.query.get(token_record.id)
                        return self.decrypt_token(updated_token.access_token)
                    else:
                        # Mark token as inactive
                        token_record.is_active = False
                        db.session.commit()
                        return None
                else:
                    # No refresh token, mark as inactive
                    token_record.is_active = False
                    db.session.commit()
                    return None
            
            return self.decrypt_token(token_record.access_token)
            
        except Exception as e:
            logger.error(f"Error getting valid token: {str(e)}")
            return None
    
    def refresh_token(self, user_id: int, platform: str) -> Dict:
        """Refresh expired access token"""
        try:
            token_record = OAuthToken.query.filter_by(
                user_id=user_id,
                platform=platform,
                is_active=True
            ).first()
            
            if not token_record or not token_record.refresh_token:
                return {'success': False, 'error': 'No refresh token available'}
            
            config = self.platform_configs.get(platform)
            if not config:
                return {'success': False, 'error': f'Unsupported platform: {platform}'}
            
            refresh_token = self.decrypt_token(token_record.refresh_token)
            
            # Prepare refresh request
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            # Platform-specific refresh
            if platform in ['facebook', 'instagram']:
                refresh_data.update({
                    'client_id': config['client_id'],
                    'client_secret': config['client_secret']
                })
                response = requests.post(config['token_url'], data=refresh_data, timeout=30)
                
            elif platform in ['youtube', 'twitter']:
                auth_header = base64.b64encode(
                    f"{config['client_id']}:{config['client_secret']}".encode()
                ).decode()
                
                headers = {
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                response = requests.post(config['token_url'], data=refresh_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_info = response.json()
                
                # Update token record
                new_access_token = token_info.get('access_token')
                new_refresh_token = token_info.get('refresh_token', refresh_token)
                expires_in = token_info.get('expires_in')
                
                if new_access_token:
                    token_record.access_token = self.encrypt_token(new_access_token)
                    token_record.refresh_token = self.encrypt_token(new_refresh_token)
                    
                    if expires_in:
                        token_record.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
                    
                    token_record.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'message': 'Token refreshed successfully'
                    }
            
            return {'success': False, 'error': f'Token refresh failed: {response.status_code}'}
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def revoke_token(self, user_id: int, platform: str) -> Dict:
        """Revoke OAuth token"""
        try:
            token_record = OAuthToken.query.filter_by(
                user_id=user_id,
                platform=platform,
                is_active=True
            ).first()
            
            if not token_record:
                return {'success': False, 'error': 'Token not found'}
            
            # Mark as inactive
            token_record.is_active = False
            token_record.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{platform} token revoked successfully'
            }
            
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_user_connected_platforms(self, user_id: int) -> List[Dict]:
        """Get list of connected platforms for user"""
        try:
            tokens = OAuthToken.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()
            
            connected_platforms = []
            for token in tokens:
                platform_info = {
                    'platform': token.platform,
                    'platform_username': token.platform_username,
                    'connected_at': token.created_at.isoformat(),
                    'expires_at': token.expires_at.isoformat() if token.expires_at else None,
                    'is_expired': token.expires_at <= datetime.utcnow() if token.expires_at else False
                }
                connected_platforms.append(platform_info)
            
            return connected_platforms
            
        except Exception as e:
            logger.error(f"Error getting connected platforms: {str(e)}")
            return []
    
    def store_oauth_state(self, user_id: int, platform: str, state: str):
        """Store OAuth state for verification"""
        # In production, use Redis or database
        # For now, we'll use a simple in-memory storage
        if not hasattr(self, '_oauth_states'):
            self._oauth_states = {}
        
        key = f"{user_id}:{platform}"
        self._oauth_states[key] = {
            'state': state,
            'created_at': datetime.utcnow()
        }
    
    def verify_oauth_state(self, user_id: int, platform: str, state: str) -> bool:
        """Verify OAuth state parameter"""
        try:
            if not hasattr(self, '_oauth_states'):
                return False
            
            key = f"{user_id}:{platform}"
            stored_state = self._oauth_states.get(key)
            
            if not stored_state:
                return False
            
            # Check if state matches and is not expired (5 minutes)
            if stored_state['state'] == state:
                if datetime.utcnow() - stored_state['created_at'] < timedelta(minutes=5):
                    # Remove used state
                    del self._oauth_states[key]
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying OAuth state: {str(e)}")
            return False

# Global OAuth token manager instance
oauth_token_manager = OAuthTokenManager()

