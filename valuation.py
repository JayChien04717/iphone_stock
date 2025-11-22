import yfinance as yf
import pandas as pd
import numpy as np


def calculate_dcf(
    free_cash_flow,
    shares_outstanding,
    discount_rate,
    growth_rate,
    terminal_growth_rate,
    eps_forecast=None,
    eps_to_fcf_ratio=None,
    net_margin=None
):
    """
    Calculates Intrinsic Value using Discounted Cash Flow to Equity (FCFE).
    
    Since yfinance 'freeCashflow' is typically Levered Free Cash Flow (FCFE),
    we do NOT adjust for Net Debt. The result is directly the Equity Value.

    Parameters
    ----------
    free_cash_flow: float
        Latest Levered Free Cash Flow (FCFE).
    shares_outstanding: float
        Share count for per-share calculations.
    discount_rate: float
        Cost of Equity (Required Return).
    growth_rate: float
        Growth rate for FCFE.
    terminal_growth_rate: float
        Terminal growth rate.
    eps_forecast: list[float]
        Forecast EPS per share sequence.
    eps_to_fcf_ratio: float
        Ratio to convert EPS to FCFE.
    net_margin: float
        Alternative ratio to approximate FCFE from EPS.
    """
    try:
        if not shares_outstanding:
            return None

        conversion_ratio = eps_to_fcf_ratio if eps_to_fcf_ratio is not None else net_margin

        if eps_forecast and conversion_ratio:
            projected_fcf = [eps * shares_outstanding * conversion_ratio for eps in eps_forecast]
        elif free_cash_flow is not None:
            projected_fcf = [free_cash_flow * ((1 + growth_rate) ** (i + 1)) for i in range(5)]
        else:
            return None

        if not projected_fcf:
            return None

        # Discount projected cash flows
        discounted = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(projected_fcf)]
        dcf_value = sum(discounted)

        # Terminal value using last projected FCF
        last_fcf = projected_fcf[-1]
        if discount_rate <= terminal_growth_rate:
            return None
        terminal_value = (last_fcf * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
        present_terminal_value = terminal_value / ((1 + discount_rate) ** len(projected_fcf))

        # Total Equity Value (Directly from FCFE)
        equity_value = dcf_value + present_terminal_value
        
        fair_value = equity_value / shares_outstanding
        return fair_value
    except Exception as e:
        print(f"DCF Error: {e}")
        return None


def derive_growth_from_forecast(forecast_series, trailing_eps=None):
    """Derive CAGR from a forecast EPS series using trailing EPS as the base."""
    if not forecast_series or trailing_eps is None or trailing_eps <= 0:
        return None

    eps_values = [entry['eps'] if isinstance(entry, dict) else entry for entry in forecast_series]
    if not eps_values:
        return None

    end_eps = eps_values[-1]
    periods = len(eps_values)
    if end_eps <= 0 or periods == 0:
        return None

    try:
        growth_rate = (end_eps / trailing_eps) ** (1 / periods) - 1
        return growth_rate
    except Exception:
        return None


def calculate_peg_ratio(pe_ratio, earnings_growth):
    """Calculate PEG ratio given P/E and earnings growth (decimal)."""
    if pe_ratio and earnings_growth and earnings_growth > 0:
        return pe_ratio / (earnings_growth * 100)
    return None


def calculate_peg_value(eps, earnings_growth):
    """Calculate fair value using PEG=1 with EPS and earnings growth (decimal)."""
    if eps and earnings_growth and earnings_growth > 0:
        fair_pe = earnings_growth * 100
        return eps * fair_pe
    return None


def calculate_graham_number(eps, book_value):
    """Calculates Graham Number = sqrt(22.5 * EPS * BVPS)."""
    if eps and book_value and eps > 0 and book_value > 0:
        graham_number = np.sqrt(22.5 * eps * book_value)
        return graham_number
    return None


def calculate_peter_lynch_value(eps, earnings_growth, dividend_yield=None):
    """Peter Lynch fair value approximation using growth and EPS."""
    if eps and earnings_growth:
        growth_component = earnings_growth * 100
        dividend_boost = (dividend_yield * 100) if dividend_yield else 0
        return eps * (growth_component + dividend_boost)
    return None


def calculate_mean_reversion_value(eps, target_pe=15.0):
    """Fair value from mean reversion to target P/E using EPS."""
    if eps and target_pe:
        return eps * target_pe
    return None


def calculate_ev_ebitda(enterprise_value, ebitda):
    """Calculate EV/EBITDA multiple."""
    if enterprise_value and ebitda:
        return enterprise_value / ebitda
    return None

def calculate_ddm(info, assumptions):
    """
    Calculates value based on Dividend Discount Model (Gordon Growth Model).
    Value = D1 / (r - g)
    D1 = Next year's dividend
    r = Required rate of return (cost of equity)
    g = Dividend growth rate
    """
    try:
        dividend_rate = info.get('dividendRate') # Annual dividend
        if not dividend_rate:
            return None
            
        required_return = assumptions.get('required_return', 10.0) / 100
        dividend_growth = assumptions.get('dividend_growth', 5.0) / 100
        
        if required_return <= dividend_growth:
            return None # Model invalid if g >= r
            
        # Assume current dividend is D0, so D1 = D0 * (1 + g)
        d1 = dividend_rate * (1 + dividend_growth)
        
        value = d1 / (required_return - dividend_growth)
        return value
    except Exception as e:
        print(f"DDM Error: {e}")
        return None

def calculate_mean_reversion(info, assumptions):
    """
    Calculates value based on Mean Reversion of P/E Ratio.
    Value = EPS * Target P/E
    """
    try:
        eps = info.get('trailingEps')
        if not eps or eps <= 0:
            return None
            
        target_pe = assumptions.get('target_pe', 15.0)
        
        value = eps * target_pe
        return value
    except Exception as e:
        print(f"Mean Reversion Error: {e}")
        return None

def get_historical_data(ticker, period='1y'):
    """
    Fetches historical price data for the given period.
    """
    try:
        hist = ticker.history(period=period)
        return hist
    except Exception as e:
        print(f"History Error: {e}")
        return None

def calculate_moving_averages(data):
    """
    Calculates 5, 20, 60, 120 day Moving Averages.
    """
    try:
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA60'] = data['Close'].rolling(window=60).mean()
        data['MA120'] = data['Close'].rolling(window=120).mean()
        return data
    except Exception as e:
        print(f"MA Error: {e}")
        return data


def calculate_wacc(ticker, info):
    """
    Calculates Weighted Average Cost of Capital (WACC).
    WACC = (E/V * Re) + (D/V * Rd * (1 - T))
    E = Market Value of Equity
    V = Total Value (Equity + Debt)
    Re = Cost of Equity
    D = Market Value of Debt
    Rd = Cost of Debt
    T = Tax Rate
    """
    try:
        # 1. Cost of Equity (Re) = Risk Free Rate + Beta * Equity Risk Premium
        # Risk Free Rate: 10 Year Treasury Yield (^TNX)
        tnx = yf.Ticker("^TNX")
        # Get the latest close price for yield (e.g. 4.5 means 4.5%)
        hist = tnx.history(period="5d")
        if hist.empty:
            risk_free_rate = 0.04 # Fallback 4%
        else:
            risk_free_rate = hist['Close'].iloc[-1] / 100
            
        beta = info.get('beta')
        if beta is None:
            beta = 1.0 # Market average fallback
            
        equity_risk_premium = 0.05 # Historical average ~5%
        
        cost_of_equity = risk_free_rate + (beta * equity_risk_premium)
        
        # 2. Cost of Debt (Rd)
        # Interest Expense / Total Debt
        # We need financials for Interest Expense
        financials = ticker.financials
        interest_expense = 0
        if financials is not None and 'Interest Expense' in financials.index:
             # Interest Expense is usually negative in statements, take absolute
             interest_expense = abs(financials.loc['Interest Expense'].iloc[0])
             
        total_debt = info.get('totalDebt')
        if total_debt and total_debt > 0:
            cost_of_debt = interest_expense / total_debt
        else:
            cost_of_debt = 0.04 # Fallback assumption if no debt info
            
        # 3. Tax Rate
        # Tax Provision / Pretax Income
        tax_rate = 0.21 # Corporate Tax Rate fallback
        if financials is not None and 'Tax Provision' in financials.index and 'Pretax Income' in financials.index:
            tax_provision = financials.loc['Tax Provision'].iloc[0]
            pretax_income = financials.loc['Pretax Income'].iloc[0]
            if pretax_income and pretax_income != 0:
                tax_rate = tax_provision / pretax_income
                
        # Clamp tax rate to reasonable bounds (0 to 40%)
        tax_rate = max(0.0, min(tax_rate, 0.40))
        
        # 4. Capital Structure Weights
        market_cap = info.get('marketCap')
        if not market_cap:
            return 0.10 # Return 10% fallback if critical info missing
            
        if not total_debt:
            total_debt = 0
            
        total_value = market_cap + total_debt
        
        weight_equity = market_cap / total_value
        weight_debt = total_debt / total_value
        
        # WACC Calculation
        wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
        
        return wacc * 100 # Return as percentage
        
    except Exception as e:
        print(f"WACC Error: {e}")
        return 10.0 # Fallback default


def calculate_price_momentum(ticker_symbol):
    """
    Calculates price momentum metrics:
    - 3-month return
    - 6-month return
    - Relative Strength (RS) vs S&P 500
    - RS Ranking (percentile interpretation)
    - IBD-style RS Rating (0-99 percentile ranking)
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Fetch 13 months of data for IBD calculation (12M + buffer)
        hist = ticker.history(period="13mo")
        
        if hist.empty or len(hist) < 60:
            return None
        
        # Get current price and historical prices
        current_price = hist['Close'].iloc[-1]
        
        # Calculate 3-month return (approximately 63 trading days)
        days_3m = min(63, len(hist) - 1)
        price_3m_ago = hist['Close'].iloc[-days_3m - 1]
        return_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        
        # Calculate 6-month return (approximately 126 trading days)
        days_6m = min(126, len(hist) - 1)
        price_6m_ago = hist['Close'].iloc[-days_6m - 1]
        return_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        
        # Calculate 12-month return for IBD RS Rating
        days_12m = min(252, len(hist) - 1)
        price_12m_ago = hist['Close'].iloc[-days_12m - 1]
        return_12m = ((current_price - price_12m_ago) / price_12m_ago) * 100
        
        # IBD RS Rating: Weighted performance
        # IBD uses: 40% weight on recent quarter, 20% on 2 quarters ago, 
        # 20% on 3 quarters ago, 20% on 4 quarters ago
        # Simplified: 40% on 3M, 20% on 3-6M, 20% on 6-9M, 20% on 9-12M
        
        # Calculate quarterly returns
        days_9m = min(189, len(hist) - 1)
        price_9m_ago = hist['Close'].iloc[-days_9m - 1] if days_9m < len(hist) - 1 else price_12m_ago
        
        q1_return = return_3m  # Most recent quarter
        q2_return = ((price_3m_ago - price_6m_ago) / price_6m_ago) * 100 if days_6m < len(hist) - 1 else 0
        q3_return = ((price_6m_ago - price_9m_ago) / price_9m_ago) * 100 if days_9m < len(hist) - 1 else 0
        q4_return = ((price_9m_ago - price_12m_ago) / price_12m_ago) * 100 if days_12m < len(hist) - 1 else 0
        
        # Weighted composite score (IBD method)
        ibd_composite = (0.4 * q1_return) + (0.2 * q2_return) + (0.2 * q3_return) + (0.2 * q4_return)
        
        # Convert to percentile (0-99)
        # Since we don't have access to all stocks, we'll use a heuristic:
        # Map the composite score to a 0-99 scale
        # Excellent performance (>50%) = 90-99
        # Good (20-50%) = 70-89
        # Average (0-20%) = 50-69
        # Below average (-20-0%) = 30-49
        # Poor (<-20%) = 0-29
        
        if ibd_composite >= 50:
            rs_rating = min(99, 90 + int((ibd_composite - 50) / 10))
        elif ibd_composite >= 20:
            rs_rating = 70 + int((ibd_composite - 20) / 1.5)
        elif ibd_composite >= 0:
            rs_rating = 50 + int(ibd_composite)
        elif ibd_composite >= -20:
            rs_rating = 30 + int((ibd_composite + 20) / 1.0)
        else:
            rs_rating = max(0, int(30 + ibd_composite + 20))
        
        rs_rating = max(0, min(99, rs_rating))  # Clamp to 0-99
        
        # Calculate Relative Strength vs S&P 500
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="13mo")
        
        if not spy_hist.empty and len(spy_hist) >= days_6m:
            spy_current = spy_hist['Close'].iloc[-1]
            spy_6m_ago = spy_hist['Close'].iloc[-days_6m - 1]
            spy_return_6m = ((spy_current - spy_6m_ago) / spy_6m_ago) * 100
            
            # Relative Strength = Stock Return - Market Return
            relative_strength = return_6m - spy_return_6m
            
            # RS Ranking interpretation
            if relative_strength > 20:
                rs_rank = "Very Strong"
            elif relative_strength > 10:
                rs_rank = "Strong"
            elif relative_strength > -10:
                rs_rank = "Neutral"
            elif relative_strength > -20:
                rs_rank = "Weak"
            else:
                rs_rank = "Very Weak"
        else:
            relative_strength = None
            rs_rank = "N/A"
        
        return {
            'return_3m': return_3m,
            'return_6m': return_6m,
            'relative_strength': relative_strength,
            'rs_ranking': rs_rank,
            'rs_rating': rs_rating  # IBD-style 0-99 rating
        }
        
    except Exception as e:
        print(f"Momentum Error: {e}")
        return None
