import logging
import requests
import os
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

# --- Configuration for n8n Webhooks ---
# It's highly recommended to load this from environment variables in a production environment.
# Example: export N8N_WEBHOOK_BASE_URL="https://your-n8n-instance.com/webhook/"
# For local development with n8n, it might be something like "http://localhost:5678/webhook-test/"
N8N_WEBHOOK_BASE_URL = os.getenv("N8N_WEBHOOK_BASE_URL", "http://localhost:5678/webhook-test/")

def send_webhook_to_n8n(event_name, payload):
    """Sends an event payload as a webhook to n8n."""
    # Ensure the base URL ends with a slash to correctly append the event_name
    if not N8N_WEBHOOK_BASE_URL.endswith("/"):
        base_url = N8N_WEBHOOK_BASE_URL + "/"
    else:
        base_url = N8N_WEBHOOK_BASE_URL

    # The full webhook URL for a specific event
    webhook_url = f"{base_url}{event_name}"

    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"Successfully sent \'{event_name}\' webhook to n8n. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send \'{event_name}\' webhook to n8n: {e}")
        return False

def trigger_event(event_name, **kwargs):
    """Trigger automation workflows based on events"""
    payload = {"event_name": event_name, "data": kwargs}

    # All events will now be sent to n8n for processing
    if send_webhook_to_n8n(event_name, payload):
        logger.info(f"Event \'{event_name}\' triggered and sent to n8n.")
    else:
        logger.error(f"Failed to trigger event \'{event_name}\' via n8n webhook.")

def schedule_event(event_name, delay, **kwargs):
    """Schedule a delayed event trigger using n8n."""
    # This function will now also send a webhook to n8n, which will then handle the delay.
    # The n8n workflow would start with a webhook, then a 'Wait' node, and then trigger the actual event.
    payload = {"event_name": event_name, "delay": delay, "data": kwargs}
    if send_webhook_to_n8n("schedule_event", payload): # Use a generic 'schedule_event' endpoint in n8n
        logger.info(f"Event \'{event_name}\' scheduled with {delay} delay via n8n.")
    else:
        logger.error(f"Failed to schedule event \'{event_name}\' via n8n webhook.")

# Decorator for event listeners
def listen_for(event: str, delay: str = None):
    """
    Decorator to register event listeners
    
    Args:
        event: The event name to listen for
        delay: Optional delay (e.g., "1 hour", "30 minutes")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Event listener '{event}' triggered for function {func.__name__}")
            if delay:
                logger.info(f"Event '{event}' will be processed after {delay}")
                # Schedule the event with delay
                schedule_event(event, delay, **kwargs)
            else:
                # Execute immediately
                return func(*args, **kwargs)
        
        # Store metadata for the decorator
        wrapper._event_name = event
        wrapper._delay = delay
        wrapper._original_func = func
        
        return wrapper
    return decorator

