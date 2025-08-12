import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import google.generativeai as genai
import os
from src.services.ai_content_generator import ai_content_generator
from src.services.external_api_integration import api_integration

logger = logging.getLogger(__name__)

class AdvancedMarketingStrategies:
    """Advanced Marketing Strategies System with 20 Comprehensive Strategies"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        
        # Comprehensive Marketing Strategies Database (20 Advanced Strategies)
        self.marketing_strategies = {
            # Core Strategies (1-5)
            'content_marketing': {
                'name_ar': 'تسويق المحتوى',
                'name_en': 'Content Marketing',
                'description_ar': 'إنشاء محتوى قيم وتعليمي يجذب العملاء ويبني الثقة',
                'description_en': 'Creating valuable and educational content that attracts customers and builds trust',
                'focus': 'valuable_educational_content',
                'tone': 'educational_helpful',
                'cta_style': 'soft_educational',
                'content_types': ['blog_posts', 'tutorials', 'guides', 'infographics', 'ebooks'],
                'best_for': ['all_businesses', 'b2b', 'education', 'consulting'],
                'target_audience': ['professionals', 'learners', 'decision_makers'],
                'platforms': ['website', 'linkedin', 'youtube', 'medium'],
                'kpis': ['engagement_rate', 'time_on_page', 'lead_generation', 'brand_awareness']
            },
            'social_media_marketing': {
                'name_ar': 'التسويق عبر وسائل التواصل الاجتماعي',
                'name_en': 'Social Media Marketing',
                'description_ar': 'بناء مجتمع وتفاعل مع العملاء عبر منصات التواصل',
                'description_en': 'Building community and engaging with customers across social platforms',
                'focus': 'engagement_community_building',
                'tone': 'conversational_friendly',
                'cta_style': 'interactive_engaging',
                'content_types': ['posts', 'stories', 'reels', 'polls', 'live_streams'],
                'best_for': ['b2c', 'lifestyle', 'entertainment', 'retail', 'restaurants'],
                'target_audience': ['general_public', 'millennials', 'gen_z'],
                'platforms': ['facebook', 'instagram', 'tiktok', 'twitter', 'snapchat'],
                'kpis': ['followers_growth', 'engagement_rate', 'reach', 'shares']
            },
            'viral_marketing': {
                'name_ar': 'التسويق الفيروسي',
                'name_en': 'Viral Marketing',
                'description_ar': 'إنشاء محتوى قابل للانتشار السريع والواسع',
                'description_en': 'Creating content designed for rapid and wide spread',
                'focus': 'shareability_rapid_spread',
                'tone': 'entertaining_memorable',
                'cta_style': 'share_encouraging',
                'content_types': ['memes', 'challenges', 'trending_content', 'viral_videos', 'hashtag_campaigns'],
                'best_for': ['youth_brands', 'entertainment', 'social_causes', 'apps'],
                'target_audience': ['young_adults', 'social_media_users', 'trend_followers'],
                'platforms': ['tiktok', 'instagram', 'twitter', 'youtube_shorts'],
                'kpis': ['viral_coefficient', 'shares', 'mentions', 'reach_growth']
            },
            'influencer_marketing': {
                'name_ar': 'تسويق المؤثرين',
                'name_en': 'Influencer Marketing',
                'description_ar': 'الشراكة مع المؤثرين لبناء الثقة والوصول لجمهور أوسع',
                'description_en': 'Partnering with influencers to build trust and reach wider audiences',
                'focus': 'authenticity_trust_building',
                'tone': 'personal_relatable',
                'cta_style': 'recommendation_based',
                'content_types': ['testimonials', 'reviews', 'collaborations', 'takeovers', 'sponsored_content'],
                'best_for': ['fashion', 'beauty', 'lifestyle', 'tech', 'fitness'],
                'target_audience': ['followers_of_influencers', 'niche_communities'],
                'platforms': ['instagram', 'youtube', 'tiktok', 'twitch'],
                'kpis': ['engagement_rate', 'conversion_rate', 'brand_mentions', 'follower_growth']
            },
            'paid_advertising': {
                'name_ar': 'الإعلانات المدفوعة',
                'name_en': 'Paid Advertising',
                'description_ar': 'استخدام الإعلانات المدفوعة لتحقيق نتائج سريعة ومحددة',
                'description_en': 'Using paid ads to achieve quick and targeted results',
                'focus': 'conversion_roi_optimization',
                'tone': 'persuasive_urgent',
                'cta_style': 'strong_direct',
                'content_types': ['ad_copy', 'headlines', 'display_ads', 'video_ads', 'search_ads'],
                'best_for': ['ecommerce', 'saas', 'high_value_products', 'lead_generation'],
                'target_audience': ['potential_customers', 'lookalike_audiences', 'retargeting'],
                'platforms': ['google_ads', 'facebook_ads', 'linkedin_ads', 'youtube_ads'],
                'kpis': ['roas', 'cpc', 'conversion_rate', 'ctr']
            },
            
            # Advanced Strategies (6-10)
            'email_marketing': {
                'name_ar': 'التسويق بالبريد الإلكتروني',
                'name_en': 'Email Marketing',
                'description_ar': 'التواصل المباشر والشخصي مع العملاء عبر البريد الإلكتروني',
                'description_en': 'Direct and personal communication with customers via email',
                'focus': 'personalization_nurturing',
                'tone': 'direct_personal',
                'cta_style': 'clear_actionable',
                'content_types': ['newsletters', 'promotions', 'sequences', 'welcome_series', 'abandoned_cart'],
                'best_for': ['ecommerce', 'saas', 'b2b', 'subscription_services'],
                'target_audience': ['existing_customers', 'subscribers', 'leads'],
                'platforms': ['email_platforms', 'crm_systems'],
                'kpis': ['open_rate', 'click_rate', 'conversion_rate', 'unsubscribe_rate']
            },
            'seo_marketing': {
                'name_ar': 'تحسين محركات البحث',
                'name_en': 'SEO Marketing',
                'description_ar': 'تحسين المحتوى والموقع للظهور في نتائج البحث الأولى',
                'description_en': 'Optimizing content and website to appear in top search results',
                'focus': 'search_visibility_organic_traffic',
                'tone': 'informative_authoritative',
                'cta_style': 'keyword_optimized',
                'content_types': ['articles', 'landing_pages', 'meta_content', 'schema_markup'],
                'best_for': ['all_businesses', 'local_businesses', 'content_sites'],
                'target_audience': ['searchers', 'information_seekers'],
                'platforms': ['google', 'bing', 'website'],
                'kpis': ['organic_traffic', 'keyword_rankings', 'click_through_rate', 'domain_authority']
            },
            'brand_storytelling': {
                'name_ar': 'سرد العلامة التجارية',
                'name_en': 'Brand Storytelling',
                'description_ar': 'بناء هوية العلامة التجارية من خلال القصص المؤثرة',
                'description_en': 'Building brand identity through compelling stories',
                'focus': 'narrative_emotional_connection',
                'tone': 'inspiring_authentic',
                'cta_style': 'journey_based',
                'content_types': ['stories', 'case_studies', 'testimonials', 'behind_scenes', 'founder_story'],
                'best_for': ['premium_brands', 'startups', 'personal_brands', 'nonprofits'],
                'target_audience': ['brand_enthusiasts', 'emotional_buyers'],
                'platforms': ['all_platforms', 'website', 'social_media'],
                'kpis': ['brand_awareness', 'emotional_engagement', 'brand_loyalty', 'story_shares']
            },
            'community_marketing': {
                'name_ar': 'تسويق المجتمع',
                'name_en': 'Community Marketing',
                'description_ar': 'بناء مجتمع قوي حول العلامة التجارية',
                'description_en': 'Building a strong community around the brand',
                'focus': 'community_building_loyalty',
                'tone': 'inclusive_supportive',
                'cta_style': 'community_driven',
                'content_types': ['discussions', 'events', 'user_content', 'forums', 'groups'],
                'best_for': ['tech_companies', 'gaming', 'fitness', 'education'],
                'target_audience': ['enthusiasts', 'power_users', 'advocates'],
                'platforms': ['discord', 'reddit', 'facebook_groups', 'slack'],
                'kpis': ['community_size', 'engagement_depth', 'user_retention', 'advocacy_rate']
            },
            'partnership_marketing': {
                'name_ar': 'تسويق الشراكات',
                'name_en': 'Partnership Marketing',
                'description_ar': 'التعاون مع شركات أخرى لتوسيع الوصول',
                'description_en': 'Collaborating with other companies to expand reach',
                'focus': 'collaboration_mutual_benefit',
                'tone': 'professional_collaborative',
                'cta_style': 'partnership_focused',
                'content_types': ['joint_content', 'co_marketing', 'cross_promotions', 'webinars'],
                'best_for': ['b2b', 'saas', 'complementary_services'],
                'target_audience': ['partner_audiences', 'shared_customers'],
                'platforms': ['linkedin', 'industry_events', 'webinars'],
                'kpis': ['partnership_roi', 'shared_leads', 'cross_sales', 'brand_reach']
            }
        }
        
        # Language-specific strategy templates
        self.strategy_templates = {
            'ar': {
                'strategy_analysis': """تحليل استراتيجية التسويق:

