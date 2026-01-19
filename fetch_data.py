"""
Crypto Trend Index - Data Fetcher
Step 1: Bitcoin price only from CoinGecko
"""

import json
import requests
from datetime import datetime, timedelta

DATA_FILE = 'data.json'


def fetch_bitcoin_price():
    """Fetch 6 months of daily Bitcoin price from CoinGecko"""
    
    # CoinGecko free API - no key needed
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        'vs_currency': 'usd',
        'days': 180,
        'interval': 'daily'
    }
    
    print(f"📡 Fetching BTC price from CoinGecko...")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    dates = []
    prices = []
    
    for item in data['prices']:
        timestamp = item[0] / 1000  # Convert milliseconds to seconds
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        price = item[1]
        dates.append(date)
        prices.append(round(price, 2))
    
    print(f"   From: {dates[0]}")
    print(f"   To: {dates[-1]}")
    
    return dates, prices


def main():
    print("🚀 Starting Bitcoin price fetch...")
    
    try:
        dates, prices = fetch_bitcoin_price()
        
        print(f"✅ Got {len(dates)} days of data")
        print(f"   First: {dates[0]} - ${prices[0]:,.0f}")
        print(f"   Last: {dates[-1]} - ${prices[-1]:,.0f}")
        
        # Create placeholder trend index (same length as prices)
        trend_index = [50.0] * len(dates)
        
        output = {
            'dates': dates,
            'btc_prices': prices,
            'trend_index': trend_index,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'keywords': ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
        }
        
        with open(DATA_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"💾 Saved to {DATA_FILE}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == '__main__':
    main()
