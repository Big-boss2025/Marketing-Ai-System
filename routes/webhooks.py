from flask import Blueprint, request, jsonify
import logging
from src.services.paypal_webhook import paypal_webhook_handler
from src.services.odoo_complete_integration import odoo_integration
from src.services.social_media_webhooks import social_media_webhooks
from src.services.subscription_checker import subscription_checker

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')

@webhooks_bp.route('/paypal', methods=['POST'])
def handle_paypal_webhook():
    """Handle PayPal webhook notifications"""
    try:
        headers = dict(request.headers)
        body = request.get_data(as_text=True)
        
        result = paypal_webhook_handler.process_webhook_event(headers, body)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling PayPal webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'processing_error'
        }), 500

@webhooks_bp.route('/odoo', methods=['POST'])
def handle_odoo_webhook():
    """Handle Odoo webhook notifications"""
    try:
        headers = dict(request.headers)
        body = request.get_data(as_text=True)
        
        result = odoo_integration.process_odoo_webhook(headers, body)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling Odoo webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'processing_error'
        }), 500

@webhooks_bp.route('/facebook', methods=['GET', 'POST'])
def handle_facebook_webhook():
    """Handle Facebook webhook notifications"""
    try:
        if request.method == 'GET':
            # Webhook verification
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            if mode == 'subscribe' and token == 'YOUR_VERIFY_TOKEN':
                return challenge, 200
            else:
                return 'Forbidden', 403
        
        elif request.method == 'POST':
            headers = dict(request.headers)
            body = request.get_data(as_text=True)
            
            result = social_media_webhooks.process_facebook_webhook(headers, body)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
    except Exception as e:
        logger.error(f"Error handling Facebook webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'processing_error'
        }), 500

@webhooks_bp.route('/tiktok', methods=['POST'])
def handle_tiktok_webhook():
    """Handle TikTok webhook notifications"""
    try:
        headers = dict(request.headers)
        body = request.get_data(as_text=True)
        
        result = social_media_webhooks.process_tiktok_webhook(headers, body)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error handling TikTok webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'processing_error'
        }), 500

@webhooks_bp.route('/subscription/check/<int:user_id>', methods=['GET'])
def check_subscription_status(user_id):
    """Check user subscription status"""
    try:
        result = subscription_checker.check_user_subscription_status(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error checking subscription status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/subscription/can-perform', methods=['POST'])
def check_can_perform_action():
    """Check if user can perform specific action"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        action_type = data.get('action_type')
        cost = data.get('cost')
        
        if not user_id or not action_type:
            return jsonify({
                'success': False,
                'error': 'user_id and action_type are required'
            }), 400
        
        result = subscription_checker.can_perform_action(user_id, action_type, cost)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error checking action permission: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/subscription/upgrade-options/<int:user_id>', methods=['GET'])
def get_upgrade_options(user_id):
    """Get available upgrade options for user"""
    try:
        result = subscription_checker.get_upgrade_options(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting upgrade options: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/analytics/collect/<int:user_id>', methods=['POST'])
def collect_user_analytics(user_id):
    """Collect analytics for all user's content"""
    try:
        result = social_media_webhooks.collect_all_user_analytics(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error collecting user analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/credits/add-monthly/<int:user_id>', methods=['POST'])
def add_monthly_credits(user_id):
    """Add monthly credits if due"""
    try:
        result = subscription_checker.add_monthly_credits_if_due(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error adding monthly credits: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/paypal/create-payment', methods=['POST'])
def create_paypal_payment():
    """Create PayPal payment link"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        description = data.get('description', 'Credits Purchase')
        
        if not user_id or not amount:
            return jsonify({
                'success': False,
                'error': 'user_id and amount are required'
            }), 400
        
        result = paypal_webhook_handler.create_payment_link(user_id, amount, description)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error creating PayPal payment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/odoo/sync-user/<int:odoo_partner_id>', methods=['POST'])
def sync_user_from_odoo(odoo_partner_id):
    """Sync user data from Odoo"""
    try:
        result = odoo_integration.sync_user_from_odoo(odoo_partner_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error syncing user from Odoo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/odoo/sync-subscription/<int:odoo_subscription_id>', methods=['POST'])
def sync_subscription_from_odoo(odoo_subscription_id):
    """Sync subscription data from Odoo"""
    try:
        result = odoo_integration.sync_subscription_from_odoo(odoo_subscription_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error syncing subscription from Odoo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/odoo/create-lead', methods=['POST'])
def create_odoo_lead():
    """Create lead in Odoo CRM"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'name and email are required'
            }), 400
        
        result = odoo_integration.create_odoo_lead(data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error creating Odoo lead: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/health', methods=['GET'])
def webhook_health_check():
    """Health check endpoint for webhooks"""
    return jsonify({
        'success': True,
        'message': 'Webhooks service is healthy',
        'timestamp': str(datetime.utcnow()),
        'services': {
            'paypal': 'active',
            'odoo': 'active',
            'social_media': 'active',
            'subscription_checker': 'active'
        }
    }), 200