الاستراتيجية: {strategy_name}
نوع العمل: {business_type}
المنتج/الخدمة: {product_service}
الجمهور المستهدف: {target_audience}

التحليل المطلوب:
1. مدى ملاءمة هذه الاستراتيجية للعمل المحدد
2. نقاط القوة والضعف المحتملة
3. التوصيات للتحسين
4. مؤشرات الأداء الرئيسية المقترحة
5. الخطوات التنفيذية المحددة

قدم تحليلاً شاملاً ومفصلاً:""",
                
                'content_strategy': """إنشاء استراتيجية محتوى:

الاستراتيجية: {strategy_name}
المنصة: {platform}
نوع المحتوى: {content_type}
اللغة: {language}

المطلوب:
1. خطة محتوى لمدة شهر (30 منشور)
2. أفكار محتوى متنوعة ومبتكرة
3. جدولة زمنية مقترحة
4. هاشتاجات مناسبة لكل منشور
5. نصائح للتفاعل والمشاركة

اكتب الخطة بالتفصيل:""",
                
                'campaign_optimization': """تحسين الحملة التسويقية:

الحملة الحالية: {current_campaign}
الأداء الحالي: {current_performance}
الهدف المطلوب: {target_goal}

التحسينات المطلوبة:
1. تحليل الأداء الحالي
2. تحديد نقاط التحسين
3. اقتراح تعديلات محددة
4. خطة تنفيذ التحسينات
5. توقعات النتائج المحسنة

