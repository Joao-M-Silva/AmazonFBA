"""
Functions to optimize PPC bids
"""

import pandas as pd
from typing import List


def optimize_bids(
        x, 
        acos_target: float, 
        price: float,
) -> str:
    try:
        ACOS = float(x["Total Advertising Cost of Sales (ACOS) "])
    except ValueError:
        ACOS = 400
    ACOS_target = float(x["Campaign Target ACOS (%)"] / 100)
    if ACOS_target == 0.0:
        ACOS_target = float(acos_target)

    CPC = x["Cost Per Click (CPC)"]
    click_share = x["Click Share (%)"] 
    search_term = x["Customer Search Term"]
    
    if (
        x["7 Day Total Sales "] == 0
        and
        x["Clicks"] > ((1.2*ACOS_target*price / CPC) - 1)
    ):
        new_bid = str(ACOS_target*price / (1 + x["Clicks"]))
        if click_share < 5:
            return new_bid
        else:
            return f"High Traffic Zero Sales: {new_bid}"
            
    if (
        x["7 Day Total Sales "] == 0
        and
        x["Clicks"] < ((0.75*ACOS_target*price / CPC) - 1)
    ):
        new_bid = str(CPC*1.1)
        return new_bid

    if ACOS < ACOS_target:
        new_bid = str(CPC*1.1)
        return new_bid
        
    if ACOS > ACOS_target:
        new_bid = str((ACOS_target / ACOS) * CPC)
        if click_share < 5:
            return new_bid
        else:
            return f"High Traffic High ACOS: {new_bid}"

    return "-"
    
    """
    elif "broad" in campaign_name.lower() or "phrase" in campaign_name.lower():
        if (
            x["7 Day Total Sales "] == 0
            and
            x["Clicks"] > ((1.2*ACOS_target*price / CPC) - 1)
        ):
            return "Negate"
        
        if x["7 Day Total Sales "] > 0:
            if ACOS > ACOS_target:
                if search_term not in high_traffic_search_terms:
                    new_bid = str((ACOS_target / ACOS) * CPC)
                    return f"Upscale and Negate: {new_bid}"
                else:
                    new_bid = str((ACOS_target / ACOS) * CPC)
                    return f"Upscale (High Traffic High ACOS): {new_bid}"
            
            elif ACOS < ACOS_target:
                new_bid = CPC*1.1
                return f"Upscale: {new_bid}"
    """

