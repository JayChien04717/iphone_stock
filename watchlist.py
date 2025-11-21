import json
import os
from datetime import datetime

WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    """Load watchlist from JSON file"""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_watchlist(watchlist):
    """Save watchlist to JSON file"""
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(watchlist, f, indent=2)

def add_to_watchlist(
    ticker,
    name,
    current_price,
    sector=None,
    industry=None,
    wacc=None,
    dcf_value=None,
    peg_ratio=None,
    lynch_value=None,
    mr_value=None,
    ev_ebitda=None,
    momentum=None,
):
    """Add a stock to the watchlist with comprehensive data.

    Sector and industry are optional because some data providers or tickers
    may not return those fields. Defaulting to ``None`` prevents runtime
    errors when callers omit them while still persisting the information
    when available.
    """
    watchlist = load_watchlist()
    
    # Check if already in watchlist
    for stock in watchlist:
        if stock['ticker'] == ticker:
            # Update existing entry
            stock['name'] = name
            stock['current_price'] = current_price
            stock['sector'] = sector
            stock['industry'] = industry
            stock['wacc'] = wacc
            stock['dcf_value'] = dcf_value
            stock['peg_ratio'] = peg_ratio
            stock['lynch_value'] = lynch_value
            stock['mr_value'] = mr_value
            stock['ev_ebitda'] = ev_ebitda
            stock['momentum'] = momentum
            stock['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_watchlist(watchlist)
            return False  # Already existed
    
    # Add new entry
    watchlist.append({
        'ticker': ticker,
        'name': name,
        'current_price': current_price,
        'sector': sector,
        'industry': industry,
        'wacc': wacc,
        'dcf_value': dcf_value,
        'peg_ratio': peg_ratio,
        'lynch_value': lynch_value,
        'mr_value': mr_value,
        'ev_ebitda': ev_ebitda,
        'momentum': momentum,
        'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_watchlist(watchlist)
    return True  # Newly added

def remove_from_watchlist(ticker):
    """Remove a stock from the watchlist"""
    watchlist = load_watchlist()
    watchlist = [stock for stock in watchlist if stock['ticker'] != ticker]
    save_watchlist(watchlist)

def is_in_watchlist(ticker):
    """Check if a ticker is in the watchlist"""
    watchlist = load_watchlist()
    return any(stock['ticker'] == ticker for stock in watchlist)

def get_watchlist():
    """Get all stocks in the watchlist (alias for load_watchlist)"""
    return load_watchlist()
