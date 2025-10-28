"""
Centralized mock data with JSON persistence
All data stored in persistence_data/ directory
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid

# Data directory
DATA_DIR = Path(__file__).parent / "persistence_data"
DATA_DIR.mkdir(exist_ok=True)

# JSON file paths
CATALOG_FILE = DATA_DIR / "catalog.json"
CUSTOMERS_FILE = DATA_DIR / "customers.json"
ORDERS_FILE = DATA_DIR / "orders.json"
PURCHASES_FILE = DATA_DIR / "purchases.json"
MEASUREMENTS_FILE = DATA_DIR / "measurements.json"
ALTERATIONS_FILE = DATA_DIR / "alterations.json"
BILLING_FILE = DATA_DIR / "billing.json"
DELIVERY_FILE = DATA_DIR / "delivery.json"
KNOWLEDGE_BASE_FILE = DATA_DIR / "knowledge_base.json"
RETURN_POLICY_FILE = DATA_DIR / "return_policy.json"
FAQ_FILE = DATA_DIR / "faq.json"

# ============= FILE OPERATIONS =============

def _load_json(file_path: Path, default: Any = None) -> Any:
    """Load JSON file or return default"""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default if default is not None else {}
    return default if default is not None else {}

def _save_json(file_path: Path, data: Any) -> bool:
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")
        return False

# ============= MEASUREMENT REQUIREMENTS =============

MALE_MEASUREMENT_REQUIREMENTS = {
    "shirt": ["chest", "waist", "shoulder_width", "sleeve_length", "neck"],
    "pants": ["waist", "inseam", "outseam", "hip", "thigh"],
    "suit": ["chest", "waist", "shoulder_width", "sleeve_length", "neck", "inseam", "outseam"]
}

FEMALE_MEASUREMENT_REQUIREMENTS = {
    "dress": ["bust", "waist", "hip", "shoulder_width", "dress_length"],
    "blouse": ["bust", "waist", "shoulder_width", "sleeve_length"],
    "shirt": ["bust", "waist", "shoulder_width", "sleeve_length"],  # Added for consistency
    "pants": ["waist", "inseam", "hip", "thigh"],
    "skirt": ["waist", "hip", "skirt_length"]
}

# ============= ALTERATION PRICING =============

ALTERATION_PRICING = {
    "hemming": 15.00,
    "taking_in": 25.00,
    "letting_out": 30.00,
    "sleeve_adjustment": 20.00,
    "waist_adjustment": 25.00,
    "shoulder_adjustment": 35.00,
    "length_adjustment": 20.00,
    "custom_alteration": 50.00
}

# ============= DELIVERY OPTIONS =============

DELIVERY_OPTIONS = {
    "standard": {
        "name": "Standard Shipping",
        "cost": 0,
        "days": 7,
        "description": "5-7 business days"
    },
    "express": {
        "name": "Express Shipping",
        "cost": 15.00,
        "days": 3,
        "description": "2-3 business days"
    },
    "overnight": {
        "name": "Overnight Shipping",
        "cost": 35.00,
        "days": 1,
        "description": "Next business day"
    }
}

# ============= INITIALIZE DEFAULT DATA =============

DEFAULT_CATALOG = {
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

DEFAULT_CUSTOMERS = {
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

DEFAULT_ORDERS = {
    "ORD-12345": {
        "order_id": "ORD-12345",
        "customer_id": "customer-456",
        "status": "delivered",
        "order_date": "2024-09-15",
        "items": [{"product_id": "SHIRT-M-001", "quantity": 1, "price": 49.99}],
        "total": 49.99,
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
        "items": [{"product_id": "BLOUSE-F-001", "quantity": 1, "price": 59.99}],
        "total": 59.99,
        "shipping": {
            "address": "456 Oak Ave, Somewhere, USA",
            "method": "Express",
            "tracking": None
        },
        "estimated_delivery": "2024-10-01"
    }
}

DEFAULT_KNOWLEDGE_BASE = {
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

DEFAULT_RETURN_POLICY = {
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

DEFAULT_FAQ = {
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

def initialize_data_files():
    """Initialize all JSON files with default data if they don't exist"""
    files_to_init = [
        (CATALOG_FILE, DEFAULT_CATALOG),
        (CUSTOMERS_FILE, DEFAULT_CUSTOMERS),
        (ORDERS_FILE, DEFAULT_ORDERS),
        (PURCHASES_FILE, {}),
        (MEASUREMENTS_FILE, {}),
        (ALTERATIONS_FILE, {}),
        (BILLING_FILE, {}),
        (DELIVERY_FILE, {}),
        (KNOWLEDGE_BASE_FILE, DEFAULT_KNOWLEDGE_BASE),
        (RETURN_POLICY_FILE, DEFAULT_RETURN_POLICY),
        (FAQ_FILE, DEFAULT_FAQ)
    ]
    
    for file_path, default_data in files_to_init:
        if not file_path.exists():
            _save_json(file_path, default_data)
    
    print(f"✅ Data files initialized in: {DATA_DIR}")

