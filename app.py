import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import valuation
import watchlist
import ai_scoring
import peer_comparison

st.set_page_config(page_title="Stock Valuation Pro", layout="wide", initial_sidebar_state="expanded")

# Mobile-optimized CSS
st.markdown("""
<style>
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        /* Reduce padding on mobile */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Make metrics more compact */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
        }
        
        /* Adjust header sizes */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* Make buttons more touch-friendly */
        .stButton button {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            min-height: 44px;  /* iOS recommended touch target */
        }
        
        /* Optimize sidebar for mobile */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        /* Make tabs more touch-friendly */
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }
        
        /* Improve table readability on mobile */
        .dataframe {
            font-size: 0.75rem;
        }
        
        /* Make expanders more touch-friendly */
        .streamlit-expanderHeader {
            font-size: 0.95rem;
            padding: 0.75rem;
        }
    }
    
    /* General improvements for all devices */
    .stButton button {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Improve metric card appearance */
    [data-testid="stMetricValue"] {
        font-weight: 600;
    }
    
    /* Better spacing for columns */
    [data-testid="column"] {
        padding: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for "Commercial Grade" look
# Removed hardcoded colors to support Dark Mode
st.markdown("""
<style>
    .stMetric {
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.title("Stock Valuation Pro")
st.markdown("### Advanced Long-Term Valuation & Analysis")

# --- Caching Wrappers ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def get_cached_info(ticker_symbol):
    # We only cache the data (info dict), not the Ticker object
    ticker, info = valuation.get_financials(ticker_symbol)
    return info

@st.cache_data(ttl=3600)
def get_cached_history(ticker_symbol, period):
    # Cache historical data (DataFrame is serializable)
    import yfinance as yf
    t = yf.Ticker(ticker_symbol)
    return valuation.get_historical_data(t, period)

# Sidebar Inputs
st.sidebar.header("Configuration")

# Page selector
page = st.sidebar.radio("📊 Navigation", ["Stock Analysis", "📋 My Watchlist"], label_visibility="visible")

st.sidebar.markdown("---")

ticker_symbol = st.sidebar.text_input("Stock Ticker", value="AAPL", help="Enter the stock symbol (e.g., AAPL, MSFT).").upper()

# Initialize Session State for Sliders
if 'wacc' not in st.session_state:
    st.session_state.wacc = 10.0
if 'target_pe' not in st.session_state:
    st.session_state.target_pe = 15.0

# Estimate Inputs Button
if st.sidebar.button("Estimate Inputs (Auto-Fill)"):
    with st.spinner("Estimating WACC and PE..."):
        try:
            # We need to fetch data here to estimate
            import yfinance as yf
            t = yf.Ticker(ticker_symbol)
            info = t.info
            
            # Calculate WACC
            estimated_wacc = valuation.calculate_wacc(t, info)
            st.session_state.wacc = round(estimated_wacc, 1)
            
            # Get PE
            pe = info.get('trailingPE')
            if pe:
                st.session_state.target_pe = round(pe, 1)
                
            st.sidebar.success(f"Estimated WACC: {st.session_state.wacc}%, PE: {st.session_state.target_pe}")
            st.sidebar.markdown(f"[:mag: Search WACC for {ticker_symbol} on Google](https://www.google.com/search?q={ticker_symbol}+WACC)", unsafe_allow_html=True)
        except Exception as e:
            st.sidebar.error(f"Could not estimate: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("Valuation Assumptions")

with st.sidebar.expander("DCF Settings", expanded=False):
    growth_rate = st.number_input("Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5, help="Expected annual growth rate of Free Cash Flow for the next 5 years.")
    # Use session state for default value
    discount_rate = st.number_input("Discount Rate (WACC) (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.wacc), step=0.1, help="Weighted Average Cost of Capital. The rate used to discount future cash flows.")
    terminal_growth_rate = st.number_input("Terminal Growth (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1, help="Growth rate of the company forever after the projection period.")

with st.sidebar.expander("Mean Reversion Settings", expanded=False):
    # Use session state for default value
    target_pe = st.number_input("Target P/E Ratio", 5.0, 1000.0, st.session_state.target_pe, 0.5, help="The Price-to-Earnings ratio you expect the stock to revert to.")

# Initialize session state for analysis
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'analyzed_ticker' not in st.session_state:
    st.session_state.analyzed_ticker = ""

# Analyze Button Logic
if st.sidebar.button("Analyze Stock", type="primary"):
    st.session_state.analyzed = True
    st.session_state.analyzed_ticker = ticker_symbol

# Main Application Logic
if st.session_state.analyzed:
    # Use the ticker that was analyzed, not just the current input (unless re-analyzed)
    active_ticker = st.session_state.analyzed_ticker
    
    with st.spinner(f"Analyzing {active_ticker}..."):
        # Use cached function for data
        info = get_cached_info(active_ticker)
        
        # Re-create ticker object (lightweight) for passing to functions if needed
        import yfinance as yf
        ticker = yf.Ticker(active_ticker)
        
        if info is None or isinstance(info, str):
            st.error(f"Error fetching data: {info}")
        else:
            # Top Level Metrics
            st.header(f"{info.get('shortName', active_ticker)} ({active_ticker})")
            
            # Improved Header Layout to prevent text truncation
            # Give Current Price enough space, Beta less, and Info the rest
            c_price, c_beta, c_info = st.columns([1.2, 0.8, 3])
            
            with c_price:
                current_price = info.get('currentPrice')
                st.metric("Current Price", f"${current_price}")
            
            with c_beta:
                beta_val = info.get('beta')
                if isinstance(beta_val, (int, float)):
                    st.metric("Beta", f"{beta_val:.1f}")
                else:
                    st.metric("Beta", "N/A")
            
            with c_info:
                st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
                st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
            
            # Price Momentum Section
            st.markdown("### 📈 Price Momentum")
            momentum = valuation.calculate_price_momentum(active_ticker)
            
            if momentum:
                # Use container with custom styling to prevent truncation
                with st.container():
                    # First row: Returns
                    col1, col2 = st.columns(2)
                    
                    # 3-month return
                    with col1:
                        ret_3m = momentum['return_3m']
                        st.metric("3M Return", f"{ret_3m:+.2f}%", 
                                 delta=None if ret_3m == 0 else ("Positive" if ret_3m > 0 else "Negative"),
                                 delta_color="normal" if ret_3m > 0 else "inverse")
                    
                    # 6-month return
                    with col2:
                        ret_6m = momentum['return_6m']
                        st.metric("6M Return", f"{ret_6m:+.2f}%",
                                 delta=None if ret_6m == 0 else ("Positive" if ret_6m > 0 else "Negative"),
                                 delta_color="normal" if ret_6m > 0 else "inverse")
                    
                    # Second row: Rankings
                    col3, col4 = st.columns(2)
                    
                    # RS Ranking
                    with col3:
                        rs_rank = momentum['rs_ranking']
                        # Color based on ranking
                        if rs_rank in ["Very Strong", "Strong"]:
                            st.metric("RS Ranking", rs_rank, "💪", delta_color="off")
                        elif rs_rank == "Neutral":
                            st.metric("RS Ranking", rs_rank, "➡️", delta_color="off")
                        else:
                            st.metric("RS Ranking", rs_rank, "⚠️", delta_color="off")
                    
                    # IBD RS Rating (0-99)
                    with col4:
                        rs_rating = momentum.get('rs_rating', 0)
                        if rs_rating >= 80:
                            rating_status = "🔥 Excellent"
                            rating_color = "normal"
                        elif rs_rating >= 70:
                            rating_status = "✅ Strong"
                            rating_color = "normal"
                        elif rs_rating >= 50:
                            rating_status = "➡️ Average"
                            rating_color = "off"
                        else:
                            rating_status = "⚠️ Weak"
                            rating_color = "inverse"
                        
                        st.metric("IBD RS Rating", f"{rs_rating}/99", rating_status, delta_color=rating_color)
            else:
                st.info("Momentum data not available for this ticker.")

            st.markdown("---")
            
            # Calculate all valuations first (needed for AI score)
            dcf_assumptions = {'growth_rate': growth_rate, 'discount_rate': discount_rate, 'terminal_growth_rate': terminal_growth_rate}
            dcf_value = valuation.calculate_dcf(ticker, info, dcf_assumptions)
            
            peg_ratio = valuation.calculate_peg_valuation(info)
            lynch_value = valuation.calculate_peter_lynch_value(info)
            
            mr_assumptions = {'target_pe': target_pe}
            mr_value = valuation.calculate_mean_reversion(info, mr_assumptions)
            
            # EV/EBITDA
            ev_ebitda = info.get('enterpriseToEbitda')
            
            # AI Stock Score Section
            st.markdown("### 🤖 AI 綜合評分")
            
            # Calculate AI score
            ai_score = ai_scoring.calculate_overall_score(
                current_price=current_price,
                dcf_value=dcf_value,
                peg_ratio=peg_ratio,
                ev_ebitda=ev_ebitda,
                pe_ratio=info.get('trailingPE'),
                info=info,
                ticker=ticker,
                momentum=momentum
            )
            
            # Display score card
            score_col1, score_col2 = st.columns([1, 2])
            
            with score_col1:
                # Big score display
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background: linear-gradient(135deg, {ai_score['color']}22, {ai_score['color']}44);'>
                    <h1 style='font-size: 72px; margin: 0; color: {ai_score['color']};'>{ai_score['total_score']}</h1>
                    <p style='font-size: 24px; margin: 10px 0;'>{ai_score['rating']}</p>
                    <p style='font-size: 18px; font-weight: bold;'>{ai_score['recommendation']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with score_col2:
                st.markdown("#### 📊 評分細項")
                breakdown = ai_score['breakdown']
                
                # Progress bars for each dimension
                st.markdown(f"**估值吸引力:** {breakdown['valuation']}/25")
                st.progress(breakdown['valuation'] / 25)
                
                st.markdown(f"**財務健康度:** {breakdown['financial_health']}/20")
                st.progress(breakdown['financial_health'] / 20)
                
                st.markdown(f"**成長潛力:** {breakdown['growth']}/20")
                st.progress(breakdown['growth'] / 20)
                
                st.markdown(f"**價格動能:** {breakdown['momentum']}/20")
                st.progress(breakdown['momentum'] / 20)
                
                st.markdown(f"**風險控制:** {breakdown['risk']}/15")
                st.progress(breakdown['risk'] / 15)
            
            # Insights and Risk Factors
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                st.markdown("#### ✅ 關鍵優勢")
                if ai_score['insights']:
                    for insight in ai_score['insights']:
                        st.markdown(f"- {insight}")
                else:
                    st.markdown("- 無明顯優勢")
            
            with insight_col2:
                st.markdown("#### ⚠️ 風險因素")
                for risk in ai_score['risk_factors']:
                    st.markdown(f"- {risk}")
            
            st.markdown("---")
            
            # Tabs for Layout
            tab_val, tab_chart, tab_data, tab_peers = st.tabs(["Valuation Models", "Interactive Chart", "Financial Data", "🏢 Industry Comparison"])
            
            with tab_val:
                st.subheader("Fair Value Estimates")
                
                # Display in Grid
                c1, c2 = st.columns(2)
                c3, c4 = st.columns(2)
                c5, c6 = st.columns(2)
                
                def display_metric(col, label, value, current):
                    if value:
                        delta = ((value - current) / current) * 100
                        col.metric(label, f"${value:.2f}", f"{delta:.1f}%")
                    else:
                        col.metric(label, "N/A")

                display_metric(c1, "DCF Fair Value", dcf_value, current_price)
                
                if peg_ratio:
                    status = "Undervalued" if peg_ratio < 1 else "Overvalued"
                    c2.metric("PEG Ratio", f"{peg_ratio:.2f}", status, delta_color="inverse")
                else:
                    c2.metric("PEG Ratio", "N/A")
                
                # EV/EBITDA
                if ev_ebitda:
                    # Generally, EV/EBITDA < 10 is considered good, but varies by industry
                    status = "Good" if ev_ebitda < 10 else "High"
                    c3.metric("EV/EBITDA", f"{ev_ebitda:.2f}", status, delta_color="inverse")
                else:
                    c3.metric("EV/EBITDA", "N/A")
                    
                display_metric(c4, "Peter Lynch Value", lynch_value, current_price)
                display_metric(c5, "Mean Reversion (Fair PE)", mr_value, current_price)
                
                # Analyst Target Price Section
                st.markdown("---")
                st.markdown("#### 📊 分析師目標價 (Analyst Consensus)")
                
                target_mean = info.get('targetMeanPrice')
                target_high = info.get('targetHighPrice')
                target_low = info.get('targetLowPrice')
                num_analysts = info.get('numberOfAnalystOpinions')
                recommendation = info.get('recommendationKey')
                
                if target_mean:
                    analyst_col1, analyst_col2, analyst_col3 = st.columns(3)
                    
                    with analyst_col1:
                        delta = ((target_mean - current_price) / current_price) * 100
                        st.metric("平均目標價 (1Y Target)", f"${target_mean:.2f}", f"{delta:+.1f}%")
                    
                    with analyst_col2:
                        if target_high and target_low:
                            st.metric("目標價範圍", f"${target_low:.2f} - ${target_high:.2f}")
                        else:
                            st.metric("目標價範圍", "N/A")
                    
                    with analyst_col3:
                        if num_analysts:
                            rec_text = {
                                'strong_buy': '🟢 強力買入',
                                'buy': '🟢 買入',
                                'hold': '🟡 持有',
                                'sell': '🔴 賣出',
                                'strong_sell': '🔴 強力賣出'
                            }.get(recommendation, recommendation or 'N/A')
                            st.metric(f"分析師建議 ({num_analysts}位)", rec_text)
                        else:
                            st.metric("分析師建議", recommendation or "N/A")
                else:
                    st.info("此股票暫無分析師目標價數據")

                # --- Valuation Comparison Chart ---
                st.markdown("### Valuation Comparison")
                
                # Prepare data for chart
                comparison_data = {
                    'Method': ['Current Price'],
                    'Value': [current_price],
                    'Color': ['#333333'] # Dark Grey for Price
                }
                
                if dcf_value: 
                    comparison_data['Method'].append('DCF')
                    comparison_data['Value'].append(dcf_value)
                    comparison_data['Color'].append('#2ecc71' if dcf_value > current_price else '#e74c3c')
                
                if lynch_value:
                    comparison_data['Method'].append('Lynch Value')
                    comparison_data['Value'].append(lynch_value)
                    comparison_data['Color'].append('#2ecc71' if lynch_value > current_price else '#e74c3c')

                if mr_value:
                    comparison_data['Method'].append('Mean Reversion')
                    comparison_data['Value'].append(mr_value)
                    comparison_data['Color'].append('#2ecc71' if mr_value > current_price else '#e74c3c')
                
                comp_df = pd.DataFrame(comparison_data)
                
                fig_comp = go.Figure(go.Bar(
                    x=comp_df['Method'],
                    y=comp_df['Value'],
                    marker_color=comp_df['Color'],
                    text=comp_df['Value'].apply(lambda x: f"${x:.2f}"),
                    textposition='auto'
                ))
                
                fig_comp.update_layout(
                    title="Fair Value vs Current Price",
                    yaxis_title="Price (USD)",
                    # Removed template="plotly_white" for dark mode support
                    height=400
                )
                
                st.plotly_chart(fig_comp, use_container_width=True)


            with tab_chart:
                st.subheader("Price History & Analysis")
                
                col_period, col_type = st.columns([1, 3])
                # Key is important here to prevent state issues, though session state wrapper helps
                time_period = col_period.selectbox("Time Period", ["1y", "3y", "5y", "10y", "max"], index=0, key="chart_period")
                
                # Fetch extra data for MA calculation
                # Map requested period to a longer fetch period to ensure MA120 has enough data
                period_mapping = {
                    "1y": "2y",
                    "3y": "5y",
                    "5y": "10y",
                    "10y": "max",
                    "max": "max"
                }
                fetch_period = period_mapping.get(time_period, "max")
                
                # Use cached history with extended period
                hist_data = get_cached_history(active_ticker, fetch_period)
                
                if hist_data is not None and not hist_data.empty:
                    # Calculate MAs on the full extended dataset
                    hist_data = valuation.calculate_moving_averages(hist_data)
                    
                    # Slice data back to the requested viewing period
                    if time_period != "max":
                        try:
                            last_date = hist_data.index.max()
                            years_map = {"1y": 1, "3y": 3, "5y": 5, "10y": 10}
                            if time_period in years_map:
                                cutoff_date = last_date - pd.DateOffset(years=years_map[time_period])
                                hist_data = hist_data[hist_data.index > cutoff_date]
                        except Exception as e:
                            st.warning(f"Could not slice data perfectly: {e}")
                    
                    # Plotly Chart
                    fig = go.Figure()
                    
                    # Candlestick
                    fig.add_trace(go.Candlestick(x=hist_data.index,
                                    open=hist_data['Open'],
                                    high=hist_data['High'],
                                    low=hist_data['Low'],
                                    close=hist_data['Close'],
                                    name='Price'))
                    
                    # Moving Averages
                    colors = {'MA5': 'blue', 'MA20': 'orange', 'MA60': 'green', 'MA120': 'red'}
                    for ma, color in colors.items():
                        if ma in hist_data.columns:
                            # Filter out NaN values for cleaner lines if any remain
                            ma_data = hist_data[ma].dropna()
                            fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data, mode='lines', name=ma, line=dict(color=color, width=1)))
                    
                    fig.update_layout(
                        title=f"{active_ticker} Price Chart",
                        yaxis_title="Price (USD)",
                        xaxis_rangeslider_visible=False,
                        height=600,
                        hovermode="x unified",
                        # Enable touch interactions for mobile
                        dragmode='pan',  # Default to pan mode (better for mobile)
                        # Configure modebar for mobile
                        modebar=dict(
                            orientation='v',  # Vertical toolbar
                            bgcolor='rgba(0,0,0,0.5)',
                            color='white',
                            activecolor='lightblue'
                        )
                    )
                    
                    # Configure for mobile-friendly interactions
                    config = {
                        'displayModeBar': True,  # Show toolbar
                        'displaylogo': False,  # Hide Plotly logo
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],  # Remove unused buttons
                        'scrollZoom': True,  # Enable scroll/pinch zoom
                        'doubleClick': 'reset',  # Double tap to reset
                        'responsive': True  # Responsive sizing
                    }
                    
                    st.plotly_chart(fig, use_container_width=True, config=config)
                else:
                    st.warning("No historical data available.")


            with tab_data:
                st.subheader("Raw Financial Data")
                st.json({
                    "Free Cash Flow": info.get('freeCashflow'),
                    "Total Cash": info.get('totalCash'),
                    "Total Debt": info.get('totalDebt'),
                    "Shares Outstanding": info.get('sharesOutstanding'),
                    "Trailing EPS": info.get('trailingEps'),
                    "Book Value": info.get('bookValue'),
                    "Trailing PE": info.get('trailingPE'),
                    "PEG Ratio": info.get('pegRatio'),
                    "Dividend Rate": info.get('dividendRate')
                })
            
            with tab_peers:
                st.subheader("🏢 同業比較分析")
                
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                st.markdown(f"**產業:** {sector} | **行業:** {industry}")
                
                # Get peer comparison data
                with st.spinner("正在獲取同業數據..."):
                    peer_df, industry_stats, rankings = peer_comparison.get_comparison_summary(active_ticker, info)
                
                if peer_df is not None and not peer_df.empty:
                    st.markdown("---")
                    
                    # Display peer comparison table
                    st.markdown("### 📊 關鍵指標對比")
                    
                    # Format the dataframe for display
                    display_df = peer_df.copy()
                    
                    # Format numeric columns
                    format_dict = {
                        'market_cap': lambda x: f"${x/1e9:.2f}B" if pd.notna(x) else "N/A",
                        'pe_ratio': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'forward_pe': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'peg_ratio': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'ev_ebitda': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'price_to_book': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'price_to_sales': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'roe': lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A",
                        'profit_margin': lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A",
                        'revenue_growth': lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A",
                        'earnings_growth': lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A",
                        'debt_to_equity': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'current_ratio': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'beta': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
                        'dividend_yield': lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A",
                    }
                    
                    # Select key columns to display
                    display_columns = ['ticker', 'name', 'market_cap', 'pe_ratio', 'peg_ratio', 
                                     'ev_ebitda', 'roe', 'profit_margin', 'revenue_growth']
                    
                    # Create display dataframe
                    display_subset = display_df[display_columns].copy()
                    
                    # Rename columns for better readability
                    column_names = {
                        'ticker': '代碼',
                        'name': '公司名稱',
                        'market_cap': '市值',
                        'pe_ratio': 'P/E',
                        'peg_ratio': 'PEG',
                        'ev_ebitda': 'EV/EBITDA',
                        'roe': 'ROE',
                        'profit_margin': '利潤率',
                        'revenue_growth': '營收成長'
                    }
                    display_subset = display_subset.rename(columns=column_names)
                    
                    # Highlight the main stock
                    def highlight_main_stock(row):
                        if row['代碼'] == active_ticker:
                            return ['background-color: #1f77b4; color: white'] * len(row)
                        return [''] * len(row)
                    
                    st.dataframe(display_subset, use_container_width=True, hide_index=True)
                    
                    # Industry Statistics
                    st.markdown("---")
                    st.markdown("### 📈 行業統計")
                    
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    
                    with stat_col1:
                        st.markdown("#### 估值指標")
                        if industry_stats:
                            pe_mean = industry_stats.get('pe_ratio_mean')
                            peg_mean = industry_stats.get('peg_ratio_mean')
                            if pe_mean:
                                st.metric("行業平均 P/E", f"{pe_mean:.2f}")
                            if peg_mean:
                                st.metric("行業平均 PEG", f"{peg_mean:.2f}")
                    
                    with stat_col2:
                        st.markdown("#### 獲利能力")
                        if industry_stats:
                            roe_mean = industry_stats.get('roe_mean')
                            margin_mean = industry_stats.get('profit_margin_mean')
                            if roe_mean:
                                st.metric("行業平均 ROE", f"{roe_mean*100:.1f}%")
                            if margin_mean:
                                st.metric("行業平均利潤率", f"{margin_mean*100:.1f}%")
                    
                    with stat_col3:
                        st.markdown("#### 成長性")
                        if industry_stats:
                            rev_growth_mean = industry_stats.get('revenue_growth_mean')
                            earn_growth_mean = industry_stats.get('earnings_growth_mean')
                            if rev_growth_mean:
                                st.metric("行業平均營收成長", f"{rev_growth_mean*100:.1f}%")
                            if earn_growth_mean:
                                st.metric("行業平均盈利成長", f"{earn_growth_mean*100:.1f}%")
                    
                    # Rankings
                    if rankings:
                        st.markdown("---")
                        st.markdown("### 🏆 同業排名")
                        
                        rank_col1, rank_col2 = st.columns(2)
                        
                        with rank_col1:
                            st.markdown("#### 估值與財務")
                            for metric in ['pe_ratio', 'peg_ratio', 'roe', 'profit_margin']:
                                if metric in rankings:
                                    rank_info = rankings[metric]
                                    metric_name = {
                                        'pe_ratio': 'P/E Ratio',
                                        'peg_ratio': 'PEG Ratio',
                                        'roe': 'ROE',
                                        'profit_margin': 'Profit Margin'
                                    }[metric]
                                    
                                    percentile = rank_info['percentile']
                                    if percentile >= 75:
                                        emoji = "🟢"
                                    elif percentile >= 50:
                                        emoji = "🟡"
                                    else:
                                        emoji = "🔴"
                                    
                                    st.markdown(f"{emoji} **{metric_name}**: {rank_info['position']}/{rank_info['total']} (前 {percentile:.0f}%)")
                        
                        with rank_col2:
                            st.markdown("#### 成長與風險")
                            for metric in ['revenue_growth', 'earnings_growth', 'debt_to_equity', 'beta']:
                                if metric in rankings:
                                    rank_info = rankings[metric]
                                    metric_name = {
                                        'revenue_growth': 'Revenue Growth',
                                        'earnings_growth': 'Earnings Growth',
                                        'debt_to_equity': 'Debt/Equity',
                                        'beta': 'Beta (Volatility)'
                                    }[metric]
                                    
                                    percentile = rank_info['percentile']
                                    if percentile >= 75:
                                        emoji = "🟢"
                                    elif percentile >= 50:
                                        emoji = "🟡"
                                    else:
                                        emoji = "🔴"
                                    
                                    st.markdown(f"{emoji} **{metric_name}**: {rank_info['position']}/{rank_info['total']} (前 {percentile:.0f}%)")
                    
                    # Radar Chart Comparison
                    st.markdown("---")
                    st.markdown("### 📊 多維度雷達圖比較")
                    
                    # Select top 5 peers for radar chart
                    radar_df = peer_df.head(6)  # Main stock + 5 peers
                    
                    # Normalize metrics for radar chart (0-100 scale)
                    metrics_for_radar = ['pe_ratio', 'peg_ratio', 'roe', 'profit_margin', 'revenue_growth']
                    
                    fig_radar = go.Figure()
                    
                    for idx, row in radar_df.iterrows():
                        values = []
                        for metric in metrics_for_radar:
                            val = row[metric]
                            if pd.notna(val):
                                # Normalize to 0-100 (simple approach)
                                if metric in ['pe_ratio', 'peg_ratio']:
                                    # Lower is better, invert
                                    normalized = max(0, 100 - (val * 10))
                                else:
                                    # Higher is better
                                    normalized = min(100, val * 100)
                                values.append(normalized)
                            else:
                                values.append(0)
                        
                        # Close the radar chart
                        values.append(values[0])
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=metrics_for_radar + [metrics_for_radar[0]],
                            fill='toself',
                            name=row['ticker'],
                            line=dict(width=2 if row['ticker'] == active_ticker else 1),
                            opacity=0.8 if row['ticker'] == active_ticker else 0.4
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100])
                        ),
                        showlegend=True,
                        height=500
                    )
                    
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
                else:
                    st.info(f"暫無 {active_ticker} 的同業比較數據。這可能是因為：\n\n1. 該股票較為小眾，沒有預設的同業對比\n2. 數據獲取失敗\n\n目前支持的主要股票包括：AAPL, MSFT, GOOGL, TSLA, NVDA, AMD, JPM, BAC, KO, PEP, WMT, AMZN, JNJ, PFE 等。")
            
            # Auto-save to watchlist
            watchlist.add_to_watchlist(
                ticker=active_ticker,
                name=info.get('shortName', active_ticker),
                current_price=current_price,
                sector=info.get('sector', 'N/A'),
                industry=info.get('industry', 'N/A'),
                wacc=st.session_state.wacc,
                dcf_value=dcf_value,
                peg_ratio=peg_ratio,
                lynch_value=lynch_value,
                mr_value=mr_value,
                ev_ebitda=ev_ebitda,
                momentum=momentum
            )

