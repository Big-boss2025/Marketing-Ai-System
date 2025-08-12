from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from src.services.performance_monitor import performance_monitor
from src.models.user import User
from src.models.task import Task

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

@performance_bp.route('/analyze/<int:user_id>', methods=['GET'])
def analyze_performance(user_id):
    """Analyze content performance for a user"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Analyze performance
        analysis_result = performance_monitor.analyze_content_performance(user_id, days)
        
        if analysis_result['success']:
            # Create task record
            task = Task(
                user_id=user_id,
                task_type='performance_analysis',
                status='completed',
                input_data={'analysis_days': days},
                output_data=analysis_result,
                credits_used=0  # Free analysis
            )
            task.save()
            
            analysis_result['task_id'] = task.id
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error analyzing performance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/optimize/<int:user_id>', methods=['POST'])
def optimize_strategy(user_id):
    """Optimize content strategy based on performance analysis"""
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Optimize strategy
        optimization_result = performance_monitor.optimize_content_strategy(user_id)
        
        if optimization_result['success']:
            # Create task record
            task = Task(
                user_id=user_id,
                task_type='strategy_optimization',
                status='completed',
                input_data={'optimization_type': 'content_strategy'},
                output_data=optimization_result,
                credits_used=0  # Free optimization
            )
            task.save()
            
            optimization_result['task_id'] = task.id
        
        return jsonify(optimization_result)
        
    except Exception as e:
        logger.error(f"Error optimizing strategy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/trends/<int:user_id>', methods=['GET'])
def get_performance_trends(user_id):
    """Get performance trends over time"""
    try:
        # Get query parameters
        days = request.args.get('days', 90, type=int)
        
        # Validate days parameter
        if days < 7 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 7 and 365'
            }), 400
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get trends
        trends_result = performance_monitor.track_performance_trends(user_id, days)
        
        return jsonify(trends_result)
        
    except Exception as e:
        logger.error(f"Error getting performance trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/report/<int:user_id>', methods=['GET'])
def generate_performance_report(user_id):
    """Generate comprehensive performance report"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        format_type = request.args.get('format', 'json')  # json, pdf, html
        
        # Validate parameters
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        if format_type not in ['json', 'pdf', 'html']:
            return jsonify({
                'success': False,
                'error': 'Format must be json, pdf, or html'
            }), 400
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Generate report
        report_result = performance_monitor.generate_performance_report(user_id, days)
        
        if report_result['success']:
            # Create task record
            task = Task(
                user_id=user_id,
                task_type='performance_report_generation',
                status='completed',
                input_data={
                    'report_days': days,
                    'format': format_type
                },
                output_data={'report_id': report_result.get('report_id')},
                credits_used=0  # Free report
            )
            task.save()
            
            report_result['task_id'] = task.id
            
            # Handle different format types
            if format_type == 'json':
                return jsonify(report_result)
            elif format_type == 'pdf':
                # In a real implementation, generate PDF
                return jsonify({
                    'success': True,
                    'message': 'PDF report generation not implemented yet',
                    'report_data': report_result
                })
            elif format_type == 'html':
                # In a real implementation, generate HTML
                return jsonify({
                    'success': True,
                    'message': 'HTML report generation not implemented yet',
                    'report_data': report_result
                })
        
        return jsonify(report_result)
        
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/benchmarks', methods=['GET'])
def get_platform_benchmarks():
    """Get industry benchmarks for all platforms"""
    try:
        benchmarks = performance_monitor.platform_benchmarks
        
        return jsonify({
            'success': True,
            'benchmarks': benchmarks,
            'description': 'Industry average benchmarks for social media platforms',
            'last_updated': '2024-01-01',
            'source': 'Industry reports and analytics platforms'
        })
        
    except Exception as e:
        logger.error(f"Error getting benchmarks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/insights/<int:user_id>', methods=['GET'])
def get_performance_insights(user_id):
    """Get AI-powered performance insights"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        platform = request.args.get('platform')  # Optional platform filter
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get performance analysis
        analysis_result = performance_monitor.analyze_content_performance(user_id, days)
        
        if not analysis_result['success']:
            return jsonify(analysis_result)
        
        # Filter by platform if specified
        insights = analysis_result['insights']
        recommendations = analysis_result['recommendations']
        
        if platform:
            platform_recommendations = recommendations.get(platform, [])
            filtered_insights = [
                insight for insight in insights 
                if platform.lower() in insight.lower()
            ]
            
            return jsonify({
                'success': True,
                'platform': platform,
                'insights': filtered_insights,
                'recommendations': platform_recommendations,
                'analysis_period': f'{days} days'
            })
        
        return jsonify({
            'success': True,
            'insights': insights,
            'recommendations': recommendations,
            'analysis_period': f'{days} days',
            'platforms_analyzed': list(analysis_result['platform_performance'].keys())
        })
        
    except Exception as e:
        logger.error(f"Error getting performance insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/compare/<int:user_id>', methods=['GET'])
def compare_performance(user_id):
    """Compare performance across different time periods"""
    try:
        # Get query parameters
        period1 = request.args.get('period1', 30, type=int)  # Current period
        period2 = request.args.get('period2', 60, type=int)  # Comparison period
        
        # Validate parameters
        if period1 < 1 or period1 > 365 or period2 < 1 or period2 > 365:
            return jsonify({
                'success': False,
                'error': 'Period parameters must be between 1 and 365'
            }), 400
        
        if period1 >= period2:
            return jsonify({
                'success': False,
                'error': 'Period1 must be less than period2'
            }), 400
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get performance for both periods
        current_analysis = performance_monitor.analyze_content_performance(user_id, period1)
        previous_analysis = performance_monitor.analyze_content_performance(user_id, period2)
        
        if not current_analysis['success'] or not previous_analysis['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to analyze one or both periods'
            })
        
        # Calculate comparisons
        comparison_result = {
            'success': True,
            'user_id': user_id,
            'comparison_periods': {
                'current': f'{period1} days',
                'previous': f'{period2} days'
            },
            'current_performance': current_analysis,
            'previous_performance': previous_analysis,
            'improvements': {},
            'declines': {},
            'summary': {}
        }
        
        # Compare platform performance
        current_platforms = current_analysis['platform_performance']
        previous_platforms = previous_analysis['platform_performance']
        
        for platform in current_platforms:
            if platform in previous_platforms:
                current_score = current_platforms[platform]['performance_score']
                previous_score = previous_platforms[platform]['performance_score']
                
                change = current_score - previous_score
                change_percentage = (change / previous_score) * 100 if previous_score > 0 else 0
                
                comparison_data = {
                    'current_score': current_score,
                    'previous_score': previous_score,
                    'change': change,
                    'change_percentage': change_percentage
                }
                
                if change > 5:
                    comparison_result['improvements'][platform] = comparison_data
                elif change < -5:
                    comparison_result['declines'][platform] = comparison_data
        
        # Generate summary
        total_improvements = len(comparison_result['improvements'])
        total_declines = len(comparison_result['declines'])
        
        if total_improvements > total_declines:
            comparison_result['summary']['overall_trend'] = 'improving'
        elif total_declines > total_improvements:
            comparison_result['summary']['overall_trend'] = 'declining'
        else:
            comparison_result['summary']['overall_trend'] = 'stable'
        
        comparison_result['summary']['platforms_improved'] = total_improvements
        comparison_result['summary']['platforms_declined'] = total_declines
        
        return jsonify(comparison_result)
        
    except Exception as e:
        logger.error(f"Error comparing performance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/alerts/<int:user_id>', methods=['GET'])
def get_performance_alerts(user_id):
    """Get performance alerts and warnings"""
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get recent performance
        analysis_result = performance_monitor.analyze_content_performance(user_id, 7)
        
        if not analysis_result['success']:
            return jsonify({
                'success': True,
                'alerts': [],
                'message': 'No recent content to analyze'
            })
        
        alerts = []
        platform_performance = analysis_result['platform_performance']
        
        # Check for performance issues
        for platform, data in platform_performance.items():
            # Low performance alert
            if data['performance_score'] < 30:
                alerts.append({
                    'type': 'critical',
                    'platform': platform,
                    'message': f'أداء ضعيف جداً على {platform} ({data["performance_score"]:.1f}/100)',
                    'action': 'يتطلب تدخل فوري لتحسين الاستراتيجية',
                    'priority': 'high'
                })
            
            # Low engagement alert
            if data.get('engagement_rate', 0) < 1.0:
                alerts.append({
                    'type': 'warning',
                    'platform': platform,
                    'message': f'معدل تفاعل منخفض على {platform} ({data.get("engagement_rate", 0):.2f}%)',
                    'action': 'استخدم محتوى تفاعلي أكثر',
                    'priority': 'medium'
                })
            
            # Low posting frequency alert
            if data['posts'] < 3:
                alerts.append({
                    'type': 'info',
                    'platform': platform,
                    'message': f'معدل نشر منخفض على {platform} ({data["posts"]} منشورات في 7 أيام)',
                    'action': 'زيد معدل النشر لتحسين الوصول',
                    'priority': 'low'
                })
        
        # Sort alerts by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['type'] == 'critical']),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting performance alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def get_performance_dashboard(user_id):
    """Get comprehensive performance dashboard data"""
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get various performance data
        current_performance = performance_monitor.analyze_content_performance(user_id, 7)
        monthly_performance = performance_monitor.analyze_content_performance(user_id, 30)
        trends = performance_monitor.track_performance_trends(user_id, 90)
        
        # Get alerts
        alerts_response = get_performance_alerts(user_id)
        alerts_data = alerts_response.get_json() if hasattr(alerts_response, 'get_json') else {}
        
        dashboard_data = {
            'success': True,
            'user_id': user_id,
            'dashboard_generated_at': datetime.now().isoformat(),
            'quick_stats': {
                'weekly_posts': 0,
                'weekly_engagement': 0,
                'weekly_reach': 0,
                'active_platforms': 0
            },
            'monthly_overview': {},
            'trends': trends if trends['success'] else {},
            'alerts': alerts_data.get('alerts', []),
            'top_performing_platform': None,
            'recommendations': []
        }
        
        # Fill quick stats
        if current_performance['success']:
            dashboard_data['quick_stats'] = {
                'weekly_posts': current_performance['overall_metrics']['total_posts'],
                'weekly_engagement': current_performance['overall_metrics']['total_engagement'],
                'weekly_reach': current_performance['overall_metrics']['total_reach'],
                'active_platforms': len(current_performance['platform_performance'])
            }
            
            # Find top performing platform
            best_platform = None
            best_score = 0
            
            for platform, data in current_performance['platform_performance'].items():
                if data['performance_score'] > best_score:
                    best_score = data['performance_score']
                    best_platform = platform
            
            dashboard_data['top_performing_platform'] = {
                'platform': best_platform,
                'score': best_score
            } if best_platform else None
        
        # Fill monthly overview
        if monthly_performance['success']:
            dashboard_data['monthly_overview'] = monthly_performance['platform_performance']
            dashboard_data['recommendations'] = monthly_performance['recommendations']
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

