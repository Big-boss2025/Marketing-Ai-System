from flask import Blueprint, request, jsonify, redirect, session
import logging
from datetime import datetime
from src.services.oauth_token_manager import oauth_token_manager

logger = logging.getLogger(__name__)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

@oauth_bp.route('/connect/<platform>/<int:user_id>', methods=['GET'])
def connect_platform(platform, user_id):
    """Generate OAuth authorization URL for platform connection"""
    try:
        result = oauth_token_manager.generate_auth_url(platform, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/callback/facebook', methods=['GET'])
def facebook_callback():
    """Handle Facebook OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'error': f'Facebook OAuth error: {error}',
                'error_description': request.args.get('error_description')
            }), 400
        
        if not code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing code or state parameter'
            }), 400
        
        result = oauth_token_manager.exchange_code_for_token('facebook', code, state)
        
        if result['success']:
            # Redirect to success page or return JSON
            return jsonify({
                'success': True,
                'message': 'Facebook account connected successfully',
                'platform': 'facebook',
                'username': result.get('platform_username')
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling Facebook callback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/callback/instagram', methods=['GET'])
def instagram_callback():
    """Handle Instagram OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'error': f'Instagram OAuth error: {error}',
                'error_description': request.args.get('error_description')
            }), 400
        
        if not code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing code or state parameter'
            }), 400
        
        result = oauth_token_manager.exchange_code_for_token('instagram', code, state)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Instagram account connected successfully',
                'platform': 'instagram',
                'username': result.get('platform_username')
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling Instagram callback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/callback/tiktok', methods=['GET'])
def tiktok_callback():
    """Handle TikTok OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'error': f'TikTok OAuth error: {error}',
                'error_description': request.args.get('error_description')
            }), 400
        
        if not code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing code or state parameter'
            }), 400
        
        result = oauth_token_manager.exchange_code_for_token('tiktok', code, state)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'TikTok account connected successfully',
                'platform': 'tiktok',
                'username': result.get('platform_username')
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling TikTok callback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/callback/youtube', methods=['GET'])
def youtube_callback():
    """Handle YouTube OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'error': f'YouTube OAuth error: {error}',
                'error_description': request.args.get('error_description')
            }), 400
        
        if not code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing code or state parameter'
            }), 400
        
        result = oauth_token_manager.exchange_code_for_token('youtube', code, state)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'YouTube account connected successfully',
                'platform': 'youtube',
                'username': result.get('platform_username')
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling YouTube callback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/callback/twitter', methods=['GET'])
def twitter_callback():
    """Handle Twitter OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'error': f'Twitter OAuth error: {error}',
                'error_description': request.args.get('error_description')
            }), 400
        
        if not code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing code or state parameter'
            }), 400
        
        result = oauth_token_manager.exchange_code_for_token('twitter', code, state)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Twitter account connected successfully',
                'platform': 'twitter',
                'username': result.get('platform_username')
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling Twitter callback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/disconnect/<platform>/<int:user_id>', methods=['POST'])
def disconnect_platform(platform, user_id):
    """Disconnect platform from user account"""
    try:
        result = oauth_token_manager.revoke_token(user_id, platform)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error disconnecting platform: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/connected/<int:user_id>', methods=['GET'])
def get_connected_platforms(user_id):
    """Get list of connected platforms for user"""
    try:
        connected_platforms = oauth_token_manager.get_user_connected_platforms(user_id)
        
        return jsonify({
            'success': True,
            'connected_platforms': connected_platforms,
            'total_connected': len(connected_platforms)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connected platforms: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/refresh/<platform>/<int:user_id>', methods=['POST'])
def refresh_platform_token(platform, user_id):
    """Refresh expired token for platform"""
    try:
        result = oauth_token_manager.refresh_token(user_id, platform)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/status/<platform>/<int:user_id>', methods=['GET'])
def check_token_status(platform, user_id):
    """Check token status for platform"""
    try:
        token = oauth_token_manager.get_valid_token(user_id, platform)
        
        if token:
            return jsonify({
                'success': True,
                'has_valid_token': True,
                'platform': platform,
                'message': 'Valid token available'
            }), 200
        else:
            return jsonify({
                'success': True,
                'has_valid_token': False,
                'platform': platform,
                'message': 'No valid token available',
                'action_required': 'reconnect'
            }), 200
            
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported platforms"""
    try:
        platforms = [
            {
                'platform': 'facebook',
                'name': 'Facebook',
                'description': 'Connect your Facebook page to post and analyze content',
                'features': ['post_content', 'get_analytics', 'manage_comments']
            },
            {
                'platform': 'instagram',
                'name': 'Instagram',
                'description': 'Connect your Instagram business account',
                'features': ['post_content', 'get_analytics', 'stories']
            },
            {
                'platform': 'tiktok',
                'name': 'TikTok',
                'description': 'Connect your TikTok account for video posting',
                'features': ['post_videos', 'get_analytics']
            },
            {
                'platform': 'youtube',
                'name': 'YouTube',
                'description': 'Connect your YouTube channel',
                'features': ['upload_videos', 'get_analytics', 'manage_channel']
            },
            {
                'platform': 'twitter',
                'name': 'Twitter',
                'description': 'Connect your Twitter account',
                'features': ['post_tweets', 'get_analytics', 'manage_replies']
            }
        ]
        
        return jsonify({
            'success': True,
            'platforms': platforms,
            'total_platforms': len(platforms)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting supported platforms: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/health', methods=['GET'])
def oauth_health_check():
    """Health check endpoint for OAuth service"""
    return jsonify({
        'success': True,
        'message': 'OAuth service is healthy',
        'timestamp': str(datetime.utcnow()),
        'supported_platforms': ['facebook', 'instagram', 'tiktok', 'youtube', 'twitter']
    }), 200

