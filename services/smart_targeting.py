import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import google.generativeai as genai
import os
from src.models.user import User
from src.models.content import Content
from src.models.task import Task
from src.services.ai_content_generator import ai_content_generator
from src.services.external_api_integration import api_integration

logger = logging.getLogger(__name__)

class SmartTargeting:
    """Advanced Smart Targeting and Campaign Optimization System"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        
        # Target audience segments with detailed profiles
        self.audience_segments = {
            'small_business_owners': {
                'name_ar': 'أصحاب الأعمال الصغيرة',
                'name_en': 'Small Business Owners',
                'demographics': {
                    'age_range': '25-45',
                    'interests': ['entrepreneurship', 'business_growth', 'marketing', 'sales'],
                    'pain_points': ['limited_budget', 'time_constraints', 'marketing_knowledge', 'competition'],
                    'goals': ['increase_sales', 'brand_awareness', 'customer_acquisition', 'efficiency']
                },
                'preferred_platforms': ['facebook', 'instagram', 'linkedin'],
                'content_preferences': ['educational', 'case_studies', 'tips', 'tools'],
                'messaging_style': 'practical_actionable',
                'best_posting_times': ['09:00', '12:00', '18:00']
            },
            'marketing_professionals': {
                'name_ar': 'المسوقين المحترفين',
                'name_en': 'Marketing Professionals',
                'demographics': {
                    'age_range': '25-40',
                    'interests': ['digital_marketing', 'automation', 'analytics', 'trends'],
                    'pain_points': ['manual_tasks', 'reporting', 'roi_measurement', 'tool_integration'],
                    'goals': ['automation', 'efficiency', 'better_results', 'career_growth']
                },
                'preferred_platforms': ['linkedin', 'twitter', 'facebook'],
                'content_preferences': ['industry_insights', 'tools', 'strategies', 'data'],
                'messaging_style': 'professional_data_driven',
                'best_posting_times': ['08:00', '13:00', '17:00']
            },
            'enterprise_companies': {
                'name_ar': 'الشركات الكبيرة',
                'name_en': 'Enterprise Companies',
                'demographics': {
                    'age_range': '30-55',
                    'interests': ['scalability', 'integration', 'security', 'compliance'],
                    'pain_points': ['complex_workflows', 'team_coordination', 'data_silos', 'cost_management'],
                    'goals': ['scalability', 'integration', 'team_efficiency', 'cost_reduction']
                },
                'preferred_platforms': ['linkedin', 'youtube', 'facebook'],
                'content_preferences': ['whitepapers', 'case_studies', 'webinars', 'demos'],
                'messaging_style': 'formal_comprehensive',
                'best_posting_times': ['10:00', '14:00', '16:00']
            },
            'ecommerce_owners': {
                'name_ar': 'أصحاب المتاجر الإلكترونية',
                'name_en': 'E-commerce Owners',
                'demographics': {
                    'age_range': '25-50',
                    'interests': ['online_sales', 'customer_retention', 'conversion', 'inventory'],
                    'pain_points': ['cart_abandonment', 'customer_acquisition', 'competition', 'seasonality'],
                    'goals': ['increase_conversions', 'customer_retention', 'brand_loyalty', 'revenue_growth']
                },
                'preferred_platforms': ['facebook', 'instagram', 'tiktok', 'youtube'],
                'content_preferences': ['product_showcases', 'customer_reviews', 'tutorials', 'promotions'],
                'messaging_style': 'engaging_visual',
                'best_posting_times': ['11:00', '15:00', '19:00']
            },
            'content_creators': {
                'name_ar': 'منشئي المحتوى',
                'name_en': 'Content Creators',
                'demographics': {
                    'age_range': '18-35',
                    'interests': ['creativity', 'audience_growth', 'monetization', 'trends'],
                    'pain_points': ['content_consistency', 'engagement', 'monetization', 'burnout'],
                    'goals': ['audience_growth', 'engagement', 'monetization', 'efficiency']
                },
                'preferred_platforms': ['tiktok', 'instagram', 'youtube', 'twitter'],
                'content_preferences': ['behind_scenes', 'tips', 'trends', 'collaborations'],
                'messaging_style': 'casual_authentic',
                'best_posting_times': ['16:00', '20:00', '22:00']
            },
            'restaurants_cafes': {
                'name_ar': 'المطاعم والمقاهي',
                'name_en': 'Restaurants & Cafes',
                'demographics': {
                    'age_range': '25-55',
                    'interests': ['food_quality', 'customer_experience', 'local_marketing', 'reviews'],
                    'pain_points': ['seasonal_fluctuations', 'competition', 'staff_management', 'online_presence'],
                    'goals': ['customer_acquisition', 'repeat_business', 'brand_recognition', 'revenue_stability']
                },
                'preferred_platforms': ['facebook', 'instagram', 'google_my_business'],
                'content_preferences': ['food_photos', 'behind_scenes', 'customer_testimonials', 'events'],
                'messaging_style': 'warm_inviting',
                'best_posting_times': ['12:00', '17:00', '19:00']
            },
            'fitness_wellness': {
                'name_ar': 'اللياقة والصحة',
                'name_en': 'Fitness & Wellness',
                'demographics': {
                    'age_range': '20-45',
                    'interests': ['health', 'fitness', 'nutrition', 'lifestyle'],
                    'pain_points': ['motivation', 'consistency', 'results', 'time_management'],
                    'goals': ['health_improvement', 'fitness_goals', 'lifestyle_change', 'community']
                },
                'preferred_platforms': ['instagram', 'tiktok', 'youtube', 'facebook'],
                'content_preferences': ['workouts', 'nutrition_tips', 'transformations', 'motivation'],
                'messaging_style': 'motivational_supportive',
                'best_posting_times': ['06:00', '12:00', '18:00']
            },
            'tech_startups': {
                'name_ar': 'الشركات التقنية الناشئة',
                'name_en': 'Tech Startups',
                'demographics': {
                    'age_range': '25-40',
                    'interests': ['innovation', 'technology', 'growth', 'funding'],
                    'pain_points': ['user_acquisition', 'product_market_fit', 'funding', 'competition'],
                    'goals': ['user_growth', 'product_adoption', 'brand_awareness', 'funding']
                },
                'preferred_platforms': ['linkedin', 'twitter', 'youtube', 'reddit'],
                'content_preferences': ['product_updates', 'tech_insights', 'founder_stories', 'tutorials'],
                'messaging_style': 'innovative_technical',
                'best_posting_times': ['09:00', '14:00', '17:00']
            }
        }
        
        # Campaign optimization strategies
        self.optimization_strategies = {
            'audience_refinement': {
                'name_ar': 'تحسين الجمهور المستهدف',
                'name_en': 'Audience Refinement',
                'description_ar': 'تحليل وتحسين استهداف الجمهور بناءً على البيانات',
                'description_en': 'Analyze and optimize audience targeting based on data'
            },
            'content_optimization': {
                'name_ar': 'تحسين المحتوى',
                'name_en': 'Content Optimization',
                'description_ar': 'تحسين المحتوى لزيادة التفاعل والتحويل',
                'description_en': 'Optimize content for better engagement and conversion'
            },
            'timing_optimization': {
                'name_ar': 'تحسين التوقيت',
                'name_en': 'Timing Optimization',
                'description_ar': 'تحديد أفضل أوقات النشر والتفاعل',
                'description_en': 'Determine optimal posting and engagement times'
            },
            'platform_optimization': {
                'name_ar': 'تحسين المنصات',
                'name_en': 'Platform Optimization',
                'description_ar': 'اختيار وتحسين المنصات الأكثر فعالية',
                'description_en': 'Select and optimize most effective platforms'
            },
            'budget_optimization': {
                'name_ar': 'تحسين الميزانية',
                'name_en': 'Budget Optimization',
                'description_ar': 'توزيع الميزانية بشكل أمثل لتحقيق أفضل عائد',
                'description_en': 'Optimize budget allocation for best ROI'
            }
        }
    
    async def analyze_target_audience(self, business_data: Dict) -> Dict:
        """Analyze and identify target audience for a business"""
        
        try:
            business_type = business_data.get('business_type', '')
            product_service = business_data.get('product_service', '')
            current_customers = business_data.get('current_customers', '')
            goals = business_data.get('goals', [])
            language = business_data.get('language', 'ar')
            
            # Build audience analysis prompt
            if language == 'ar':
                prompt = f"""أنت خبير في تحليل الجمهور المستهدف والتسويق الرقمي.

