from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.intelligent_prompt_analyzer import intelligent_analyzer
import logging

prompt_analyzer_bp = Blueprint('prompt_analyzer', __name__)
logger = logging.getLogger(__name__)

@prompt_analyzer_bp.route('/analyze', methods=['POST'])
@jwt_required()
async def analyze_prompt():
    """Analyze prompt and extract video specifications"""
    try:
        data = request.get_json()
        
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400
        
        language = data.get('language', 'auto')
        
        # Analyze prompt
        result = await intelligent_analyzer.analyze_prompt(prompt, language)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Prompt analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prompt_analyzer_bp.route('/optimize', methods=['POST'])
@jwt_required()
async def optimize_prompt():
    """Optimize prompt based on specifications"""
    try:
        data = request.get_json()
        
        original_prompt = data.get('prompt', '').strip()
        if not original_prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400
        
        specifications = data.get('specifications', {})
        
        # Get optimized prompt
        optimized_prompt = await intelligent_analyzer.get_optimized_prompt(
            original_prompt, specifications
        )
        
        return jsonify({
            'success': True,
            'original_prompt': original_prompt,
            'optimized_prompt': optimized_prompt,
            'specifications': specifications
        })
    
    except Exception as e:
        logger.error(f"Prompt optimization error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prompt_analyzer_bp.route('/suggestions', methods=['POST'])
@jwt_required()
async def get_prompt_suggestions():
    """Get prompt suggestions based on content type and platform"""
    try:
        data = request.get_json()
        
        content_type = data.get('content_type', 'promotional')
        platform = data.get('platform', 'instagram')
        business_type = data.get('business_type', 'general')
        language = data.get('language', 'en')
        
        # Generate suggestions
        suggestions = await _generate_prompt_suggestions(
            content_type, platform, business_type, language
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'content_type': content_type,
            'platform': platform,
            'business_type': business_type
        })
    
    except Exception as e:
        logger.error(f"Prompt suggestions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prompt_analyzer_bp.route('/platform-specs', methods=['GET'])
def get_platform_specifications():
    """Get platform-specific video specifications"""
    try:
        platform = request.args.get('platform')
        
        if platform:
            specs = intelligent_analyzer.platform_specs.get(platform)
            if specs:
                return jsonify({
                    'success': True,
                    'platform': platform,
                    'specifications': specs
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Platform {platform} not found'
                }), 404
        else:
            # Return all platform specs
            return jsonify({
                'success': True,
                'platforms': intelligent_analyzer.platform_specs
            })
    
    except Exception as e:
        logger.error(f"Platform specs error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prompt_analyzer_bp.route('/validate', methods=['POST'])
@jwt_required()
async def validate_specifications():
    """Validate video specifications"""
    try:
        data = request.get_json()
        
        specifications = data.get('specifications', {})
        
        validation_result = _validate_specifications(specifications)
        
        return jsonify({
            'success': True,
            'valid': validation_result['valid'],
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings'],
            'suggestions': validation_result['suggestions']
        })
    
    except Exception as e:
        logger.error(f"Specification validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@prompt_analyzer_bp.route('/examples', methods=['GET'])
def get_prompt_examples():
    """Get example prompts for different use cases"""
    try:
        content_type = request.args.get('content_type', 'all')
        platform = request.args.get('platform', 'all')
        language = request.args.get('language', 'en')
        
        examples = _get_prompt_examples(content_type, platform, language)
        
        return jsonify({
            'success': True,
            'examples': examples,
            'filters': {
                'content_type': content_type,
                'platform': platform,
                'language': language
            }
        })
    
    except Exception as e:
        logger.error(f"Prompt examples error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper functions
async def _generate_prompt_suggestions(content_type: str, platform: str, 
                                      business_type: str, language: str) -> list:
    """Generate prompt suggestions"""
    
    suggestions_map = {
        'promotional': {
            'instagram': [
                "Create a dynamic vertical video showcasing our new product launch with vibrant colors and upbeat music",
                "Design a 30-second Instagram Reel highlighting key product benefits with smooth transitions",
                "Generate an engaging story-format video with product demonstration and customer testimonials"
            ],
            'tiktok': [
                "Create a trendy 15-second TikTok video with viral music and quick product reveals",
                "Design a vertical video showing before/after transformation using our product",
                "Generate a fun, energetic video with trending effects and clear call-to-action"
            ],
            'youtube': [
                "Create a professional 60-second product demonstration video with clear narration",
                "Design a cinematic promotional video highlighting brand values and product quality",
                "Generate an educational video explaining product features and benefits"
            ]
        },
        'educational': {
            'instagram': [
                "Create a step-by-step tutorial video in vertical format with clear text overlays",
                "Design an informative Reel explaining industry tips with professional visuals",
                "Generate a how-to video with engaging animations and easy-to-follow instructions"
            ],
            'youtube': [
                "Create a comprehensive tutorial video with detailed explanations and examples",
                "Design an educational series episode with professional presentation style",
                "Generate an informative video with charts, graphs, and expert insights"
            ]
        },
        'entertainment': {
            'tiktok': [
                "Create a funny, relatable video with trending audio and creative editing",
                "Design an entertaining challenge video with engaging visual effects",
                "Generate a humorous skit related to our brand with viral potential"
            ],
            'instagram': [
                "Create an entertaining Reel with trending music and creative transitions",
                "Design a fun behind-the-scenes video with authentic moments",
                "Generate an engaging story series with interactive elements"
            ]
        }
    }
    
    # Get suggestions for the specific combination
    platform_suggestions = suggestions_map.get(content_type, {}).get(platform, [])
    
    # If no specific suggestions, provide general ones
    if not platform_suggestions:
        platform_suggestions = [
            f"Create a {content_type} video for {platform} showcasing your {business_type} business",
            f"Design an engaging {content_type} video optimized for {platform} with clear messaging",
            f"Generate a professional {content_type} video that resonates with your target audience"
        ]
    
    return platform_suggestions

def _validate_specifications(specs: dict) -> dict:
    """Validate video specifications"""
    errors = []
    warnings = []
    suggestions = []
    
    # Validate duration
    duration = specs.get('duration', 30)
    if duration < 5:
        errors.append("Duration too short (minimum 5 seconds)")
    elif duration > 300:
        warnings.append("Duration very long, consider shorter for better engagement")
    
    # Validate orientation
    orientation = specs.get('orientation')
    if orientation not in ['vertical', 'horizontal', 'square']:
        errors.append("Invalid orientation. Must be 'vertical', 'horizontal', or 'square'")
    
    # Validate platform compatibility
    platform = specs.get('platform')
    if platform and platform in intelligent_analyzer.platform_specs:
        platform_spec = intelligent_analyzer.platform_specs[platform]
        
        if duration > platform_spec['max_duration']:
            errors.append(f"Duration exceeds {platform} maximum ({platform_spec['max_duration']}s)")
        
        if orientation != platform_spec['orientation']:
            warnings.append(f"{platform} works best with {platform_spec['orientation']} orientation")
    
    # Validate quality
    quality = specs.get('quality')
    if quality not in ['ultra_high', 'high', 'medium']:
        errors.append("Invalid quality. Must be 'ultra_high', 'high', or 'medium'")
    
    # Generate suggestions
    if not errors:
        if duration < 15 and platform in ['tiktok', 'instagram_reels']:
            suggestions.append("Consider 15-30 seconds for optimal engagement")
        
        if quality == 'medium':
            suggestions.append("Upgrade to 'high' quality for better visual appeal")
        
        if not specs.get('music_style'):
            suggestions.append("Add background music to enhance engagement")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'suggestions': suggestions
    }

def _get_prompt_examples(content_type: str, platform: str, language: str) -> dict:
    """Get example prompts"""
    
    examples = {
        'promotional': {
            'beginner': [
                "Create a product showcase video",
                "Show our new collection",
                "Highlight key features"
            ],
            'intermediate': [
                "Create a 30-second vertical video showcasing our premium skincare line with soft lighting and elegant transitions",
                "Design a dynamic product reveal video with upbeat music and vibrant colors for Instagram Reels",
                "Generate a professional demonstration video highlighting the unique benefits of our service"
            ],
            'advanced': [
                "Create a cinematic 45-second vertical video for Instagram Reels showcasing our luxury watch collection. Use dramatic lighting, slow-motion product reveals, elegant transitions, and sophisticated background music. Include subtle brand elements and end with a compelling call-to-action. Target audience: affluent professionals aged 25-45.",
                "Design a high-energy 15-second TikTok video for our fitness app launch. Use trending music, quick cuts, before/after transformations, vibrant colors, and motivational text overlays. Show diverse users achieving their goals. Include app interface glimpses and download CTA.",
                "Generate a professional 60-second YouTube video demonstrating our AI-powered business software. Use clean, modern visuals, screen recordings, animated explanations, corporate background music, and clear narration. Target B2B audience with focus on efficiency and ROI benefits."
            ]
        },
        'educational': {
            'beginner': [
                "Explain how to use our product",
                "Show step-by-step tutorial",
                "Teach industry basics"
            ],
            'intermediate': [
                "Create a tutorial video showing 5 easy steps to achieve professional results",
                "Design an educational video explaining industry best practices with visual examples",
                "Generate a how-to video with clear instructions and helpful tips"
            ],
            'advanced': [
                "Create a comprehensive 90-second educational video for YouTube explaining advanced digital marketing strategies. Use professional presentation style, animated charts and graphs, expert talking head segments, and practical examples. Include actionable tips, case studies, and clear takeaways for marketing professionals.",
                "Design a 30-second vertical tutorial for Instagram showing 3 quick photography tips. Use split-screen comparisons, before/after examples, text overlays with key points, upbeat background music, and engaging visual demonstrations. Target amateur photographers and content creators.",
                "Generate a detailed tutorial series episode explaining complex software features. Use screen recordings, step-by-step annotations, clear narration, and practical examples. Include troubleshooting tips and best practices for professional users."
            ]
        }
    }
    
    # Filter by content type
    if content_type != 'all' and content_type in examples:
        return {content_type: examples[content_type]}
    
    return examples

