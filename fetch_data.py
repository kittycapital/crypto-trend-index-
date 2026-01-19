"""
Crypto Trend Index - Data Fetcher
Bitcoin price from CoinGecko + Google Trends from SerpAPI
Automatically fetches last 6 months of data
"""

import os
import json
import requests
from datetime import datetime, timedelta

# Configuration
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
KEYWORDS = ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
DATA_FILE = 'data.json'


def get_date_range():
    """Get date range for last 6 months"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


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


def fetch_google_trends(keyword, start_date, end_date):
    """Fetch Google Trends data for a single keyword using SerpAPI"""
    
    url = "https://serpapi.com/search.json"
    params = {
        'engine': 'google_trends',
        'q': keyword,
        'date': f'{start_date} {end_date}',
        'api_key': SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'interest_over_time' in data and 'timeline_data' in data['interest_over_time']:
            timeline = data['interest_over_time']['timeline_data']
            results = []
            
            for item in timeline:
                if 'timestamp' in item:
                    timestamp = int(item['timestamp'])
                    date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    
                    if item.get('values') and len(item['values']) > 0:
                        value = item['values'][0].get('extracted_value', 0)
                        results.append({'date': date, 'value': int(value)})
            
            return results
            
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    return []


def calculate_trend_index(all_trends_data):
    """Calculate average trend index from all keywords"""
    
    if not all_trends_data:
        return {}
    
    date_values = {}
    
    for keyword_data in all_trends_data:
        for item in keyword_data:
            date = item['date']
            if date not in date_values:
                date_values[date] = []
            date_values[date].append(item['value'])
    
    return {
        date: round(sum(values) / len(values), 1)
        for date, values in date_values.items()
    }


def main():
    print("🚀 Starting Crypto Trend Index data fetch...\n")
    
    # Get 6-month date range
    start_date, end_date = get_date_range()
    print(f"📅 Date range: {start_date} to {end_date}\n")
    
    # Step 1: Fetch Bitcoin price
    btc_prices = fetch_bitcoin_price()
    
    if not btc_prices:
        print("❌ Error: Could not fetch Bitcoin price")
        return
    
    # Step 2: Fetch Google Trends
    print(f"\n📊 Fetching Google Trends for {len(KEYWORDS)} keywords...")
    
    if not SERPAPI_KEY:
        print("   ❌ SERPAPI_KEY not found")
        trend_index = {}
    else:
        all_trends = []
        for keyword in KEYWORDS:
            print(f"   - {keyword}...", end=" ")
            trends = fetch_google_trends(keyword, start_date, end_date)
            if trends:
                all_trends.append(trends)
                print(f"✅ {len(trends)} points")
            else:
                print("❌ failed")
        
        trend_index = calculate_trend_index(all_trends)
        print(f"   ✅ Combined trend index: {len(trend_index)} dates")
    
    # Step 3: Align data
    print("\n🔄 Aligning data...")
    
    all_btc_dates = sorted(btc_prices.keys())
    
    final_dates = []
    final_prices = []
    final_index = []
    
    for date in all_btc_dates:
        price = btc_prices[date]
        
        if date in trend_index:
            idx = trend_index[date]
        else:
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