else:
    st.info("👈 Enter a stock ticker in the sidebar and click 'Analyze Stock' to begin.")

# Watchlist Page
if page == "📋 My Watchlist":
    st.title("📋 My Watchlist")
    st.markdown("All stocks you've analyzed are automatically saved here.")
    
    saved_stocks = watchlist.load_watchlist()
    
    if not saved_stocks:
        st.info("No stocks in your watchlist yet. Analyze a stock to add it automatically!")
    else:
        st.markdown(f"**Total Stocks Tracked:** {len(saved_stocks)}")
        st.markdown("---")
        
        # Display as cards
        for stock in reversed(saved_stocks):  # Show most recent first
            with st.expander(f"**{stock['ticker']}** - {stock['name']} | ${stock.get('current_price', 'N/A')}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 📊 Basic Info")
                    st.markdown(f"**Sector:** {stock.get('sector', 'N/A')}")
                    st.markdown(f"**Industry:** {stock.get('industry', 'N/A')}")
                    st.markdown(f"**Current Price:** ${stock.get('current_price', 'N/A')}")
                    st.markdown(f"**WACC:** {stock.get('wacc', 'N/A')}%")
                    st.markdown(f"**Last Updated:** {stock.get('last_updated', 'N/A')}")
                
                with col2:
                    st.markdown("### 💰 Valuations")
                    dcf = stock.get('dcf_value')
                    if dcf:
                        st.markdown(f"**DCF:** ${dcf:.2f}")
                    else:
                        st.markdown("**DCF:** N/A")
                    
                    peg = stock.get('peg_ratio')
                    if peg:
                        st.markdown(f"**PEG:** {peg:.2f}")
                    else:
                        st.markdown("**PEG:** N/A")
                    
                    lynch = stock.get('lynch_value')
                    if lynch:
                        st.markdown(f"**Lynch Value:** ${lynch:.2f}")
                    else:
                        st.markdown("**Lynch Value:** N/A")
                    
                    mr = stock.get('mr_value')
                    if mr:
                        st.markdown(f"**Mean Reversion:** ${mr:.2f}")
                    else:
                        st.markdown("**Mean Reversion:** N/A")
                    
                    ev = stock.get('ev_ebitda')
                    if ev:
                        st.markdown(f"**EV/EBITDA:** {ev:.2f}")
                    else:
                        st.markdown("**EV/EBITDA:** N/A")
                
                with col3:
                    st.markdown("### 📈 Momentum")
                    mom = stock.get('momentum')
                    if mom:
                        st.markdown(f"**3M Return:** {mom.get('return_3m', 0):+.2f}%")
                        st.markdown(f"**6M Return:** {mom.get('return_6m', 0):+.2f}%")
                        st.markdown(f"**RS Ranking:** {mom.get('rs_ranking', 'N/A')}")
                        st.markdown(f"**IBD RS Rating:** {mom.get('rs_rating', 0)}/99")
                    else:
                        st.markdown("No momentum data")
                
                # Quick analyze button
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                with col_btn1:
                    if st.button(f"🔍 Analyze", key=f"analyze_{stock['ticker']}"):
                        st.session_state.analyzed = True
                        st.session_state.analyzed_ticker = stock['ticker']
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"🗑️ Remove", key=f"remove_{stock['ticker']}"):
                        watchlist.remove_from_watchlist(stock['ticker'])
                        st.rerun()
