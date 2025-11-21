"""
Data Fetching Module
Handles all data fetching and caching logic
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import valuation


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_info(ticker_symbol):
    """Get cached stock info from yfinance"""
    ticker = yf.Ticker(ticker_symbol)
    return ticker.info


@st.cache_data(ttl=3600)
def get_cached_history(ticker_symbol, period="2y"):
    """Get cached historical data with moving averages"""
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)
    
    if not hist.empty:
        # Calculate moving averages
        hist['MA_20'] = hist['Close'].rolling(window=20).mean()
        hist['MA_50'] = hist['Close'].rolling(window=50).mean()
        hist['MA_200'] = hist['Close'].rolling(window=200).mean()
    
    return hist


def calculate_momentum_metrics(hist_data):
    """Calculate price momentum metrics"""
    if hist_data is None or hist_data.empty:
        return None
    
    try:
        current_price = hist_data['Close'].iloc[-1]
        
        # 3-month return
        if len(hist_data) >= 63:  # ~3 months of trading days
            price_3m_ago = hist_data['Close'].iloc[-63]
            return_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        else:
            return_3m = 0
        
        # 6-month return
        if len(hist_data) >= 126:  # ~6 months of trading days
            price_6m_ago = hist_data['Close'].iloc[-126]
            return_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        else:
            return_6m = 0
        
        # RS Ranking (simplified - in production, compare with market)
        if return_6m > 50:
            rs_ranking = "A (Top 20%)"
        elif return_6m > 20:
            rs_ranking = "B (Top 40%)"
        elif return_6m > 0:
            rs_ranking = "C (Top 60%)"
        elif return_6m > -20:
            rs_ranking = "D (Bottom 40%)"
        else:
            rs_ranking = "E (Bottom 20%)"
        
        # IBD RS Rating (0-99, simplified calculation)
        rs_rating = min(99, max(0, int(50 + return_6m)))
        
        return {
            'return_3m': return_3m,
            'return_6m': return_6m,
            'rs_ranking': rs_ranking,
            'rs_rating': rs_rating
        }
    except Exception as e:
        print(f"Error calculating momentum: {e}")
        return None


def calculate_all_valuations(info, wacc, growth_rate, terminal_growth):
    """Calculate all valuation metrics"""
    valuations = {}
    
    # DCF Valuation
    try:
        valuations['dcf_value'] = valuation.calculate_dcf(
            info.get('freeCashflow'),
            info.get('sharesOutstanding'),
            wacc,
            growth_rate,
            terminal_growth
        )
    except:
        valuations['dcf_value'] = None
    
    # PEG Ratio
    try:
        valuations['peg_ratio'] = valuation.calculate_peg_ratio(
            info.get('trailingPE') or info.get('forwardPE'),
            info.get('earningsGrowth')
        )
        
        # PEG-based fair value
        if valuations['peg_ratio'] and valuations['peg_ratio'] > 0:
            eps = info.get('trailingEps')
            earnings_growth = info.get('earningsGrowth')
            if eps and earnings_growth:
                fair_pe = earnings_growth * 100
                valuations['peg_value'] = eps * fair_pe
            else:
                valuations['peg_value'] = None
        else:
            valuations['peg_value'] = None
    except:
        valuations['peg_ratio'] = None
        valuations['peg_value'] = None
    
    # Peter Lynch Value
    try:
        valuations['lynch_value'] = valuation.calculate_peter_lynch_value(
            info.get('trailingEps'),
            info.get('earningsGrowth'),
            info.get('dividendYield')
        )
    except:
        valuations['lynch_value'] = None
    
    # Mean Reversion Value
    try:
        valuations['mr_value'] = valuation.calculate_mean_reversion_value(
            info.get('trailingEps')
        )
    except:
        valuations['mr_value'] = None
    
    # EV/EBITDA
    try:
        valuations['ev_ebitda'] = valuation.calculate_ev_ebitda(
            info.get('enterpriseValue'),
            info.get('ebitda')
        )
    except:
        valuations['ev_ebitda'] = None
    
    return valuations


def get_analyst_targets(info):
    """Get analyst target prices"""
    return {
        'target_mean': info.get('targetMeanPrice'),
        'target_high': info.get('targetHighPrice'),
        'target_low': info.get('targetLowPrice'),
        'num_analysts': info.get('numberOfAnalystOpinions'),
        'recommendation': info.get('recommendationKey')
    }
