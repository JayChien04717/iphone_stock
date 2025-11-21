"""
AI Stock Scoring System
Comprehensive evaluation system scoring stocks 0-100 across multiple dimensions
"""

def calculate_valuation_score(current_price, dcf_value, peg_ratio, ev_ebitda, pe_ratio, info):
    """
    Valuation Attractiveness Score (0-25 points)
    Evaluates if stock is undervalued or overvalued
    """
    score = 0
    
    # 1. DCF vs Price (0-10 points)
    if dcf_value and current_price:
        discount = ((dcf_value - current_price) / current_price) * 100
        if discount > 30:  # >30% undervalued
            score += 10
        elif discount > 15:
            score += 8
        elif discount > 0:
            score += 6
        elif discount > -15:
            score += 4
        elif discount > -30:
            score += 2
        # else 0 points (>30% overvalued)
    
    # 2. PEG Ratio (0-8 points)
    if peg_ratio:
        if peg_ratio < 0.5:
            score += 8
        elif peg_ratio < 1.0:
            score += 6
        elif peg_ratio < 1.5:
            score += 4
        elif peg_ratio < 2.0:
            score += 2
        # else 0 points
    
    # 3. EV/EBITDA (0-7 points)
    if ev_ebitda:
        if ev_ebitda < 8:
            score += 7
        elif ev_ebitda < 12:
            score += 5
        elif ev_ebitda < 15:
            score += 3
        elif ev_ebitda < 20:
            score += 1
        # else 0 points
    
    return min(score, 25)


def calculate_financial_health_score(info, ticker):
    """
    Financial Health Score (0-20 points)
    Evaluates company's financial stability
    """
    score = 0
    
    # 1. Debt to Equity Ratio (0-6 points)
    total_debt = info.get('totalDebt', 0)
    market_cap = info.get('marketCap', 1)
    if market_cap > 0:
        debt_to_equity = total_debt / market_cap
        if debt_to_equity < 0.3:
            score += 6
        elif debt_to_equity < 0.5:
            score += 5
        elif debt_to_equity < 1.0:
            score += 3
        elif debt_to_equity < 2.0:
            score += 1
    
    # 2. Free Cash Flow (0-6 points)
    fcf = info.get('freeCashflow')
    if fcf:
        if fcf > 0:
            score += 6
            # Bonus for strong FCF
            if market_cap > 0 and (fcf / market_cap) > 0.05:  # >5% FCF yield
                score += 2
    
    # 3. ROE - Return on Equity (0-4 points)
    roe = info.get('returnOnEquity')
    if roe:
        if roe > 0.20:  # >20%
            score += 4
        elif roe > 0.15:
            score += 3
        elif roe > 0.10:
            score += 2
        elif roe > 0:
            score += 1
    
    # 4. Profit Margins (0-4 points)
    profit_margin = info.get('profitMargins')
    if profit_margin:
        if profit_margin > 0.20:
            score += 4
        elif profit_margin > 0.15:
            score += 3
        elif profit_margin > 0.10:
            score += 2
        elif profit_margin > 0:
            score += 1
    
    return min(score, 20)


def calculate_growth_score(info):
    """
    Growth Potential Score (0-20 points)
    Evaluates company's growth trajectory
    """
    score = 0
    
    # 1. Revenue Growth (0-8 points)
    revenue_growth = info.get('revenueGrowth')
    if revenue_growth:
        if revenue_growth > 0.30:  # >30%
            score += 8
        elif revenue_growth > 0.20:
            score += 6
        elif revenue_growth > 0.10:
            score += 4
        elif revenue_growth > 0:
            score += 2
    
    # 2. Earnings Growth (0-8 points)
    earnings_growth = info.get('earningsGrowth')
    if earnings_growth:
        if earnings_growth > 0.30:
            score += 8
        elif earnings_growth > 0.20:
            score += 6
        elif earnings_growth > 0.10:
            score += 4
        elif earnings_growth > 0:
            score += 2
    
    # 3. Earnings Quarterly Growth (0-4 points)
    earnings_quarterly_growth = info.get('earningsQuarterlyGrowth')
    if earnings_quarterly_growth:
        if earnings_quarterly_growth > 0.25:
            score += 4
        elif earnings_quarterly_growth > 0.15:
            score += 3
        elif earnings_quarterly_growth > 0.05:
            score += 2
        elif earnings_quarterly_growth > 0:
            score += 1
    
    return min(score, 20)


