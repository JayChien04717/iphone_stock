"""
Peer Comparison UI Component
Renders the industry peer comparison tab
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import peer_comparison


def render_peer_comparison_tab(ticker, info):
    """Render complete peer comparison analysis"""
    st.subheader("🏢 同業比較分析")
    
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    st.markdown(f"**產業:** {sector} | **行業:** {industry}")
    
    # Get peer comparison data
    with st.spinner("正在獲取同業數據..."):
        peer_df, industry_stats, rankings = peer_comparison.get_comparison_summary(ticker, info)
    
    if peer_df is None or peer_df.empty:
        st.info(f"暫無 {ticker} 的同業比較數據。這可能是因為：\n\n1. 該股票較為小眾，沒有預設的同業對比\n2. 數據獲取失敗\n\n目前支持的主要股票包括：AAPL, MSFT, GOOGL, TSLA, NVDA, AMD, JPM, BAC, KO, PEP, WMT, AMZN, JNJ, PFE 等。")
        return
    
    st.markdown("---")
    
    # Display peer comparison table
    st.markdown("### 📊 關鍵指標對比")
    
    # Prepare display dataframe
    display_df = peer_df.copy()
    
    # Select and rename columns (removed ROE, removed name)
    display_columns = {
        'ticker': '代碼',
        'market_cap': '市值',
        'pe_ratio': 'P/E',
        'peg_ratio': 'PEG',
        'ev_ebitda': 'EV/EBITDA',
        'profit_margin': '利潤率(%)',
        'revenue_growth': '營收成長(YOY%)',
        'revenue_growth_quarterly': '營收成長(QOQ%)',
        'earnings_growth': '盈利成長(YOY%)'
    }
    
    # Create formatted display dataframe
    formatted_df = pd.DataFrame()
    
    for col_key, col_name in display_columns.items():
        if col_key in display_df.columns:
            if col_key == 'ticker':
                formatted_df[col_name] = display_df[col_key]
            elif col_key == 'market_cap':
                formatted_df[col_name] = display_df[col_key].apply(
                    lambda x: f"${x/1e9:.1f}B" if pd.notna(x) else "N/A"
                )
            elif col_key in ['profit_margin', 'revenue_growth', 'revenue_growth_quarterly', 'earnings_growth']:
                # Format as percentage with 1 decimal place (already as %)
                formatted_df[col_name] = display_df[col_key].apply(
                    lambda x: f"{x*100:.1f}" if pd.notna(x) else "N/A"
                )
            else:
                # Other numeric values with 2 decimal places
                formatted_df[col_name] = display_df[col_key].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )
    
    # Highlight the main stock
    def highlight_main_stock(row):
        if row['代碼'] == ticker:
            return ['background-color: #1f77b4; color: white'] * len(row)
        return [''] * len(row)
    
    # Display table
    st.dataframe(
        formatted_df.style.apply(highlight_main_stock, axis=1),
        use_container_width=True,
        hide_index=True
    )
    
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
            margin_mean = industry_stats.get('profit_margin_mean')
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
            for metric in ['pe_ratio', 'peg_ratio', 'profit_margin']:
                if metric in rankings:
                    rank_info = rankings[metric]
                    metric_name = {
                        'pe_ratio': 'P/E Ratio',
                        'peg_ratio': 'PEG Ratio',
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
    metrics_for_radar = ['pe_ratio', 'peg_ratio', 'profit_margin', 'revenue_growth']
    
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
            line=dict(width=2 if row['ticker'] == ticker else 1),
            opacity=0.8 if row['ticker'] == ticker else 0.4
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
