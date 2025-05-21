from math import ceil
from typing import Dict, Any

# Pricing configuration
CREDITS_PER_KB = 1  # 1 credit per KB
BASE_CREDITS = 1    # Minimum credits per request
USD_PER_CREDIT = 0.001  # $0.001 per credit

def compute_credits(event: Dict[str, Any]) -> int:
    """
    Compute credits for a given event based on bytes served.
    
    Args:
        event: Dictionary containing event data including bytes_served
        
    Returns:
        int: Number of credits to bill
    """
    bytes_served = event.get('bytes_served', 0)
    if bytes_served <= 0:
        return BASE_CREDITS
        
    # Convert bytes to KB and ceil to nearest KB
    kb_served = ceil(bytes_served / 1024)
    credits = max(BASE_CREDITS, kb_served * CREDITS_PER_KB)
    
    return credits

def calculate_cost(credits: int) -> float:
    """
    Calculate USD cost for given number of credits.
    
    Args:
        credits: Number of credits
        
    Returns:
        float: Cost in USD
    """
    return credits * USD_PER_CREDIT 