معلومات العمل:
- نوع العمل: {business_type}
- المنتج/الخدمة: {product_service}
- العملاء الحاليين: {current_customers}
- الأهداف: {', '.join(goals)}

مهمتك:
1. تحليل الجمهور المستهدف الأمثل لهذا العمل
2. تحديد الخصائص الديموغرافية والسيكوغرافية
3. تحديد نقاط الألم والاحتياجات
4. اقتراح أفضل المنصات للوصول لهذا الجمهور
5. تحديد أفضل أوقات التفاعل
6. اقتراح أسلوب المراسلة المناسب

قدم تحليلاً شاملاً ومفصلاً:"""
            else:
                prompt = f"""You are an expert in target audience analysis and digital marketing.

Business Information:
- Business Type: {business_type}
- Product/Service: {product_service}
- Current Customers: {current_customers}
- Goals: {', '.join(goals)}

Your Task:
1. Analyze the optimal target audience for this business
2. Define demographic and psychographic characteristics
3. Identify pain points and needs
4. Suggest best platforms to reach this audience
5. Determine optimal engagement times
6. Recommend appropriate messaging style

Provide comprehensive and detailed analysis:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                analysis_text = result['data'].get('text', '')
                
                # Match with predefined segments
                matched_segments = self.match_audience_segments(business_data)
                
                # Generate targeting recommendations
                targeting_recommendations = await self.generate_targeting_recommendations(business_data, matched_segments)
                
                return {
                    'success': True,
                    'analysis': analysis_text,
                    'matched_segments': matched_segments,
                    'targeting_recommendations': targeting_recommendations,
                    'business_type': business_type,
                    'language': language
                }
            else:
                return {'success': False, 'error': result.get('error')}
            
        except Exception as e:
            logger.error(f"Error analyzing target audience: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def match_audience_segments(self, business_data: Dict) -> List[Dict]:
        """Match business with predefined audience segments"""
        
        business_type = business_data.get('business_type', '').lower()
        product_service = business_data.get('product_service', '').lower()
        
        matched_segments = []
        
        for segment_id, segment in self.audience_segments.items():
            score = 0
            
            # Check business type alignment
            if any(interest in business_type or interest in product_service 
                   for interest in segment['demographics']['interests']):
                score += 30
            
            # Check specific business type matches
            if 'small' in business_type and 'business' in business_type and segment_id == 'small_business_owners':
                score += 40
            elif 'marketing' in business_type and segment_id == 'marketing_professionals':
                score += 40
            elif 'enterprise' in business_type or 'large' in business_type and segment_id == 'enterprise_companies':
                score += 40
            elif 'ecommerce' in business_type or 'online' in business_type and segment_id == 'ecommerce_owners':
                score += 40
            elif 'content' in business_type and segment_id == 'content_creators':
                score += 40
            elif 'restaurant' in business_type or 'cafe' in business_type and segment_id == 'restaurants_cafes':
                score += 40
            elif 'fitness' in business_type or 'health' in business_type and segment_id == 'fitness_wellness':
                score += 40
            elif 'tech' in business_type or 'startup' in business_type and segment_id == 'tech_startups':
                score += 40
            
            if score > 20:  # Minimum threshold
                matched_segments.append({
                    'segment_id': segment_id,
                    'segment_name': segment['name_ar'],
                    'score': score,
                    'demographics': segment['demographics'],
                    'preferred_platforms': segment['preferred_platforms'],
                    'content_preferences': segment['content_preferences'],
                    'messaging_style': segment['messaging_style'],
                    'best_posting_times': segment['best_posting_times']
                })
        
        # Sort by score
        matched_segments.sort(key=lambda x: x['score'], reverse=True)
        return matched_segments[:3]  # Return top 3 matches
    
    async def generate_targeting_recommendations(self, business_data: Dict, matched_segments: List[Dict]) -> Dict:
        """Generate specific targeting recommendations"""
        
        try:
            language = business_data.get('language', 'ar')
            
            if not matched_segments:
                return {'platforms': [], 'content_strategy': '', 'timing': []}
            
            # Aggregate recommendations from matched segments
            all_platforms = []
            all_content_prefs = []
            all_posting_times = []
            
            for segment in matched_segments:
                all_platforms.extend(segment['preferred_platforms'])
                all_content_prefs.extend(segment['content_preferences'])
                all_posting_times.extend(segment['best_posting_times'])
            
            # Get most common recommendations
            platform_counts = {}
            for platform in all_platforms:
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            recommended_platforms = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Generate content strategy
            if language == 'ar':
                content_prompt = f"""بناءً على تحليل الجمهور المستهدف، اقترح استراتيجية محتوى:

الجمهور المستهدف: {', '.join([seg['segment_name'] for seg in matched_segments])}
المنصات المفضلة: {', '.join([p[0] for p in recommended_platforms])}
تفضيلات المحتوى: {', '.join(set(all_content_prefs))}

اقترح:
1. أنواع المحتوى الأكثر فعالية
2. أسلوب المراسلة المناسب
3. تكرار النشر المقترح
4. نصائح للتفاعل

اكتب الاستراتيجية بشكل مختصر ومحدد:"""
            else:
                content_prompt = f"""Based on target audience analysis, suggest content strategy:

Target Audience: {', '.join([seg['segment_name'] for seg in matched_segments])}
Preferred Platforms: {', '.join([p[0] for p in recommended_platforms])}
Content Preferences: {', '.join(set(all_content_prefs))}

Suggest:
1. Most effective content types
2. Appropriate messaging style
3. Suggested posting frequency
4. Engagement tips

Write strategy concisely and specifically:"""
            
            result = await api_integration.generate_text(
                prompt=content_prompt,
                max_tokens=800,
                temperature=0.7,
                service='google_gemini'
            )
            
            content_strategy = result['data'].get('text', '') if result['success'] else ''
            
            return {
                'platforms': [{'platform': p[0], 'priority': p[1]} for p in recommended_platforms],
                'content_strategy': content_strategy,
                'timing': list(set(all_posting_times)),
                'content_types': list(set(all_content_prefs))
            }
            
        except Exception as e:
            logger.error(f"Error generating targeting recommendations: {str(e)}")
            return {'platforms': [], 'content_strategy': '', 'timing': []}
    
    async def optimize_campaign_performance(self, campaign_data: Dict) -> Dict:
        """Optimize campaign performance based on current metrics"""
        
        try:
            campaign_name = campaign_data.get('campaign_name', '')
            current_metrics = campaign_data.get('current_metrics', {})
            target_metrics = campaign_data.get('target_metrics', {})
            audience_data = campaign_data.get('audience_data', {})
            language = campaign_data.get('language', 'ar')
            
            # Analyze performance gaps
            performance_gaps = self.analyze_performance_gaps(current_metrics, target_metrics)
            
            # Generate optimization recommendations
            optimization_recommendations = await self.generate_optimization_recommendations(
                campaign_data, performance_gaps, language
            )
            
            # Suggest A/B testing opportunities
            ab_test_suggestions = self.suggest_ab_tests(campaign_data, performance_gaps)
            
            return {
                'success': True,
                'campaign_name': campaign_name,
                'performance_gaps': performance_gaps,
                'optimization_recommendations': optimization_recommendations,
                'ab_test_suggestions': ab_test_suggestions,
                'priority_actions': self.extract_priority_actions(optimization_recommendations),
                'estimated_improvement': self.estimate_improvement_potential(performance_gaps)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing campaign performance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_performance_gaps(self, current_metrics: Dict, target_metrics: Dict) -> List[Dict]:
        """Analyze gaps between current and target performance"""
        
        gaps = []
        
        for metric, target_value in target_metrics.items():
            current_value = current_metrics.get(metric, 0)
            
            if isinstance(target_value, (int, float)) and isinstance(current_value, (int, float)):
                if target_value > current_value:
                    gap_percentage = ((target_value - current_value) / current_value) * 100 if current_value > 0 else 100
                    
                    gaps.append({
                        'metric': metric,
                        'current_value': current_value,
                        'target_value': target_value,
                        'gap_percentage': round(gap_percentage, 1),
                        'priority': 'high' if gap_percentage > 50 else 'medium' if gap_percentage > 20 else 'low'
                    })
        
        # Sort by gap percentage
        gaps.sort(key=lambda x: x['gap_percentage'], reverse=True)
        return gaps
    
    async def generate_optimization_recommendations(self, campaign_data: Dict, performance_gaps: List[Dict], language: str) -> str:
        """Generate specific optimization recommendations"""
        
        try:
            gaps_summary = ', '.join([f"{gap['metric']}: {gap['gap_percentage']}%" for gap in performance_gaps[:3]])
            
            if language == 'ar':
                prompt = f"""أنت خبير في تحسين الحملات التسويقية.

بيانات الحملة:
- اسم الحملة: {campaign_data.get('campaign_name', '')}
- الفجوات في الأداء: {gaps_summary}
- الجمهور المستهدف: {campaign_data.get('audience_data', {}).get('segment', '')}

مطلوب:
1. تحليل أسباب ضعف الأداء
2. اقتراح تحسينات محددة وقابلة للتنفيذ
3. ترتيب التحسينات حسب الأولوية
4. تقدير الوقت المطلوب لكل تحسين
5. توقع النتائج المحتملة

قدم توصيات مفصلة ومحددة:"""
            else:
                prompt = f"""You are an expert in marketing campaign optimization.

Campaign Data:
- Campaign Name: {campaign_data.get('campaign_name', '')}
- Performance Gaps: {gaps_summary}
- Target Audience: {campaign_data.get('audience_data', {}).get('segment', '')}

Required:
1. Analyze reasons for poor performance
2. Suggest specific and actionable improvements
3. Prioritize improvements by importance
4. Estimate time required for each improvement
5. Predict potential results

Provide detailed and specific recommendations:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7,
                service='google_gemini'
            )
            
            return result['data'].get('text', '') if result['success'] else ''
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {str(e)}")
            return ''
    
    def suggest_ab_tests(self, campaign_data: Dict, performance_gaps: List[Dict]) -> List[Dict]:
        """Suggest A/B testing opportunities"""
        
        ab_tests = []
        
        for gap in performance_gaps[:3]:  # Focus on top 3 gaps
            metric = gap['metric']
            
            if metric in ['click_through_rate', 'ctr']:
                ab_tests.append({
                    'test_name': 'Headlines A/B Test',
                    'test_name_ar': 'اختبار العناوين',
                    'variable': 'headline',
                    'description': 'Test different headline styles to improve CTR',
                    'description_ar': 'اختبار أساليب عناوين مختلفة لتحسين معدل النقر',
                    'duration': '7-14 days',
                    'expected_improvement': '15-30%'
                })
            
            elif metric in ['conversion_rate', 'conversions']:
                ab_tests.append({
                    'test_name': 'CTA Button A/B Test',
                    'test_name_ar': 'اختبار أزرار الدعوة للعمل',
                    'variable': 'cta_button',
                    'description': 'Test different CTA button colors and text',
                    'description_ar': 'اختبار ألوان ونصوص مختلفة لأزرار الدعوة للعمل',
                    'duration': '10-21 days',
                    'expected_improvement': '10-25%'
                })
            
            elif metric in ['engagement_rate', 'engagement']:
                ab_tests.append({
                    'test_name': 'Content Format A/B Test',
                    'test_name_ar': 'اختبار تنسيق المحتوى',
                    'variable': 'content_format',
                    'description': 'Test video vs image vs carousel content',
                    'description_ar': 'اختبار محتوى الفيديو مقابل الصور مقابل الكاروسيل',
                    'duration': '14-28 days',
                    'expected_improvement': '20-40%'
                })
        
        return ab_tests
    
    def extract_priority_actions(self, recommendations: str) -> List[str]:
        """Extract priority actions from recommendations"""
        
        actions = []
        lines = recommendations.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['1.', '2.', '3.', 'أولاً', 'ثانياً', 'ثالثاً', 'first', 'second', 'third', 'priority', 'urgent', 'important']):
                if len(line) > 15:  # Avoid very short lines
                    actions.append(line)
        
        return actions[:5]  # Return top 5 actions
    
    def estimate_improvement_potential(self, performance_gaps: List[Dict]) -> Dict:
        """Estimate improvement potential based on gaps"""
        
        if not performance_gaps:
            return {'overall_potential': 0, 'timeline': '0 weeks', 'confidence': 'low'}
        
        # Calculate weighted improvement potential
        total_potential = 0
        total_weight = 0
        
        for gap in performance_gaps:
            weight = 3 if gap['priority'] == 'high' else 2 if gap['priority'] == 'medium' else 1
            potential = min(gap['gap_percentage'], 100)  # Cap at 100%
            
            total_potential += potential * weight
            total_weight += weight
        
        overall_potential = total_potential / total_weight if total_weight > 0 else 0
        
        # Estimate timeline based on number and complexity of gaps
        high_priority_gaps = len([g for g in performance_gaps if g['priority'] == 'high'])
        
        if high_priority_gaps >= 3:
            timeline = '8-12 weeks'
            confidence = 'medium'
        elif high_priority_gaps >= 1:
            timeline = '4-8 weeks'
            confidence = 'high'
        else:
            timeline = '2-4 weeks'
            confidence = 'high'
        
        return {
            'overall_potential': round(overall_potential, 1),
            'timeline': timeline,
            'confidence': confidence,
            'high_priority_gaps': high_priority_gaps
        }
    
    def get_audience_segment_details(self, segment_id: str, language: str = 'ar') -> Dict:
        """Get detailed information about a specific audience segment"""
        
        segment = self.audience_segments.get(segment_id)
        if not segment:
            return {'success': False, 'error': 'Segment not found'}
        
        return {
            'success': True,
            'segment_id': segment_id,
            'name': segment['name_ar'] if language == 'ar' else segment['name_en'],
            'demographics': segment['demographics'],
            'preferred_platforms': segment['preferred_platforms'],
            'content_preferences': segment['content_preferences'],
            'messaging_style': segment['messaging_style'],
            'best_posting_times': segment['best_posting_times']
        }
    
    def get_all_audience_segments(self, language: str = 'ar') -> List[Dict]:
        """Get list of all available audience segments"""
        
        segments = []
        
        for segment_id, segment in self.audience_segments.items():
            segments.append({
                'segment_id': segment_id,
                'name': segment['name_ar'] if language == 'ar' else segment['name_en'],
                'age_range': segment['demographics']['age_range'],
                'interests': segment['demographics']['interests'][:3],  # Top 3 interests
                'preferred_platforms': segment['preferred_platforms']
            })
        
        return segments


# Global instance
smart_targeting = SmartTargeting()

