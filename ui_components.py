"""
UI Components Module
Contains all UI rendering functions for the Stock Valuation App
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_api_status(api_status):
    """Render API status indicators in sidebar"""
    st.markdown("---")
    st.markdown("#### 🔌 API Status")
    
    if api_status['finnhub']:
        st.success("✅ Finnhub API: Active")
    else:
        st.warning("⚠️ Finnhub API: Not configured")
    
    if api_status['alpha_vantage']:
        st.success("✅ Alpha Vantage API: Active")
    else:
        st.info("ℹ️ Alpha Vantage API: Not configured")
    
    if not any(api_status.values()):
        st.info("💡 查看 API_KEYS_GUIDE.md 了解如何配置免費 API")
    
    st.markdown("---")


def render_basic_info(info, current_price):
    """Render basic stock information"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${current_price:.2f}")
    with col2:
        market_cap = info.get('marketCap')
        if market_cap:
            st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
        else:
            st.metric("Market Cap", "N/A")
    with col3:
        pe_ratio = info.get('trailingPE')
        if pe_ratio:
            st.metric("P/E Ratio", f"{pe_ratio:.2f}")
        else:
            st.metric("P/E Ratio", "N/A")
    with col4:
        dividend_yield = info.get('dividendYield')
        if dividend_yield:
            st.metric("Dividend Yield", f"{dividend_yield*100:.2f}%")
        else:
            st.metric("Dividend Yield", "N/A")


def render_momentum_metrics(momentum):
    """Render price momentum metrics in 2x2 grid"""
    st.markdown("### 📈 Price Momentum")
    
    # First row
    col1, col2 = st.columns(2)
    with col1:
        return_3m = momentum.get('return_3m', 0)
        st.metric("3-Month Return", f"{return_3m:+.2f}%")
    with col2:
        return_6m = momentum.get('return_6m', 0)
        st.metric("6-Month Return", f"{return_6m:+.2f}%")
    
    # Second row
    col3, col4 = st.columns(2)
    with col3:
        rs_ranking = momentum.get('rs_ranking', 'N/A')
        st.metric("RS Ranking", rs_ranking)
    with col4:
        rs_rating = momentum.get('rs_rating', 0)
        st.metric("IBD RS Rating", f"{rs_rating}/99")


