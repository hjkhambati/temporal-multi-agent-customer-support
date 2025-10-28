"""Female Specialist Tools - Measurement capture and validation for female clothing"""

from typing import Dict, Any, List
import json
from data.persistent_data import (
    FEMALE_MEASUREMENT_REQUIREMENTS,
    get_catalog,
    get_product,
    save_measurements,
    get_measurements
)

def list_female_shirts_inventory() -> Dict[str, Any]:
    """List all available shirts/blouses in inventory for female customers with details"""
    try:
        female_shirts = []
        catalog = get_catalog()
        
        for product_id, product in catalog.items():
            if product.get("gender") == "female" and product.get("category") in ["blouse", "shirt"]:
                female_shirts.append({
                    "product_id": product_id,
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "sizes": product.get("sizes", []),
                    "colors": product.get("colors", []),
                    "requires_measurements": product.get("requires_measurements", False),
                    "alterable": product.get("alterable", False),
                    "category": product.get("category")
                })
        
        if not female_shirts:
            return {
                "success": False,
                "error": "No female shirts/blouses available in inventory"
            }
        
        return {
            "success": True,
            "total_products": len(female_shirts),
            "shirts": female_shirts,
            "message": f"Found {len(female_shirts)} female shirt(s)/blouse(s) in inventory"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_female_product_details(product_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific female product"""
    try:
        product = get_product(product_id)
        
        if not product:
            return {
                "success": False,
                "error": f"Product {product_id} not found in catalog"
            }
        
        if product.get("gender") != "female":
            return {
                "success": False,
                "error": f"Product {product_id} is not a female product"
            }
        
        return {
            "success": True,
            "product": {
                "product_id": product_id,
                "name": product.get("name"),
                "category": product.get("category"),
                "price": product.get("price"),
                "sizes": product.get("sizes", []),
                "colors": product.get("colors", []),
                "requires_measurements": product.get("requires_measurements", False),
                "alterable": product.get("alterable", False)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_female_measurement_requirements(item_category: str) -> Dict[str, Any]:
    """Get required measurements for a female clothing category"""
    try:
        category_lower = item_category.lower()
        requirements = FEMALE_MEASUREMENT_REQUIREMENTS.get(category_lower, [])
        
        if not requirements:
            return {
                "success": False,
                "error": f"Unknown category: {item_category}. Available: {list(FEMALE_MEASUREMENT_REQUIREMENTS.keys())}"
            }
        
        measurement_guide = {
            "category": item_category,
            "required_measurements": requirements,
            "measurement_guide": {
                "bust": "Measure around the fullest part of bust",
                "waist": "Measure around natural waistline",
                "hip": "Measure around fullest part of hips",
                "shoulder_width": "Measure from shoulder point to shoulder point across back",
                "sleeve_length": "Measure from shoulder to wrist with arm slightly bent",
                "dress_length": "Measure from shoulder to desired hem length",
                "skirt_length": "Measure from waist to desired hem length",
                "inseam": "Measure from crotch to ankle along inner leg",
                "thigh": "Measure around fullest part of thigh"
            },
            "units": "inches"
        }
        
        return {"success": True, "requirements": measurement_guide}
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_female_measurements(measurements: Dict[str, float], item_category: str) -> Dict[str, Any]:
    """Validate female measurements against requirements and reasonable ranges"""
    try:
        category_lower = item_category.lower()
        required = FEMALE_MEASUREMENT_REQUIREMENTS.get(category_lower, [])
        
        if not required:
            return {"success": False, "error": f"Unknown category: {item_category}"}
        
        # Check all required measurements provided
        missing = [m for m in required if m not in measurements]
        if missing:
            return {
                "success": False,
                "valid": False,
                "error": f"Missing required measurements: {missing}"
            }
        
        # Validate reasonable ranges (in inches)
        validation_ranges = {
            "bust": (28, 50),
            "waist": (22, 42),
            "hip": (30, 52),
            "shoulder_width": (13, 20),
            "sleeve_length": (28, 36),
            "dress_length": (32, 48),
            "skirt_length": (14, 32),
            "inseam": (26, 36),
            "thigh": (16, 28)
        }
        
        validation_issues = []
        for measurement_name, value in measurements.items():
            if measurement_name in validation_ranges:
                min_val, max_val = validation_ranges[measurement_name]
                if not (min_val <= value <= max_val):
                    validation_issues.append(
                        f"{measurement_name}: {value} inches (expected {min_val}-{max_val})"
                    )
        
        if validation_issues:
            return {
                "success": True,
                "valid": False,
                "issues": validation_issues,
                "message": "Some measurements are outside typical ranges. Please verify."
            }
        
        return {
            "success": True,
            "valid": True,
            "message": "All measurements validated successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def record_female_measurements(customer_id: str, measurements: Dict[str, float], item_category: str) -> Dict[str, Any]:
    """Record validated female measurements to database"""
    try:
        # Validate first
        validation = validate_female_measurements(measurements, item_category)
        if not validation.get("success") or not validation.get("valid"):
            return validation
        
        # Save measurements
        success = save_measurements(customer_id, "female", measurements)
        
        if success:
            return {
                "success": True,
                "message": f"Female measurements for {item_category} recorded successfully",
                "customer_id": customer_id,
                "measurements": measurements
            }
        else:
            return {"success": False, "error": "Failed to save measurements"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def retrieve_female_measurements(customer_id: str) -> Dict[str, Any]:
    """Retrieve previously recorded female measurements"""
    try:
        measurements_data = get_measurements(customer_id, "female")
        
        if not measurements_data:
            return {
                "success": True,
                "found": False,
                "message": "No previous measurements found for this customer"
            }
        
        return {
            "success": True,
            "found": True,
            "measurements": measurements_data.get("measurements", {}),
            "recorded_at": measurements_data.get("recorded_at")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def recommend_size_female(measurements: Dict[str, float], product_id: str) -> Dict[str, Any]:
    """Recommend size based on measurements and product sizing chart"""
    try:
        product = get_product(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        
        # Simple sizing logic based on bust/waist/hip
        if "bust" in measurements and "waist" in measurements and "hip" in measurements:
            bust = measurements["bust"]
            waist = measurements["waist"]
            hip = measurements["hip"]
            
            # Average-based sizing
            avg = (bust + waist + hip) / 3
            
            if avg < 32:
                recommended_size = "XS"
            elif avg < 35:
                recommended_size = "S"
            elif avg < 38:
                recommended_size = "M"
            elif avg < 42:
                recommended_size = "L"
            else:
                recommended_size = "XL"
        else:
            return {"success": False, "error": "Insufficient measurements for size recommendation (need bust, waist, hip)"}
        
        # Check if size available
        available_sizes = product.get("sizes", [])
        if recommended_size not in available_sizes:
            return {
                "success": True,
                "recommended_size": recommended_size,
                "available": False,
                "message": f"Recommended size {recommended_size} not available. Available sizes: {available_sizes}"
            }
        
        return {
            "success": True,
            "recommended_size": recommended_size,
            "available": True,
            "confidence": "high",
            "measurements_used": list(measurements.keys())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
