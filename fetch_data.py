"""
Crypto Trend Index - Data Fetcher
Bitcoin price from CoinGecko + Google Trends from uploaded CSV (already averaged)
"""

import json
import requests
import csv
from datetime import datetime
from pathlib import Path

# Configuration
KEYWORDS = ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
DATA_FILE = 'data.json'
TRENDS_CSV = 'trends.csv'


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


def parse_google_trends_csv():
    """Parse simple 2-column CSV (Date, Index)"""
    
    print(f"\n📊 Reading Trend Index from {TRENDS_CSV}...")
    
    if not Path(TRENDS_CSV).exists():
        print(f"   ❌ {TRENDS_CSV} not found")
        return {}
    
    trend_index = {}
    
    with open(TRENDS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Skip header row
        header = next(reader, None)
        print(f"   📋 Header: {header}")
        
        for row in reader:
            if not row or len(row) < 2:
                continue
            
            try:
                # Parse date (first column)
                date_str = row[0].strip()
                
                # Handle different date formats
                date = None
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%Y-%m', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        date = date_obj.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                
                if not date:
                    continue
                
                # Parse index value (second column)
                val = row[1].strip()
                if '<' in val:
                    index_val = 0.0
                else:
                    index_val = float(val)
                
                trend_index[date] = round(index_val, 1)
                    
            except Exception as e:
                continue
    
    print(f"   ✅ Got {len(trend_index)} data points from CSV")
    
    if trend_index:
        dates = sorted(trend_index.keys())
        print(f"   📅 Range: {dates[0]} to {dates[-1]}")
    
    return trend_index


def main():
    print("🚀 Starting Crypto Trend Index data fetch...\n")
    
    # Step 1: Fetch Bitcoin price
    btc_prices = fetch_bitcoin_price()
    
    if not btc_prices:
        print("❌ Error: Could not fetch Bitcoin price")
        return
    
    # Step 2: Read Google Trends CSV
    trend_index = parse_google_trends_csv()
    
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
