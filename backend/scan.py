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
    # Pine Script: center = sclose
    pp = close 
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
        # Need enough data for monthly resampling (at least 3-4 months)
        data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', threads=True)
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
            if len(df) < 50: continue # Ensure enough data for monthly calc
            
            # --- Daily Data Points ---
            today = df.iloc[-1]
            current_price = today['Close']
            
            # --- 1. Calculate Daily Indicators (for Doji Strategy) ---
            # Row -2 is Yesterday (T-1) for Daily Pivots
            prev_day_daily = df.iloc[-2]
            
            cpr_daily = calculate_cpr_value(prev_day_daily['High'], prev_day_daily['Low'], prev_day_daily['Close'])
            cam_daily = calculate_camarilla_value(prev_day_daily['High'], prev_day_daily['Low'], prev_day_daily['Close'])
            
            # --- 2. Calculate Monthly Indicators (for Inside Cam Strategy) ---
            # Resample to Monthly
            # yfinance index is DatetimeIndex. Resample 'ME' gives last day of month.
            try:
                df_monthly = df.resample('ME').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last'
                })
                
                if len(df_monthly) < 3: continue
                
                # Monthly Pivots for CURRENT Month are based on LAST Month (Row -2)
                last_month = df_monthly.iloc[-2] # Completed
                cam_monthly_curr = calculate_camarilla_value(last_month['High'], last_month['Low'], last_month['Close'])
                cpr_monthly_curr = calculate_cpr_value(last_month['High'], last_month['Low'], last_month['Close'])

                # Monthly Pivots for LAST Month were based on 2 MONTHS AGO (Row -3)
                month_before_last = df_monthly.iloc[-3]
                cam_monthly_prev = calculate_camarilla_value(month_before_last['High'], month_before_last['Low'], month_before_last['Close'])
                
            except Exception as e:
                # print(f"Monthly resample failed for {ticker}: {e}")
                continue

            # --- 3. Strategy Logic ---
            strategies = []
            
            # --- Strategy A: Daily Doji/CPR Setup ---
            is_tight_cpr = cpr_daily['width_pct'] < CPR_WIDTH_THRESHOLD
            dist_to_center = abs(current_price - cam_daily['center']) / cam_daily['center'] * 100
            is_near_center = dist_to_center < 0.3
            has_pattern, pattern_name = check_candle_pattern(today['Open'], today['High'], today['Low'], today['Close'])
            is_above_pivot_daily = current_price >= (cpr_daily['pivot'] * 0.999)
            
            # EMA Proximity Check
            # Calculate distance % from 8 and 20 EMA
            dist_ema8 = abs(current_price - ema8) / ema8 * 100
            dist_ema20 = abs(current_price - ema20) / ema20 * 100
            
            # Condition: Near 8 EMA OR Near 20 EMA (within 1.5%)
            is_near_ema = (dist_ema8 < 1.5) or (dist_ema20 < 1.5)
            
            # User said "range for now doesnt matter", so removing is_low_range from Doji strategy
            # Also checking for "Small Candle" if not Doji/Hammer
            if not has_pattern:
                body_size = abs(today['Close'] - today['Open'])
                range_size = today['High'] - today['Low']
                if range_size > 0 and (body_size / range_size) < 0.3: # Body less than 30% of range
                    has_pattern = True
                    pattern_name = "Small Candle"

            if is_tight_cpr and is_near_center and has_pattern and is_above_pivot_daily and is_near_ema:
                strategies.append("Doji_Setup")

            # --- Strategy B: Monthly Inside Camarilla (Pine Script Alignment) ---
            # Requirement: Recent month Camerilla (L3 L4 H3 H4) should be within Last month (L3 L4 H3 H4)
            # Replaced CPR check with Strict Containment as per User Instruction referring to calculation.
            
            is_inside_h3l3 = (cam_monthly_curr['h3'] <= cam_monthly_prev['h3']) and (cam_monthly_curr['l3'] >= cam_monthly_prev['l3'])
            is_inside_h4l4 = (cam_monthly_curr['h4'] <= cam_monthly_prev['h4']) and (cam_monthly_curr['l4'] >= cam_monthly_prev['l4'])
            
            if is_inside_h3l3 and is_inside_h4l4:
                strategies.append("Inside_Camarilla")

            # --- 4. Add to List ---
            if strategies:
                valid_stocks.append({
                    "ticker": ticker.replace(".NS", ""),
                    "price": round(current_price, 2),
                    "strategies": strategies,
                    "range_pct": round(today_range_pct, 2),
                    
                    # Store Daily levels for Doji tab
                    "daily": {
                         "cpr_width": cpr_daily['width_pct'],
                         "cam_center": cam_daily['center'],
                         "pivot": cpr_daily['pivot']
                    },
                    
                    # Store Monthly levels for Inside Tab
                    "monthly": {
                        "curr_h3": cam_monthly_curr['h3'],
                        "prev_h3": cam_monthly_prev['h3'],
                        "curr_l3": cam_monthly_curr['l3'],
                        "prev_l3": cam_monthly_prev['l3'],
                        "pivot": cpr_monthly_curr['pivot']
                    }
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