قدم خطة تحسين شاملة:"""
            },
            'en': {
                'strategy_analysis': """Marketing Strategy Analysis:

Strategy: {strategy_name}
Business Type: {business_type}
Product/Service: {product_service}
Target Audience: {target_audience}

Required Analysis:
1. How suitable is this strategy for the specified business
2. Potential strengths and weaknesses
3. Recommendations for improvement
4. Suggested key performance indicators
5. Specific implementation steps

Provide comprehensive and detailed analysis:""",
                
                'content_strategy': """Content Strategy Creation:

Strategy: {strategy_name}
Platform: {platform}
Content Type: {content_type}
Language: {language}

Requirements:
1. One-month content plan (30 posts)
2. Diverse and innovative content ideas
3. Suggested scheduling timeline
4. Appropriate hashtags for each post
5. Tips for engagement and sharing

Write the detailed plan:""",
                
                'campaign_optimization': """Campaign Optimization:

Current Campaign: {current_campaign}
Current Performance: {current_performance}
Target Goal: {target_goal}

Required Optimizations:
1. Current performance analysis
2. Identify improvement points
3. Suggest specific modifications
4. Implementation plan for improvements
5. Expected improved results

Provide comprehensive optimization plan:"""
            }
        }
    
    async def analyze_strategy_fit(self, business_data: Dict) -> Dict:
        """Analyze which marketing strategies best fit the business"""
        
        try:
            business_type = business_data.get('business_type', '')
            target_audience = business_data.get('target_audience', '')
            budget = business_data.get('budget', 'medium')
            goals = business_data.get('goals', [])
            language = business_data.get('language', 'ar')
            
            # Build analysis prompt
            if language == 'ar':
                prompt = f"""أنت خبير تسويق متخصص في تحليل الاستراتيجيات التسويقية.

