"""Validation module for AI Asset Registry

This module contains validation functions for asset creation and updates,
ensuring compliance with business rules and data integrity constraints.
"""

from enum import Enum
from typing import Any, Dict, Optional, Union

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_asset_creation(
    data: Dict[str, Any]
) -> None:
    """
    Validate parameters for creating a new AI asset.
    
    Args:
        data: Dictionary containing asset creation parameters
        
    Raises:
        ValueError: If validation fails
    """
    required_fields = ["tenant_id", "asset_name", "asset_type", "version", "provider"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    if not isinstance(data["asset_type"], str) or data["asset_type"] not in [t.value for t in AssetType]:
        raise ValueError(f"Invalid asset_type: {data['asset_type']}")

    valid_risk = ["low", "medium", "high", "critical"]
    if data.get("risk_classification") and data["risk_classification"] not in valid_risk:
        raise ValueError(f"Invalid risk_classification: {data['risk_classification']}")

    valid_lifecycle = ["active", "deprecated", "retired"]
    if data.get("lifecycle_state") and data["lifecycle_state"] not in valid_lifecycle:
        raise ValueError(f"Invalid lifecycle_state: {data['lifecycle_state']}")

    valid_approval = ["approved", "pending", "denied"]
    if data.get("approval_state") and data["approval_state"] not in valid_approval:
        raise ValueError(f"Invalid approval_state: {data['approval_state']}")

def validate_asset_update(
    data: Dict[str, Any]
) -> None:
    """
    Validate parameters for updating an existing asset.
    
    Args:
        data: Dictionary containing update parameters
        
    Raises:
        ValueError: If validation fails
    """
    if "asset_id" not in data or not data["asset_id"]:
        raise ValueError("asset_id is required for updates")

    # Check duration of change
    if "version" in data and len(data["version"]) > 100:
        raise ValueError("Version string too long")

    # Validate other fields as needed...