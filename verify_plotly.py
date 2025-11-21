import plotly.graph_objects as go
import pandas as pd

print("Testing Plotly...")

try:
    # Create dummy data
    df = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [99, 100, 101],
        'Close': [102, 103, 104]
    }, index=pd.date_range(start='2023-01-01', periods=3))

    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='Price'))
    
    print("Plotly Figure created successfully.")
    
    # Check if layout update works
    fig.update_layout(title="Test Chart")
    print("Layout updated successfully.")
    
except Exception as e:
    print(f"Plotly Error: {e}")
    exit(1)
