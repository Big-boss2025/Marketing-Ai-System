from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from src.services.strategy_engine import strategy_engine
from src.models.marketing_strategy import (
    MarketingStrategy, StrategyExecution, StrategyTemplate, 
    StrategyRecommendation, StrategyPerformance
)
from src.models.user import User
from src.models.base import db

logger = logging.getLogger(__name__)

marketing_strategies_bp = Blueprint('marketing_strategies', __name__, url_prefix='/marketing-strategies')

@marketing_strategies_bp.route('/initialize', methods=['POST'])
def initialize_strategies():
    """Initialize default marketing strategies"""
    try:
        result = strategy_engine.initialize_default_strategies()
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error initializing strategies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/list', methods=['GET'])
def list_strategies():
    """Get list of all marketing strategies"""
    try:
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        cost_level = request.args.get('cost_level')
        
        query = MarketingStrategy.query.filter_by(is_active=True)
        
        if category:
            query = query.filter(MarketingStrategy.category == category)
        if difficulty:
            query = query.filter(MarketingStrategy.difficulty_level == difficulty)
        if cost_level:
            query = query.filter(MarketingStrategy.cost_level == cost_level)
        
        strategies = query.order_by(MarketingStrategy.effectiveness_score.desc()).all()
        
        return jsonify({
            'success': True,
            'strategies': [strategy.to_dict() for strategy in strategies],
            'total': len(strategies),
            'filters': {
                'categories': list(strategy_engine.strategy_categories.keys()),
                'difficulty_levels': ['easy', 'medium', 'hard', 'expert'],
                'cost_levels': ['free', 'low', 'medium', 'high']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/<int:strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """Get detailed information about a specific strategy"""
    try:
        strategy = MarketingStrategy.query.get(strategy_id)
        if not strategy:
            return jsonify({
                'success': False,
                'error': 'Strategy not found'
            }), 404
        
        # Get performance data
        performance = strategy_engine.get_strategy_performance(strategy_id)
        
        return jsonify({
            'success': True,
            'strategy': strategy.to_dict(),
            'performance': performance.get('performance', {}),
            'recent_executions': performance.get('recent_executions', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting strategy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    """Get AI-powered strategy recommendations for a user"""
    try:
        # Get business context from request
        business_context = request.args.to_dict()
        
        # Generate recommendations
        recommendations = strategy_engine.recommend_strategies(user_id, business_context)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'total': len(recommendations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/recommendations/<int:recommendation_id>/feedback', methods=['POST'])
def provide_recommendation_feedback(recommendation_id):
    """Provide feedback on a strategy recommendation"""
    try:
        data = request.get_json()
        rating = data.get('rating')  # 1-5
        comment = data.get('comment')
        action = data.get('action')  # 'accept', 'dismiss', 'view'
        
        recommendation = StrategyRecommendation.query.get(recommendation_id)
        if not recommendation:
            return jsonify({
                'success': False,
                'error': 'Recommendation not found'
            }), 404
        
        # Update recommendation
        if rating:
            recommendation.feedback_rating = rating
        if comment:
            recommendation.feedback_comment = comment
        
        if action == 'accept':
            recommendation.is_accepted = True
        elif action == 'dismiss':
            recommendation.is_dismissed = True
        elif action == 'view':
            recommendation.is_viewed = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Feedback recorded successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error providing feedback: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/execute', methods=['POST'])
def execute_strategy():
    """Start executing a marketing strategy"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        strategy_id = data.get('strategy_id')
        execution_params = data.get('execution_params', {})
        
        if not user_id or not strategy_id:
            return jsonify({
                'success': False,
                'error': 'user_id and strategy_id are required'
            }), 400
        
        result = strategy_engine.execute_strategy(user_id, strategy_id, execution_params)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error executing strategy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/executions/<int:user_id>', methods=['GET'])
def get_user_executions(user_id):
    """Get strategy executions for a user"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        
        query = StrategyExecution.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter(StrategyExecution.status == status)
        
        executions = query.order_by(StrategyExecution.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'executions': [execution.to_dict() for execution in executions],
            'total': len(executions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user executions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/executions/<int:execution_id>', methods=['PUT'])
def update_execution(execution_id):
    """Update strategy execution status and metrics"""
    try:
        data = request.get_json()
        
        execution = StrategyExecution.query.get(execution_id)
        if not execution:
            return jsonify({
                'success': False,
                'error': 'Execution not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'status', 'actual_metrics', 'spent_amount', 'audience_reached',
            'engagement_rate', 'conversion_rate', 'roi', 'success_score',
            'lessons_learned', 'recommendations', 'next_steps'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(execution, field, data[field])
        
        # Update end date if status is completed
        if data.get('status') == 'completed' and not execution.end_date:
            execution.end_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Execution updated successfully',
            'execution': execution.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating execution: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/templates', methods=['GET'])
def get_strategy_templates():
    """Get strategy templates for different business types"""
    try:
        business_type = request.args.get('business_type')
        budget_range = request.args.get('budget_range')
        
        query = StrategyTemplate.query
        
        if business_type:
            query = query.filter(StrategyTemplate.business_type == business_type)
        if budget_range:
            query = query.filter(StrategyTemplate.budget_range == budget_range)
        
        templates = query.order_by(StrategyTemplate.average_success_rate.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates],
            'total': len(templates),
            'business_types': list(strategy_engine.business_types.keys())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/templates/<int:template_id>/apply', methods=['POST'])
def apply_template(template_id):
    """Apply a strategy template to a user's account"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        customizations = data.get('customizations', {})
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id is required'
            }), 400
        
        template = StrategyTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        # Create executions for each strategy in the template
        executions = []
        
        for strategy_id in template.strategies_included:
            execution_params = {
                'campaign_name': f"{template.name} - Strategy {strategy_id}",
                'budget': customizations.get('budget', 0),
                'platforms': customizations.get('platforms', []),
                'target_metrics': customizations.get('target_metrics', {})
            }
            
            result = strategy_engine.execute_strategy(user_id, strategy_id, execution_params)
            if result['success']:
                executions.append(result['execution_id'])
        
        # Update template usage count
        template.usage_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Template applied successfully. Created {len(executions)} strategy executions.',
            'execution_ids': executions,
            'timeline': template.timeline,
            'expected_results': template.expected_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error applying template: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/analytics/overview', methods=['GET'])
def get_analytics_overview():
    """Get overall analytics for marketing strategies"""
    try:
        # Get top performing strategies
        top_strategies = db.session.query(
            MarketingStrategy.id,
            MarketingStrategy.name,
            MarketingStrategy.name_ar,
            MarketingStrategy.effectiveness_score,
            db.func.count(StrategyExecution.id).label('execution_count'),
            db.func.avg(StrategyExecution.success_score).label('avg_success')
        ).join(
            StrategyExecution, MarketingStrategy.id == StrategyExecution.strategy_id
        ).group_by(
            MarketingStrategy.id
        ).order_by(
            db.func.avg(StrategyExecution.success_score).desc()
        ).limit(10).all()
        
        # Get category performance
        category_performance = db.session.query(
            MarketingStrategy.category,
            db.func.count(StrategyExecution.id).label('execution_count'),
            db.func.avg(StrategyExecution.success_score).label('avg_success'),
            db.func.avg(StrategyExecution.roi).label('avg_roi')
        ).join(
            StrategyExecution, MarketingStrategy.id == StrategyExecution.strategy_id
        ).group_by(
            MarketingStrategy.category
        ).all()
        
        # Get recent activity
        recent_executions = StrategyExecution.query.order_by(
            StrategyExecution.created_at.desc()
        ).limit(20).all()
        
        return jsonify({
            'success': True,
            'analytics': {
                'top_strategies': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'name_ar': s.name_ar,
                        'effectiveness_score': s.effectiveness_score,
                        'execution_count': s.execution_count,
                        'average_success': round(s.avg_success or 0, 2)
                    } for s in top_strategies
                ],
                'category_performance': [
                    {
                        'category': c.category,
                        'category_ar': strategy_engine.strategy_categories.get(c.category, c.category),
                        'execution_count': c.execution_count,
                        'average_success': round(c.avg_success or 0, 2),
                        'average_roi': round(c.avg_roi or 0, 2)
                    } for c in category_performance
                ],
                'recent_activity': [e.to_dict() for e in recent_executions],
                'total_strategies': MarketingStrategy.query.filter_by(is_active=True).count(),
                'total_executions': StrategyExecution.query.count(),
                'active_executions': StrategyExecution.query.filter_by(status='active').count()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/search', methods=['GET'])
def search_strategies():
    """Search strategies by keywords"""
    try:
        query_text = request.args.get('q', '')
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        
        if not query_text:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Build search query
        search_query = MarketingStrategy.query.filter_by(is_active=True)
        
        # Text search in name, description, and tags
        search_query = search_query.filter(
            db.or_(
                MarketingStrategy.name.contains(query_text),
                MarketingStrategy.name_ar.contains(query_text),
                MarketingStrategy.description.contains(query_text),
                MarketingStrategy.description_ar.contains(query_text),
                MarketingStrategy.tags.contains(query_text)
            )
        )
        
        # Apply filters
        if category:
            search_query = search_query.filter(MarketingStrategy.category == category)
        if difficulty:
            search_query = search_query.filter(MarketingStrategy.difficulty_level == difficulty)
        
        strategies = search_query.order_by(MarketingStrategy.effectiveness_score.desc()).all()
        
        return jsonify({
            'success': True,
            'strategies': [strategy.to_dict() for strategy in strategies],
            'total': len(strategies),
            'query': query_text
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching strategies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@marketing_strategies_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for marketing strategies service"""
    return jsonify({
        'success': True,
        'message': 'Marketing strategies service is healthy',
        'timestamp': str(datetime.utcnow()),
        'total_strategies': MarketingStrategy.query.filter_by(is_active=True).count(),
        'total_executions': StrategyExecution.query.count()
    }), 200

