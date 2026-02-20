"""
Real-time data service using MFAPI.in
Fetches live mutual fund NAV and historical data
"""

import httpx
from typing import Optional, Dict, List
from datetime import datetime
import asyncio

MFAPI_BASE = "https://api.mfapi.in/mf"

# Cache for fund list (refreshed periodically)
_fund_list_cache: Optional[List[Dict]] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_MINUTES = 60


async def get_all_funds() -> List[Dict]:
    """Fetch list of all mutual funds"""
    global _fund_list_cache, _cache_timestamp
    
    now = datetime.now()
    if _fund_list_cache and _cache_timestamp:
        age = (now - _cache_timestamp).total_seconds() / 60
        if age < CACHE_TTL_MINUTES:
            return _fund_list_cache
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(MFAPI_BASE)
        response.raise_for_status()
        _fund_list_cache = response.json()
        _cache_timestamp = now
        return _fund_list_cache


async def get_fund_details(scheme_code: str) -> Optional[Dict]:
    """
    Fetch fund details including NAV history
    
    Args:
        scheme_code: AMFI scheme code
        
    Returns:
        Fund details with NAV data
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{MFAPI_BASE}/{scheme_code}")
        if response.status_code == 200:
            return response.json()
        return None


async def search_funds(query: str, limit: int = 10) -> List[Dict]:
    """
    Search funds by name
    
    Args:
        query: Search string
        limit: Max results
        
    Returns:
        List of matching funds
    """
    funds = await get_all_funds()
    query_lower = query.lower()
    
    matches = []
    for fund in funds:
        name = fund.get("schemeName", "").lower()
        if query_lower in name:
            matches.append(fund)
            if len(matches) >= limit:
                break
    
    return matches


async def get_fund_nav(scheme_code: str) -> Optional[Dict]:
    """
    Get current NAV for a fund
    
    Args:
        scheme_code: AMFI scheme code
        
    Returns:
        NAV details including date and value
    """
    details = await get_fund_details(scheme_code)
    if details and details.get("data"):
        latest = details["data"][0]
        return {
            "scheme_code": scheme_code,
            "scheme_name": details.get("meta", {}).get("scheme_name", ""),
            "nav": float(latest.get("nav", 0)),
            "date": latest.get("date", ""),
            "fund_house": details.get("meta", {}).get("fund_house", "")
        }
    return None


async def get_fund_returns(scheme_code: str, months: int = 12) -> Optional[Dict]:
    """
    Calculate returns for a fund over specified period
    
    Args:
        scheme_code: AMFI scheme code
        months: Number of months for return calculation
        
    Returns:
        Return details
    """
    details = await get_fund_details(scheme_code)
    if not details or not details.get("data"):
        return None
    
    nav_data = details["data"]
    if len(nav_data) < 2:
        return None
    
    current_nav = float(nav_data[0].get("nav", 0))
    current_date = nav_data[0].get("date", "")
    
    # Find NAV from specified months ago
    target_days = months * 30
    old_nav = None
    old_date = None
    
    for entry in nav_data:
        try:
            entry_date = datetime.strptime(entry["date"], "%d-%m-%Y")
            current_dt = datetime.strptime(current_date, "%d-%m-%Y")
            days_diff = (current_dt - entry_date).days
            
            if days_diff >= target_days:
                old_nav = float(entry.get("nav", 0))
                old_date = entry.get("date", "")
                break
        except:
            continue
    
    if old_nav and old_nav > 0:
        returns = ((current_nav - old_nav) / old_nav) * 100
        return {
            "scheme_code": scheme_code,
            "scheme_name": details.get("meta", {}).get("scheme_name", ""),
            "current_nav": current_nav,
            "current_date": current_date,
            "old_nav": old_nav,
            "old_date": old_date,
            "period_months": months,
            "returns_percent": round(returns, 2)
        }
    
    return None


async def match_fund_by_name(name: str) -> Optional[Dict]:
    """
    Find best matching fund by name using fuzzy search
    
    Args:
        name: Fund name to search
        
    Returns:
        Best matching fund or None
    """
    try:
        from rapidfuzz import fuzz, process
        
        funds = await get_all_funds()
        
        # Create case-insensitive mapping
        fund_names = [f.get("schemeName", "") for f in funds]
        fund_names_lower = [n.lower() for n in fund_names]
        
        # Match against lowercase names
        result = process.extractOne(
            name.lower(),
            fund_names_lower,
            scorer=fuzz.token_set_ratio
        )
        
        if result and result[1] >= 50:
            matched_idx = fund_names_lower.index(result[0])
            return funds[matched_idx]
        
        return None
        
    except ImportError:
        # Fallback to simple search
        funds = await search_funds(name, limit=1)
        return funds[0] if funds else None
