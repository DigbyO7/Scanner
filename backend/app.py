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
                st.session_state.total_scanned = result.get('total_scanned', 0)
                st.success(f"Scan Complete! Found {len(result['stocks'])} stocks.")
            else:
                 st.error("Scan returned no data. Check logs or temporary API issues.")
        except Exception as e:
            st.error(f"Error during scan: {e}")

# Sidebar controls
st.sidebar.header("Scanner Controls")

# Scanner Selection
scanner_mode = st.sidebar.radio(
    "Select Scanner Mode:",
    ("Doji / CPR (Daily)", "Inside Camarilla (Monthly)")
)

if st.sidebar.button("Run Daily Scan", type="primary"):
    run_scan()

st.sidebar.markdown("---")
st.sidebar.info(f"Last Updated: {st.session_state.last_updated}")
if 'total_scanned' in st.session_state:
    st.sidebar.text(f"Stocks Scanned: {st.session_state.total_scanned}")

# Main Display
if st.session_state.scan_data:
    stocks = st.session_state.scan_data
    
    if len(stocks) == 0:
        st.warning("No stocks matched any criteria today.")
    else:
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
                    # Access 'daily' dict
                    d = s.get('daily', {})
                    row.update({
                        "Signal": "Doji/CPR",
                        "CPR Width %": d.get('cpr_width'),
                        "Cam Center": d.get('cam_center'),
                        "Pivot": d.get('pivot')
                    })
                elif strategy_name == "Inside_Camarilla":
                    # Access 'monthly' dict
                    m = s.get('monthly', {})
                    row.update({
                        "Signal": "Inside Monthly",
                        "Cur Month H3": m.get('curr_h3'),
                        "Pre Month H3": m.get('prev_h3'),
                        "Cur Month L3": m.get('curr_l3'),
                        "Pre Month L3": m.get('prev_l3')
                    })
                data.append(row)
            return pd.DataFrame(data)

        if scanner_mode == "Doji / CPR (Daily)":
            st.subheader("🕯️ Daily Doji & CPR Setups (Compact)")
            st.caption("Criteria: Doji/Small Pattern (Short Wicks) + Near Pivot/Cam + Low Range (<1.5%).")
            df_doji = create_df("Doji_Setup")
            
            if df_doji.empty:
                st.info("No stocks matched the Daily Doji setup criteria.")
            else:
                st.dataframe(
                    df_doji,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="₹%.2f"),
                        "Range %": st.column_config.NumberColumn(format="%.2f%%"),
                        "CPR Width %": st.column_config.NumberColumn(format="%.2f%%"),
                        "Cam Center": st.column_config.NumberColumn(format="₹%.2f"),
                        "Chart": st.column_config.LinkColumn("TradingView", display_text="Open Chart"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
        elif scanner_mode == "Inside Camarilla (Monthly)":
            st.subheader("📉 Monthly Inside Camarilla Setups")
            st.caption("Criteria: Inside Month (Curr H3/H4/L3/L4 inside Prev).")
            df_inside = create_df("Inside_Camarilla")
            
            if df_inside.empty:
                st.info("No stocks matched the Monthly Inside Camarilla criteria.")
            else:
                st.dataframe(
                    df_inside,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="₹%.2f"),
                        "Range %": st.column_config.NumberColumn(format="%.2f%%"),
                        "Cur Month H3": st.column_config.NumberColumn(format="₹%.2f"),
                        "Pre Month H3": st.column_config.NumberColumn(format="₹%.2f"),
                        "Cur Month L3": st.column_config.NumberColumn(format="₹%.2f"),
                        "Pre Month L3": st.column_config.NumberColumn(format="₹%.2f"),
                        "Chart": st.column_config.LinkColumn("TradingView", display_text="Open Chart"),
                    },
                    use_container_width=True,
                    hide_index=True
                )

else:
    st.info("Click 'Run Daily Scan' to start searching for potential trades.")

st.markdown("---")
st.markdown("Automated by Streamlit & Yahoo Finance")
