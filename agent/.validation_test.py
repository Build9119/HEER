"""Validation Test Suites for AI Asset Registry

This file contains automated tests for the validation functions in .validation.py
"""

import unittest
from .validation import validate_asset_creation, validate_asset_update
from .ai_asset_registry import AssetType, RiskClassification, LifecycleState, ApprovalState

class TestValidation(unittest.TestCase):

    def test_asset_creation_valid(self):
        data = {
            "tenant_id": "demo_tenant",
            "asset_name": "Test Agent",
            "asset_type": AssetType.AGENT.value,
            "version": "1.0.0",
            "provider": "HEER-AGENCY",
            "risk_classification": RiskClassification.LOW.value,
            "lifecycle_state": LifecycleState.ACTIVE.value,
            "approval_state": ApprovalState.PENDING.value
        }
        # No exception should be raised
        self.assertIsNone(validate_asset_creation(data))

    def test_asset_creation_missing_fields(self):
        # Test missing tenant_id
        data = {**{}, **{"asset_name": "Test Agent", ...}}  # Fill other fields
        with self.assertRaises(ValueError) as context:
            validate_asset_creation(data)
        self.assertIn("tenant_id", str(context.exception))

    def test_invalid_asset_type(self):
        data = {**{}, "asset_type": "invalid_type"}
        with self.assertRaises(ValueError) as context:
            validate_asset_creation(data)
        self.assertIn("Invalid asset_type", str(context.exception))

    def test_asset_update_valid(self):
        data = {
            "asset_id": "1234567890abcdef",
            "version": "1.1.0"
        }
        self.assertIsNone(validate_asset_update(data))

    def test_asset_update_missing_id(self):
        data = {"version": "1.1.0"}
        with self.assertRaises(ValueError) as context:
            validate_asset_update(data)
        self.assertIn("asset_id", str(context.exception))

    # Add more test cases as needed...

if __name__ == '__main__':
    unittest.main()