def render_ai_score(ai_score, current_price):
    """Render AI comprehensive score section"""
    st.markdown("### 🤖 AI 綜合評分")

    ai_score = ai_score or {}

    # Overall score card
    score = ai_score.get('overall_score') or ai_score.get('total_score') or 0
    rating = ai_score.get('rating', "")
    recommendation = ai_score.get('recommendation', "")
    
    # Color based on score
    if score >= 80:
        score_color = "#00C853"  # Green
    elif score >= 60:
        score_color = "#FFC107"  # Yellow
    else:
        score_color = "#F44336"  # Red
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {score_color}22 0%, {score_color}11 100%); 
                padding: 2rem; border-radius: 15px; border-left: 5px solid {score_color}; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; color: {score_color}; font-size: 3rem;">{score}/100</h1>
        <p style="margin: 0.5rem 0; font-size: 1.5rem;">{rating}</p>
        <p style="margin: 0; font-size: 1.2rem; opacity: 0.8;">{recommendation}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Score breakdown
    st.markdown("#### 📊 評分細節")
    breakdown = ai_score.get('breakdown', {})
    valuation_score = breakdown.get('valuation', 0)
    financial_health_score = breakdown.get('financial_health', 0)
    growth_score = breakdown.get('growth', 0)
    momentum_score = breakdown.get('momentum', 0)
    risk_score = breakdown.get('risk', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**估值吸引力** (25分)")
        st.progress(valuation_score / 25)
        st.caption(f"{valuation_score:.1f} / 25")

        st.markdown("**財務健康** (20分)")
        st.progress(financial_health_score / 20)
        st.caption(f"{financial_health_score:.1f} / 20")

        st.markdown("**成長潛力** (20分)")
        st.progress(growth_score / 20)
        st.caption(f"{growth_score:.1f} / 20")

    with col2:
        st.markdown("**動能與市場情緒** (20分)")
        st.progress(momentum_score / 20)
        st.caption(f"{momentum_score:.1f} / 20")

        st.markdown("**風險評估** (15分)")
        st.progress(risk_score / 15)
        st.caption(f"{risk_score:.1f} / 15")
    
    # Insights and risks
    st.markdown("---")
    insight_col1, insight_col2 = st.columns(2)
    
    key_insights = ai_score.get('key_insights') or ai_score.get('insights', [])

    with insight_col1:
        st.markdown("#### ✅ 關鍵優勢")
        if key_insights:
            for insight in key_insights:
                st.markdown(f"- {insight}")
        else:
            st.markdown("- 無明顯優勢")

    risk_factors = ai_score.get('risk_factors') or ["無重大風險"]

    with insight_col2:
        st.markdown("#### ⚠️ 風險因素")
        for risk in risk_factors:
            st.markdown(f"- {risk}")


def render_valuation_comparison_chart(dcf_value, peg_value, lynch_value, mr_value, current_price):
    """Render valuation comparison chart"""
    st.markdown("### Valuation Comparison")
    
    # Prepare data for chart
    valuation_data = {
        'Method': [],
        'Fair Value': [],
        'vs Current': []
    }
    
    if dcf_value:
        valuation_data['Method'].append('DCF')
        valuation_data['Fair Value'].append(dcf_value)
        valuation_data['vs Current'].append(((dcf_value - current_price) / current_price) * 100)
    
    if peg_value:
        valuation_data['Method'].append('PEG-based')
        valuation_data['Fair Value'].append(peg_value)
        valuation_data['vs Current'].append(((peg_value - current_price) / current_price) * 100)
    
    if lynch_value:
        valuation_data['Method'].append('Peter Lynch')
        valuation_data['Fair Value'].append(lynch_value)
        valuation_data['vs Current'].append(((lynch_value - current_price) / current_price) * 100)
    
    if mr_value:
        valuation_data['Method'].append('Mean Reversion')
        valuation_data['Fair Value'].append(mr_value)
        valuation_data['vs Current'].append(((mr_value - current_price) / current_price) * 100)
    
    if valuation_data['Method']:
        df_val = pd.DataFrame(valuation_data)
        
        fig = go.Figure()
        
        # Add bars for fair values
        fig.add_trace(go.Bar(
            x=df_val['Method'],
            y=df_val['Fair Value'],
            name='Fair Value',
            marker_color='lightblue',
            text=df_val['Fair Value'].apply(lambda x: f'${x:.2f}'),
            textposition='outside'
        ))
        
        # Add current price line
        fig.add_hline(y=current_price, line_dash="dash", line_color="red",
                     annotation_text=f"Current: ${current_price:.2f}",
                     annotation_position="right")
        
        fig.update_layout(
            title="Fair Value Estimates vs Current Price",
            yaxis_title="Price (USD)",
            xaxis_title="Valuation Method",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_price_chart(hist_data, ticker):
    """Render interactive price chart with moving averages"""
    st.subheader("Stock Price with Moving Averages")
    
    if hist_data is not None and not hist_data.empty:
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='Price'
        ))
        
        # Moving averages
        colors = {
            'MA_20': 'orange',
            'MA_50': 'blue',
            'MA_200': 'red'
        }
        
        for ma, color in colors.items():
            if ma in hist_data.columns:
                ma_data = hist_data[ma].dropna()
                fig.add_trace(go.Scatter(
                    x=ma_data.index, 
                    y=ma_data, 
                    mode='lines', 
                    name=ma, 
                    line=dict(color=color, width=1)
                ))
        
        fig.update_layout(
            title=f"{ticker} Price Chart",
            yaxis_title="Price (USD)",
            xaxis_rangeslider_visible=False,
            height=600,
            hovermode="x unified",
            dragmode='pan',
            modebar=dict(
                orientation='v',
                bgcolor='rgba(0,0,0,0.5)',
                color='white',
                activecolor='lightblue'
            )
        )
        
        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'scrollZoom': True,
            'doubleClick': 'reset',
            'responsive': True
        }
        
        st.plotly_chart(fig, use_container_width=True, config=config)
    else:
        st.warning("No historical data available.")


