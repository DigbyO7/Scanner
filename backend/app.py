import streamlit as st
import pandas as pd
import scan
import datetime

st.set_page_config(page_title="Camarilla Stock Scanner", layout="wide")

st.title("📈 Camarilla & CPR Stock Scanner")
st.markdown("Identify swing trading setups with **Doji/Hammer** patterns and **Inside Camarilla** setups.")

# Initialize session state for data
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = "Never"

def run_scan():
    with st.spinner('Scanning Nifty Total/500 stocks... This may take a minute.'):
        try:
            result = scan.scan_stocks()
            if result and 'stocks' in result:
                st.session_state.scan_data = result['stocks']
                st.session_state.last_updated = result.get('last_updated', 'Just now')
                st.success(f"Scan Complete! Found {len(result['stocks'])} stocks.")
            else:
                 st.error("Scan returned no data. Check logs or temporary API issues.")
        except Exception as e:
            st.error(f"Error during scan: {e}")

# Sidebar controls
st.sidebar.header("Scanner Controls")
if st.sidebar.button("Run Daily Scan", type="primary"):
    run_scan()

st.sidebar.markdown("---")
st.sidebar.info(f"Last Updated: {st.session_state.last_updated}")

# Main Display
if st.session_state.scan_data:
    stocks = st.session_state.scan_data
    
    if len(stocks) == 0:
        st.warning("No stocks matched any criteria today.")
    else:
        # Create Tabs
        tab1, tab2 = st.tabs(["🕯️ Doji / CPR Setups", "📉 Inside Camarilla"])
        
        # --- Helper to create DF ---
        def create_df(strategy_name):
            filtered = [s for s in stocks if strategy_name in s.get('strategies', [])]
            if not filtered: return pd.DataFrame()
            
            data = []
            for s in filtered:
                tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{s['ticker']}"
                row = {
                    "Ticker": s['ticker'],
                    "Price": s['price'],
                    "Range %": s.get('range_pct', 0),
                    "Chart": tv_url
                }
                
                if strategy_name == "Doji_Setup":
                    row.update({
                        "Signal": "Doji/CPR",
                        "CPR Width %": s['cpr']['width_pct'],
                        "Cam Center": s['camarilla']['center'],
                        "Pivot": s['cpr']['pivot']
                    })
                elif strategy_name == "Inside_Camarilla":
                    row.update({
                        "Signal": "Inside Cam",
                        "Today H3": s['camarilla']['h3'],
                        "Pre H3": s['prev_camarilla']['h3'],
                        "Today L3": s['camarilla']['l3'],
                        "Pre L3": s['prev_camarilla']['l3']
                    })
                data.append(row)
            return pd.DataFrame(data)

        # --- Tab 1: Doji ---
        with tab1:
            st.markdown("### Doji & Tight CPR Setups")
            st.caption("Criteria: Price > Pivot, Range < 1%, Tight CPR, Near Cam Center.")
            df_doji = create_df("Doji_Setup")
            
            if df_doji.empty:
                st.info("No stocks matched the Doji setup criteria.")
            else:
                st.dataframe(
                    df_doji,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="₹%.2f"),
                        "Range %": st.column_config.NumberColumn(format="%.2f%%"),
                        "CPR Width %": st.column_config.NumberColumn(format="%.2f%%"),
                        "Chart": st.column_config.LinkColumn("TradingView", display_text="Open Chart"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
        # --- Tab 2: Inside Camarilla ---
        with tab2:
            st.markdown("### Inside Camarilla Setups")
            st.caption("Criteria: Today's Camarilla Range (H3-L3) is completely inside Yesterday's Range.")
            df_inside = create_df("Inside_Camarilla")
            
            if df_inside.empty:
                st.info("No stocks matched the Inside Camarilla criteria.")
            else:
                st.dataframe(
                    df_inside,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="₹%.2f"),
                        "Range %": st.column_config.NumberColumn(format="%.2f%%"),
                        "Chart": st.column_config.LinkColumn("TradingView", display_text="Open Chart"),
                    },
                    use_container_width=True,
                    hide_index=True
                )

else:
    st.info("Click 'Run Daily Scan' to start searching for potential trades.")

st.markdown("---")
st.markdown("Automated by Streamlit & Yahoo Finance")
