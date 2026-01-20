"""
Crypto Trend Index - Data Fetcher
Bitcoin price from CoinGecko + Google Trends from uploaded CSV
Supports both 6-month and 12-month data
"""

import json
import requests
import csv
from datetime import datetime
from pathlib import Path

# Configuration
KEYWORDS = ['Bitcoin', 'Crypto', 'Binance', 'CoinMarketCap', 'DefiLlama']
DATA_FILE = 'data.json'
TRENDS_CSV_6M = 'trends.csv'
TRENDS_CSV_12M = 'trends12.csv'


def fetch_bitcoin_price(days):
    """Fetch Bitcoin price from CoinGecko"""
    
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    
    print(f"📡 Fetching BTC price ({days} days) from CoinGecko...")
    
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


def parse_google_trends_csv(filename):
    """Parse simple 2-column CSV (Date, Index)"""
    
    print(f"\n📊 Reading Trend Index from {filename}...")
    
    if not Path(filename).exists():
        print(f"   ⚠️ {filename} not found")
        return {}
    
    trend_index = {}
    
    with open(filename, 'r', encoding='utf-8') as f:
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


def align_data(btc_prices, trend_index):
    """Align Bitcoin prices with trend index data"""
    
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
    
    return final_dates, final_prices, final_index


def main():
    print("🚀 Starting Crypto Trend Index data fetch...\n")
    
    # ===== 6-MONTH DATA =====
    print("=" * 50)
    print("Processing 6-MONTH data...")
    print("=" * 50)
    
    btc_prices_6m = fetch_bitcoin_price(180)
    trend_index_6m = parse_google_trends_csv(TRENDS_CSV_6M)
    
    print("\n🔄 Aligning 6-month data...")
    dates_6m, prices_6m, index_6m = align_data(btc_prices_6m, trend_index_6m)
    print(f"   ✅ Aligned {len(dates_6m)} data points")
    
    # ===== 12-MONTH DATA =====
    print("\n" + "=" * 50)
    print("Processing 12-MONTH data...")
    print("=" * 50)
    
    btc_prices_12m = fetch_bitcoin_price(365)
    trend_index_12m = parse_google_trends_csv(TRENDS_CSV_12M)
    
    print("\n🔄 Aligning 12-month data...")
    dates_12m, prices_12m, index_12m = align_data(btc_prices_12m, trend_index_12m)
    print(f"   ✅ Aligned {len(dates_12m)} data points")
    
    # ===== SAVE DATA =====
    output = {
        # 6-month data (default)
        'dates': dates_6m,
        'btc_prices': prices_6m,
        'trend_index': index_6m,
        # 12-month data
        'dates_12m': dates_12m,
        'btc_prices_12m': prices_12m,
        'trend_index_12m': index_12m,
        # Metadata
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'keywords': KEYWORDS
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved to {DATA_FILE}")
    print(f"\n📊 Summary:")
    print(f"   6M: {dates_6m[0]} to {dates_6m[-1]} ({len(dates_6m)} days)")
    print(f"   12M: {dates_12m[0]} to {dates_12m[-1]} ({len(dates_12m)} days)")
    print(f"   💰 Latest BTC: ${prices_6m[-1]:,.0f}")
    print(f"   📈 Latest Index (6M): {index_6m[-1]}")
    print(f"   📈 Latest Index (12M): {index_12m[-1]}")


if __name__ == '__main__':
    main()
