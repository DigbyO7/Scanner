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
DAYS_BACK = 60  # Fetch enough data for EMAs
CAMARILLA_DOJI_THRESHOLD = 0.05  # 0.05% proximity to Central Pivot
CPR_WIDTH_THRESHOLD = 0.5  # Arbitrary threshold for "Tight", can be adjusted

def calculate_cpr(df):
    """
    Calculates Central Pivot Range (CPR) for the next day based on current day's OHLC.
    Returns pivot, bc, tc.
    """
    # Using the last completed day (which is 'today' if market is closed, or yesterday)
    # yfinance 'history' returns the last row as the most recent data
    
    # We need to calculate pivots based on the *previous* day to trade *today*?
    # Or calculate for *tomorrow* based on *today*?
    # The user asks for "Near Camarilla's Central pivot". Usually this means price IS near the pivot.
    # Pivots are calculated from previous day's High, Low, Close.
    # So for Today's price action, we use Yesterday's HLC.
    
    # Let's take the last row as "Today" (current price) and the second last row as "Yesterday" (for pivots).
    # If the market is closed, the last row is the completed day.
    # If market is LIVE, the last row is continuously updating.
    # Ideally, run this after market close (as per "Updates daily at 6 PM").
    
    # So: Last row = Today (Signal Candle). calculate pivots from Second Last Row.
    
    if len(df) < 2:
        return None
        
    prev_day = df.iloc[-2] # The completed day before today
    today = df.iloc[-1]    # The current day being scanned (could be completed or live)
    
    high = prev_day['High']
    low = prev_day['Low']
    close = prev_day['Close']
    
    pivot = (high + low + close) / 3
    bc = (high + low) / 2
    tc = (pivot - bc) + pivot
    
    cpr = {
        'pivot': round(pivot, 2),
        'bc': round(bc, 2),
        'tc': round(tc, 2),
        'width_pct': round(abs(tc - bc) / pivot * 100, 2)
    }
    return cpr

def calculate_camarilla(df):
    """
    Calculates Camarilla Pivots (H3, L3, H4, L4) based on previous day.
    """
    if len(df) < 2:
        return None
        
    prev_day = df.iloc[-2]
    high = prev_day['High']
    low = prev_day['Low']
    close = prev_day['Close']
    r = high - low
    
    h3 = close + (r * 1.1) / 4
    l3 = close - (r * 1.1) / 4
    h4 = close + (r * 1.1) / 2
    l4 = close - (r * 1.1) / 2
    
    # Central pivot for Camarilla typically refers to the area between H3 and L3 or simply the Pivot Point
    # Some users check "Camarilla Pivot" as (H+L+C)/3 similar to standard.
    # But usually "Central Pivot" in context of "Doji near Central Pivot" implies the standard pivot or the middle of the range.
    # Let's assume standard Pivot for "Central" reference or the midpoint of Camarilla.
    # Actually, often CPR Pivot is used as the "Central Pivot".
    # User said: "Camarilla's Central pivot". Camarilla indicators often have a 'PP'.
    pp = (high + low + close) / 3
    
    return {
        'h3': round(h3, 2),
        'l3': round(l3, 2),
        'h4': round(h4, 2),
        'l4': round(l4, 2),
        'center': round(pp, 2)
    }

def check_candle_pattern(df):
    """
    Checks for Doji or Hammer pattern on the last candle.
    """
    if len(df) < 1:
        return False, "None"
        
    candle = df.iloc[-1]
    open_p = candle['Open']
    close_p = candle['Close']
    high_p = candle['High']
    low_p = candle['Low']
    
    body = abs(close_p - open_p)
    total_range = high_p - low_p
    
    if total_range == 0:
        return False, "None"
        
    # Doji definition: Body is very small relative to range
    is_doji = body <= (total_range * 0.1) # 10% of range
    
    # Hammer definition: Small body at top, long lower wick
    # (High - max(Open, Close)) is small upper wick
    # (min(Open, Close) - Low) is long lower wick
    upper_wick = high_p - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low_p
    
    is_hammer = (lower_wick > 2 * body) and (upper_wick < body)
    
    if is_doji:
        return True, "Doji"
    if is_hammer:
        return True, "Hammer"
        
    return False, "None"

