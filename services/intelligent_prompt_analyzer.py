import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from src.services.free_ai_services import free_ai

logger = logging.getLogger(__name__)

class IntelligentPromptAnalyzer:
    """Advanced AI-powered prompt analyzer for automatic video specification detection"""
    
    def __init__(self):
        # Video orientation patterns
        self.orientation_patterns = {
            'vertical': [
                'vertical', 'portrait', 'story', 'stories', 'reels', 'tiktok', 'shorts',
                'instagram story', 'snap story', 'mobile', 'phone', '9:16', '1080x1920',
                'عمودي', 'ستوري', 'ريلز', 'تيك توك', 'شورتس', 'موبايل'
            ],
            'horizontal': [
                'horizontal', 'landscape', 'widescreen', 'youtube', 'facebook video',
                'tv', 'monitor', '16:9', '1920x1080', 'cinema', 'cinematic',
                'أفقي', 'عريض', 'يوتيوب', 'سينمائي', 'تلفزيون'
            ],
            'square': [
                'square', 'instagram post', 'facebook post', '1:1', '1080x1080',
                'مربع', 'منشور انستجرام', 'منشور فيسبوك'
            ]
        }
        
        # Duration patterns
        self.duration_patterns = {
            'seconds': [
                r'(\d+)\s*(?:second|sec|s)\b',
                r'(\d+)\s*(?:ثانية|ث)\b'
            ],
            'minutes': [
                r'(\d+)\s*(?:minute|min|m)\b',
                r'(\d+)\s*(?:دقيقة|د)\b'
            ],
            'specific_durations': {
                'short': ['short', 'quick', 'brief', 'قصير', 'سريع'],
                'medium': ['medium', 'normal', 'standard', 'متوسط', 'عادي'],
                'long': ['long', 'extended', 'detailed', 'طويل', 'مفصل']
            }
        }
        
        # Platform-specific requirements
        self.platform_specs = {
            'tiktok': {
                'orientation': 'vertical',
                'aspect_ratio': '9:16',
                'max_duration': 180,
                'recommended_duration': 15,
                'resolution': '1080x1920'
            },
            'instagram_reels': {
                'orientation': 'vertical',
                'aspect_ratio': '9:16',
                'max_duration': 90,
                'recommended_duration': 30,
                'resolution': '1080x1920'
            },
            'instagram_story': {
                'orientation': 'vertical',
                'aspect_ratio': '9:16',
                'max_duration': 15,
                'recommended_duration': 10,
                'resolution': '1080x1920'
            },
            'youtube_shorts': {
                'orientation': 'vertical',
                'aspect_ratio': '9:16',
                'max_duration': 60,
                'recommended_duration': 30,
                'resolution': '1080x1920'
            },
            'youtube': {
                'orientation': 'horizontal',
                'aspect_ratio': '16:9',
                'max_duration': 3600,
                'recommended_duration': 300,
                'resolution': '1920x1080'
            },
            'facebook': {
                'orientation': 'horizontal',
                'aspect_ratio': '16:9',
                'max_duration': 7200,
                'recommended_duration': 60,
                'resolution': '1920x1080'
            },
            'twitter': {
                'orientation': 'horizontal',
                'aspect_ratio': '16:9',
                'max_duration': 140,
                'recommended_duration': 30,
                'resolution': '1280x720'
            }
        }
        
        # Style patterns
        self.style_patterns = {
            'cinematic': [
                'cinematic', 'movie', 'film', 'dramatic', 'epic', 'professional',
                'سينمائي', 'فيلم', 'درامي', 'ملحمي', 'احترافي'
            ],
            'modern': [
                'modern', 'contemporary', 'trendy', 'stylish', 'sleek',
                'حديث', 'عصري', 'أنيق', 'عملي'
            ],
            'vintage': [
                'vintage', 'retro', 'classic', 'old school', 'nostalgic',
                'قديم', 'كلاسيكي', 'تراثي', 'نوستالجي'
            ],
            'minimalist': [
                'minimalist', 'simple', 'clean', 'minimal', 'basic',
                'بسيط', 'نظيف', 'أساسي', 'مينيمال'
            ],
            'dynamic': [
                'dynamic', 'energetic', 'fast', 'action', 'exciting',
                'ديناميكي', 'نشيط', 'سريع', 'حماسي', 'مثير'
            ],
            'elegant': [
                'elegant', 'sophisticated', 'luxury', 'premium', 'classy',
                'أنيق', 'راقي', 'فاخر', 'مميز', 'كلاسي'
            ]
        }
        
        # Quality patterns
        self.quality_patterns = {
            'ultra_high': [
                '4k', 'ultra hd', 'uhd', 'ultra high', 'premium quality',
                'جودة عالية جداً', 'فور كي', 'جودة ممتازة'
            ],
            'high': [
                'hd', 'high definition', 'high quality', '1080p', 'full hd',
                'جودة عالية', 'اتش دي', 'جودة ممتازة'
            ],
            'medium': [
                '720p', 'standard', 'normal quality', 'medium',
                'جودة متوسطة', 'عادي', 'ستاندرد'
            ]
        }
        
        # Content type patterns
        self.content_patterns = {
            'promotional': [
                'promo', 'advertisement', 'ad', 'marketing', 'promotion', 'sale',
                'إعلان', 'ترويج', 'تسويق', 'عرض', 'تخفيض'
            ],
            'educational': [
                'tutorial', 'how to', 'guide', 'lesson', 'educational', 'learn',
                'تعليمي', 'شرح', 'درس', 'كيفية', 'تعلم'
            ],
            'entertainment': [
                'fun', 'funny', 'entertainment', 'comedy', 'amusing',
                'ترفيهي', 'مضحك', 'كوميدي', 'ممتع'
            ],
            'testimonial': [
                'testimonial', 'review', 'feedback', 'customer story',
                'شهادة', 'مراجعة', 'تقييم', 'قصة عميل'
            ],
            'product_demo': [
                'demo', 'demonstration', 'showcase', 'product', 'features',
                'عرض', 'توضيح', 'منتج', 'مميزات'
            ]
        }
    
    async def analyze_prompt(self, prompt: str, language: str = 'auto') -> Dict[str, Any]:
        """Comprehensive prompt analysis with AI enhancement"""
        try:
            # Detect language if auto
            if language == 'auto':
                language = self._detect_language(prompt)
            
            # Basic pattern analysis
            basic_analysis = self._analyze_patterns(prompt)
            
            # AI-enhanced analysis
            ai_analysis = await self._ai_enhanced_analysis(prompt, language)
            
            # Merge and validate results
            final_specs = self._merge_and_validate(basic_analysis, ai_analysis)
            
            # Apply platform-specific optimizations
            optimized_specs = self._apply_platform_optimizations(final_specs)
            
            return {
                'success': True,
                'specifications': optimized_specs,
                'confidence_score': self._calculate_confidence(basic_analysis, ai_analysis),
                'language_detected': language,
                'analysis_method': 'hybrid_ai_pattern',
                'recommendations': self._generate_recommendations(optimized_specs)
            }
        
        except Exception as e:
            logger.error(f"Prompt analysis error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'specifications': self._get_default_specs()
            }
    
    def _detect_language(self, text: str) -> str:
        """Detect text language"""
        # Simple Arabic detection
        arabic_chars = len([c for c in text if '\u0600' <= c <= '\u06FF'])
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return 'en'
        
        arabic_ratio = arabic_chars / total_chars
        return 'ar' if arabic_ratio > 0.3 else 'en'
    
    def _analyze_patterns(self, prompt: str) -> Dict[str, Any]:
        """Pattern-based analysis"""
        prompt_lower = prompt.lower()
        analysis = {}
        
        # Analyze orientation
        analysis['orientation'] = self._detect_orientation(prompt_lower)
        
        # Analyze duration
        analysis['duration'] = self._detect_duration(prompt_lower)
        
        # Analyze platform
        analysis['platform'] = self._detect_platform(prompt_lower)
        
        # Analyze style
        analysis['style'] = self._detect_style(prompt_lower)
        
        # Analyze quality
        analysis['quality'] = self._detect_quality(prompt_lower)
        
        # Analyze content type
        analysis['content_type'] = self._detect_content_type(prompt_lower)
        
        return analysis
    
    def _detect_orientation(self, prompt: str) -> str:
        """Detect video orientation from prompt"""
        scores = {'vertical': 0, 'horizontal': 0, 'square': 0}
        
        for orientation, patterns in self.orientation_patterns.items():
            for pattern in patterns:
                if pattern in prompt:
                    scores[orientation] += 1
        
        # Return orientation with highest score
        max_orientation = max(scores, key=scores.get)
        return max_orientation if scores[max_orientation] > 0 else 'horizontal'  # Default
    
    def _detect_duration(self, prompt: str) -> int:
        """Detect video duration from prompt"""
        # Check for specific time mentions
        for pattern in self.duration_patterns['seconds']:
            matches = re.findall(pattern, prompt)
            if matches:
                return int(matches[0])
        
        for pattern in self.duration_patterns['minutes']:
            matches = re.findall(pattern, prompt)
            if matches:
                return int(matches[0]) * 60
        
        # Check for duration descriptors
        for duration_type, keywords in self.duration_patterns['specific_durations'].items():
            for keyword in keywords:
                if keyword in prompt:
                    if duration_type == 'short':
                        return 15
                    elif duration_type == 'medium':
                        return 30
                    elif duration_type == 'long':
                        return 60
        
        return 30  # Default duration
    
    def _detect_platform(self, prompt: str) -> Optional[str]:
        """Detect target platform from prompt"""
        platform_keywords = {
            'tiktok': ['tiktok', 'tik tok', 'تيك توك'],
            'instagram_reels': ['instagram reels', 'reels', 'ريلز', 'انستجرام ريلز'],
            'instagram_story': ['instagram story', 'story', 'stories', 'ستوري', 'انستجرام ستوري'],
            'youtube_shorts': ['youtube shorts', 'shorts', 'يوتيوب شورتس', 'شورتس'],
            'youtube': ['youtube', 'يوتيوب'],
            'facebook': ['facebook', 'فيسبوك'],
            'twitter': ['twitter', 'تويتر']
        }
        
        for platform, keywords in platform_keywords.items():
            for keyword in keywords:
                if keyword in prompt:
                    return platform
        
        return None
    
    def _detect_style(self, prompt: str) -> str:
        """Detect video style from prompt"""
        scores = {}
        
        for style, patterns in self.style_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in prompt:
                    score += 1
            if score > 0:
                scores[style] = score
        
        return max(scores, key=scores.get) if scores else 'modern'
    
    def _detect_quality(self, prompt: str) -> str:
        """Detect quality requirements from prompt"""
        for quality, patterns in self.quality_patterns.items():
            for pattern in patterns:
                if pattern in prompt:
                    return quality
        
        return 'high'  # Default quality
    
    def _detect_content_type(self, prompt: str) -> str:
        """Detect content type from prompt"""
        scores = {}
        
        for content_type, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in prompt:
                    score += 1
            if score > 0:
                scores[content_type] = score
        
        return max(scores, key=scores.get) if scores else 'promotional'
    
    async def _ai_enhanced_analysis(self, prompt: str, language: str) -> Dict[str, Any]:
        """AI-powered prompt analysis"""
        try:
            analysis_prompt = f"""
            Analyze this video creation prompt and extract specifications:
            
            Prompt: "{prompt}"
            
            Extract and return in JSON format:
            {{
                "orientation": "vertical/horizontal/square",
                "duration_seconds": number,
                "aspect_ratio": "16:9/9:16/1:1",
                "resolution": "1920x1080/1080x1920/1080x1080",
                "style": "cinematic/modern/vintage/minimalist/dynamic/elegant",
                "quality": "ultra_high/high/medium",
                "content_type": "promotional/educational/entertainment/testimonial/product_demo",
                "platform": "tiktok/instagram_reels/youtube/facebook/etc",
                "mood": "energetic/calm/professional/fun/dramatic",
                "target_audience": "description",
                "key_elements": ["element1", "element2"],
                "color_scheme": "description",
                "music_style": "upbeat/calm/dramatic/corporate",
                "text_overlay": true/false,
                "branding": true/false
            }}
            
            Be specific and accurate based on the prompt content.
            """
            
            result = await free_ai.generate_text(
                prompt=analysis_prompt,
                language=language,
                style='analytical',
                max_length=500
            )
            
            if result['success']:
                try:
                    # Extract JSON from response
                    response_text = result['text']
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    
                    if json_start != -1 and json_end != -1:
                        json_str = response_text[json_start:json_end]
                        ai_specs = json.loads(json_str)
                        return ai_specs
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI analysis JSON")
            
            return {}
        
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return {}
    
    def _merge_and_validate(self, basic_analysis: Dict, ai_analysis: Dict) -> Dict[str, Any]:
        """Merge pattern and AI analysis results"""
        merged = {}
        
        # Priority: AI analysis > Pattern analysis > Defaults
        
        # Orientation
        merged['orientation'] = (
            ai_analysis.get('orientation') or 
            basic_analysis.get('orientation') or 
            'horizontal'
        )
        
        # Duration
        ai_duration = ai_analysis.get('duration_seconds')
        basic_duration = basic_analysis.get('duration')
        merged['duration'] = ai_duration or basic_duration or 30
        
        # Platform
        merged['platform'] = (
            ai_analysis.get('platform') or 
            basic_analysis.get('platform')
        )
        
        # Style
        merged['style'] = (
            ai_analysis.get('style') or 
            basic_analysis.get('style') or 
            'modern'
        )
        
        # Quality
        merged['quality'] = (
            ai_analysis.get('quality') or 
            basic_analysis.get('quality') or 
            'high'
        )
        
        # Content type
        merged['content_type'] = (
            ai_analysis.get('content_type') or 
            basic_analysis.get('content_type') or 
            'promotional'
        )
        
        # Additional AI-only fields
        merged['mood'] = ai_analysis.get('mood', 'professional')
        merged['target_audience'] = ai_analysis.get('target_audience', 'general')
        merged['key_elements'] = ai_analysis.get('key_elements', [])
        merged['color_scheme'] = ai_analysis.get('color_scheme', 'vibrant')
        merged['music_style'] = ai_analysis.get('music_style', 'upbeat')
        merged['text_overlay'] = ai_analysis.get('text_overlay', True)
        merged['branding'] = ai_analysis.get('branding', True)
        
        # Calculate aspect ratio and resolution
        merged['aspect_ratio'] = self._get_aspect_ratio(merged['orientation'])
        merged['resolution'] = self._get_resolution(merged['orientation'], merged['quality'])
        
        return merged
    
    def _apply_platform_optimizations(self, specs: Dict) -> Dict[str, Any]:
        """Apply platform-specific optimizations"""
        platform = specs.get('platform')
        
        if platform and platform in self.platform_specs:
            platform_spec = self.platform_specs[platform]
            
            # Override with platform requirements
            specs['orientation'] = platform_spec['orientation']
            specs['aspect_ratio'] = platform_spec['aspect_ratio']
            specs['resolution'] = platform_spec['resolution']
            
            # Adjust duration to platform limits
            max_duration = platform_spec['max_duration']
            recommended_duration = platform_spec['recommended_duration']
            
            if specs['duration'] > max_duration:
                specs['duration'] = max_duration
                specs['duration_adjusted'] = True
                specs['original_duration'] = specs['duration']
            
            # Add platform-specific recommendations
            specs['platform_optimized'] = True
            specs['recommended_duration'] = recommended_duration
        
        return specs
    
    def _get_aspect_ratio(self, orientation: str) -> str:
        """Get aspect ratio based on orientation"""
        ratios = {
            'vertical': '9:16',
            'horizontal': '16:9',
            'square': '1:1'
        }
        return ratios.get(orientation, '16:9')
    
    def _get_resolution(self, orientation: str, quality: str) -> str:
        """Get resolution based on orientation and quality"""
        resolutions = {
            'vertical': {
                'ultra_high': '1080x1920',
                'high': '1080x1920',
                'medium': '720x1280'
            },
            'horizontal': {
                'ultra_high': '3840x2160',
                'high': '1920x1080',
                'medium': '1280x720'
            },
            'square': {
                'ultra_high': '1080x1080',
                'high': '1080x1080',
                'medium': '720x720'
            }
        }
        
        return resolutions.get(orientation, {}).get(quality, '1920x1080')
    
    def _calculate_confidence(self, basic_analysis: Dict, ai_analysis: Dict) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on pattern matches
        if basic_analysis.get('orientation') != 'horizontal':  # Non-default
            confidence += 0.1
        if basic_analysis.get('duration') != 30:  # Non-default
            confidence += 0.1
        if basic_analysis.get('platform'):
            confidence += 0.2
        
        # Increase confidence based on AI analysis
        if ai_analysis:
            confidence += 0.2
            if len(ai_analysis.get('key_elements', [])) > 0:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_recommendations(self, specs: Dict) -> List[str]:
        """Generate recommendations based on specifications"""
        recommendations = []
        
        # Duration recommendations
        duration = specs.get('duration', 30)
        if duration < 15:
            recommendations.append("Consider extending duration to at least 15 seconds for better engagement")
        elif duration > 60 and specs.get('platform') in ['tiktok', 'instagram_reels']:
            recommendations.append("Consider shortening for better platform performance")
        
        # Platform-specific recommendations
        platform = specs.get('platform')
        if platform == 'tiktok':
            recommendations.append("Add trending hashtags and music for better reach")
            recommendations.append("Use vertical orientation with engaging opening")
        elif platform == 'youtube':
            recommendations.append("Include compelling thumbnail and title")
            recommendations.append("Add clear call-to-action")
        
        # Quality recommendations
        if specs.get('quality') == 'medium':
            recommendations.append("Consider upgrading to high quality for professional appearance")
        
        # Style recommendations
        style = specs.get('style')
        if style == 'cinematic':
            recommendations.append("Use dramatic lighting and smooth camera movements")
        elif style == 'dynamic':
            recommendations.append("Include quick cuts and energetic transitions")
        
        return recommendations
    
    def _get_default_specs(self) -> Dict[str, Any]:
        """Get default video specifications"""
        return {
            'orientation': 'horizontal',
            'duration': 30,
            'aspect_ratio': '16:9',
            'resolution': '1920x1080',
            'style': 'modern',
            'quality': 'high',
            'content_type': 'promotional',
            'mood': 'professional',
            'target_audience': 'general',
            'key_elements': [],
            'color_scheme': 'vibrant',
            'music_style': 'upbeat',
            'text_overlay': True,
            'branding': True
        }
    
    async def get_optimized_prompt(self, original_prompt: str, specs: Dict) -> str:
        """Generate optimized prompt based on specifications"""
        try:
            optimization_prompt = f"""
            Enhance this video creation prompt with technical specifications:
            
            Original: "{original_prompt}"
            
            Specifications to include:
            - Orientation: {specs.get('orientation')}
            - Duration: {specs.get('duration')} seconds
            - Style: {specs.get('style')}
            - Quality: {specs.get('quality')}
            - Mood: {specs.get('mood')}
            - Resolution: {specs.get('resolution')}
            
            Create an enhanced prompt that includes all technical details while maintaining the original creative intent.
            Make it detailed and specific for AI video generation.
            """
            
            result = await free_ai.generate_text(
                prompt=optimization_prompt,
                language='en',
                style='technical',
                max_length=300
            )
            
            if result['success']:
                return result['text']
            else:
                return original_prompt
        
        except Exception as e:
            logger.error(f"Prompt optimization error: {str(e)}")
            return original_prompt

# Global intelligent prompt analyzer instance
intelligent_analyzer = IntelligentPromptAnalyzer()

