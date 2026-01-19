"""
Crypto Trend Index - Data Fetcher
Step 1: Bitcoin price only from Binance
"""

import json
import requests
from datetime import datetime, timedelta

DATA_FILE = 'data.json'


def fetch_bitcoin_price():
    """Fetch 6 months of daily Bitcoin price from Binance"""
    url = "https://api.binance.com/api/v3/klines"
    
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=180)).timestamp() * 1000)
    
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1d',
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    print(f"📡 Fetching BTC price from Binance...")
    print(f"   From: {datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d')}")
    print(f"   To: {datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d')}")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    dates = []
    prices = []
    
    for candle in data:
        date = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d')
        price = float(candle[4])  # Close price
        dates.append(date)
        prices.append(round(price, 2))
    
    return dates, prices


def main():
    print("🚀 Starting Bitcoin price fetch...")
    
    try:
        dates, prices = fetch_bitcoin_price()
        
        print(f"✅ Got {len(dates)} days of data")
        print(f"   First date: {dates[0]} - ${prices[0]:,.0f}")
        print(f"   Last date: {dates[-1]} - ${prices[-1]:,.0f}")
        
        # Create placeholder trend index (same length as prices)
        # Will be replaced with real Google Trends data later
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
