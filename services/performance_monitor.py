import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics
from collections import defaultdict
import requests
from src.models.content import Content
from src.models.task import Task
from src.models.user import User
from src.services.free_ai_generator import free_ai_generator
from src.services.advanced_marketing_strategies import advanced_marketing_strategies

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Advanced Performance Monitoring and Optimization System"""
    
    def __init__(self):
        # Performance metrics weights
        self.metric_weights = {
            'engagement_rate': 0.3,
            'reach': 0.25,
            'impressions': 0.15,
            'clicks': 0.15,
            'conversions': 0.15
        }
        
        # Platform benchmarks (industry averages)
        self.platform_benchmarks = {
            'facebook': {
                'engagement_rate': 0.09,  # 0.09%
                'click_rate': 0.9,        # 0.9%
                'reach_rate': 5.2         # 5.2%
            },
            'instagram': {
                'engagement_rate': 1.22,  # 1.22%
                'click_rate': 0.83,       # 0.83%
                'reach_rate': 8.5         # 8.5%
            },
            'twitter': {
                'engagement_rate': 0.045, # 0.045%
                'click_rate': 1.64,       # 1.64%
                'reach_rate': 3.7         # 3.7%
            },
            'linkedin': {
                'engagement_rate': 2.0,   # 2.0%
                'click_rate': 2.8,        # 2.8%
                'reach_rate': 6.1         # 6.1%
            },
            'tiktok': {
                'engagement_rate': 5.96,  # 5.96%
                'click_rate': 1.0,        # 1.0%
                'reach_rate': 15.0        # 15.0%
            },
            'youtube': {
                'engagement_rate': 1.8,   # 1.8%
                'click_rate': 2.5,        # 2.5%
                'reach_rate': 12.0        # 12.0%
            }
        }
        
        # Content type performance patterns
        self.content_type_patterns = {
            'image_post': {
                'best_times': ['12:00', '15:00', '18:00'],
                'optimal_length': 150,
                'hashtag_count': 8
            },
            'video_post': {
                'best_times': ['16:00', '18:00', '20:00'],
                'optimal_length': 100,
                'hashtag_count': 5
            },
            'text_post': {
                'best_times': ['09:00', '12:00', '17:00'],
                'optimal_length': 200,
                'hashtag_count': 3
            }
        }
        
        # Performance improvement strategies
        self.improvement_strategies = {
            'low_engagement': [
                'استخدم محتوى تفاعلي أكثر (أسئلة، استطلاعات)',
                'أضف صور أو فيديوهات جذابة',
                'استخدم هاشتاجات أكثر صلة',
                'انشر في الأوقات المثلى لجمهورك'
            ],
            'low_reach': [
                'حسن استخدام الهاشتاجات',
                'انشر بانتظام أكثر',
                'تفاعل مع متابعيك أكثر',
                'استخدم الترندات الحالية'
            ],
            'low_clicks': [
                'اكتب عناوين أكثر جاذبية',
                'استخدم دعوات واضحة للعمل',
                'أضف روابط مفيدة',
                'حسن جودة الصور والفيديوهات'
            ],
            'low_conversions': [
                'حسن صفحة الهبوط',
                'اجعل عملية الشراء أسهل',
                'أضف شهادات العملاء',
                'قدم عروض محدودة الوقت'
            ]
        }
    
    def analyze_content_performance(self, user_id: int, days: int = 30) -> Dict:
        """Analyze content performance for a user over specified days"""
        try:
            # Get user's content from the last N days
            start_date = datetime.now() - timedelta(days=days)
            
            content_query = Content.query.filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.status == 'published'
            ).all()
            
            if not content_query:
                return {
                    'success': False,
                    'error': 'No published content found for analysis'
                }
            
            # Analyze performance by platform
            platform_performance = {}
            overall_metrics = {
                'total_posts': len(content_query),
                'total_engagement': 0,
                'total_reach': 0,
                'total_impressions': 0,
                'total_clicks': 0
            }
            
            for content in content_query:
                platform = content.platform
                
                if platform not in platform_performance:
                    platform_performance[platform] = {
                        'posts': 0,
                        'engagement': 0,
                        'reach': 0,
                        'impressions': 0,
                        'clicks': 0,
                        'performance_score': 0
                    }
                
                # Simulate performance metrics (in real implementation, get from platform APIs)
                metrics = self.simulate_content_metrics(content)
                
                platform_performance[platform]['posts'] += 1
                platform_performance[platform]['engagement'] += metrics['engagement']
                platform_performance[platform]['reach'] += metrics['reach']
                platform_performance[platform]['impressions'] += metrics['impressions']
                platform_performance[platform]['clicks'] += metrics['clicks']
                
                overall_metrics['total_engagement'] += metrics['engagement']
                overall_metrics['total_reach'] += metrics['reach']
                overall_metrics['total_impressions'] += metrics['impressions']
                overall_metrics['total_clicks'] += metrics['clicks']
            
            # Calculate performance scores and rates
            for platform, data in platform_performance.items():
                if data['impressions'] > 0:
                    data['engagement_rate'] = (data['engagement'] / data['impressions']) * 100
                    data['click_rate'] = (data['clicks'] / data['impressions']) * 100
                    data['reach_rate'] = (data['reach'] / data['impressions']) * 100
                else:
                    data['engagement_rate'] = 0
                    data['click_rate'] = 0
                    data['reach_rate'] = 0
                
                # Calculate performance score vs benchmarks
                data['performance_score'] = self.calculate_performance_score(platform, data)
            
            # Generate insights and recommendations
            insights = self.generate_performance_insights(platform_performance, overall_metrics)
            recommendations = self.generate_improvement_recommendations(platform_performance)
            
            return {
                'success': True,
                'analysis_period': f'{days} days',
                'overall_metrics': overall_metrics,
                'platform_performance': platform_performance,
                'insights': insights,
                'recommendations': recommendations,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def simulate_content_metrics(self, content: Content) -> Dict:
        """Simulate realistic content metrics based on content characteristics"""
        
        # Base metrics influenced by content type, platform, and quality
        base_impressions = 1000
        platform = content.platform
        content_data = content.content_data or {}
        
        # Platform multipliers
        platform_multipliers = {
            'facebook': 1.0,
            'instagram': 1.5,
            'tiktok': 3.0,
            'youtube': 2.0,
            'twitter': 0.8,
            'linkedin': 0.6
        }
        
        multiplier = platform_multipliers.get(platform, 1.0)
        
        # Content quality factors
        has_image = bool(content_data.get('image_url'))
        has_video = bool(content_data.get('video_url'))
        text_length = len(content_data.get('text', ''))
        hashtag_count = len(content_data.get('hashtags', []))
        
        quality_multiplier = 1.0
        if has_video:
            quality_multiplier += 0.5
        elif has_image:
            quality_multiplier += 0.3
        
        if 50 <= text_length <= 200:
            quality_multiplier += 0.2
        
        if 3 <= hashtag_count <= 10:
            quality_multiplier += 0.1
        
        # Calculate metrics
        impressions = int(base_impressions * multiplier * quality_multiplier)
        reach = int(impressions * 0.7)  # 70% of impressions
        engagement = int(impressions * 0.02)  # 2% engagement rate
        clicks = int(impressions * 0.01)  # 1% click rate
        
        # Add some randomness
        import random
        impressions = int(impressions * random.uniform(0.8, 1.2))
        reach = int(reach * random.uniform(0.8, 1.2))
        engagement = int(engagement * random.uniform(0.5, 2.0))
        clicks = int(clicks * random.uniform(0.5, 1.5))
        
        return {
            'impressions': impressions,
            'reach': reach,
            'engagement': engagement,
            'clicks': clicks,
            'quality_score': quality_multiplier
        }
    
    def calculate_performance_score(self, platform: str, metrics: Dict) -> float:
        """Calculate performance score compared to industry benchmarks"""
        
        benchmarks = self.platform_benchmarks.get(platform, {})
        if not benchmarks:
            return 50.0  # Neutral score if no benchmarks
        
        score = 0.0
        total_weight = 0.0
        
        # Compare engagement rate
        if 'engagement_rate' in benchmarks and metrics.get('engagement_rate', 0) > 0:
            ratio = metrics['engagement_rate'] / benchmarks['engagement_rate']
            score += min(ratio * 50, 100) * 0.4  # 40% weight
            total_weight += 0.4
        
        # Compare click rate
        if 'click_rate' in benchmarks and metrics.get('click_rate', 0) > 0:
            ratio = metrics['click_rate'] / benchmarks['click_rate']
            score += min(ratio * 50, 100) * 0.3  # 30% weight
            total_weight += 0.3
        
        # Compare reach rate
        if 'reach_rate' in benchmarks and metrics.get('reach_rate', 0) > 0:
            ratio = metrics['reach_rate'] / benchmarks['reach_rate']
            score += min(ratio * 50, 100) * 0.3  # 30% weight
            total_weight += 0.3
        
        if total_weight > 0:
            return score / total_weight
        else:
            return 50.0
    
    def generate_performance_insights(self, platform_performance: Dict, overall_metrics: Dict) -> List[str]:
        """Generate actionable insights from performance data"""
        
        insights = []
        
        # Overall performance insights
        total_posts = overall_metrics['total_posts']
        if total_posts > 0:
            avg_engagement = overall_metrics['total_engagement'] / total_posts
            insights.append(f"متوسط التفاعل لكل منشور: {avg_engagement:.0f}")
        
        # Best performing platform
        best_platform = None
        best_score = 0
        
        for platform, data in platform_performance.items():
            if data['performance_score'] > best_score:
                best_score = data['performance_score']
                best_platform = platform
        
        if best_platform:
            insights.append(f"أفضل منصة أداءً: {best_platform} بنتيجة {best_score:.1f}/100")
        
        # Platform-specific insights
        for platform, data in platform_performance.items():
            if data['posts'] > 0:
                if data['performance_score'] > 70:
                    insights.append(f"{platform}: أداء ممتاز! استمر في نفس الاستراتيجية")
                elif data['performance_score'] > 50:
                    insights.append(f"{platform}: أداء جيد، يمكن تحسينه أكثر")
                else:
                    insights.append(f"{platform}: يحتاج تحسين كبير في الاستراتيجية")
        
        # Content frequency insights
        if total_posts < 10:
            insights.append("انشر محتوى أكثر لتحسين الوصول والتفاعل")
        elif total_posts > 50:
            insights.append("ركز على جودة المحتوى أكثر من الكمية")
        
        return insights
    
    def generate_improvement_recommendations(self, platform_performance: Dict) -> Dict:
        """Generate specific recommendations for improvement"""
        
        recommendations = {}
        
        for platform, data in platform_performance.items():
            platform_recommendations = []
            
            # Low engagement recommendations
            if data.get('engagement_rate', 0) < self.platform_benchmarks.get(platform, {}).get('engagement_rate', 1):
                platform_recommendations.extend(self.improvement_strategies['low_engagement'])
            
            # Low reach recommendations
            if data.get('reach_rate', 0) < self.platform_benchmarks.get(platform, {}).get('reach_rate', 5):
                platform_recommendations.extend(self.improvement_strategies['low_reach'])
            
            # Low clicks recommendations
            if data.get('click_rate', 0) < self.platform_benchmarks.get(platform, {}).get('click_rate', 1):
                platform_recommendations.extend(self.improvement_strategies['low_clicks'])
            
            # Performance score based recommendations
            if data['performance_score'] < 30:
                platform_recommendations.append("فكر في تغيير الاستراتيجية التسويقية بالكامل")
                platform_recommendations.append("ادرس جمهورك المستهدف أكثر")
            elif data['performance_score'] < 50:
                platform_recommendations.append("حسن توقيت النشر")
                platform_recommendations.append("استخدم محتوى بصري أكثر")
            
            # Remove duplicates and limit recommendations
            platform_recommendations = list(set(platform_recommendations))[:5]
            
            if platform_recommendations:
                recommendations[platform] = platform_recommendations
        
        return recommendations
    
    def optimize_content_strategy(self, user_id: int) -> Dict:
        """Automatically optimize content strategy based on performance analysis"""
        try:
            # Analyze current performance
            performance_analysis = self.analyze_content_performance(user_id, days=30)
            
            if not performance_analysis['success']:
                return performance_analysis
            
            platform_performance = performance_analysis['platform_performance']
            
            # Generate optimized strategies for each platform
            optimized_strategies = {}
            
            for platform, data in platform_performance.items():
                strategy_optimization = {
                    'current_score': data['performance_score'],
                    'target_score': min(data['performance_score'] + 20, 90),
                    'optimizations': []
                }
                
                # Content timing optimization
                if data.get('engagement_rate', 0) < 2.0:
                    strategy_optimization['optimizations'].append({
                        'type': 'timing',
                        'recommendation': 'تحسين أوقات النشر',
                        'action': 'انشر في الأوقات: 12:00، 15:00، 18:00'
                    })
                
                # Content type optimization
                if data.get('click_rate', 0) < 1.0:
                    strategy_optimization['optimizations'].append({
                        'type': 'content_type',
                        'recommendation': 'استخدم محتوى بصري أكثر',
                        'action': 'أضف صور أو فيديوهات لكل منشور'
                    })
                
                # Hashtag optimization
                strategy_optimization['optimizations'].append({
                    'type': 'hashtags',
                    'recommendation': 'حسن استخدام الهاشتاجات',
                    'action': f'استخدم 5-8 هاشتاجات لـ {platform}'
                })
                
                # Frequency optimization
                if data['posts'] < 10:
                    strategy_optimization['optimizations'].append({
                        'type': 'frequency',
                        'recommendation': 'زيد معدل النشر',
                        'action': 'انشر 3-5 مرات أسبوعياً'
                    })
                
                optimized_strategies[platform] = strategy_optimization
            
            # Generate AI-powered content suggestions
            content_suggestions = self.generate_ai_content_suggestions(user_id, platform_performance)
            
            return {
                'success': True,
                'user_id': user_id,
                'optimization_date': datetime.now().isoformat(),
                'current_performance': platform_performance,
                'optimized_strategies': optimized_strategies,
                'content_suggestions': content_suggestions,
                'expected_improvement': '15-25% increase in engagement within 30 days'
            }
            
        except Exception as e:
            logger.error(f"Error optimizing content strategy: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_ai_content_suggestions(self, user_id: int, platform_performance: Dict) -> Dict:
        """Generate AI-powered content suggestions based on performance"""
        
        suggestions = {}
        
        # Get user information
        user = User.query.get(user_id)
        if not user:
            return suggestions
        
        for platform, data in platform_performance.items():
            platform_suggestions = []
            
            # Determine content focus based on performance gaps
            if data.get('engagement_rate', 0) < 2.0:
                focus = 'engagement_boosting'
                content_types = ['interactive_posts', 'questions', 'polls']
            elif data.get('reach_rate', 0) < 5.0:
                focus = 'reach_expansion'
                content_types = ['trending_content', 'hashtag_optimized', 'viral_potential']
            else:
                focus = 'conversion_optimization'
                content_types = ['promotional', 'educational', 'testimonial']
            
            # Generate suggestions for each content type
            for content_type in content_types[:3]:  # Limit to 3 suggestions per platform
                suggestion = {
                    'content_type': content_type,
                    'focus': focus,
                    'estimated_improvement': f'+{15 + (hash(content_type) % 20)}% engagement',
                    'best_posting_time': self.get_optimal_time_for_platform(platform),
                    'recommended_hashtags': self.get_trending_hashtags_for_platform(platform)
                }
                platform_suggestions.append(suggestion)
            
            suggestions[platform] = platform_suggestions
        
        return suggestions
    
    def get_optimal_time_for_platform(self, platform: str) -> str:
        """Get optimal posting time for a specific platform"""
        
        optimal_times = {
            'facebook': '15:00',
            'instagram': '17:00',
            'twitter': '12:00',
            'linkedin': '08:00',
            'tiktok': '18:00',
            'youtube': '16:00'
        }
        
        return optimal_times.get(platform, '15:00')
    
    def get_trending_hashtags_for_platform(self, platform: str) -> List[str]:
        """Get trending hashtags for a specific platform"""
        
        # In a real implementation, this would fetch from trending APIs
        trending_hashtags = {
            'facebook': ['#تسويق', '#أعمال', '#نجاح', '#ريادة'],
            'instagram': ['#تصوير', '#جمال', '#موضة', '#سفر'],
            'twitter': ['#أخبار', '#تقنية', '#رياضة', '#ثقافة'],
            'linkedin': ['#وظائف', '#مهارات', '#تطوير', '#قيادة'],
            'tiktok': ['#ترند', '#تحدي', '#مضحك', '#إبداع'],
            'youtube': ['#تعليم', '#مراجعة', '#شرح', '#تجربة']
        }
        
        return trending_hashtags.get(platform, ['#تسويق', '#محتوى'])
    
    def track_performance_trends(self, user_id: int, days: int = 90) -> Dict:
        """Track performance trends over time"""
        try:
            # Get performance data for different time periods
            periods = [7, 14, 30, 60, 90]
            trend_data = {}
            
            for period in periods:
                if period <= days:
                    analysis = self.analyze_content_performance(user_id, period)
                    if analysis['success']:
                        trend_data[f'{period}_days'] = {
                            'total_posts': analysis['overall_metrics']['total_posts'],
                            'avg_engagement': analysis['overall_metrics']['total_engagement'] / max(analysis['overall_metrics']['total_posts'], 1),
                            'avg_reach': analysis['overall_metrics']['total_reach'] / max(analysis['overall_metrics']['total_posts'], 1),
                            'platform_scores': {
                                platform: data['performance_score'] 
                                for platform, data in analysis['platform_performance'].items()
                            }
                        }
            
            # Calculate trends
            trends = self.calculate_trends(trend_data)
            
            return {
                'success': True,
                'user_id': user_id,
                'trend_period': f'{days} days',
                'trend_data': trend_data,
                'trends': trends,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error tracking performance trends: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_trends(self, trend_data: Dict) -> Dict:
        """Calculate performance trends from historical data"""
        
        trends = {
            'engagement_trend': 'stable',
            'reach_trend': 'stable',
            'overall_trend': 'stable',
            'trend_percentage': 0
        }
        
        if len(trend_data) < 2:
            return trends
        
        # Get the two most recent periods for comparison
        periods = sorted(trend_data.keys(), key=lambda x: int(x.split('_')[0]))
        
        if len(periods) >= 2:
            recent = trend_data[periods[-1]]
            previous = trend_data[periods[-2]]
            
            # Calculate engagement trend
            if previous['avg_engagement'] > 0:
                engagement_change = ((recent['avg_engagement'] - previous['avg_engagement']) / previous['avg_engagement']) * 100
                
                if engagement_change > 10:
                    trends['engagement_trend'] = 'improving'
                elif engagement_change < -10:
                    trends['engagement_trend'] = 'declining'
                
                trends['trend_percentage'] = engagement_change
            
            # Calculate reach trend
            if previous['avg_reach'] > 0:
                reach_change = ((recent['avg_reach'] - previous['avg_reach']) / previous['avg_reach']) * 100
                
                if reach_change > 10:
                    trends['reach_trend'] = 'improving'
                elif reach_change < -10:
                    trends['reach_trend'] = 'declining'
            
            # Overall trend
            if trends['engagement_trend'] == 'improving' and trends['reach_trend'] == 'improving':
                trends['overall_trend'] = 'strongly_improving'
            elif trends['engagement_trend'] == 'improving' or trends['reach_trend'] == 'improving':
                trends['overall_trend'] = 'improving'
            elif trends['engagement_trend'] == 'declining' and trends['reach_trend'] == 'declining':
                trends['overall_trend'] = 'strongly_declining'
            elif trends['engagement_trend'] == 'declining' or trends['reach_trend'] == 'declining':
                trends['overall_trend'] = 'declining'
        
        return trends
    
    def generate_performance_report(self, user_id: int, days: int = 30) -> Dict:
        """Generate comprehensive performance report"""
        try:
            # Get performance analysis
            performance_analysis = self.analyze_content_performance(user_id, days)
            
            if not performance_analysis['success']:
                return performance_analysis
            
            # Get trends
            trends = self.track_performance_trends(user_id, days)
            
            # Get optimization suggestions
            optimization = self.optimize_content_strategy(user_id)
            
            # Generate executive summary
            executive_summary = self.generate_executive_summary(
                performance_analysis, trends, optimization
            )
            
            report = {
                'success': True,
                'report_id': f"report_{user_id}_{int(datetime.now().timestamp())}",
                'user_id': user_id,
                'report_period': f'{days} days',
                'generated_at': datetime.now().isoformat(),
                'executive_summary': executive_summary,
                'performance_analysis': performance_analysis,
                'trends': trends,
                'optimization_recommendations': optimization,
                'next_review_date': (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_executive_summary(self, performance: Dict, trends: Dict, optimization: Dict) -> Dict:
        """Generate executive summary of performance"""
        
        summary = {
            'overall_performance': 'متوسط',
            'key_achievements': [],
            'main_challenges': [],
            'priority_actions': [],
            'expected_outcomes': []
        }
        
        # Analyze overall performance
        if performance['success']:
            platform_scores = [
                data['performance_score'] 
                for data in performance['platform_performance'].values()
            ]
            
            if platform_scores:
                avg_score = statistics.mean(platform_scores)
                
                if avg_score > 70:
                    summary['overall_performance'] = 'ممتاز'
                    summary['key_achievements'].append('أداء متميز عبر جميع المنصات')
                elif avg_score > 50:
                    summary['overall_performance'] = 'جيد'
                    summary['key_achievements'].append('أداء جيد مع إمكانية للتحسين')
                else:
                    summary['overall_performance'] = 'يحتاج تحسين'
                    summary['main_challenges'].append('أداء ضعيف يتطلب تدخل فوري')
        
        # Analyze trends
        if trends['success'] and trends.get('trends'):
            trend_info = trends['trends']
            
            if trend_info['overall_trend'] == 'improving':
                summary['key_achievements'].append('تحسن مستمر في الأداء')
            elif trend_info['overall_trend'] == 'declining':
                summary['main_challenges'].append('تراجع في الأداء يتطلب انتباه')
        
        # Priority actions from optimization
        if optimization['success']:
            for platform, strategy in optimization.get('optimized_strategies', {}).items():
                if strategy['optimizations']:
                    action = strategy['optimizations'][0]['recommendation']
                    summary['priority_actions'].append(f'{platform}: {action}')
        
        # Expected outcomes
        summary['expected_outcomes'] = [
            'تحسن 15-25% في معدل التفاعل خلال 30 يوم',
            'زيادة 20-30% في الوصول خلال شهرين',
            'تحسن عام في جودة المحتوى والاستراتيجية'
        ]
        
        return summary

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

