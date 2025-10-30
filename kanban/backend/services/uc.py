import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import dynamic pricing, but don't fail if it doesn't exist
try:
    from ..automation.workflows.dynamic_pricing import adjust_prices_for_demand
    HAS_DYNAMIC_PRICING = True
except ImportError:
    HAS_DYNAMIC_PRICING = False
    logger.warning("Dynamic pricing module not available")

def run_scheduled_jobs():
    """Runs all scheduled background jobs."""
    logger.info("Running scheduled jobs...")
    
    try:
        # Add the dynamic pricing adjustment to your scheduled jobs
        if HAS_DYNAMIC_PRICING:
            logger.info("Executing dynamic pricing adjustment...")
            adjust_prices_for_demand()
            logger.info("Dynamic pricing adjustment completed.")
        else:
            logger.info("Dynamic pricing not available, skipping...")
            
        # Add other scheduled jobs here
        logger.info("All scheduled jobs completed successfully.")
        
    except Exception as e:
        logger.error(f"Error running scheduled jobs: {e}")
        raise

