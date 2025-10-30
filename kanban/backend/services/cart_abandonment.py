# backend/app/automation/workflows/cart_abandonment.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.db import get_db
from app.models import User, Cart, CartItem, Product, ProductView
from app.services.ai_services import AIService
from app.services.email_svc import EmailService
from app.automation.triggers.event_triggers import trigger_event, listen_for

logger = logging.getLogger(__name__)


class CartAbandonmentService:
    """Automated cart abandonment recovery with AI personalization"""
    
    @staticmethod
    def get_viewed_items(user_id: int, limit: int = 3) -> List[Product]:
        """Get user's recently viewed items from database"""
        try:
            db = next(get_db())
            
            # Get last viewed products (excluding items already in cart)
            viewed_products = db.query(Product).join(
                ProductView, ProductView.product_id == Product.id
            ).filter(
                ProductView.user_id == user_id
            ).order_by(
                ProductView.viewed_at.desc()
            ).limit(limit).all()
            
            return viewed_products
            
        except Exception as e:
            logger.error(f"Error fetching viewed items for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def generate_personalized_email(
        user_name: str,
        cart_items: List[str],
        viewed_items: List[str] = None,
        cart_value: float = 0.0
    ) -> Dict[str, str]:
        """
        Generate personalized cart abandonment email using AI
        
        Returns:
            Dict with 'subject' and 'body' keys
        """
        try:
            # Build context for AI
            cart_products = ", ".join(cart_items) if cart_items else "some great items"
            viewed_products = ", ".join(viewed_items) if viewed_items else ""
            
            prompt = f"""
            Write a friendly, personalized cart abandonment email for an e-commerce customer.
            
            Customer name: {user_name}
            Items in cart: {cart_products}
            Cart value: ${cart_value:.2f}
            Recently viewed: {viewed_products if viewed_products else "N/A"}
            
            Requirements:
            - Warm, conversational tone (not salesy or pushy)
            - Remind them about their cart items
            - If they viewed other items, subtly mention them as recommendations
            - Include urgency (limited stock or sale ending) but naturally
            - End with clear call-to-action to complete purchase
            - Keep it concise (3-4 short paragraphs max)
            
            Format as JSON with keys: "subject" and "body"
            """
            
            # Get AI-generated email
            ai_response = AIService.generate_content(prompt)
            
            # Parse AI response
            import json
            try:
                email_content = json.loads(ai_response)
                return {
                    "subject": email_content.get("subject", f"Hey {user_name}, your cart is waiting!"),
                    "body": email_content.get("body", CartAbandonmentService._fallback_email_body(user_name, cart_products))
                }
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                return {
                    "subject": f"Hey {user_name}, your cart is waiting!",
                    "body": CartAbandonmentService._fallback_email_body(user_name, cart_products)
                }
                
        except Exception as e:
            logger.error(f"Error generating personalized email: {str(e)}")
            return {
                "subject": f"Hey {user_name}, your cart is waiting!",
                "body": CartAbandonmentService._fallback_email_body(user_name, cart_products)
            }
    
    @staticmethod
    def _fallback_email_body(user_name: str, cart_items: str) -> str:
        """Fallback email template if AI generation fails"""
        return f"""
        Hi {user_name},
        
        We noticed you left some items in your cart: {cart_items}
        
        These popular items won't last long! Complete your purchase now before they're gone.
        
        [Complete My Purchase]
        
        Thanks,
        Your E-commerce Team
        """
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        """Send email using existing email service"""
        try:
            EmailService.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                email_type="cart_abandonment"
            )
            logger.info(f"Cart abandonment email sent to {to_email}")
            
        except Exception as e:
            logger.error(f"Error sending cart abandonment email to {to_email}: {str(e)}")
    
    @staticmethod
    def process_abandoned_cart(user_id: int, cart_id: int):
        """
        Main workflow for processing abandoned carts
        Called 1 hour after cart creation
        """
        try:
            db = next(get_db())
            
            # Get user and cart
            user = db.query(User).filter(User.id == user_id).first()
            cart = db.query(Cart).filter(Cart.id == cart_id).first()
            
            if not user or not cart:
                logger.warning(f"User {user_id} or cart {cart_id} not found")
                return
            
            # Check if cart still has items and hasn't been converted to order
            if not cart.items or cart.status == 'completed':
                logger.info(f"Cart {cart_id} already completed or empty, skipping")
                return
            
            # Get cart details
            cart_items = [item.product.name for item in cart.items]
            cart_value = sum(item.quantity * item.product.price for item in cart.items)
            
            # Get viewed items
            viewed_items = CartAbandonmentService.get_viewed_items(user_id)
            viewed_item_names = [item.name for item in viewed_items]
            
            # Generate personalized email
            email_content = CartAbandonmentService.generate_personalized_email(
                user_name=user.name or user.email.split('@')[0],
                cart_items=cart_items,
                viewed_items=viewed_item_names,
                cart_value=cart_value
            )
            
            # Send email
            CartAbandonmentService.send_email(
                to_email=user.email,
                subject=email_content['subject'],
                body=email_content['body']
            )
            
            # Trigger automation event for tracking
            trigger_event("cart_abandonment_email_sent", {
                "user_id": user_id,
                "cart_id": cart_id,
                "cart_value": float(cart_value),
                "items_count": len(cart_items)
            })
            
            logger.info(f"Cart abandonment workflow completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error processing abandoned cart {cart_id}: {str(e)}")


# Decorator-based event listener (as per your original design)
@listen_for(event="cart_created", delay="1 hour")
def send_abandonment_email(user_id: int, cart_id: int):
    """
    Triggered 1 hour after cart creation
    Sends personalized abandonment email with AI-generated content
    """
    try:
        logger.info(f"Cart abandonment trigger fired for user {user_id}, cart {cart_id}")
        CartAbandonmentService.process_abandoned_cart(user_id, cart_id)
        
    except Exception as e:
        logger.error(f"Error in abandonment email trigger: {str(e)}")


# Convenience functions (matching your original naming)
def generate_personalized_email(user_name: str, product_names: List[str], viewed_items: List[str] = None) -> str:
    """Quick function to generate email body"""
    result = CartAbandonmentService.generate_personalized_email(
        user_name=user_name,
        cart_items=product_names,
        viewed_items=viewed_items
    )
    return result['body']


def get_viewed_items(user_id: int) -> List[Product]:
    """Quick function to get viewed items"""
    return CartAbandonmentService.get_viewed_items(user_id)


def send_email(to_email: str, subject: str, body: str):
    """Quick function to send email"""
    CartAbandonmentService.send_email(to_email, subject, body)