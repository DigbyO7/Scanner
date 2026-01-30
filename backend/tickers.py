import pandas as pd
import requests
import io
import os
import time

CACHE_FILE = os.path.join(os.path.dirname(__file__), "nifty500.csv")
# Cache valid for 24 hours
MAX_CACHE_AGE = 86400 

def get_nifty500_tickers():
    """
    Fetches Nifty 500 tickers.
    Priority:
    1. Local Cache (nifty500.csv) if < 24h old.
    2. Web Download (NSE).
    3. Local Cache (Stale) if download fails.
    4. Hardcoded Fallback.
    """
    
    # 1. Try Cache (Fresh)
    if os.path.exists(CACHE_FILE):
        try:
            age = time.time() - os.path.getmtime(CACHE_FILE)
            if age < MAX_CACHE_AGE:
                print("Using cached ticker list.")
                return load_tickers_from_file(CACHE_FILE)
        except Exception as e:
            print(f"Error reading cache: {e}")

    # 2. Try Web
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching Nifty 500 list from {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Validate content before saving
        text = response.text
        if "Symbol" in text or "Company Name" in text:
            with open(CACHE_FILE, 'w') as f:
                f.write(text)
            print("Successfully fetched and cached Nifty 500 list.")
            return parse_csv(text)
            
    except Exception as e:
        print(f"Error fetching Nifty 500 list: {e}")

    # 3. Try Cache (Stale)
    if os.path.exists(CACHE_FILE):
        print("Using stale cache file.")
        try:
             return load_tickers_from_file(CACHE_FILE)
        except: pass

    # 4. Fallback
    print("Web fetch failed and no cache. Using hardcoded fallback (Top 50).")
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "HINDUNILVR.NS",
        "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "ULTRACEMCO.NS",
        "ONGC.NS", "NTPC.NS", "TATAMOTORS.NS", "POWERGRID.NS", "ADANIENT.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "M&M.NS", "COALINDIA.NS", "ADANIPORTS.NS",
        "BAJAJFINSV.NS", "WIPRO.NS", "BPCL.NS", "NESTLEIND.NS", "TECHM.NS", "HINDALCO.NS", "GRASIM.NS", "CIPLA.NS", "EICHERMOT.NS", "SBI_LIFE.NS",
        "DRREDDY.NS", "BRITANNIA.NS", "TATACONSUM.NS", "HEROMOTOCO.NS", "APOLLOHOSP.NS", "DIVISLAB.NS", "INDUSINDBK.NS", "BAJAJ-AUTO.NS", "UPL.NS"
    ]

def load_tickers_from_file(path):
    with open(path, 'r') as f:
        return parse_csv(f.read())

def parse_csv(text):
    try:
        df = pd.read_csv(io.StringIO(text))
        if 'Symbol' in df.columns:
            return [f"{symbol}.NS" for symbol in df['Symbol'].tolist()]
        elif 'Company Name' in df.columns: # Fallback if header is weird
             # Logic to find symbol? Usually it's close.
             # If completely fail, return empty list to trigger fallback logic?
             pass
        return []
    except:
        return []

if __name__ == "__main__":
    t = get_nifty500_tickers()
    print(f"Fetched {len(t)} tickers.")