def calculate_momentum_score(momentum):
    """
    Momentum & Market Sentiment Score (0-20 points)
    Evaluates price momentum and relative strength
    """
    score = 0
    
    if not momentum:
        return 0
    
    # 1. IBD RS Rating (0-8 points)
    rs_rating = momentum.get('rs_rating', 0)
    if rs_rating >= 90:
        score += 8
    elif rs_rating >= 80:
        score += 7
    elif rs_rating >= 70:
        score += 5
    elif rs_rating >= 60:
        score += 3
    elif rs_rating >= 50:
        score += 1
    
    # 2. 6-Month Return (0-6 points)
    ret_6m = momentum.get('return_6m', 0)
    if ret_6m > 30:
        score += 6
    elif ret_6m > 15:
        score += 5
    elif ret_6m > 5:
        score += 3
    elif ret_6m > 0:
        score += 2
    elif ret_6m > -10:
        score += 1
    
    # 3. 3-Month Return (0-6 points)
    ret_3m = momentum.get('return_3m', 0)
    if ret_3m > 20:
        score += 6
    elif ret_3m > 10:
        score += 5
    elif ret_3m > 5:
        score += 3
    elif ret_3m > 0:
        score += 2
    elif ret_3m > -5:
        score += 1
    
    return min(score, 20)


def calculate_risk_score(info, current_price):
    """
    Risk Assessment Score (0-15 points)
    Lower risk = higher score
    """
    score = 15  # Start with full points, deduct for risks
    
    # 1. Beta (Volatility) - deduct up to 5 points
    beta = info.get('beta')
    if beta:
        if beta > 2.0:
            score -= 5
        elif beta > 1.5:
            score -= 3
        elif beta > 1.2:
            score -= 1
        # Beta < 1.2 is good, no deduction
    
    # 2. 52-Week Range Position - deduct up to 5 points
    high_52 = info.get('fiftyTwoWeekHigh')
    low_52 = info.get('fiftyTwoWeekLow')
    if high_52 and low_52 and current_price:
        position = (current_price - low_52) / (high_52 - low_52)
        if position > 0.95:  # Near 52-week high (risky)
            score -= 3
        elif position < 0.20:  # Near 52-week low (risky)
            score -= 2
        # 0.4-0.8 range is ideal, no deduction
    
    # 3. Analyst Recommendation - deduct up to 5 points
    recommendation = info.get('recommendationKey')
    if recommendation:
        if recommendation in ['strong_sell', 'sell']:
            score -= 5
        elif recommendation == 'hold':
            score -= 2
        elif recommendation == 'buy':
            score -= 0
        elif recommendation == 'strong_buy':
            score += 0  # No bonus, already at max
    
    return max(0, min(score, 15))


def calculate_overall_score(current_price, dcf_value, peg_ratio, ev_ebitda, pe_ratio, info, ticker, momentum):
    """
    Calculate comprehensive AI score (0-100)
    Returns dict with overall score, breakdown, and recommendation
    """
    
    # Calculate individual scores
    valuation = calculate_valuation_score(current_price, dcf_value, peg_ratio, ev_ebitda, pe_ratio, info)
    financial = calculate_financial_health_score(info, ticker)
    growth = calculate_growth_score(info)
    momentum_score = calculate_momentum_score(momentum)
    risk = calculate_risk_score(info, current_price)
    
    # Total score
    total = valuation + financial + growth + momentum_score + risk
    
    # Generate rating
    if total >= 90:
        rating = "🌟🌟🌟🌟🌟 強力買入"
        recommendation = "Strong Buy"
        color = "#00C853"
    elif total >= 75:
        rating = "🌟🌟🌟🌟 買入"
        recommendation = "Buy"
        color = "#64DD17"
    elif total >= 60:
        rating = "🌟🌟🌟 持有"
        recommendation = "Hold"
        color = "#FFD600"
    elif total >= 40:
        rating = "🌟🌟 觀望"
        recommendation = "Watch"
        color = "#FF6D00"
    else:
        rating = "🌟 避免"
        recommendation = "Avoid"
        color = "#D50000"
    
    # Generate key insights
    insights = []
    if valuation >= 20:
        insights.append("估值具吸引力")
    if financial >= 16:
        insights.append("財務健康")
    if growth >= 16:
        insights.append("高成長潛力")
    if momentum_score >= 16:
        insights.append("強勁動能")
    if risk >= 12:
        insights.append("風險可控")
    
    # Risk factors
    risk_factors = []
    if valuation < 10:
        risk_factors.append("估值偏高")
    if financial < 10:
        risk_factors.append("財務狀況需關注")
    if growth < 8:
        risk_factors.append("成長性不足")
    if momentum_score < 8:
        risk_factors.append("價格動能疲弱")
    if risk < 8:
        risk_factors.append("波動性較高")
    
    # Provide both legacy and UI-friendly keys so the rendering layer can
    # consume ``overall_score``/``key_insights`` while existing callers that
    # reference ``total_score``/``insights`` continue to work.
    return {
        'overall_score': total,
        'total_score': total,
        'rating': rating,
        'recommendation': recommendation,
        'color': color,
        'breakdown': {
            'valuation': valuation,
            'financial_health': financial,
            'growth': growth,
            'momentum': momentum_score,
            'risk': risk
        },
        'key_insights': insights,
        'insights': insights,
        'risk_factors': risk_factors if risk_factors else ["無重大風險"]
    }
