"""
Tests for MOR loader fund type transformations.
"""

import pandas as pd
import pytest
from crm_ingestion.loaders.mor_loader import load_and_transform, _map_fund_type


def test_map_fund_type():
    """Test the _map_fund_type function directly."""
    # Test exact matches
    assert _map_fund_type("אלפא מור תגמולים") == "קופת גמל"
    assert _map_fund_type("מור השתלמות") == "קרן השתלמות"
    
    # Test with extra whitespace
    assert _map_fund_type("  אלפא מור תגמולים  ") == "קופת גמל"
    assert _map_fund_type("  מור השתלמות  ") == "קרן השתלמות"
    
    # Test non-matching values remain unchanged
    assert _map_fund_type("סוג אחר") == "סוג אחר"
    assert _map_fund_type("") == ""
    assert _map_fund_type(None) is None
    assert _map_fund_type(123) == 123


def test_load_and_transform_fund_types():
    """Test that load_and_transform correctly maps fund types."""
    # Create test data
    test_data = {
        "שם העמית": ["משה כהן", "דוד לוי", "שרה אברהם", "רחל דוד"],
        "זהות": ["123456789", "987654321", "456789123", "321654987"],
        "חשבון": ["ACC123", "ACC456", "ACC789", "ACC012"],
        "סוג קופה": [
            "אלפא מור תגמולים", 
            "מור השתלמות", 
            "סוג אחר", 
            "  אלפא מור תגמולים  "  # With extra spaces
        ],
        "מסלול": ["מסלול א", "מסלול ב", "מסלול ג", "מסלול ד"],
        "יתרה נכון ל-27/07/25": [10000, 20000, 30000, 40000]
    }
    
    # Create DataFrame and process it
    df = pd.DataFrame(test_data)
    result = load_and_transform(df, "2025-01-01")
    
    # Check that fund types were mapped correctly
    assert result.iloc[0]["fund_type"] == "קופת גמל"
    assert result.iloc[1]["fund_type"] == "קרן השתלמות"
    assert result.iloc[2]["fund_type"] == "סוג אחר"
    assert result.iloc[3]["fund_type"] == "קופת גמל"  # Should be trimmed and mapped


def test_load_and_transform_with_missing_fund_type():
    """Test that the loader handles missing fund_type column gracefully."""
    # Create test data without fund_type column
    test_data = {
        "שם העמית": ["משה כהן", "דוד לוי"],
        "זהות": ["123456789", "987654321"],
        "חשבון": ["ACC123", "ACC456"],
        "מסלול": ["מסלול א", "מסלול ב"],
        "יתרה נכון ל-27/07/25": [10000, 20000]
    }
    
    # Create DataFrame and process it
    df = pd.DataFrame(test_data)
    
    # This should not raise an exception
    result = load_and_transform(df, "2025-01-01")
    
    # Verify the result has the expected columns
    assert "fund_type" not in result.columns
