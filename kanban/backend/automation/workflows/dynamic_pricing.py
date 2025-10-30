from app.services.ai_services import AIService
from app.services.product_service import update_price, get_product_details

# Placeholder for get_sales_trend. You would replace this with your actual implementation.
def get_sales_trend():
    """Simulates fetching current sales data."""
    # In a real application, this would query your sales database or analytics service.
    return {"product_abc": {"demand": "high"}, "product_xyz": {"demand": "medium"}}


def adjust_prices_for_demand():
    """Automatically sets prices based on real-time demand."""
    # 1. Get current sales data (use YOUR existing service)
    sales_data = get_sales_trend()
    
    # 2. Use AI to determine optimal pricing
    prompt = f"Current demand trend: {sales_data}. For each product, return ONLY a JSON object with product_id as key and optimal_price as value. Example: {{'product_abc': 120.0, 'product_xyz': 180.0}}"

    response_text = AIService.quick_analysis(prompt)

    # Parse the AI response
    import json
    try:
        response = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback if AI doesn't return valid JSON
        response = {"default_product": "150.0"}
    
    # 3. Update prices (uses YOUR existing update function)
    for product_id, new_price_str in response.items():
        try:
            new_price = float(new_price_str)
        except ValueError:
            print(f"Warning: Could not convert price '{new_price_str}' for product {product_id} to float. Skipping.")
            continue

        # Retrieve product details to get min_price
        product = get_product_details(product_id)
        if not product:
            print(f"Warning: Product details not found for {product_id}. Skipping price adjustment.")
            continue

        # Apply minimum price threshold
        # Never drop below 50% of min price
        if new_price < product.min_price * 0.5:
            new_price = product.min_price * 0.5
            print(f"Adjusted price for {product_id} to {new_price} due to minimum threshold.")

        update_price(product_id, new_price)

