import yfinance as yf
import pandas as pd

def check_candle_pattern(open_p, high_p, low_p, close_p):
    body = abs(close_p - open_p)
    total_range = high_p - low_p
    
    print(f"  O:{open_p} H:{high_p} L:{low_p} C:{close_p}")
    print(f"  Body: {body:.2f}, Range: {total_range:.2f}")
    
    if total_range == 0: return False, "None"
    
    is_doji = body <= (total_range * 0.1)
    print(f"  is_doji (Body <= 10% Range): {is_doji}")
    
    upper_wick = high_p - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low_p
    is_hammer = (lower_wick > 2 * body) and (upper_wick < body)
    print(f"  is_hammer: {is_hammer}")
    
    if is_doji: return True, "Doji"
    if is_hammer: return True, "Hammer"
    
    # Fallback Small Candle
    is_small = (body / total_range) < 0.3
    print(f"  is_small (Body < 30% Range): {is_small}")
    
    if is_small: return True, "Small Candle"
    
    return False, "None"

def test_scan():
    tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "HDFCBANK.NS"]
    print(f"Downloading {tickers}...")
    data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', threads=True)
    
    for ticker in tickers:
        print(f"\nTesting {ticker}...")
        try:
            df = data[ticker].dropna()
            if df.empty:
                print("  No data")
                continue
            
            today = df.iloc[-1]
            print(f"  Date: {today.name}")
            
            res, name = check_candle_pattern(today['Open'], today['High'], today['Low'], today['Close'])
            print(f"  Result: {res} ({name})")
            
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_scan()
