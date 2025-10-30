# backend/app/services/churn_prediction.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.db import get_db
from app.models import User, Order
from app.automation.triggers.event_triggers import trigger_event
from app.services.ai_services import AIService
from app.automation.integrations import ai_services
from app.automation.workflows import churn_prediction
import json

# backend/app/automation/workflows/churn_prediction.py



logger = logging.getLogger(__name__)


class ChurnPredictionService:
    """AI-powered customer churn prediction and prevention"""
    
    # Churn risk thresholds
    HIGH_RISK = 0.7
    MEDIUM_RISK = 0.4
    LOW_RISK = 0.2
    
    @staticmethod
    def predict_churn_risk(user_id: int) -> float:
        """
        Predict churn risk for a user using AI analysis
        
        Returns:
            float: Churn risk score between 0 (no risk) and 1 (high risk)
        """
        try:
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"User {user_id} not found for churn prediction")
                return 0.0
            
            # Get user activity metrics
            metrics = ChurnPredictionService._get_user_metrics(user_id)
            
            # Use AI to calculate churn risk
            risk_score = ChurnPredictionService._ai_calculate_risk(user, metrics)
            
            logger.info(f"Churn risk for user {user_id}: {risk_score:.2f}")
            return risk_score
            
        except Exception as e:
            logger.error(f"Error predicting churn for user {user_id}: {str(e)}")
            return 0.0
    
    @staticmethod
    def _get_user_metrics(user_id: int) -> Dict[str, Any]:
        """Collect user engagement metrics"""
        db = next(get_db())
        
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_60_days = now - timedelta(days=60)
        last_90_days = now - timedelta(days=90)
        
        # Get orders
        orders = db.query(Order).filter(
            Order.user_id == user_id,
            Order.created_at >= last_90_days
        ).all()
        
        orders_30d = [o for o in orders if o.created_at >= last_30_days]
        orders_60d = [o for o in orders if o.created_at >= last_60_days]
        
        # Calculate metrics
        metrics = {
            "total_orders": len(orders),
            "orders_last_30d": len(orders_30d),
            "orders_last_60d": len(orders_60d),
            "avg_order_value": sum(o.total_amount for o in orders) / len(orders) if orders else 0,
            "days_since_last_order": (now - orders[0].created_at).days if orders else 999,
            "total_spent": sum(o.total_amount for o in orders),
            "order_frequency_declining": len(orders_30d) < len(orders_60d) - len(orders_30d),
            "has_cancelled_orders": any(o.status == 'cancelled' for o in orders)
        }
        
        return metrics
    
    @staticmethod
    def _ai_calculate_risk(user: User, metrics: Dict[str, Any]) -> float:
        """Use AI to calculate churn risk based on metrics"""
        try:
            # Prepare prompt for AI
            prompt = f"""
            Analyze this customer's churn risk based on their behavior metrics:
            
            Customer Profile:
            - Days since last order: {metrics['days_since_last_order']}
            - Total orders (90 days): {metrics['total_orders']}
            - Recent orders (30 days): {metrics['orders_last_30d']}
            - Average order value: ${metrics['avg_order_value']:.2f}
            - Total spent: ${metrics['total_spent']:.2f}
            - Order frequency declining: {metrics['order_frequency_declining']}
            - Has cancelled orders: {metrics['has_cancelled_orders']}
            
            Return a churn risk score between 0.0 (no risk) and 1.0 (very high risk).
            Consider:
            - Recency: How long since last purchase
            - Frequency: How often they buy
            - Monetary: How much they spend
            - Trend: Are they buying less over time?
            
            Respond with ONLY a number between 0.0 and 1.0, nothing else.
            """
            
            # Get AI prediction
            ai_response = AIService.quick_analysis(prompt)
            
            try:
                # Extract risk score from AI response
                risk_score = float(ai_response.strip())
                risk_score = max(0.0, min(1.0, risk_score))  # Clamp between 0-1
                return risk_score
            except ValueError:
                # Fallback to rule-based if AI fails
                return ChurnPredictionService._rule_based_risk(metrics)
                
        except Exception as e:
            logger.error(f"AI churn prediction failed: {str(e)}, using rule-based")
            return ChurnPredictionService._rule_based_risk(metrics)
    
    @staticmethod
    def _rule_based_risk(metrics: Dict[str, Any]) -> float:
        """Fallback rule-based churn risk calculation"""
        risk_score = 0.0
        
        # Recency risk
        if metrics['days_since_last_order'] > 60:
            risk_score += 0.4
        elif metrics['days_since_last_order'] > 30:
            risk_score += 0.2
        
        # Frequency risk
        if metrics['orders_last_30d'] == 0:
            risk_score += 0.3
        
        # Declining trend risk
        if metrics['order_frequency_declining']:
            risk_score += 0.2
        
        # Cancellation risk
        if metrics['has_cancelled_orders']:
            risk_score += 0.1
        
        return min(1.0, risk_score)
    
    @staticmethod
    def check_and_trigger_retention(user_id: int):
        """Check churn risk and trigger retention actions if needed"""
        try:
            risk_score = ChurnPredictionService.predict_churn_risk(user_id)
            
            # Trigger retention workflows based on risk level
            if risk_score >= ChurnPredictionService.HIGH_RISK:
                ChurnPredictionService._trigger_high_risk_retention(user_id, risk_score)
            elif risk_score >= ChurnPredictionService.MEDIUM_RISK:
                ChurnPredictionService._trigger_medium_risk_retention(user_id, risk_score)
            
        except Exception as e:
            logger.error(f"Error in retention check for user {user_id}: {str(e)}")
    
    @staticmethod
    def _trigger_high_risk_retention(user_id: int, risk_score: float):
        """Trigger aggressive retention for high-risk users"""
        logger.info(f"HIGH RISK user {user_id} (score: {risk_score:.2f}) - triggering retention")
        
        trigger_event("churn_high_risk", {
            "user_id": user_id,
            "risk_score": risk_score,
            "action": "apply_15_percent_discount",
            "urgency": "high"
        })
    
    @staticmethod
    def _trigger_medium_risk_retention(user_id: int, risk_score: float):
        """Trigger moderate retention for medium-risk users"""
        logger.info(f"MEDIUM RISK user {user_id} (score: {risk_score:.2f}) - triggering retention")
        
        trigger_event("churn_medium_risk", {
            "user_id": user_id,
            "risk_score": risk_score,
            "action": "send_engagement_email",
            "urgency": "medium"
        })