# ============= CATALOG OPERATIONS =============

def get_catalog() -> Dict[str, Any]:
    """Get full product catalog"""
    return _load_json(CATALOG_FILE, {})

def get_product(product_id: str) -> Dict[str, Any]:
    """Get specific product"""
    catalog = get_catalog()
    return catalog.get(product_id, {})

def search_products(gender: str = None, category: str = None) -> List[Dict[str, Any]]:
    """Search products by gender and/or category"""
    catalog = get_catalog()
    products = list(catalog.values())
    
    if gender:
        products = [p for p in products if p.get("gender", "").lower() == gender.lower()]
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    
    return products

# ============= CUSTOMER OPERATIONS =============

def get_customers() -> Dict[str, Any]:
    """Get all customers"""
    return _load_json(CUSTOMERS_FILE, {})

def get_customer(customer_id: str) -> Dict[str, Any]:
    """Get specific customer"""
    customers = get_customers()
    return customers.get(customer_id, {})

# ============= PURCHASE OPERATIONS =============

def get_purchases() -> Dict[str, Any]:
    """Get all purchases"""
    return _load_json(PURCHASES_FILE, {})

def get_purchase(purchase_id: str) -> Dict[str, Any]:
    """Get specific purchase"""
    purchases = get_purchases()
    return purchases.get(purchase_id, {})

def create_purchase(customer_id: str, items: List[Dict], **kwargs) -> str:
    """
    Create new purchase order (called by BILLING agent only)
    
    Args:
        customer_id: Customer ID
        items: List of items with product_id, product_name, size, color, price, measurements
        **kwargs: Additional fields (subtotal, tax, total, discount, etc.)
    """
    purchases = get_purchases()
    
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
        **kwargs
    }
    
    purchases[purchase_id] = purchase_data
    _save_json(PURCHASES_FILE, purchases)
    
    return purchase_id

def update_purchase(purchase_id: str, updates: Dict[str, Any]) -> bool:
    """Update purchase order"""
    purchases = get_purchases()
    
    if purchase_id in purchases:
        purchases[purchase_id].update(updates)
        _save_json(PURCHASES_FILE, purchases)
        return True
    return False

# ============= MEASUREMENTS OPERATIONS =============

def get_measurements() -> Dict[str, Any]:
    """Get all measurements"""
    return _load_json(MEASUREMENTS_FILE, {})

def get_customer_measurements(customer_id: str, gender: str) -> Dict[str, Any]:
    """Get customer measurements"""
    measurements = get_measurements()
    key = f"{customer_id}_{gender}"
    return measurements.get(key, {})

def save_measurements(customer_id: str, gender: str, measurements_data: Dict[str, Any]) -> bool:
    """Save customer measurements"""
    all_measurements = get_measurements()
    
    key = f"{customer_id}_{gender}"
    all_measurements[key] = {
        "customer_id": customer_id,
        "gender": gender,
        "measurements": measurements_data,
        "recorded_at": datetime.now().isoformat()
    }
    
    return _save_json(MEASUREMENTS_FILE, all_measurements)

# ============= BILLING OPERATIONS =============

def get_billing_records() -> Dict[str, Any]:
    """Get all billing records"""
    return _load_json(BILLING_FILE, {})

def get_billing_record(purchase_id: str) -> Dict[str, Any]:
    """Get billing record for purchase"""
    billing = get_billing_records()
    return billing.get(purchase_id, {})

def save_billing(purchase_id: str, billing_data: Dict[str, Any]) -> bool:
    """Save billing information"""
    all_billing = get_billing_records()
    
    all_billing[purchase_id] = {
        "purchase_id": purchase_id,
        "billing_data": billing_data,
        "processed_at": datetime.now().isoformat()
    }
    
    return _save_json(BILLING_FILE, all_billing)

# Alias for backward compatibility
save_billing_info = save_billing

# ============= DELIVERY OPERATIONS =============

DELIVERY_OPTIONS = {
    "standard": {"name": "Standard Delivery", "cost": 9.99, "days": 5},
    "express": {"name": "Express Delivery", "cost": 19.99, "days": 2},
    "overnight": {"name": "Overnight Delivery", "cost": 39.99, "days": 1}
}

def get_delivery_schedules() -> Dict[str, Any]:
    """Get all delivery schedules"""
    return _load_json(DELIVERY_FILE, {})

