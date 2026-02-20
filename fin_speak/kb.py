"""
Knowledge Base module
Handles fund queries using real-time data
"""

from typing import Dict
from .data_service import (
    get_fund_nav,
    get_fund_returns,
    match_fund_by_name,
    search_funds
)


async def query_nav(fund_name: str) -> Dict:
    """Query current NAV for a fund"""
    fund = await match_fund_by_name(fund_name)
    if not fund:
        return {"error": f"Fund '{fund_name}' not found"}
    
    nav_data = await get_fund_nav(fund["schemeCode"])
    if nav_data:
        return {
            "success": True,
            "fund_name": nav_data["scheme_name"],
            "nav": nav_data["nav"],
            "date": nav_data["date"],
            "fund_house": nav_data["fund_house"]
        }
    
    return {"error": "Could not fetch NAV data"}


async def query_returns(fund_name: str, months: int = 12) -> Dict:
    """Query returns for a fund"""
    fund = await match_fund_by_name(fund_name)
    if not fund:
        return {"error": f"Fund '{fund_name}' not found"}
    
    returns_data = await get_fund_returns(fund["schemeCode"], months)
    if returns_data:
        return {
            "success": True,
            "fund_name": returns_data["scheme_name"],
            "returns_percent": returns_data["returns_percent"],
            "period_months": returns_data["period_months"],
            "current_nav": returns_data["current_nav"],
            "old_nav": returns_data["old_nav"]
        }
    
    return {"error": "Could not calculate returns"}


async def search_fund(query: str) -> Dict:
    """Search for funds by name"""
    funds = await search_funds(query, limit=5)
    return {
        "success": True,
        "count": len(funds),
        "funds": [{"code": f["schemeCode"], "name": f["schemeName"]} for f in funds]
    }
