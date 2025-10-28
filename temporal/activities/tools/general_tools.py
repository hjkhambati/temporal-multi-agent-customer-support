"""General support tools for the General Support Specialist agent"""

import dspy
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from data.persistent_data import search_faq, get_customer, get_customers

def search_faq_tool(query: str) -> Dict[str, Any]:
    """Search FAQ database for common questions and answers"""
    try:
        results = search_faq(query)
        
        if not results:
            return {
                "success": False,
                "message": "No FAQ entries found for this query"
            }
        
        return {
            "success": True,
            "faq_results": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_account_info(customer_id: str) -> Dict[str, Any]:
    """Retrieve customer account information"""
    try:
        customer = get_customer(customer_id)
        
        if not customer:
            return {"success": False, "error": "Customer not found"}
        
        # Filter sensitive information for customer service
        account_info = {
            "customer_id": customer_id,
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer.get("phone", "Not provided"),
            "tier": customer.get("tier", "Standard"),
            "join_date": customer.get("join_date"),
            "preferences": customer.get("preferences", {}),
            "last_login": "2024-09-28"  # Mock data
        }
        
        return {"success": True, "account_info": account_info}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_customer_preferences(customer_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Update customer preferences and settings"""
    try:
        customer = get_customer(customer_id)
        
        if not customer:
            return {"success": False, "error": "Customer not found"}
        
        # Mock preference update (in real implementation, this would update the database)
        updated_preferences = {**customer.get("preferences", {}), **preferences}
        
        allowed_preferences = [
            "contact_method", "language", "timezone", "marketing_emails", 
            "notification_frequency", "preferred_support_channel"
        ]
        
        # Filter to only allowed preferences
        filtered_preferences = {
            k: v for k, v in updated_preferences.items() 
            if k in allowed_preferences
        }
        
        return {
            "success": True,
            "updated_preferences": filtered_preferences,
            "message": "Customer preferences updated successfully"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def schedule_callback(customer_id: str, callback_time: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
    """Schedule a callback with a human agent"""
    try:
        customer = get_customer(customer_id)
        
        if not customer:
            return {"success": False, "error": "Customer not found"}
        
        # Use provided phone or customer's default
        contact_phone = phone_number or customer.get("phone")
        
        if not contact_phone:
            return {"success": False, "error": "No phone number available for callback"}
        
        # Generate callback ID
        callback_id = f"CB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Parse callback time (assume format: "YYYY-MM-DD HH:MM")
        try:
            callback_datetime = datetime.strptime(callback_time, "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "error": "Invalid callback time format. Use YYYY-MM-DD HH:MM"}
        
        # Check if callback time is in business hours and future
        if callback_datetime <= datetime.now():
            return {"success": False, "error": "Callback time must be in the future"}
        
        callback_request = {
            "callback_id": callback_id,
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "phone_number": contact_phone,
            "requested_time": callback_time,
            "status": "scheduled",
            "priority": customer.get("tier", "Standard"),
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "callback_request": callback_request,
            "message": f"Callback scheduled for {callback_time}. Reference ID: {callback_id}"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_support_ticket(customer_id: str, issue_summary: str, category: str = "general") -> Dict[str, Any]:
    """Create a general support ticket"""
    try:
        customer = get_customer(customer_id)
        
        if not customer:
            return {"success": False, "error": "Customer not found"}
        
        # Generate ticket ID
        ticket_id = f"SUP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        support_ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "issue_summary": issue_summary,
            "category": category,
            "priority": "normal",
            "status": "open",
            "assigned_to": None,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "support_ticket": support_ticket,
            "message": f"Support ticket {ticket_id} created successfully"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_business_hours() -> Dict[str, Any]:
    """Get current business hours and availability"""
    try:
        business_hours = {
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S EST"),
            "is_business_hours": True,  # Mock - would check actual time
            "hours": {
                "monday_friday": "9:00 AM - 8:00 PM EST",
                "saturday": "10:00 AM - 6:00 PM EST",
                "sunday": "12:00 PM - 5:00 PM EST"
            },
            "support_channels": {
                "chat": "Available 24/7",
                "phone": "Business hours only",
                "email": "24-48 hour response time"
            },
            "next_available_callback": "2024-09-30 09:00:00"
        }
        
        return {"success": True, "business_hours": business_hours}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_service_status() -> Dict[str, Any]:
    """Check current service status and any outages"""
    try:
        service_status = {
            "overall_status": "operational",
            "services": {
                "website": {"status": "operational", "uptime": "99.9%"},
                "ordering": {"status": "operational", "uptime": "99.8%"},
                "customer_portal": {"status": "operational", "uptime": "99.7%"},
                "mobile_app": {"status": "operational", "uptime": "99.9%"}
            },
            "recent_incidents": [],
            "maintenance_windows": [
                {
                    "service": "customer_portal",
                    "scheduled": "2024-10-05 02:00 AM EST",
                    "duration": "2 hours",
                    "impact": "Limited functionality"
                }
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return {"success": True, "service_status": service_status}
    
    except Exception as e:
        return {"success": False, "error": str(e)}