def get_delivery_schedule(purchase_id: str) -> Dict[str, Any]:
    """Get delivery schedule for purchase"""
    schedules = get_delivery_schedules()
    return schedules.get(purchase_id, {})

def schedule_delivery(purchase_id: str, delivery_option: str, address: Dict[str, Any]) -> bool:
    """Schedule delivery"""
    all_schedules = get_delivery_schedules()
    
    delivery_date = datetime.now() + timedelta(days=DELIVERY_OPTIONS[delivery_option]["days"])
    
    all_schedules[purchase_id] = {
        "purchase_id": purchase_id,
        "delivery_option": delivery_option,
        "address": address,
        "scheduled_date": delivery_date.strftime("%Y-%m-%d"),
        "tracking_number": f"TRK-{uuid.uuid4().hex[:8].upper()}",
        "status": "scheduled",
        "delivery_cost": DELIVERY_OPTIONS[delivery_option]["cost"]
    }
    
    return _save_json(DELIVERY_FILE, all_schedules)

# ============= ALTERATION OPERATIONS =============

ALTERATION_PRICING = {
    "hemming": 15.00,
    "taking_in": 25.00,
    "letting_out": 30.00,
    "sleeve_adjustment": 20.00,
    "waist_adjustment": 25.00
}

def get_alterations() -> Dict[str, Any]:
    """Get all alteration requests"""
    return _load_json(ALTERATIONS_FILE, {})

def get_alteration(alteration_id: str) -> Dict[str, Any]:
    """Get specific alteration request"""
    alterations = get_alterations()
    return alterations.get(alteration_id, {})

def create_alteration_request(purchase_id: str, item_id: str, alterations: List[Dict]) -> str:
    """Create alteration request"""
    all_alterations = get_alterations()
    
    alteration_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    all_alterations[alteration_id] = {
        "alteration_id": alteration_id,
        "purchase_id": purchase_id,
        "item_id": item_id,
        "alterations": alterations,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    _save_json(ALTERATIONS_FILE, all_alterations)
    return alteration_id

def save_alteration_request(alteration_id: str, alteration_data: Dict[str, Any]) -> bool:
    """Save/update an alteration request"""
    all_alterations = get_alterations()
    all_alterations[alteration_id] = alteration_data
    return _save_json(ALTERATIONS_FILE, all_alterations)

# Aliases for backward compatibility
get_alteration_requests = get_alterations

# ============= ORDER OPERATIONS =============

def get_orders() -> Dict[str, Any]:
    """Get all orders"""
    return _load_json(ORDERS_FILE, {})

def get_order(order_id: str) -> Dict[str, Any]:
    """Get specific order by ID"""
    orders = get_orders()
    return orders.get(order_id, {})

def get_customer_orders(customer_id: str) -> List[Dict[str, Any]]:
    """Get all orders for a specific customer"""
    orders = get_orders()
    return [order for order in orders.values() if order.get("customer_id") == customer_id]

# Alias for backward compatibility
get_order_by_id = get_order

# ============= KNOWLEDGE BASE OPERATIONS =============

def get_knowledge_base() -> Dict[str, Any]:
    """Get technical knowledge base"""
    return _load_json(KNOWLEDGE_BASE_FILE, {})

def search_knowledge_base(query: str) -> List[Dict[str, Any]]:
    """Search knowledge base for solutions"""
    kb = get_knowledge_base()
    results = []
    query_lower = query.lower()
    
    for key, data in kb.items():
        if any(term in data["issue"].lower() for term in query_lower.split()):
            results.append(data)
    
    return results

def get_product_info(product_id: str) -> Dict[str, Any]:
    """Get product information (alias for get_product)"""
    return get_product(product_id)

# ============= RETURN POLICY OPERATIONS =============

def get_return_policy() -> Dict[str, Any]:
    """Get return policy"""
    return _load_json(RETURN_POLICY_FILE, {})

# Global constant for backward compatibility
RETURN_POLICY = None

def _load_return_policy():
    """Load return policy into global constant"""
    global RETURN_POLICY
    RETURN_POLICY = get_return_policy()

# ============= FAQ OPERATIONS =============

def get_faq() -> Dict[str, Any]:
    """Get FAQ data"""
    return _load_json(FAQ_FILE, {})

def search_faq(query: str) -> List[Dict[str, Any]]:
    """Search FAQ for answers"""
    faq_data = get_faq()
    results = []
    query_lower = query.lower()
    
    for category, faqs in faq_data.items():
        for faq in faqs:
            if any(term in faq["question"].lower() or term in faq["answer"].lower() 
                   for term in query_lower.split()):
                results.append({**faq, "category": category})
    
    return results

# Initialize on import
initialize_data_files()
_load_return_policy()  # Load return policy into global constant
