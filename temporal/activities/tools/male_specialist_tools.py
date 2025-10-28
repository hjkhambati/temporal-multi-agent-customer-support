"""Male Specialist Tools - Measurement capture and validation for male clothing"""

from typing import Dict, Any, List
import json
from data.persistent_data import (
    MALE_MEASUREMENT_REQUIREMENTS,
    get_catalog,
    get_product,
    save_measurements,
    get_measurements
)

def list_male_shirts_inventory() -> Dict[str, Any]:
    """List all available shirts in inventory for male customers with details"""
    try:
        male_shirts = []
        catalog = get_catalog()
        
        for product_id, product in catalog.items():
            if product.get("gender") == "male" and product.get("category") == "shirt":
                male_shirts.append({
                    "product_id": product_id,
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "sizes": product.get("sizes", []),
                    "colors": product.get("colors", []),
                    "requires_measurements": product.get("requires_measurements", False),
                    "alterable": product.get("alterable", False)
                })
        
        if not male_shirts:
            return {
                "success": False,
                "error": "No male shirts available in inventory"
            }
        
        return {
            "success": True,
            "total_products": len(male_shirts),
            "shirts": male_shirts,
            "message": f"Found {len(male_shirts)} male shirt(s) in inventory"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_male_product_details(product_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific male product"""
    try:
        product = get_product(product_id)
        
        if not product:
            return {
                "success": False,
                "error": f"Product {product_id} not found in catalog"
            }
        
        if product.get("gender") != "male":
            return {
                "success": False,
                "error": f"Product {product_id} is not a male product"
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

def get_male_measurement_requirements(item_category: str) -> Dict[str, Any]:
    """Get required measurements for a male clothing category"""
    try:
        category_lower = item_category.lower()
        requirements = MALE_MEASUREMENT_REQUIREMENTS.get(category_lower, [])
        
        if not requirements:
            return {
                "success": False,
                "error": f"Unknown category: {item_category}. Available: {list(MALE_MEASUREMENT_REQUIREMENTS.keys())}"
            }
        
        measurement_guide = {
            "category": item_category,
            "required_measurements": requirements,
            "measurement_guide": {
                "chest": "Measure around the fullest part of chest, under arms",
                "waist": "Measure around natural waistline",
                "shoulder_width": "Measure from shoulder point to shoulder point across back",
                "sleeve_length": "Measure from shoulder to wrist with arm slightly bent",
                "neck": "Measure around the base of neck",
                "inseam": "Measure from crotch to ankle along inner leg",
                "outseam": "Measure from waist to ankle along outer leg",
                "hip": "Measure around fullest part of hips",
                "thigh": "Measure around fullest part of thigh"
            },
            "units": "inches"
        }
        
        return {"success": True, "requirements": measurement_guide}
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_male_measurements(measurements: Dict[str, float], item_category: str) -> Dict[str, Any]:
    """Validate male measurements against requirements and reasonable ranges"""
    try:
        category_lower = item_category.lower()
        required = MALE_MEASUREMENT_REQUIREMENTS.get(category_lower, [])
        
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
            "chest": (30, 60),
            "waist": (24, 50),
            "shoulder_width": (14, 24),
            "sleeve_length": (30, 40),
            "neck": (13, 20),
            "inseam": (26, 38),
            "outseam": (38, 48),
            "hip": (30, 55),
            "thigh": (18, 32)
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

def record_male_measurements(customer_id: str, measurements: Dict[str, float], item_category: str) -> Dict[str, Any]:
    """Record validated male measurements to database"""
    try:
        # Validate first
        validation = validate_male_measurements(measurements, item_category)
        if not validation.get("success") or not validation.get("valid"):
            return validation
        
        # Save measurements
        success = save_measurements(customer_id, "male", measurements)
        
        if success:
            return {
                "success": True,
                "message": f"Male measurements for {item_category} recorded successfully",
                "customer_id": customer_id,
                "measurements": measurements
            }
        else:
            return {"success": False, "error": "Failed to save measurements"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def retrieve_male_measurements(customer_id: str) -> Dict[str, Any]:
    """Retrieve previously recorded male measurements"""
    try:
        measurements_data = get_measurements(customer_id, "male")
        
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

def recommend_size_male(measurements: Dict[str, float], product_id: str) -> Dict[str, Any]:
    """Recommend size based on measurements and product sizing chart"""
    try:
        product = get_product(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        
        # Simple sizing logic based on chest/waist
        if "chest" in measurements:
            chest = measurements["chest"]
            if chest < 36:
                recommended_size = "S"
            elif chest < 40:
                recommended_size = "M"
            elif chest < 44:
                recommended_size = "L"
            elif chest < 48:
                recommended_size = "XL"
            else:
                recommended_size = "XXL"
        elif "waist" in measurements:
            waist = measurements["waist"]
            if waist < 30:
                recommended_size = "28"
            elif waist < 32:
                recommended_size = "30"
            elif waist < 34:
                recommended_size = "32"
            elif waist < 36:
                recommended_size = "34"
            elif waist < 38:
                recommended_size = "36"
            else:
                recommended_size = "38"
        else:
            return {"success": False, "error": "Insufficient measurements for size recommendation"}
        
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
