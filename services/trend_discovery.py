import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
import json
import requests
import random
from collections import Counter, defaultdict
from src.services.free_ai_generator import free_ai_generator
from src.services.geo_language_detector import geo_language_detector

logger = logging.getLogger(__name__)

class TrendDiscovery:
    """Advanced Trend Discovery and Analysis System"""
    
    def __init__(self):
        # Platform APIs for trend discovery
        self.platform_apis = {
            'tiktok': {
                'trending_hashtags_url': 'https://api.tiktok.com/trending/hashtags',
                'trending_sounds_url': 'https://api.tiktok.com/trending/sounds',
                'trending_effects_url': 'https://api.tiktok.com/trending/effects',
                'rate_limit': 100  # requests per hour
            },
            'instagram': {
                'trending_hashtags_url': 'https://graph.instagram.com/trending/hashtags',
                'trending_reels_url': 'https://graph.instagram.com/trending/reels',
                'rate_limit': 200
            },
            'youtube': {
                'trending_videos_url': 'https://www.googleapis.com/youtube/v3/videos',
                'trending_keywords_url': 'https://www.googleapis.com/youtube/v3/search',
                'rate_limit': 10000
            },
            'twitter': {
                'trending_topics_url': 'https://api.twitter.com/2/trends/by/woeid',
                'trending_hashtags_url': 'https://api.twitter.com/2/tweets/search/recent',
                'rate_limit': 300
            }
        }
        
        # Trend categories
        self.trend_categories = {
            'viral_content': {
                'keywords': ['viral', 'trending', 'challenge', 'dance', 'meme'],
                'weight': 1.0
            },
            'news_events': {
                'keywords': ['breaking', 'news', 'event', 'happening', 'live'],
                'weight': 0.8
            },
            'entertainment': {
                'keywords': ['movie', 'music', 'celebrity', 'show', 'series'],
                'weight': 0.7
            },
            'technology': {
                'keywords': ['tech', 'ai', 'innovation', 'gadget', 'app'],
                'weight': 0.6
            },
            'lifestyle': {
                'keywords': ['fashion', 'beauty', 'food', 'travel', 'fitness'],
                'weight': 0.5
            },
            'business': {
                'keywords': ['business', 'startup', 'investment', 'money', 'success'],
                'weight': 0.4
            }
        }
        
        # Arabic trend patterns
        self.arabic_trend_patterns = {
            'viral_indicators': [
                'ترند', 'فيروسي', 'منتشر', 'رائج', 'شائع', 'مشهور', 'تحدي',
                'رقص', 'ميم', 'مضحك', 'جديد', 'عاجل', 'حصري'
            ],
            'engagement_words': [
                'شارك', 'احفظ', 'تابع', 'لايك', 'كومنت', 'تفاعل', 'انشر',
                'جرب', 'اكتشف', 'تعلم', 'شاهد', 'استمع'
            ],
            'emotional_triggers': [
                'مذهل', 'رائع', 'لا_يصدق', 'صادم', 'مؤثر', 'ملهم', 'مضحك',
                'حزين', 'سعيد', 'غاضب', 'متحمس', 'فخور'
            ]
        }
        
        # Trend scoring weights
        self.scoring_weights = {
            'engagement_rate': 0.3,
            'growth_velocity': 0.25,
            'reach_potential': 0.2,
            'recency': 0.15,
            'relevance': 0.1
        }
        
        # Platform-specific trend indicators
        self.platform_indicators = {
            'tiktok': {
                'viral_threshold': 100000,  # views
                'engagement_threshold': 0.1,  # 10%
                'growth_threshold': 50,  # 50% growth in 24h
                'trending_duration': 3  # days
            },
            'instagram': {
                'viral_threshold': 50000,
                'engagement_threshold': 0.08,
                'growth_threshold': 40,
                'trending_duration': 5
            },
            'youtube': {
                'viral_threshold': 500000,
                'engagement_threshold': 0.05,
                'growth_threshold': 30,
                'trending_duration': 7
            },
            'twitter': {
                'viral_threshold': 10000,
                'engagement_threshold': 0.15,
                'growth_threshold': 100,
                'trending_duration': 1
            }
        }
    
    def discover_trending_topics(self, platform: str = 'all', 
                               language: str = 'ar', 
                               region: str = 'middle_east') -> Dict:
        """Discover current trending topics across platforms"""
        try:
            if platform == 'all':
                platforms = ['tiktok', 'instagram', 'youtube', 'twitter']
            else:
                platforms = [platform]
            
            all_trends = {}
            
            for p in platforms:
                trends = self.get_platform_trends(p, language, region)
                if trends['success']:
                    all_trends[p] = trends['trends']
            
            # Combine and rank trends
            combined_trends = self.combine_platform_trends(all_trends, language)
            
            # Generate trend insights
            insights = self.generate_trend_insights(combined_trends, language)
            
            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'platform': platform,
                'language': language,
                'region': region,
                'trending_topics': combined_trends,
                'insights': insights,
                'recommendations': self.generate_trend_recommendations(combined_trends, language)
            }
            
        except Exception as e:
            logger.error(f"Error discovering trending topics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_platform_trends(self, platform: str, language: str, region: str) -> Dict:
        """Get trending topics from a specific platform"""
        try:
            # Simulate API calls (in real implementation, these would be actual API calls)
            # For now, we'll generate realistic trending data
            
            trends = self.generate_simulated_trends(platform, language, region)
            
            # Score and rank trends
            scored_trends = []
            for trend in trends:
                score = self.calculate_trend_score(trend, platform)
                trend['score'] = score
                trend['platform'] = platform
                scored_trends.append(trend)
            
            # Sort by score
            scored_trends.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'success': True,
                'platform': platform,
                'trends': scored_trends[:20],  # Top 20 trends
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting {platform} trends: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_simulated_trends(self, platform: str, language: str, region: str) -> List[Dict]:
        """Generate realistic trending data for simulation"""
        trends = []
        
        if language == 'ar':
            trend_topics = [
                # Technology trends
                {'topic': 'الذكاء_الاصطناعي', 'category': 'technology', 'hashtags': ['#الذكاء_الاصطناعي', '#تقنية', '#مستقبل']},
                {'topic': 'تطبيقات_جديدة', 'category': 'technology', 'hashtags': ['#تطبيقات', '#جديد', '#تقنية']},
                
                # Entertainment trends
                {'topic': 'تحدي_الرقص', 'category': 'viral_content', 'hashtags': ['#تحدي_الرقص', '#ترند', '#فيروسي']},
                {'topic': 'كوميديا_عربية', 'category': 'entertainment', 'hashtags': ['#كوميديا', '#مضحك', '#عربي']},
                
                # Lifestyle trends
                {'topic': 'وصفات_صحية', 'category': 'lifestyle', 'hashtags': ['#وصفات', '#صحي', '#طبخ']},
                {'topic': 'تمارين_منزلية', 'category': 'lifestyle', 'hashtags': ['#تمارين', '#لياقة', '#منزل']},
                
                # Business trends
                {'topic': 'ريادة_الأعمال', 'category': 'business', 'hashtags': ['#ريادة_أعمال', '#نجاح', '#استثمار']},
                {'topic': 'تسويق_رقمي', 'category': 'business', 'hashtags': ['#تسويق_رقمي', '#إعلان', '#أعمال']},
                
                # News trends
                {'topic': 'أخبار_التقنية', 'category': 'news_events', 'hashtags': ['#أخبار', '#تقنية', '#عاجل']},
                {'topic': 'أحداث_محلية', 'category': 'news_events', 'hashtags': ['#أحداث', '#محلي', '#مهم']}
            ]
        else:
            trend_topics = [
                # Technology trends
                {'topic': 'artificial_intelligence', 'category': 'technology', 'hashtags': ['#AI', '#tech', '#future']},
                {'topic': 'new_apps', 'category': 'technology', 'hashtags': ['#apps', '#new', '#technology']},
                
                # Entertainment trends
                {'topic': 'dance_challenge', 'category': 'viral_content', 'hashtags': ['#dancechallenge', '#trending', '#viral']},
                {'topic': 'comedy_content', 'category': 'entertainment', 'hashtags': ['#comedy', '#funny', '#entertainment']},
                
                # Lifestyle trends
                {'topic': 'healthy_recipes', 'category': 'lifestyle', 'hashtags': ['#healthy', '#recipes', '#cooking']},
                {'topic': 'home_workouts', 'category': 'lifestyle', 'hashtags': ['#workout', '#fitness', '#home']},
                
                # Business trends
                {'topic': 'entrepreneurship', 'category': 'business', 'hashtags': ['#entrepreneur', '#business', '#startup']},
                {'topic': 'digital_marketing', 'category': 'business', 'hashtags': ['#digitalmarketing', '#marketing', '#business']},
                
                # News trends
                {'topic': 'tech_news', 'category': 'news_events', 'hashtags': ['#technews', '#breaking', '#news']},
                {'topic': 'local_events', 'category': 'news_events', 'hashtags': ['#local', '#events', '#community']}
            ]
        
        # Generate trend data with realistic metrics
        for topic_data in trend_topics:
            indicators = self.platform_indicators.get(platform, {})
            
            trend = {
                'topic': topic_data['topic'],
                'category': topic_data['category'],
                'hashtags': topic_data['hashtags'],
                'engagement_rate': random.uniform(0.05, 0.25),
                'views': random.randint(
                    indicators.get('viral_threshold', 10000),
                    indicators.get('viral_threshold', 10000) * 10
                ),
                'growth_rate': random.uniform(20, 200),  # percentage
                'mentions': random.randint(100, 10000),
                'sentiment': random.choice(['positive', 'neutral', 'negative']),
                'age_hours': random.randint(1, 48),
                'geographic_spread': random.choice(['local', 'regional', 'global']),
                'predicted_duration': random.randint(1, 7),  # days
                'related_keywords': self.generate_related_keywords(topic_data['topic'], language)
            }
            
            trends.append(trend)
        
        return trends
    
    def generate_related_keywords(self, topic: str, language: str) -> List[str]:
        """Generate related keywords for a topic"""
        if language == 'ar':
            keyword_map = {
                'الذكاء_الاصطناعي': ['تقنية', 'مستقبل', 'روبوت', 'تعلم_آلي', 'ابتكار'],
                'تحدي_الرقص': ['رقص', 'موسيقى', 'حركة', 'إيقاع', 'تقليد'],
                'وصفات_صحية': ['طبخ', 'غذاء', 'صحة', 'مكونات', 'تغذية'],
                'ريادة_الأعمال': ['أعمال', 'مشروع', 'استثمار', 'نجاح', 'قيادة']
            }
        else:
            keyword_map = {
                'artificial_intelligence': ['technology', 'future', 'robot', 'machine_learning', 'innovation'],
                'dance_challenge': ['dance', 'music', 'movement', 'rhythm', 'viral'],
                'healthy_recipes': ['cooking', 'food', 'health', 'ingredients', 'nutrition'],
                'entrepreneurship': ['business', 'startup', 'investment', 'success', 'leadership']
            }
        
        return keyword_map.get(topic, [topic.replace('_', ' ').split()])
    
    def calculate_trend_score(self, trend: Dict, platform: str) -> float:
        """Calculate trend score based on multiple factors"""
        try:
            score = 0.0
            weights = self.scoring_weights
            
            # Engagement rate score
            engagement_rate = trend.get('engagement_rate', 0)
            engagement_score = min(engagement_rate * 10, 10)  # Max 10
            score += engagement_score * weights['engagement_rate']
            
            # Growth velocity score
            growth_rate = trend.get('growth_rate', 0)
            growth_score = min(growth_rate / 20, 10)  # Max 10
            score += growth_score * weights['growth_velocity']
            
            # Reach potential score
            views = trend.get('views', 0)
            indicators = self.platform_indicators.get(platform, {})
            viral_threshold = indicators.get('viral_threshold', 10000)
            reach_score = min((views / viral_threshold) * 5, 10)  # Max 10
            score += reach_score * weights['reach_potential']
            
            # Recency score
            age_hours = trend.get('age_hours', 24)
            recency_score = max(10 - (age_hours / 24) * 5, 0)  # Newer is better
            score += recency_score * weights['recency']
            
            # Relevance score (based on category)
            category = trend.get('category', 'lifestyle')
            category_weight = self.trend_categories.get(category, {}).get('weight', 0.5)
            relevance_score = category_weight * 10
            score += relevance_score * weights['relevance']
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {str(e)}")
            return 0.0
    
    def combine_platform_trends(self, platform_trends: Dict, language: str) -> List[Dict]:
        """Combine trends from multiple platforms"""
        try:
            combined = []
            topic_scores = defaultdict(list)
            
            # Collect all trends
            for platform, trends in platform_trends.items():
                for trend in trends:
                    topic = trend['topic']
                    topic_scores[topic].append({
                        'platform': platform,
                        'score': trend['score'],
                        'trend_data': trend
                    })
            
            # Create combined trends
            for topic, platform_data in topic_scores.items():
                # Calculate average score across platforms
                avg_score = sum(data['score'] for data in platform_data) / len(platform_data)
                
                # Get the best performing platform data
                best_platform_data = max(platform_data, key=lambda x: x['score'])
                
                combined_trend = best_platform_data['trend_data'].copy()
                combined_trend['average_score'] = avg_score
                combined_trend['platforms'] = [data['platform'] for data in platform_data]
                combined_trend['cross_platform'] = len(platform_data) > 1
                
                combined.append(combined_trend)
            
            # Sort by average score
            combined.sort(key=lambda x: x['average_score'], reverse=True)
            
            return combined[:15]  # Top 15 combined trends
            
        except Exception as e:
            logger.error(f"Error combining platform trends: {str(e)}")
            return []
    
    def generate_trend_insights(self, trends: List[Dict], language: str) -> Dict:
        """Generate insights from trending data"""
        try:
            if not trends:
                return {'message': 'No trends available for analysis'}
            
            # Category analysis
            category_counts = Counter(trend['category'] for trend in trends)
            top_category = category_counts.most_common(1)[0][0]
            
            # Platform analysis
            platform_mentions = []
            for trend in trends:
                platform_mentions.extend(trend.get('platforms', []))
            platform_counts = Counter(platform_mentions)
            top_platform = platform_counts.most_common(1)[0][0] if platform_counts else 'unknown'
            
            # Sentiment analysis
            sentiment_counts = Counter(trend['sentiment'] for trend in trends)
            dominant_sentiment = sentiment_counts.most_common(1)[0][0]
            
            # Growth analysis
            high_growth_trends = [t for t in trends if t.get('growth_rate', 0) > 100]
            
            insights = {
                'total_trends': len(trends),
                'top_category': top_category,
                'category_distribution': dict(category_counts),
                'top_platform': top_platform,
                'platform_distribution': dict(platform_counts),
                'dominant_sentiment': dominant_sentiment,
                'sentiment_distribution': dict(sentiment_counts),
                'high_growth_trends': len(high_growth_trends),
                'cross_platform_trends': len([t for t in trends if t.get('cross_platform', False)]),
                'average_engagement': round(
                    sum(t.get('engagement_rate', 0) for t in trends) / len(trends), 3
                ),
                'trending_hashtags': self.extract_trending_hashtags(trends),
                'opportunity_score': self.calculate_opportunity_score(trends)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating trend insights: {str(e)}")
            return {'error': str(e)}
    
    def extract_trending_hashtags(self, trends: List[Dict]) -> List[str]:
        """Extract most trending hashtags"""
        all_hashtags = []
        for trend in trends:
            all_hashtags.extend(trend.get('hashtags', []))
        
        hashtag_counts = Counter(all_hashtags)
        return [hashtag for hashtag, count in hashtag_counts.most_common(10)]
    
    def calculate_opportunity_score(self, trends: List[Dict]) -> float:
        """Calculate overall opportunity score for content creation"""
        if not trends:
            return 0.0
        
        # Factors that increase opportunity
        high_engagement = len([t for t in trends if t.get('engagement_rate', 0) > 0.1])
        high_growth = len([t for t in trends if t.get('growth_rate', 0) > 50])
        cross_platform = len([t for t in trends if t.get('cross_platform', False)])
        positive_sentiment = len([t for t in trends if t.get('sentiment') == 'positive'])
        
        total_trends = len(trends)
        
        score = (
            (high_engagement / total_trends) * 0.3 +
            (high_growth / total_trends) * 0.3 +
            (cross_platform / total_trends) * 0.2 +
            (positive_sentiment / total_trends) * 0.2
        ) * 100
        
        return round(score, 1)
    
    def generate_trend_recommendations(self, trends: List[Dict], language: str) -> List[Dict]:
        """Generate actionable recommendations based on trends"""
        try:
            recommendations = []
            
            if not trends:
                return recommendations
            
            # Top trend recommendation
            top_trend = trends[0]
            recommendations.append({
                'type': 'immediate_action',
                'priority': 'high',
                'title': f"استغل ترند '{top_trend['topic']}'" if language == 'ar' else f"Leverage '{top_trend['topic']}' trend",
                'description': f"هذا الترند يحقق معدل تفاعل {top_trend.get('engagement_rate', 0):.1%}" if language == 'ar' 
                             else f"This trend has {top_trend.get('engagement_rate', 0):.1%} engagement rate",
                'hashtags': top_trend.get('hashtags', []),
                'platforms': top_trend.get('platforms', []),
                'estimated_reach': top_trend.get('views', 0)
            })
            
            # Cross-platform trends
            cross_platform_trends = [t for t in trends if t.get('cross_platform', False)]
            if cross_platform_trends:
                trend = cross_platform_trends[0]
                recommendations.append({
                    'type': 'cross_platform',
                    'priority': 'high',
                    'title': f"انشر على منصات متعددة" if language == 'ar' else "Post across multiple platforms",
                    'description': f"ترند '{trend['topic']}' رائج على {len(trend['platforms'])} منصات" if language == 'ar'
                                 else f"'{trend['topic']}' is trending on {len(trend['platforms'])} platforms",
                    'hashtags': trend.get('hashtags', []),
                    'platforms': trend.get('platforms', [])
                })
            
            # High growth trends
            high_growth = [t for t in trends if t.get('growth_rate', 0) > 100]
            if high_growth:
                trend = high_growth[0]
                recommendations.append({
                    'type': 'growth_opportunity',
                    'priority': 'medium',
                    'title': f"فرصة نمو سريع" if language == 'ar' else "Rapid growth opportunity",
                    'description': f"ترند '{trend['topic']}' ينمو بمعدل {trend.get('growth_rate', 0):.0f}%" if language == 'ar'
                                 else f"'{trend['topic']}' is growing at {trend.get('growth_rate', 0):.0f}%",
                    'hashtags': trend.get('hashtags', []),
                    'timing': 'urgent'
                })
            
            # Category-based recommendations
            category_counts = Counter(trend['category'] for trend in trends)
            top_category = category_counts.most_common(1)[0][0]
            
            recommendations.append({
                'type': 'content_strategy',
                'priority': 'medium',
                'title': f"ركز على محتوى {top_category}" if language == 'ar' else f"Focus on {top_category} content",
                'description': f"فئة {top_category} تهيمن على التريندات حالياً" if language == 'ar'
                             else f"{top_category} category is dominating current trends",
                'category': top_category,
                'trend_count': category_counts[top_category]
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def get_trending_sounds(self, platform: str = 'tiktok', language: str = 'ar') -> Dict:
        """Get trending sounds/music for content creation"""
        try:
            # Simulate trending sounds data
            if language == 'ar':
                sounds = [
                    {
                        'name': 'موسيقى ترندية 1',
                        'artist': 'فنان عربي',
                        'usage_count': 1500000,
                        'trend_score': 95,
                        'category': 'dance',
                        'duration': 30,
                        'mood': 'energetic'
                    },
                    {
                        'name': 'أغنية شعبية',
                        'artist': 'مطرب مشهور',
                        'usage_count': 1200000,
                        'trend_score': 88,
                        'category': 'emotional',
                        'duration': 45,
                        'mood': 'nostalgic'
                    }
                ]
            else:
                sounds = [
                    {
                        'name': 'Trending Beat 1',
                        'artist': 'Popular Artist',
                        'usage_count': 2000000,
                        'trend_score': 92,
                        'category': 'dance',
                        'duration': 30,
                        'mood': 'upbeat'
                    },
                    {
                        'name': 'Viral Sound Effect',
                        'artist': 'Sound Creator',
                        'usage_count': 1800000,
                        'trend_score': 89,
                        'category': 'comedy',
                        'duration': 15,
                        'mood': 'funny'
                    }
                ]
            
            return {
                'success': True,
                'platform': platform,
                'language': language,
                'trending_sounds': sounds,
                'last_updated': datetime.utcnow().isoformat(),
                'recommendations': {
                    'best_for_viral': sounds[0]['name'],
                    'optimal_duration': '15-30 seconds',
                    'usage_tip': 'استخدم الصوت في أول 24 ساعة من انتشاره' if language == 'ar' 
                                else 'Use sound within first 24 hours of trending'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting trending sounds: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_trend_lifecycle(self, trend_topic: str, platform: str) -> Dict:
        """Analyze the lifecycle stage of a trend"""
        try:
            # Simulate trend lifecycle analysis
            lifecycle_stages = ['emerging', 'growing', 'peak', 'declining', 'dead']
            
            # Generate realistic lifecycle data
            current_stage = random.choice(lifecycle_stages[:4])  # Exclude 'dead'
            
            stage_data = {
                'emerging': {
                    'description': 'Trend is just starting to gain traction',
                    'opportunity': 'high',
                    'competition': 'low',
                    'recommended_action': 'Create content immediately'
                },
                'growing': {
                    'description': 'Trend is rapidly gaining popularity',
                    'opportunity': 'very_high',
                    'competition': 'medium',
                    'recommended_action': 'Maximize content production'
                },
                'peak': {
                    'description': 'Trend is at maximum popularity',
                    'opportunity': 'medium',
                    'competition': 'high',
                    'recommended_action': 'Focus on unique angles'
                },
                'declining': {
                    'description': 'Trend is losing momentum',
                    'opportunity': 'low',
                    'competition': 'very_high',
                    'recommended_action': 'Move to new trends'
                }
            }
            
            current_data = stage_data[current_stage]
            
            # Estimate remaining time
            remaining_days = {
                'emerging': random.randint(3, 7),
                'growing': random.randint(2, 5),
                'peak': random.randint(1, 3),
                'declining': random.randint(0, 2)
            }
            
            return {
                'success': True,
                'trend_topic': trend_topic,
                'platform': platform,
                'current_stage': current_stage,
                'stage_description': current_data['description'],
                'opportunity_level': current_data['opportunity'],
                'competition_level': current_data['competition'],
                'recommended_action': current_data['recommended_action'],
                'estimated_remaining_days': remaining_days[current_stage],
                'confidence': random.uniform(0.7, 0.95),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend lifecycle: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global trend discovery instance
trend_discovery = TrendDiscovery()