معلومات العمل:
- نوع العمل: {business_type}
- الجمهور المستهدف: {target_audience}
- الميزانية: {budget}
- الأهداف: {', '.join(goals)}

مهمتك:
1. تحليل أفضل 5 استراتيجيات تسويقية مناسبة لهذا العمل
2. ترتيب الاستراتيجيات حسب الأولوية والفعالية
3. شرح سبب اختيار كل استراتيجية
4. تقدير التكلفة والعائد المتوقع لكل استراتيجية
5. خطة تنفيذ مبدئية لكل استراتيجية

قدم تحليلاً مفصلاً ومهنياً:"""
            else:
                prompt = f"""You are a marketing expert specialized in analyzing marketing strategies.

Business Information:
- Business Type: {business_type}
- Target Audience: {target_audience}
- Budget: {budget}
- Goals: {', '.join(goals)}

Your Task:
1. Analyze the best 5 marketing strategies suitable for this business
2. Rank strategies by priority and effectiveness
3. Explain why each strategy was chosen
4. Estimate cost and expected ROI for each strategy
5. Initial implementation plan for each strategy

Provide detailed and professional analysis:"""
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                analysis_text = result['data'].get('text', '')
                
                # Score strategies based on business fit
                strategy_scores = self.calculate_strategy_scores(business_data)
                
                return {
                    'success': True,
                    'analysis': analysis_text,
                    'recommended_strategies': strategy_scores[:5],
                    'business_type': business_type,
                    'language': language
                }
            else:
                return {'success': False, 'error': result.get('error')}
            
        except Exception as e:
            logger.error(f"Error analyzing strategy fit: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_strategy_scores(self, business_data: Dict) -> List[Dict]:
        """Calculate fit scores for each strategy"""
        
        business_type = business_data.get('business_type', '').lower()
        target_audience = business_data.get('target_audience', '').lower()
        budget = business_data.get('budget', 'medium').lower()
        goals = [goal.lower() for goal in business_data.get('goals', [])]
        
        scored_strategies = []
        
        for strategy_id, strategy in self.marketing_strategies.items():
            score = 0
            
            # Business type fit
            best_for = [bf.lower() for bf in strategy['best_for']]
            if any(bt in business_type for bt in best_for) or 'all_businesses' in best_for:
                score += 30
            
            # Target audience fit
            target_audiences = [ta.lower() for ta in strategy['target_audience']]
            if any(ta in target_audience for ta in target_audiences):
                score += 25
            
            # Budget considerations
            if budget == 'low' and strategy_id in ['content_marketing', 'social_media_marketing', 'seo_marketing']:
                score += 20
            elif budget == 'high' and strategy_id in ['paid_advertising', 'influencer_marketing']:
                score += 20
            else:
                score += 10
            
            # Goals alignment
            strategy_focus = strategy['focus'].lower()
            if any(goal in strategy_focus for goal in goals):
                score += 25
            
            scored_strategies.append({
                'strategy_id': strategy_id,
                'strategy_name': strategy['name_ar'],
                'score': score,
                'description': strategy['description_ar'],
                'focus': strategy['focus'],
                'platforms': strategy['platforms'],
                'kpis': strategy['kpis']
            })
        
        # Sort by score
        scored_strategies.sort(key=lambda x: x['score'], reverse=True)
        return scored_strategies
    
    async def create_content_strategy(self, strategy_data: Dict) -> Dict:
        """Create detailed content strategy"""
        
        try:
            strategy_id = strategy_data.get('strategy_id', 'content_marketing')
            platform = strategy_data.get('platform', 'facebook')
            language = strategy_data.get('language', 'ar')
            business_type = strategy_data.get('business_type', '')
            duration = strategy_data.get('duration', 30)  # days
            
            strategy = self.marketing_strategies.get(strategy_id)
            if not strategy:
                return {'success': False, 'error': 'Strategy not found'}
            
            # Build content strategy prompt
            template = self.strategy_templates[language]['content_strategy']
            prompt = template.format(
                strategy_name=strategy['name_ar'] if language == 'ar' else strategy['name_en'],
                platform=platform,
                content_type=', '.join(strategy['content_types']),
                language=language
            )
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=3000,
                temperature=0.8,
                service='google_gemini'
            )
            
            if result['success']:
                content_plan = result['data'].get('text', '')
                
                # Generate specific content ideas
                content_ideas = await self.generate_content_ideas(strategy_data, duration)
                
                return {
                    'success': True,
                    'content_strategy': content_plan,
                    'content_ideas': content_ideas,
                    'strategy_id': strategy_id,
                    'platform': platform,
                    'duration': duration
                }
            else:
                return {'success': False, 'error': result.get('error')}
            
        except Exception as e:
            logger.error(f"Error creating content strategy: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_content_ideas(self, strategy_data: Dict, duration: int) -> List[Dict]:
        """Generate specific content ideas for the strategy"""
        
        try:
            strategy_id = strategy_data.get('strategy_id', 'content_marketing')
            language = strategy_data.get('language', 'ar')
            business_type = strategy_data.get('business_type', '')
            product_service = strategy_data.get('product_service', '')
            
            strategy = self.marketing_strategies.get(strategy_id)
            content_types = strategy['content_types']
            
            content_ideas = []
            
            for i in range(min(duration, 30)):  # Limit to 30 ideas
                # Rotate through content types
                content_type = content_types[i % len(content_types)]
                
                if language == 'ar':
                    prompt = f"""أنشئ فكرة محتوى محددة:

