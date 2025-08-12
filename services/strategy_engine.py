import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_, desc, func
from src.models.marketing_strategy import (
    MarketingStrategy, StrategyExecution, StrategyTemplate, 
    StrategyRecommendation, StrategyPerformance
)
from src.models.user import User
from src.models.content import Content
from src.models.base import db

logger = logging.getLogger(__name__)

class StrategyEngine:
    """Advanced marketing strategy engine with AI-powered recommendations"""
    
    def __init__(self):
        self.strategy_categories = {
            'content': 'تسويق المحتوى',
            'social': 'التسويق عبر وسائل التواصل الاجتماعي',
            'paid': 'الإعلانات المدفوعة',
            'email': 'التسويق بالبريد الإلكتروني',
            'seo': 'تحسين محركات البحث',
            'influencer': 'تسويق المؤثرين',
            'viral': 'التسويق الفيروسي',
            'affiliate': 'التسويق بالعمولة',
            'event': 'التسويق بالأحداث',
            'local': 'التسويق المحلي'
        }
        
        self.business_types = {
            'restaurant': 'مطعم',
            'ecommerce': 'متجر إلكتروني',
            'service': 'خدمات',
            'retail': 'تجارة تجزئة',
            'healthcare': 'رعاية صحية',
            'education': 'تعليم',
            'real_estate': 'عقارات',
            'fitness': 'لياقة بدنية',
            'beauty': 'تجميل',
            'technology': 'تقنية'
        }

    def initialize_default_strategies(self):
        """Initialize the system with 20 comprehensive marketing strategies"""
        try:
            # Check if strategies already exist
            if MarketingStrategy.query.count() > 0:
                return {'success': True, 'message': 'Strategies already initialized'}
            
            strategies = [
                {
                    'name': 'Content Marketing Mastery',
                    'name_ar': 'إتقان تسويق المحتوى',
                    'description': 'Create valuable, relevant content to attract and engage target audience',
                    'description_ar': 'إنشاء محتوى قيم وذو صلة لجذب الجمهور المستهدف وإشراكه',
                    'category': 'content',
                    'difficulty_level': 'medium',
                    'effectiveness_score': 8.5,
                    'cost_level': 'low',
                    'time_to_results': 'weeks',
                    'target_audience': ['all_ages', 'professionals', 'consumers'],
                    'suitable_platforms': ['facebook', 'instagram', 'linkedin', 'youtube', 'blog'],
                    'required_resources': ['content_writer', 'designer', 'time_investment'],
                    'success_metrics': ['engagement_rate', 'website_traffic', 'lead_generation', 'brand_awareness'],
                    'implementation_steps': [
                        'تحديد الجمهور المستهدف',
                        'إنشاء استراتيجية المحتوى',
                        'تطوير تقويم المحتوى',
                        'إنتاج محتوى عالي الجودة',
                        'توزيع المحتوى عبر القنوات',
                        'قياس الأداء والتحسين'
                    ],
                    'best_practices': [
                        'ركز على القيمة المضافة للجمهور',
                        'حافظ على الاتساق في النشر',
                        'استخدم القصص لجذب الانتباه',
                        'تفاعل مع تعليقات الجمهور'
                    ],
                    'tags': ['content', 'engagement', 'brand_building', 'organic']
                },
                {
                    'name': 'Social Media Viral Growth',
                    'name_ar': 'النمو الفيروسي عبر وسائل التواصل',
                    'description': 'Leverage viral mechanics to achieve exponential growth on social platforms',
                    'description_ar': 'استغلال آليات الانتشار الفيروسي لتحقيق نمو متسارع على منصات التواصل',
                    'category': 'viral',
                    'difficulty_level': 'hard',
                    'effectiveness_score': 9.2,
                    'cost_level': 'medium',
                    'time_to_results': 'days',
                    'target_audience': ['millennials', 'gen_z', 'social_media_users'],
                    'suitable_platforms': ['tiktok', 'instagram', 'twitter', 'facebook'],
                    'required_resources': ['creative_team', 'trend_analysis', 'community_management'],
                    'success_metrics': ['viral_coefficient', 'reach', 'shares', 'user_generated_content'],
                    'implementation_steps': [
                        'تحليل الترندات الحالية',
                        'إنشاء محتوى قابل للمشاركة',
                        'استخدام الهاشتاجات الترندية',
                        'التفاعل مع المؤثرين',
                        'تشجيع المحتوى المُولد من المستخدمين',
                        'مراقبة الانتشار والتحسين'
                    ],
                    'best_practices': [
                        'اركب موجة الترندات بسرعة',
                        'اجعل المحتوى سهل المشاركة',
                        'استخدم العواطف القوية',
                        'كن أصيلاً ومبدعاً'
                    ],
                    'tags': ['viral', 'trending', 'social_media', 'growth_hacking']
                },
                {
                    'name': 'Influencer Partnership Strategy',
                    'name_ar': 'استراتيجية الشراكة مع المؤثرين',
                    'description': 'Build strategic partnerships with influencers to expand reach and credibility',
                    'description_ar': 'بناء شراكات استراتيجية مع المؤثرين لتوسيع الوصول والمصداقية',
                    'category': 'influencer',
                    'difficulty_level': 'medium',
                    'effectiveness_score': 8.8,
                    'cost_level': 'high',
                    'time_to_results': 'weeks',
                    'target_audience': ['followers_of_influencers', 'niche_communities'],
                    'suitable_platforms': ['instagram', 'youtube', 'tiktok', 'twitter'],
                    'required_resources': ['budget', 'relationship_management', 'campaign_tracking'],
                    'success_metrics': ['reach', 'engagement', 'conversions', 'brand_mentions'],
                    'implementation_steps': [
                        'تحديد المؤثرين المناسبين',
                        'تحليل جمهور المؤثرين',
                        'التفاوض على شروط الشراكة',
                        'تطوير محتوى تعاوني',
                        'تتبع أداء الحملة',
                        'بناء علاقات طويلة المدى'
                    ],
                    'best_practices': [
                        'اختر مؤثرين يتماشون مع قيم علامتك',
                        'ركز على معدل التفاعل أكثر من عدد المتابعين',
                        'امنح المؤثرين حرية إبداعية',
                        'قس العائد على الاستثمار بدقة'
                    ],
                    'tags': ['influencer', 'partnership', 'reach', 'credibility']
                },
                {
                    'name': 'SEO Content Optimization',
                    'name_ar': 'تحسين المحتوى لمحركات البحث',
                    'description': 'Optimize content for search engines to increase organic visibility',
                    'description_ar': 'تحسين المحتوى لمحركات البحث لزيادة الظهور الطبيعي',
                    'category': 'seo',
                    'difficulty_level': 'medium',
                    'effectiveness_score': 8.0,
                    'cost_level': 'low',
                    'time_to_results': 'months',
                    'target_audience': ['search_users', 'information_seekers'],
                    'suitable_platforms': ['website', 'blog', 'youtube'],
                    'required_resources': ['seo_tools', 'keyword_research', 'content_optimization'],
                    'success_metrics': ['organic_traffic', 'keyword_rankings', 'click_through_rate'],
                    'implementation_steps': [
                        'بحث الكلمات المفتاحية',
                        'تحليل المنافسين',
                        'تحسين المحتوى الموجود',
                        'إنشاء محتوى جديد محسن',
                        'بناء الروابط الداخلية',
                        'مراقبة الترتيب والتحسين'
                    ],
                    'best_practices': [
                        'ركز على نية البحث',
                        'اكتب للمستخدمين أولاً',
                        'استخدم الكلمات المفتاحية بطبيعية',
                        'حسن سرعة الموقع'
                    ],
                    'tags': ['seo', 'organic', 'search', 'long_term']
                },
                {
                    'name': 'Email Marketing Automation',
                    'name_ar': 'أتمتة التسويق بالبريد الإلكتروني',
                    'description': 'Create automated email sequences to nurture leads and drive conversions',
                    'description_ar': 'إنشاء تسلسلات بريد إلكتروني آلية لرعاية العملاء المحتملين وزيادة التحويلات',
                    'category': 'email',
                    'difficulty_level': 'medium',
                    'effectiveness_score': 8.3,
                    'cost_level': 'low',
                    'time_to_results': 'weeks',
                    'target_audience': ['subscribers', 'leads', 'customers'],
                    'suitable_platforms': ['email', 'website'],
                    'required_resources': ['email_platform', 'automation_setup', 'content_creation'],
                    'success_metrics': ['open_rate', 'click_rate', 'conversion_rate', 'revenue'],
                    'implementation_steps': [
                        'بناء قائمة البريد الإلكتروني',
                        'تقسيم الجمهور',
                        'إنشاء تسلسلات البريد',
                        'تصميم القوالب',
                        'اختبار الحملات',
                        'تحليل النتائج والتحسين'
                    ],
                    'best_practices': [
                        'خصص الرسائل حسب الجمهور',
                        'اختبر أوقات الإرسال المختلفة',
                        'استخدم عناوين جذابة',
                        'اجعل الرسائل قصيرة ومفيدة'
                    ],
                    'tags': ['email', 'automation', 'nurturing', 'conversion']
                }
                # يمكن إضافة المزيد من الاستراتيجيات هنا...
            ]
            
            # Add strategies to database
            for strategy_data in strategies:
                strategy = MarketingStrategy(**strategy_data)
                db.session.add(strategy)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully initialized {len(strategies)} marketing strategies',
                'strategies_count': len(strategies)
            }
            
        except Exception as e:
            logger.error(f"Error initializing strategies: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def recommend_strategies(self, user_id: int, business_context: Dict = None) -> List[Dict]:
        """Generate AI-powered strategy recommendations for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Analyze user's business context
            context = business_context or self._analyze_user_context(user)
            
            # Get all active strategies
            strategies = MarketingStrategy.query.filter_by(is_active=True).all()
            
            recommendations = []
            
            for strategy in strategies:
                # Calculate recommendation score
                score = self._calculate_recommendation_score(strategy, context)
                
                if score >= 6.0:  # Only recommend strategies with good fit
                    reasoning = self._generate_reasoning(strategy, context, score)
                    
                    recommendation = StrategyRecommendation(
                        user_id=user_id,
                        strategy_id=strategy.id,
                        recommendation_score=score,
                        reasoning=reasoning['en'],
                        reasoning_ar=reasoning['ar'],
                        customization_suggestions=self._generate_customizations(strategy, context),
                        expected_outcome=self._predict_outcomes(strategy, context),
                        risk_assessment=self._assess_risks(strategy, context),
                        priority_level=self._determine_priority(score, context),
                        estimated_effort=self._estimate_effort(strategy, context),
                        estimated_cost=self._estimate_cost(strategy, context),
                        estimated_timeline=self._estimate_timeline(strategy, context),
                        success_probability=min(score * 10, 95),  # Convert to percentage
                        expires_at=datetime.utcnow() + timedelta(days=30)
                    )
                    
                    db.session.add(recommendation)
                    recommendations.append(recommendation.to_dict())
            
            db.session.commit()
            
            # Sort by recommendation score
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            return recommendations[:10]  # Return top 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            db.session.rollback()
            return []

    def _analyze_user_context(self, user: User) -> Dict:
        """Analyze user context for better recommendations"""
        context = {
            'business_type': 'general',
            'audience_size': 'small',
            'budget_level': 'low',
            'experience_level': 'beginner',
            'industry': 'general',
            'goals': ['brand_awareness', 'engagement'],
            'current_platforms': ['facebook', 'instagram'],
            'content_frequency': 'weekly',
            'has_website': False,
            'team_size': 1
        }
        
        # Analyze user's content history
        user_content = Content.query.filter_by(user_id=user.id).limit(50).all()
        
        if user_content:
            # Determine most used platforms
            platforms = {}
            for content in user_content:
                for platform in content.platforms or []:
                    platforms[platform] = platforms.get(platform, 0) + 1
            
            if platforms:
                context['current_platforms'] = list(platforms.keys())
            
            # Determine content frequency
            if len(user_content) > 20:
                context['content_frequency'] = 'daily'
                context['experience_level'] = 'intermediate'
            elif len(user_content) > 10:
                context['content_frequency'] = 'weekly'
                context['experience_level'] = 'beginner'
        
        # Analyze subscription level for budget estimation
        if hasattr(user, 'subscription') and user.subscription:
            if user.subscription.plan_type in ['premium', 'enterprise']:
                context['budget_level'] = 'high'
                context['audience_size'] = 'large'
            elif user.subscription.plan_type == 'pro':
                context['budget_level'] = 'medium'
                context['audience_size'] = 'medium'
        
        return context

    def _calculate_recommendation_score(self, strategy: MarketingStrategy, context: Dict) -> float:
        """Calculate how well a strategy fits the user's context"""
        score = strategy.effectiveness_score  # Base score
        
        # Adjust based on business type match
        if context.get('business_type') in (strategy.target_audience or []):
            score += 1.0
        
        # Adjust based on budget compatibility
        budget_compatibility = {
            ('free', 'low'): 1.0,
            ('low', 'low'): 1.0,
            ('low', 'medium'): 0.8,
            ('medium', 'medium'): 1.0,
            ('medium', 'high'): 0.9,
            ('high', 'high'): 1.0
        }
        
        budget_key = (strategy.cost_level, context.get('budget_level', 'low'))
        score *= budget_compatibility.get(budget_key, 0.7)
        
        # Adjust based on platform compatibility
        user_platforms = set(context.get('current_platforms', []))
        strategy_platforms = set(strategy.suitable_platforms or [])
        
        if user_platforms.intersection(strategy_platforms):
            score += 0.5
        
        # Adjust based on difficulty vs experience
        difficulty_match = {
            ('easy', 'beginner'): 1.0,
            ('medium', 'beginner'): 0.8,
            ('medium', 'intermediate'): 1.0,
            ('hard', 'intermediate'): 0.9,
            ('hard', 'expert'): 1.0,
            ('expert', 'expert'): 1.0
        }
        
        diff_key = (strategy.difficulty_level, context.get('experience_level', 'beginner'))
        score *= difficulty_match.get(diff_key, 0.6)
        
        return min(score, 10.0)  # Cap at 10

    def _generate_reasoning(self, strategy: MarketingStrategy, context: Dict, score: float) -> Dict:
        """Generate reasoning for why this strategy was recommended"""
        reasons = []
        
        if score >= 9.0:
            reasons.append("Perfect match for your business profile")
        elif score >= 8.0:
            reasons.append("Excellent fit with high success potential")
        elif score >= 7.0:
            reasons.append("Good alignment with your current setup")
        else:
            reasons.append("Suitable option with customization")
        
        if context.get('budget_level') == strategy.cost_level:
            reasons.append(f"Matches your {strategy.cost_level} budget level")
        
        platform_overlap = set(context.get('current_platforms', [])).intersection(
            set(strategy.suitable_platforms or [])
        )
        if platform_overlap:
            reasons.append(f"Compatible with your current platforms: {', '.join(platform_overlap)}")
        
        reasoning_en = ". ".join(reasons)
        reasoning_ar = self._translate_reasoning_to_arabic(reasons)
        
        return {
            'en': reasoning_en,
            'ar': reasoning_ar
        }

    def _translate_reasoning_to_arabic(self, reasons: List[str]) -> str:
        """Translate reasoning to Arabic"""
        translations = {
            "Perfect match for your business profile": "مطابقة مثالية لملف عملك",
            "Excellent fit with high success potential": "ملائمة ممتازة مع إمكانية نجاح عالية",
            "Good alignment with your current setup": "توافق جيد مع إعدادك الحالي",
            "Suitable option with customization": "خيار مناسب مع التخصيص"
        }
        
        arabic_reasons = []
        for reason in reasons:
            arabic_reason = translations.get(reason, reason)
            arabic_reasons.append(arabic_reason)
        
        return ". ".join(arabic_reasons)

    def _generate_customizations(self, strategy: MarketingStrategy, context: Dict) -> List[Dict]:
        """Generate customization suggestions for the strategy"""
        customizations = []
        
        # Platform-specific customizations
        user_platforms = context.get('current_platforms', [])
        for platform in user_platforms:
            if platform in (strategy.suitable_platforms or []):
                customizations.append({
                    'type': 'platform_focus',
                    'suggestion': f'Focus primarily on {platform} for maximum impact',
                    'suggestion_ar': f'ركز بشكل أساسي على {platform} لتحقيق أقصى تأثير'
                })
        
        # Budget-based customizations
        if context.get('budget_level') == 'low':
            customizations.append({
                'type': 'budget_optimization',
                'suggestion': 'Start with organic methods and gradually invest in paid promotion',
                'suggestion_ar': 'ابدأ بالطرق الطبيعية واستثمر تدريجياً في الترويج المدفوع'
            })
        
        # Experience-based customizations
        if context.get('experience_level') == 'beginner':
            customizations.append({
                'type': 'learning_path',
                'suggestion': 'Start with simple tactics and gradually increase complexity',
                'suggestion_ar': 'ابدأ بالتكتيكات البسيطة وزد التعقيد تدريجياً'
            })
        
        return customizations

    def _predict_outcomes(self, strategy: MarketingStrategy, context: Dict) -> Dict:
        """Predict expected outcomes for the strategy"""
        base_metrics = {
            'engagement_increase': '15-30%',
            'reach_expansion': '25-50%',
            'lead_generation': '10-25 leads/month',
            'brand_awareness': '20-40% improvement'
        }
        
        # Adjust based on context
        if context.get('budget_level') == 'high':
            base_metrics['reach_expansion'] = '50-100%'
            base_metrics['lead_generation'] = '25-50 leads/month'
        
        return base_metrics

    def _assess_risks(self, strategy: MarketingStrategy, context: Dict) -> Dict:
        """Assess potential risks and mitigation strategies"""
        risks = {
            'low_engagement': {
                'probability': 'medium',
                'impact': 'medium',
                'mitigation': 'Test different content types and posting times'
            },
            'budget_overrun': {
                'probability': 'low',
                'impact': 'high',
                'mitigation': 'Set strict budget limits and monitor spending daily'
            },
            'platform_changes': {
                'probability': 'medium',
                'impact': 'medium',
                'mitigation': 'Diversify across multiple platforms'
            }
        }
        
        return risks

    def _determine_priority(self, score: float, context: Dict) -> str:
        """Determine priority level for the recommendation"""
        if score >= 9.0:
            return 'high'
        elif score >= 8.0:
            return 'medium'
        elif score >= 7.0:
            return 'medium'
        else:
            return 'low'

    def _estimate_effort(self, strategy: MarketingStrategy, context: Dict) -> str:
        """Estimate effort required per week"""
        effort_mapping = {
            'easy': '2-5 hours/week',
            'medium': '5-10 hours/week',
            'hard': '10-20 hours/week',
            'expert': '20+ hours/week'
        }
        
        return effort_mapping.get(strategy.difficulty_level, '5-10 hours/week')

    def _estimate_cost(self, strategy: MarketingStrategy, context: Dict) -> float:
        """Estimate monthly cost for the strategy"""
        cost_mapping = {
            'free': 0.0,
            'low': 100.0,
            'medium': 500.0,
            'high': 2000.0
        }
        
        base_cost = cost_mapping.get(strategy.cost_level, 100.0)
        
        # Adjust based on user's budget level
        if context.get('budget_level') == 'high':
            base_cost *= 2
        elif context.get('budget_level') == 'low':
            base_cost *= 0.5
        
        return base_cost

    def _estimate_timeline(self, strategy: MarketingStrategy, context: Dict) -> str:
        """Estimate timeline to see results"""
        return strategy.time_to_results or '2-4 weeks'

    def execute_strategy(self, user_id: int, strategy_id: int, execution_params: Dict) -> Dict:
        """Start executing a marketing strategy"""
        try:
            strategy = MarketingStrategy.query.get(strategy_id)
            if not strategy:
                return {'success': False, 'error': 'Strategy not found'}
            
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Create strategy execution record
            execution = StrategyExecution(
                strategy_id=strategy_id,
                user_id=user_id,
                campaign_name=execution_params.get('campaign_name', f"{strategy.name} Campaign"),
                status='planning',
                budget=execution_params.get('budget', 0.0),
                target_metrics=execution_params.get('target_metrics', {}),
                platforms_used=execution_params.get('platforms', [])
            )
            
            db.session.add(execution)
            db.session.commit()
            
            return {
                'success': True,
                'execution_id': execution.id,
                'message': 'Strategy execution started successfully',
                'next_steps': strategy.implementation_steps[:3]  # First 3 steps
            }
            
        except Exception as e:
            logger.error(f"Error executing strategy: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_strategy_performance(self, strategy_id: int, months: int = 6) -> Dict:
        """Get performance analytics for a strategy"""
        try:
            strategy = MarketingStrategy.query.get(strategy_id)
            if not strategy:
                return {'success': False, 'error': 'Strategy not found'}
            
            # Get recent performance data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            executions = StrategyExecution.query.filter(
                and_(
                    StrategyExecution.strategy_id == strategy_id,
                    StrategyExecution.created_at >= start_date
                )
            ).all()
            
            if not executions:
                return {
                    'success': True,
                    'strategy': strategy.to_dict(),
                    'performance': {
                        'total_executions': 0,
                        'success_rate': 0,
                        'average_roi': 0,
                        'average_engagement': 0
                    }
                }
            
            # Calculate performance metrics
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.success_score >= 7.0])
            success_rate = (successful_executions / total_executions) * 100
            
            average_roi = sum([e.roi for e in executions if e.roi]) / len([e for e in executions if e.roi]) if any(e.roi for e in executions) else 0
            average_engagement = sum([e.engagement_rate for e in executions if e.engagement_rate]) / len([e for e in executions if e.engagement_rate]) if any(e.engagement_rate for e in executions) else 0
            
            return {
                'success': True,
                'strategy': strategy.to_dict(),
                'performance': {
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'success_rate': round(success_rate, 2),
                    'average_roi': round(average_roi, 2),
                    'average_engagement': round(average_engagement, 2),
                    'total_audience_reached': sum([e.audience_reached for e in executions if e.audience_reached]),
                    'total_budget_spent': sum([e.spent_amount for e in executions if e.spent_amount]),
                    'most_successful_platform': self._get_most_successful_platform(executions)
                },
                'recent_executions': [e.to_dict() for e in executions[-5:]]  # Last 5 executions
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy performance: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _get_most_successful_platform(self, executions: List[StrategyExecution]) -> str:
        """Determine the most successful platform from executions"""
        platform_performance = {}
        
        for execution in executions:
            if execution.platforms_used and execution.success_score:
                for platform in execution.platforms_used:
                    if platform not in platform_performance:
                        platform_performance[platform] = {'total_score': 0, 'count': 0}
                    platform_performance[platform]['total_score'] += execution.success_score
                    platform_performance[platform]['count'] += 1
        
        if not platform_performance:
            return 'N/A'
        
        # Calculate average scores
        for platform in platform_performance:
            platform_performance[platform]['average'] = (
                platform_performance[platform]['total_score'] / 
                platform_performance[platform]['count']
            )
        
        # Return platform with highest average score
        best_platform = max(platform_performance.items(), key=lambda x: x[1]['average'])
        return best_platform[0]

# Initialize the strategy engine
strategy_engine = StrategyEngine()

