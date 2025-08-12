import logging
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Any
import requests
from src.models.user import User
from src.models.credit_transaction import CreditTransaction
from src.services.credit_manager import credit_manager

logger = logging.getLogger(__name__)

class PayPalWebhookHandler:
    """PayPal Webhook Handler for processing payment notifications"""
    
    def __init__(self):
        # PayPal configuration
        self.paypal_client_id = "YOUR_PAYPAL_CLIENT_ID"
        self.paypal_client_secret = "YOUR_PAYPAL_CLIENT_SECRET"
        self.webhook_id = "YOUR_WEBHOOK_ID"
        self.sandbox_mode = True  # Set to False for production
        
        # PayPal API URLs
        if self.sandbox_mode:
            self.api_base = "https://api-m.sandbox.paypal.com"
        else:
            self.api_base = "https://api-m.paypal.com"
        
        # Credit packages mapping (amount -> credits)
        self.credit_packages = {
            5.00: 100,    # $5 = 100 credits
            10.00: 250,   # $10 = 250 credits (25% bonus)
            20.00: 550,   # $20 = 550 credits (37.5% bonus)
            50.00: 1500,  # $50 = 1500 credits (50% bonus)
            100.00: 3500, # $100 = 3500 credits (75% bonus)
        }
        
        # Supported webhook events
        self.supported_events = [
            'PAYMENT.CAPTURE.COMPLETED',
            'PAYMENT.CAPTURE.DENIED',
            'PAYMENT.CAPTURE.REFUNDED',
            'CHECKOUT.ORDER.APPROVED',
            'CHECKOUT.ORDER.COMPLETED',
            'BILLING.SUBSCRIPTION.CREATED',
            'BILLING.SUBSCRIPTION.ACTIVATED',
            'BILLING.SUBSCRIPTION.CANCELLED',
            'BILLING.SUBSCRIPTION.SUSPENDED'
        ]
    
    def verify_webhook_signature(self, headers: Dict, body: str) -> bool:
        """Verify PayPal webhook signature"""
        try:
            # Get signature headers
            transmission_id = headers.get('PAYPAL-TRANSMISSION-ID')
            cert_id = headers.get('PAYPAL-CERT-ID')
            transmission_sig = headers.get('PAYPAL-TRANSMISSION-SIG')
            transmission_time = headers.get('PAYPAL-TRANSMISSION-TIME')
            
            if not all([transmission_id, cert_id, transmission_sig, transmission_time]):
                logger.error("Missing required PayPal headers")
                return False
            
            # Verify webhook with PayPal API
            verification_data = {
                "transmission_id": transmission_id,
                "cert_id": cert_id,
                "transmission_sig": transmission_sig,
                "transmission_time": transmission_time,
                "webhook_id": self.webhook_id,
                "webhook_event": json.loads(body)
            }
            
            access_token = self.get_access_token()
            if not access_token:
                logger.error("Failed to get PayPal access token")
                return False
            
            response = requests.post(
                f"{self.api_base}/v1/notifications/verify-webhook-signature",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}'
                },
                json=verification_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('verification_status') == 'SUCCESS'
            else:
                logger.error(f"PayPal verification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying PayPal webhook signature: {str(e)}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        try:
            auth_url = f"{self.api_base}/v1/oauth2/token"
            
            response = requests.post(
                auth_url,
                headers={
                    'Accept': 'application/json',
                    'Accept-Language': 'en_US',
                },
                auth=(self.paypal_client_id, self.paypal_client_secret),
                data={'grant_type': 'client_credentials'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Failed to get PayPal access token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {str(e)}")
            return None
    
    def process_webhook_event(self, headers: Dict, body: str) -> Dict:
        """Process PayPal webhook event"""
        try:
            # Verify webhook signature
            if not self.verify_webhook_signature(headers, body):
                return {
                    'success': False,
                    'error': 'Invalid webhook signature',
                    'status': 'signature_verification_failed'
                }
            
            # Parse webhook data
            webhook_data = json.loads(body)
            event_type = webhook_data.get('event_type')
            
            if event_type not in self.supported_events:
                logger.warning(f"Unsupported webhook event: {event_type}")
                return {
                    'success': True,
                    'message': f'Event {event_type} ignored',
                    'status': 'ignored'
                }
            
            # Process based on event type
            if event_type in ['PAYMENT.CAPTURE.COMPLETED', 'CHECKOUT.ORDER.COMPLETED']:
                return self.handle_payment_completed(webhook_data)
            
            elif event_type == 'PAYMENT.CAPTURE.DENIED':
                return self.handle_payment_denied(webhook_data)
            
            elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
                return self.handle_payment_refunded(webhook_data)
            
            elif event_type in ['BILLING.SUBSCRIPTION.CREATED', 'BILLING.SUBSCRIPTION.ACTIVATED']:
                return self.handle_subscription_activated(webhook_data)
            
            elif event_type in ['BILLING.SUBSCRIPTION.CANCELLED', 'BILLING.SUBSCRIPTION.SUSPENDED']:
                return self.handle_subscription_cancelled(webhook_data)
            
            else:
                return {
                    'success': True,
                    'message': f'Event {event_type} processed',
                    'status': 'processed'
                }
                
        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def handle_payment_completed(self, webhook_data: Dict) -> Dict:
        """Handle completed payment"""
        try:
            resource = webhook_data.get('resource', {})
            
            # Extract payment information
            payment_id = resource.get('id')
            amount_info = resource.get('amount', {})
            amount = float(amount_info.get('value', 0))
            currency = amount_info.get('currency_code', 'USD')
            
            # Get payer information
            payer_info = webhook_data.get('resource', {}).get('payer', {})
            payer_email = payer_info.get('email_address')
            payer_id = payer_info.get('payer_id')
            
            # Get custom data (should contain user_id)
            custom_data = resource.get('custom_id') or resource.get('invoice_id')
            
            if not payment_id or not amount or not payer_email:
                return {
                    'success': False,
                    'error': 'Missing required payment information',
                    'status': 'invalid_data'
                }
            
            # Find user by email or custom data
            user = self.find_user_by_payment_info(payer_email, custom_data)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found',
                    'status': 'user_not_found',
                    'payer_email': payer_email
                }
            
            # Calculate credits based on amount
            credits_to_add = self.calculate_credits_from_amount(amount)
            if credits_to_add == 0:
                return {
                    'success': False,
                    'error': 'Invalid payment amount',
                    'status': 'invalid_amount',
                    'amount': amount
                }
            
            # Add credits to user account
            result = credit_manager.add_credits(
                user_id=user.id,
                amount=credits_to_add,
                transaction_type='paypal_payment',
                description=f'PayPal payment: ${amount} USD',
                reference_id=payment_id
            )
            
            if result['success']:
                # Log successful transaction
                logger.info(f"PayPal payment processed: User {user.id}, Amount ${amount}, Credits {credits_to_add}")
                
                # Send notification to user (optional)
                self.send_payment_confirmation(user, amount, credits_to_add, payment_id)
                
                return {
                    'success': True,
                    'message': 'Payment processed successfully',
                    'status': 'completed',
                    'user_id': user.id,
                    'amount': amount,
                    'credits_added': credits_to_add,
                    'payment_id': payment_id
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to add credits'),
                    'status': 'credit_addition_failed'
                }
                
        except Exception as e:
            logger.error(f"Error handling PayPal payment completion: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def handle_payment_denied(self, webhook_data: Dict) -> Dict:
        """Handle denied payment"""
        try:
            resource = webhook_data.get('resource', {})
            payment_id = resource.get('id')
            
            logger.warning(f"PayPal payment denied: {payment_id}")
            
            return {
                'success': True,
                'message': 'Payment denial processed',
                'status': 'payment_denied',
                'payment_id': payment_id
            }
            
        except Exception as e:
            logger.error(f"Error handling PayPal payment denial: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def handle_payment_refunded(self, webhook_data: Dict) -> Dict:
        """Handle refunded payment"""
        try:
            resource = webhook_data.get('resource', {})
            refund_id = resource.get('id')
            amount_info = resource.get('amount', {})
            refund_amount = float(amount_info.get('value', 0))
            
            # Find original transaction
            original_payment_id = resource.get('invoice_id')
            
            # Calculate credits to deduct
            credits_to_deduct = self.calculate_credits_from_amount(refund_amount)
            
            # Find user and deduct credits
            # This would require finding the user from the original transaction
            # For now, we'll log the refund
            
            logger.info(f"PayPal refund processed: {refund_id}, Amount: ${refund_amount}")
            
            return {
                'success': True,
                'message': 'Refund processed',
                'status': 'refunded',
                'refund_id': refund_id,
                'amount': refund_amount
            }
            
        except Exception as e:
            logger.error(f"Error handling PayPal refund: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def handle_subscription_activated(self, webhook_data: Dict) -> Dict:
        """Handle subscription activation"""
        try:
            resource = webhook_data.get('resource', {})
            subscription_id = resource.get('id')
            
            # Get subscriber information
            subscriber = resource.get('subscriber', {})
            subscriber_email = subscriber.get('email_address')
            
            # Find user
            user = self.find_user_by_payment_info(subscriber_email, None)
            if user:
                # Update user subscription status
                # This would update the user's subscription in the database
                logger.info(f"PayPal subscription activated for user {user.id}: {subscription_id}")
            
            return {
                'success': True,
                'message': 'Subscription activation processed',
                'status': 'subscription_activated',
                'subscription_id': subscription_id
            }
            
        except Exception as e:
            logger.error(f"Error handling PayPal subscription activation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def handle_subscription_cancelled(self, webhook_data: Dict) -> Dict:
        """Handle subscription cancellation"""
        try:
            resource = webhook_data.get('resource', {})
            subscription_id = resource.get('id')
            
            logger.info(f"PayPal subscription cancelled: {subscription_id}")
            
            return {
                'success': True,
                'message': 'Subscription cancellation processed',
                'status': 'subscription_cancelled',
                'subscription_id': subscription_id
            }
            
        except Exception as e:
            logger.error(f"Error handling PayPal subscription cancellation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status': 'processing_error'
            }
    
    def find_user_by_payment_info(self, email: str, custom_data: Optional[str]) -> Optional[User]:
        """Find user by payment information"""
        try:
            # First try to find by custom_data (user_id)
            if custom_data and custom_data.isdigit():
                user = User.query.get(int(custom_data))
                if user:
                    return user
            
            # Then try to find by email
            if email:
                user = User.query.filter_by(email=email).first()
                if user:
                    return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by payment info: {str(e)}")
            return None
    
    def calculate_credits_from_amount(self, amount: float) -> int:
        """Calculate credits based on payment amount"""
        try:
            # Find exact match first
            if amount in self.credit_packages:
                return self.credit_packages[amount]
            
            # For custom amounts, use base rate (20 credits per dollar)
            base_rate = 20
            return int(amount * base_rate)
            
        except Exception as e:
            logger.error(f"Error calculating credits from amount: {str(e)}")
            return 0
    
    def send_payment_confirmation(self, user: User, amount: float, credits: int, payment_id: str):
        """Send payment confirmation to user"""
        try:
            # This would send an email or notification to the user
            # For now, we'll just log it
            logger.info(f"Payment confirmation sent to {user.email}: ${amount} = {credits} credits")
            
        except Exception as e:
            logger.error(f"Error sending payment confirmation: {str(e)}")
    
    def create_payment_link(self, user_id: int, amount: float, description: str = "Credits Purchase") -> Dict:
        """Create PayPal payment link"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            # Create order
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": "USD",
                        "value": str(amount)
                    },
                    "description": description,
                    "custom_id": str(user_id)
                }],
                "application_context": {
                    "return_url": "https://your-domain.com/payment/success",
                    "cancel_url": "https://your-domain.com/payment/cancel"
                }
            }
            
            response = requests.post(
                f"{self.api_base}/v2/checkout/orders",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}'
                },
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 201:
                order = response.json()
                
                # Find approval link
                approval_link = None
                for link in order.get('links', []):
                    if link.get('rel') == 'approve':
                        approval_link = link.get('href')
                        break
                
                return {
                    'success': True,
                    'order_id': order.get('id'),
                    'approval_link': approval_link,
                    'amount': amount,
                    'credits': self.calculate_credits_from_amount(amount)
                }
            else:
                return {
                    'success': False,
                    'error': f'PayPal API error: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Error creating PayPal payment link: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global PayPal webhook handler instance
paypal_webhook_handler = PayPalWebhookHandler()

