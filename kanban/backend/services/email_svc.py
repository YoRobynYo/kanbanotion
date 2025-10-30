import logging
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending various types of emails"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, email_type: str = "general"):
        """Send email using configured email service"""
        try:
            # For now, just log the email (in production, use SendGrid or similar)
            logger.info(f"[Email → {to_email}] Subject: {subject}")
            logger.info(f"[Email → {to_email}] Body: {body[:100]}...")
            logger.info(f"[Email → {to_email}] Type: {email_type}")
            
            # TODO: Implement actual email sending with SendGrid
            # if settings.SENDGRID_API_KEY:
            #     # Use SendGrid to send email
            #     pass
            
            return True
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_order_confirmation(email: str, order_id: int, total_cents: int, currency: str):
        """Send order confirmation email"""
        subject = f"Order Confirmation #{order_id}"
        body = f"Thank you for your order! Total: {total_cents/100:.2f} {currency.upper()}"
        
        return EmailService.send_email(
            to_email=email,
            subject=subject,
            body=body,
            email_type="order_confirmation"
        )
    
    @staticmethod
    def send_cart_abandonment(email: str, subject: str, body: str):
        """Send cart abandonment email"""
        return EmailService.send_email(
            to_email=email,
            subject=subject,
            body=body,
            email_type="cart_abandonment"
        )

# Legacy function for backward compatibility
def send_order_confirmation(email: str, order_id: int, total_cents: int, currency: str):
    """Legacy function - redirects to EmailService"""
    return EmailService.send_order_confirmation(email, order_id, total_cents, currency)
