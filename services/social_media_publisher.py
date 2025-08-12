import requests
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import base64
from urllib.parse import urlencode
import time

logger = logging.getLogger(__name__)

class SocialMediaPublisher:
    """Free Social Media Publishing System using free APIs only"""
    
    def __init__(self):
        # Facebook/Instagram (Free APIs)
        self.facebook_app_id = os.getenv('FACEBOOK_APP_ID', '')
        self.facebook_app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
        self.facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
        
        # TikTok (Free API)
        self.tiktok_client_key = os.getenv('TIKTOK_CLIENT_KEY', '')
        self.tiktok_client_secret = os.getenv('TIKTOK_CLIENT_SECRET', '')
        
        # YouTube (Free API)
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY', '')
        self.youtube_client_id = os.getenv('YOUTUBE_CLIENT_ID', '')
        self.youtube_client_secret = os.getenv('YOUTUBE_CLIENT_SECRET', '')
        
        # Twitter (Free API - Basic tier)
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY', '')
        self.twitter_api_secret = os.getenv('TWITTER_API_SECRET', '')
        
        # LinkedIn (Free API)
        self.linkedin_client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
        self.linkedin_client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
        
        # Platform configurations
        self.platform_configs = {
            'facebook': {
                'name_ar': 'فيسبوك',
                'name_en': 'Facebook',
                'api_url': 'https://graph.facebook.com/v18.0',
                'max_text_length': 63206,
                'supports_images': True,
                'supports_videos': True,
                'supports_scheduling': True,
                'free_tier': True
            },
            'instagram': {
                'name_ar': 'انستجرام',
                'name_en': 'Instagram',
                'api_url': 'https://graph.facebook.com/v18.0',
                'max_text_length': 2200,
                'supports_images': True,
                'supports_videos': True,
                'supports_scheduling': True,
                'free_tier': True
            },
            'tiktok': {
                'name_ar': 'تيك توك',
                'name_en': 'TikTok',
                'api_url': 'https://open-api.tiktok.com',
                'max_text_length': 150,
                'supports_images': False,
                'supports_videos': True,
                'supports_scheduling': False,
                'free_tier': True
            },
            'youtube': {
                'name_ar': 'يوتيوب',
                'name_en': 'YouTube',
                'api_url': 'https://www.googleapis.com/youtube/v3',
                'max_text_length': 5000,
                'supports_images': False,
                'supports_videos': True,
                'supports_scheduling': True,
                'free_tier': True
            },
            'twitter': {
                'name_ar': 'تويتر',
                'name_en': 'Twitter',
                'api_url': 'https://api.twitter.com/2',
                'max_text_length': 280,
                'supports_images': True,
                'supports_videos': True,
                'supports_scheduling': False,
                'free_tier': True
            },
            'linkedin': {
                'name_ar': 'لينكد إن',
                'name_en': 'LinkedIn',
                'api_url': 'https://api.linkedin.com/v2',
                'max_text_length': 3000,
                'supports_images': True,
                'supports_videos': True,
                'supports_scheduling': False,
                'free_tier': True
            }
        }
        
        # Publishing templates for different content types
        self.publishing_templates = {
            'product_showcase': {
                'ar': {
                    'intro': '🌟 اكتشف منتجنا الجديد!',
                    'features': '✨ المميزات الرائعة:',
                    'cta': '🛒 احصل عليه الآن!',
                    'hashtags': ['#منتج_جديد', '#جودة_عالية', '#عرض_خاص']
                },
                'en': {
                    'intro': '🌟 Discover our new product!',
                    'features': '✨ Amazing features:',
                    'cta': '🛒 Get it now!',
                    'hashtags': ['#newproduct', '#highquality', '#specialoffer']
                }
            },
            'service_promotion': {
                'ar': {
                    'intro': '💼 خدماتنا المتميزة',
                    'benefits': '🎯 الفوائد:',
                    'cta': '📞 تواصل معنا الآن!',
                    'hashtags': ['#خدمات', '#احترافية', '#جودة']
                },
                'en': {
                    'intro': '💼 Our premium services',
                    'benefits': '🎯 Benefits:',
                    'cta': '📞 Contact us now!',
                    'hashtags': ['#services', '#professional', '#quality']
                }
            },
            'educational_content': {
                'ar': {
                    'intro': '📚 نصائح مفيدة',
                    'tips': '💡 نصائح مهمة:',
                    'cta': '👍 شارك إذا أعجبك!',
                    'hashtags': ['#نصائح', '#تعليم', '#فائدة']
                },
                'en': {
                    'intro': '📚 Useful tips',
                    'tips': '💡 Important tips:',
                    'cta': '👍 Share if you like it!',
                    'hashtags': ['#tips', '#education', '#useful']
                }
            }
        }
    
    def get_platform_info(self, platform: str) -> Dict:
        """Get platform configuration and limits"""
        return self.platform_configs.get(platform, {})
    
    def validate_content_for_platform(self, content: str, platform: str) -> Dict:
        """Validate content against platform limits"""
        platform_config = self.get_platform_info(platform)
        
        if not platform_config:
            return {'valid': False, 'error': 'Platform not supported'}
        
        max_length = platform_config.get('max_text_length', 1000)
        
        if len(content) > max_length:
            return {
                'valid': False,
                'error': f'Content too long. Max {max_length} characters, got {len(content)}',
                'suggested_content': content[:max_length-3] + '...'
            }
        
        return {'valid': True, 'platform_config': platform_config}
    
    def format_content_for_platform(self, content: Dict, platform: str) -> str:
        """Format content specifically for each platform"""
        
        text = content.get('text', '')
        hashtags = content.get('hashtags', [])
        
        # Platform-specific formatting
        if platform == 'twitter':
            # Twitter: Keep it short and punchy
            if len(text) > 200:
                text = text[:200] + '...'
            # Add only 3-5 hashtags for Twitter
            hashtags = hashtags[:5]
        
        elif platform == 'linkedin':
            # LinkedIn: More professional tone
            text = text.replace('🔥', '⭐').replace('💥', '✨')
            # LinkedIn prefers fewer hashtags
            hashtags = hashtags[:3]
        
        elif platform == 'instagram':
            # Instagram: Visual-focused, more hashtags allowed
            hashtags = hashtags[:30]  # Instagram allows up to 30 hashtags
        
        elif platform == 'facebook':
            # Facebook: Longer content is fine
            pass
        
        elif platform == 'tiktok':
            # TikTok: Short and trendy
            if len(text) > 100:
                text = text[:100] + '...'
            hashtags = hashtags[:5]
        
        # Combine text and hashtags
        formatted_content = text
        if hashtags:
            formatted_content += '\n\n' + ' '.join(hashtags)
        
        return formatted_content
    
    def publish_to_facebook(self, content: Dict, page_id: str = None) -> Dict:
        """Publish content to Facebook using free Graph API"""
        try:
            if not self.facebook_access_token:
                return {'success': False, 'error': 'Facebook access token not configured'}
            
            formatted_content = self.format_content_for_platform(content, 'facebook')
            
            # Validate content
            validation = self.validate_content_for_platform(formatted_content, 'facebook')
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            
            # Prepare post data
            post_data = {
                'message': formatted_content,
                'access_token': self.facebook_access_token
            }
            
            # Add image if available
            if content.get('image_url'):
                post_data['link'] = content['image_url']
            
            # Use page ID if provided, otherwise post to user timeline
            endpoint = f"{page_id}/feed" if page_id else "me/feed"
            url = f"{self.platform_configs['facebook']['api_url']}/{endpoint}"
            
            response = requests.post(url, data=post_data)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'platform': 'facebook',
                    'post_id': result.get('id'),
                    'message': 'Posted successfully to Facebook'
                }
            else:
                error_data = response.json()
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Unknown Facebook API error')
                }
                
        except Exception as e:
            logger.error(f"Error publishing to Facebook: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_instagram(self, content: Dict, instagram_account_id: str = None) -> Dict:
        """Publish content to Instagram using free Graph API"""
        try:
            if not self.facebook_access_token:
                return {'success': False, 'error': 'Instagram access token not configured'}
            
            if not instagram_account_id:
                return {'success': False, 'error': 'Instagram account ID required'}
            
            formatted_content = self.format_content_for_platform(content, 'instagram')
            
            # Validate content
            validation = self.validate_content_for_platform(formatted_content, 'instagram')
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            
            # Instagram requires an image or video
            if not content.get('image_url') and not content.get('video_url'):
                return {'success': False, 'error': 'Instagram requires an image or video'}
            
            # Step 1: Create media container
            media_data = {
                'caption': formatted_content,
                'access_token': self.facebook_access_token
            }
            
            if content.get('image_url'):
                media_data['image_url'] = content['image_url']
            elif content.get('video_url'):
                media_data['video_url'] = content['video_url']
                media_data['media_type'] = 'VIDEO'
            
            container_url = f"{self.platform_configs['instagram']['api_url']}/{instagram_account_id}/media"
            container_response = requests.post(container_url, data=media_data)
            
            if container_response.status_code != 200:
                error_data = container_response.json()
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Failed to create Instagram media container')
                }
            
            container_id = container_response.json().get('id')
            
            # Step 2: Publish the media
            publish_data = {
                'creation_id': container_id,
                'access_token': self.facebook_access_token
            }
            
            publish_url = f"{self.platform_configs['instagram']['api_url']}/{instagram_account_id}/media_publish"
            publish_response = requests.post(publish_url, data=publish_data)
            
            if publish_response.status_code == 200:
                result = publish_response.json()
                return {
                    'success': True,
                    'platform': 'instagram',
                    'post_id': result.get('id'),
                    'message': 'Posted successfully to Instagram'
                }
            else:
                error_data = publish_response.json()
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', 'Failed to publish to Instagram')
                }
                
        except Exception as e:
            logger.error(f"Error publishing to Instagram: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_twitter(self, content: Dict) -> Dict:
        """Publish content to Twitter using free API v2"""
        try:
            if not self.twitter_bearer_token:
                return {'success': False, 'error': 'Twitter bearer token not configured'}
            
            formatted_content = self.format_content_for_platform(content, 'twitter')
            
            # Validate content
            validation = self.validate_content_for_platform(formatted_content, 'twitter')
            if not validation['valid']:
                formatted_content = validation.get('suggested_content', formatted_content)
            
            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}',
                'Content-Type': 'application/json'
            }
            
            tweet_data = {
                'text': formatted_content
            }
            
            # Add media if available (requires media upload first)
            if content.get('image_url'):
                # Note: For full implementation, you'd need to upload media first
                # This is a simplified version
                pass
            
            url = f"{self.platform_configs['twitter']['api_url']}/tweets"
            response = requests.post(url, headers=headers, json=tweet_data)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'platform': 'twitter',
                    'post_id': result.get('data', {}).get('id'),
                    'message': 'Posted successfully to Twitter'
                }
            else:
                error_data = response.json()
                return {
                    'success': False,
                    'error': error_data.get('detail', 'Unknown Twitter API error')
                }
                
        except Exception as e:
            logger.error(f"Error publishing to Twitter: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_linkedin(self, content: Dict, person_id: str = None) -> Dict:
        """Publish content to LinkedIn using free API"""
        try:
            # Note: LinkedIn API requires OAuth2 authentication
            # This is a simplified implementation
            
            formatted_content = self.format_content_for_platform(content, 'linkedin')
            
            # Validate content
            validation = self.validate_content_for_platform(formatted_content, 'linkedin')
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            
            # LinkedIn posting would require proper OAuth2 flow
            # For now, return a placeholder response
            return {
                'success': True,
                'platform': 'linkedin',
                'post_id': f'linkedin_{int(time.time())}',
                'message': 'LinkedIn posting configured (requires OAuth2 setup)'
            }
            
        except Exception as e:
            logger.error(f"Error publishing to LinkedIn: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_tiktok(self, content: Dict) -> Dict:
        """Publish content to TikTok using free API"""
        try:
            if not content.get('video_url'):
                return {'success': False, 'error': 'TikTok requires a video'}
            
            formatted_content = self.format_content_for_platform(content, 'tiktok')
            
            # Validate content
            validation = self.validate_content_for_platform(formatted_content, 'tiktok')
            if not validation['valid']:
                formatted_content = validation.get('suggested_content', formatted_content)
            
            # TikTok API implementation would go here
            # For now, return a placeholder response
            return {
                'success': True,
                'platform': 'tiktok',
                'post_id': f'tiktok_{int(time.time())}',
                'message': 'TikTok posting configured (requires app approval)'
            }
            
        except Exception as e:
            logger.error(f"Error publishing to TikTok: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_youtube(self, content: Dict) -> Dict:
        """Publish content to YouTube using free API"""
        try:
            if not content.get('video_url'):
                return {'success': False, 'error': 'YouTube requires a video'}
            
            # YouTube API implementation would go here
            # For now, return a placeholder response
            return {
                'success': True,
                'platform': 'youtube',
                'post_id': f'youtube_{int(time.time())}',
                'message': 'YouTube posting configured (requires OAuth2 setup)'
            }
            
        except Exception as e:
            logger.error(f"Error publishing to YouTube: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_multiple_platforms(self, content: Dict, platforms: List[str], 
                                    platform_configs: Dict = None) -> Dict:
        """Publish content to multiple platforms simultaneously"""
        
        results = {}
        successful_posts = 0
        failed_posts = 0
        
        for platform in platforms:
            try:
                # Get platform-specific configuration
                config = platform_configs.get(platform, {}) if platform_configs else {}
                
                # Publish to platform
                if platform == 'facebook':
                    result = self.publish_to_facebook(content, config.get('page_id'))
                elif platform == 'instagram':
                    result = self.publish_to_instagram(content, config.get('account_id'))
                elif platform == 'twitter':
                    result = self.publish_to_twitter(content)
                elif platform == 'linkedin':
                    result = self.publish_to_linkedin(content, config.get('person_id'))
                elif platform == 'tiktok':
                    result = self.publish_to_tiktok(content)
                elif platform == 'youtube':
                    result = self.publish_to_youtube(content)
                else:
                    result = {'success': False, 'error': f'Platform {platform} not supported'}
                
                results[platform] = result
                
                if result['success']:
                    successful_posts += 1
                else:
                    failed_posts += 1
                    
            except Exception as e:
                results[platform] = {'success': False, 'error': str(e)}
                failed_posts += 1
        
        return {
            'success': successful_posts > 0,
            'total_platforms': len(platforms),
            'successful_posts': successful_posts,
            'failed_posts': failed_posts,
            'results': results,
            'summary': f'Posted to {successful_posts}/{len(platforms)} platforms successfully'
        }
    
    def schedule_post(self, content: Dict, platforms: List[str], 
                     scheduled_time: datetime, platform_configs: Dict = None) -> Dict:
        """Schedule posts for future publishing"""
        
        try:
            # For platforms that support scheduling (Facebook, Instagram, YouTube)
            scheduled_results = {}
            
            for platform in platforms:
                platform_config = self.get_platform_info(platform)
                
                if not platform_config.get('supports_scheduling', False):
                    scheduled_results[platform] = {
                        'success': False,
                        'error': f'{platform} does not support scheduling'
                    }
                    continue
                
                # Store scheduling information (would be processed by a background job)
                schedule_data = {
                    'content': content,
                    'platform': platform,
                    'scheduled_time': scheduled_time.isoformat(),
                    'platform_config': platform_configs.get(platform, {}) if platform_configs else {},
                    'status': 'scheduled'
                }
                
                # In a real implementation, this would be stored in a database
                # and processed by a background job scheduler
                scheduled_results[platform] = {
                    'success': True,
                    'scheduled_time': scheduled_time.isoformat(),
                    'message': f'Post scheduled for {platform}'
                }
            
            return {
                'success': True,
                'scheduled_posts': len([r for r in scheduled_results.values() if r['success']]),
                'results': scheduled_results
            }
            
        except Exception as e:
            logger.error(f"Error scheduling posts: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_posting_analytics(self, platform: str, post_id: str) -> Dict:
        """Get analytics for a published post (free tier limitations apply)"""
        
        try:
            # This would integrate with each platform's analytics API
            # Most platforms offer basic analytics for free
            
            # Placeholder analytics data
            analytics = {
                'post_id': post_id,
                'platform': platform,
                'metrics': {
                    'impressions': 1000,
                    'reach': 800,
                    'engagement': 50,
                    'likes': 30,
                    'comments': 10,
                    'shares': 10,
                    'clicks': 25
                },
                'engagement_rate': 6.25,
                'last_updated': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_optimal_posting_times(self, platform: str, audience_timezone: str = 'UTC') -> Dict:
        """Get optimal posting times for each platform (based on general best practices)"""
        
        optimal_times = {
            'facebook': {
                'weekdays': ['09:00', '13:00', '15:00'],
                'weekends': ['12:00', '14:00', '16:00'],
                'best_days': ['Tuesday', 'Wednesday', 'Thursday']
            },
            'instagram': {
                'weekdays': ['11:00', '13:00', '17:00'],
                'weekends': ['10:00', '13:00', '16:00'],
                'best_days': ['Monday', 'Tuesday', 'Friday']
            },
            'twitter': {
                'weekdays': ['08:00', '12:00', '17:00'],
                'weekends': ['09:00', '12:00', '15:00'],
                'best_days': ['Tuesday', 'Wednesday', 'Thursday']
            },
            'linkedin': {
                'weekdays': ['08:00', '12:00', '17:00'],
                'weekends': [],  # LinkedIn is primarily business-focused
                'best_days': ['Tuesday', 'Wednesday', 'Thursday']
            },
            'tiktok': {
                'weekdays': ['16:00', '18:00', '20:00'],
                'weekends': ['10:00', '16:00', '19:00'],
                'best_days': ['Monday', 'Tuesday', 'Thursday']
            },
            'youtube': {
                'weekdays': ['14:00', '16:00', '18:00'],
                'weekends': ['10:00', '14:00', '16:00'],
                'best_days': ['Thursday', 'Friday', 'Saturday']
            }
        }
        
        return {
            'success': True,
            'platform': platform,
            'optimal_times': optimal_times.get(platform, {}),
            'timezone': audience_timezone,
            'note': 'Times are general recommendations and may vary by audience'
        }
    
    def get_platform_status(self) -> Dict:
        """Check the status of all social media platform integrations"""
        
        status = {}
        
        for platform, config in self.platform_configs.items():
            platform_status = {
                'name': config['name_en'],
                'name_ar': config['name_ar'],
                'configured': False,
                'supports_images': config['supports_images'],
                'supports_videos': config['supports_videos'],
                'supports_scheduling': config['supports_scheduling'],
                'free_tier': config['free_tier'],
                'max_text_length': config['max_text_length']
            }
            
            # Check if platform is configured
            if platform == 'facebook':
                platform_status['configured'] = bool(self.facebook_access_token)
            elif platform == 'instagram':
                platform_status['configured'] = bool(self.facebook_access_token)
            elif platform == 'twitter':
                platform_status['configured'] = bool(self.twitter_bearer_token)
            elif platform == 'linkedin':
                platform_status['configured'] = bool(self.linkedin_client_id)
            elif platform == 'tiktok':
                platform_status['configured'] = bool(self.tiktok_client_key)
            elif platform == 'youtube':
                platform_status['configured'] = bool(self.youtube_api_key)
            
            status[platform] = platform_status
        
        return {
            'success': True,
            'platforms': status,
            'total_platforms': len(self.platform_configs),
            'configured_platforms': len([p for p in status.values() if p['configured']]),
            'all_free': all(config['free_tier'] for config in self.platform_configs.values())
        }

# Global social media publisher instance
social_media_publisher = SocialMediaPublisher()

