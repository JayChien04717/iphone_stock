import valuation
import pandas as pd

print("Testing Time Period Logic...")

# Mock Ticker object
class MockTicker:
    def history(self, period='1y'):
        print(f"Fetching history for period: {period}")
        # Return dummy data
        return pd.DataFrame({'Close': [100]}, index=[pd.Timestamp('2023-01-01')])

mock_ticker = MockTicker()

# Test get_historical_data with different periods
periods = ['1y', '3y', '5y', '10y', 'max']
for p in periods:
    valuation.get_historical_data(mock_ticker, period=p)

print("Time period test completed.")
