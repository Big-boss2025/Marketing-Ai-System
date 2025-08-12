from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import logging
from src.services.analytics_engine import analytics_engine
from src.models.user import User
from src.services.api_manager import api_manager

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/dashboard')
def reports_dashboard():
    """Serve the reports dashboard HTML page"""
    try:
        return render_template('reports-dashboard.html')
    except Exception as e:
        logger.error(f"Error serving reports dashboard: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard'}), 500

@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate comprehensive analytics report"""
    try:
        data = request.get_json()
        
        # Validate required fields
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Get report parameters
        report_type = data.get('report_type', 'weekly')
        date_range = data.get('date_range')
        platform_filter = data.get('platform_filter', 'all')
        
        # Validate report type
        valid_types = ['weekly', 'monthly', 'campaign', 'custom']
        if report_type not in valid_types:
            return jsonify({'error': f'Invalid report type. Must be one of: {valid_types}'}), 400
        
        # Generate date range if not provided
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
        
        # Generate report
        report = analytics_engine.generate_comprehensive_report(
            user_id=user_id,
            report_type=report_type,
            date_range=date_range
        )
        
        if not report.get('success'):
            return jsonify({'error': report.get('error', 'Failed to generate report')}), 500
        
        # Apply platform filter if specified
        if platform_filter != 'all':
            report = apply_platform_filter(report, platform_filter)
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/overview/<int:user_id>')
def get_overview_metrics(user_id):
    """Get overview metrics for a user"""
    try:
        # Get date range from query parameters
        days = request.args.get('days', 7, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Generate overview metrics
        overview = analytics_engine.generate_overview_metrics(user_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'date_range': date_range,
            'overview': overview
        })
        
    except Exception as e:
        logger.error(f"Error getting overview metrics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/content-performance/<int:user_id>')
def get_content_performance(user_id):
    """Get content performance analysis"""
    try:
        # Get parameters
        days = request.args.get('days', 7, type=int)
        platform = request.args.get('platform', 'all')
        content_type = request.args.get('content_type', 'all')
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Apply filters
        if platform != 'all':
            user_data['content_data'] = [
                item for item in user_data['content_data'] 
                if item['platform'] == platform
            ]
        
        if content_type != 'all':
            user_data['content_data'] = [
                item for item in user_data['content_data'] 
                if item['content_type'] == content_type
            ]
        
        # Analyze content performance
        performance_analysis = analytics_engine.analyze_content_performance(user_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'filters': {
                'platform': platform,
                'content_type': content_type,
                'days': days
            },
            'performance_analysis': performance_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting content performance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/audience-insights/<int:user_id>')
def get_audience_insights(user_id):
    """Get audience insights and demographics"""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Analyze audience insights
        audience_insights = analytics_engine.analyze_audience_insights(user_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'date_range': date_range,
            'audience_insights': audience_insights
        })
        
    except Exception as e:
        logger.error(f"Error getting audience insights: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/platform-analysis/<int:user_id>')
def get_platform_analysis(user_id):
    """Get platform performance analysis"""
    try:
        days = request.args.get('days', 7, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Analyze platform performance
        platform_analysis = analytics_engine.analyze_platform_performance(user_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'date_range': date_range,
            'platform_analysis': platform_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting platform analysis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/growth-trends/<int:user_id>')
def get_growth_trends(user_id):
    """Get growth trends analysis"""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Analyze growth trends
        growth_analysis = analytics_engine.analyze_growth_trends(user_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'date_range': date_range,
            'growth_analysis': growth_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting growth trends: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/recommendations/<int:user_id>')
def get_recommendations(user_id):
    """Get personalized recommendations"""
    try:
        days = request.args.get('days', 7, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Generate recommendations
        recommendations = analytics_engine.generate_recommendations(user_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'date_range': date_range,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/charts-data/<int:user_id>')
def get_charts_data(user_id):
    """Get data for charts and visualizations"""
    try:
        report_type = request.args.get('report_type', 'weekly')
        days = request.args.get('days', 7, type=int)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_range = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        # Get user analytics data
        user_data = analytics_engine.get_user_analytics_data(user_id, date_range)
        
        if not user_data:
            return jsonify({'error': 'No data found for user'}), 404
        
        # Generate charts data
        charts_data = analytics_engine.generate_charts_data(user_data, report_type)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'report_type': report_type,
            'date_range': date_range,
            'charts_data': charts_data
        })
        
    except Exception as e:
        logger.error(f"Error getting charts data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/export', methods=['POST'])
def export_report():
    """Export report in various formats"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        report_id = data.get('report_id')
        export_format = data.get('format', 'pdf')  # pdf, excel, image
        
        if not user_id or not report_id:
            return jsonify({'error': 'User ID and Report ID are required'}), 400
        
        # Validate export format
        valid_formats = ['pdf', 'excel', 'image', 'json']
        if export_format not in valid_formats:
            return jsonify({'error': f'Invalid format. Must be one of: {valid_formats}'}), 400
        
        # For now, return a mock response
        # In a real implementation, this would generate the actual file
        export_result = {
            'success': True,
            'export_id': f"export_{user_id}_{report_id}_{int(datetime.utcnow().timestamp())}",
            'format': export_format,
            'download_url': f"/api/reports/download/{user_id}/{report_id}.{export_format}",
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            'file_size': '2.5 MB',
            'status': 'ready'
        }
        
        return jsonify(export_result)
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/download/<int:user_id>/<filename>')
def download_report(user_id, filename):
    """Download exported report file"""
    try:
        # In a real implementation, this would serve the actual file
        return jsonify({
            'message': 'File download would start here',
            'user_id': user_id,
            'filename': filename,
            'note': 'This is a mock response. In production, this would serve the actual file.'
        })
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reports_bp.route('/scheduled', methods=['GET', 'POST'])
def manage_scheduled_reports():
    """Manage scheduled reports"""
    try:
        if request.method == 'GET':
            # Get scheduled reports for user
            user_id = request.args.get('user_id', type=int)
            if not user_id:
                return jsonify({'error': 'User ID is required'}), 400
            
            # Mock scheduled reports data
            scheduled_reports = [
                {
                    'id': 1,
                    'name': 'تقرير أسبوعي',
                    'type': 'weekly',
                    'schedule': 'كل يوم أحد 9:00 ص',
                    'recipients': ['user@example.com'],
                    'last_sent': '2024-01-15T09:00:00Z',
                    'next_send': '2024-01-22T09:00:00Z',
                    'status': 'active'
                },
                {
                    'id': 2,
                    'name': 'تقرير شهري',
                    'type': 'monthly',
                    'schedule': 'أول كل شهر 10:00 ص',
                    'recipients': ['manager@example.com'],
                    'last_sent': '2024-01-01T10:00:00Z',
                    'next_send': '2024-02-01T10:00:00Z',
                    'status': 'active'
                }
            ]
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'scheduled_reports': scheduled_reports
            })
        
        elif request.method == 'POST':
            # Create new scheduled report
            data = request.get_json()
            
            user_id = data.get('user_id')
            name = data.get('name')
            report_type = data.get('report_type')
            schedule = data.get('schedule')
            recipients = data.get('recipients', [])
            
            if not all([user_id, name, report_type, schedule]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Mock creation response
            new_report = {
                'id': 3,
                'name': name,
                'type': report_type,
                'schedule': schedule,
                'recipients': recipients,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            return jsonify({
                'success': True,
                'message': 'Scheduled report created successfully',
                'scheduled_report': new_report
            })
        
    except Exception as e:
        logger.error(f"Error managing scheduled reports: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def apply_platform_filter(report, platform_filter):
    """Apply platform filter to report data"""
    try:
        if platform_filter == 'all':
            return report
        
        # Filter content data
        if 'content_performance' in report and 'content_data' in report:
            filtered_content = [
                item for item in report.get('content_data', [])
                if item.get('platform') == platform_filter
            ]
            
            # Recalculate metrics for filtered data
            if filtered_content:
                # Update overview metrics
                total_views = sum(item['metrics']['views'] for item in filtered_content)
                total_likes = sum(item['metrics']['likes'] for item in filtered_content)
                total_comments = sum(item['metrics']['comments'] for item in filtered_content)
                total_shares = sum(item['metrics']['shares'] for item in filtered_content)
                
                report['overview'].update({
                    'total_content': len(filtered_content),
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'filtered_by': platform_filter
                })
        
        return report
        
    except Exception as e:
        logger.error(f"Error applying platform filter: {str(e)}")
        return report