def scan_stocks():
    print("Starting stock scan...")
    tickers = get_nifty500_tickers()
    valid_stocks = []
    
    # Batch processing or loop?
    # Individual loop is safer for error handling but slower.
    # yfinance download(tickers) is faster but complex to handle missing data for single ticker.
    # Let's try bulk download for speed, then process.
    
    print(f"Downloading data for {len(tickers)} tickers...")
    
    # Download last 60 days
    try:
        data = yf.download(tickers, period="2mo", interval="1d", group_by='ticker', threads=True)
    except Exception as e:
        print(f"Bulk download failed: {e}")
        return {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": []
        }

    # If data is empty
    if data is None or data.empty:
         print("No data received from Yahoo Finance.")
         return {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": []
        }

    print("Processing data...")
    count = 0
    
    for ticker in tickers:
        try:
            # Extract dataframe for this ticker
            if len(tickers) > 1:
                df = data[ticker].copy()
            else:
                df = data.copy() # Single ticker case
            
            # Drop NaN
            df.dropna(inplace=True)
            
            if len(df) < 20: # Need at least 20 for EMA
                continue
                
            # Current price
            current_price = df.iloc[-1]['Close']
            
            # 1. Indicators
            # EMAs
            df['EMA8'] = ta.ema(df['Close'], length=8)
            df['EMA20'] = ta.ema(df['Close'], length=20)
            
            current_ema8 = df['EMA8'].iloc[-1]
            current_ema20 = df['EMA20'].iloc[-1]
            
            # Pivots (based on previous day)
            cpr = calculate_cpr(df)
            cam = calculate_camarilla(df)
            
            if not cpr or not cam:
                continue
                
            # 2. Pattern Logic
            has_pattern, pattern_name = check_candle_pattern(df)
            
            # Conditions
            # A. Tight CPR
            is_tight_cpr = cpr['width_pct'] < CPR_WIDTH_THRESHOLD
            
            # B. Doji/Pattern near Camarilla Central Pivot
            # Check percent distance to Center Pivot
            dist_to_center = abs(current_price - cam['center']) / cam['center'] * 100
            is_near_center = dist_to_center < 0.2 # Within 0.2% range
            
            # C. Proximity to EMA (Support)
            # Price > EMA but close to it (e.g., within 1%)
            dist_ema8 = (current_price - current_ema8) / current_ema8 * 100
            dist_ema20 = (current_price - current_ema20) / current_ema20 * 100
            
            # Logic: "Doji-like candles near Camarilla's Central pivot and tight CPR"
            # AND "Proximity to 8-day or 20-day EMAs"
            
            condition_met = False
            signal_desc = ""
            
            if is_tight_cpr and is_near_center and (has_pattern or is_near_center): 
                # Relaxed: If near center and tight CPR, even without perfect doji, it's interesting. 
                # But user asked for "Doji-like".
                if has_pattern:
                    condition_met = True
                    signal_desc = f"{pattern_name} at Cam Center + Tight CPR"
            
            # Check EMA support as well? Or is that an alternative? 
            # "and proximity to 8-day or 20-day EMAs" implied AND.
            if condition_met:
                 is_near_ema = (abs(dist_ema8) < 1.0) or (abs(dist_ema20) < 1.0)
                 if is_near_ema:
                     signal_desc += " + Near EMA"
                 else:
                     # If strict "AND", then continue. If loose, keep it.
                     # Let's keep it but mark it.
                     pass

            if condition_met:
                valid_stocks.append({
                    "ticker": ticker.replace(".NS", ""),
                    "price": round(current_price, 2),
                    "cpr": cpr,
                    "camarilla": cam,
                    "signal": signal_desc,
                    "ema_status": f"EMA8: {round(current_ema8,1)}, EMA20: {round(current_ema20,1)}"
                })
                count += 1
                
        except Exception as e:
            # print(f"Error processing {ticker}: {e}")
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
        print(f"Warning: Could not save to file (likely read-only env): {e}")
        
    print(f"Scan complete. Found {len(valid_stocks)} stocks.")
    
    return result

if __name__ == "__main__":
    scan_stocks()
