"""
Tests for fund_utils.py
"""

import pytest
from crm_ingestion.utils.fund_utils import detect_fund_type


def test_detect_fund_type_gemel():
    """Test detection of regular gemel fund."""
    assert detect_fund_type("קופת גמל כללית") == "קופת גמל"
    assert detect_fund_type("גמל השקעות") == "קופת גמל"
    assert detect_fund_type("קרן גמל") == "קופת גמל"


def test_detect_fund_type_hishtalmut():
    """Test detection of hishtalmut fund."""
    assert detect_fund_type("קרן השתלמות לעובדי הייטק") == "קרן השתלמות"
    assert detect_fund_type("השתלמות כללית") == "קרן השתלמות"


def test_detect_fund_type_gemel_lehashkaza():
    """Test detection of gemel lehashkaza fund."""
    assert detect_fund_type("גמל להשקעה כללי") == "גמל להשקעה"
    assert detect_fund_type("גמל להשקעה") == "גמל להשקעה"
    assert detect_fund_type("גמל להשקעה אופציה") == "גמל להשקעה"


def test_detect_fund_type_edge_cases():
    """Test edge cases and partial matches."""
    # Exact matches should work
    assert detect_fund_type("גמל להשקעה") == "גמל להשקעה"
    
    # Case should not matter
    assert detect_fund_type("גמל להשקעה".upper()) == "גמל להשקעה"
    
    # Partial matches should work
    assert detect_fund_type("השתלמות") == "קרן השתלמות"
    assert detect_fund_type("גמל") == "קופת גמל"
    
    # Empty or invalid inputs
    assert detect_fund_type("") == ""
    assert detect_fund_type(None) == ""
    assert detect_fund_type(123) == ""
