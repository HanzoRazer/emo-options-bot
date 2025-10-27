"""Utility functions."""

from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal


def calculate_days_to_expiration(expiration_date) -> int:
    """Calculate days until option expiration."""
    if isinstance(expiration_date, str):
        expiration_date = datetime.fromisoformat(expiration_date).date()
    
    today = datetime.now().date()
    delta = expiration_date - today
    return delta.days


def format_currency(amount: Decimal) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"


def parse_expiration(expiration_str: str):
    """
    Parse expiration string to date.
    
    Supports formats like:
    - '2024-12-20'
    - '30 days'
    - 'next friday'
    """
    expiration_str = expiration_str.lower().strip()
    
    # ISO format
    if "-" in expiration_str:
        return datetime.fromisoformat(expiration_str).date()
    
    # Days format
    if "day" in expiration_str:
        days = int(expiration_str.split()[0])
        return (datetime.now() + timedelta(days=days)).date()
    
    # Default to 30 days
    return (datetime.now() + timedelta(days=30)).date()


def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format."""
    if not symbol:
        return False
    
    # Basic validation
    return symbol.isupper() and 1 <= len(symbol) <= 5 and symbol.isalpha()
