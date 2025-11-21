import yfinance as yf
import pandas as pd
import numpy as np

def get_financials(ticker_symbol):
    """
    Fetches financial data for a given ticker.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        # Check if data is available
        if 'symbol' not in info:
             return None, "Invalid Ticker or No Data"
        return ticker, info
    except Exception as e:
        return None, str(e)

def calculate_dcf(ticker, info, assumptions):
    """
    Calculates Intrinsic Value using Discounted Cash Flow (DCF).
    Assumptions dict should contain: 'growth_rate', 'discount_rate', 'terminal_growth_rate'
    """
    try:
        free_cash_flow = info.get('freeCashflow')
        if free_cash_flow is None:
            # Try to calculate from cash flow statement if direct field is missing
            cashflow = ticker.cashflow
            if cashflow is not None and not cashflow.empty and 'Free Cash Flow' in cashflow.index:
                 free_cash_flow = cashflow.loc['Free Cash Flow'].iloc[0]
            else:
                return None # Cannot calculate without FCF

        growth_rate = assumptions['growth_rate'] / 100
        discount_rate = assumptions['discount_rate'] / 100
        terminal_growth_rate = assumptions['terminal_growth_rate'] / 100
        
        # Project FCF for next 5 years
        future_fcf = []
        for i in range(1, 6):
            fcf = free_cash_flow * ((1 + growth_rate) ** i)
            future_fcf.append(fcf)
            
        # Calculate Terminal Value
        terminal_value = (future_fcf[-1] * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
        
        # Discount Cash Flows to Present Value
        dcf_value = 0
        for i in range(0, 5):
            dcf_value += future_fcf[i] / ((1 + discount_rate) ** (i + 1))
            
        # Discount Terminal Value
        present_terminal_value = terminal_value / ((1 + discount_rate) ** 5)
        
        # Total Equity Value
        total_equity_value = dcf_value + present_terminal_value
        
        # Add Cash and Subtract Debt (Net Debt) - Simplified
        # Ideally: Enterprise Value -> Equity Value
        # Here we assume FCF is to Firm, so we need to adjust for debt/cash if we want Equity Value per share
        # BUT, yfinance 'freeCashflow' is often FCF to Equity or Firm? It's ambiguous. 
        # Standard DCF usually uses FCFF. Let's assume FCFF and adjust.
        
        total_cash = info.get('totalCash', 0)
        total_debt = info.get('totalDebt', 0)
        
        equity_value = total_equity_value + total_cash - total_debt
        
        shares_outstanding = info.get('sharesOutstanding')
        if not shares_outstanding:
            return None

        fair_value = equity_value / shares_outstanding
        return fair_value
    except Exception as e:
        print(f"DCF Error: {e}")
        return None

def calculate_peg_valuation(info):
    """
    Returns the PEG ratio and an implied valuation based on PEG=1.
    """
    # Try to get PEG from info, yfinance often uses 'trailingPegRatio' now
    peg_ratio = info.get('pegRatio')
    if peg_ratio is None:
        peg_ratio = info.get('trailingPegRatio')
        
    # Fallback: Calculate manually if missing
    # PEG = (P/E) / (Earnings Growth Rate * 100)
    if peg_ratio is None:
        pe = info.get('trailingPE')
        growth = info.get('earningsGrowth') # This is usually a decimal (e.g. 0.15 for 15%)
        if pe and growth and growth > 0:
            peg_ratio = pe / (growth * 100)
    
    current_price = info.get('currentPrice')
    
    if peg_ratio and current_price:
        # Implied Fair Value if PEG were 1.0 (Fairly Valued)
        # Price = PEG * Earnings * Growth
        # If PEG < 1, Undervalued. 
        # We can't strictly calculate a 'price' from PEG without knowing the 'fair' PEG.
        # Usually PEG < 1 is good.
        return peg_ratio
    return None

def calculate_graham_number(info):
    """
    Calculates Graham Number = Sqrt(22.5 * EPS * BVPS)
    """
    eps = info.get('trailingEps')
    bvps = info.get('bookValue')
    
    if eps and bvps and eps > 0 and bvps > 0:
        graham_number = np.sqrt(22.5 * eps * bvps)
        return graham_number
    return None

def calculate_peter_lynch_value(info):
    """
    Peter Lynch Fair Value = PEG of 1 implies P/E = Growth Rate.
    Fair Value = Expected Growth Rate * EPS.
    """
    # Use earningsGrowth or revenueGrowth as proxy if not available, 
    # but ideally we want long term growth estimate.
    # yfinance info has 'earningsGrowth' (quarterly). 
    # Let's try to use a growth estimate if available, or derive from PEG.
    # PEG = (P/E) / Growth => Growth = (P/E) / PEG
    
    pe_ratio = info.get('trailingPE')
    
    # Use our robust PEG calculation which handles fallbacks
    peg_ratio = calculate_peg_valuation(info)
    
    eps = info.get('trailingEps')
    
    if pe_ratio and peg_ratio and peg_ratio > 0:
        growth_rate = pe_ratio / peg_ratio
        # Lynch Fair Value = Growth Rate * EPS
        if eps:
            fair_value = growth_rate * eps
            return fair_value
            
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
