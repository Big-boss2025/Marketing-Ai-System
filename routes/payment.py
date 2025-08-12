from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.base import db
from src.models.user import User
from src.models.subscription import UserSubscription
from src.models.credit_transaction import CreditTransaction
from src.services.odoo_integration import odoo_integration
from src.services.credit_manager import credit_manager
import logging
from datetime import datetime

payment_bp = Blueprint('payment', __name__)
logger = logging.getLogger(__name__)

@payment_bp.route('/subscription-plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    
    plans = {
        'free': {
            'name': 'مجاني',
            'name_en': 'Free',
            'price': 0,
            'credits': 100,
            'features': [
                'إنشاء 10 منشورات شهرياً',
                'منصة واحدة للنشر',
                'دعم أساسي'
            ],
            'features_en': [
                '10 posts per month',
                'Single platform publishing',
                'Basic support'
            ],
            'popular': False
        },
        'basic': {
            'name': 'أساسي',
            'name_en': 'Basic',
            'price': 29.99,
            'credits': 1000,
            'features': [
                'إنشاء 100 منشور شهرياً',
                'جميع منصات التواصل',
                'إنشاء صور بالذكاء الاصطناعي',
                'دعم عبر البريد الإلكتروني'
            ],
            'features_en': [
                '100 posts per month',
                'All social platforms',
                'AI image generation',
                'Email support'
            ],
            'popular': True
        },
        'premium': {
            'name': 'متقدم',
            'name_en': 'Premium',
            'price': 79.99,
            'credits': 5000,
            'features': [
                'منشورات غير محدودة',
                'إنشاء فيديوهات بالذكاء الاصطناعي',
                'تحليلات متقدمة',
                'نظام الإحالة',
                'دعم أولوية'
            ],
            'features_en': [
                'Unlimited posts',
                'AI video generation',
                'Advanced analytics',
                'Referral system',
                'Priority support'
            ],
            'popular': False
        },
        'enterprise': {
            'name': 'مؤسسي',
            'name_en': 'Enterprise',
            'price': 199.99,
            'credits': 20000,
            'features': [
                'جميع ميزات الباقة المتقدمة',
                'تكامل مخصص',
                'مدير حساب مخصص',
                'تدريب فريق العمل',
                'دعم 24/7'
            ],
            'features_en': [
                'All Premium features',
                'Custom integrations',
                'Dedicated account manager',
                'Team training',
                '24/7 support'
            ],
            'popular': False
        }
    }
    
    return jsonify({
        'success': True,
        'plans': plans
    })

@payment_bp.route('/credit-packages', methods=['GET'])
def get_credit_packages():
    """Get available credit packages"""
    
    packages = {
        'starter': {
            'name': 'باقة البداية',
            'name_en': 'Starter Package',
            'credits': 500,
            'price': 9.99,
            'bonus_credits': 50,
            'popular': False
        },
        'standard': {
            'name': 'باقة قياسية',
            'name_en': 'Standard Package',
            'credits': 1500,
            'price': 24.99,
            'bonus_credits': 200,
            'popular': True
        },
        'professional': {
            'name': 'باقة احترافية',
            'name_en': 'Professional Package',
            'credits': 3500,
            'price': 49.99,
            'bonus_credits': 500,
            'popular': False
        },
        'enterprise': {
            'name': 'باقة مؤسسية',
            'name_en': 'Enterprise Package',
            'credits': 10000,
            'price': 119.99,
            'bonus_credits': 1500,
            'popular': False
        }
    }
    
    return jsonify({
        'success': True,
        'packages': packages
    })

@payment_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def create_subscription():
    """Create subscription payment"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        plan = data.get('plan')
        if not plan:
            return jsonify({
                'success': False,
                'error': 'Subscription plan is required'
            }), 400
        
        # Get plan details
        plans_response = get_subscription_plans()
        plans = plans_response.json['plans']
        
        if plan not in plans:
            return jsonify({
                'success': False,
                'error': 'Invalid subscription plan'
            }), 400
        
        plan_details = plans[plan]
        amount = plan_details['price']
        
        if amount == 0:
            # Free plan - activate immediately
            user = User.get_by_id(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
            
            # Create free subscription
            subscription = UserSubscription(
                user_id=user_id,
                plan_name=plan,
                status='active',
                start_date=datetime.now(),
                amount_paid=0,
                payment_method='free'
            )
            subscription.save()
            
            # Update user
            user.subscription_status = plan
            user.save()
            
            # Add free credits
            credit_manager.add_credits(
                user_id=user_id,
                amount=plan_details['credits'],
                description=f"Free plan activation: {plan}",
                category='subscription'
            )
            
            return jsonify({
                'success': True,
                'subscription_id': subscription.id,
                'plan': plan,
                'status': 'active'
            })
        
        # Paid plan - create PayPal payment
        result = odoo_integration.process_subscription_payment(user_id, plan, amount)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@payment_bp.route('/buy-credits', methods=['POST'])
@jwt_required()
def buy_credits():
    """Buy credit package"""
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        package = data.get('package')
        if not package:
            return jsonify({
                'success': False,
                'error': 'Credit package is required'
            }), 400
        
        # Get package details
        packages_response = get_credit_packages()
        packages = packages_response.json['packages']
        
        if package not in packages:
            return jsonify({
                'success': False,
                'error': 'Invalid credit package'
            }), 400
        
        package_details = packages[package]
        amount = package_details['price']
        total_credits = package_details['credits'] + package_details['bonus_credits']
        
        # Create PayPal payment for credits
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Create payment data
        payment_data = {
            'items': [{
                'name': f'Marketing Credits - {package_details["name_en"]}',
                'sku': f'credits-{package}',
                'price': str(amount),
                'currency': 'USD',
                'quantity': 1
            }],
            'total': amount,
            'currency': 'USD',
            'description': f'Marketing Automation Credits Package - {total_credits} credits',
            'return_url': f"{request.host_url}payment/credits/success",
            'cancel_url': f"{request.host_url}payment/credits/cancel"
        }
        
        paypal_payment = odoo_integration.create_paypal_payment(payment_data)
        
        if not paypal_payment:
            return jsonify({
                'success': False,
                'error': 'Failed to create payment'
            }), 500
        
        # Get approval URL
        approval_url = None
        for link in paypal_payment.get('links', []):
            if link.get('rel') == 'approval_url':
                approval_url = link.get('href')
                break
        
        if not approval_url:
            return jsonify({
                'success': False,
                'error': 'Payment approval URL not found'
            }), 500
        
        # Store payment information
        payment_info = {
            'paypal_payment_id': paypal_payment.get('id'),
            'amount': amount,
            'currency': 'USD',
            'package': package,
            'credits': total_credits,
            'type': 'credits',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        user.set_payment_info(payment_info)
        user.save()
        
        return jsonify({
            'success': True,
            'payment_id': paypal_payment.get('id'),
            'approval_url': approval_url,
            'amount': amount,
            'credits': total_credits
        })
        
    except Exception as e:
        logger.error(f"Error buying credits: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@payment_bp.route('/success', methods=['GET'])
def payment_success():
    """Handle successful payment return from PayPal"""
    
    try:
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        if not payment_id or not payer_id:
            return jsonify({
                'success': False,
                'error': 'Missing payment parameters'
            }), 400
        
        # Complete subscription payment
        result = odoo_integration.complete_subscription_payment(payment_id, payer_id)
        
        if result['success']:
            return redirect(f"{request.host_url}dashboard?payment=success&plan={result.get('plan')}")
        else:
            return redirect(f"{request.host_url}dashboard?payment=failed&error={result.get('error')}")
        
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")
        return redirect(f"{request.host_url}dashboard?payment=error")

@payment_bp.route('/credits/success', methods=['GET'])
def credits_payment_success():
    """Handle successful credit purchase return from PayPal"""
    
    try:
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        if not payment_id or not payer_id:
            return jsonify({
                'success': False,
                'error': 'Missing payment parameters'
            }), 400
        
        # Execute PayPal payment
        payment_result = odoo_integration.execute_paypal_payment(payment_id, payer_id)
        
        if not payment_result or payment_result.get('state') != 'approved':
            return redirect(f"{request.host_url}dashboard?payment=failed")
        
        # Find user by payment ID
        users = User.query.all()
        user = None
        
        for u in users:
            payment_info = u.get_payment_info()
            if payment_info and payment_info.get('paypal_payment_id') == payment_id:
                user = u
                break
        
        if not user:
            return redirect(f"{request.host_url}dashboard?payment=failed&error=user_not_found")
        
        payment_info = user.get_payment_info()
        
        if payment_info.get('type') != 'credits':
            return redirect(f"{request.host_url}dashboard?payment=failed&error=invalid_payment_type")
        
        credits_to_add = payment_info.get('credits', 0)
        package = payment_info.get('package', '')
        
        # Add credits to user account
        credit_result = credit_manager.add_credits(
            user_id=user.id,
            amount=credits_to_add,
            description=f"Credit package purchase: {package}",
            category='purchase',
            reference_id=payment_id
        )
        
        if not credit_result['success']:
            logger.error(f"Failed to add purchased credits: {credit_result['error']}")
            return redirect(f"{request.host_url}dashboard?payment=failed&error=credit_addition_failed")
        
        # Update payment info
        payment_info['status'] = 'completed'
        payment_info['completed_at'] = datetime.now().isoformat()
        user.set_payment_info(payment_info)
        user.save()
        
        logger.info(f"Successfully processed credit purchase for user {user.id}: {credits_to_add} credits")
        
        return redirect(f"{request.host_url}dashboard?payment=success&credits={credits_to_add}")
        
    except Exception as e:
        logger.error(f"Error handling credits payment success: {str(e)}")
        return redirect(f"{request.host_url}dashboard?payment=error")

@payment_bp.route('/cancel', methods=['GET'])
def payment_cancel():
    """Handle cancelled payment"""
    return redirect(f"{request.host_url}dashboard?payment=cancelled")

@payment_bp.route('/credits/cancel', methods=['GET'])
def credits_payment_cancel():
    """Handle cancelled credit purchase"""
    return redirect(f"{request.host_url}dashboard?payment=cancelled")

@payment_bp.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook notifications"""
    
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        
        logger.info(f"Received PayPal webhook: {event_type}")
        
        if event_type == 'PAYMENT.SALE.COMPLETED':
            # Handle completed payment
            resource = data.get('resource', {})
            payment_id = resource.get('parent_payment')
            
            if payment_id:
                # Find and update payment status
                users = User.query.all()
                for user in users:
                    payment_info = user.get_payment_info()
                    if payment_info and payment_info.get('paypal_payment_id') == payment_id:
                        payment_info['webhook_received'] = True
                        payment_info['webhook_event'] = event_type
                        payment_info['webhook_timestamp'] = datetime.now().isoformat()
                        user.set_payment_info(payment_info)
                        user.save()
                        break
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling PayPal webhook: {str(e)}")
        return jsonify({'success': False}), 500

@payment_bp.route('/user/subscription', methods=['GET'])
@jwt_required()
def get_user_subscription():
    """Get current user subscription details"""
    
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get active subscription
        subscription = UserSubscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if subscription:
            subscription_data = {
                'id': subscription.id,
                'plan': subscription.plan_name,
                'status': subscription.status,
                'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                'amount_paid': subscription.amount_paid,
                'payment_method': subscription.payment_method,
                'auto_renew': subscription.auto_renew
            }
        else:
            subscription_data = None
        
        # Get credit balance
        credit_balance = credit_manager.get_user_credits(user_id)
        
        return jsonify({
            'success': True,
            'subscription': subscription_data,
            'credits_balance': credit_balance['balance'],
            'subscription_status': user.subscription_status
        })
        
    except Exception as e:
        logger.error(f"Error getting user subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@payment_bp.route('/user/invoices', methods=['GET'])
@jwt_required()
def get_user_invoices():
    """Get user invoices from Odoo"""
    
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        invoices = []
        
        if user.odoo_customer_id:
            invoices = odoo_integration.get_odoo_invoices(user.odoo_customer_id)
        
        return jsonify({
            'success': True,
            'invoices': invoices
        })
        
    except Exception as e:
        logger.error(f"Error getting user invoices: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@payment_bp.route('/sync-odoo', methods=['POST'])
@jwt_required()
def sync_with_odoo():
    """Sync user data with Odoo"""
    
    try:
        user_id = get_jwt_identity()
        result = odoo_integration.sync_user_with_odoo(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error syncing with Odoo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@payment_bp.route('/admin/odoo/validate', methods=['GET'])
@jwt_required()
def validate_odoo_connection():
    """Validate Odoo connection (Admin only)"""
    
    try:
        # In a real implementation, you would check if user is admin
        result = odoo_integration.validate_odoo_connection()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating Odoo connection: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

