import pandas as pd
import requests
import io

def get_nifty500_tickers():
    """
    Fetches the Nifty Total Market stock list from NSE archives or fallback to Nifty 500.
    Returns a list of tickers with '.NS' suffix for yfinance.
    """
    url = "https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching Nifty Total Market list from {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        
        # Check if 'Symbol' column exists
        if 'Symbol' in df.columns:
            tickers = [f"{symbol}.NS" for symbol in df['Symbol'].tolist()]
            print(f"Successfully fetched {len(tickers)} tickers.")
            return tickers
        elif 'Company Name' in df.columns and 'Symbol' not in df.columns:
             # Try to find symbol column if named differently, or fallback
            print("Layout changed, could not find 'Symbol' column.")
            raise ValueError("CSV format unexpected")
            
    except Exception as e:
        print(f"Error fetching Nifty 500 list: {e}")
        print("Using fallback list (Top 10 stocks).")
        # Fallback list of top NSE stocks
        return [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
            "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "HINDUNILVR.NS"
        ]

if __name__ == "__main__":
    tickers = get_nifty500_tickers()
    print(tickers[:10])
