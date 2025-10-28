"""Technical support tools for the Technical Specialist agent"""

import dspy
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from data.persistent_data import get_product_info, search_knowledge_base, get_product

def search_knowledge_base_tool(issue_description: str) -> Dict[str, Any]:
    """Search technical knowledge base for solutions"""
    try:
        results = search_knowledge_base(issue_description)
        
        if not results:
            return {
                "success": False, 
                "message": "No solutions found for this specific issue"
            }
        
        return {
            "success": True,
            "solutions": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_product_specs(product_id: str) -> Dict[str, Any]:
    """Get technical specifications for a product"""
    try:
        product = get_product_info(product_id)
        
        if not product:
            return {"success": False, "error": "Product not found"}
        
        return {
            "success": True,
            "product": {
                "name": product["name"],
                "category": product["category"],
                "specs": product["specs"],
                "common_issues": product.get("common_issues", [])
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_warranty(product_id: str, purchase_date: str) -> Dict[str, Any]:
    """Check warranty status for a product"""
    try:
        product = get_product_info(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        
        # Parse warranty period
        warranty_spec = product["specs"].get("warranty", "1 year")
        warranty_years = int(warranty_spec.split()[0]) if "year" in warranty_spec else 1
        
        # Calculate warranty expiry
        purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d")
        warranty_expiry = purchase_dt + timedelta(days=warranty_years * 365)
        days_remaining = (warranty_expiry - datetime.now()).days
        
        is_under_warranty = days_remaining > 0
        
        return {
            "success": True,
            "warranty_info": {
                "product_name": product["name"],
                "warranty_period": warranty_spec,
                "purchase_date": purchase_date,
                "warranty_expiry": warranty_expiry.strftime("%Y-%m-%d"),
                "is_under_warranty": is_under_warranty,
                "days_remaining": max(0, days_remaining)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_escalation_ticket(issue_details: Dict[str, Any]) -> Dict[str, Any]:
    """Create a technical escalation ticket for complex issues"""
    try:
        ticket_id = f"TECH-ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        escalation_ticket = {
            "ticket_id": ticket_id,
            "type": "technical_escalation",
            "priority": issue_details.get("priority", "medium"),
            "issue_summary": issue_details.get("summary", "Complex technical issue"),
            "product_id": issue_details.get("product_id"),
            "customer_id": issue_details.get("customer_id"),
            "attempted_solutions": issue_details.get("attempted_solutions", []),
            "created_at": datetime.now().isoformat(),
            "status": "open"
        }
        
        return {
            "success": True,
            "escalation_ticket": escalation_ticket,
            "message": f"Technical escalation ticket {ticket_id} created successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_diagnostics(product_id: str, issue_type: str) -> Dict[str, Any]:
    """Run diagnostic steps for common issues"""
    try:
        product = get_product_info(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        
        # Define diagnostic steps for different issue types
        diagnostic_steps = {
            "connectivity": [
                "Check power connection",
                "Verify network settings",
                "Test with different device",
                "Reset network settings",
                "Update drivers/firmware"
            ],
            "performance": [
                "Check available storage space",
                "Close unnecessary applications",
                "Restart device",
                "Check for software updates",
                "Review system requirements"
            ],
            "hardware": [
                "Inspect for physical damage",
                "Check all connections",
                "Test with minimal setup",
                "Verify power supply",
                "Contact technical support if under warranty"
            ]
        }
        
        steps = diagnostic_steps.get(issue_type, diagnostic_steps["hardware"])
        
        return {
            "success": True,
            "diagnostic_steps": steps,
            "product_name": product["name"],
            "issue_type": issue_type,
            "estimated_time": "15-30 minutes"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_firmware_updates(product_id: str) -> Dict[str, Any]:
    """Check for available firmware updates"""
    try:
        product = get_product_info(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        
        # Mock firmware update check
        updates_available = True  # In real implementation, this would check actual update servers
        
        if updates_available:
            return {
                "success": True,
                "updates_available": True,
                "current_version": "v1.2.3",
                "latest_version": "v1.3.0",
                "update_notes": [
                    "Improved connectivity stability",
                    "Bug fixes for battery optimization",
                    "Enhanced audio quality"
                ],
                "download_size": "15.2 MB",
                "estimated_update_time": "10-15 minutes"
            }
        else:
            return {
                "success": True,
                "updates_available": False,
                "current_version": "v1.3.0",
                "message": "Device is running the latest firmware version"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}