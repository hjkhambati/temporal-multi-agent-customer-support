"""Order-related tools for the Order Specialist agent"""

import dspy
from typing import Dict, List, Any, Optional
from datetime import datetime
from data.persistent_data import get_customer_orders, get_order_by_id

def search_orders(customer_id: str, order_id: Optional[str] = None) -> Dict[str, Any]:
    """Search for orders by customer ID or specific order ID"""
    try:
        if order_id:
            order = get_order_by_id(order_id)
            if order and order.get("customer_id") == customer_id:
                return {"success": True, "orders": [order]}
            else:
                return {"success": False, "error": "Order not found or doesn't belong to customer"}
        else:
            orders = get_customer_orders(customer_id)
            return {"success": True, "orders": orders}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_order_status(order_id: str) -> Dict[str, Any]:
    """Get current status and tracking information for an order"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        status_info = {
            "order_id": order_id,
            "status": order["status"],
            "order_date": order["order_date"],
            "tracking": order["shipping"].get("tracking"),
            "estimated_delivery": order.get("estimated_delivery"),
            "delivery_date": order.get("delivery_date")
        }
        
        return {"success": True, "status_info": status_info}
    except Exception as e:
        return {"success": False, "error": str(e)}

def modify_order(order_id: str, action: str, details: Optional[Dict] = None) -> Dict[str, Any]:
    """Modify an existing order (cancel, change shipping, etc.)"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if order["status"] in ["shipped", "delivered"]:
            return {"success": False, "error": "Cannot modify order that has been shipped or delivered"}
        
        # Mock modification logic
        modifications = []
        if action == "cancel":
            modifications.append("Order has been cancelled successfully")
        elif action == "change_shipping":
            if details and "address" in details:
                modifications.append(f"Shipping address updated to: {details['address']}")
            if details and "method" in details:
                modifications.append(f"Shipping method changed to: {details['method']}")
        elif action == "change_items":
            modifications.append("Item modifications processed")
        
        return {
            "success": True, 
            "modifications": modifications,
            "message": f"Order {order_id} has been successfully modified"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_order_history(customer_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get customer's order history with optional limit"""
    try:
        orders = get_customer_orders(customer_id)
        
        # Sort by order date (most recent first)
        sorted_orders = sorted(orders, key=lambda x: x["order_date"], reverse=True)
        limited_orders = sorted_orders[:limit]
        
        # Summarize order history
        total_orders = len(orders)
        total_spent = sum(order["total"] for order in orders)
        
        return {
            "success": True,
            "orders": limited_orders,
            "summary": {
                "total_orders": total_orders,
                "total_spent": total_spent,
                "showing": len(limited_orders)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def calculate_shipping_cost(items: List[Dict], shipping_method: str = "standard") -> Dict[str, Any]:
    """Calculate shipping cost for given items and method"""
    try:
        base_costs = {
            "standard": 5.99,
            "express": 12.99,
            "overnight": 24.99
        }
        
        # Free shipping over $50
        total_value = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
        
        if total_value >= 50:
            cost = 0.00
            message = "Free shipping (order over $50)"
        else:
            cost = base_costs.get(shipping_method, 5.99)
            message = f"Shipping cost for {shipping_method}"
        
        return {
            "success": True,
            "shipping_cost": cost,
            "message": message,
            "free_shipping_threshold": 50.0
        }
    except Exception as e:
        return {"success": False, "error": str(e)}