"""
Multi-API Data Provider
Integrates multiple free APIs with fallback logic
"""
import os
import requests
from datetime import datetime, timedelta

# API Keys (set as environment variables or Streamlit secrets)
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')  # Free: 60 calls/min
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')  # Free: 25 calls/day

class MultiAPIProvider:
    """
    Provides stock data from multiple sources with automatic fallback
    """
    
    def __init__(self):
        self.finnhub_base = "https://finnhub.io/api/v1"
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
    
    def get_company_news(self, ticker, days=7):
        """
        Get company news from Finnhub
        Free tier: 60 calls/minute
        """
        if not FINNHUB_API_KEY:
            return None
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            url = f"{self.finnhub_base}/company-news"
            params = {
                'symbol': ticker,
                'from': start_date,
                'to': end_date,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching news from Finnhub: {e}")
            return None
    
    def get_sentiment_analysis(self, ticker):
        """
        Get sentiment analysis from Finnhub
        Returns: bullish/bearish sentiment scores
        """
        if not FINNHUB_API_KEY:
            return None
        
        try:
            url = f"{self.finnhub_base}/news-sentiment"
            params = {
                'symbol': ticker,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching sentiment from Finnhub: {e}")
            return None
    
    def get_recommendation_trends(self, ticker):
        """
        Get analyst recommendation trends from Finnhub
        """
        if not FINNHUB_API_KEY:
            return None
        
        try:
            url = f"{self.finnhub_base}/stock/recommendation"
            params = {
                'symbol': ticker,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching recommendations from Finnhub: {e}")
            return None
    
    def get_company_profile(self, ticker):
        """
        Get detailed company profile from Finnhub
        """
        if not FINNHUB_API_KEY:
            return None
        
        try:
            url = f"{self.finnhub_base}/stock/profile2"
            params = {
                'symbol': ticker,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching profile from Finnhub: {e}")
            return None
    
    def get_peers(self, ticker):
        """
        Get industry peers from Finnhub
        This is better than our hardcoded list!
        """
        if not FINNHUB_API_KEY:
            return None
        
        try:
            url = f"{self.finnhub_base}/stock/peers"
            params = {
                'symbol': ticker,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                peers = response.json()
                # Filter out the ticker itself and limit to 10
                return [p for p in peers if p != ticker][:10]
            return None
        except Exception as e:
            print(f"Error fetching peers from Finnhub: {e}")
            return None
    
    def get_technical_indicators(self, ticker, indicator='RSI', resolution='D', timeperiod=14):
        """
        Get technical indicators from Alpha Vantage
        Free tier: 25 calls/day (use sparingly)
        """
        if not ALPHA_VANTAGE_API_KEY:
            return None
        
        try:
            # Map indicator names to Alpha Vantage function names
            indicator_map = {
                'RSI': 'RSI',
                'MACD': 'MACD',
                'SMA': 'SMA',
                'EMA': 'EMA'
            }
            
            function = indicator_map.get(indicator, 'RSI')
            
            params = {
                'function': function,
                'symbol': ticker,
                'interval': 'daily',
                'time_period': timeperiod,
                'series_type': 'close',
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(self.alpha_vantage_base, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching indicators from Alpha Vantage: {e}")
            return None
    
    def get_earnings_calendar(self, ticker):
        """
        Get earnings calendar from Finnhub
        """
        if not FINNHUB_API_KEY:
            return None
        
        try:
            url = f"{self.finnhub_base}/calendar/earnings"
            params = {
                'symbol': ticker,
                'token': FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching earnings calendar from Finnhub: {e}")
            return None


# Global instance
api_provider = MultiAPIProvider()


def has_api_keys():
    """Check if any API keys are configured"""
    return bool(FINNHUB_API_KEY or ALPHA_VANTAGE_API_KEY)


def get_api_status():
    """Get status of configured APIs"""
    status = {
        'finnhub': bool(FINNHUB_API_KEY),
        'alpha_vantage': bool(ALPHA_VANTAGE_API_KEY)
    }
    return status
