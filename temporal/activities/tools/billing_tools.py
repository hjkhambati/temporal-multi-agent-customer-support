"""Billing Tools - Price calculation, discounts, and payment processing"""

from typing import Dict, Any, List
from data.persistent_data import (
    ALTERATION_PRICING,
    get_purchase,
    update_purchase,
    save_billing_info,
    get_customer,
    create_purchase,
    get_catalog,
    get_product
)

def calculate_purchase_total(purchase_id: str) -> Dict[str, Any]:
    """Calculate total cost for a purchase including items and alterations"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        items_total = 0
        item_breakdown = []
        
        for item in purchase.get("items", []):
            price = item.get("price", 0)
            quantity = item.get("quantity", 1)
            item_total = price * quantity
            items_total += item_total
            
            item_breakdown.append({
                "product": item.get("product_name", "Unknown"),
                "price": price,
                "quantity": quantity,
                "subtotal": item_total
            })
        
        # Add alteration costs if any
        alteration_cost = 0
        if purchase.get("alterations_requested"):
            # This would be calculated from alteration requests
            alteration_cost = purchase.get("alteration_cost", 0)
        
        subtotal = items_total + alteration_cost
        tax_rate = 0.08  # 8% tax
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)
        
        return {
            "success": True,
            "purchase_id": purchase_id,
            "item_breakdown": item_breakdown,
            "items_total": round(items_total, 2),
            "alteration_cost": round(alteration_cost, 2),
            "subtotal": round(subtotal, 2),
            "tax": tax,
            "tax_rate": f"{tax_rate * 100}%",
            "total": total
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_discount(purchase_id: str, discount_code: str) -> Dict[str, Any]:
    """Apply discount code to purchase"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        # Mock discount codes
        discount_codes = {
            "FIRST10": {"type": "percentage", "value": 10, "description": "10% off first purchase"},
            "SAVE20": {"type": "percentage", "value": 20, "description": "20% off"},
            "FLAT50": {"type": "fixed", "value": 50, "description": "$50 off"},
            "VIP25": {"type": "percentage", "value": 25, "description": "25% VIP discount"}
        }
        
        discount = discount_codes.get(discount_code.upper())
        if not discount:
            return {
                "success": False,
                "error": f"Invalid discount code: {discount_code}"
            }
        
        # Calculate current total
        total_calc = calculate_purchase_total(purchase_id)
        if not total_calc.get("success"):
            return total_calc
        
        subtotal = total_calc["subtotal"]
        
        # Apply discount
        if discount["type"] == "percentage":
            discount_amount = round(subtotal * (discount["value"] / 100), 2)
        else:  # fixed
            discount_amount = discount["value"]
        
        # Recalculate total
        new_subtotal = subtotal - discount_amount
        tax_rate = 0.08
        new_tax = round(new_subtotal * tax_rate, 2)
        new_total = round(new_subtotal + new_tax, 2)
        
        # Update purchase
        update_purchase(purchase_id, {
            "discount_code": discount_code.upper(),
            "discount_amount": discount_amount,
            "discount_description": discount["description"]
        })
        
        return {
            "success": True,
            "discount_applied": True,
            "discount_code": discount_code.upper(),
            "discount_description": discount["description"],
            "discount_amount": discount_amount,
            "original_total": total_calc["total"],
            "new_total": new_total,
            "savings": round(total_calc["total"] - new_total, 2)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_customer_tier_discount(customer_id: str) -> Dict[str, Any]:
    """Get discount based on customer tier"""
    try:
        customer = get_customer(customer_id)
        if not customer:
            return {"success": False, "error": "Customer not found"}
        
        tier = customer.get("tier", "Standard")
        
        tier_discounts = {
            "Standard": 0,
            "Silver": 5,
            "Gold": 10,
            "Platinum": 15
        }
        
        discount_percentage = tier_discounts.get(tier, 0)
        
        return {
            "success": True,
            "customer_tier": tier,
            "discount_percentage": discount_percentage,
            "eligible": discount_percentage > 0
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_payment(purchase_id: str, payment_method: str, payment_details: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment for purchase"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        # Calculate final total
        total_calc = calculate_purchase_total(purchase_id)
        if not total_calc.get("success"):
            return total_calc
        
        total_amount = total_calc["total"]
        
        # Apply discount if exists
        if purchase.get("discount_amount"):
            total_amount -= purchase["discount_amount"]
            total_amount = round(total_amount + (total_amount * 0.08), 2)  # Recalc tax
        
        # Mock payment processing
        supported_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        if payment_method not in supported_methods:
            return {
                "success": False,
                "error": f"Unsupported payment method. Supported: {supported_methods}"
            }
        
        # Simulate payment success
        transaction_id = f"TXN-{purchase_id[-8:]}"
        
        billing_data = {
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "amount_charged": total_amount,
            "currency": "USD",
            "status": "completed",
            "payment_details": payment_details
        }
        
        # Save billing info
        save_billing_info(purchase_id, billing_data)
        
        # Update purchase status
        update_purchase(purchase_id, {
            "billing_complete": True,
            "payment_status": "paid",
            "transaction_id": transaction_id
        })
        
        return {
            "success": True,
            "payment_processed": True,
            "transaction_id": transaction_id,
            "amount_charged": total_amount,
            "payment_method": payment_method,
            "message": "Payment processed successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_invoice(purchase_id: str) -> Dict[str, Any]:
    """Generate invoice for purchase"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        total_calc = calculate_purchase_total(purchase_id)
        if not total_calc.get("success"):
            return total_calc
        
        customer_id = purchase.get("customer_id")
        customer = get_customer(customer_id) or {}
        
        invoice = {
            "invoice_id": f"INV-{purchase_id[-8:]}",
            "purchase_id": purchase_id,
            "customer_name": customer.get("name", "Unknown"),
            "customer_email": customer.get("email", ""),
            "items": total_calc["item_breakdown"],
            "subtotal": total_calc["subtotal"],
            "tax": total_calc["tax"],
            "discount": purchase.get("discount_amount", 0),
            "total": total_calc["total"],
            "payment_status": purchase.get("payment_status", "pending"),
            "transaction_id": purchase.get("transaction_id", "N/A")
        }
        
        return {
            "success": True,
            "invoice": invoice,
            "invoice_id": invoice["invoice_id"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_payment_status(purchase_id: str) -> Dict[str, Any]:
    """Check payment status for purchase"""
    try:
        purchase = get_purchase(purchase_id)
        if not purchase:
            return {"success": False, "error": "Purchase not found"}
        
        payment_status = purchase.get("payment_status", "pending")
        billing_complete = purchase.get("billing_complete", False)
        
        return {
            "success": True,
            "purchase_id": purchase_id,
            "payment_status": payment_status,
            "billing_complete": billing_complete,
            "transaction_id": purchase.get("transaction_id", "N/A"),
            "paid": payment_status == "paid"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_bill_from_conversation(customer_id: str, product_name: str, size: str, color: str, price: float) -> Dict[str, Any]:
    """
    Create a new bill from purchase details extracted from conversation.
    Use this when specialist has collected product details but hasn't created a purchase order yet.
    
    Args:
        customer_id: Customer ID
        product_name: Product name (e.g., "Casual Cotton Shirt")
        size: Size selected (e.g., "L")
        color: Color selected (e.g., "Gray")
        price: Base price of the item
        
    Returns:
        Dict with purchase_id, total, invoice details
    """
    try:
        # Find product_id from catalog by name
        catalog = get_catalog()
        product_id = None
        for pid, product in catalog.items():
            if product["name"].lower() == product_name.lower():
                product_id = pid
                break
        
        if not product_id:
            return {
                "success": False,
                "error": f"Product '{product_name}' not found in catalog. Available products: {', '.join([p['name'] for p in catalog.values()])}"
            }
        
        # Create purchase order (already imported at top)
        import uuid
        
        items = [{
            "product_id": product_id,
            "product_name": product_name,
            "size": size,
            "color": color,
            "price": price,
            "quantity": 1
        }]
        
        purchase_id = create_purchase(customer_id, items)
        
        # Calculate total with tax
        subtotal = price
        tax_rate = 0.08
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)
        
        # Check for customer tier discount
        customer = get_customer(customer_id) or {}
        tier = customer.get("tier", "")
        discount_amount = 0
        
        if tier == "Gold":
            discount_amount = round(subtotal * 0.10, 2)  # 10% off
        elif tier == "Platinum":
            discount_amount = round(subtotal * 0.15, 2)  # 15% off
        
        if discount_amount > 0:
            subtotal -= discount_amount
            tax = round(subtotal * tax_rate, 2)
            total = round(subtotal + tax, 2)
            update_purchase(purchase_id, {
                "discount_amount": discount_amount,
                "discount_description": f"{tier} member discount"
            })
        
        # Update purchase with billing info
        update_purchase(purchase_id, {
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "measurements_complete": True
        })
        
        return {
            "success": True,
            "purchase_id": purchase_id,
            "product_name": product_name,
            "size": size,
            "color": color,
            "base_price": price,
            "discount": discount_amount,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "message": f"Bill created for {product_name} ({size}, {color}) - Total: ${total}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
