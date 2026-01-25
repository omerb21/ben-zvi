"""
Name utilities for Mini CRM
Handles splitting full names and name normalization
"""

def split_full_name(full_name: str) -> tuple[str, str]:
    """
    Split full name into first and last name
    
    Args:
        full_name: Full name string
        
    Returns:
        tuple: (first_name, last_name) with proper handling of multiple spaces
    """
    if not full_name or not isinstance(full_name, str):
        return "", ""
    
    # Clean up multiple spaces and strip
    parts = full_name.strip().split()
    
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        # Single name - treat as first name
        return parts[0], ""
    else:
        # Multiple parts - first is first_name, rest is last_name
        return parts[0], " ".join(parts[1:])
