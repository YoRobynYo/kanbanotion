# backend/app/services/order_service.py

from typing import Dict, Any, List
from datetime import datetime
from app.models import Order, OrderItem
from app.db import get_db
from app.automation.triggers.event_triggers import trigger_event
import logging

logger = logging.getLogger(__name__)


class OrderService:
    """Service for handling order operations with automation triggers"""
    
    @staticmethod
    def create_order(user_id: int, items: List[Dict[str, Any]], payment_info: Dict[str, Any]) -> Order:
        """
        Create a new order and trigger automation workflows
        
        Args:
            user_id: ID of the user placing the order
            items: List of items with product_id, quantity, price
            payment_info: Payment details (payment_method, transaction_id, etc.)
        
        Returns:
            Order: The created order object
        """
        try:
            db = next(get_db())
            
            # Calculate total
            total_amount = sum(item['price'] * item['quantity'] for item in items)
            
            # Create order
            order = Order(
                user_id=user_id,
                total_amount=total_amount,
                status='pending',
                payment_method=payment_info.get('payment_method'),
                transaction_id=payment_info.get('transaction_id'),
                created_at=datetime.utcnow()
            )
            
            db.add(order)
            db.flush()  # Get order.id without committing
            
            # Add order items
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                db.add(order_item)
            
            # Commit to database
            db.commit()
            db.refresh(order)
            
            # 🚀 TRIGGER AUTOMATION EVENT
            trigger_event("order_created", {
                "order_id": order.id,
                "user_id": user_id,
                "total_amount": float(total_amount),
                "items": items,
                "status": order.status,
                "created_at": str(order.created_at)
            })
            
            logger.info(f"Order {order.id} created successfully for user {user_id}")
            return order
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating order: {str(e)}")
            raise
    
    @staticmethod
    def update_order_status(order_id: int, new_status: str) -> Order:
        """Update order status and trigger automation"""
        try:
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(order)
            
            # 🚀 TRIGGER AUTOMATION EVENT
            trigger_event("order_status_changed", {
                "order_id": order.id,
                "old_status": old_status,
                "new_status": new_status,
                "user_id": order.user_id
            })
            
            logger.info(f"Order {order_id} status updated: {old_status} -> {new_status}")
            return order
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating order status: {str(e)}")
            raise
    
    @staticmethod
    def cancel_order(order_id: int, reason: str = None) -> Order:
        """Cancel an order and trigger automation"""
        try:
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if order.status in ['shipped', 'delivered', 'cancelled']:
                raise ValueError(f"Cannot cancel order with status: {order.status}")
            
            order.status = 'cancelled'
            order.cancellation_reason = reason
            order.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(order)
            
            # 🚀 TRIGGER AUTOMATION EVENT
            trigger_event("order_cancelled", {
                "order_id": order.id,
                "user_id": order.user_id,
                "reason": reason,
                "refund_amount": float(order.total_amount)
            })
            
            logger.info(f"Order {order_id} cancelled. Reason: {reason}")
            return order
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling order: {str(e)}")
            raise
    
    @staticmethod
    def get_order(order_id: int) -> Order:
        """Get order by ID"""
        db = next(get_db())
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        return order
    
    @staticmethod
    def get_user_orders(user_id: int) -> List[Order]:
        """Get all orders for a user"""
        db = next(get_db())
        orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
        return orders


# Legacy function support (for backward compatibility)
def create_order(user, items):
    """Legacy function - redirects to OrderService"""
    return OrderService.create_order(
        user_id=user.id if hasattr(user, 'id') else user,
        items=items,
        payment_info={}
    )