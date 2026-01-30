import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json
import os
import datetime
import numpy as np
from tickers import get_nifty500_tickers

# Configuration
OUTPUT_FILE = "../frontend/public/data.json"
DAYS_BACK = 60
CAMARILLA_DOJI_THRESHOLD = 0.05
CPR_WIDTH_THRESHOLD = 0.5

def calculate_cpr_value(high, low, close):
    pivot = (high + low + close) / 3
    bc = (high + low) / 2
    tc = (pivot - bc) + pivot
    return {
        'pivot': round(pivot, 2),
        'bc': round(bc, 2),
        'tc': round(tc, 2),
        'width_pct': round(abs(tc - bc) / pivot * 100, 2)
    }

def calculate_camarilla_value(high, low, close):
    r = high - low
    h3 = close + (r * 1.1) / 4
    l3 = close - (r * 1.1) / 4
    h4 = close + (r * 1.1) / 2
    l4 = close - (r * 1.1) / 2
    pp = (high + low + close) / 3
    return {
        'h3': round(h3, 2),
        'l3': round(l3, 2),
        'h4': round(h4, 2),
        'l4': round(l4, 2),
        'center': round(pp, 2)
    }

def check_candle_pattern(open_p, high_p, low_p, close_p):
    body = abs(close_p - open_p)
    total_range = high_p - low_p
    if total_range == 0: return False, "None"
    
    is_doji = body <= (total_range * 0.1)
    upper_wick = high_p - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low_p
    is_hammer = (lower_wick > 2 * body) and (upper_wick < body)
    
    if is_doji: return True, "Doji"
    if is_hammer: return True, "Hammer"
    return False, "None"

def scan_stocks():
    print("Starting stock scan...")
    tickers = get_nifty500_tickers()
    valid_stocks = []
    
    print(f"Downloading data for {len(tickers)} tickers...")
    try:
        data = yf.download(tickers, period="3mo", interval="1d", group_by='ticker', threads=True)
    except Exception as e:
        print(f"Bulk download failed: {e}")
        return {"stocks": []}

    if data is None or data.empty:
         print("No data received.")
         return {"stocks": []}

    print("Processing data...")
    
    for ticker in tickers:
        try:
            if len(tickers) > 1:
                df = data[ticker].copy()
            else:
                df = data.copy()
            
            df.dropna(inplace=True)
            if len(df) < 5: continue
            
            # Data Points
            # Row -1: Today (Live/Latest)
            # Row -2: Yesterday (T-1) -> Used for Today's levels
            # Row -3: Day Before (T-2) -> Used for Yesterday's levels
            
            today = df.iloc[-1]
            prev_day = df.iloc[-2]  # T-1
            prev_prev = df.iloc[-3] # T-2
            
            current_price = today['Close']
            
            # --- 1. Calculate Indicators ---
            
            # CPR & Camarilla for TODAY (Using T-1)
            cpr_today = calculate_cpr_value(prev_day['High'], prev_day['Low'], prev_day['Close'])
            cam_today = calculate_camarilla_value(prev_day['High'], prev_day['Low'], prev_day['Close'])
            
            # Camarilla for YESTERDAY (Using T-2) - For Inside Cam Strategy
            cam_yesterday = calculate_camarilla_value(prev_prev['High'], prev_prev['Low'], prev_prev['Close'])
            
            # EMAs
            # Calculate on full series to be accurate
            ema8 = ta.ema(df['Close'], length=8).iloc[-1]
            ema20 = ta.ema(df['Close'], length=20).iloc[-1]
            
            # --- 2. Strategy Logic ---
            strategies = []
            
            # --- Strategy A: Doji/CPR Setup ---
            # Criteria 1: Tight CPR
            is_tight_cpr = cpr_today['width_pct'] < CPR_WIDTH_THRESHOLD
            
            # Criteria 2: Near Cam Center
            dist_to_center = abs(current_price - cam_today['center']) / cam_today['center'] * 100
            is_near_center = dist_to_center < 0.3
            
            # Criteria 3: Candlestick Pattern (Reviewing last candle)
            has_pattern, pattern_name = check_candle_pattern(today['Open'], today['High'], today['Low'], today['Close'])
            
            # Criteria 4: Price Near/Above Pivot (Using CPR Pivot as reference)
            # User: "near or above pivot"
            is_above_pivot = current_price >= (cpr_today['pivot'] * 0.999) # 0.1% tolerance
            
            # Criteria 5: Short Daily Range (< 1%)
            today_range_pct = (today['High'] - today['Low']) / current_price * 100
            is_low_range = today_range_pct < 1.0
            
            if is_tight_cpr and is_near_center and has_pattern and is_above_pivot and is_low_range:
                strategies.append("Doji_Setup")

            # --- Strategy B: Inside Camarilla ---
            # "Recent camerilla should be within the previous Camerilla"
            # Today's Range (H3-L3) inside Yesterday's Range (H3-L3)
            # i.e. Today H3 < Yesterday H3  AND  Today L3 > Yesterday L3
            
            is_inside_cam = (cam_today['h3'] < cam_yesterday['h3']) and (cam_today['l3'] > cam_yesterday['l3'])
            
            if is_inside_cam:
                strategies.append("Inside_Camarilla")

            # --- 3. Add to List if any strategy matches ---
            if strategies:
                valid_stocks.append({
                    "ticker": ticker.replace(".NS", ""),
                    "price": round(current_price, 2),
                    "cpr": cpr_today,
                    "camarilla": cam_today,
                    "prev_camarilla": cam_yesterday, # Useful for visualizing "Inside"
                    "strategies": strategies,
                    "signal": ", ".join(strategies), # For simple display
                    "range_pct": round(today_range_pct, 2),
                    "ema_status": f"EMA8: {round(ema8,1)}, EMA20: {round(ema20,1)}"
                })

        except Exception as e:
            continue
            
    # Output
    result = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stocks": valid_stocks
    }
    
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Data saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Warning: Could not save to file: {e}")
        
    print(f"Scan complete. Found {len(valid_stocks)} stocks.")
    return result

if __name__ == "__main__":
    scan_stocks()
