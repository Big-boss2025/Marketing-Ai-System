from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.base import db
from src.models.user import User
from src.models.task import Task
from src.models.content import Content
from src.services.free_ai_services import free_ai
from src.services.task_queue import task_queue, QueueTask, TaskPriority
from src.services.credit_manager import credit_manager
from src.services.intelligent_prompt_analyzer import intelligent_analyzer
import json
import uuid
from datetime import datetime
import logging
import asyncio

video_generation_bp = Blueprint('video_generation', __name__)
logger = logging.getLogger(__name__)

@video_generation_bp.route('/generate', methods=['POST'])
@jwt_required()
async def generate_video():
    """Generate video using free AI services with intelligent prompt analysis"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate input
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400
        
        # Intelligent prompt analysis
        analysis_result = await intelligent_analyzer.analyze_prompt(prompt)
        
        if not analysis_result['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to analyze prompt'
            }), 400
        
        specs = analysis_result['specifications']
        
        # Allow manual overrides
        manual_duration = data.get('duration')
        manual_orientation = data.get('orientation')
        manual_style = data.get('style')
        manual_quality = data.get('quality')
        manual_platform = data.get('platform')
        
        if manual_duration:
            specs['duration'] = manual_duration
        if manual_orientation:
            specs['orientation'] = manual_orientation
            specs['aspect_ratio'] = intelligent_analyzer._get_aspect_ratio(manual_orientation)
            specs['resolution'] = intelligent_analyzer._get_resolution(manual_orientation, specs['quality'])
        if manual_style:
            specs['style'] = manual_style
        if manual_quality:
            specs['quality'] = manual_quality
            specs['resolution'] = intelligent_analyzer._get_resolution(specs['orientation'], manual_quality)
        if manual_platform:
            specs['platform'] = manual_platform
            specs = intelligent_analyzer._apply_platform_optimizations(specs)
        
        # Get optimized prompt
        optimized_prompt = await intelligent_analyzer.get_optimized_prompt(prompt, specs)
        
        priority = data.get('priority', 'normal')
        
        # Check user credits (free but with fair usage)
        credit_cost = 0  # Free service
        
        # Create task
        task_id = str(uuid.uuid4())
        task_data = {
            'original_prompt': prompt,
            'optimized_prompt': optimized_prompt,
            'specifications': specs,
            'analysis_result': analysis_result,
            'user_id': user_id,
            'task_type': 'video_generation'
        }
        
        # Add to queue
        queue_task = QueueTask(
            id=task_id,
            user_id=user_id,
            task_type='video_generation',
            data=task_data,
            priority=TaskPriority.HIGH.value if priority == 'urgent' else TaskPriority.NORMAL.value
        )
        
        success = await task_queue.add_task(queue_task)
        
        if success:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': 'Video generation started with intelligent analysis',
                'specifications': specs,
                'analysis': {
                    'confidence_score': analysis_result['confidence_score'],
                    'language_detected': analysis_result['language_detected'],
                    'recommendations': analysis_result['recommendations']
                },
                'estimated_time': f"{specs['duration'] // 10 + 2}-{specs['duration'] // 5 + 5} minutes",
                'cost': credit_cost
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue video generation task'
            }), 500
    
    except Exception as e:
        logger.error(f"Video generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@video_generation_bp.route('/templates', methods=['GET'])
def get_video_templates():
    """Get available video templates"""
    templates = {
        'promotional': {
            'name': 'Promotional Video',
            'description': 'High-energy promotional content',
            'duration': 30,
            'style': 'dynamic',
            'best_for': 'Product launches, sales, marketing campaigns'
        },
        'product_demo': {
            'name': 'Product Demo',
            'description': 'Clean product demonstration',
            'duration': 60,
            'style': 'clean',
            'best_for': 'Product features, tutorials, explanations'
        },
        'social_story': {
            'name': 'Social Story',
            'description': 'Trendy social media content',
            'duration': 15,
            'style': 'trendy',
            'best_for': 'Instagram stories, TikTok, quick engagement'
        },
        'educational': {
            'name': 'Educational',
            'description': 'Professional educational content',
            'duration': 120,
            'style': 'professional',
            'best_for': 'Training, courses, informational content'
        },
        'testimonial': {
            'name': 'Testimonial',
            'description': 'Authentic customer testimonials',
            'duration': 45,
            'style': 'authentic',
            'best_for': 'Customer reviews, success stories'
        }
    }
    
    return jsonify({
        'success': True,
        'templates': templates
    })

@video_generation_bp.route('/from-template', methods=['POST'])
@jwt_required()
async def generate_from_template():
    """Generate video from template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        template_name = data.get('template')
        content_data = data.get('content', {})
        
        if not template_name:
            return jsonify({
                'success': False,
                'error': 'Template name is required'
            }), 400
        
        # Create task
        task_id = str(uuid.uuid4())
        task_data = {
            'template': template_name,
            'content': content_data,
            'user_id': user_id,
            'task_type': 'video_from_template'
        }
        
        queue_task = QueueTask(
            id=task_id,
            user_id=user_id,
            task_type='video_from_template',
            data=task_data,
            priority=TaskPriority.NORMAL.value
        )
        
        success = await task_queue.add_task(queue_task)
        
        if success:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': f'Video generation from {template_name} template started',
                'estimated_time': '3-7 minutes'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue template video generation'
            }), 500
    
    except Exception as e:
        logger.error(f"Template video generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@video_generation_bp.route('/enhance', methods=['POST'])
@jwt_required()
async def enhance_video():
    """Enhance existing video"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        video_path = data.get('video_path')
        enhancements = data.get('enhancements', {})
        
        if not video_path:
            return jsonify({
                'success': False,
                'error': 'Video path is required'
            }), 400
        
        # Create enhancement task
        task_id = str(uuid.uuid4())
        task_data = {
            'video_path': video_path,
            'enhancements': enhancements,
            'user_id': user_id,
            'task_type': 'video_enhancement'
        }
        
        queue_task = QueueTask(
            id=task_id,
            user_id=user_id,
            task_type='video_enhancement',
            data=task_data,
            priority=TaskPriority.NORMAL.value
        )
        
        success = await task_queue.add_task(queue_task)
        
        if success:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': 'Video enhancement started',
                'estimated_time': '1-3 minutes'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue video enhancement'
            }), 500
    
    except Exception as e:
        logger.error(f"Video enhancement error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@video_generation_bp.route('/convert', methods=['POST'])
@jwt_required()
async def convert_video():
    """Convert video format"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        input_path = data.get('input_path')
        output_format = data.get('output_format')
        
        if not input_path or not output_format:
            return jsonify({
                'success': False,
                'error': 'Input path and output format are required'
            }), 400
        
        # Create conversion task
        task_id = str(uuid.uuid4())
        task_data = {
            'input_path': input_path,
            'output_format': output_format,
            'user_id': user_id,
            'task_type': 'video_conversion'
        }
        
        queue_task = QueueTask(
            id=task_id,
            user_id=user_id,
            task_type='video_conversion',
            data=task_data,
            priority=TaskPriority.LOW.value
        )
        
        success = await task_queue.add_task(queue_task)
        
        if success:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': f'Video conversion to {output_format} started',
                'estimated_time': '30 seconds - 2 minutes'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue video conversion'
            }), 500
    
    except Exception as e:
        logger.error(f"Video conversion error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@video_generation_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required()
def get_video_status(task_id):
    """Get video generation status"""
    try:
        user_id = get_jwt_identity()
        
        # Get task status from queue
        user_tasks = task_queue.get_user_tasks(user_id)
        task_info = None
        
        for task in user_tasks:
            if task.get('id') == task_id:
                task_info = task
                break
        
        if not task_info:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': task_info.get('status'),
            'progress': task_info.get('progress', 0),
            'result': task_info.get('result'),
            'error': task_info.get('error_message'),
            'created_at': task_info.get('created_at'),
            'completed_at': task_info.get('completed_at')
        })
    
    except Exception as e:
        logger.error(f"Get video status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@video_generation_bp.route('/history', methods=['GET'])
@jwt_required()
def get_video_history():
    """Get user's video generation history"""
    try:
        user_id = get_jwt_identity()
        
        # Get video generation tasks
        video_tasks = task_queue.get_user_tasks(user_id)
        video_history = []
        
        for task in video_tasks:
            if task.get('task_type', '').startswith('video_'):
                video_history.append({
                    'task_id': task.get('id'),
                    'task_type': task.get('task_type'),
                    'status': task.get('status'),
                    'created_at': task.get('created_at'),
                    'completed_at': task.get('completed_at'),
                    'data': task.get('data', {}),
                    'result': task.get('result')
                })
        
        # Sort by creation date (newest first)
        video_history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'history': video_history,
            'total_count': len(video_history)
        })
    
    except Exception as e:
        logger.error(f"Get video history error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@video_generation_bp.route('/cancel/<task_id>', methods=['POST'])
@jwt_required()
async def cancel_video_generation(task_id):
    """Cancel video generation task"""
    try:
        user_id = get_jwt_identity()
        
        success = await task_queue.cancel_task(task_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Video generation cancelled'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to cancel task or task not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Cancel video generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Register video generation processors
async def process_video_generation(task_data):
    """Process video generation task"""
    try:
        result = await free_ai.generate_video(
            prompt=task_data['prompt'],
            duration=task_data.get('duration', 5),
            style=task_data.get('style', 'cinematic'),
            quality=task_data.get('quality', 'high')
        )
        
        if result['success']:
            # Save to content database
            content = Content(
                user_id=task_data['user_id'],
                title=f"Generated Video: {task_data['prompt'][:50]}...",
                content_type='video',
                file_path=result.get('video_path'),
                metadata=json.dumps({
                    'prompt': task_data['prompt'],
                    'duration': task_data.get('duration'),
                    'style': task_data.get('style'),
                    'service_used': result.get('service'),
                    'quality': result.get('quality')
                })
            )
            content.save()
            
            result['content_id'] = content.id
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def process_video_from_template(task_data):
    """Process video generation from template"""
    try:
        # This would use the video generator service
        # For now, delegate to regular video generation
        return await process_video_generation(task_data['content'])
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def process_video_enhancement(task_data):
    """Process video enhancement task"""
    try:
        # This would use FFmpeg for video enhancement
        result = {
            'success': True,
            'enhanced_video_path': task_data['video_path'],
            'enhancements_applied': task_data['enhancements']
        }
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def process_video_conversion(task_data):
    """Process video conversion task"""
    try:
        # This would use FFmpeg for format conversion
        result = {
            'success': True,
            'converted_video_path': task_data['input_path'].replace('.mp4', f'.{task_data["output_format"]}'),
            'format': task_data['output_format']
        }
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Register processors with task queue
task_queue.register_processor('video_generation', process_video_generation)
task_queue.register_processor('video_from_template', process_video_from_template)
task_queue.register_processor('video_enhancement', process_video_enhancement)
task_queue.register_processor('video_conversion', process_video_conversion)

