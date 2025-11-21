import yfinance as yf

def check_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    
    print(f"--- Data for {ticker_symbol} ---")
    print(f"Beta: {info.get('beta')}")
    print(f"Total Debt: {info.get('totalDebt')}")
    print(f"Market Cap: {info.get('marketCap')}")
    print(f"Interest Expense: {info.get('interestExpense')}") # Might need to check financials if not in info
    
    # Check financials for interest expense and tax if not in info
    financials = ticker.financials
    print("\n--- Financials (Index) ---")
    print(financials.index)
    
    try:
        interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index else "N/A"
        tax_provision = financials.loc['Tax Provision'].iloc[0] if 'Tax Provision' in financials.index else "N/A"
        pretax_income = financials.loc['Pretax Income'].iloc[0] if 'Pretax Income' in financials.index else "N/A"
        
        print(f"\nInterest Expense (Financials): {interest_expense}")
        print(f"Tax Provision: {tax_provision}")
        print(f"Pretax Income: {pretax_income}")
    except Exception as e:
        print(f"Error reading financials: {e}")

    # Risk Free Rate
    try:
        tnx = yf.Ticker("^TNX")
        rf_rate = tnx.history(period="1d")['Close'].iloc[-1]
        print(f"\nRisk Free Rate (^TNX): {rf_rate}%")
    except Exception as e:
        print(f"Error fetching Risk Free Rate: {e}")

    print(f"\nTrailing PE: {info.get('trailingPE')}")
    print(f"Forward PE: {info.get('forwardPE')}")

if __name__ == "__main__":
    check_data("AAPL")
