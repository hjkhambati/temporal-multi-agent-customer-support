"""Alteration Tools - Request and manage clothing alterations"""

from typing import Dict, Any, List
from data.persistent_data import (
    ALTERATION_PRICING,
    get_catalog,
    get_product,
    get_purchase,
    update_purchase,
    create_alteration_request,
    get_alteration_requests
)

def get_available_alterations() -> Dict[str, Any]:
    """Get list of available alteration types and pricing"""
    try:
        return {
            "success": True,
            "alterations": [
                {
                    "type": "hemming",
                    "description": "Adjust length of pants, skirts, or dresses",
                    "price": ALTERATION_PRICING["hemming"]
                },
                {
                    "type": "taking_in",
                    "description": "Make garment smaller (waist, sides, etc.)",
                    "price": ALTERATION_PRICING["taking_in"]
                },
                {
                    "type": "letting_out",
                    "description": "Make garment larger (if fabric allows)",
                    "price": ALTERATION_PRICING["letting_out"]
                },
                {
                    "type": "sleeve_adjustment",
                    "description": "Shorten or lengthen sleeves",
                    "price": ALTERATION_PRICING["sleeve_adjustment"]
                },
                {
                    "type": "waist_adjustment",
                    "description": "Adjust waist fit",
                    "price": ALTERATION_PRICING["waist_adjustment"]
                }
            ],
            "note": "Prices are per alteration. Multiple alterations can be combined."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_alteration_feasibility(product_id: str, alteration_types: List[str]) -> Dict[str, Any]:
    """Check if requested alterations are feasible for the product"""
    try:
        product = get_product(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        
        if not product.get("alterable", False):
            return {
                "success": True,
                "feasible": False,
                "reason": "This product cannot be altered"
            }
        
        # Check each alteration type
        valid_types = list(ALTERATION_PRICING.keys())
        invalid_types = [alt for alt in alteration_types if alt not in valid_types]
        
        if invalid_types:
            return {
                "success": False,
                "error": f"Invalid alteration types: {invalid_types}. Valid types: {valid_types}"
            }
        
        # Category-specific limitations
        category = product.get("category", "").lower()
        limitations = []
        
        if category in ["shirt", "blouse"]:
            if "hemming" in alteration_types:
                limitations.append("Hemming not typically done on shirts/blouses")
        
        if category == "pants":
            if "letting_out" in alteration_types:
                limitations.append("Letting out may be limited by available fabric")
        
        return {
            "success": True,
            "feasible": True,
            "product_name": product["name"],
            "category": category,
            "alterations_requested": alteration_types,
            "limitations": limitations if limitations else None,
            "estimated_time": "7-10 business days"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def calculate_alteration_cost(alteration_types: List[str]) -> Dict[str, Any]:
    """Calculate total cost for requested alterations"""
    try:
        valid_types = list(ALTERATION_PRICING.keys())
        invalid_types = [alt for alt in alteration_types if alt not in valid_types]
        
        if invalid_types:
            return {
                "success": False,
                "error": f"Invalid alteration types: {invalid_types}"
            }
        
        breakdown = []
        total_cost = 0
        
        for alt_type in alteration_types:
            cost = ALTERATION_PRICING[alt_type]
            breakdown.append({
                "type": alt_type,
                "cost": cost
            })
            total_cost += cost
        
        return {
            "success": True,
            "breakdown": breakdown,
            "total_cost": round(total_cost, 2),
            "currency": "USD"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def request_alteration(purchase_id: str, item_id: str, alterations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Request alterations for a purchased item"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        # Validate item exists in purchase
        items = purchase.get("items", [])
        item = None
        for i in items:
            if i.get("product_id") == item_id:
                item = i
                break
        
        if not item:
            return {"success": False, "error": f"Item {item_id} not found in purchase"}
        
        # Check feasibility
        alteration_types = [alt["type"] for alt in alterations]
        feasibility = check_alteration_feasibility(item_id, alteration_types)
        
        if not feasibility.get("success") or not feasibility.get("feasible"):
            return feasibility
        
        # Calculate cost
        cost_calc = calculate_alteration_cost(alteration_types)
        if not cost_calc.get("success"):
            return cost_calc
        
        # Create alteration request
        alteration_id = create_alteration_request(purchase_id, item_id, alterations)
        
        # Update purchase with alteration info
        current_alteration_cost = purchase.get("alteration_cost", 0)
        new_alteration_cost = current_alteration_cost + cost_calc["total_cost"]
        
        update_purchase(purchase_id, {
            "alterations_requested": True,
            "alteration_cost": new_alteration_cost
        })
        
        return {
            "success": True,
            "message": "Alteration request created successfully",
            "alteration_id": alteration_id,
            "purchase_id": purchase_id,
            "item_id": item_id,
            "alterations": alterations,
            "total_cost": cost_calc["total_cost"],
            "estimated_completion": "7-10 business days",
            "note": "Alterations will be completed before delivery"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_alteration_status(alteration_id: str) -> Dict[str, Any]:
    """Get status of an alteration request"""
    try:
        alteration_requests = get_alteration_requests()
        alteration = alteration_requests.get(alteration_id)
        if not alteration:
            return {"success": False, "error": "Alteration request not found"}
        
        return {
            "success": True,
            "alteration_id": alteration_id,
            "purchase_id": alteration["purchase_id"],
            "item_id": alteration["item_id"],
            "alterations": alteration["alterations"],
            "status": alteration["status"],
            "created_at": alteration["created_at"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def cancel_alteration(alteration_id: str) -> Dict[str, Any]:
    """Cancel an alteration request"""
    try:
        alteration_requests = get_alteration_requests()
        alteration = alteration_requests.get(alteration_id)
        if not alteration:
            return {"success": False, "error": "Alteration request not found"}
        
        current_status = alteration.get("status")
        if current_status == "completed":
            return {
                "success": False,
                "error": "Cannot cancel completed alteration"
            }
        
        if current_status == "in_progress":
            return {
                "success": False,
                "error": "Alteration already in progress. Contact support for assistance."
            }
        
        # Cancel alteration
        alteration["status"] = "cancelled"
        # Note: In persistent_data, need to use save function
        from data.persistent_data import save_alteration_request
        save_alteration_request(alteration_id, alteration)
        
        # Update purchase - remove alteration cost
        purchase_id = alteration["purchase_id"]
        purchase = get_purchase(purchase_id)
        
        if purchase:
            # Recalculate alteration cost
            alteration_types = [alt["type"] for alt in alteration["alterations"]]
            cost_calc = calculate_alteration_cost(alteration_types)
            removed_cost = cost_calc.get("total_cost", 0)
            
            current_cost = purchase.get("alteration_cost", 0)
            new_cost = max(0, current_cost - removed_cost)
            
            update_purchase(purchase_id, {"alteration_cost": new_cost})
        
        return {
            "success": True,
            "message": "Alteration request cancelled successfully",
            "alteration_id": alteration_id,
            "refunded_amount": removed_cost if purchase else 0
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
