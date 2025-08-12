import json
import os
import logging
import subprocess
import tempfile
import uuid
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from PIL import Image
import io
import requests
import google.generativeai as genai
from src.services.external_api_integration import api_integration

logger = logging.getLogger(__name__)

class FreeAIGenerator:
    """Free AI Content Generator using Google Gemini and other free services"""
    
    def __init__(self):
        # Google Gemini Configuration (Free)
        self.gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        
        # Hugging Face Free Models
        self.hf_api_url = 'https://api-inference.huggingface.co/models'
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        
        # Free Text Generation Models (Hugging Face)
        self.free_text_models = [
            'microsoft/DialoGPT-large',
            'facebook/blenderbot-400M-distill',
            'microsoft/DialoGPT-medium',
            'EleutherAI/gpt-neo-2.7B',
            'EleutherAI/gpt-j-6B'
        ]
        
        # Free Image Generation Models (Hugging Face)
        self.free_image_models = [
            'runwayml/stable-diffusion-v1-5',
            'stabilityai/stable-diffusion-2-1',
            'CompVis/stable-diffusion-v1-4',
            'dreamlike-art/dreamlike-diffusion-1.0'
        ]
        
        # Free Text-to-Speech Models (Hugging Face)
        self.free_tts_models = [
            'microsoft/speecht5_tts',
            'facebook/fastspeech2-en-ljspeech',
            'espnet/kan-bayashi_ljspeech_vits'
        ]
        
        # Marketing strategies with free alternatives
        self.free_marketing_strategies = {
            'content_marketing': {
                'prompts_ar': [
                    'اكتب محتوى تسويقي مفيد وجذاب عن {product}',
                    'أنشئ مقال تعليمي عن فوائد {product}',
                    'اكتب نصائح مهمة حول استخدام {product}'
                ],
                'prompts_en': [
                    'Write valuable and engaging marketing content about {product}',
                    'Create an educational article about {product} benefits',
                    'Write important tips about using {product}'
                ]
            },
            'social_media_marketing': {
                'prompts_ar': [
                    'اكتب منشور جذاب لوسائل التواصل الاجتماعي عن {product}',
                    'أنشئ محتوى تفاعلي للسوشيال ميديا عن {product}',
                    'اكتب كابشن مثير للاهتمام عن {product}'
                ],
                'prompts_en': [
                    'Write an engaging social media post about {product}',
                    'Create interactive social media content about {product}',
                    'Write an interesting caption about {product}'
                ]
            },
            'viral_marketing': {
                'prompts_ar': [
                    'اكتب محتوى فيروسي قابل للانتشار عن {product}',
                    'أنشئ محتوى مثير ومفاجئ عن {product}',
                    'اكتب شيء يجعل الناس تريد مشاركة {product}'
                ],
                'prompts_en': [
                    'Write viral content that spreads about {product}',
                    'Create exciting and surprising content about {product}',
                    'Write something that makes people want to share {product}'
                ]
            }
        }
    
    async def generate_free_text_content(self, prompt: str, language: str = 'ar', strategy: str = 'content_marketing') -> Dict:
        """Generate text content using free services"""
        
        try:
            # Try Google Gemini first (free tier)
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                return {
                    'success': True,
                    'content': result['data'].get('text', ''),
                    'service': 'google_gemini',
                    'strategy': strategy,
                    'language': language
                }
            
            # Fallback to Hugging Face free models
            return await self.generate_with_huggingface_text(prompt, language)
            
        except Exception as e:
            logger.error(f"Error generating free text content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_with_huggingface_text(self, prompt: str, language: str = 'ar') -> Dict:
        """Generate text using Hugging Face free models"""
        
        try:
            if not self.hf_api_key:
                return {'success': False, 'error': 'Hugging Face API key not configured'}
            
            # Try different models
            for model in self.free_text_models:
                try:
                    headers = {
                        'Authorization': f'Bearer {self.hf_api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    payload = {
                        'inputs': prompt,
                        'parameters': {
                            'max_length': 500,
                            'temperature': 0.7,
                            'do_sample': True
                        }
                    }
                    
                    response = requests.post(
                        f"{self.hf_api_url}/{model}",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if isinstance(result, list) and len(result) > 0:
                            generated_text = result[0].get('generated_text', '')
                            
                            return {
                                'success': True,
                                'content': generated_text,
                                'service': f'huggingface_{model}',
                                'language': language
                            }
                
                except Exception as model_error:
                    logger.warning(f"Model {model} failed: {str(model_error)}")
                    continue
            
            return {'success': False, 'error': 'All Hugging Face text models failed'}
            
        except Exception as e:
            logger.error(f"Error with Hugging Face text generation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_free_image_content(self, prompt: str, product: str = '', language: str = 'ar') -> Dict:
        """Generate image content using free services"""
        
        try:
            # Enhance prompt for better results
            if language == 'ar':
                enhanced_prompt = f"صورة تسويقية احترافية، {prompt}، جودة عالية، تصميم حديث"
            else:
                enhanced_prompt = f"Professional marketing image, {prompt}, high quality, modern design"
            
            # Try Google Gemini first
            result = await api_integration.generate_image(
                prompt=enhanced_prompt,
                width=1024,
                height=1024,
                service='google_gemini'
            )
            
            if result['success']:
                # Save image
                image_data = base64.b64decode(result['data']['content'])
                image_filename = f"free_generated_image_{uuid.uuid4().hex}.png"
                image_path = os.path.join('src/static/generated_images', image_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                return {
                    'success': True,
                    'image_url': f"/static/generated_images/{image_filename}",
                    'image_path': image_path,
                    'service': 'google_gemini',
                    'prompt': enhanced_prompt
                }
            
            # Fallback to Hugging Face
            return await self.generate_with_huggingface_image(enhanced_prompt)
            
        except Exception as e:
            logger.error(f"Error generating free image content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_with_huggingface_image(self, prompt: str) -> Dict:
        """Generate image using Hugging Face free models"""
        
        try:
            if not self.hf_api_key:
                return {'success': False, 'error': 'Hugging Face API key not configured'}
            
            # Try different image models
            for model in self.free_image_models:
                try:
                    headers = {
                        'Authorization': f'Bearer {self.hf_api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    payload = {
                        'inputs': prompt,
                        'parameters': {
                            'num_inference_steps': 20,
                            'guidance_scale': 7.5
                        }
                    }
                    
                    response = requests.post(
                        f"{self.hf_api_url}/{model}",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        # Save image
                        image_filename = f"hf_generated_image_{uuid.uuid4().hex}.png"
                        image_path = os.path.join('src/static/generated_images', image_filename)
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(image_path), exist_ok=True)
                        
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                        
                        return {
                            'success': True,
                            'image_url': f"/static/generated_images/{image_filename}",
                            'image_path': image_path,
                            'service': f'huggingface_{model}',
                            'prompt': prompt
                        }
                
                except Exception as model_error:
                    logger.warning(f"Image model {model} failed: {str(model_error)}")
                    continue
            
            return {'success': False, 'error': 'All Hugging Face image models failed'}
            
        except Exception as e:
            logger.error(f"Error with Hugging Face image generation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_free_audio_content(self, text: str, language: str = 'ar') -> Dict:
        """Generate audio content using free services"""
        
        try:
            # Try Google TTS first (free tier)
            result = await api_integration.generate_speech(
                text=text,
                language='ar-SA' if language == 'ar' else 'en-US',
                service='google_tts'
            )
            
            if result['success']:
                # Save audio
                audio_data = base64.b64decode(result['data']['content'])
                audio_filename = f"free_generated_audio_{uuid.uuid4().hex}.mp3"
                audio_path = os.path.join('src/static/generated_audio', audio_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                
                return {
                    'success': True,
                    'audio_url': f"/static/generated_audio/{audio_filename}",
                    'audio_path': audio_path,
                    'service': 'google_tts',
                    'text': text
                }
            
            # Fallback to Hugging Face TTS
            return await self.generate_with_huggingface_tts(text, language)
            
        except Exception as e:
            logger.error(f"Error generating free audio content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_with_huggingface_tts(self, text: str, language: str = 'ar') -> Dict:
        """Generate audio using Hugging Face TTS models"""
        
        try:
            if not self.hf_api_key:
                return {'success': False, 'error': 'Hugging Face API key not configured'}
            
            # Use English models for now (Arabic TTS models are limited)
            if language == 'ar':
                # Translate to English for TTS
                text = f"Arabic text: {text}"  # Simple fallback
            
            for model in self.free_tts_models:
                try:
                    headers = {
                        'Authorization': f'Bearer {self.hf_api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    payload = {
                        'inputs': text,
                        'parameters': {
                            'speaker_embeddings': 'default'
                        }
                    }
                    
                    response = requests.post(
                        f"{self.hf_api_url}/{model}",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        # Save audio
                        audio_filename = f"hf_generated_audio_{uuid.uuid4().hex}.wav"
                        audio_path = os.path.join('src/static/generated_audio', audio_filename)
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                        
                        with open(audio_path, 'wb') as f:
                            f.write(response.content)
                        
                        return {
                            'success': True,
                            'audio_url': f"/static/generated_audio/{audio_filename}",
                            'audio_path': audio_path,
                            'service': f'huggingface_{model}',
                            'text': text
                        }
                
                except Exception as model_error:
                    logger.warning(f"TTS model {model} failed: {str(model_error)}")
                    continue
            
            return {'success': False, 'error': 'All Hugging Face TTS models failed'}
            
        except Exception as e:
            logger.error(f"Error with Hugging Face TTS: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_complete_marketing_content(self, task_data: Dict) -> Dict:
        """Generate complete marketing content using only free services"""
        
        try:
            strategy = task_data.get('strategy', 'content_marketing')
            language = task_data.get('language', 'ar')
            product = task_data.get('product_service', '')
            business_type = task_data.get('business_type', '')
            target_audience = task_data.get('target_audience', '')
            
            # Get strategy prompts
            strategy_prompts = self.free_marketing_strategies.get(strategy, self.free_marketing_strategies['content_marketing'])
            prompts = strategy_prompts[f'prompts_{language}']
            
            # Select random prompt and format it
            import random
            selected_prompt = random.choice(prompts).format(product=product)
            
            # Build comprehensive prompt
            if language == 'ar':
                full_prompt = f"""أنت خبير تسويق محترف. {selected_prompt}

معلومات إضافية:
- نوع العمل: {business_type}
- الجمهور المستهدف: {target_audience}
- المنتج/الخدمة: {product}

اكتب محتوى تسويقي جذاب ومؤثر يناسب الجمهور المستهدف."""
            else:
                full_prompt = f"""You are a professional marketing expert. {selected_prompt}

Additional Information:
- Business Type: {business_type}
- Target Audience: {target_audience}
- Product/Service: {product}

Write engaging and impactful marketing content suitable for the target audience."""
            
            # Generate text content
            text_result = await self.generate_free_text_content(full_prompt, language, strategy)
            
            if not text_result['success']:
                return {'success': False, 'error': 'Failed to generate text content'}
            
            content = {
                'text': text_result['content'],
                'strategy': strategy,
                'language': language,
                'service_used': text_result['service']
            }
            
            # Generate image if requested
            if task_data.get('include_image', True):
                if language == 'ar':
                    image_prompt = f"صورة تسويقية لـ {product}"
                else:
                    image_prompt = f"Marketing image for {product}"
                
                image_result = await self.generate_free_image_content(image_prompt, product, language)
                if image_result['success']:
                    content['image_url'] = image_result['image_url']
                    content['image_service'] = image_result['service']
            
            # Generate audio if requested
            if task_data.get('include_audio', False):
                audio_text = content['text'][:500]  # Limit text length for audio
                audio_result = await self.generate_free_audio_content(audio_text, language)
                if audio_result['success']:
                    content['audio_url'] = audio_result['audio_url']
                    content['audio_service'] = audio_result['service']
            
            # Generate hashtags
            hashtags = await self.generate_free_hashtags(product, target_audience, language)
            content['hashtags'] = hashtags
            
            return {
                'success': True,
                'content': content,
                'services_used': {
                    'text': text_result['service'],
                    'image': content.get('image_service', 'none'),
                    'audio': content.get('audio_service', 'none')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating complete marketing content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_free_hashtags(self, product: str, target_audience: str, language: str = 'ar') -> List[str]:
        """Generate hashtags using free services"""
        
        try:
            if language == 'ar':
                prompt = f"أنشئ 10 هاشتاجات مناسبة لـ {product} والجمهور {target_audience}"
            else:
                prompt = f"Generate 10 relevant hashtags for {product} and audience {target_audience}"
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=200,
                temperature=0.8,
                service='google_gemini'
            )
            
            if result['success']:
                hashtags_text = result['data'].get('text', '')
                hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip()]
                
                # Ensure hashtags start with #
                hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
                
                return hashtags[:10]  # Limit to 10 hashtags
            
            # Fallback hashtags
            return ['#marketing', '#business', '#success', '#growth', '#digital']
            
        except Exception as e:
            logger.error(f"Error generating free hashtags: {str(e)}")
            return ['#marketing', '#business', '#success']
    
    def get_free_services_status(self) -> Dict:
        """Get status of all free services"""
        
        status = {
            'google_gemini': {
                'available': bool(self.gemini_api_key),
                'services': ['text_generation', 'image_generation'],
                'cost': 'Free tier available'
            },
            'huggingface': {
                'available': bool(self.hf_api_key),
                'services': ['text_generation', 'image_generation', 'text_to_speech'],
                'cost': 'Free with rate limits'
            },
            'google_tts': {
                'available': True,
                'services': ['text_to_speech'],
                'cost': 'Free tier available'
            }
        }
        
        return status
    
    def estimate_generation_cost(self, task_data: Dict) -> Dict:
        """Estimate cost for content generation (all free)"""
        
        return {
            'text_generation': 0.0,
            'image_generation': 0.0,
            'audio_generation': 0.0,
            'total_cost': 0.0,
            'currency': 'USD',
            'note': 'All services use free tiers'
        }


# Global instance
free_ai_generator = FreeAIGenerator()

