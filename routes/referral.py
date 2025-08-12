from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from src.services.referral_manager import referral_manager
from src.models.user import User
from src.models.referral import ReferralCode, Referral, ReferralTier, ReferralCampaign

logger = logging.getLogger(__name__)

referral_bp = Blueprint('referral', __name__, url_prefix='/api/referral')

@referral_bp.route('/code/create/<int:user_id>', methods=['POST'])
def create_referral_code(user_id):
    """Create a referral code for a user"""
    try:
        data = request.get_json() or {}
        
        reward_type = data.get('reward_type', 'credits')
        reward_value = data.get('reward_value', 10.0)
        max_usage = data.get('max_usage', 100)
        
        result = referral_manager.create_referral_code(
            user_id, reward_type, reward_value, max_usage
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating referral code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/code/use', methods=['POST'])
def use_referral_code():
    """Use a referral code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data or 'referred_user_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Code and referred_user_id are required'
            }), 400
        
        code = data['code']
        referred_user_id = data['referred_user_id']
        ip_address = data.get('ip_address', request.remote_addr)
        user_agent = data.get('user_agent', request.headers.get('User-Agent'))
        
        result = referral_manager.use_referral_code(
            code, referred_user_id, ip_address, user_agent
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error using referral code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/stats/<int:user_id>', methods=['GET'])
def get_user_referral_stats(user_id):
    """Get referral statistics for a user"""
    try:
        result = referral_manager.get_user_referral_stats(user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting referral stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/tier/<int:user_id>', methods=['GET'])
def get_user_tier(user_id):
    """Get user's current referral tier"""
    try:
        tier = referral_manager.get_user_tier(user_id)
        
        if 'error' not in tier:
            return jsonify({
                'success': True,
                'tier': tier
            })
        else:
            return jsonify({
                'success': False,
                'error': tier['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting user tier: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/tiers', methods=['GET'])
def get_all_tiers():
    """Get all referral tiers"""
    try:
        tiers = ReferralTier.query.order_by(ReferralTier.min_referrals).all()
        
        return jsonify({
            'success': True,
            'tiers': [tier.to_dict() for tier in tiers]
        })
        
    except Exception as e:
        logger.error(f"Error getting tiers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/content/generate/<int:user_id>', methods=['GET'])
def generate_referral_content(user_id):
    """Generate AI-powered referral content"""
    try:
        language = request.args.get('language', 'ar')
        
        result = referral_manager.generate_referral_content(user_id, language)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error generating referral content: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get referral leaderboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        period = request.args.get('period', 'all_time')
        
        if period not in ['all_time', 'this_month', 'this_week', 'today']:
            return jsonify({
                'success': False,
                'error': 'Invalid period. Must be: all_time, this_month, this_week, or today'
            }), 400
        
        result = referral_manager.get_leaderboard(limit, period)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/analytics', methods=['GET'])
def get_referral_analytics():
    """Get referral system analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days must be between 1 and 365'
            }), 400
        
        result = referral_manager.get_referral_analytics(days)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting referral analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/campaign/create', methods=['POST'])
def create_referral_campaign():
    """Create a new referral campaign"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Campaign data is required'
            }), 400
        
        required_fields = ['name', 'name_ar', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Field {field} is required'
                }), 400
        
        result = referral_manager.create_referral_campaign(data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating referral campaign: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/campaign/active', methods=['GET'])
def get_active_campaign():
    """Get currently active referral campaign"""
    try:
        campaign = referral_manager.get_active_campaign()
        
        return jsonify({
            'success': True,
            'campaign': campaign
        })
        
    except Exception as e:
        logger.error(f"Error getting active campaign: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/campaign/list', methods=['GET'])
def list_campaigns():
    """List all referral campaigns"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')  # active, inactive, all
        
        query = ReferralCampaign.query
        
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)
        
        campaigns = query.order_by(ReferralCampaign.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'campaigns': [campaign.to_dict() for campaign in campaigns.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': campaigns.total,
                'pages': campaigns.pages,
                'has_next': campaigns.has_next,
                'has_prev': campaigns.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/validate/<code>', methods=['GET'])
def validate_referral_code(code):
    """Validate a referral code"""
    try:
        referral_code = ReferralCode.query.filter_by(code=code.upper()).first()
        
        if not referral_code:
            return jsonify({
                'success': False,
                'valid': False,
                'error': 'Referral code not found'
            }), 404
        
        is_valid = referral_code.is_valid()
        
        response_data = {
            'success': True,
            'valid': is_valid,
            'code': referral_code.code,
            'reward_value': referral_code.reward_value,
            'reward_type': referral_code.reward_type,
            'usage_count': referral_code.usage_count,
            'max_usage': referral_code.max_usage
        }
        
        if not is_valid:
            if referral_code.usage_count >= referral_code.max_usage:
                response_data['error'] = 'Referral code has reached maximum usage'
            elif referral_code.expires_at and datetime.utcnow() > referral_code.expires_at:
                response_data['error'] = 'Referral code has expired'
            elif not referral_code.is_active:
                response_data['error'] = 'Referral code is inactive'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error validating referral code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/code/<int:user_id>', methods=['GET'])
def get_user_referral_code(user_id):
    """Get user's referral code"""
    try:
        referral_code = ReferralCode.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()
        
        if not referral_code:
            return jsonify({
                'success': False,
                'error': 'No active referral code found for user'
            }), 404
        
        return jsonify({
            'success': True,
            'referral_code': referral_code.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting user referral code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/referrals/<int:user_id>', methods=['GET'])
def get_user_referrals(user_id):
    """Get user's referrals"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')  # pending, completed, cancelled
        
        query = Referral.query.filter_by(referrer_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        referrals = query.order_by(Referral.referred_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'referrals': [referral.to_dict() for referral in referrals.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': referrals.total,
                'pages': referrals.pages,
                'has_next': referrals.has_next,
                'has_prev': referrals.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user referrals: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@referral_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def get_referral_dashboard(user_id):
    """Get comprehensive referral dashboard for a user"""
    try:
        # Get user stats
        stats_result = referral_manager.get_user_referral_stats(user_id)
        
        if not stats_result['success']:
            return jsonify(stats_result), 404
        
        # Get active campaign
        active_campaign = referral_manager.get_active_campaign()
        
        # Get recent referrals
        recent_referrals = Referral.query.filter_by(
            referrer_id=user_id
        ).order_by(Referral.referred_at.desc()).limit(5).all()
        
        dashboard_data = {
            'success': True,
            'user_id': user_id,
            'stats': stats_result['stats'],
            'referral_code': stats_result['referral_code'],
            'current_tier': stats_result['stats']['current_tier'],
            'active_campaign': active_campaign,
            'recent_referrals': [r.to_dict() for r in recent_referrals],
            'quick_actions': [
                {
                    'action': 'share_code',
                    'title': 'شارك كود الإحالة',
                    'description': 'شارك كودك مع الأصدقاء واحصل على مكافآت'
                },
                {
                    'action': 'generate_content',
                    'title': 'إنشاء محتوى ترويجي',
                    'description': 'أنشئ محتوى جذاب لمشاركة كود الإحالة'
                },
                {
                    'action': 'view_leaderboard',
                    'title': 'لوحة المتصدرين',
                    'description': 'شاهد ترتيبك بين أفضل المُحيلين'
                }
            ]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting referral dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

