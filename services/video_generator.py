import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio
import aiohttp
from src.models.base import db
from src.models.task import Task
from src.models.content import Content

logger = logging.getLogger(__name__)

class VideoGeneratorService:
    """Professional video generation service using free APIs and tools"""
    
    def __init__(self):
        self.supported_formats = ['mp4', 'webm', 'avi', 'mov']
        self.supported_resolutions = {
            'sd': (640, 480),
            'hd': (1280, 720),
            'fhd': (1920, 1080),
            '4k': (3840, 2160),
            'square': (1080, 1080),
            'vertical': (1080, 1920),
            'story': (1080, 1920)
        }
        
        # Free video generation APIs
        self.apis = {
            'runway_ml': {
                'url': 'https://api.runwayml.com/v1/generate',
                'key': os.getenv('RUNWAY_API_KEY', ''),
                'free_tier': True
            },
            'stable_video': {
                'url': 'https://api.stability.ai/v2alpha/generation/video',
                'key': os.getenv('STABILITY_API_KEY', ''),
                'free_tier': True
            },
            'pika_labs': {
                'url': 'https://api.pika.art/v1/generate',
                'key': os.getenv('PIKA_API_KEY', ''),
                'free_tier': True
            },
            'local_ffmpeg': {
                'enabled': True,
                'path': '/usr/bin/ffmpeg'
            }
        }
        
        self.video_templates = {
            'promotional': {
                'duration': 30,
                'style': 'dynamic',
                'music': 'upbeat',
                'transitions': 'fast'
            },
            'product_demo': {
                'duration': 60,
                'style': 'clean',
                'music': 'corporate',
                'transitions': 'smooth'
            },
            'social_story': {
                'duration': 15,
                'style': 'trendy',
                'music': 'viral',
                'transitions': 'quick'
            },
            'educational': {
                'duration': 120,
                'style': 'professional',
                'music': 'ambient',
                'transitions': 'slow'
            },
            'testimonial': {
                'duration': 45,
                'style': 'authentic',
                'music': 'emotional',
                'transitions': 'natural'
            }
        }
    
    async def generate_video(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video based on task requirements"""
        try:
            video_type = task_data.get('video_type', 'promotional')
            prompt = task_data.get('prompt', '')
            duration = task_data.get('duration', 30)
            resolution = task_data.get('resolution', 'hd')
            style = task_data.get('style', 'dynamic')
            
            # Choose best available API
            api_result = await self._try_apis(task_data)
            
            if api_result['success']:
                return api_result
            
            # Fallback to local generation
            return await self._generate_local_video(task_data)
            
        except Exception as e:
            logger.error(f"Video generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _try_apis(self, task_data: Dict) -> Dict[str, Any]:
        """Try different APIs for video generation"""
        
        # Try Runway ML first
        if self.apis['runway_ml']['key']:
            result = await self._generate_runway_video(task_data)
            if result['success']:
                return result
        
        # Try Stability AI
        if self.apis['stable_video']['key']:
            result = await self._generate_stability_video(task_data)
            if result['success']:
                return result
        
        # Try Pika Labs
        if self.apis['pika_labs']['key']:
            result = await self._generate_pika_video(task_data)
            if result['success']:
                return result
        
        return {'success': False, 'error': 'No API keys available'}
    
    async def _generate_runway_video(self, task_data: Dict) -> Dict[str, Any]:
        """Generate video using Runway ML API"""
        try:
            headers = {
                'Authorization': f"Bearer {self.apis['runway_ml']['key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'prompt': task_data.get('prompt', ''),
                'duration': task_data.get('duration', 30),
                'resolution': task_data.get('resolution', 'hd'),
                'style': task_data.get('style', 'cinematic'),
                'seed': task_data.get('seed', -1)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.apis['runway_ml']['url'],
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'video_url': result.get('video_url'),
                            'task_id': result.get('task_id'),
                            'api_used': 'runway_ml'
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"Runway API error: {error_text}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Runway API exception: {str(e)}"
            }
    
    async def _generate_stability_video(self, task_data: Dict) -> Dict[str, Any]:
        """Generate video using Stability AI API"""
        try:
            headers = {
                'Authorization': f"Bearer {self.apis['stable_video']['key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text_prompts': [
                    {
                        'text': task_data.get('prompt', ''),
                        'weight': 1.0
                    }
                ],
                'cfg_scale': task_data.get('cfg_scale', 7),
                'motion_bucket_id': task_data.get('motion_bucket_id', 127),
                'seed': task_data.get('seed', 0)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.apis['stable_video']['url'],
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'video_url': result.get('artifacts', [{}])[0].get('url'),
                            'task_id': result.get('id'),
                            'api_used': 'stability_ai'
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"Stability API error: {error_text}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Stability API exception: {str(e)}"
            }
    
    async def _generate_pika_video(self, task_data: Dict) -> Dict[str, Any]:
        """Generate video using Pika Labs API"""
        try:
            headers = {
                'Authorization': f"Bearer {self.apis['pika_labs']['key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'prompt': task_data.get('prompt', ''),
                'aspect_ratio': task_data.get('aspect_ratio', '16:9'),
                'duration': task_data.get('duration', 3),
                'fps': task_data.get('fps', 24),
                'guidance_scale': task_data.get('guidance_scale', 12)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.apis['pika_labs']['url'],
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'video_url': result.get('video_url'),
                            'task_id': result.get('task_id'),
                            'api_used': 'pika_labs'
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"Pika API error: {error_text}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Pika API exception: {str(e)}"
            }
    
    async def _generate_local_video(self, task_data: Dict) -> Dict[str, Any]:
        """Generate video using local tools (FFmpeg + AI)"""
        try:
            # Create video from images and text
            video_id = str(uuid.uuid4())
            output_path = f"/tmp/video_{video_id}.mp4"
            
            # Generate images for video frames
            images = await self._generate_video_frames(task_data)
            
            if not images:
                return {
                    'success': False,
                    'error': 'Failed to generate video frames'
                }
            
            # Create video from images using FFmpeg
            success = await self._create_video_from_images(images, output_path, task_data)
            
            if success:
                return {
                    'success': True,
                    'video_path': output_path,
                    'video_id': video_id,
                    'api_used': 'local_ffmpeg'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create video from images'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Local video generation error: {str(e)}"
            }
    
    async def _generate_video_frames(self, task_data: Dict) -> List[str]:
        """Generate images for video frames"""
        try:
            prompt = task_data.get('prompt', '')
            frame_count = task_data.get('frame_count', 30)
            
            frames = []
            
            # Generate keyframes with slight variations
            for i in range(frame_count):
                frame_prompt = f"{prompt}, frame {i+1}, slight motion, cinematic"
                
                # Use Stable Diffusion or similar for frame generation
                frame_result = await self._generate_frame_image(frame_prompt, i)
                
                if frame_result['success']:
                    frames.append(frame_result['image_path'])
            
            return frames
        
        except Exception as e:
            logger.error(f"Frame generation error: {str(e)}")
            return []
    
    async def _generate_frame_image(self, prompt: str, frame_index: int) -> Dict[str, Any]:
        """Generate single frame image"""
        try:
            # Use OpenAI DALL-E or local Stable Diffusion
            import openai
            
            response = await openai.Image.acreate(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            image_url = response['data'][0]['url']
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        image_path = f"/tmp/frame_{frame_index}.png"
                        with open(image_path, 'wb') as f:
                            f.write(await resp.read())
                        
                        return {
                            'success': True,
                            'image_path': image_path
                        }
            
            return {'success': False, 'error': 'Failed to download image'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _create_video_from_images(self, images: List[str], output_path: str, task_data: Dict) -> bool:
        """Create video from image sequence using FFmpeg"""
        try:
            import subprocess
            
            duration = task_data.get('duration', 30)
            fps = len(images) / duration if duration > 0 else 1
            
            # Create input file list
            input_list_path = "/tmp/input_list.txt"
            with open(input_list_path, 'w') as f:
                for image in images:
                    f.write(f"file '{image}'\n")
                    f.write(f"duration {1/fps}\n")
            
            # FFmpeg command
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', input_list_path,
                '-vf', f'fps={fps},scale=1920:1080',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-y',
                output_path
            ]
            
            # Add audio if specified
            if task_data.get('add_music'):
                music_path = await self._get_background_music(task_data.get('music_style', 'upbeat'))
                if music_path:
                    cmd.extend(['-i', music_path, '-c:a', 'aac', '-shortest'])
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True
            else:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Video creation error: {str(e)}")
            return False
    
    async def _get_background_music(self, style: str) -> Optional[str]:
        """Get background music for video"""
        try:
            # Use free music APIs or local music library
            music_apis = {
                'freesound': 'https://freesound.org/apiv2/search/text/',
                'zapsplat': 'https://api.zapsplat.com/v1/search',
                'pixabay': 'https://pixabay.com/api/music/'
            }
            
            # For now, return None (no music)
            # In production, implement music search and download
            return None
        
        except Exception as e:
            logger.error(f"Music retrieval error: {str(e)}")
            return None
    
    def create_video_from_template(self, template_name: str, content_data: Dict) -> Dict[str, Any]:
        """Create video using predefined templates"""
        try:
            if template_name not in self.video_templates:
                return {
                    'success': False,
                    'error': f'Template {template_name} not found'
                }
            
            template = self.video_templates[template_name]
            
            # Merge template settings with content data
            video_config = {
                **template,
                **content_data,
                'template_used': template_name
            }
            
            # Generate video based on template
            return asyncio.run(self.generate_video(video_config))
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_video_templates(self) -> Dict[str, Any]:
        """Get available video templates"""
        return {
            'templates': self.video_templates,
            'supported_formats': self.supported_formats,
            'supported_resolutions': self.supported_resolutions
        }
    
    async def enhance_video(self, video_path: str, enhancements: Dict) -> Dict[str, Any]:
        """Enhance existing video with effects"""
        try:
            output_path = f"/tmp/enhanced_{uuid.uuid4()}.mp4"
            
            cmd = ['ffmpeg', '-i', video_path]
            
            # Add filters based on enhancements
            filters = []
            
            if enhancements.get('brightness'):
                filters.append(f"eq=brightness={enhancements['brightness']}")
            
            if enhancements.get('contrast'):
                filters.append(f"eq=contrast={enhancements['contrast']}")
            
            if enhancements.get('saturation'):
                filters.append(f"eq=saturation={enhancements['saturation']}")
            
            if enhancements.get('stabilize'):
                filters.append("vidstabdetect=stepsize=6:shakiness=8:accuracy=9")
            
            if enhancements.get('denoise'):
                filters.append("hqdn3d")
            
            if filters:
                cmd.extend(['-vf', ','.join(filters)])
            
            cmd.extend(['-c:v', 'libx264', '-y', output_path])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'enhanced_video_path': output_path
                }
            else:
                return {
                    'success': False,
                    'error': f"Enhancement failed: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def convert_video_format(self, input_path: str, output_format: str) -> Dict[str, Any]:
        """Convert video to different format"""
        try:
            if output_format not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Format {output_format} not supported'
                }
            
            output_path = f"/tmp/converted_{uuid.uuid4()}.{output_format}"
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'converted_video_path': output_path,
                    'format': output_format
                }
            else:
                return {
                    'success': False,
                    'error': f"Conversion failed: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global video generator instance
video_generator = VideoGeneratorService()

