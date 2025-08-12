import logging
import json
import requests
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.models.content import Content
from src.models.user import User
from src.services.oauth_token_manager import oauth_token_manager

logger = logging.getLogger(__name__)

class SocialMediaWebhooks:
    """Social Media Webhooks Handler for receiving platform notifications"""
    
    def __init__(self):
        # Webhook verification tokens
        self.webhook_secrets = {
            'facebook': 'YOUR_FACEBOOK_WEBHOOK_SECRET',
            'instagram': 'YOUR_INSTAGRAM_WEBHOOK_SECRET',
            'tiktok': 'YOUR_TIKTOK_WEBHOOK_SECRET',
            'youtube': 'YOUR_YOUTUBE_WEBHOOK_SECRET',
            'twitter': 'YOUR_TWITTER_WEBHOOK_SECRET'
        }
        
        # Supported webhook events
        self.supported_events = {
            'facebook': [
                'feed',  # New posts, comments, likes
                'page_messaging',  # Messages
                'page_changes',  # Page updates
                'instagram'  # Instagram business account updates
            ],
            'instagram': [
                'story_insights',
                'mentions',
                'comments'
            ],
            'tiktok': [
                'video.publish',
                'video.delete',
                'user.data.update'
            ],
            'youtube': [
                'channelSection',
                'comment',
                'commentThread',
                'video'
            ],
            'twitter': [
                'tweet_create_events',
                'favorite_events',
                'follow_events',
                'direct_message_events'
            ]
        }
        
        # Analytics collection intervals
        self.collection_intervals = {
            'realtime': 300,    # 5 minutes
            'hourly': 3600,     # 1 hour
            'daily': 86400,     # 24 hours
            'weekly': 604800    # 7 days
        }
    
    def verify_facebook_signature(self, payload: str, signature: str) -> bool:
        """Verify Facebook webhook signature"""
        try:
            expected_signature = hmac.new(
                self.webhook_secrets['facebook'].encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Facebook sends signature as 'sha256=<signature>'
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Facebook signature: {str(e)}")
            return False
    
    def verify_tiktok_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """Verify TikTok webhook signature"""
        try:
            # TikTok signature verification
            message = f"{timestamp}{payload}"
            expected_signature = hmac.new(
                self.webhook_secrets['tiktok'].encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying TikTok signature: {str(e)}")
            return False
    
    def verify_youtube_signature(self, payload: str, signature: str) -> bool:
        """Verify YouTube webhook signature"""
        try:
            expected_signature = hmac.new(
                self.webhook_secrets['youtube'].encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying YouTube signature: {str(e)}")
            return False
    
    def process_facebook_webhook(self, headers: Dict, body: str) -> Dict:
        """Process Facebook webhook"""
        try:
            # Verify signature
            signature = headers.get('X-Hub-Signature-256', '')
            if not self.verify_facebook_signature(body, signature):
                return {
                    'success': False,
                    'error': 'Invalid signature',
                    'status': 'signature_verification_failed'
                }
            
            webhook_data = json.loads(body)
            
            # Handle verification challenge
            if webhook_data.get('hub.mode') == 'subscribe':
                challenge = webhook_data.get('hub.challenge')
                verify_token = webhook_data.get('hub.verify_token')
                
                if verify_token == 'YOUR_VERIFY_TOKEN':
                    return {'success': True, 'challenge': challenge}
                else:
                    return {'success': False, 'error': 'Invalid verify token'}
            
            # Process webhook entries
            entries = webhook_data.get('entry', [])
            results = []
            
            for entry in entries:
                page_id = entry.get('id')
                changes = entry.get('changes', [])
                
                for change in changes:
                    field = change.get('field')
                    value = change.get('value', {})
                    
                    if field == 'feed':
                        result = self.handle_facebook_feed_update(page_id, value)
                        results.append(result)
                    elif field == 'instagram':
                        result = self.handle_instagram_update(page_id, value)
                        results.append(result)
            
            return {
                'success': True,
                'message': 'Facebook webhook processed',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing Facebook webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_facebook_feed_update(self, page_id: str, value: Dict) -> Dict:
        """Handle Facebook feed update"""
        try:
            post_id = value.get('post_id')
            verb = value.get('verb')  # add, edit, remove, hide, unhide
            
            if verb == 'add':
                # New post created
                return self.collect_facebook_post_analytics(page_id, post_id)
            elif verb in ['edit', 'remove']:
                # Post updated or removed
                return self.update_facebook_post_status(page_id, post_id, verb)
            
            return {'success': True, 'message': f'Facebook feed update processed: {verb}'}
            
        except Exception as e:
            logger.error(f"Error handling Facebook feed update: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_instagram_update(self, page_id: str, value: Dict) -> Dict:
        """Handle Instagram update"""
        try:
            media_id = value.get('media_id')
            
            if media_id:
                return self.collect_instagram_media_analytics(page_id, media_id)
            
            return {'success': True, 'message': 'Instagram update processed'}
            
        except Exception as e:
            logger.error(f"Error handling Instagram update: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_tiktok_webhook(self, headers: Dict, body: str) -> Dict:
        """Process TikTok webhook"""
        try:
            # Verify signature
            signature = headers.get('X-TikTok-Signature', '')
            timestamp = headers.get('X-TikTok-Timestamp', '')
            
            if not self.verify_tiktok_signature(body, signature, timestamp):
                return {
                    'success': False,
                    'error': 'Invalid signature',
                    'status': 'signature_verification_failed'
                }
            
            webhook_data = json.loads(body)
            event_type = webhook_data.get('event')
            
            if event_type == 'video.publish':
                return self.handle_tiktok_video_published(webhook_data)
            elif event_type == 'video.delete':
                return self.handle_tiktok_video_deleted(webhook_data)
            
            return {
                'success': True,
                'message': f'TikTok webhook processed: {event_type}'
            }
            
        except Exception as e:
            logger.error(f"Error processing TikTok webhook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_tiktok_video_published(self, webhook_data: Dict) -> Dict:
        """Handle TikTok video published event"""
        try:
            video_data = webhook_data.get('video', {})
            video_id = video_data.get('id')
            user_id = webhook_data.get('user_id')
            
            if video_id and user_id:
                # Start collecting analytics for this video
                return self.collect_tiktok_video_analytics(user_id, video_id)
            
            return {'success': True, 'message': 'TikTok video published processed'}
            
        except Exception as e:
            logger.error(f"Error handling TikTok video published: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_tiktok_video_deleted(self, webhook_data: Dict) -> Dict:
        """Handle TikTok video deleted event"""
        try:
            video_id = webhook_data.get('video', {}).get('id')
            
            if video_id:
                # Update content status in database
                content = Content.query.filter_by(
                    platform='tiktok',
                    platform_post_id=video_id
                ).first()
                
                if content:
                    content.status = 'deleted'
                    content.updated_at = datetime.utcnow()
                    
                    from src.models.base import db
                    db.session.commit()
            
            return {'success': True, 'message': 'TikTok video deletion processed'}
            
        except Exception as e:
            logger.error(f"Error handling TikTok video deleted: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_facebook_post_analytics(self, page_id: str, post_id: str) -> Dict:
        """Collect Facebook post analytics"""
        try:
            # Find user by page ID
            user = self.find_user_by_platform_id('facebook', page_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get access token
            access_token = oauth_token_manager.get_valid_token(user.id, 'facebook')
            if not access_token:
                return {'success': False, 'error': 'No valid access token'}
            
            # Collect post insights
            insights_url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
            params = {
                'metric': 'post_impressions,post_engaged_users,post_clicks,post_reactions_by_type_total',
                'access_token': access_token
            }
            
            response = requests.get(insights_url, params=params, timeout=30)
            
            if response.status_code == 200:
                insights_data = response.json()
                
                # Process and store analytics
                analytics = self.process_facebook_insights(insights_data)
                
                # Update content record
                content = Content.query.filter_by(
                    user_id=user.id,
                    platform='facebook',
                    platform_post_id=post_id
                ).first()
                
                if content:
                    content.analytics_data = json.dumps(analytics)
                    content.views = analytics.get('impressions', 0)
                    content.likes = analytics.get('reactions', 0)
                    content.comments = analytics.get('comments', 0)
                    content.shares = analytics.get('shares', 0)
                    content.updated_at = datetime.utcnow()
                    
                    from src.models.base import db
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Facebook analytics collected',
                    'analytics': analytics
                }
            else:
                return {'success': False, 'error': f'Facebook API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error collecting Facebook analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_instagram_media_analytics(self, page_id: str, media_id: str) -> Dict:
        """Collect Instagram media analytics"""
        try:
            # Find user by page ID
            user = self.find_user_by_platform_id('instagram', page_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get access token
            access_token = oauth_token_manager.get_valid_token(user.id, 'instagram')
            if not access_token:
                return {'success': False, 'error': 'No valid access token'}
            
            # Collect media insights
            insights_url = f"https://graph.facebook.com/v18.0/{media_id}/insights"
            params = {
                'metric': 'impressions,reach,likes,comments,saves,shares',
                'access_token': access_token
            }
            
            response = requests.get(insights_url, params=params, timeout=30)
            
            if response.status_code == 200:
                insights_data = response.json()
                
                # Process and store analytics
                analytics = self.process_instagram_insights(insights_data)
                
                # Update content record
                content = Content.query.filter_by(
                    user_id=user.id,
                    platform='instagram',
                    platform_post_id=media_id
                ).first()
                
                if content:
                    content.analytics_data = json.dumps(analytics)
                    content.views = analytics.get('impressions', 0)
                    content.likes = analytics.get('likes', 0)
                    content.comments = analytics.get('comments', 0)
                    content.shares = analytics.get('shares', 0)
                    content.saves = analytics.get('saves', 0)
                    content.updated_at = datetime.utcnow()
                    
                    from src.models.base import db
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Instagram analytics collected',
                    'analytics': analytics
                }
            else:
                return {'success': False, 'error': f'Instagram API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error collecting Instagram analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_tiktok_video_analytics(self, user_id: str, video_id: str) -> Dict:
        """Collect TikTok video analytics"""
        try:
            # Find user by TikTok user ID
            user = self.find_user_by_platform_id('tiktok', user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get access token
            access_token = oauth_token_manager.get_valid_token(user.id, 'tiktok')
            if not access_token:
                return {'success': False, 'error': 'No valid access token'}
            
            # Collect video analytics
            analytics_url = "https://open-api.tiktok.com/video/data/"
            headers = {'Authorization': f'Bearer {access_token}'}
            params = {
                'video_ids': [video_id],
                'fields': ['like_count', 'comment_count', 'share_count', 'view_count']
            }
            
            response = requests.post(analytics_url, headers=headers, json=params, timeout=30)
            
            if response.status_code == 200:
                analytics_data = response.json()
                
                # Process and store analytics
                video_data = analytics_data.get('data', {}).get('videos', [])
                if video_data:
                    video_stats = video_data[0]
                    analytics = {
                        'views': video_stats.get('view_count', 0),
                        'likes': video_stats.get('like_count', 0),
                        'comments': video_stats.get('comment_count', 0),
                        'shares': video_stats.get('share_count', 0)
                    }
                    
                    # Update content record
                    content = Content.query.filter_by(
                        user_id=user.id,
                        platform='tiktok',
                        platform_post_id=video_id
                    ).first()
                    
                    if content:
                        content.analytics_data = json.dumps(analytics)
                        content.views = analytics['views']
                        content.likes = analytics['likes']
                        content.comments = analytics['comments']
                        content.shares = analytics['shares']
                        content.updated_at = datetime.utcnow()
                        
                        from src.models.base import db
                        db.session.commit()
                    
                    return {
                        'success': True,
                        'message': 'TikTok analytics collected',
                        'analytics': analytics
                    }
            
            return {'success': False, 'error': f'TikTok API error: {response.status_code}'}
            
        except Exception as e:
            logger.error(f"Error collecting TikTok analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_facebook_insights(self, insights_data: Dict) -> Dict:
        """Process Facebook insights data"""
        try:
            analytics = {}
            
            for insight in insights_data.get('data', []):
                metric_name = insight.get('name')
                values = insight.get('values', [])
                
                if values:
                    latest_value = values[-1].get('value', 0)
                    
                    if metric_name == 'post_impressions':
                        analytics['impressions'] = latest_value
                    elif metric_name == 'post_engaged_users':
                        analytics['engaged_users'] = latest_value
                    elif metric_name == 'post_clicks':
                        analytics['clicks'] = latest_value
                    elif metric_name == 'post_reactions_by_type_total':
                        # Sum all reaction types
                        total_reactions = sum(latest_value.values()) if isinstance(latest_value, dict) else latest_value
                        analytics['reactions'] = total_reactions
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error processing Facebook insights: {str(e)}")
            return {}
    
    def process_instagram_insights(self, insights_data: Dict) -> Dict:
        """Process Instagram insights data"""
        try:
            analytics = {}
            
            for insight in insights_data.get('data', []):
                metric_name = insight.get('name')
                values = insight.get('values', [])
                
                if values:
                    latest_value = values[-1].get('value', 0)
                    analytics[metric_name] = latest_value
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error processing Instagram insights: {str(e)}")
            return {}
    
    def find_user_by_platform_id(self, platform: str, platform_id: str) -> Optional[User]:
        """Find user by platform ID"""
        try:
            from src.services.oauth_token_manager import OAuthToken
            
            token = OAuthToken.query.filter_by(
                platform=platform,
                platform_user_id=platform_id,
                is_active=True
            ).first()
            
            if token:
                return User.query.get(token.user_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by platform ID: {str(e)}")
            return None
    
    def schedule_analytics_collection(self, user_id: int, platform: str, content_id: int, interval: str = 'hourly') -> Dict:
        """Schedule periodic analytics collection"""
        try:
            # In a real implementation, this would use a task queue like Celery
            # For now, we'll simulate scheduling
            
            collection_time = datetime.utcnow() + timedelta(seconds=self.collection_intervals.get(interval, 3600))
            
            logger.info(f"Scheduled analytics collection for user {user_id}, platform {platform}, content {content_id} at {collection_time}")
            
            return {
                'success': True,
                'message': 'Analytics collection scheduled',
                'next_collection': collection_time.isoformat(),
                'interval': interval
            }
            
        except Exception as e:
            logger.error(f"Error scheduling analytics collection: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_all_user_analytics(self, user_id: int) -> Dict:
        """Collect analytics for all user's content across platforms"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get all user's content
            contents = Content.query.filter_by(user_id=user_id, status='published').all()
            
            results = []
            for content in contents:
                if content.platform == 'facebook' and content.platform_post_id:
                    result = self.collect_facebook_post_analytics(content.platform_page_id, content.platform_post_id)
                    results.append({'content_id': content.id, 'platform': 'facebook', 'result': result})
                
                elif content.platform == 'instagram' and content.platform_post_id:
                    result = self.collect_instagram_media_analytics(content.platform_page_id, content.platform_post_id)
                    results.append({'content_id': content.id, 'platform': 'instagram', 'result': result})
                
                elif content.platform == 'tiktok' and content.platform_post_id:
                    result = self.collect_tiktok_video_analytics(content.platform_user_id, content.platform_post_id)
                    results.append({'content_id': content.id, 'platform': 'tiktok', 'result': result})
            
            successful_collections = len([r for r in results if r['result'].get('success')])
            
            return {
                'success': True,
                'message': f'Analytics collection completed for {len(contents)} content items',
                'successful_collections': successful_collections,
                'total_content': len(contents),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error collecting all user analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global social media webhooks instance
social_media_webhooks = SocialMediaWebhooks()

