"""
⚠️ DEPRECATED - This file is deprecated and should not be used ⚠️

All data has been migrated to persistent_data.py which provides:
- JSON file persistence in persistence_data/ directory
- Better data management and consistency
- Same API with persistent storage

Please use persistent_data.py instead:
    from data.persistent_data import (
        get_catalog, get_customer, get_orders, get_purchase,
        search_knowledge_base, get_return_policy, search_faq,
        save_measurements, create_purchase, etc.
    )

This file will be removed in a future version.
"""

import warnings
warnings.warn(
    "mock_data.py is deprecated. Use persistent_data.py instead.",
    DeprecationWarning,
    stacklevel=2
)

from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# Mock Customer Data
MOCK_CUSTOMERS = {
    "customer-456": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "tier": "Gold",
        "join_date": "2022-03-15",
        "preferences": {
            "contact_method": "email",
            "language": "english",
            "timezone": "EST"
        }
    },
    "customer-789": {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+1-555-0124",
        "tier": "Platinum",
        "join_date": "2021-01-20",
        "preferences": {
            "contact_method": "phone",
            "language": "english",
            "timezone": "PST"
        }
    }
}

# Mock Product Catalog
MOCK_PRODUCTS = {
    "PROD-001": {
        "name": "Wireless Bluetooth Headphones",
        "category": "Electronics",
        "price": 199.99,
        "specs": {
            "battery_life": "30 hours",
            "connectivity": "Bluetooth 5.0",
            "weight": "250g",
            "warranty": "2 years"
        },
        "common_issues": [
            "Connection problems",
            "Battery not charging",
            "Audio quality issues"
        ]
    },
    "PROD-002": {
        "name": "Smart Fitness Watch",
        "category": "Wearables",
        "price": 299.99,
        "specs": {
            "battery_life": "7 days",
            "display": "AMOLED",
            "water_resistance": "50m",
            "warranty": "1 year"
        },
        "common_issues": [
            "Syncing problems",
            "Heart rate inaccuracy",
            "Screen not responding"
        ]
    }
}

# Mock Order Data
MOCK_ORDERS = {
    "ORD-12345": {
        "order_id": "ORD-12345",
        "customer_id": "customer-456",
        "status": "delivered",
        "order_date": "2024-09-15",
        "items": [
            {
                "product_id": "PROD-001",
                "quantity": 1,
                "price": 199.99
            }
        ],
        "total": 199.99,
        "shipping": {
            "address": "123 Main St, Anytown, USA",
            "method": "Standard",
            "tracking": "TRK-789123"
        },
        "delivery_date": "2024-09-18"
    },
    "ORD-12346": {
        "order_id": "ORD-12346",
        "customer_id": "customer-789",
        "status": "processing",
        "order_date": "2024-09-25",
        "items": [
            {
                "product_id": "PROD-002",
                "quantity": 1,
                "price": 299.99
            }
        ],
        "total": 299.99,
        "shipping": {
            "address": "456 Oak Ave, Somewhere, USA",
            "method": "Express",
            "tracking": None
        },
        "estimated_delivery": "2024-10-01"
    }
}

# Mock Return Policy
RETURN_POLICY = {
    "return_window_days": 30,
    "refund_processing_time": "5-7 business days",
    "return_shipping_cost": 9.99,
    "conditions": [
        "Item must be in original condition",
        "Original packaging required",
        "Receipt or order number required"
    ],
    "non_returnable_items": [
        "Used electronics with signs of wear",
        "Items damaged by customer",
        "Items over return window"
    ],
    "exceptions": {
        "defective_items": "Full refund including shipping",
        "wrong_item_sent": "Full refund including return shipping"
    }
}

