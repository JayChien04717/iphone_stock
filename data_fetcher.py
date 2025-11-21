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


@st.cache_data(ttl=3600)
def forecast_eps(ticker_symbol, years=5, custom_growth=None):
    """Forecast EPS for a given number of years using analyst data or custom growth."""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    earnings = ticker.earnings

    shares_outstanding = info.get('sharesOutstanding') or 0
    eps_history = []

    if earnings is not None and not earnings.empty and shares_outstanding:
        # Convert historical net income to EPS per share
        eps_history = (earnings['Earnings'] / shares_outstanding).tolist()

    trailing_eps = info.get('trailingEps')
    if trailing_eps:
        if not eps_history:
            eps_history = [trailing_eps]
        elif trailing_eps not in eps_history:
            eps_history.append(trailing_eps)

    base_eps = eps_history[-1] if eps_history else info.get('forwardEps') or trailing_eps

    # Growth preference: custom > analyst estimate > derived from forward EPS
    growth_rate = custom_growth
    if growth_rate is None:
        growth_rate = info.get('earningsGrowth')

    if growth_rate is None and base_eps and info.get('forwardEps'):
        try:
            growth_rate = (info['forwardEps'] / base_eps) - 1
        except Exception:
            growth_rate = None

    if growth_rate is None:
        growth_rate = 0.0

    start_year = (earnings.index[-1] + 1) if (earnings is not None and not earnings.empty) else pd.Timestamp.now().year + 1
    forecast = []
    if base_eps:
        for i in range(years):
            projected_eps = base_eps * ((1 + growth_rate) ** (i + 1))
            forecast.append({
                'year': int(start_year + i),
                'eps': projected_eps
            })

    return {
        'base_eps': base_eps,
        'growth_rate': growth_rate,
        'forecast': forecast,
        'shares_outstanding': shares_outstanding
    }


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


def calculate_all_valuations(
    ticker_symbol,
    info,
    wacc,
    growth_rate,
    terminal_growth,
    eps_forecast=None,
    eps_to_fcf_ratio=None,
    net_margin=None,
    target_pe=15.0
):
    """Calculate all valuation metrics using both trailing and forecasted EPS."""
    valuations = {}

    forecast_values = [entry['eps'] for entry in eps_forecast or []]
    eps_forwards = forecast_values[0] if forecast_values else None

    # DCF Valuation
    try:
        valuations['dcf_value'] = valuation.calculate_dcf(
            info.get('freeCashflow'),
            info.get('sharesOutstanding'),
            wacc,
            growth_rate,
            terminal_growth,
            eps_forecast=forecast_values,
            eps_to_fcf_ratio=eps_to_fcf_ratio,
            net_margin=net_margin
        )
    except Exception as e:
        print(f"DCF calculation failed for {ticker_symbol}: {e}")
        valuations['dcf_value'] = None

    # PEG Ratio (prefer forecast growth and EPS)
    try:
        growth_for_peg = valuation.derive_growth_from_forecast(eps_forecast, info.get('trailingEps'))
        if growth_for_peg is None:
            growth_for_peg = info.get('earningsGrowth')

        pe_to_use = info.get('forwardPE') or info.get('trailingPE')
        valuations['peg_ratio'] = valuation.calculate_peg_ratio(
            pe_to_use,
            growth_for_peg
        )

        if valuations['peg_ratio'] and valuations['peg_ratio'] > 0:
            eps_value = eps_forwards or info.get('trailingEps')
            valuations['peg_value'] = valuation.calculate_peg_value(
                eps_value,
                growth_for_peg
            )
        else:
            valuations['peg_value'] = None
    except Exception as e:
        print(f"PEG calculation failed for {ticker_symbol}: {e}")
        valuations['peg_ratio'] = None
        valuations['peg_value'] = None

    # Peter Lynch Value
    try:
        valuations['lynch_value'] = valuation.calculate_peter_lynch_value(
            info.get('trailingEps'),
            info.get('earningsGrowth'),
            info.get('dividendYield')
        )
    except Exception as e:
        print(f"Peter Lynch calculation failed for {ticker_symbol}: {e}")
        valuations['lynch_value'] = None

    # Mean Reversion Value (use forecast EPS if available)
    try:
        valuations['mr_value'] = valuation.calculate_mean_reversion_value(
            eps_forwards or info.get('trailingEps'),
            target_pe
        )
    except Exception as e:
        print(f"Mean reversion calculation failed for {ticker_symbol}: {e}")
        valuations['mr_value'] = None

    # EV/EBITDA
    try:
        valuations['ev_ebitda'] = valuation.calculate_ev_ebitda(
            info.get('enterpriseValue'),
            info.get('ebitda')
        )
    except Exception as e:
        print(f"EV/EBITDA calculation failed for {ticker_symbol}: {e}")
        valuations['ev_ebitda'] = None

    valuations['eps_forecast'] = eps_forecast
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
