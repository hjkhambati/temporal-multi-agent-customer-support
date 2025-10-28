"""Refund and return tools for the Refund Specialist agent"""

import dspy
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from data.persistent_data import RETURN_POLICY, get_order_by_id

def check_refund_eligibility(order_id: str, reason: str) -> Dict[str, Any]:
    """Check if an order is eligible for refund based on policy"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Calculate days since order
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
        days_since_order = (datetime.now() - order_date).days
        
        eligibility = {
            "order_id": order_id,
            "within_return_window": days_since_order <= RETURN_POLICY["return_window_days"],
            "days_since_order": days_since_order,
            "return_window_days": RETURN_POLICY["return_window_days"],
            "reason": reason
        }
        
        # Check specific conditions
        reason_lower = reason.lower()
        
        if "defective" in reason_lower or "wrong item" in reason_lower:
            eligibility["eligible"] = True
            eligibility["exception_type"] = "defective_or_wrong_item"
            eligibility["refund_shipping"] = True
        elif days_since_order > RETURN_POLICY["return_window_days"]:
            eligibility["eligible"] = False
            eligibility["reason_declined"] = "Outside return window"
        elif order["status"] == "delivered":
            eligibility["eligible"] = True
            eligibility["refund_shipping"] = False
        else:
            eligibility["eligible"] = True
            eligibility["refund_shipping"] = False
        
        return {"success": True, "eligibility": eligibility}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def calculate_refund_amount(order_id: str, refund_type: str = "full") -> Dict[str, Any]:
    """Calculate refund amount based on order and refund type"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        original_total = order["total"]
        
        # Calculate refund components
        if refund_type == "full":
            refund_amount = original_total
            deductions = []
        elif refund_type == "partial":
            # Example: partial refund with restocking fee
            restocking_fee = original_total * 0.15  # 15% restocking fee
            refund_amount = original_total - restocking_fee
            deductions = [{"type": "restocking_fee", "amount": restocking_fee}]
        else:
            return {"success": False, "error": "Invalid refund type"}
        
        # Check if shipping should be refunded
        shipping_cost = 0  # Assume included in total for this example
        
        refund_breakdown = {
            "order_id": order_id,
            "original_total": original_total,
            "refund_amount": round(refund_amount, 2),
            "refund_type": refund_type,
            "deductions": deductions,
            "processing_time": RETURN_POLICY["refund_processing_time"]
        }
        
        return {"success": True, "refund_breakdown": refund_breakdown}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def initiate_refund(order_id: str, refund_amount: float, reason: str) -> Dict[str, Any]:
    """Initiate the refund process"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Generate refund ID
        refund_id = f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        refund_request = {
            "refund_id": refund_id,
            "order_id": order_id,
            "customer_id": order["customer_id"],
            "refund_amount": refund_amount,
            "reason": reason,
            "status": "processing",
            "initiated_date": datetime.now().isoformat(),
            "expected_completion": (datetime.now() + timedelta(days=7)).isoformat(),
            "payment_method": "Original payment method"
        }
        
        return {
            "success": True,
            "refund_request": refund_request,
            "message": f"Refund {refund_id} initiated successfully. Processing time: {RETURN_POLICY['refund_processing_time']}"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_return_label(order_id: str, return_reason: str) -> Dict[str, Any]:
    """Generate a return shipping label"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # Generate return label ID
        label_id = f"LBL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return_label = {
            "label_id": label_id,
            "order_id": order_id,
            "return_address": {
                "name": "Customer Returns",
                "address": "123 Return Center Way",
                "city": "Returns City",
                "state": "RC",
                "zip": "12345"
            },
            "from_address": order["shipping"]["address"],
            "tracking_number": f"RT-{label_id}",
            "shipping_cost": RETURN_POLICY["return_shipping_cost"],
            "estimated_delivery": "3-5 business days",
            "expires": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        return {
            "success": True,
            "return_label": return_label,
            "message": "Return label generated successfully. Please package items securely and drop off at any authorized location."
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_return_status(return_id: str) -> Dict[str, Any]:
    """Check the status of a return"""
    try:
        # Mock return status (in real implementation, this would query the returns database)
        return_status = {
            "return_id": return_id,
            "status": "in_transit",
            "tracking_number": f"RT-{return_id}",
            "shipped_date": "2024-09-27",
            "expected_delivery": "2024-10-02",
            "updates": [
                {"date": "2024-09-27", "status": "Package picked up"},
                {"date": "2024-09-28", "status": "In transit to return center"},
                {"date": "2024-09-29", "status": "Package scanned at sorting facility"}
            ]
        }
        
        return {"success": True, "return_status": return_status}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_return_policy_details(category: str = "general") -> Dict[str, Any]:
    """Get specific return policy information"""
    try:
        policy_details = {
            "general": RETURN_POLICY,
            "electronics": {
                **RETURN_POLICY,
                "special_conditions": [
                    "Must include all original accessories",
                    "Cannot have signs of liquid damage",
                    "Software must be uninstalled/reset"
                ]
            },
            "clothing": {
                **RETURN_POLICY,
                "special_conditions": [
                    "Tags must be attached",
                    "No signs of wear or washing",
                    "Must be in original packaging"
                ]
            }
        }
        
        return {
            "success": True,
            "policy": policy_details.get(category, RETURN_POLICY),
            "category": category
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}