def render_news_tab(api_provider, ticker):
    """Render news and sentiment analysis tab"""
    st.subheader("📰 新聞與市場情緒")
    
    # Check if Finnhub API is available
    if not api_provider.get_api_status()['finnhub']:
        st.warning("⚠️ Finnhub API 未配置")
        st.info("""
        要使用新聞和情緒分析功能，請：
        1. 前往 https://finnhub.io/register 註冊免費帳號
        2. 獲取 API Key
        3. 在 Streamlit Secrets 中配置 `FINNHUB_API_KEY`
        
        詳細說明請查看 `API_KEYS_GUIDE.md`
        """)
        return
    
    # Get company news
    with st.spinner("正在獲取最新新聞..."):
        news = api_provider.api_provider.get_company_news(ticker, days=7)
    
    if news and len(news) > 0:
        st.markdown("### 📰 最新新聞 (過去 7 天)")
        
        for article in news[:10]:
            with st.expander(f"📄 {article.get('headline', 'No title')}", expanded=False):
                col_news1, col_news2 = st.columns([3, 1])
                
                with col_news1:
                    st.markdown(f"**來源:** {article.get('source', 'Unknown')}")
                    st.markdown(f"**時間:** {pd.to_datetime(article.get('datetime', 0), unit='s').strftime('%Y-%m-%d %H:%M')}")
                    
                    summary = article.get('summary', '')
                    if summary:
                        st.markdown(f"**摘要:** {summary[:300]}...")
                    
                    url = article.get('url', '')
                    if url:
                        st.markdown(f"[閱讀全文]({url})")
                
                with col_news2:
                    sentiment = article.get('sentiment', 0)
                    if sentiment > 0:
                        st.success(f"😊 正面")
                    elif sentiment < 0:
                        st.error(f"😟 負面")
                    else:
                        st.info(f"😐 中性")
    else:
        st.info("暫無最新新聞數據")
    
    st.markdown("---")
    
    # Get recommendation trends
    with st.spinner("正在獲取分析師建議趨勢..."):
        recommendations = api_provider.api_provider.get_recommendation_trends(ticker)
    
    if recommendations and len(recommendations) > 0:
        st.markdown("### 📊 分析師建議趨勢")
        
        rec_df = pd.DataFrame(recommendations)
        
        if not rec_df.empty and 'period' in rec_df.columns:
            latest = rec_df.iloc[0]
            
            rec_col1, rec_col2, rec_col3, rec_col4, rec_col5 = st.columns(5)
            
            with rec_col1:
                st.metric("強力買入", int(latest.get('strongBuy', 0)))
            with rec_col2:
                st.metric("買入", int(latest.get('buy', 0)))
            with rec_col3:
                st.metric("持有", int(latest.get('hold', 0)))
            with rec_col4:
                st.metric("賣出", int(latest.get('sell', 0)))
            with rec_col5:
                st.metric("強力賣出", int(latest.get('strongSell', 0)))
            
            st.markdown(f"**更新時間:** {latest.get('period', 'N/A')}")
            
            # Trend chart
            if len(rec_df) > 1:
                st.markdown("#### 建議趨勢圖")
                
                fig_rec = go.Figure()
                
                fig_rec.add_trace(go.Scatter(
                    x=rec_df['period'], y=rec_df['strongBuy'], 
                    mode='lines+markers', name='強力買入',
                    line=dict(color='darkgreen', width=2)
                ))
                fig_rec.add_trace(go.Scatter(
                    x=rec_df['period'], y=rec_df['buy'], 
                    mode='lines+markers', name='買入',
                    line=dict(color='lightgreen', width=2)
                ))
                fig_rec.add_trace(go.Scatter(
                    x=rec_df['period'], y=rec_df['hold'], 
                    mode='lines+markers', name='持有',
                    line=dict(color='gray', width=2)
                ))
                fig_rec.add_trace(go.Scatter(
                    x=rec_df['period'], y=rec_df['sell'], 
                    mode='lines+markers', name='賣出',
                    line=dict(color='orange', width=2)
                ))
                fig_rec.add_trace(go.Scatter(
                    x=rec_df['period'], y=rec_df['strongSell'], 
                    mode='lines+markers', name='強力賣出',
                    line=dict(color='red', width=2)
                ))
                
                fig_rec.update_layout(
                    title="分析師建議趨勢",
                    xaxis_title="時間",
                    yaxis_title="分析師數量",
                    height=400,
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig_rec, use_container_width=True)
    else:
        st.info("暫無分析師建議趨勢數據")
