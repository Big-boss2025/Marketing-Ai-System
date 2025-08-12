import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import random
from collections import defaultdict, Counter
import statistics
from src.models.content import Content
from src.models.task import Task
from src.models.user import User

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Advanced Analytics and Reporting Engine for Clients"""
    
    def __init__(self):
        # Performance metrics weights
        self.metric_weights = {
            'views': 0.25,
            'likes': 0.20,
            'shares': 0.20,
            'comments': 0.15,
            'saves': 0.10,
            'click_through_rate': 0.10
        }
        
        # Platform benchmarks (industry averages)
        self.platform_benchmarks = {
            'instagram': {
                'engagement_rate': 0.018,  # 1.8%
                'reach_rate': 0.12,       # 12%
                'save_rate': 0.005,       # 0.5%
                'share_rate': 0.003       # 0.3%
            },
            'tiktok': {
                'engagement_rate': 0.055,  # 5.5%
                'reach_rate': 0.25,       # 25%
                'save_rate': 0.008,       # 0.8%
                'share_rate': 0.015       # 1.5%
            },
            'youtube': {
                'engagement_rate': 0.025,  # 2.5%
                'reach_rate': 0.08,       # 8%
                'save_rate': 0.012,       # 1.2%
                'share_rate': 0.005       # 0.5%
            },
            'facebook': {
                'engagement_rate': 0.015,  # 1.5%
                'reach_rate': 0.10,       # 10%
                'save_rate': 0.003,       # 0.3%
                'share_rate': 0.004       # 0.4%
            },
            'twitter': {
                'engagement_rate': 0.020,  # 2.0%
                'reach_rate': 0.15,       # 15%
                'save_rate': 0.002,       # 0.2%
                'share_rate': 0.008       # 0.8%
            }
        }
        
        # Content performance categories
        self.performance_categories = {
            'excellent': {'min_score': 85, 'color': '#10B981', 'label': 'ممتاز'},
            'good': {'min_score': 70, 'color': '#3B82F6', 'label': 'جيد'},
            'average': {'min_score': 50, 'color': '#F59E0B', 'label': 'متوسط'},
            'poor': {'min_score': 0, 'color': '#EF4444', 'label': 'ضعيف'}
        }
        
        # Report templates
        self.report_templates = {
            'weekly': {
                'metrics': ['views', 'engagement', 'reach', 'growth'],
                'charts': ['line', 'bar', 'pie'],
                'insights': ['top_content', 'best_times', 'audience_growth']
            },
            'monthly': {
                'metrics': ['views', 'engagement', 'reach', 'growth', 'roi'],
                'charts': ['line', 'bar', 'pie', 'heatmap'],
                'insights': ['content_analysis', 'audience_demographics', 'competitor_comparison']
            },
            'campaign': {
                'metrics': ['conversions', 'ctr', 'cost_per_click', 'roi'],
                'charts': ['funnel', 'line', 'bar'],
                'insights': ['campaign_performance', 'optimization_suggestions']
            }
        }
    
    def generate_comprehensive_report(self, user_id: int, 
                                    report_type: str = 'weekly',
                                    date_range: Dict = None) -> Dict:
        """Generate comprehensive analytics report"""
        try:
            if not date_range:
                end_date = datetime.utcnow()
                if report_type == 'weekly':
                    start_date = end_date - timedelta(days=7)
                elif report_type == 'monthly':
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=7)
                
                date_range = {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            
            # Get user data
            user_data = self.get_user_analytics_data(user_id, date_range)
            
            # Generate different report sections
            overview = self.generate_overview_metrics(user_data)
            content_performance = self.analyze_content_performance(user_data)
            audience_insights = self.analyze_audience_insights(user_data)
            platform_analysis = self.analyze_platform_performance(user_data)
            growth_analysis = self.analyze_growth_trends(user_data)
            recommendations = self.generate_recommendations(user_data)
            
            # Generate visualizations data
            charts_data = self.generate_charts_data(user_data, report_type)
            
            report = {
                'success': True,
                'report_id': f"report_{user_id}_{int(datetime.utcnow().timestamp())}",
                'user_id': user_id,
                'report_type': report_type,
                'date_range': date_range,
                'generated_at': datetime.utcnow().isoformat(),
                'overview': overview,
                'content_performance': content_performance,
                'audience_insights': audience_insights,
                'platform_analysis': platform_analysis,
                'growth_analysis': growth_analysis,
                'recommendations': recommendations,
                'charts_data': charts_data,
                'summary': self.generate_report_summary(overview, content_performance, growth_analysis)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_user_analytics_data(self, user_id: int, date_range: Dict) -> Dict:
        """Get user analytics data from database"""
        try:
            # In a real implementation, this would query the database
            # For now, we'll simulate realistic data
            
            start_date = datetime.fromisoformat(date_range['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(date_range['end_date'].replace('Z', '+00:00'))
            days_count = (end_date - start_date).days
            
            # Simulate content data
            content_data = []
            platforms = ['instagram', 'tiktok', 'youtube', 'facebook', 'twitter']
            content_types = ['image', 'video', 'carousel', 'story']
            
            for i in range(random.randint(10, 30)):  # 10-30 posts
                platform = random.choice(platforms)
                content_type = random.choice(content_types)
                
                # Generate realistic metrics based on platform
                base_views = random.randint(1000, 50000)
                engagement_rate = random.uniform(0.01, 0.08)
                
                content_item = {
                    'id': f"content_{i}",
                    'platform': platform,
                    'content_type': content_type,
                    'published_at': (start_date + timedelta(days=random.randint(0, days_count))).isoformat(),
                    'metrics': {
                        'views': base_views,
                        'likes': int(base_views * engagement_rate * random.uniform(0.6, 0.8)),
                        'comments': int(base_views * engagement_rate * random.uniform(0.1, 0.3)),
                        'shares': int(base_views * engagement_rate * random.uniform(0.05, 0.2)),
                        'saves': int(base_views * engagement_rate * random.uniform(0.02, 0.1)),
                        'reach': int(base_views * random.uniform(0.7, 1.2)),
                        'impressions': int(base_views * random.uniform(1.2, 2.0))
                    },
                    'performance_score': random.uniform(40, 95)
                }
                content_data.append(content_item)
            
            # Simulate audience data
            audience_data = {
                'total_followers': random.randint(5000, 100000),
                'new_followers': random.randint(100, 2000),
                'demographics': {
                    'age_groups': {
                        '18-24': random.uniform(0.2, 0.4),
                        '25-34': random.uniform(0.3, 0.5),
                        '35-44': random.uniform(0.15, 0.25),
                        '45+': random.uniform(0.05, 0.15)
                    },
                    'gender': {
                        'male': random.uniform(0.4, 0.6),
                        'female': random.uniform(0.4, 0.6)
                    },
                    'locations': {
                        'Egypt': random.uniform(0.3, 0.5),
                        'Saudi Arabia': random.uniform(0.2, 0.3),
                        'UAE': random.uniform(0.1, 0.2),
                        'Other': random.uniform(0.1, 0.3)
                    }
                }
            }
            
            return {
                'user_id': user_id,
                'date_range': date_range,
                'content_data': content_data,
                'audience_data': audience_data,
                'platforms': list(set(item['platform'] for item in content_data))
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics data: {str(e)}")
            return {}
    
    def generate_overview_metrics(self, user_data: Dict) -> Dict:
        """Generate overview metrics"""
        try:
            content_data = user_data.get('content_data', [])
            audience_data = user_data.get('audience_data', {})
            
            if not content_data:
                return {'error': 'No content data available'}
            
            # Calculate total metrics
            total_views = sum(item['metrics']['views'] for item in content_data)
            total_likes = sum(item['metrics']['likes'] for item in content_data)
            total_comments = sum(item['metrics']['comments'] for item in content_data)
            total_shares = sum(item['metrics']['shares'] for item in content_data)
            total_reach = sum(item['metrics']['reach'] for item in content_data)
            
            # Calculate engagement rate
            total_engagement = total_likes + total_comments + total_shares
            engagement_rate = (total_engagement / total_reach) if total_reach > 0 else 0
            
            # Calculate average performance score
            avg_performance = statistics.mean(item['performance_score'] for item in content_data)
            
            # Calculate growth metrics (comparing with previous period)
            # Simulated growth data
            growth_metrics = {
                'followers_growth': random.uniform(-5, 25),  # percentage
                'engagement_growth': random.uniform(-10, 30),
                'reach_growth': random.uniform(-8, 35),
                'content_performance_growth': random.uniform(-5, 20)
            }
            
            overview = {
                'total_content': len(content_data),
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_shares': total_shares,
                'total_reach': total_reach,
                'engagement_rate': round(engagement_rate, 4),
                'avg_performance_score': round(avg_performance, 1),
                'total_followers': audience_data.get('total_followers', 0),
                'new_followers': audience_data.get('new_followers', 0),
                'growth_metrics': growth_metrics,
                'top_performing_platform': self.get_top_performing_platform(content_data),
                'best_content_type': self.get_best_content_type(content_data)
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error generating overview metrics: {str(e)}")
            return {'error': str(e)}
    
    def analyze_content_performance(self, user_data: Dict) -> Dict:
        """Analyze content performance"""
        try:
            content_data = user_data.get('content_data', [])
            
            if not content_data:
                return {'error': 'No content data available'}
            
            # Sort content by performance score
            sorted_content = sorted(content_data, key=lambda x: x['performance_score'], reverse=True)
            
            # Get top and bottom performers
            top_performers = sorted_content[:5]
            bottom_performers = sorted_content[-3:]
            
            # Analyze by content type
            content_type_performance = defaultdict(list)
            for item in content_data:
                content_type_performance[item['content_type']].append(item['performance_score'])
            
            content_type_avg = {
                content_type: statistics.mean(scores)
                for content_type, scores in content_type_performance.items()
            }
            
            # Analyze by platform
            platform_performance = defaultdict(list)
            for item in content_data:
                platform_performance[item['platform']].append(item['performance_score'])
            
            platform_avg = {
                platform: statistics.mean(scores)
                for platform, scores in platform_performance.items()
            }
            
            # Performance distribution
            performance_distribution = {
                'excellent': len([item for item in content_data if item['performance_score'] >= 85]),
                'good': len([item for item in content_data if 70 <= item['performance_score'] < 85]),
                'average': len([item for item in content_data if 50 <= item['performance_score'] < 70]),
                'poor': len([item for item in content_data if item['performance_score'] < 50])
            }
            
            return {
                'top_performers': top_performers,
                'bottom_performers': bottom_performers,
                'content_type_performance': dict(content_type_avg),
                'platform_performance': dict(platform_avg),
                'performance_distribution': performance_distribution,
                'total_content_analyzed': len(content_data),
                'average_score': round(statistics.mean(item['performance_score'] for item in content_data), 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {str(e)}")
            return {'error': str(e)}
    
    def analyze_audience_insights(self, user_data: Dict) -> Dict:
        """Analyze audience insights"""
        try:
            audience_data = user_data.get('audience_data', {})
            content_data = user_data.get('content_data', [])
            
            if not audience_data:
                return {'error': 'No audience data available'}
            
            demographics = audience_data.get('demographics', {})
            
            # Calculate engagement by demographics (simulated)
            engagement_by_age = {
                '18-24': random.uniform(0.04, 0.08),
                '25-34': random.uniform(0.03, 0.06),
                '35-44': random.uniform(0.02, 0.05),
                '45+': random.uniform(0.01, 0.03)
            }
            
            # Best posting times analysis
            posting_times_analysis = self.analyze_posting_times(content_data)
            
            # Audience growth trend
            growth_trend = self.generate_audience_growth_trend()
            
            return {
                'total_followers': audience_data.get('total_followers', 0),
                'new_followers': audience_data.get('new_followers', 0),
                'demographics': demographics,
                'engagement_by_age': engagement_by_age,
                'posting_times_analysis': posting_times_analysis,
                'growth_trend': growth_trend,
                'audience_quality_score': random.uniform(70, 95),
                'most_active_age_group': max(engagement_by_age.items(), key=lambda x: x[1])[0],
                'primary_location': max(demographics.get('locations', {}).items(), key=lambda x: x[1])[0] if demographics.get('locations') else 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audience insights: {str(e)}")
            return {'error': str(e)}
    
    def analyze_platform_performance(self, user_data: Dict) -> Dict:
        """Analyze performance by platform"""
        try:
            content_data = user_data.get('content_data', [])
            platforms = user_data.get('platforms', [])
            
            platform_metrics = {}
            
            for platform in platforms:
                platform_content = [item for item in content_data if item['platform'] == platform]
                
                if platform_content:
                    total_views = sum(item['metrics']['views'] for item in platform_content)
                    total_engagement = sum(
                        item['metrics']['likes'] + item['metrics']['comments'] + item['metrics']['shares']
                        for item in platform_content
                    )
                    total_reach = sum(item['metrics']['reach'] for item in platform_content)
                    
                    engagement_rate = (total_engagement / total_reach) if total_reach > 0 else 0
                    avg_performance = statistics.mean(item['performance_score'] for item in platform_content)
                    
                    # Compare with benchmarks
                    benchmark = self.platform_benchmarks.get(platform, {})
                    benchmark_engagement = benchmark.get('engagement_rate', 0.02)
                    
                    performance_vs_benchmark = (engagement_rate / benchmark_engagement) if benchmark_engagement > 0 else 1
                    
                    platform_metrics[platform] = {
                        'content_count': len(platform_content),
                        'total_views': total_views,
                        'total_engagement': total_engagement,
                        'total_reach': total_reach,
                        'engagement_rate': round(engagement_rate, 4),
                        'avg_performance_score': round(avg_performance, 1),
                        'benchmark_comparison': round(performance_vs_benchmark, 2),
                        'performance_status': 'above_benchmark' if performance_vs_benchmark > 1 else 'below_benchmark'
                    }
            
            # Rank platforms by performance
            ranked_platforms = sorted(
                platform_metrics.items(),
                key=lambda x: x[1]['avg_performance_score'],
                reverse=True
            )
            
            return {
                'platform_metrics': platform_metrics,
                'ranked_platforms': ranked_platforms,
                'best_performing_platform': ranked_platforms[0][0] if ranked_platforms else None,
                'total_platforms': len(platforms),
                'platform_distribution': {
                    platform: len([item for item in content_data if item['platform'] == platform])
                    for platform in platforms
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing platform performance: {str(e)}")
            return {'error': str(e)}
    
    def analyze_growth_trends(self, user_data: Dict) -> Dict:
        """Analyze growth trends"""
        try:
            content_data = user_data.get('content_data', [])
            
            # Generate growth trend data (simulated)
            days = 7  # For weekly report
            growth_data = []
            
            base_followers = random.randint(5000, 50000)
            base_engagement = random.randint(500, 5000)
            
            for i in range(days):
                day_data = {
                    'date': (datetime.utcnow() - timedelta(days=days-i-1)).strftime('%Y-%m-%d'),
                    'followers': base_followers + random.randint(-50, 200),
                    'engagement': base_engagement + random.randint(-100, 500),
                    'reach': random.randint(1000, 10000),
                    'content_published': random.randint(0, 3)
                }
                growth_data.append(day_data)
                base_followers = day_data['followers']
                base_engagement = day_data['engagement']
            
            # Calculate growth rates
            if len(growth_data) >= 2:
                followers_growth = ((growth_data[-1]['followers'] - growth_data[0]['followers']) / growth_data[0]['followers']) * 100
                engagement_growth = ((growth_data[-1]['engagement'] - growth_data[0]['engagement']) / growth_data[0]['engagement']) * 100
            else:
                followers_growth = 0
                engagement_growth = 0
            
            # Predict next week performance
            predicted_growth = self.predict_growth_trend(growth_data)
            
            return {
                'daily_growth_data': growth_data,
                'followers_growth_rate': round(followers_growth, 2),
                'engagement_growth_rate': round(engagement_growth, 2),
                'growth_trend': 'increasing' if followers_growth > 0 else 'decreasing',
                'predicted_growth': predicted_growth,
                'growth_consistency': self.calculate_growth_consistency(growth_data),
                'best_growth_day': max(growth_data, key=lambda x: x['followers'])['date'],
                'total_growth_score': random.uniform(60, 90)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing growth trends: {str(e)}")
            return {'error': str(e)}
    
    def generate_recommendations(self, user_data: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        try:
            content_data = user_data.get('content_data', [])
            recommendations = []
            
            # Content performance recommendations
            if content_data:
                avg_performance = statistics.mean(item['performance_score'] for item in content_data)
                
                if avg_performance < 60:
                    recommendations.append({
                        'type': 'content_improvement',
                        'priority': 'high',
                        'title': 'تحسين جودة المحتوى',
                        'description': 'متوسط أداء المحتوى أقل من المتوقع. ننصح بالتركيز على المحتوى التفاعلي والجذاب.',
                        'action_items': [
                            'استخدم المزيد من الفيديوهات القصيرة',
                            'أضف قصص تفاعلية',
                            'استخدم الترندات الحالية'
                        ]
                    })
                
                # Platform-specific recommendations
                platform_performance = defaultdict(list)
                for item in content_data:
                    platform_performance[item['platform']].append(item['performance_score'])
                
                for platform, scores in platform_performance.items():
                    avg_score = statistics.mean(scores)
                    if avg_score < 50:
                        recommendations.append({
                            'type': 'platform_optimization',
                            'priority': 'medium',
                            'title': f'تحسين الأداء على {platform}',
                            'description': f'الأداء على منصة {platform} يحتاج إلى تحسين.',
                            'action_items': [
                                f'راجع أوقات النشر المثلى لـ {platform}',
                                f'استخدم الهاشتاجات الترندية لـ {platform}',
                                f'تفاعل أكثر مع الجمهور على {platform}'
                            ]
                        })
            
            # Engagement recommendations
            recommendations.append({
                'type': 'engagement_boost',
                'priority': 'medium',
                'title': 'زيادة التفاعل',
                'description': 'استراتيجيات لزيادة التفاعل مع المحتوى.',
                'action_items': [
                    'اطرح أسئلة في نهاية المنشورات',
                    'استخدم استطلاعات الرأي في الستوريز',
                    'رد على التعليقات بسرعة',
                    'شارك محتوى من إنشاء المتابعين'
                ]
            })
            
            # Growth recommendations
            recommendations.append({
                'type': 'growth_strategy',
                'priority': 'high',
                'title': 'استراتيجية النمو',
                'description': 'خطة لزيادة عدد المتابعين والوصول.',
                'action_items': [
                    'تعاون مع المؤثرين في مجالك',
                    'استخدم الإعلانات المدفوعة بذكاء',
                    'انشر محتوى في أوقات الذروة',
                    'استخدم الهاشتاجات المتنوعة'
                ]
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def generate_charts_data(self, user_data: Dict, report_type: str) -> Dict:
        """Generate data for charts and visualizations"""
        try:
            content_data = user_data.get('content_data', [])
            
            charts_data = {}
            
            # Performance over time (line chart)
            performance_timeline = []
            for item in content_data:
                performance_timeline.append({
                    'date': item['published_at'][:10],  # YYYY-MM-DD
                    'performance_score': item['performance_score'],
                    'views': item['metrics']['views'],
                    'engagement': item['metrics']['likes'] + item['metrics']['comments'] + item['metrics']['shares']
                })
            
            charts_data['performance_timeline'] = sorted(performance_timeline, key=lambda x: x['date'])
            
            # Platform distribution (pie chart)
            platform_distribution = Counter(item['platform'] for item in content_data)
            charts_data['platform_distribution'] = [
                {'platform': platform, 'count': count, 'percentage': (count/len(content_data))*100}
                for platform, count in platform_distribution.items()
            ]
            
            # Content type performance (bar chart)
            content_type_performance = defaultdict(list)
            for item in content_data:
                content_type_performance[item['content_type']].append(item['performance_score'])
            
            charts_data['content_type_performance'] = [
                {
                    'content_type': content_type,
                    'avg_performance': statistics.mean(scores),
                    'count': len(scores)
                }
                for content_type, scores in content_type_performance.items()
            ]
            
            # Engagement metrics (multi-bar chart)
            engagement_metrics = {
                'likes': sum(item['metrics']['likes'] for item in content_data),
                'comments': sum(item['metrics']['comments'] for item in content_data),
                'shares': sum(item['metrics']['shares'] for item in content_data),
                'saves': sum(item['metrics']['saves'] for item in content_data)
            }
            
            charts_data['engagement_metrics'] = [
                {'metric': metric, 'value': value}
                for metric, value in engagement_metrics.items()
            ]
            
            # Top performing content (horizontal bar chart)
            top_content = sorted(content_data, key=lambda x: x['performance_score'], reverse=True)[:10]
            charts_data['top_content'] = [
                {
                    'content_id': item['id'],
                    'platform': item['platform'],
                    'performance_score': item['performance_score'],
                    'views': item['metrics']['views']
                }
                for item in top_content
            ]
            
            return charts_data
            
        except Exception as e:
            logger.error(f"Error generating charts data: {str(e)}")
            return {}
    
    def generate_report_summary(self, overview: Dict, content_performance: Dict, growth_analysis: Dict) -> Dict:
        """Generate executive summary of the report"""
        try:
            summary = {
                'key_highlights': [],
                'performance_status': 'good',  # excellent, good, average, poor
                'main_achievements': [],
                'areas_for_improvement': [],
                'overall_score': 0
            }
            
            # Calculate overall score
            scores = []
            if 'avg_performance_score' in overview:
                scores.append(overview['avg_performance_score'])
            if 'total_growth_score' in growth_analysis:
                scores.append(growth_analysis['total_growth_score'])
            
            if scores:
                summary['overall_score'] = round(statistics.mean(scores), 1)
            
            # Determine performance status
            if summary['overall_score'] >= 85:
                summary['performance_status'] = 'excellent'
            elif summary['overall_score'] >= 70:
                summary['performance_status'] = 'good'
            elif summary['overall_score'] >= 50:
                summary['performance_status'] = 'average'
            else:
                summary['performance_status'] = 'poor'
            
            # Key highlights
            if overview.get('total_views', 0) > 10000:
                summary['key_highlights'].append(f"تحقيق {overview['total_views']:,} مشاهدة")
            
            if overview.get('engagement_rate', 0) > 0.03:
                summary['key_highlights'].append(f"معدل تفاعل ممتاز {overview['engagement_rate']:.1%}")
            
            if growth_analysis.get('followers_growth_rate', 0) > 5:
                summary['key_highlights'].append(f"نمو في المتابعين بنسبة {growth_analysis['followers_growth_rate']:.1f}%")
            
            # Main achievements
            if content_performance.get('performance_distribution', {}).get('excellent', 0) > 0:
                excellent_count = content_performance['performance_distribution']['excellent']
                summary['main_achievements'].append(f"{excellent_count} منشور حقق أداءً ممتازاً")
            
            if overview.get('top_performing_platform'):
                platform = overview['top_performing_platform']
                summary['main_achievements'].append(f"أداء متميز على منصة {platform}")
            
            # Areas for improvement
            if content_performance.get('performance_distribution', {}).get('poor', 0) > 0:
                poor_count = content_performance['performance_distribution']['poor']
                summary['areas_for_improvement'].append(f"تحسين {poor_count} منشور ضعيف الأداء")
            
            if overview.get('engagement_rate', 0) < 0.02:
                summary['areas_for_improvement'].append("زيادة معدل التفاعل")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating report summary: {str(e)}")
            return {'error': str(e)}
    
    # Helper methods
    def get_top_performing_platform(self, content_data: List[Dict]) -> str:
        """Get the top performing platform"""
        platform_scores = defaultdict(list)
        for item in content_data:
            platform_scores[item['platform']].append(item['performance_score'])
        
        platform_averages = {
            platform: statistics.mean(scores)
            for platform, scores in platform_scores.items()
        }
        
        return max(platform_averages.items(), key=lambda x: x[1])[0] if platform_averages else 'unknown'
    
    def get_best_content_type(self, content_data: List[Dict]) -> str:
        """Get the best performing content type"""
        content_type_scores = defaultdict(list)
        for item in content_data:
            content_type_scores[item['content_type']].append(item['performance_score'])
        
        content_type_averages = {
            content_type: statistics.mean(scores)
            for content_type, scores in content_type_scores.items()
        }
        
        return max(content_type_averages.items(), key=lambda x: x[1])[0] if content_type_averages else 'unknown'
    
    def analyze_posting_times(self, content_data: List[Dict]) -> Dict:
        """Analyze best posting times"""
        # Simulate posting times analysis
        return {
            'best_hours': ['19:00', '20:00', '21:00'],
            'best_days': ['Thursday', 'Friday', 'Saturday'],
            'worst_hours': ['03:00', '04:00', '05:00'],
            'optimal_frequency': '2-3 posts per day'
        }
    
    def generate_audience_growth_trend(self) -> List[Dict]:
        """Generate audience growth trend data"""
        trend_data = []
        base_followers = random.randint(5000, 50000)
        
        for i in range(30):  # Last 30 days
            day_followers = base_followers + random.randint(-100, 300)
            trend_data.append({
                'date': (datetime.utcnow() - timedelta(days=30-i)).strftime('%Y-%m-%d'),
                'followers': day_followers,
                'growth': day_followers - base_followers
            })
            base_followers = day_followers
        
        return trend_data
    
    def predict_growth_trend(self, growth_data: List[Dict]) -> Dict:
        """Predict future growth trend"""
        if len(growth_data) < 3:
            return {'prediction': 'insufficient_data'}
        
        # Simple linear prediction
        recent_growth = [item['followers'] for item in growth_data[-3:]]
        avg_growth = (recent_growth[-1] - recent_growth[0]) / len(recent_growth)
        
        predicted_followers = growth_data[-1]['followers'] + (avg_growth * 7)  # Next week
        
        return {
            'predicted_followers_next_week': int(predicted_followers),
            'predicted_growth_rate': round((avg_growth / growth_data[-1]['followers']) * 100, 2),
            'confidence': random.uniform(0.7, 0.9)
        }
    
    def calculate_growth_consistency(self, growth_data: List[Dict]) -> float:
        """Calculate growth consistency score"""
        if len(growth_data) < 2:
            return 0.0
        
        growth_rates = []
        for i in range(1, len(growth_data)):
            if growth_data[i-1]['followers'] > 0:
                rate = (growth_data[i]['followers'] - growth_data[i-1]['followers']) / growth_data[i-1]['followers']
                growth_rates.append(rate)
        
        if not growth_rates:
            return 0.0
        
        # Lower standard deviation means more consistent growth
        std_dev = statistics.stdev(growth_rates) if len(growth_rates) > 1 else 0
        consistency = max(0, 100 - (std_dev * 1000))  # Scale to 0-100
        
        return round(consistency, 1)

# Global analytics engine instance
analytics_engine = AnalyticsEngine()

