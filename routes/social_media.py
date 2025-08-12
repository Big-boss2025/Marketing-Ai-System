from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from src.services.social_media_publisher import social_media_publisher
from src.services.free_ai_generator import free_ai_generator
from src.services.credit_manager import credit_manager
from src.models.user import User
from src.models.task import Task
from src.models.content import Content

logger = logging.getLogger(__name__)

social_media_bp = Blueprint('social_media', __name__, url_prefix='/api/social-media')

@social_media_bp.route('/platforms', methods=['GET'])
def get_platforms():
    """Get all available social media platforms and their status"""
    try:
        platform_status = social_media_publisher.get_platform_status()
        
        return jsonify({
            'success': True,
            'data': platform_status,
            'message': 'Platform status retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting platforms: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/publish', methods=['POST'])
def publish_content():
    """Publish content to selected social media platforms"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'content', 'platforms']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        content = data['content']
        platforms = data['platforms']
        platform_configs = data.get('platform_configs', {})
        
        # Check user credits
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Calculate credit cost (1 credit per platform)
        total_cost = len(platforms)
        
        if user.credits < total_cost:
            return jsonify({
                'success': False,
                'error': f'Insufficient credits. Required: {total_cost}, Available: {user.credits}'
            }), 400
        
        # Publish to platforms
        publish_result = social_media_publisher.publish_to_multiple_platforms(
            content, platforms, platform_configs
        )
        
        if publish_result['success']:
            # Deduct credits only for successful posts
            successful_posts = publish_result['successful_posts']
            credit_result = credit_manager.deduct_credits(
                user_id, successful_posts, 'social_media_publishing'
            )
            
            if not credit_result['success']:
                logger.warning(f"Failed to deduct credits: {credit_result['error']}")
        
        # Create task record
        task = Task(
            user_id=user_id,
            task_type='social_media_publishing',
            status='completed' if publish_result['success'] else 'failed',
            input_data={
                'platforms': platforms,
                'content_preview': content.get('text', '')[:100]
            },
            output_data=publish_result,
            credits_used=publish_result.get('successful_posts', 0)
        )
        task.save()
        
        # Save content records
        for platform, result in publish_result.get('results', {}).items():
            if result['success']:
                content_record = Content(
                    user_id=user_id,
                    task_id=task.id,
                    content_type='social_media_post',
                    platform=platform,
                    content_data={
                        'text': content.get('text', ''),
                        'hashtags': content.get('hashtags', []),
                        'image_url': content.get('image_url'),
                        'video_url': content.get('video_url')
                    },
                    post_id=result.get('post_id'),
                    status='published'
                )
                content_record.save()
        
        return jsonify({
            'success': True,
            'data': publish_result,
            'task_id': task.id,
            'credits_used': publish_result.get('successful_posts', 0),
            'message': f'Published to {publish_result["successful_posts"]}/{len(platforms)} platforms'
        })
        
    except Exception as e:
        logger.error(f"Error publishing content: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/schedule', methods=['POST'])
def schedule_content():
    """Schedule content for future publishing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'content', 'platforms', 'scheduled_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        content = data['content']
        platforms = data['platforms']
        scheduled_time_str = data['scheduled_time']
        platform_configs = data.get('platform_configs', {})
        
        # Parse scheduled time
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid scheduled_time format. Use ISO format.'
            }), 400
        
        # Check if scheduled time is in the future
        if scheduled_time <= datetime.now():
            return jsonify({
                'success': False,
                'error': 'Scheduled time must be in the future'
            }), 400
        
        # Check user credits
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Calculate credit cost
        total_cost = len(platforms)
        
        if user.credits < total_cost:
            return jsonify({
                'success': False,
                'error': f'Insufficient credits. Required: {total_cost}, Available: {user.credits}'
            }), 400
        
        # Schedule posts
        schedule_result = social_media_publisher.schedule_post(
            content, platforms, scheduled_time, platform_configs
        )
        
        if schedule_result['success']:
            # Reserve credits for scheduled posts
            scheduled_posts = schedule_result['scheduled_posts']
            credit_result = credit_manager.deduct_credits(
                user_id, scheduled_posts, 'scheduled_social_media_publishing'
            )
            
            if not credit_result['success']:
                logger.warning(f"Failed to reserve credits: {credit_result['error']}")
        
        # Create task record
        task = Task(
            user_id=user_id,
            task_type='scheduled_social_media_publishing',
            status='scheduled',
            input_data={
                'platforms': platforms,
                'scheduled_time': scheduled_time_str,
                'content_preview': content.get('text', '')[:100]
            },
            output_data=schedule_result,
            credits_used=schedule_result.get('scheduled_posts', 0),
            scheduled_time=scheduled_time
        )
        task.save()
        
        return jsonify({
            'success': True,
            'data': schedule_result,
            'task_id': task.id,
            'credits_reserved': schedule_result.get('scheduled_posts', 0),
            'message': f'Scheduled posts for {schedule_result["scheduled_posts"]} platforms'
        })
        
    except Exception as e:
        logger.error(f"Error scheduling content: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/generate-and-publish', methods=['POST'])
def generate_and_publish():
    """Generate content with AI and publish to social media platforms"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'product_service', 'platforms']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        product_service = data['product_service']
        platforms = data['platforms']
        strategy = data.get('strategy', 'social_media_marketing')
        language = data.get('language', 'ar')
        target_audience = data.get('target_audience', '')
        include_video = data.get('include_video', False)
        platform_configs = data.get('platform_configs', {})
        
        # Check user credits
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Calculate total credit cost (generation + publishing)
        generation_cost = 2  # 2 credits for AI generation
        publishing_cost = len(platforms)  # 1 credit per platform
        if include_video:
            generation_cost += 3  # Additional 3 credits for video
        
        total_cost = generation_cost + publishing_cost
        
        if user.credits < total_cost:
            return jsonify({
                'success': False,
                'error': f'Insufficient credits. Required: {total_cost}, Available: {user.credits}'
            }), 400
        
        # Generate content with AI
        task_data = {
            'strategy': strategy,
            'language': language,
            'product_service': product_service,
            'target_audience': target_audience,
            'include_video': include_video
        }
        
        generation_result = free_ai_generator.generate_marketing_content(task_data)
        
        if not generation_result['success']:
            return jsonify({
                'success': False,
                'error': f'Content generation failed: {generation_result["error"]}'
            }), 500
        
        generated_content = generation_result['content']
        
        # Publish to platforms
        publish_result = social_media_publisher.publish_to_multiple_platforms(
            generated_content, platforms, platform_configs
        )
        
        # Calculate actual credits used
        credits_used = generation_cost  # Always charge for generation
        if publish_result['success']:
            credits_used += publish_result['successful_posts']
        
        # Deduct credits
        credit_result = credit_manager.deduct_credits(
            user_id, credits_used, 'ai_content_generation_and_publishing'
        )
        
        if not credit_result['success']:
            logger.warning(f"Failed to deduct credits: {credit_result['error']}")
        
        # Create task record
        task = Task(
            user_id=user_id,
            task_type='ai_content_generation_and_publishing',
            status='completed' if publish_result['success'] else 'partial',
            input_data={
                'product_service': product_service,
                'strategy': strategy,
                'language': language,
                'platforms': platforms,
                'include_video': include_video
            },
            output_data={
                'generated_content': generated_content,
                'publish_result': publish_result
            },
            credits_used=credits_used
        )
        task.save()
        
        # Save content records
        for platform, result in publish_result.get('results', {}).items():
            if result['success']:
                content_record = Content(
                    user_id=user_id,
                    task_id=task.id,
                    content_type='ai_generated_social_media_post',
                    platform=platform,
                    content_data=generated_content,
                    post_id=result.get('post_id'),
                    status='published'
                )
                content_record.save()
        
        return jsonify({
            'success': True,
            'data': {
                'generated_content': generated_content,
                'publish_result': publish_result,
                'task_id': task.id,
                'credits_used': credits_used
            },
            'message': f'Generated content and published to {publish_result["successful_posts"]}/{len(platforms)} platforms'
        })
        
    except Exception as e:
        logger.error(f"Error generating and publishing content: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/analytics/<platform>/<post_id>', methods=['GET'])
def get_post_analytics(platform, post_id):
    """Get analytics for a specific post"""
    try:
        analytics_result = social_media_publisher.get_posting_analytics(platform, post_id)
        
        return jsonify({
            'success': True,
            'data': analytics_result,
            'message': 'Analytics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting post analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/optimal-times/<platform>', methods=['GET'])
def get_optimal_posting_times(platform):
    """Get optimal posting times for a platform"""
    try:
        timezone = request.args.get('timezone', 'UTC')
        
        optimal_times = social_media_publisher.get_optimal_posting_times(platform, timezone)
        
        return jsonify({
            'success': True,
            'data': optimal_times,
            'message': 'Optimal posting times retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting optimal times: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/user-content/<int:user_id>', methods=['GET'])
def get_user_content(user_id):
    """Get all published content for a user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        platform = request.args.get('platform')
        
        query = Content.query.filter_by(user_id=user_id)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        content_records = query.order_by(Content.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        content_list = []
        for content in content_records.items:
            content_data = {
                'id': content.id,
                'platform': content.platform,
                'content_type': content.content_type,
                'content_data': content.content_data,
                'post_id': content.post_id,
                'status': content.status,
                'created_at': content.created_at.isoformat(),
                'updated_at': content.updated_at.isoformat()
            }
            content_list.append(content_data)
        
        return jsonify({
            'success': True,
            'data': {
                'content': content_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': content_records.total,
                    'pages': content_records.pages,
                    'has_next': content_records.has_next,
                    'has_prev': content_records.has_prev
                }
            },
            'message': 'User content retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting user content: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/validate-content', methods=['POST'])
def validate_content():
    """Validate content for specific platforms"""
    try:
        data = request.get_json()
        
        content = data.get('content', '')
        platforms = data.get('platforms', [])
        
        if not content or not platforms:
            return jsonify({
                'success': False,
                'error': 'Content and platforms are required'
            }), 400
        
        validation_results = {}
        
        for platform in platforms:
            validation = social_media_publisher.validate_content_for_platform(content, platform)
            validation_results[platform] = validation
        
        return jsonify({
            'success': True,
            'data': validation_results,
            'message': 'Content validation completed'
        })
        
    except Exception as e:
        logger.error(f"Error validating content: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_media_bp.route('/setup-check', methods=['GET'])
def check_setup():
    """Check if free AI models are properly set up"""
    try:
        setup_result = free_ai_generator.setup_free_models()
        
        return jsonify({
            'success': True,
            'data': setup_result,
            'message': 'Setup check completed'
        })
        
    except Exception as e:
        logger.error(f"Error checking setup: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