# Mock Knowledge Base
KNOWLEDGE_BASE = {
    "bluetooth_connection": {
        "issue": "Bluetooth connection problems",
        "solutions": [
            "Reset Bluetooth settings on device",
            "Clear Bluetooth cache",
            "Ensure devices are within 30 feet",
            "Update device drivers",
            "Restart both devices"
        ],
        "estimated_time": "10-15 minutes"
    },
    "battery_not_charging": {
        "issue": "Battery not charging",
        "solutions": [
            "Check charging cable for damage",
            "Try different power outlet",
            "Clean charging ports",
            "Reset device to factory settings",
            "Contact technical support if under warranty"
        ],
        "estimated_time": "15-30 minutes"
    },
    "refund_process": {
        "issue": "How to request refund",
        "solutions": [
            "Items must be returned within 30 days",
            "Original packaging required",
            "Use return label provided",
            "Refund processed within 5-7 business days"
        ],
        "estimated_time": "5-7 business days"
    }
}

# Mock FAQ Data
FAQ_DATA = {
    "shipping": [
        {
            "question": "How long does shipping take?",
            "answer": "Standard shipping: 3-5 business days. Express: 1-2 business days."
        },
        {
            "question": "Can I change my shipping address?",
            "answer": "Yes, if order hasn't been processed yet. Contact support immediately."
        }
    ],
    "returns": [
        {
            "question": "What is your return policy?",
            "answer": "30-day return window for items in original condition with packaging."
        },
        {
            "question": "How do I return an item?",
            "answer": "Request a return label through your account or contact customer service."
        }
    ],
    "account": [
        {
            "question": "How do I reset my password?",
            "answer": "Use the 'Forgot Password' link on the login page or contact support."
        },
        {
            "question": "How do I update my account information?",
            "answer": "Log into your account and go to 'Account Settings' to make changes."
        }
    ]
}

def get_customer_orders(customer_id: str) -> List[Dict]:
    """Get all orders for a customer"""
    return [order for order in MOCK_ORDERS.values() if order["customer_id"] == customer_id]

def get_order_by_id(order_id: str) -> Dict:
    """Get specific order details"""
    return MOCK_ORDERS.get(order_id, {})

def get_product_info(product_id: str) -> Dict:
    """Get product information"""
    return MOCK_PRODUCTS.get(product_id, {})

def search_knowledge_base(query: str) -> List[Dict]:
    """Search knowledge base for solutions"""
    results = []
    query_lower = query.lower()
    
    for key, data in KNOWLEDGE_BASE.items():
        if any(term in data["issue"].lower() for term in query_lower.split()):
            results.append(data)
    
    return results

def search_faq(query: str) -> List[Dict]:
    """Search FAQ for answers"""
    results = []
    query_lower = query.lower()
    
    for category, faqs in FAQ_DATA.items():
        for faq in faqs:
            if any(term in faq["question"].lower() or term in faq["answer"].lower() 
                   for term in query_lower.split()):
                results.append({**faq, "category": category})
    
    return results

# ============= PURCHASE FLOW DATA (MUTABLE) =============

