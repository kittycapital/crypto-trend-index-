"""
Crypto Trend Index - Data Fetcher
Bitcoin price from CoinGecko + Google Trends from pytrends (free, no API key)
"""

import json
import requests
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import time

# Configuration
KEYWORDS = ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
DATA_FILE = 'data.json'


def fetch_bitcoin_price():
    """Fetch 6 months of daily Bitcoin price from CoinGecko"""
    
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        'vs_currency': 'usd',
        'days': 180,
        'interval': 'daily'
    }
    
    print("📡 Fetching BTC price from CoinGecko...")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    prices_by_date = {}
    
    for item in data['prices']:
        timestamp = item[0] / 1000
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        price = item[1]
        prices_by_date[date] = round(price, 2)
    
    print(f"   ✅ Got {len(prices_by_date)} days of price data")
    
    return prices_by_date


def fetch_google_trends():
    """Fetch Google Trends data using pytrends"""
    
    print(f"\n📊 Fetching Google Trends for {len(KEYWORDS)} keywords...")
    
    try:
        # Initialize pytrends
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Build payload with all keywords at once (max 5)
        pytrends.build_payload(KEYWORDS, cat=0, timeframe='today 6-m', geo='', gprop='')
        
        # Get interest over time
        df = pytrends.interest_over_time()
        
        if df.empty:
            print("   ❌ No data returned")
            return {}
        
        # Calculate average across all keywords for each date
        trend_index = {}
        
        for date, row in df.iterrows():
            date_str = date.strftime('%Y-%m-%d')
            values = [row[kw] for kw in KEYWORDS if kw in row]
            if values:
                avg = sum(values) / len(values)
                trend_index[date_str] = round(avg, 1)
        
        print(f"   ✅ Got {len(trend_index)} data points")
        
        for kw in KEYWORDS:
            if kw in df.columns:
                latest = df[kw].iloc[-1]
                print(f"      - {kw}: {latest}")
        
        return trend_index
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {}


def main():
    print("🚀 Starting Crypto Trend Index data fetch...\n")
    
    # Step 1: Fetch Bitcoin price
    btc_prices = fetch_bitcoin_price()
    
    if not btc_prices:
        print("❌ Error: Could not fetch Bitcoin price")
        return
    
    # Step 2: Fetch Google Trends
    trend_index = fetch_google_trends()
    
    # Step 3: Align data
    print("\n🔄 Aligning data...")
    
    all_btc_dates = sorted(btc_prices.keys())
    
    final_dates = []
    final_prices = []
    final_index = []
    
    for date in all_btc_dates:
        price = btc_prices[date]
        
        # Find matching or nearest trend index
        if date in trend_index:
            idx = trend_index[date]
        else:
            # Find nearest trend date within 7 days
            nearest_idx = None
            min_diff = 8
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            
            for trend_date, trend_val in trend_index.items():
                trend_date_obj = datetime.strptime(trend_date, '%Y-%m-%d')
                diff = abs((date_obj - trend_date_obj).days)
                if diff < min_diff:
                    min_diff = diff
                    nearest_idx = trend_val
            
            idx = nearest_idx if nearest_idx is not None else 50.0
        
        final_dates.append(date)
        final_prices.append(price)
        final_index.append(idx)
    
    print(f"   ✅ Aligned {len(final_dates)} data points")
    
    # Step 4: Save to JSON
    output = {
        'dates': final_dates,
        'btc_prices': final_prices,
        'trend_index': final_index,
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'keywords': KEYWORDS
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved to {DATA_FILE}")
    print(f"   📅 Date range: {final_dates[0]} to {final_dates[-1]}")
    print(f"   💰 Latest BTC: ${final_prices[-1]:,.0f}")
    print(f"   📈 Latest Index: {final_index[-1]}")


if __name__ == '__main__':
    main()
