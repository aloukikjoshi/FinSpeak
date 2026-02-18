"""
Knowledge Base (KB) module
Handles fund data loading and queries
"""

import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta

import pandas as pd

from .config import Config


# Cache for loaded data
_funds_cache: Optional[pd.DataFrame] = None
_nav_cache: Optional[pd.DataFrame] = None


def load_funds_data() -> pd.DataFrame:
    """
    Load funds data from CSV
    
    Returns:
        DataFrame with fund information
    """
    global _funds_cache
    
    if _funds_cache is None:
        if not os.path.exists(Config.FUNDS_CSV):
            raise FileNotFoundError(f"Funds CSV not found: {Config.FUNDS_CSV}")
        
        _funds_cache = pd.read_csv(Config.FUNDS_CSV)
        if Config.DEBUG:
            print(f"Loaded {len(_funds_cache)} funds")
    
    return _funds_cache


def load_nav_data() -> pd.DataFrame:
    """
    Load NAV history data from CSV
    
    Returns:
        DataFrame with NAV history
    """
    global _nav_cache
    
    if _nav_cache is None:
        if not os.path.exists(Config.NAV_HISTORY_CSV):
            raise FileNotFoundError(f"NAV history CSV not found: {Config.NAV_HISTORY_CSV}")
        
        _nav_cache = pd.read_csv(Config.NAV_HISTORY_CSV)
        _nav_cache['date'] = pd.to_datetime(_nav_cache['date'])
        _nav_cache = _nav_cache.sort_values(['fund_id', 'date'])
        
        if Config.DEBUG:
            print(f"Loaded {len(_nav_cache)} NAV records")
    
    return _nav_cache


def match_fund(name: str) -> Optional[str]:
    """
    Match fund name to fund_id
    
    Args:
        name: Fund name (exact or fuzzy)
        
    Returns:
        fund_id or None if not found
    """
    try:
        from rapidfuzz import fuzz, process
        
        funds_df = load_funds_data()
        fund_names = funds_df['fund_name'].tolist()
        
        # Find best match
        result = process.extractOne(
            name,
            fund_names,
            scorer=fuzz.token_set_ratio
        )
        
        if result:
            matched_name, score, _ = result
            if score >= Config.FUZZY_MATCH_THRESHOLD:
                fund_id = funds_df[funds_df['fund_name'] == matched_name]['fund_id'].iloc[0]
                return fund_id
        
        return None
        
    except ImportError:
        # Fallback to exact matching
        funds_df = load_funds_data()
        name_lower = name.lower()
        
        for _, row in funds_df.iterrows():
            if name_lower in row['fund_name'].lower() or row['fund_name'].lower() in name_lower:
                return row['fund_id']
        
        return None


def get_latest_nav(fund_id: str) -> Optional[Dict]:
    """
    Get the latest NAV for a fund
    
    Args:
        fund_id: Fund ID
        
    Returns:
        Dictionary with date and NAV
    """
    nav_df = load_nav_data()
    fund_navs = nav_df[nav_df['fund_id'] == fund_id]
    
    if fund_navs.empty:
        return None
    
    latest = fund_navs.iloc[-1]
    
    return {
        'date': latest['date'].strftime('%Y-%m-%d'),
        'nav': float(latest['nav'])
    }


def get_fund_info(fund_id: str) -> Optional[Dict]:
    """
    Get fund information
    
    Args:
        fund_id: Fund ID
        
    Returns:
        Dictionary with fund information
    """
    funds_df = load_funds_data()
    fund = funds_df[funds_df['fund_id'] == fund_id]
    
    if fund.empty:
        return None
    
    return fund.iloc[0].to_dict()


def compute_return(fund_id: str, months: int = 12) -> Dict:
    """
    Compute return for a fund over specified period
    
    Args:
        fund_id: Fund ID
        months: Number of months to look back
        
    Returns:
        Dictionary with return data including:
        - start_date, end_date
        - start_nav, end_nav
        - absolute_return, percentage_return
        - period_months
    """
    nav_df = load_nav_data()
    fund_navs = nav_df[nav_df['fund_id'] == fund_id].copy()
    
    if fund_navs.empty:
        raise ValueError(f"No NAV data found for fund {fund_id}")
    
    # Get latest NAV
    end_date = fund_navs['date'].max()
    end_nav = fund_navs[fund_navs['date'] == end_date]['nav'].iloc[0]
    
    # Calculate target start date
    target_start_date = end_date - timedelta(days=months * 30)
    
    # Find closest available date to target
    fund_navs['date_diff'] = abs((fund_navs['date'] - target_start_date).dt.days)
    closest_start = fund_navs.loc[fund_navs['date_diff'].idxmin()]
    
    start_date = closest_start['date']
    start_nav = closest_start['nav']
    
    # Calculate returns
    absolute_return = end_nav - start_nav
    percentage_return = (absolute_return / start_nav) * 100
    
    # Calculate actual period
    actual_days = (end_date - start_date).days
    actual_months = actual_days / 30.0
    
    return {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'start_nav': float(start_nav),
        'end_nav': float(end_nav),
        'absolute_return': float(absolute_return),
        'percentage_return': float(percentage_return),
        'period_months': round(actual_months, 1),
        'requested_months': months
    }


def get_all_funds() -> List[Dict]:
    """
    Get list of all funds
    
    Returns:
        List of fund dictionaries
    """
    funds_df = load_funds_data()
    return funds_df.to_dict('records')


def search_funds(query: str) -> List[Dict]:
    """
    Search for funds by name or category
    
    Args:
        query: Search query
        
    Returns:
        List of matching funds
    """
    funds_df = load_funds_data()
    query_lower = query.lower()
    
    matches = funds_df[
        funds_df['fund_name'].str.lower().str.contains(query_lower) |
        funds_df['category'].str.lower().str.contains(query_lower)
    ]
    
    return matches.to_dict('records')
