import os
import json
import requests
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import subprocess
import tempfile
import base64

logger = logging.getLogger(__name__)

class FreeAIServices:
    """Comprehensive free AI services with high performance"""
    
    def __init__(self):
        # Free text generation APIs
        self.text_apis = {
            'huggingface': {
                'url': 'https://api-inference.huggingface.co/models/',
                'models': {
                    'gpt2': 'gpt2',
                    'bloom': 'bigscience/bloom-560m',
                    'flan_t5': 'google/flan-t5-large',
                    'arabic_gpt': 'aubmindlab/aragpt2-base'
                },
                'free': True
            },
            'ollama_local': {
                'url': 'http://localhost:11434/api/generate',
                'models': {
                    'llama2': 'llama2:7b',
                    'codellama': 'codellama:7b',
                    'mistral': 'mistral:7b',
                    'arabic_llama': 'arabic-llama2:7b'
                },
                'free': True
            },
            'groq': {
                'url': 'https://api.groq.com/openai/v1/chat/completions',
                'models': {
                    'mixtral': 'mixtral-8x7b-32768',
                    'llama2': 'llama2-70b-4096'
                },
                'free_tier': 'high_limit'
            }
        }
        
        # Free image generation APIs
        self.image_apis = {
            'stable_diffusion_local': {
                'url': 'http://localhost:7860/sdapi/v1/txt2img',
                'free': True,
                'high_quality': True
            },
            'pollinations': {
                'url': 'https://image.pollinations.ai/prompt/',
                'free': True,
                'unlimited': True
            },
            'craiyon': {
                'url': 'https://api.craiyon.com/v3',
                'free': True,
                'fast': True
            },
            'lexica': {
                'url': 'https://lexica.art/api/v1/search',
                'free': True,
                'search_based': True
            }
        }
        
        # Free video generation services
        self.video_apis = {
            'runway_free': {
                'url': 'https://api.runwayml.com/v1/generate',
                'free_tier': True,
                'quality': 'high'
            },
            'pika_free': {
                'url': 'https://api.pika.art/v1/generate',
                'free_tier': True,
                'quality': 'medium'
            },
            'local_ffmpeg': {
                'enabled': True,
                'unlimited': True,
                'quality': 'ultra_high'
            },
            'animatediff': {
                'local': True,
                'free': True,
                'quality': 'high'
            }
        }
        
        # Free audio/TTS services
        self.audio_apis = {
            'coqui_tts': {
                'local': True,
                'free': True,
                'quality': 'high',
                'multilingual': True
            },
            'espeak': {
                'local': True,
                'free': True,
                'fast': True
            },
            'festival': {
                'local': True,
                'free': True,
                'quality': 'medium'
            }
        }
        
        # Free translation services
        self.translation_apis = {
            'libre_translate': {
                'url': 'https://libretranslate.de/translate',
                'free': True,
                'unlimited': True
            },
            'mymemory': {
                'url': 'https://api.mymemory.translated.net/get',
                'free': True,
                'high_limit': True
            },
            'google_translate_free': {
                'url': 'https://translate.googleapis.com/translate_a/single',
                'free': True,
                'unlimited': True
            }
        }
    
    async def generate_text(self, prompt: str, language: str = 'en', 
                           style: str = 'creative', max_length: int = 500) -> Dict[str, Any]:
        """Generate text using free APIs with high quality"""
        try:
            # Try Ollama local first (best quality)
            result = await self._generate_text_ollama(prompt, language, style, max_length)
            if result['success']:
                return result
            
            # Try Hugging Face
            result = await self._generate_text_huggingface(prompt, language, style, max_length)
            if result['success']:
                return result
            
            # Try Groq (free tier)
            result = await self._generate_text_groq(prompt, language, style, max_length)
            if result['success']:
                return result
            
            return {
                'success': False,
                'error': 'All text generation services unavailable'
            }
        
        except Exception as e:
            logger.error(f"Text generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_text_ollama(self, prompt: str, language: str, 
                                   style: str, max_length: int) -> Dict[str, Any]:
        """Generate text using local Ollama"""
        try:
            model = 'arabic-llama2:7b' if language == 'ar' else 'llama2:7b'
            
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'num_predict': max_length,
                    'temperature': 0.7,
                    'top_p': 0.9
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.text_apis['ollama_local']['url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'text': result.get('response', ''),
                            'model_used': model,
                            'service': 'ollama_local'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Ollama error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Ollama exception: {str(e)}"
            }
    
    async def _generate_text_huggingface(self, prompt: str, language: str, 
                                        style: str, max_length: int) -> Dict[str, Any]:
        """Generate text using Hugging Face free API"""
        try:
            model = 'aubmindlab/aragpt2-base' if language == 'ar' else 'google/flan-t5-large'
            
            headers = {
                'Authorization': f"Bearer {os.getenv('HUGGINGFACE_API_KEY', '')}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'inputs': prompt,
                'parameters': {
                    'max_length': max_length,
                    'temperature': 0.7,
                    'do_sample': True,
                    'top_p': 0.9
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.text_apis['huggingface']['url']}{model}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        generated_text = result[0].get('generated_text', '') if isinstance(result, list) else result.get('generated_text', '')
                        
                        return {
                            'success': True,
                            'text': generated_text,
                            'model_used': model,
                            'service': 'huggingface'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Hugging Face error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Hugging Face exception: {str(e)}"
            }
    
    async def _generate_text_groq(self, prompt: str, language: str, 
                                 style: str, max_length: int) -> Dict[str, Any]:
        """Generate text using Groq free tier"""
        try:
            headers = {
                'Authorization': f"Bearer {os.getenv('GROQ_API_KEY', '')}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'mixtral-8x7b-32768',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': max_length,
                'temperature': 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.text_apis['groq']['url'],
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result['choices'][0]['message']['content']
                        
                        return {
                            'success': True,
                            'text': text,
                            'model_used': 'mixtral-8x7b',
                            'service': 'groq'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Groq error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Groq exception: {str(e)}"
            }
    
    async def generate_image(self, prompt: str, style: str = 'realistic', 
                           size: str = '1024x1024', quality: str = 'high') -> Dict[str, Any]:
        """Generate images using free services with high quality"""
        try:
            # Try local Stable Diffusion first (best quality)
            result = await self._generate_image_stable_diffusion(prompt, style, size, quality)
            if result['success']:
                return result
            
            # Try Pollinations (unlimited free)
            result = await self._generate_image_pollinations(prompt, style, size)
            if result['success']:
                return result
            
            # Try Craiyon (fast and free)
            result = await self._generate_image_craiyon(prompt, style)
            if result['success']:
                return result
            
            return {
                'success': False,
                'error': 'All image generation services unavailable'
            }
        
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_image_stable_diffusion(self, prompt: str, style: str, 
                                              size: str, quality: str) -> Dict[str, Any]:
        """Generate image using local Stable Diffusion"""
        try:
            width, height = map(int, size.split('x'))
            
            payload = {
                'prompt': f"{prompt}, {style} style, high quality, detailed",
                'negative_prompt': 'blurry, low quality, distorted, ugly',
                'width': width,
                'height': height,
                'steps': 30 if quality == 'high' else 20,
                'cfg_scale': 7,
                'sampler_name': 'DPM++ 2M Karras'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.image_apis['stable_diffusion_local']['url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Save image
                        image_data = result['images'][0]
                        image_path = f"/tmp/generated_image_{uuid.uuid4()}.png"
                        
                        with open(image_path, 'wb') as f:
                            f.write(base64.b64decode(image_data))
                        
                        return {
                            'success': True,
                            'image_path': image_path,
                            'service': 'stable_diffusion_local',
                            'quality': 'ultra_high'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Stable Diffusion error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Stable Diffusion exception: {str(e)}"
            }
    
    async def _generate_image_pollinations(self, prompt: str, style: str, size: str) -> Dict[str, Any]:
        """Generate image using Pollinations (unlimited free)"""
        try:
            # Pollinations URL format
            encoded_prompt = requests.utils.quote(f"{prompt}, {style} style")
            image_url = f"{self.image_apis['pollinations']['url']}{encoded_prompt}?width={size.split('x')[0]}&height={size.split('x')[1]}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image_path = f"/tmp/generated_image_{uuid.uuid4()}.png"
                        
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        return {
                            'success': True,
                            'image_path': image_path,
                            'service': 'pollinations',
                            'quality': 'high'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Pollinations error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Pollinations exception: {str(e)}"
            }
    
    async def _generate_image_craiyon(self, prompt: str, style: str) -> Dict[str, Any]:
        """Generate image using Craiyon (fast and free)"""
        try:
            payload = {
                'prompt': f"{prompt}, {style} style"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.image_apis['craiyon']['url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Craiyon returns base64 images
                        images = result.get('images', [])
                        if images:
                            image_data = base64.b64decode(images[0])
                            image_path = f"/tmp/generated_image_{uuid.uuid4()}.png"
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                            
                            return {
                                'success': True,
                                'image_path': image_path,
                                'service': 'craiyon',
                                'quality': 'medium'
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'No images generated'
                            }
                    else:
                        return {
                            'success': False,
                            'error': f"Craiyon error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Craiyon exception: {str(e)}"
            }
    
    async def generate_video(self, prompt: str, duration: int = 5, 
                           style: str = 'cinematic', quality: str = 'high') -> Dict[str, Any]:
        """Generate videos using free services with high quality"""
        try:
            # Try local AnimateDiff first (best quality)
            result = await self._generate_video_animatediff(prompt, duration, style, quality)
            if result['success']:
                return result
            
            # Try FFmpeg with generated images (unlimited)
            result = await self._generate_video_ffmpeg(prompt, duration, style, quality)
            if result['success']:
                return result
            
            # Try free tier APIs
            result = await self._generate_video_free_apis(prompt, duration, style)
            if result['success']:
                return result
            
            return {
                'success': False,
                'error': 'All video generation services unavailable'
            }
        
        except Exception as e:
            logger.error(f"Video generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_video_animatediff(self, prompt: str, duration: int, 
                                         style: str, quality: str) -> Dict[str, Any]:
        """Generate video using local AnimateDiff"""
        try:
            # AnimateDiff command
            output_path = f"/tmp/generated_video_{uuid.uuid4()}.mp4"
            
            cmd = [
                'python', '/opt/AnimateDiff/scripts/animate.py',
                '--config', '/opt/AnimateDiff/configs/inference/inference.yaml',
                '--prompt', f"{prompt}, {style} style, high quality",
                '--n_prompt', 'blurry, low quality, distorted',
                '--length', str(duration * 8),  # 8 frames per second
                '--output', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                return {
                    'success': True,
                    'video_path': output_path,
                    'service': 'animatediff_local',
                    'quality': 'ultra_high'
                }
            else:
                return {
                    'success': False,
                    'error': f"AnimateDiff error: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"AnimateDiff exception: {str(e)}"
            }
    
    async def _generate_video_ffmpeg(self, prompt: str, duration: int, 
                                    style: str, quality: str) -> Dict[str, Any]:
        """Generate video using FFmpeg with AI-generated images"""
        try:
            # Generate keyframes
            frame_count = duration * 8  # 8 FPS
            frames = []
            
            for i in range(frame_count):
                frame_prompt = f"{prompt}, {style} style, frame {i+1}, slight motion"
                
                # Generate frame image
                image_result = await self.generate_image(frame_prompt, style, '1920x1080', quality)
                
                if image_result['success']:
                    frames.append(image_result['image_path'])
                else:
                    # Use previous frame if generation fails
                    if frames:
                        frames.append(frames[-1])
            
            if not frames:
                return {
                    'success': False,
                    'error': 'Failed to generate video frames'
                }
            
            # Create video from frames
            output_path = f"/tmp/generated_video_{uuid.uuid4()}.mp4"
            
            # Create input file list
            input_list = f"/tmp/input_list_{uuid.uuid4()}.txt"
            with open(input_list, 'w') as f:
                for frame in frames:
                    f.write(f"file '{frame}'\n")
                    f.write(f"duration {1/8}\n")  # 8 FPS
            
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', input_list,
                '-vf', 'fps=24,scale=1920:1080',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '18' if quality == 'high' else '23',
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup
            os.unlink(input_list)
            for frame in frames:
                try:
                    os.unlink(frame)
                except:
                    pass
            
            if process.returncode == 0 and os.path.exists(output_path):
                return {
                    'success': True,
                    'video_path': output_path,
                    'service': 'ffmpeg_local',
                    'quality': 'high'
                }
            else:
                return {
                    'success': False,
                    'error': f"FFmpeg error: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"FFmpeg exception: {str(e)}"
            }
    
    async def _generate_video_free_apis(self, prompt: str, duration: int, style: str) -> Dict[str, Any]:
        """Try free tier video APIs"""
        try:
            # This would implement free tier APIs like Runway, Pika, etc.
            # For now, return not available
            return {
                'success': False,
                'error': 'Free video APIs not configured'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_audio(self, text: str, language: str = 'en', 
                           voice: str = 'neutral', quality: str = 'high') -> Dict[str, Any]:
        """Generate audio using free TTS services"""
        try:
            # Try Coqui TTS first (best quality)
            result = await self._generate_audio_coqui(text, language, voice, quality)
            if result['success']:
                return result
            
            # Try eSpeak (fast and reliable)
            result = await self._generate_audio_espeak(text, language, voice)
            if result['success']:
                return result
            
            # Try Festival
            result = await self._generate_audio_festival(text, language)
            if result['success']:
                return result
            
            return {
                'success': False,
                'error': 'All audio generation services unavailable'
            }
        
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_audio_coqui(self, text: str, language: str, 
                                   voice: str, quality: str) -> Dict[str, Any]:
        """Generate audio using Coqui TTS"""
        try:
            output_path = f"/tmp/generated_audio_{uuid.uuid4()}.wav"
            
            # Coqui TTS command
            cmd = [
                'tts',
                '--text', text,
                '--model_name', f'tts_models/{language}/fairseq/vits',
                '--out_path', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                return {
                    'success': True,
                    'audio_path': output_path,
                    'service': 'coqui_tts',
                    'quality': 'high'
                }
            else:
                return {
                    'success': False,
                    'error': f"Coqui TTS error: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Coqui TTS exception: {str(e)}"
            }
    
    async def _generate_audio_espeak(self, text: str, language: str, voice: str) -> Dict[str, Any]:
        """Generate audio using eSpeak"""
        try:
            output_path = f"/tmp/generated_audio_{uuid.uuid4()}.wav"
            
            # eSpeak command
            lang_code = 'ar' if language == 'ar' else 'en'
            cmd = [
                'espeak',
                '-v', lang_code,
                '-s', '150',  # Speed
                '-w', output_path,
                text
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                return {
                    'success': True,
                    'audio_path': output_path,
                    'service': 'espeak',
                    'quality': 'medium'
                }
            else:
                return {
                    'success': False,
                    'error': f"eSpeak error: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"eSpeak exception: {str(e)}"
            }
    
    async def _generate_audio_festival(self, text: str, language: str) -> Dict[str, Any]:
        """Generate audio using Festival"""
        try:
            output_path = f"/tmp/generated_audio_{uuid.uuid4()}.wav"
            
            # Festival command
            cmd = [
                'text2wave',
                '-o', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=text.encode())
            
            if process.returncode == 0 and os.path.exists(output_path):
                return {
                    'success': True,
                    'audio_path': output_path,
                    'service': 'festival',
                    'quality': 'medium'
                }
            else:
                return {
                    'success': False,
                    'error': f"Festival error: {stderr.decode()}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Festival exception: {str(e)}"
            }
    
    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate text using free services"""
        try:
            # Try LibreTranslate first
            result = await self._translate_libre(text, source_lang, target_lang)
            if result['success']:
                return result
            
            # Try MyMemory
            result = await self._translate_mymemory(text, source_lang, target_lang)
            if result['success']:
                return result
            
            # Try Google Translate free
            result = await self._translate_google_free(text, source_lang, target_lang)
            if result['success']:
                return result
            
            return {
                'success': False,
                'error': 'All translation services unavailable'
            }
        
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _translate_libre(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate using LibreTranslate"""
        try:
            payload = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.translation_apis['libre_translate']['url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'translated_text': result['translatedText'],
                            'service': 'libre_translate'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"LibreTranslate error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"LibreTranslate exception: {str(e)}"
            }
    
    async def _translate_mymemory(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate using MyMemory"""
        try:
            params = {
                'q': text,
                'langpair': f"{source_lang}|{target_lang}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.translation_apis['mymemory']['url'],
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'translated_text': result['responseData']['translatedText'],
                            'service': 'mymemory'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"MyMemory error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"MyMemory exception: {str(e)}"
            }
    
    async def _translate_google_free(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate using Google Translate free endpoint"""
        try:
            params = {
                'client': 'gtx',
                'sl': source_lang,
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.translation_apis['google_translate_free']['url'],
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated_text = result[0][0][0]
                        return {
                            'success': True,
                            'translated_text': translated_text,
                            'service': 'google_translate_free'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Google Translate error: {response.status}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Google Translate exception: {str(e)}"
            }

# Global free AI services instance
free_ai = FreeAIServices()

