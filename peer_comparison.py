"""
Industry Peer Comparison Module
Compares a stock against its industry peers
"""
import yfinance as yf
import pandas as pd
import numpy as np
import data_fetcher

def get_industry_peers(ticker_symbol, info, max_peers=10):
    """
    Get industry peer companies
    First tries Finnhub API, then falls back to hardcoded list
    """
    # Try to get peers from Finnhub API first
    try:
        from api_provider import api_provider
        finnhub_peers = api_provider.get_peers(ticker_symbol)
        if finnhub_peers:
            return finnhub_peers[:max_peers]
    except Exception as e:
        print(f"Finnhub API not available, using fallback: {e}")
    
    # Fallback to hardcoded peer map
    sector = info.get('sector', '')
    industry = info.get('industry', '')
    
    # Common peers by sector (hardcoded for now - in production, use an API)
    # This is a simplified approach
    peer_map = {
        'AAPL': ['MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA'],
        'MSFT': ['AAPL', 'GOOGL', 'META', 'NVDA', 'ORCL'],
        'GOOGL': ['AAPL', 'MSFT', 'META', 'AMZN', 'NVDA'],
        'TSLA': ['F', 'GM', 'RIVN', 'LCID', 'NIO'],
        'NVDA': ['AMD', 'INTC', 'QCOM', 'AVGO', 'TSM'],
        'AMD': ['NVDA', 'INTC', 'QCOM', 'AVGO', 'MU'],
        'JPM': ['BAC', 'WFC', 'C', 'GS', 'MS'],
        'BAC': ['JPM', 'WFC', 'C', 'USB', 'PNC'],
        'KO': ['PEP', 'MNST', 'DPS', 'KDP', 'CELH'],
        'PEP': ['KO', 'MNST', 'DPS', 'KDP', 'CELH'],
        'WMT': ['TGT', 'COST', 'HD', 'LOW', 'AMZN'],
        'AMZN': ['WMT', 'TGT', 'COST', 'EBAY', 'SHOP'],
        'JNJ': ['PFE', 'UNH', 'ABBV', 'MRK', 'LLY'],
        'PFE': ['JNJ', 'MRK', 'ABBV', 'LLY', 'BMY'],
    }
    
    # Get predefined peers if available
    peers = peer_map.get(ticker_symbol.upper(), [])
    
    # If no predefined peers, return empty list
    # In production, you would query an API here
    return peers[:max_peers]


def get_peer_metrics(ticker_symbol):
    """
    Get key metrics for a single ticker
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Calculate PEG if not available
        peg_ratio = info.get('pegRatio')
        if not peg_ratio or peg_ratio == 0:
            # Try to calculate PEG manually
            pe_ratio = info.get('trailingPE') or info.get('forwardPE')
            earnings_growth = info.get('earningsGrowth')
            
            if pe_ratio and earnings_growth and earnings_growth > 0:
                # PEG = P/E / (Earnings Growth * 100)
                peg_ratio = pe_ratio / (earnings_growth * 100)
        
        # Get QOQ revenue growth using data_fetcher
        revenue_growth_quarterly = data_fetcher.get_quarterly_growth(ticker_symbol)
        
        return {
            'ticker': ticker_symbol,
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': peg_ratio,
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'ev_ebitda': info.get('enterpriseToEbitda'),
            'profit_margin': info.get('profitMargins'),
            'roe': info.get('returnOnEquity'),
            'revenue_growth': info.get('revenueGrowth'),  # YOY
            'revenue_growth_quarterly': revenue_growth_quarterly,  # QOQ (calculated)
            'earnings_growth': info.get('earningsGrowth'),
            'earnings_growth_quarterly': info.get('earningsQuarterlyGrowth'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'beta': info.get('beta'),
            'dividend_yield': info.get('dividendYield'),
        }
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None


def compare_with_peers(ticker_symbol, info):
    """
    Compare the stock with its industry peers
    Returns a DataFrame with comparison metrics
    """
    # Get peer list
    peers = get_industry_peers(ticker_symbol, info)
    
    if not peers:
        return None, None
    
    # Get metrics for the main stock
    main_metrics = get_peer_metrics(ticker_symbol)
    
    # Get metrics for all peers
    peer_metrics = []
    for peer in peers:
        metrics = get_peer_metrics(peer)
        if metrics:
            peer_metrics.append(metrics)
    
    if not peer_metrics:
        return None, None
    
    # Create DataFrame
    all_metrics = [main_metrics] + peer_metrics
    df = pd.DataFrame(all_metrics)
    
    # Calculate industry statistics
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    industry_stats = {}
    
    for col in numeric_columns:
        if col != 'market_cap':  # Exclude market cap from averaging
            industry_stats[f'{col}_mean'] = df[col].mean()
            industry_stats[f'{col}_median'] = df[col].median()
            industry_stats[f'{col}_min'] = df[col].min()
            industry_stats[f'{col}_max'] = df[col].max()
    
    return df, industry_stats


def calculate_peer_ranking(ticker_symbol, df):
    """
    Calculate ranking of the stock among its peers
    Returns dict with rankings for each metric
    """
    if df is None or df.empty:
        return None
    
    rankings = {}
    
    # Metrics where lower is better
    lower_is_better = ['pe_ratio', 'forward_pe', 'peg_ratio', 'ev_ebitda', 
                       'price_to_book', 'price_to_sales', 'debt_to_equity', 'beta']
    
    # Metrics where higher is better
    higher_is_better = ['roe', 'profit_margin', 'revenue_growth', 'earnings_growth',
                       'current_ratio', 'dividend_yield']
    
    main_stock_idx = df[df['ticker'] == ticker_symbol].index[0]
    
    for col in df.select_dtypes(include=[np.number]).columns:
        if col == 'market_cap':
            continue
            
        if col in lower_is_better:
            # Rank ascending (lower is better)
            df_sorted = df.sort_values(col, ascending=True)
        elif col in higher_is_better:
            # Rank descending (higher is better)
            df_sorted = df.sort_values(col, ascending=False)
        else:
            continue
        
        # Find position (1-indexed)
        position = df_sorted.index.get_loc(main_stock_idx) + 1
        total = len(df_sorted)
        
        rankings[col] = {
            'position': position,
            'total': total,
            'percentile': (total - position + 1) / total * 100
        }
    
    return rankings


def get_comparison_summary(ticker_symbol, info):
    """
    Get a complete comparison summary
    Returns comparison DataFrame, industry stats, and rankings
    """
    df, industry_stats = compare_with_peers(ticker_symbol, info)
    
    if df is None:
        return None, None, None
    
    rankings = calculate_peer_ranking(ticker_symbol, df)
    
    return df, industry_stats, rankings