# Convenience functions
def predict_churn_risk(user_id: int) -> float:
    """Quick function to predict churn risk"""
    return ChurnPredictionService.predict_churn_risk(user_id)


def apply_discount(user_id: int, discount: str):
    """Apply retention discount to user"""
    try:
        logger.info(f"Applying {discount} to user {user_id}")
        
        trigger_event("discount_applied", {
            "user_id": user_id,
            "discount": discount,
            "reason": "churn_prevention"
        })
        
    except Exception as e:
        logger.error(f"Error applying discount to user {user_id}: {str(e)}")


# Event listener decorator (for future implementation)
def listen_for(event: str, delay: str = None):
    """
    Decorator to mark functions as event listeners
    This is a placeholder for future scheduler integration
    """
    def decorator(func):
        func._event_listener = event
        func._delay = delay
        return func
    return decorator


# Example usage with decorator
@listen_for(event="low_engagement", delay="24h")
def trigger_retention_offer(user_id: int):
    """
    Triggered when user shows low engagement
    Waits 24h then checks churn risk and applies discount if needed
    """
    try:
        risk_score = predict_churn_risk(user_id)
        
        if risk_score > 0.7:  # High risk threshold
            logger.info(f"User {user_id} has high churn risk ({risk_score:.2f}), applying discount")
            apply_discount(user_id, "15% off")
        else:
            logger.info(f"User {user_id} churn risk acceptable ({risk_score:.2f}), no action needed")
            
    except Exception as e:
        logger.error(f"Error in retention offer for user {user_id}: {str(e)}")