# Mock Purchase Catalog - Clothing items
PURCHASE_CATALOG = {
    "SHIRT-M-001": {
        "product_id": "SHIRT-M-001",
        "name": "Classic Formal Shirt",
        "gender": "male",
        "category": "shirt",
        "price": 49.99,
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["White", "Blue", "Black"],
        "requires_measurements": True,
        "alterable": True
    },
    "SHIRT-M-002": {
        "product_id": "SHIRT-M-002",
        "name": "Casual Cotton Shirt",
        "gender": "male",
        "category": "shirt",
        "price": 39.99,
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["White", "Gray", "Navy", "Light Blue"],
        "requires_measurements": True,
        "alterable": True
    },
    "SHIRT-M-003": {
        "product_id": "SHIRT-M-003",
        "name": "Oxford Button-Down Shirt",
        "gender": "male",
        "category": "shirt",
        "price": 54.99,
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["White", "Pink", "Light Blue", "Striped"],
        "requires_measurements": True,
        "alterable": True
    },
    "SHIRT-M-004": {
        "product_id": "SHIRT-M-004",
        "name": "Linen Summer Shirt",
        "gender": "male",
        "category": "shirt",
        "price": 44.99,
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["White", "Beige", "Sky Blue"],
        "requires_measurements": True,
        "alterable": True
    },
    "PANTS-M-001": {
        "product_id": "PANTS-M-001",
        "name": "Slim Fit Trousers",
        "gender": "male",
        "category": "pants",
        "price": 79.99,
        "sizes": ["28", "30", "32", "34", "36", "38"],
        "colors": ["Black", "Navy", "Gray"],
        "requires_measurements": True,
        "alterable": True
    },
    "DRESS-F-001": {
        "product_id": "DRESS-F-001",
        "name": "Evening Gown",
        "gender": "female",
        "category": "dress",
        "price": 149.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Red", "Black", "Navy"],
        "requires_measurements": True,
        "alterable": True
    },
    "BLOUSE-F-001": {
        "product_id": "BLOUSE-F-001",
        "name": "Silk Blouse",
        "gender": "female",
        "category": "blouse",
        "price": 59.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["White", "Cream", "Pink"],
        "requires_measurements": True,
        "alterable": True
    },
    "BLOUSE-F-002": {
        "product_id": "BLOUSE-F-002",
        "name": "Chiffon Blouse",
        "gender": "female",
        "category": "blouse",
        "price": 54.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["White", "Black", "Burgundy", "Navy"],
        "requires_measurements": True,
        "alterable": True
    },
    "BLOUSE-F-003": {
        "product_id": "BLOUSE-F-003",
        "name": "Cotton Button-Up Shirt",
        "gender": "female",
        "category": "blouse",
        "price": 44.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["White", "Light Blue", "Striped"],
        "requires_measurements": True,
        "alterable": True
    }
}

# Mutable in-progress purchase orders (tools will modify this)
ACTIVE_PURCHASES = {}

# Mutable customer measurements (tools will modify this)
CUSTOMER_MEASUREMENTS = {}

# Mutable alteration requests (tools will modify this)
ALTERATION_REQUESTS = {}

# Mutable billing information (tools will modify this)
BILLING_INFO = {}

# Mutable delivery schedules (tools will modify this)
DELIVERY_SCHEDULES = {}

# Standard measurement requirements
MALE_MEASUREMENT_REQUIREMENTS = {
    "shirt": ["chest", "waist", "shoulder_width", "sleeve_length", "neck"],
    "pants": ["waist", "inseam", "outseam", "hip", "thigh"],
    "suit": ["chest", "waist", "shoulder_width", "sleeve_length", "neck", "inseam", "outseam"]
}

FEMALE_MEASUREMENT_REQUIREMENTS = {
    "dress": ["bust", "waist", "hip", "shoulder_width", "dress_length"],
    "blouse": ["bust", "waist", "shoulder_width", "sleeve_length"],
    "pants": ["waist", "inseam", "hip", "thigh"],
    "skirt": ["waist", "hip", "skirt_length"]
}

# Alteration pricing
ALTERATION_PRICING = {
    "hemming": 15.00,
    "taking_in": 25.00,
    "letting_out": 30.00,
    "sleeve_adjustment": 20.00,
    "waist_adjustment": 25.00
}

# Delivery options
DELIVERY_OPTIONS = {
    "standard": {
        "name": "Standard Delivery",
        "cost": 9.99,
        "days": 5
    },
    "express": {
        "name": "Express Delivery",
        "cost": 19.99,
        "days": 2
    },
    "overnight": {
        "name": "Overnight Delivery",
        "cost": 39.99,
        "days": 1
    }
}

def get_product_catalog(gender: str = None, category: str = None) -> List[Dict]:
    """Get products from catalog with optional filters"""
    products = list(PURCHASE_CATALOG.values())
    if gender:
        products = [p for p in products if p.get("gender", "").lower() == gender.lower()]
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    return products

