"""Delivery Tools - Address validation, scheduling, and tracking"""

from typing import Dict, Any
from datetime import datetime, timedelta
from data.persistent_data import (
    DELIVERY_OPTIONS,
    get_purchase,
    update_purchase,
    schedule_delivery,
    get_delivery_schedules
)

def get_delivery_options() -> Dict[str, Any]:
    """Get available delivery options with costs and timelines"""
    try:
        return {
            "success": True,
            "delivery_options": DELIVERY_OPTIONS
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_delivery_address(address: Dict[str, str]) -> Dict[str, Any]:
    """Validate delivery address"""
    try:
        required_fields = ["street", "city", "state", "zip_code", "country"]
        missing_fields = [field for field in required_fields if field not in address or not address[field]]
        
        if missing_fields:
            return {
                "success": False,
                "valid": False,
                "error": f"Missing required fields: {missing_fields}"
            }
        
        # Basic validation
        zip_code = address["zip_code"]
        if not (len(zip_code) == 5 and zip_code.isdigit()):
            return {
                "success": True,
                "valid": False,
                "issue": "Invalid ZIP code format (must be 5 digits)"
            }
        
        # Mock: Check if address is in serviceable area
        serviceable_states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
        state = address["state"].upper()
        
        if state not in serviceable_states:
            return {
                "success": True,
                "valid": False,
                "issue": f"Delivery not available in {state}. Serviceable states: {serviceable_states}"
            }
        
        return {
            "success": True,
            "valid": True,
            "message": "Address validated successfully",
            "formatted_address": f"{address['street']}, {address['city']}, {address['state']} {address['zip_code']}, {address['country']}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def calculate_delivery_date(delivery_option: str) -> Dict[str, Any]:
    """Calculate expected delivery date based on option"""
    try:
        if delivery_option not in DELIVERY_OPTIONS:
            return {
                "success": False,
                "error": f"Invalid delivery option. Available: {list(DELIVERY_OPTIONS.keys())}"
            }
        
        option = DELIVERY_OPTIONS[delivery_option]
        delivery_date = datetime.now() + timedelta(days=option["days"])
        
        # Skip weekends
        while delivery_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            delivery_date += timedelta(days=1)
        
        return {
            "success": True,
            "delivery_option": delivery_option,
            "delivery_name": option["name"],
            "delivery_cost": option["cost"],
            "business_days": option["days"],
            "estimated_delivery_date": delivery_date.strftime("%Y-%m-%d"),
            "day_of_week": delivery_date.strftime("%A")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def schedule_purchase_delivery(purchase_id: str, delivery_option: str, address: Dict[str, str]) -> Dict[str, Any]:
    """Schedule delivery for a purchase"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        # Validate address
        validation = validate_delivery_address(address)
        if not validation.get("success") or not validation.get("valid"):
            return validation
        
        # Check if billing is complete
        if not purchase.get("billing_complete"):
            return {
                "success": False,
                "error": "Cannot schedule delivery. Billing must be completed first."
            }
        
        # Schedule delivery
        success = schedule_delivery(purchase_id, delivery_option, address)
        
        if not success:
            return {"success": False, "error": "Failed to schedule delivery"}
        
        # Get scheduled info
        delivery_schedules = get_delivery_schedules()
        delivery_info = delivery_schedules.get(purchase_id, {})
        
        # Update purchase
        update_purchase(purchase_id, {
            "delivery_scheduled": True,
            "delivery_option": delivery_option,
            "delivery_address": validation["formatted_address"]
        })
        
        return {
            "success": True,
            "message": "Delivery scheduled successfully",
            "purchase_id": purchase_id,
            "delivery_date": delivery_info.get("scheduled_date"),
            "tracking_number": delivery_info.get("tracking_number"),
            "delivery_address": validation["formatted_address"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def track_delivery(purchase_id: str = None, tracking_number: str = None) -> Dict[str, Any]:
    """Track delivery status"""
    try:
        delivery_schedules = get_delivery_schedules()
        if purchase_id:
            delivery_info = delivery_schedules.get(purchase_id)
        elif tracking_number:
            # Find by tracking number
            delivery_info = None
            for pid, info in delivery_schedules.items():
                if info.get("tracking_number") == tracking_number:
                    delivery_info = info
                    purchase_id = pid
                    break
        else:
            return {"success": False, "error": "Must provide either purchase_id or tracking_number"}
        
        if not delivery_info:
            return {
                "success": False,
                "error": "No delivery information found"
            }
        
        # Mock tracking status
        scheduled_date = datetime.strptime(delivery_info["scheduled_date"], "%Y-%m-%d")
        today = datetime.now()
        days_until_delivery = (scheduled_date - today).days
        
        if days_until_delivery > 2:
            status = "preparing"
            status_message = "Your order is being prepared for shipment"
        elif days_until_delivery > 0:
            status = "in_transit"
            status_message = "Your order is in transit"
        elif days_until_delivery == 0:
            status = "out_for_delivery"
            status_message = "Your order is out for delivery today"
        else:
            status = "delivered"
            status_message = "Your order has been delivered"
        
        return {
            "success": True,
            "purchase_id": purchase_id,
            "tracking_number": delivery_info.get("tracking_number"),
            "status": status,
            "status_message": status_message,
            "scheduled_delivery_date": delivery_info["scheduled_date"],
            "delivery_option": delivery_info.get("delivery_option"),
            "delivery_address": delivery_info.get("address")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_delivery_address(purchase_id: str, new_address: Dict[str, str]) -> Dict[str, Any]:
    """Update delivery address before shipment"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        delivery_schedules = get_delivery_schedules()
        delivery_info = delivery_schedules.get(purchase_id)
        if not delivery_info:
            return {"success": False, "error": "No delivery scheduled yet"}
        
        # Check if already shipped
        if delivery_info.get("status") in ["in_transit", "delivered"]:
            return {
                "success": False,
                "error": "Cannot update address. Order already shipped."
            }
        
        # Validate new address
        validation = validate_delivery_address(new_address)
        if not validation.get("success") or not validation.get("valid"):
            return validation
        
        # Update address
        delivery_info["address"] = new_address
        # Save back to file
        from data.persistent_data import save_delivery_schedule
        save_delivery_schedule(purchase_id, delivery_info)
        
        return {
            "success": True,
            "message": "Delivery address updated successfully",
            "new_address": validation["formatted_address"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_delivery_status(purchase_id: str) -> Dict[str, Any]:
    """Get delivery status for a purchase"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        delivery_scheduled = purchase.get("delivery_scheduled", False)
        
        if not delivery_scheduled:
            return {
                "success": True,
                "delivery_scheduled": False,
                "message": "Delivery not yet scheduled"
            }
        
        delivery_schedules = get_delivery_schedules()
        delivery_info = delivery_schedules.get(purchase_id, {})
        
        return {
            "success": True,
            "delivery_scheduled": True,
            "scheduled_date": delivery_info.get("scheduled_date"),
            "tracking_number": delivery_info.get("tracking_number"),
            "status": delivery_info.get("status", "scheduled")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
