import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hmac
import hashlib
from src.models.user import User
from src.models.subscription import SubscriptionPlan
from src.services.credit_manager import credit_manager

logger = logging.getLogger(__name__)

class OdooCompleteIntegration:
    """Complete Odoo Integration with APIs and Webhooks"""
    
    def __init__(self):
        # Odoo configuration
        self.odoo_url = "https://your-odoo-instance.com"
        self.odoo_db = "your_database"
        self.odoo_username = "your_username"
        self.odoo_password = "your_password"
        self.webhook_secret = "your_webhook_secret"
        
        # API endpoints
        self.api_endpoints = {
            'auth': '/web/session/authenticate',
            'partners': '/web/dataset/call_kw/res.partner',
            'subscriptions': '/web/dataset/call_kw/sale.subscription',
            'invoices': '/web/dataset/call_kw/account.move',
            'products': '/web/dataset/call_kw/product.product',
            'users': '/web/dataset/call_kw/res.users'
        }
        
        # Session management
        self.session = requests.Session()
        self.session_id = None
        self.last_auth = None
        
        # Subscription plans mapping
        self.subscription_plans = {
            'basic': {
                'credits_per_month': 500,
                'price': 29.99,
                'features': ['basic_ai', 'social_posting', 'basic_analytics']
            },
            'pro': {
                'credits_per_month': 1500,
                'price': 79.99,
                'features': ['advanced_ai', 'all_platforms', 'advanced_analytics', 'priority_support']
            },
            'enterprise': {
                'credits_per_month': 5000,
                'price': 199.99,
                'features': ['unlimited_ai', 'white_label', 'custom_integrations', 'dedicated_support']
            }
        }
    
    def authenticate(self) -> bool:
        """Authenticate with Odoo"""
        try:
            # Check if we have a valid session
            if self.session_id and self.last_auth:
                if datetime.utcnow() - self.last_auth < timedelta(hours=8):
                    return True
            
            auth_data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'db': self.odoo_db,
                    'login': self.odoo_username,
                    'password': self.odoo_password
                },
                'id': 1
            }
            
            response = self.session.post(
                f"{self.odoo_url}{self.api_endpoints['auth']}",
                json=auth_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') and not result.get('error'):
                    self.session_id = result['result'].get('session_id')
                    self.last_auth = datetime.utcnow()
                    logger.info("Successfully authenticated with Odoo")
                    return True
            
            logger.error(f"Odoo authentication failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error authenticating with Odoo: {str(e)}")
            return False
    
    def make_odoo_request(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Dict:
        """Make authenticated request to Odoo"""
        try:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
            
            request_data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'model': model,
                    'method': method,
                    'args': args or [],
                    'kwargs': kwargs or {}
                },
                'id': 1
            }
            
            response = self.session.post(
                f"{self.odoo_url}/web/dataset/call_kw/{model}/{method}",
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('error'):
                    return {'success': False, 'error': result['error']}
                return {'success': True, 'data': result.get('result')}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error making Odoo request: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_user_from_odoo(self, odoo_partner_id: int) -> Dict:
        """Sync user data from Odoo partner"""
        try:
            # Get partner data from Odoo
            result = self.make_odoo_request(
                'res.partner',
                'read',
                args=[[odoo_partner_id]],
                kwargs={'fields': ['name', 'email', 'phone', 'country_id', 'lang', 'is_company', 'parent_id']}
            )
            
            if not result['success']:
                return result
            
            partner_data = result['data'][0] if result['data'] else None
            if not partner_data:
                return {'success': False, 'error': 'Partner not found'}
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=partner_data['email']).first()
            
            if existing_user:
                # Update existing user
                existing_user.name = partner_data['name']
                existing_user.phone = partner_data.get('phone')
                existing_user.country = partner_data.get('country_id', [None, None])[1] if partner_data.get('country_id') else None
                existing_user.language = partner_data.get('lang', 'en_US')
                existing_user.odoo_partner_id = odoo_partner_id
                existing_user.updated_at = datetime.utcnow()
                
                # Commit changes
                from src.models.base import db
                db.session.commit()
                
                return {
                    'success': True,
                    'user_id': existing_user.id,
                    'action': 'updated',
                    'message': 'User updated successfully'
                }
            else:
                # Create new user
                new_user = User(
                    name=partner_data['name'],
                    email=partner_data['email'],
                    phone=partner_data.get('phone'),
                    country=partner_data.get('country_id', [None, None])[1] if partner_data.get('country_id') else None,
                    language=partner_data.get('lang', 'en_US'),
                    odoo_partner_id=odoo_partner_id,
                    credits_balance=100,  # Welcome credits
                    created_at=datetime.utcnow()
                )
                
                from src.models.base import db
                db.session.add(new_user)
                db.session.commit()
                
                # Add welcome credits
                credit_manager.add_credits(
                    user_id=new_user.id,
                    amount=100,
                    transaction_type='welcome_bonus',
                    description='Welcome bonus from Odoo registration'
                )
                
                return {
                    'success': True,
                    'user_id': new_user.id,
                    'action': 'created',
                    'message': 'User created successfully'
                }
                
        except Exception as e:
            logger.error(f"Error syncing user from Odoo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def sync_subscription_from_odoo(self, odoo_subscription_id: int) -> Dict:
        """Sync subscription data from Odoo"""
        try:
            # Get subscription data from Odoo
            result = self.make_odoo_request(
                'sale.subscription',
                'read',
                args=[[odoo_subscription_id]],
                kwargs={'fields': ['partner_id', 'state', 'template_id', 'recurring_next_date', 'recurring_total']}
            )
            
            if not result['success']:
                return result
            
            subscription_data = result['data'][0] if result['data'] else None
            if not subscription_data:
                return {'success': False, 'error': 'Subscription not found'}
            
            # Find user by Odoo partner ID
            partner_id = subscription_data['partner_id'][0]
            user = User.query.filter_by(odoo_partner_id=partner_id).first()
            
            if not user:
                # Sync user first
                user_result = self.sync_user_from_odoo(partner_id)
                if not user_result['success']:
                    return user_result
                user = User.query.get(user_result['user_id'])
            
            # Determine subscription plan
            template_name = subscription_data.get('template_id', [None, ''])[1].lower()
            plan_type = 'basic'
            if 'pro' in template_name:
                plan_type = 'pro'
            elif 'enterprise' in template_name:
                plan_type = 'enterprise'
            
            # Check if subscription already exists
            existing_subscription = Subscription.query.filter_by(
                user_id=user.id,
                odoo_subscription_id=odoo_subscription_id
            ).first()
            
            if existing_subscription:
                # Update existing subscription
                existing_subscription.status = subscription_data['state']
                existing_subscription.plan_type = plan_type
                existing_subscription.next_billing_date = datetime.strptime(
                    subscription_data['recurring_next_date'], '%Y-%m-%d'
                ) if subscription_data.get('recurring_next_date') else None
                existing_subscription.amount = subscription_data.get('recurring_total', 0)
                existing_subscription.updated_at = datetime.utcnow()
                
                from src.models.base import db
                db.session.commit()
                
                # Add monthly credits if subscription is active
                if subscription_data['state'] in ['open', 'pending']:
                    self.add_monthly_credits(user.id, plan_type)
                
                return {
                    'success': True,
                    'subscription_id': existing_subscription.id,
                    'action': 'updated'
                }
            else:
                # Create new subscription
                new_subscription = Subscription(
                    user_id=user.id,
                    plan_type=plan_type,
                    status=subscription_data['state'],
                    amount=subscription_data.get('recurring_total', 0),
                    currency='USD',
                    billing_cycle='monthly',
                    next_billing_date=datetime.strptime(
                        subscription_data['recurring_next_date'], '%Y-%m-%d'
                    ) if subscription_data.get('recurring_next_date') else None,
                    odoo_subscription_id=odoo_subscription_id,
                    created_at=datetime.utcnow()
                )
                
                from src.models.base import db
                db.session.add(new_subscription)
                db.session.commit()
                
                # Add monthly credits for new subscription
                if subscription_data['state'] in ['open', 'pending']:
                    self.add_monthly_credits(user.id, plan_type)
                
                return {
                    'success': True,
                    'subscription_id': new_subscription.id,
                    'action': 'created'
                }
                
        except Exception as e:
            logger.error(f"Error syncing subscription from Odoo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def add_monthly_credits(self, user_id: int, plan_type: str) -> Dict:
        """Add monthly credits based on subscription plan"""
        try:
            plan_info = self.subscription_plans.get(plan_type, {})
            credits_amount = plan_info.get('credits_per_month', 0)
            
            if credits_amount > 0:
                result = credit_manager.add_credits(
                    user_id=user_id,
                    amount=credits_amount,
                    transaction_type='monthly_subscription',
                    description=f'Monthly credits for {plan_type} plan'
                )
                return result
            
            return {'success': False, 'error': 'Invalid plan type'}
            
        except Exception as e:
            logger.error(f"Error adding monthly credits: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_notification_to_odoo(self, user_id: int, notification_type: str, data: Dict) -> Dict:
        """Send notification to Odoo"""
        try:
            user = User.query.get(user_id)
            if not user or not user.odoo_partner_id:
                return {'success': False, 'error': 'User not found or not linked to Odoo'}
            
            # Create notification message
            notification_messages = {
                'task_completed': f"Task completed successfully: {data.get('task_name', 'Unknown')}",
                'task_failed': f"Task failed: {data.get('error', 'Unknown error')}",
                'credits_low': f"Credits running low: {data.get('credits_remaining', 0)} remaining",
                'subscription_expired': "Subscription has expired",
                'payment_received': f"Payment received: ${data.get('amount', 0)}"
            }
            
            message = notification_messages.get(notification_type, f"Notification: {notification_type}")
            
            # Create message in Odoo
            result = self.make_odoo_request(
                'mail.message',
                'create',
                args=[{
                    'subject': f'Marketing Automation System - {notification_type.replace("_", " ").title()}',
                    'body': message,
                    'model': 'res.partner',
                    'res_id': user.odoo_partner_id,
                    'message_type': 'notification',
                    'author_id': 1  # System user
                }]
            )
            
            if result['success']:
                logger.info(f"Notification sent to Odoo for user {user_id}: {notification_type}")
                return result
            else:
                logger.error(f"Failed to send notification to Odoo: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error sending notification to Odoo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_webhook_signature(self, headers: Dict, body: str) -> bool:
        """Verify Odoo webhook signature"""
        try:
            signature = headers.get('X-Odoo-Signature')
            if not signature:
                return False
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying Odoo webhook signature: {str(e)}")
            return False
    
    def process_odoo_webhook(self, headers: Dict, body: str) -> Dict:
        """Process Odoo webhook"""
        try:
            # Verify signature
            if not self.verify_webhook_signature(headers, body):
                return {
                    'success': False,
                    'error': 'Invalid webhook signature',
                    'status': 'signature_verification_failed'
                }
            
            # Parse webhook data
            webhook_data = json.loads(body)
            event_type = webhook_data.get('event_type')
            model = webhook_data.get('model')
            record_id = webhook_data.get('record_id')
            
            logger.info(f"Processing Odoo webhook: {event_type} for {model} ID {record_id}")
            
            # Process based on event type and model
            if model == 'res.partner' and event_type in ['create', 'write']:
                return self.sync_user_from_odoo(record_id)
            
            elif model == 'sale.subscription' and event_type in ['create', 'write']:
                return self.sync_subscription_from_odoo(record_id)
            
            elif model == 'account.move' and event_type == 'write':
                return self.handle_invoice_update(record_id)
            
            else:
                return {
                    'success': True,
                    'message': f'Event {event_type} for {model} processed',
                    'status': 'processed'
                }
                
        except Exception as e:
            logger.error(f"Error processing Odoo webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def handle_invoice_update(self, invoice_id: int) -> Dict:
        """Handle invoice update from Odoo"""
        try:
            # Get invoice data
            result = self.make_odoo_request(
                'account.move',
                'read',
                args=[[invoice_id]],
                kwargs={'fields': ['partner_id', 'state', 'amount_total', 'invoice_line_ids']}
            )
            
            if not result['success']:
                return result
            
            invoice_data = result['data'][0] if result['data'] else None
            if not invoice_data:
                return {'success': False, 'error': 'Invoice not found'}
            
            # If invoice is paid, add credits
            if invoice_data['state'] == 'posted':
                partner_id = invoice_data['partner_id'][0]
                user = User.query.filter_by(odoo_partner_id=partner_id).first()
                
                if user:
                    amount = invoice_data['amount_total']
                    credits = int(amount * 20)  # 20 credits per dollar
                    
                    credit_manager.add_credits(
                        user_id=user.id,
                        amount=credits,
                        transaction_type='odoo_invoice',
                        description=f'Credits from Odoo invoice #{invoice_id}',
                        reference_id=str(invoice_id)
                    )
                    
                    return {
                        'success': True,
                        'message': f'Credits added for invoice {invoice_id}',
                        'credits_added': credits
                    }
            
            return {'success': True, 'message': 'Invoice processed'}
            
        except Exception as e:
            logger.error(f"Error handling invoice update: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_user_subscription_status(self, user_id: int) -> Dict:
        """Get user subscription status from Odoo"""
        try:
            user = User.query.get(user_id)
            if not user or not user.odoo_partner_id:
                return {'success': False, 'error': 'User not found or not linked to Odoo'}
            
            # Get active subscriptions from Odoo
            result = self.make_odoo_request(
                'sale.subscription',
                'search_read',
                kwargs={
                    'domain': [['partner_id', '=', user.odoo_partner_id], ['state', 'in', ['open', 'pending']]],
                    'fields': ['state', 'template_id', 'recurring_next_date', 'recurring_total']
                }
            )
            
            if result['success']:
                subscriptions = result['data']
                if subscriptions:
                    return {
                        'success': True,
                        'has_active_subscription': True,
                        'subscriptions': subscriptions
                    }
                else:
                    return {
                        'success': True,
                        'has_active_subscription': False,
                        'subscriptions': []
                    }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting subscription status: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_odoo_lead(self, user_data: Dict) -> Dict:
        """Create lead in Odoo CRM"""
        try:
            lead_data = {
                'name': f"Marketing Automation Interest - {user_data.get('name', 'Unknown')}",
                'partner_name': user_data.get('name'),
                'email_from': user_data.get('email'),
                'phone': user_data.get('phone'),
                'description': user_data.get('message', 'Interested in marketing automation services'),
                'source_id': 1,  # Website
                'team_id': 1,   # Sales team
                'user_id': 1    # Salesperson
            }
            
            result = self.make_odoo_request(
                'crm.lead',
                'create',
                args=[lead_data]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating Odoo lead: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global Odoo integration instance
odoo_integration = OdooCompleteIntegration()