def get_purchase_by_id(purchase_id: str) -> Dict:
    """Get active purchase by ID"""
    return ACTIVE_PURCHASES.get(purchase_id, {})

def create_purchase(customer_id: str, items: List[Dict]) -> str:
    """Create new purchase order"""
    from data.persistence import save_purchase
    
    purchase_id = f"PURCH-{uuid.uuid4().hex[:8].upper()}"
    purchase_data = {
        "purchase_id": purchase_id,
        "customer_id": customer_id,
        "items": items,
        "status": "initiated",
        "created_at": datetime.now().isoformat(),
        "measurements_complete": False,
        "billing_complete": False,
        "delivery_scheduled": False,
        "alterations_requested": False
    }
    
    # Save to in-memory dict
    ACTIVE_PURCHASES[purchase_id] = purchase_data
    
    # Persist to file
    save_purchase(purchase_id, purchase_data)
    
    return purchase_id

def update_purchase(purchase_id: str, updates: Dict) -> bool:
    """Update purchase order"""
    from data.persistence import update_purchase_in_file
    
    if purchase_id in ACTIVE_PURCHASES:
        # Update in-memory
        ACTIVE_PURCHASES[purchase_id].update(updates)
        
        # Persist to file
        update_purchase_in_file(purchase_id, updates)
        return True
    return False

def save_measurements(customer_id: str, gender: str, measurements: Dict) -> bool:
    """Save customer measurements"""
    from data.persistence import save_measurement_to_file
    
    key = f"{customer_id}_{gender}"
    measurement_data = {
        "customer_id": customer_id,
        "gender": gender,
        "measurements": measurements,
        "recorded_at": datetime.now().isoformat()
    }
    
    # Save to in-memory dict
    CUSTOMER_MEASUREMENTS[key] = measurement_data
    
    # Persist to file
    save_measurement_to_file(key, measurement_data)
    
    return True

def get_measurements(customer_id: str, gender: str) -> Dict:
    """Get customer measurements"""
    key = f"{customer_id}_{gender}"
    return CUSTOMER_MEASUREMENTS.get(key, {})

def create_alteration_request(purchase_id: str, item_id: str, alterations: List[Dict]) -> str:
    """Create alteration request"""
    from data.persistence import save_alteration_to_file
    
    alteration_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    alteration_data = {
        "alteration_id": alteration_id,
        "purchase_id": purchase_id,
        "item_id": item_id,
        "alterations": alterations,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    # Save to in-memory dict
    ALTERATION_REQUESTS[alteration_id] = alteration_data
    
    # Persist to file
    save_alteration_to_file(alteration_id, alteration_data)
    
    return alteration_id

def save_billing_info(purchase_id: str, billing_data: Dict) -> bool:
    """Save billing information"""
    from data.persistence import save_billing_to_file
    
    billing_info = {
        "purchase_id": purchase_id,
        "billing_data": billing_data,
        "processed_at": datetime.now().isoformat()
    }
    
    # Save to in-memory dict
    BILLING_INFO[purchase_id] = billing_info
    
    # Persist to file
    save_billing_to_file(purchase_id, billing_info)
    
    return True

def schedule_delivery(purchase_id: str, delivery_option: str, address: Dict) -> bool:
    """Schedule delivery"""
    from data.persistence import save_delivery_to_file
    
    delivery_date = datetime.now() + timedelta(days=DELIVERY_OPTIONS[delivery_option]["days"])
    delivery_data = {
        "purchase_id": purchase_id,
        "delivery_option": delivery_option,
        "address": address,
        "scheduled_date": delivery_date.strftime("%Y-%m-%d"),
        "tracking_number": f"TRK-{uuid.uuid4().hex[:8].upper()}",
        "status": "scheduled"
    }
    
    # Save to in-memory dict
    DELIVERY_SCHEDULES[purchase_id] = delivery_data
    
    # Persist to file
    save_delivery_to_file(purchase_id, delivery_data)
    
    return True