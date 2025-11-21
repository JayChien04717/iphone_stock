"""
Stock Valuation Pro - Main Application
Clean, modular structure with separated concerns
"""
import streamlit as st
import pandas as pd

# Import custom modules
import data_fetcher
import ui_components
import watchlist
import ai_scoring
import peer_comparison
import peer_comparison_ui
import api_provider

# Page configuration
st.set_page_config(
    page_title="Stock Valuation Pro", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Mobile-optimized CSS
st.markdown("""
<style>
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.2rem;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        .stButton button {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            min-height: 44px;
        }
        
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }
        
        .dataframe {
            font-size: 0.75rem;
        }
        
        .streamlit-expanderHeader {
            font-size: 0.95rem;
            padding: 0.75rem;
        }
    }
    
    .stButton button {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    [data-testid="stMetricValue"] {
        font-weight: 600;
    }
    
    [data-testid="column"] {
        padding: 0.25rem;
    }
    
    .stMetric {
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.title("Stock Valuation Pro")
st.markdown("### Advanced Long-Term Valuation & Analysis")

# Sidebar - API Status
with st.sidebar:
    ui_components.render_api_status(api_provider.get_api_status())

# Sidebar - Page Selection
page = st.sidebar.radio("Navigation", ["📊 Stock Analysis", "📋 My Watchlist"])

# ==================== STOCK ANALYSIS PAGE ====================
if page == "📊 Stock Analysis":
    # Initialize session state
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False
    if 'analyzed_ticker' not in st.session_state:
        st.session_state.analyzed_ticker = ""
    
    # Sidebar inputs
    with st.sidebar:
        st.markdown("---")
        st.subheader("Stock Selection")
        ticker_input = st.text_input("Enter Stock Ticker", value="AAPL").upper()
        
        # Estimate Inputs button
        if st.button("🔍 Analyze Stock"):
            st.session_state.analyzed = True
            st.session_state.analyzed_ticker = ticker_input
        
        # Valuation parameters
        if st.session_state.analyzed:
            st.markdown("---")
            st.subheader("Valuation Parameters")
            
            wacc = st.number_input("WACC (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.1) / 100
            growth_rate = st.number_input("Growth Rate (%)", min_value=-10.0, max_value=50.0, value=5.0, step=0.5) / 100
            terminal_growth = st.number_input("Terminal Growth (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1) / 100
    
    # Main content
    if st.session_state.analyzed:
        active_ticker = st.session_state.analyzed_ticker
        
        try:
            # Fetch data
            with st.spinner(f"Fetching data for {active_ticker}..."):
                info = data_fetcher.get_cached_info(active_ticker)
                hist_data = data_fetcher.get_cached_history(active_ticker, period="2y")
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if not current_price and not hist_data.empty:
                    current_price = hist_data['Close'].iloc[-1]
            
            # Display basic info
            ui_components.render_basic_info(info, current_price)
            
            st.markdown("---")
            
            # Calculate momentum
            momentum = data_fetcher.calculate_momentum_metrics(hist_data)
            if momentum:
                ui_components.render_momentum_metrics(momentum)
            
            st.markdown("---")
            
            # Calculate all valuations
            valuations = data_fetcher.calculate_all_valuations(info, wacc, growth_rate, terminal_growth)
            
            # Calculate AI score
            pe_ratio = info.get('trailingPE')
            ai_score = ai_scoring.calculate_overall_score(
                current_price=current_price,
                dcf_value=valuations['dcf_value'],
                peg_ratio=valuations['peg_ratio'],
                ev_ebitda=valuations['ev_ebitda'],
                pe_ratio=pe_ratio,
                info=info,
                ticker=active_ticker,
                momentum=momentum
            )
            
            # Display AI score
            ui_components.render_ai_score(ai_score, current_price)
            
            st.markdown("---")
            
            # Tabs
            tab_val, tab_chart, tab_data, tab_peers, tab_news = st.tabs([
                "Valuation Models",
                "Interactive Chart",
                "Financial Data",
                "🏢 Industry Comparison",
                "📰 News & Sentiment"
            ])
            
            # ===== VALUATION TAB =====
            with tab_val:
                st.subheader("Fair Value Estimates")
                
                # Display valuation metrics
                c1, c2 = st.columns(2)
                c3, c4 = st.columns(2)
                c5, c6 = st.columns(2)

                # Helper to display metric with N/A handling
                def display_metric(col, label, value, current):
                    if value is not None:
                        delta = ((value - current) / current) * 100
                        col.metric(label, f"${value:.2f}", f"{delta:.1f}%")
                    else:
                        col.metric(label, "N/A")

                # DCF Fair Value
                display_metric(c1, "DCF Fair Value", valuations.get('dcf_value'), current_price)

                # PEG Ratio
                if valuations.get('peg_ratio') is not None:
                    status = "Undervalued" if valuations['peg_ratio'] < 1 else "Overvalued"
                    c2.metric("PEG Ratio", f"{valuations['peg_ratio']:.2f}", status, delta_color="inverse")
                else:
                    c2.metric("PEG Ratio", "N/A")

                # EV/EBITDA
                if valuations.get('ev_ebitda') is not None:
                    status = "Good" if valuations['ev_ebitda'] < 10 else "High"
                    c3.metric("EV/EBITDA", f"{valuations['ev_ebitda']:.2f}", status, delta_color="inverse")
                else:
                    c3.metric("EV/EBITDA", "N/A")

                # Peter Lynch Value
                display_metric(c4, "Peter Lynch Value", valuations.get('lynch_value'), current_price)

                # Mean Reversion (Fair PE)
                display_metric(c5, "Mean Reversion (Fair PE)", valuations.get('mr_value'), current_price)
                
                # Analyst target prices
                st.markdown("---")
                st.markdown("#### 📊 分析師目標價 (Analyst Consensus)")
                
                targets = data_fetcher.get_analyst_targets(info)
                
                if targets['target_mean']:
                    analyst_col1, analyst_col2, analyst_col3 = st.columns(3)
                    
                    with analyst_col1:
                        delta = ((targets['target_mean'] - current_price) / current_price) * 100
                        st.metric("平均目標價 (1Y Target)", f"${targets['target_mean']:.2f}", f"{delta:+.1f}%")
                    
                    with analyst_col2:
                        if targets['target_high'] and targets['target_low']:
                            st.metric("目標價範圍", f"${targets['target_low']:.2f} - ${targets['target_high']:.2f}")
                        else:
                            st.metric("目標價範圍", "N/A")
                    
                    with analyst_col3:
                        if targets['num_analysts']:
                            rec_text = {
                                'strong_buy': '🟢 強力買入',
                                'buy': '🟢 買入',
                                'hold': '🟡 持有',
                                'sell': '🔴 賣出',
                                'strong_sell': '🔴 強力賣出'
                            }.get(targets['recommendation'], targets['recommendation'] or 'N/A')
                            st.metric(f"分析師建議 ({targets['num_analysts']}位)", rec_text)
                        else:
                            st.metric("分析師建議", targets['recommendation'] or "N/A")
                else:
                    st.info("此股票暫無分析師目標價數據")
                
                # Valuation comparison chart
                ui_components.render_valuation_comparison_chart(
                    valuations['dcf_value'],
                    valuations['peg_value'],
                    valuations['lynch_value'],
                    valuations['mr_value'],
                    current_price
                )
            
            # ===== CHART TAB =====
            with tab_chart:
                ui_components.render_price_chart(hist_data, active_ticker)
            
            # ===== DATA TAB =====
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
            
            # ===== PEERS TAB =====
            with tab_peers:
                peer_comparison_ui.render_peer_comparison_tab(active_ticker, info)
            
            # ===== NEWS TAB =====
            with tab_news:
                ui_components.render_news_tab(api_provider, active_ticker)
            
            # Auto-save to watchlist
            watchlist.add_to_watchlist(
                ticker=active_ticker,
                name=info.get('shortName', active_ticker),
                current_price=current_price,
                sector=info.get('sector'),
                industry=info.get('industry'),
                wacc=wacc,
                dcf_value=valuations['dcf_value'],
                peg_ratio=valuations['peg_ratio'],
                lynch_value=valuations['lynch_value'],
                mr_value=valuations['mr_value'],
                ev_ebitda=valuations['ev_ebitda'],
                momentum=momentum
            )
            
        except Exception as e:
            st.error(f"Error analyzing {active_ticker}: {str(e)}")
            st.info("Please check the ticker symbol and try again.")
    
    else:
        st.info("👈 Enter a stock ticker in the sidebar and click 'Analyze Stock' to begin.")

# ==================== WATCHLIST PAGE ====================
elif page == "📋 My Watchlist":
    st.subheader("My Stock Watchlist")
    
    stocks = watchlist.get_watchlist()
    
    if not stocks:
        st.info("Your watchlist is empty. Analyze some stocks to add them here!")
    else:
        st.markdown(f"**Total Stocks:** {len(stocks)}")
        
        for stock in reversed(stocks):
            with st.expander(f"**{stock['ticker']}** - {stock['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 💰 Current")
                    st.markdown(f"**Price:** ${stock['current_price']:.2f}")
                    st.markdown(f"**WACC:** {stock.get('wacc', 0)*100:.1f}%")
                    st.markdown(f"**Updated:** {stock.get('last_updated', 'N/A')}")
                
                with col2:
                    st.markdown("### 📊 Valuations")
                    dcf = stock.get('dcf_value')
                    if dcf:
                        st.markdown(f"**DCF Value:** ${dcf:.2f}")
                    else:
                        st.markdown("**DCF Value:** N/A")
                    
                    peg = stock.get('peg_ratio')
                    if peg:
                        st.markdown(f"**PEG Ratio:** {peg:.2f}")
                    else:
                        st.markdown("**PEG Ratio:** N/A")
                    
                    lynch = stock.get('lynch_value')
                    if lynch:
                        st.markdown(f"**Lynch Value:** ${lynch:.2f}")
                    else:
                        st.markdown("**Lynch Value:** N/A")
                
                with col3:
                    st.markdown("### 📈 Momentum")
                    mom = stock.get('momentum')
                    if mom:
                        st.markdown(f"**3M Return:** {mom.get('return_3m', 0):+.2f}%")
                        st.markdown(f"**6M Return:** {mom.get('return_6m', 0):+.2f}%")
                        st.markdown(f"**RS Rating:** {mom.get('rs_rating', 0)}/99")
                    else:
                        st.markdown("No momentum data")
                
                # Action buttons
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
