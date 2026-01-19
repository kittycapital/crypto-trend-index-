"""
Crypto Trend Index - Data Fetcher
Fetches Google Trends data via SerpAPI and Bitcoin price from Binance
Runs daily via GitHub Actions
"""

import os
import json
import requests
from datetime import datetime, timedelta

# Configuration
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
KEYWORDS = ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
DATA_FILE = 'data.json'

def fetch_google_trends(keyword):
    """Fetch Google Trends data for a single keyword using SerpAPI"""
    url = "https://serpapi.com/search.json"
    params = {
        'engine': 'google_trends',
        'q': keyword,
        'date': 'today 6-m',  # Last 6 months
        'api_key': SERPAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract interest over time data
        if 'interest_over_time' in data and 'timeline_data' in data['interest_over_time']:
            timeline = data['interest_over_time']['timeline_data']
            return [
                {
                    'date': item['date'].split(' – ')[0] if ' – ' in item['date'] else item['date'],
                    'value': item['values'][0]['extracted_value'] if item['values'] else 0
                }
                for item in timeline
            ]
    except Exception as e:
        print(f"Error fetching trends for {keyword}: {e}")
    
    return []


def fetch_bitcoin_price():
    """Fetch 6 months of daily Bitcoin price from Binance"""
    url = "https://api.binance.com/api/v3/klines"
    
    # Calculate timestamps for 6 months ago
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=180)).timestamp() * 1000)
    
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1w',  # Weekly to match Google Trends
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                'date': datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d'),
                'price': float(candle[4])  # Close price
            }
            for candle in data
        ]
    except Exception as e:
        print(f"Error fetching Bitcoin price: {e}")
    
    return []


def calculate_trend_index(all_trends_data):
    """Calculate average trend index from all keywords"""
    if not all_trends_data or not all_trends_data[0]:
        return []
    
    # Get dates from first keyword (all should have same dates)
    dates = [item['date'] for item in all_trends_data[0]]
    
    # Calculate average for each date
    index_values = []
    for i in range(len(dates)):
        values = []
        for keyword_data in all_trends_data:
            if i < len(keyword_data):
                values.append(keyword_data[i]['value'])
        
        avg = sum(values) / len(values) if values else 0
        index_values.append(round(avg, 1))
    
    return dates, index_values


def align_data(trend_dates, trend_index, btc_data):
    """Align Bitcoin prices with trend dates"""
    btc_dict = {item['date']: item['price'] for item in btc_data}
    
    aligned_dates = []
    aligned_prices = []
    aligned_index = []
    
    for i, date in enumerate(trend_dates):
        # Find closest Bitcoin price date
        trend_date = datetime.strptime(date, '%b %d, %Y') if ', ' in date else datetime.strptime(date, '%Y-%m-%d')
        trend_date_str = trend_date.strftime('%Y-%m-%d')
        
        # Look for matching or closest date in BTC data
        best_price = None
        min_diff = float('inf')
        
        for btc_date_str, price in btc_dict.items():
            btc_date = datetime.strptime(btc_date_str, '%Y-%m-%d')
            diff = abs((btc_date - trend_date).days)
            if diff < min_diff:
                min_diff = diff
                best_price = price
        
        if best_price is not None and min_diff <= 7:  # Within a week
            aligned_dates.append(trend_date_str)
            aligned_prices.append(round(best_price, 2))
            aligned_index.append(trend_index[i])
    
    return aligned_dates, aligned_prices, aligned_index


def main():
    print("🚀 Starting Crypto Trend Index data fetch...")
    
    if not SERPAPI_KEY:
        print("❌ Error: SERPAPI_KEY not found in environment variables")
        return
    
    # Fetch Google Trends for all keywords
    print(f"📊 Fetching Google Trends for {len(KEYWORDS)} keywords...")
    all_trends = []
    for keyword in KEYWORDS:
        print(f"   - {keyword}")
        trends = fetch_google_trends(keyword)
        if trends:
            all_trends.append(trends)
    
    if not all_trends:
        print("❌ Error: Could not fetch any trends data")
        return
    
    # Calculate combined index
    print("📈 Calculating trend index...")
    trend_dates, trend_index = calculate_trend_index(all_trends)
    
    # Fetch Bitcoin price
    print("💰 Fetching Bitcoin price...")
    btc_data = fetch_bitcoin_price()
    
    if not btc_data:
        print("❌ Error: Could not fetch Bitcoin price")
        return
    
    # Align data
    print("🔄 Aligning data...")
    dates, btc_prices, final_index = align_data(trend_dates, trend_index, btc_data)
    
    # Save to JSON
    output = {
        'dates': dates,
        'btc_prices': btc_prices,
        'trend_index': final_index,
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'keywords': KEYWORDS
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Data saved to {DATA_FILE}")
    print(f"   - Data points: {len(dates)}")
    print(f"   - Latest BTC price: ${btc_prices[-1]:,.0f}" if btc_prices else "")
    print(f"   - Latest trend index: {final_index[-1]}" if final_index else "")


if __name__ == '__main__':
    main()