نوع المحتوى: {content_type}
نوع العمل: {business_type}
المنتج/الخدمة: {product_service}
اليوم: {i + 1}

المطلوب:
- عنوان جذاب
- وصف المحتوى (2-3 جمل)
- 3 هاشتاجات مناسبة
- نصيحة للتفاعل

اكتب الفكرة بشكل مختصر ومحدد:"""
                else:
                    prompt = f"""Create a specific content idea:

Content Type: {content_type}
Business Type: {business_type}
Product/Service: {product_service}
Day: {i + 1}

Required:
- Catchy title
- Content description (2-3 sentences)
- 3 relevant hashtags
- Engagement tip

Write the idea concisely and specifically:"""
                
                result = await api_integration.generate_text(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.9,
                    service='google_gemini'
                )
                
                if result['success']:
                    idea_text = result['data'].get('text', '')
                    content_ideas.append({
                        'day': i + 1,
                        'content_type': content_type,
                        'idea': idea_text,
                        'generated_at': datetime.now().isoformat()
                    })
            
            return content_ideas
            
        except Exception as e:
            logger.error(f"Error generating content ideas: {str(e)}")
            return []
    
    async def optimize_campaign(self, campaign_data: Dict) -> Dict:
        """Optimize existing marketing campaign"""
        
        try:
            campaign_name = campaign_data.get('campaign_name', '')
            current_metrics = campaign_data.get('current_metrics', {})
            target_metrics = campaign_data.get('target_metrics', {})
            language = campaign_data.get('language', 'ar')
            
            # Build optimization prompt
            template = self.strategy_templates[language]['campaign_optimization']
            prompt = template.format(
                current_campaign=campaign_name,
                current_performance=str(current_metrics),
                target_goal=str(target_metrics)
            )
            
            result = await api_integration.generate_text(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
                service='google_gemini'
            )
            
            if result['success']:
                optimization_plan = result['data'].get('text', '')
                
                # Calculate improvement potential
                improvement_analysis = self.analyze_improvement_potential(current_metrics, target_metrics)
                
                return {
                    'success': True,
                    'optimization_plan': optimization_plan,
                    'improvement_analysis': improvement_analysis,
                    'campaign_name': campaign_name,
                    'priority_actions': self.extract_priority_actions(optimization_plan)
                }
            else:
                return {'success': False, 'error': result.get('error')}
            
        except Exception as e:
            logger.error(f"Error optimizing campaign: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_improvement_potential(self, current_metrics: Dict, target_metrics: Dict) -> Dict:
        """Analyze improvement potential based on metrics"""
        
        analysis = {
            'improvement_areas': [],
            'priority_level': 'medium',
            'estimated_timeline': '2-4 weeks',
            'success_probability': 70
        }
        
        for metric, target_value in target_metrics.items():
            current_value = current_metrics.get(metric, 0)
            
            if isinstance(target_value, (int, float)) and isinstance(current_value, (int, float)):
                if target_value > current_value:
                    improvement_needed = ((target_value - current_value) / current_value) * 100
                    
                    analysis['improvement_areas'].append({
                        'metric': metric,
                        'current': current_value,
                        'target': target_value,
                        'improvement_needed': f"{improvement_needed:.1f}%"
                    })
                    
                    # Adjust priority based on improvement needed
                    if improvement_needed > 50:
                        analysis['priority_level'] = 'high'
                        analysis['estimated_timeline'] = '4-8 weeks'
                        analysis['success_probability'] = 60
        
        return analysis
    
    def extract_priority_actions(self, optimization_plan: str) -> List[str]:
        """Extract priority actions from optimization plan"""
        
        # Simple extraction based on common patterns
        actions = []
        lines = optimization_plan.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['1.', '2.', '3.', 'أولاً', 'ثانياً', 'ثالثاً', 'first', 'second', 'third']):
                if len(line) > 10:  # Avoid very short lines
                    actions.append(line)
        
        return actions[:5]  # Return top 5 actions
    
    def get_strategy_details(self, strategy_id: str, language: str = 'ar') -> Dict:
        """Get detailed information about a specific strategy"""
        
        strategy = self.marketing_strategies.get(strategy_id)
        if not strategy:
            return {'success': False, 'error': 'Strategy not found'}
        
        return {
            'success': True,
            'strategy_id': strategy_id,
            'name': strategy['name_ar'] if language == 'ar' else strategy['name_en'],
            'description': strategy['description_ar'] if language == 'ar' else strategy['description_en'],
            'focus': strategy['focus'],
            'tone': strategy['tone'],
            'cta_style': strategy['cta_style'],
            'content_types': strategy['content_types'],
            'best_for': strategy['best_for'],
            'target_audience': strategy['target_audience'],
            'platforms': strategy['platforms'],
            'kpis': strategy['kpis']
        }
    
    def get_all_strategies(self, language: str = 'ar') -> List[Dict]:
        """Get list of all available strategies"""
        
        strategies = []
        
        for strategy_id, strategy in self.marketing_strategies.items():
            strategies.append({
                'strategy_id': strategy_id,
                'name': strategy['name_ar'] if language == 'ar' else strategy['name_en'],
                'description': strategy['description_ar'] if language == 'ar' else strategy['description_en'],
                'focus': strategy['focus'],
                'best_for': strategy['best_for'],
                'platforms': strategy['platforms']
            })
        
        return strategies


# Global instance
advanced_marketing_strategies = AdvancedMarketingStrategies()

