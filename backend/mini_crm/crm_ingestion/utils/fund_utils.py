"""
Utility functions for fund-related operations.
"""

def detect_fund_type(fund_name: str) -> str:
    """
    Detect the fund type based on the fund name according to business rules.
    
    Args:
        fund_name: The name of the fund to analyze
        
    Returns:
        str: One of: "קופת גמל", "קרן השתלמות", "גמל להשקעה", or empty string if no match
    """
    if not fund_name or not isinstance(fund_name, str):
        return ""
        
    fund_name = fund_name.strip()
    
    # Check for exact matches first
    if "גמל להשקעה" in fund_name:
        return "גמל להשקעה"
    elif "השתלמות" in fund_name:
        return "קרן השתלמות"
    elif "גמל" in fund_name:
        return "קופת גמל"
        
    return ""  # Default if no match found
