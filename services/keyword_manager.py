import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
import json
from collections import Counter
from src.models.keywords import (
    KeywordCategory, Keyword, Hashtag, ContentKeyword, 
    ContentHashtag, TrendingTopic
)
from src.models.content import Content
from src.services.free_ai_generator import free_ai_generator

logger = logging.getLogger(__name__)

class KeywordManager:
    """Advanced Keyword and Hashtag Management System"""
    
    def __init__(self):
        # Default categories - Extended for algorithm optimization
        self.default_categories = [
            # Core Business Categories
            {
                'name': 'Business',
                'name_ar': 'أعمال',
                'description': 'Business and entrepreneurship keywords',
                'description_ar': 'كلمات مفتاحية للأعمال وريادة الأعمال',
                'color': '#3B82F6',
                'icon': 'briefcase'
            },
            {
                'name': 'Technology',
                'name_ar': 'تقنية',
                'description': 'Technology and innovation keywords',
                'description_ar': 'كلمات مفتاحية للتقنية والابتكار',
                'color': '#8B5CF6',
                'icon': 'cpu'
            },
            {
                'name': 'Marketing',
                'name_ar': 'تسويق',
                'description': 'Marketing and advertising keywords',
                'description_ar': 'كلمات مفتاحية للتسويق والإعلان',
                'color': '#EF4444',
                'icon': 'megaphone'
            },
            {
                'name': 'Health',
                'name_ar': 'صحة',
                'description': 'Health and wellness keywords',
                'description_ar': 'كلمات مفتاحية للصحة والعافية',
                'color': '#10B981',
                'icon': 'heart'
            },
            {
                'name': 'Education',
                'name_ar': 'تعليم',
                'description': 'Education and learning keywords',
                'description_ar': 'كلمات مفتاحية للتعليم والتعلم',
                'color': '#F59E0B',
                'icon': 'book'
            },
            {
                'name': 'Entertainment',
                'name_ar': 'ترفيه',
                'description': 'Entertainment and lifestyle keywords',
                'description_ar': 'كلمات مفتاحية للترفيه ونمط الحياة',
                'color': '#EC4899',
                'icon': 'film'
            },
            
            # Lifestyle Categories
            {
                'name': 'Food & Restaurants',
                'name_ar': 'طعام ومطاعم',
                'description': 'Food, cooking, and restaurant keywords',
                'description_ar': 'كلمات مفتاحية للطعام والطبخ والمطاعم',
                'color': '#F97316',
                'icon': 'utensils'
            },
            {
                'name': 'Travel & Tourism',
                'name_ar': 'سفر وسياحة',
                'description': 'Travel, tourism, and adventure keywords',
                'description_ar': 'كلمات مفتاحية للسفر والسياحة والمغامرة',
                'color': '#06B6D4',
                'icon': 'plane'
            },
            {
                'name': 'Sports & Fitness',
                'name_ar': 'رياضة ولياقة',
                'description': 'Sports, fitness, and wellness keywords',
                'description_ar': 'كلمات مفتاحية للرياضة واللياقة والعافية',
                'color': '#84CC16',
                'icon': 'dumbbell'
            },
            {
                'name': 'Fashion & Beauty',
                'name_ar': 'موضة وجمال',
                'description': 'Fashion, beauty, and style keywords',
                'description_ar': 'كلمات مفتاحية للموضة والجمال والأناقة',
                'color': '#EC4899',
                'icon': 'sparkles'
            },
            {
                'name': 'Real Estate',
                'name_ar': 'عقارات',
                'description': 'Real estate and property keywords',
                'description_ar': 'كلمات مفتاحية للعقارات والممتلكات',
                'color': '#78716C',
                'icon': 'home'
            },
            {
                'name': 'Automotive',
                'name_ar': 'سيارات',
                'description': 'Cars, automotive, and transportation keywords',
                'description_ar': 'كلمات مفتاحية للسيارات والنقل',
                'color': '#374151',
                'icon': 'car'
            },
            {
                'name': 'Parenting & Kids',
                'name_ar': 'أطفال وأمومة',
                'description': 'Parenting, kids, and family keywords',
                'description_ar': 'كلمات مفتاحية للأطفال والأمومة والعائلة',
                'color': '#FBBF24',
                'icon': 'baby'
            },
            {
                'name': 'Arts & Culture',
                'name_ar': 'فنون وثقافة',
                'description': 'Arts, culture, and creativity keywords',
                'description_ar': 'كلمات مفتاحية للفنون والثقافة والإبداع',
                'color': '#A855F7',
                'icon': 'palette'
            },
            
            # Professional Categories
            {
                'name': 'E-commerce',
                'name_ar': 'تجارة إلكترونية',
                'description': 'E-commerce and online business keywords',
                'description_ar': 'كلمات مفتاحية للتجارة الإلكترونية والأعمال الرقمية',
                'color': '#059669',
                'icon': 'shopping-cart'
            },
            {
                'name': 'Finance',
                'name_ar': 'خدمات مالية',
                'description': 'Finance, banking, and investment keywords',
                'description_ar': 'كلمات مفتاحية للمالية والبنوك والاستثمار',
                'color': '#DC2626',
                'icon': 'dollar-sign'
            },
            {
                'name': 'Medical',
                'name_ar': 'طب',
                'description': 'Medical and healthcare keywords',
                'description_ar': 'كلمات مفتاحية للطب والرعاية الصحية',
                'color': '#DC2626',
                'icon': 'stethoscope'
            },
            {
                'name': 'Legal',
                'name_ar': 'قانون',
                'description': 'Legal and law keywords',
                'description_ar': 'كلمات مفتاحية للقانون والمحاماة',
                'color': '#1F2937',
                'icon': 'scale'
            },
            {
                'name': 'Engineering',
                'name_ar': 'هندسة',
                'description': 'Engineering and construction keywords',
                'description_ar': 'كلمات مفتاحية للهندسة والبناء',
                'color': '#6B7280',
                'icon': 'cog'
            },
            {
                'name': 'Agriculture',
                'name_ar': 'زراعة',
                'description': 'Agriculture and environment keywords',
                'description_ar': 'كلمات مفتاحية للزراعة والبيئة',
                'color': '#16A34A',
                'icon': 'leaf'
            },
            
            # Trending Categories
            {
                'name': 'Cryptocurrency',
                'name_ar': 'عملات رقمية',
                'description': 'Cryptocurrency and blockchain keywords',
                'description_ar': 'كلمات مفتاحية للعملات الرقمية والبلوك تشين',
                'color': '#F59E0B',
                'icon': 'bitcoin'
            },
            {
                'name': 'Gaming',
                'name_ar': 'ألعاب',
                'description': 'Gaming and esports keywords',
                'description_ar': 'كلمات مفتاحية للألعاب والرياضات الإلكترونية',
                'color': '#8B5CF6',
                'icon': 'gamepad'
            },
            {
                'name': 'Sustainability',
                'name_ar': 'استدامة',
                'description': 'Sustainability and green living keywords',
                'description_ar': 'كلمات مفتاحية للاستدامة والحياة الخضراء',
                'color': '#059669',
                'icon': 'recycle'
            }
        ]
        
        # High-performance hashtags optimized for algorithms
        self.popular_hashtags = {
            'business': [
                # High-engagement business hashtags
                'أعمال', 'ريادة_أعمال', 'استثمار', 'نجاح', 'تطوير_الذات', 'إدارة', 'قيادة', 'مشاريع_ناشئة',
                'تجارة_إلكترونية', 'اقتصاد', 'مال_وأعمال', 'ثروة', 'شركات_ناشئة', 'مؤسسات', 'تمويل',
                'استراتيجية', 'تخطيط', 'إنتاجية', 'فرص_عمل', 'وظائف', 'مهارات', 'تدريب_مهني',
                'business', 'entrepreneur', 'startup', 'success', 'leadership', 'investment', 'growth'
            ],
            'technology': [
                # Trending tech hashtags
                'تقنية', 'تكنولوجيا', 'ذكاء_اصطناعي', 'برمجة', 'تطبيقات', 'مواقع_ويب',
                'انترنت', 'رقمي', 'ابتكار', 'تطوير_تقني', 'حاسوب', 'هواتف_ذكية', 'تقني',
                'بلوك_تشين', 'عملات_رقمية', 'أمن_سيبراني', 'بيانات_ضخمة', 'إنترنت_الأشياء',
                'واقع_افتراضي', 'واقع_معزز', 'تعلم_آلي', 'روبوتات', 'أتمتة',
                'tech', 'ai', 'blockchain', 'coding', 'innovation', 'digital', 'future'
            ],
            'marketing': [
                # High-conversion marketing hashtags
                'تسويق', 'إعلان', 'دعاية', 'ترويج', 'علامة_تجارية', 'عملاء', 'مبيعات',
                'تسويق_رقمي', 'سوشيال_ميديا', 'محتوى_تسويقي', 'استراتيجية_تسويق', 'حملة_إعلانية',
                'تسويق_بالمحتوى', 'تسويق_بالفيديو', 'تسويق_بالمؤثرين', 'سيو', 'جوجل_ادز',
                'فيسبوك_ادز', 'انستجرام_ادز', 'تحليلات', 'معدل_التحويل', 'عائد_الاستثمار',
                'marketing', 'advertising', 'branding', 'socialmedia', 'content', 'seo', 'ads'
            ],
            'health': [
                # Wellness and health hashtags
                'صحة', 'طب', 'علاج', 'وقاية', 'لياقة_بدنية', 'رياضة', 'تغذية_صحية', 'طبيعي',
                'عافية', 'صحي', 'طبي', 'مستشفى', 'دواء', 'فيتامينات', 'مكملات_غذائية',
                'صحة_نفسية', 'تأمل', 'يوجا', 'تمارين', 'حمية', 'إنقاص_الوزن', 'بناء_عضلات',
                'طب_بديل', 'أعشاب_طبية', 'صحة_المرأة', 'صحة_الطفل', 'صحة_كبار_السن',
                'health', 'fitness', 'wellness', 'nutrition', 'medical', 'healthy', 'workout'
            ],
            'education': [
                # Educational content hashtags
                'تعليم', 'تعلم', 'دراسة', 'جامعة', 'مدرسة', 'طلاب', 'معلم', 'أستاذ',
                'كتاب', 'قراءة', 'علم', 'معرفة', 'ثقافة', 'تدريب', 'دورة_تدريبية',
                'تعليم_إلكتروني', 'تعلم_عن_بعد', 'مهارات', 'شهادات', 'دبلوم', 'ماجستير',
                'دكتوراه', 'بحث_علمي', 'مؤتمر', 'ورشة_عمل', 'ندوة', 'محاضرة',
                'education', 'learning', 'study', 'knowledge', 'skills', 'training', 'course'
            ],
            'entertainment': [
                # Entertainment and lifestyle hashtags
                'ترفيه', 'فن', 'موسيقى', 'فيلم', 'مسلسل', 'لعبة', 'سفر', 'سياحة',
                'طبخ', 'موضة', 'جمال', 'هوايات', 'رياضة_ترفيهية', 'نشاطات', 'مرح',
                'كوميديا', 'مسرح', 'سينما', 'تلفزيون', 'راديو', 'بودكاست', 'يوتيوب',
                'تيك_توك', 'انستجرام', 'سناب_شات', 'تويتر', 'فيسبوك', 'لايف',
                'entertainment', 'fun', 'music', 'movie', 'travel', 'lifestyle', 'comedy'
            ],
            'food': [
                # Food and restaurant hashtags
                'طعام', 'طبخ', 'وصفات', 'مطعم', 'شيف', 'أكل_صحي', 'حلويات', 'مشروبات',
                'إفطار', 'غداء', 'عشاء', 'وجبة_خفيفة', 'مأكولات_شعبية', 'مطبخ_عربي',
                'مطبخ_عالمي', 'نباتي', 'كيتو', 'دايت', 'بروتين', 'كربوهيدرات',
                'طعام_عضوي', 'مكونات_طبيعية', 'توصيل_طعام', 'مراجعة_مطعم',
                'food', 'cooking', 'recipe', 'restaurant', 'chef', 'healthy', 'delicious'
            ],
            'travel': [
                # Travel and tourism hashtags
                'سفر', 'سياحة', 'رحلة', 'إجازة', 'عطلة', 'مغامرة', 'استكشاف', 'وجهة_سياحية',
                'فندق', 'منتجع', 'شاطئ', 'جبال', 'صحراء', 'مدينة', 'قرية', 'تراث',
                'ثقافة_محلية', 'طيران', 'مطار', 'حجز', 'تذكرة', 'جواز_سفر', 'فيزا',
                'حقيبة_سفر', 'تصوير_سفر', 'مدون_سفر', 'نصائح_سفر', 'ميزانية_سفر',
                'travel', 'tourism', 'vacation', 'adventure', 'explore', 'destination', 'trip'
            ],
            'sports': [
                # Sports and fitness hashtags
                'رياضة', 'لياقة', 'تمارين', 'جيم', 'كمال_أجسام', 'كارديو', 'يوجا', 'بيلاتس',
                'جري', 'مشي', 'سباحة', 'كرة_قدم', 'كرة_سلة', 'تنس', 'جولف', 'ملاكمة',
                'فنون_قتالية', 'تايكوندو', 'كاراتيه', 'مصارعة', 'رفع_أثقال', 'كروس_فيت',
                'تحدي_رياضي', 'ماراثون', 'سباق', 'بطولة', 'فريق', 'لاعب', 'مدرب',
                'sports', 'fitness', 'workout', 'gym', 'training', 'athlete', 'competition'
            ],
            'fashion': [
                # Fashion and beauty hashtags
                'موضة', 'أزياء', 'ستايل', 'جمال', 'مكياج', 'عناية_بالبشرة', 'عطور', 'إكسسوارات',
                'حقائب', 'أحذية', 'ملابس', 'فساتين', 'بدلات', 'كاجوال', 'رسمي', 'عصري',
                'كلاسيكي', 'عتيق', 'مصمم_أزياء', 'عارضة_أزياء', 'تسريحة_شعر', 'أظافر',
                'تجميل', 'سبا', 'صالون', 'علاج_تجميلي', 'منتجات_طبيعية', 'عضوي',
                'fashion', 'style', 'beauty', 'makeup', 'skincare', 'outfit', 'trendy'
            ]
        }
        
        # Trending keywords patterns
        self.trending_patterns = {
            'seasonal': {
                'ramadan': ['رمضان', 'إفطار', 'سحور', 'صيام', 'عيد', 'روحانية'],
                'summer': ['صيف', 'إجازة', 'سفر', 'بحر', 'شاطئ', 'عطلة'],
                'winter': ['شتاء', 'برد', 'دفء', 'مطر', 'ثلج', 'شوربة'],
                'eid': ['عيد', 'فرحة', 'احتفال', 'هدايا', 'عائلة', 'تهنئة']
            },
            'events': {
                'world_cup': ['كأس_العالم', 'فيفا', 'كرة_قدم', 'منتخب', 'مباراة'],
                'olympics': ['أولمبياد', 'رياضة', 'ميداليات', 'بطولة', 'رياضيين'],
                'new_year': ['سنة_جديدة', 'احتفال', 'قرارات', 'أهداف', 'تفاؤل']
            }
        }
    
    def initialize_default_categories(self):
        """Initialize default keyword categories"""
        try:
            existing_categories = KeywordCategory.query.count()
            
            if existing_categories == 0:
                for cat_data in self.default_categories:
                    category = KeywordCategory(
                        name=cat_data['name'],
                        name_ar=cat_data['name_ar'],
                        description=cat_data['description'],
                        description_ar=cat_data['description_ar'],
                        color=cat_data['color'],
                        icon=cat_data['icon']
                    )
                    category.save()
                
                logger.info("Default keyword categories initialized")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error initializing default categories: {str(e)}")
            return False
    
    def create_keyword(self, keyword_data: Dict) -> Dict:
        """Create a new keyword"""
        try:
            # Check if keyword already exists
            existing_keyword = Keyword.query.filter_by(
                keyword=keyword_data['keyword'].lower().strip()
            ).first()
            
            if existing_keyword:
                return {
                    'success': False,
                    'error': 'Keyword already exists',
                    'existing_keyword': existing_keyword.to_dict()
                }
            
            # Create keyword
            keyword = Keyword(**keyword_data)
            keyword.save()
            
            logger.info(f"Created keyword: {keyword.keyword}")
            
            return {
                'success': True,
                'keyword': keyword.to_dict(),
                'message': 'Keyword created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating keyword: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_hashtag(self, hashtag_data: Dict) -> Dict:
        """Create a new hashtag"""
        try:
            # Clean hashtag
            hashtag_text = hashtag_data['hashtag'].replace('#', '').lower().strip()
            
            # Check if hashtag already exists
            existing_hashtag = Hashtag.query.filter_by(hashtag=hashtag_text).first()
            
            if existing_hashtag:
                return {
                    'success': False,
                    'error': 'Hashtag already exists',
                    'existing_hashtag': existing_hashtag.to_dict()
                }
            
            # Create hashtag
            hashtag_data['hashtag'] = hashtag_text
            hashtag = Hashtag(**hashtag_data)
            hashtag.save()
            
            logger.info(f"Created hashtag: #{hashtag.hashtag}")
            
            return {
                'success': True,
                'hashtag': hashtag.to_dict(),
                'message': 'Hashtag created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating hashtag: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def suggest_keywords(self, content_text: str, industry: str = None, 
                        language: str = 'ar', limit: int = 10) -> Dict:
        """Suggest relevant keywords for content"""
        try:
            suggestions = []
            
            # Extract potential keywords from content
            content_keywords = self.extract_keywords_from_text(content_text, language)
            
            # Get existing keywords that match content
            existing_keywords = Keyword.query.filter(
                Keyword.language == language,
                Keyword.is_active == True
            )
            
            if industry:
                existing_keywords = existing_keywords.filter(
                    Keyword.industry == industry
                )
            
            existing_keywords = existing_keywords.all()
            
            # Calculate relevance scores
            for keyword in existing_keywords:
                relevance_score = keyword.calculate_relevance_score(content_text)
                if relevance_score > 0:
                    keyword_dict = keyword.to_dict()
                    keyword_dict['relevance_score'] = relevance_score
                    suggestions.append(keyword_dict)
            
            # Sort by relevance score
            suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Add AI-generated keyword suggestions
            ai_suggestions = self.generate_ai_keywords(content_text, industry, language)
            
            return {
                'success': True,
                'content_keywords': content_keywords[:limit],
                'existing_keywords': suggestions[:limit],
                'ai_suggestions': ai_suggestions[:limit],
                'total_suggestions': len(suggestions) + len(ai_suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error suggesting keywords: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def suggest_hashtags(self, content_text: str, platform: str = 'instagram',
                        industry: str = None, language: str = 'ar', limit: int = 15) -> Dict:
        """Suggest relevant hashtags for content"""
        try:
            suggestions = []
            
            # Get trending hashtags
            trending_hashtags = self.get_trending_hashtags(platform, language, limit=5)
            
            # Get industry-specific hashtags
            if industry and industry in self.popular_hashtags:
                industry_hashtags = self.popular_hashtags[industry][:10]
            else:
                industry_hashtags = []
            
            # Get existing hashtags that match content
            existing_hashtags = Hashtag.query.filter(
                Hashtag.language == language,
                Hashtag.is_active == True,
                Hashtag.is_banned == False
            )
            
            if industry:
                existing_hashtags = existing_hashtags.filter(
                    Hashtag.industry == industry
                )
            
            existing_hashtags = existing_hashtags.order_by(
                Hashtag.popularity_score.desc()
            ).limit(limit).all()
            
            # Generate AI hashtag suggestions
            ai_hashtags = self.generate_ai_hashtags(content_text, platform, language)
            
            return {
                'success': True,
                'trending_hashtags': trending_hashtags,
                'industry_hashtags': [{'hashtag': tag, 'formatted': f'#{tag}'} for tag in industry_hashtags],
                'existing_hashtags': [hashtag.to_dict() for hashtag in existing_hashtags],
                'ai_suggestions': ai_hashtags,
                'platform_recommendations': self.get_platform_specific_recommendations(platform)
            }
            
        except Exception as e:
            logger.error(f"Error suggesting hashtags: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_keywords_from_text(self, text: str, language: str = 'ar') -> List[str]:
        """Extract potential keywords from text"""
        try:
            # Clean text
            text = re.sub(r'[^\w\s]', ' ', text)
            words = text.split()
            
            # Filter words
            keywords = []
            for word in words:
                word = word.strip().lower()
                
                # Skip short words and common words
                if len(word) < 3:
                    continue
                
                # Skip common Arabic stop words
                arabic_stop_words = [
                    'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
                    'التي', 'الذي', 'التي', 'كان', 'كانت', 'يكون', 'تكون', 'لكن', 'لكن'
                ]
                
                if language == 'ar' and word in arabic_stop_words:
                    continue
                
                keywords.append(word)
            
            # Count frequency and return most common
            word_freq = Counter(keywords)
            return [word for word, count in word_freq.most_common(20)]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def generate_ai_keywords(self, content_text: str, industry: str = None, 
                           language: str = 'ar') -> List[Dict]:
        """Generate AI-powered keyword suggestions"""
        try:
            # Create prompt for AI keyword generation
            if language == 'ar':
                prompt = f"""
                اقترح 10 كلمات مفتاحية مناسبة للمحتوى التالي:
                
                المحتوى: {content_text[:500]}
                
                {"الصناعة: " + industry if industry else ""}
                
                يجب أن تكون الكلمات المفتاحية:
                - مناسبة للمحتوى
                - شائعة في البحث
                - مفيدة لتحسين محركات البحث
                
                اكتب الكلمات المفتاحية فقط، مفصولة بفواصل.
                """
            else:
                prompt = f"""
                Suggest 10 relevant keywords for the following content:
                
                Content: {content_text[:500]}
                
                {"Industry: " + industry if industry else ""}
                
                Keywords should be:
                - Relevant to the content
                - Popular in search
                - Useful for SEO
                
                Write only the keywords, separated by commas.
                """
            
            # Generate keywords using AI
            ai_result = free_ai_generator.generate_text(prompt, max_length=200)
            
            if ai_result['success']:
                keywords_text = ai_result['text']
                keywords = [kw.strip() for kw in keywords_text.split(',')]
                
                # Format keywords
                formatted_keywords = []
                for keyword in keywords[:10]:
                    if keyword:
                        formatted_keywords.append({
                            'keyword': keyword.lower(),
                            'source': 'ai_generated',
                            'confidence': 0.8,
                            'suggested_industry': industry
                        })
                
                return formatted_keywords
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating AI keywords: {str(e)}")
            return []
    
    def generate_ai_hashtags(self, content_text: str, platform: str = 'instagram',
                           language: str = 'ar') -> List[Dict]:
        """Generate AI-powered hashtag suggestions"""
        try:
            # Create prompt for AI hashtag generation
            if language == 'ar':
                prompt = f"""
                اقترح 15 هاشتاج مناسب للمحتوى التالي على منصة {platform}:
                
                المحتوى: {content_text[:500]}
                
                يجب أن تكون الهاشتاجات:
                - مناسبة للمحتوى والمنصة
                - شائعة ومتداولة
                - متنوعة (عامة ومتخصصة)
                - باللغة العربية
                
                اكتب الهاشتاجات بدون رمز #، مفصولة بفواصل.
                """
            else:
                prompt = f"""
                Suggest 15 relevant hashtags for the following content on {platform}:
                
                Content: {content_text[:500]}
                
                Hashtags should be:
                - Relevant to content and platform
                - Popular and trending
                - Mix of general and specific
                - In English
                
                Write hashtags without # symbol, separated by commas.
                """
            
            # Generate hashtags using AI
            ai_result = free_ai_generator.generate_text(prompt, max_length=300)
            
            if ai_result['success']:
                hashtags_text = ai_result['text']
                hashtags = [tag.strip() for tag in hashtags_text.split(',')]
                
                # Format hashtags
                formatted_hashtags = []
                for hashtag in hashtags[:15]:
                    if hashtag:
                        clean_hashtag = hashtag.replace('#', '').strip()
                        formatted_hashtags.append({
                            'hashtag': clean_hashtag,
                            'formatted': f'#{clean_hashtag}',
                            'source': 'ai_generated',
                            'platform': platform,
                            'confidence': 0.8
                        })
                
                return formatted_hashtags
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating AI hashtags: {str(e)}")
            return []
    
    def get_trending_hashtags(self, platform: str = 'instagram', 
                            language: str = 'ar', limit: int = 10) -> List[Dict]:
        """Get trending hashtags for a platform"""
        try:
            # Get trending hashtags from database
            trending_hashtags = Hashtag.query.filter(
                Hashtag.is_trending == True,
                Hashtag.is_active == True,
                Hashtag.is_banned == False,
                Hashtag.language == language
            ).order_by(Hashtag.popularity_score.desc()).limit(limit).all()
            
            # If no trending hashtags in database, return popular ones
            if not trending_hashtags:
                popular_hashtags = Hashtag.query.filter(
                    Hashtag.is_active == True,
                    Hashtag.is_banned == False,
                    Hashtag.language == language
                ).order_by(Hashtag.usage_count.desc()).limit(limit).all()
                
                return [hashtag.to_dict() for hashtag in popular_hashtags]
            
            return [hashtag.to_dict() for hashtag in trending_hashtags]
            
        except Exception as e:
            logger.error(f"Error getting trending hashtags: {str(e)}")
            return []
    
    def get_platform_specific_recommendations(self, platform: str) -> Dict:
        """Get platform-specific hashtag recommendations"""
        recommendations = {
            'instagram': {
                'optimal_count': '8-15 hashtags',
                'tips': [
                    'استخدم مزيج من الهاشتاجات الشائعة والمتخصصة',
                    'تجنب الهاشتاجات المحظورة',
                    'استخدم هاشتاجات متعلقة بالموقع الجغرافي'
                ],
                'best_practices': [
                    'ضع الهاشتاجات في التعليق الأول',
                    'استخدم هاشتاجات ذات صلة بالمحتوى',
                    'تابع أداء الهاشتاجات وحدثها'
                ]
            },
            'twitter': {
                'optimal_count': '1-3 hashtags',
                'tips': [
                    'استخدم هاشتاجات قصيرة ومفهومة',
                    'تابع الترندات الحالية',
                    'استخدم هاشتاجات الأحداث الجارية'
                ],
                'best_practices': [
                    'ضع الهاشتاجات في نص التغريدة',
                    'تجنب الإفراط في الهاشتاجات',
                    'استخدم هاشتاجات ذات صلة بالموضوع'
                ]
            },
            'linkedin': {
                'optimal_count': '3-5 hashtags',
                'tips': [
                    'استخدم هاشتاجات مهنية',
                    'ركز على الصناعة والمهارات',
                    'استخدم هاشتاجات الشركة'
                ],
                'best_practices': [
                    'ضع الهاشتاجات في نهاية المنشور',
                    'استخدم هاشتاجات متعلقة بالعمل',
                    'تابع هاشتاجات الصناعة'
                ]
            },
            'tiktok': {
                'optimal_count': '3-8 hashtags',
                'tips': [
                    'استخدم هاشتاجات ترندية',
                    'امزج بين العامة والمتخصصة',
                    'استخدم هاشتاجات التحديات'
                ],
                'best_practices': [
                    'ضع الهاشتاجات في الوصف',
                    'تابع الترندات اليومية',
                    'استخدم هاشتاجات إبداعية'
                ]
            }
        }
        
        return recommendations.get(platform, {
            'optimal_count': '5-10 hashtags',
            'tips': ['استخدم هاشتاجات مناسبة للمحتوى'],
            'best_practices': ['تابع أداء الهاشتاجات']
        })
    
    def analyze_keyword_performance(self, keyword_id: int, days: int = 30) -> Dict:
        """Analyze keyword performance"""
        try:
            keyword = Keyword.query.get(keyword_id)
            if not keyword:
                return {'success': False, 'error': 'Keyword not found'}
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get content using this keyword
            content_keywords = ContentKeyword.query.filter(
                ContentKeyword.keyword_id == keyword_id,
                ContentKeyword.created_at >= start_date
            ).all()
            
            # Calculate performance metrics
            total_usage = len(content_keywords)
            avg_relevance = sum(ck.relevance_score for ck in content_keywords) / total_usage if total_usage > 0 else 0
            
            # Get content performance data
            content_ids = [ck.content_id for ck in content_keywords]
            if content_ids:
                contents = Content.query.filter(Content.id.in_(content_ids)).all()
                # Here you would calculate actual performance metrics from social media APIs
                # For now, we'll simulate the data
                avg_engagement = 150  # Simulated
                avg_reach = 1000  # Simulated
            else:
                avg_engagement = 0
                avg_reach = 0
            
            return {
                'success': True,
                'keyword': keyword.to_dict(),
                'performance': {
                    'total_usage': total_usage,
                    'average_relevance_score': round(avg_relevance, 2),
                    'average_engagement': avg_engagement,
                    'average_reach': avg_reach,
                    'performance_trend': 'improving' if keyword.performance_score > 50 else 'stable',
                    'recommendation': self.get_keyword_recommendation(keyword, avg_relevance, total_usage)
                },
                'usage_history': [ck.to_dict() for ck in content_keywords[-10:]]  # Last 10 uses
            }
            
        except Exception as e:
            logger.error(f"Error analyzing keyword performance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_keyword_recommendation(self, keyword: Keyword, avg_relevance: float, usage_count: int) -> str:
        """Get recommendation for keyword usage"""
        if usage_count == 0:
            return "لم يتم استخدام هذه الكلمة المفتاحية بعد. جرب استخدامها في المحتوى القادم."
        
        if avg_relevance > 80:
            return "كلمة مفتاحية ممتازة! استمر في استخدامها."
        elif avg_relevance > 60:
            return "كلمة مفتاحية جيدة. يمكن تحسين الاستخدام."
        elif avg_relevance > 40:
            return "كلمة مفتاحية متوسطة. فكر في البدائل."
        else:
            return "كلمة مفتاحية ضعيفة. ابحث عن بدائل أفضل."
    
    def update_trending_topics(self) -> Dict:
        """Update trending topics and keywords"""
        try:
            # This would typically fetch from external APIs
            # For now, we'll simulate trending topics
            
            current_trends = [
                {
                    'topic': 'الذكاء الاصطناعي',
                    'topic_ar': 'الذكاء الاصطناعي',
                    'trend_score': 95.0,
                    'category': 'technology',
                    'related_keywords': ['ذكاء اصطناعي', 'تقنية', 'مستقبل', 'ابتكار'],
                    'related_hashtags': ['ذكاء_اصطناعي', 'تقنية', 'مستقبل', 'ابتكار']
                },
                {
                    'topic': 'ريادة الأعمال',
                    'topic_ar': 'ريادة الأعمال',
                    'trend_score': 88.0,
                    'category': 'business',
                    'related_keywords': ['ريادة', 'أعمال', 'استثمار', 'نجاح'],
                    'related_hashtags': ['ريادة_أعمال', 'استثمار', 'نجاح', 'مشاريع']
                },
                {
                    'topic': 'التسويق الرقمي',
                    'topic_ar': 'التسويق الرقمي',
                    'trend_score': 82.0,
                    'category': 'marketing',
                    'related_keywords': ['تسويق رقمي', 'سوشيال ميديا', 'إعلان', 'محتوى'],
                    'related_hashtags': ['تسويق_رقمي', 'سوشيال_ميديا', 'محتوى', 'إعلان']
                }
            ]
            
            updated_count = 0
            
            for trend_data in current_trends:
                # Check if trend already exists
                existing_trend = TrendingTopic.query.filter_by(
                    topic=trend_data['topic']
                ).first()
                
                if existing_trend:
                    # Update existing trend
                    existing_trend.trend_score = trend_data['trend_score']
                    existing_trend.updated_at = datetime.utcnow()
                    existing_trend.save()
                else:
                    # Create new trend
                    trend = TrendingTopic(
                        topic=trend_data['topic'],
                        topic_ar=trend_data['topic_ar'],
                        trend_score=trend_data['trend_score'],
                        category=trend_data['category'],
                        related_keywords=json.dumps(trend_data['related_keywords']),
                        related_hashtags=json.dumps(trend_data['related_hashtags'])
                    )
                    trend.save()
                
                updated_count += 1
            
            return {
                'success': True,
                'updated_trends': updated_count,
                'message': f'Updated {updated_count} trending topics'
            }
            
        except Exception as e:
            logger.error(f"Error updating trending topics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_content_optimization_suggestions(self, content_id: int) -> Dict:
        """Get optimization suggestions for content"""
        try:
            content = Content.query.get(content_id)
            if not content:
                return {'success': False, 'error': 'Content not found'}
            
            content_data = content.content_data or {}
            content_text = content_data.get('text', '')
            
            if not content_text:
                return {'success': False, 'error': 'No text content found'}
            
            # Get current keywords and hashtags
            current_keywords = ContentKeyword.query.filter_by(content_id=content_id).all()
            current_hashtags = ContentHashtag.query.filter_by(content_id=content_id).all()
            
            # Suggest improvements
            keyword_suggestions = self.suggest_keywords(content_text, limit=5)
            hashtag_suggestions = self.suggest_hashtags(content_text, content.platform, limit=10)
            
            # Analyze content structure
            word_count = len(content_text.split())
            
            suggestions = {
                'success': True,
                'content_analysis': {
                    'word_count': word_count,
                    'current_keywords': len(current_keywords),
                    'current_hashtags': len(current_hashtags),
                    'readability_score': self.calculate_readability_score(content_text)
                },
                'keyword_suggestions': keyword_suggestions,
                'hashtag_suggestions': hashtag_suggestions,
                'optimization_tips': self.get_optimization_tips(content_text, content.platform),
                'seo_score': self.calculate_seo_score(content_text, current_keywords)
            }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting optimization suggestions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate readability score for Arabic text"""
        try:
            # Simple readability calculation for Arabic
            sentences = text.split('.')
            words = text.split()
            
            if len(sentences) == 0 or len(words) == 0:
                return 0.0
            
            avg_sentence_length = len(words) / len(sentences)
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # Simple scoring (higher is better)
            score = 100 - (avg_sentence_length * 2) - (avg_word_length * 3)
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating readability: {str(e)}")
            return 50.0
    
    def calculate_seo_score(self, text: str, keywords: List[ContentKeyword]) -> float:
        """Calculate SEO score for content"""
        try:
            score = 0.0
            
            # Keyword density score
            if keywords:
                total_relevance = sum(kw.relevance_score for kw in keywords)
                score += min(total_relevance / len(keywords), 30)
            
            # Content length score
            word_count = len(text.split())
            if 100 <= word_count <= 500:
                score += 20
            elif word_count > 500:
                score += 15
            else:
                score += 10
            
            # Structure score (simple check for headings, lists, etc.)
            if any(marker in text for marker in ['#', '•', '-', '1.', '2.']):
                score += 15
            
            # Call-to-action score
            cta_words = ['اشترك', 'تابع', 'شارك', 'اضغط', 'زر', 'رابط']
            if any(word in text for word in cta_words):
                score += 10
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating SEO score: {str(e)}")
            return 50.0
    
    def get_optimization_tips(self, text: str, platform: str) -> List[str]:
        """Get optimization tips for content"""
        tips = []
        
        word_count = len(text.split())
        
        # Platform-specific tips
        if platform == 'instagram':
            if word_count > 300:
                tips.append("قلل من طول النص - انستجرام يفضل المحتوى المختصر")
            tips.append("أضف دعوة واضحة للعمل")
            tips.append("استخدم الإيموجي لجذب الانتباه")
            
        elif platform == 'twitter':
            if word_count > 50:
                tips.append("اختصر النص ليناسب تويتر")
            tips.append("استخدم هاشتاجات ترندية")
            
        elif platform == 'linkedin':
            if word_count < 100:
                tips.append("أضف المزيد من التفاصيل المهنية")
            tips.append("استخدم لغة مهنية")
            tips.append("أضف رؤى من الصناعة")
        
        # General tips
        if not any(marker in text for marker in ['؟', '!']):
            tips.append("أضف أسئلة أو علامات تعجب لزيادة التفاعل")
        
        if 'http' not in text:
            tips.append("فكر في إضافة رابط مفيد")
        
        return tips

# Global keyword manager instance
keyword_manager = KeywordManager()

