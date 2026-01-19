"""
Crypto Trend Index - Data Fetcher
Fetches Google Trends data via SerpAPI and Bitcoin price from Binance
Runs daily via GitHub Actions
"""

import os
import json
import requests
from datetime import datetime, timedelta
import re

# Configuration
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
KEYWORDS = ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
DATA_FILE = 'data.json'


def parse_trend_date(date_str):
    """Parse various date formats from Google Trends"""
    date_str = date_str.strip()
    
    # Handle range format "Jan 5 – 11, 2025" -> take first date
    if '–' in date_str or '-' in date_str:
        date_str = re.split(r'[–-]', date_str)[0].strip()
    
    # Try different formats
    formats = [
        '%b %d, %Y',      # Jan 5, 2025
        '%B %d, %Y',      # January 5, 2025
        '%b %d %Y',       # Jan 5 2025
        '%Y-%m-%d',       # 2025-01-05
        '%b %d',          # Jan 5 (no year)
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # If no year in format, add current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    
    return None


def fetch_google_trends(keyword):
    """Fetch Google Trends data for a single keyword using SerpAPI"""
    url = "https://serpapi.com/search.json"
    params = {
        'engine': 'google_trends',
        'q': keyword,
        'date': 'today 6-m',
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
                date_str = item.get('date', '')
                parsed_date = parse_trend_date(date_str)
                
                if parsed_date and item.get('values'):
                    value = item['values'][0].get('extracted_value', 0)
                    # Handle "<1" values
                    if isinstance(value, str) and '<' in value:
                        value = 0
                    results.append({
                        'date': parsed_date,
                        'value': int(value) if value else 0
                    })
            
            return results
            
    except Exception as e:
        print(f"Error fetching trends for {keyword}: {e}")
    
    return []


def fetch_bitcoin_price_daily():
    """Fetch 6 months of daily Bitcoin price from Binance"""
    url = "https://api.binance.com/api/v3/klines"
    
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=180)).timestamp() * 1000)
    
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1d',  # Daily data
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            datetime.fromtimestamp(candle[0] / 1000).date(): float(candle[4])
            for candle in data
        }
    except Exception as e:
        print(f"Error fetching Bitcoin price: {e}")
    
    return {}


def calculate_trend_index(all_trends_data):
    """Calculate average trend index from all keywords, aligned by date"""
    if not all_trends_data:
        return {}
    
    # Collect all values by date
    date_values = {}
    
    for keyword_data in all_trends_data:
        for item in keyword_data:
            date = item['date'].date()
            if date not in date_values:
                date_values[date] = []
            date_values[date].append(item['value'])
    
    # Calculate average for each date
    return {
        date: round(sum(values) / len(values), 1)
        for date, values in date_values.items()
    }


def find_closest_price(target_date, btc_prices, max_days=3):
    """Find the closest Bitcoin price within max_days"""
    for offset in range(max_days + 1):
        for direction in [0, -1, 1]:
            check_date = target_date + timedelta(days=offset * direction) if direction else target_date
            if check_date in btc_prices:
                return btc_prices[check_date]
    return None


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
            print(f"     Got {len(trends)} data points")
    
    if not all_trends:
        print("❌ Error: Could not fetch any trends data")
        return
    
    # Calculate combined index
    print("📈 Calculating trend index...")
    trend_index = calculate_trend_index(all_trends)
    print(f"   Combined {len(trend_index)} dates")
    
    # Fetch Bitcoin price
    print("💰 Fetching Bitcoin price from Binance...")
    btc_prices = fetch_bitcoin_price_daily()
    print(f"   Got {len(btc_prices)} price points")
    
    if not btc_prices:
        print("❌ Error: Could not fetch Bitcoin price")
        return
    
    # Align data - only include dates where we have both
    print("🔄 Aligning data...")
    
    sorted_dates = sorted(trend_index.keys())
    
    final_dates = []
    final_prices = []
    final_index = []
    
    for date in sorted_dates:
        price = find_closest_price(date, btc_prices)
        if price:
            final_dates.append(date.strftime('%Y-%m-%d'))
            final_prices.append(round(price, 2))
            final_index.append(trend_index[date])
    
    if not final_dates:
        print("❌ Error: Could not align any data points")
        return
    
    # Save to JSON
    output = {
        'dates': final_dates,
        'btc_prices': final_prices,
        'trend_index': final_index,
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'keywords': KEYWORDS
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Data saved to {DATA_FILE}")
    print(f"   - Date range: {final_dates[0]} to {final_dates[-1]}")
    print(f"   - Data points: {len(final_dates)}")
    print(f"   - Latest BTC price: ${final_prices[-1]:,.0f}")
    print(f"   - Latest trend index: {final_index[-1]}")


if __name__ == '__main__':
    main()
