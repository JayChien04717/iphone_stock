import yfinance as yf

def debug_peg(ticker_symbol):
    print(f"--- Debugging PEG for {ticker_symbol} ---")
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    
    print(f"pegRatio: {info.get('pegRatio')}")
    print(f"trailingPegRatio: {info.get('trailingPegRatio')}")
    print(f"trailingPE: {info.get('trailingPE')}")
    print(f"forwardPE: {info.get('forwardPE')}")
    print(f"earningsGrowth: {info.get('earningsGrowth')}")
    print(f"revenueGrowth: {info.get('revenueGrowth')}")
    
    # Check for any key containing 'peg'
    peg_keys = [k for k in info.keys() if 'peg' in k.lower()]
    print(f"Keys containing 'peg': {peg_keys}")

if __name__ == "__main__":
    debug_peg("AAPL")
    debug_peg("TSLA")
