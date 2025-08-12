import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from src.models.base import db
from src.models.user import User
from src.models.subscription import UserSubscription
from src.models.credit_transaction import CreditTransaction
from src.services.credit_manager import credit_manager

logger = logging.getLogger(__name__)

class OdooIntegration:
    """Integration service for Odoo ERP system"""
    
    def __init__(self):
        self.odoo_url = os.getenv('ODOO_URL', 'https://your-odoo-instance.com')
        self.odoo_db = os.getenv('ODOO_DB', 'your_database')
        self.odoo_username = os.getenv('ODOO_USERNAME', 'admin')
        self.odoo_password = os.getenv('ODOO_PASSWORD', 'admin')
        self.odoo_api_key = os.getenv('ODOO_API_KEY', '')
        
        # PayPal Configuration
        self.paypal_client_id = os.getenv('PAYPAL_CLIENT_ID', '')
        self.paypal_client_secret = os.getenv('PAYPAL_CLIENT_SECRET', '')
        self.paypal_mode = os.getenv('PAYPAL_MODE', 'sandbox')  # sandbox or live
        
        if self.paypal_mode == 'sandbox':
            self.paypal_base_url = 'https://api.sandbox.paypal.com'
        else:
            self.paypal_base_url = 'https://api.paypal.com'
        
        self.session_cache = {}
        
    def authenticate_odoo(self) -> Optional[str]:
        """Authenticate with Odoo and get session ID"""
        
        try:
            auth_url = f"{self.odoo_url}/web/session/authenticate"
            
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
            
            response = requests.post(
                auth_url,
                json=auth_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') and result['result'].get('uid'):
                    session_id = response.cookies.get('session_id')
                    self.session_cache['session_id'] = session_id
                    self.session_cache['uid'] = result['result']['uid']
                    self.session_cache['expires'] = datetime.now() + timedelta(hours=8)
                    
                    logger.info("Successfully authenticated with Odoo")
                    return session_id
                else:
                    logger.error(f"Odoo authentication failed: {result}")
                    return None
            else:
                logger.error(f"Odoo authentication request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating with Odoo: {str(e)}")
            return None
    
    def get_valid_session(self) -> Optional[str]:
        """Get a valid Odoo session, authenticate if needed"""
        
        # Check if we have a cached session that's still valid
        if (self.session_cache.get('session_id') and 
            self.session_cache.get('expires') and
            datetime.now() < self.session_cache['expires']):
            return self.session_cache['session_id']
        
        # Authenticate and get new session
        return self.authenticate_odoo()
    
    def call_odoo_api(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Optional[Dict]:
        """Make API call to Odoo"""
        
        session_id = self.get_valid_session()
        if not session_id:
            return None
        
        try:
            api_url = f"{self.odoo_url}/web/dataset/call_kw"
            
            api_data = {
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
            
            cookies = {'session_id': session_id}
            
            response = requests.post(
                api_url,
                json=api_data,
                cookies=cookies,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'error' in result:
                    logger.error(f"Odoo API error: {result['error']}")
                    return None
                return result.get('result')
            else:
                logger.error(f"Odoo API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Odoo API: {str(e)}")
            return None
    
    def create_odoo_customer(self, user_data: Dict) -> Optional[int]:
        """Create customer in Odoo"""
        
        try:
            customer_data = {
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'phone': user_data.get('phone', ''),
                'is_company': False,
                'customer_rank': 1,
                'supplier_rank': 0,
                'category_id': [(6, 0, [])],  # Customer categories
                'comment': f"Created from Marketing Automation System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            # Add address information if available
            if user_data.get('street'):
                customer_data['street'] = user_data['street']
            if user_data.get('city'):
                customer_data['city'] = user_data['city']
            if user_data.get('country_code'):
                # Get country ID from Odoo
                country_id = self.get_country_id(user_data['country_code'])
                if country_id:
                    customer_data['country_id'] = country_id
            
            result = self.call_odoo_api('res.partner', 'create', [customer_data])
            
            if result:
                logger.info(f"Created Odoo customer with ID: {result}")
                return result
            else:
                logger.error("Failed to create Odoo customer")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Odoo customer: {str(e)}")
            return None
    
    def get_country_id(self, country_code: str) -> Optional[int]:
        """Get country ID from Odoo by country code"""
        
        try:
            result = self.call_odoo_api(
                'res.country', 
                'search_read', 
                [[['code', '=', country_code.upper()]]], 
                {'fields': ['id']}
            )
            
            if result and len(result) > 0:
                return result[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Error getting country ID: {str(e)}")
            return None
    
    def create_subscription_product(self, subscription_data: Dict) -> Optional[int]:
        """Create subscription product in Odoo"""
        
        try:
            product_data = {
                'name': subscription_data.get('name', 'Marketing Automation Subscription'),
                'type': 'service',
                'categ_id': 1,  # Service category
                'list_price': subscription_data.get('price', 0.0),
                'sale_ok': True,
                'purchase_ok': False,
                'recurring_invoice': True,
                'subscription_template_id': subscription_data.get('template_id'),
                'description': subscription_data.get('description', ''),
                'default_code': subscription_data.get('sku', '')
            }
            
            result = self.call_odoo_api('product.product', 'create', [product_data])
            
            if result:
                logger.info(f"Created subscription product with ID: {result}")
                return result
            else:
                logger.error("Failed to create subscription product")
                return None
                
        except Exception as e:
            logger.error(f"Error creating subscription product: {str(e)}")
            return None
    
    def create_sale_order(self, customer_id: int, order_data: Dict) -> Optional[int]:
        """Create sale order in Odoo"""
        
        try:
            order_lines = []
            for item in order_data.get('items', []):
                order_lines.append((0, 0, {
                    'product_id': item['product_id'],
                    'product_uom_qty': item.get('quantity', 1),
                    'price_unit': item.get('price', 0.0),
                    'name': item.get('description', '')
                }))
            
            sale_order_data = {
                'partner_id': customer_id,
                'order_line': order_lines,
                'state': 'draft',
                'origin': 'Marketing Automation System',
                'note': order_data.get('notes', ''),
                'payment_term_id': order_data.get('payment_term_id', 1)
            }
            
            result = self.call_odoo_api('sale.order', 'create', [sale_order_data])
            
            if result:
                logger.info(f"Created sale order with ID: {result}")
                return result
            else:
                logger.error("Failed to create sale order")
                return None
                
        except Exception as e:
            logger.error(f"Error creating sale order: {str(e)}")
            return None
    
    def confirm_sale_order(self, order_id: int) -> bool:
        """Confirm sale order in Odoo"""
        
        try:
            result = self.call_odoo_api('sale.order', 'action_confirm', [order_id])
            
            if result:
                logger.info(f"Confirmed sale order {order_id}")
                return True
            else:
                logger.error(f"Failed to confirm sale order {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error confirming sale order: {str(e)}")
            return False
    
    def get_paypal_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        
        try:
            auth_url = f"{self.paypal_base_url}/v1/oauth2/token"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            
            data = 'grant_type=client_credentials'
            
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                auth=(self.paypal_client_id, self.paypal_client_secret),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('access_token')
            else:
                logger.error(f"PayPal authentication failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {str(e)}")
            return None
    
    def create_paypal_payment(self, payment_data: Dict) -> Optional[Dict]:
        """Create PayPal payment"""
        
        access_token = self.get_paypal_access_token()
        if not access_token:
            return None
        
        try:
            payment_url = f"{self.paypal_base_url}/v1/payments/payment"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            payment_request = {
                'intent': 'sale',
                'payer': {
                    'payment_method': 'paypal'
                },
                'redirect_urls': {
                    'return_url': payment_data.get('return_url', ''),
                    'cancel_url': payment_data.get('cancel_url', '')
                },
                'transactions': [{
                    'item_list': {
                        'items': payment_data.get('items', [])
                    },
                    'amount': {
                        'currency': payment_data.get('currency', 'USD'),
                        'total': str(payment_data.get('total', 0.0))
                    },
                    'description': payment_data.get('description', 'Marketing Automation System Payment')
                }]
            }
            
            response = requests.post(
                payment_url,
                json=payment_request,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Created PayPal payment: {result.get('id')}")
                return result
            else:
                logger.error(f"PayPal payment creation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating PayPal payment: {str(e)}")
            return None
    
    def execute_paypal_payment(self, payment_id: str, payer_id: str) -> Optional[Dict]:
        """Execute PayPal payment"""
        
        access_token = self.get_paypal_access_token()
        if not access_token:
            return None
        
        try:
            execute_url = f"{self.paypal_base_url}/v1/payments/payment/{payment_id}/execute"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            execute_request = {
                'payer_id': payer_id
            }
            
            response = requests.post(
                execute_url,
                json=execute_request,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Executed PayPal payment: {payment_id}")
                return result
            else:
                logger.error(f"PayPal payment execution failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing PayPal payment: {str(e)}")
            return None
    
    def process_subscription_payment(self, user_id: int, subscription_plan: str, amount: float) -> Dict:
        """Process subscription payment through PayPal and Odoo"""
        
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Create or get Odoo customer
            odoo_customer_id = user.odoo_customer_id
            if not odoo_customer_id:
                customer_data = {
                    'name': user.full_name or user.email,
                    'email': user.email,
                    'phone': user.phone_number
                }
                odoo_customer_id = self.create_odoo_customer(customer_data)
                
                if odoo_customer_id:
                    user.odoo_customer_id = odoo_customer_id
                    user.save()
                else:
                    logger.warning("Failed to create Odoo customer, continuing without Odoo integration")
            
            # Create PayPal payment
            payment_data = {
                'items': [{
                    'name': f'Marketing Automation - {subscription_plan}',
                    'sku': f'ma-{subscription_plan.lower()}',
                    'price': str(amount),
                    'currency': 'USD',
                    'quantity': 1
                }],
                'total': amount,
                'currency': 'USD',
                'description': f'Marketing Automation {subscription_plan} Subscription',
                'return_url': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/payment/success",
                'cancel_url': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/payment/cancel"
            }
            
            paypal_payment = self.create_paypal_payment(payment_data)
            
            if not paypal_payment:
                return {'success': False, 'error': 'Failed to create PayPal payment'}
            
            # Get approval URL
            approval_url = None
            for link in paypal_payment.get('links', []):
                if link.get('rel') == 'approval_url':
                    approval_url = link.get('href')
                    break
            
            if not approval_url:
                return {'success': False, 'error': 'PayPal approval URL not found'}
            
            # Store payment information
            payment_info = {
                'paypal_payment_id': paypal_payment.get('id'),
                'amount': amount,
                'currency': 'USD',
                'subscription_plan': subscription_plan,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            user.set_payment_info(payment_info)
            user.save()
            
            return {
                'success': True,
                'payment_id': paypal_payment.get('id'),
                'approval_url': approval_url,
                'amount': amount,
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error processing subscription payment: {str(e)}")
            return {'success': False, 'error': 'Internal server error'}
    
    def complete_subscription_payment(self, payment_id: str, payer_id: str) -> Dict:
        """Complete subscription payment and activate subscription"""
        
        try:
            # Execute PayPal payment
            payment_result = self.execute_paypal_payment(payment_id, payer_id)
            
            if not payment_result or payment_result.get('state') != 'approved':
                return {'success': False, 'error': 'Payment execution failed'}
            
            # Find user by payment ID
            users = User.query.all()
            user = None
            
            for u in users:
                payment_info = u.get_payment_info()
                if payment_info and payment_info.get('paypal_payment_id') == payment_id:
                    user = u
                    break
            
            if not user:
                return {'success': False, 'error': 'User not found for payment'}
            
            payment_info = user.get_payment_info()
            subscription_plan = payment_info.get('subscription_plan')
            amount = payment_info.get('amount')
            
            # Create subscription record
            subscription = UserSubscription(
                user_id=user.id,
                plan_name=subscription_plan,
                status='active',
                start_date=datetime.now(),
                amount_paid=amount,
                payment_method='paypal',
                payment_reference=payment_id
            )
            
            # Set end date based on plan (assuming monthly)
            subscription.end_date = datetime.now() + timedelta(days=30)
            subscription.save()
            
            # Update user subscription status
            user.subscription_status = subscription_plan
            user.subscription_expires_at = subscription.end_date
            
            # Add credits based on subscription plan
            credit_packages = {
                'basic': 1000,
                'premium': 5000,
                'enterprise': 20000
            }
            
            credits_to_add = credit_packages.get(subscription_plan.lower(), 1000)
            
            credit_result = credit_manager.add_credits(
                user_id=user.id,
                amount=credits_to_add,
                description=f"Subscription activation: {subscription_plan}",
                category='subscription',
                reference_id=str(subscription.id)
            )
            
            if not credit_result['success']:
                logger.error(f"Failed to add subscription credits: {credit_result['error']}")
            
            # Update payment info
            payment_info['status'] = 'completed'
            payment_info['completed_at'] = datetime.now().isoformat()
            user.set_payment_info(payment_info)
            user.save()
            
            # Create sale order in Odoo if customer exists
            if user.odoo_customer_id:
                try:
                    order_data = {
                        'items': [{
                            'product_id': 1,  # Default product ID, should be configured
                            'quantity': 1,
                            'price': amount,
                            'description': f'Marketing Automation {subscription_plan} Subscription'
                        }],
                        'notes': f'PayPal Payment ID: {payment_id}'
                    }
                    
                    order_id = self.create_sale_order(user.odoo_customer_id, order_data)
                    if order_id:
                        self.confirm_sale_order(order_id)
                        logger.info(f"Created and confirmed Odoo sale order: {order_id}")
                    
                except Exception as e:
                    logger.error(f"Error creating Odoo sale order: {str(e)}")
            
            logger.info(f"Successfully completed subscription payment for user {user.id}")
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'plan': subscription_plan,
                'credits_added': credits_to_add,
                'expires_at': subscription.end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error completing subscription payment: {str(e)}")
            return {'success': False, 'error': 'Internal server error'}
    
    def sync_user_with_odoo(self, user_id: int) -> Dict:
        """Sync user data with Odoo"""
        
        try:
            user = User.get_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Create or update Odoo customer
            if user.odoo_customer_id:
                # Update existing customer
                customer_data = {
                    'name': user.full_name or user.email,
                    'email': user.email,
                    'phone': user.phone_number
                }
                
                result = self.call_odoo_api('res.partner', 'write', [[user.odoo_customer_id], customer_data])
                
                if result:
                    logger.info(f"Updated Odoo customer {user.odoo_customer_id}")
                    return {'success': True, 'action': 'updated', 'odoo_id': user.odoo_customer_id}
                else:
                    return {'success': False, 'error': 'Failed to update Odoo customer'}
            else:
                # Create new customer
                customer_data = {
                    'name': user.full_name or user.email,
                    'email': user.email,
                    'phone': user.phone_number
                }
                
                odoo_customer_id = self.create_odoo_customer(customer_data)
                
                if odoo_customer_id:
                    user.odoo_customer_id = odoo_customer_id
                    user.save()
                    
                    logger.info(f"Created Odoo customer {odoo_customer_id}")
                    return {'success': True, 'action': 'created', 'odoo_id': odoo_customer_id}
                else:
                    return {'success': False, 'error': 'Failed to create Odoo customer'}
                    
        except Exception as e:
            logger.error(f"Error syncing user with Odoo: {str(e)}")
            return {'success': False, 'error': 'Internal server error'}
    
    def get_odoo_invoices(self, customer_id: int) -> List[Dict]:
        """Get customer invoices from Odoo"""
        
        try:
            result = self.call_odoo_api(
                'account.move',
                'search_read',
                [[['partner_id', '=', customer_id], ['move_type', '=', 'out_invoice']]],
                {'fields': ['name', 'invoice_date', 'amount_total', 'state', 'payment_state']}
            )
            
            return result or []
            
        except Exception as e:
            logger.error(f"Error getting Odoo invoices: {str(e)}")
            return []
    
    def validate_odoo_connection(self) -> Dict:
        """Validate connection to Odoo"""
        
        try:
            session_id = self.get_valid_session()
            
            if session_id:
                # Test API call
                result = self.call_odoo_api('res.users', 'read', [self.session_cache['uid']], {'fields': ['name', 'login']})
                
                if result:
                    return {
                        'success': True,
                        'message': 'Odoo connection successful',
                        'user': result[0] if result else None
                    }
                else:
                    return {'success': False, 'error': 'Failed to read user data'}
            else:
                return {'success': False, 'error': 'Authentication failed'}
                
        except Exception as e:
            logger.error(f"Error validating Odoo connection: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global Odoo integration instance
odoo_integration = OdooIntegration()

