import streamlit as st
import pandas as pd
import scan
import datetime

st.set_page_config(page_title="Camarilla Stock Scanner", layout="wide")

st.title("📈 Camarilla & CPR Stock Scanner")
st.markdown("Identify swing trading setups with **Doji/Hammer** patterns near **Camarilla Central Pivots** and **Tight CPR**.")

# Initialize session state for data
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = "Never"

def run_scan():
    with st.spinner('Scanning Nifty 500 stocks... This may take a minute.'):
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
        st.warning("No stocks matched the criteria today.")
    else:
        # Prepare DataFrame for display
        display_data = []
        for s in stocks:
            display_data.append({
                "Ticker": s['ticker'],
                "Price": s['price'],
                "Signal": s['signal'],
                "CPR Width %": s['cpr']['width_pct'],
                "Cam Center": s['camarilla']['center'],
                "EMA Status": s['ema_status']
            })
        
        df = pd.DataFrame(display_data)
        
        # summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Stocks Found", len(stocks))
        
        st.subheader("Potential Setups")
        st.dataframe(
            df,
            column_config={
                "Price": st.column_config.NumberColumn(format="₹%.2f"),
                "CPR Width %": st.column_config.NumberColumn(format="%.2f%%"),
                "Cam Center": st.column_config.NumberColumn(format="₹%.2f"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed Cards (Optional expansion)
        with st.expander("View Detailed Breakdown"):
            for s in stocks:
                st.markdown(f"### {s['ticker']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Price", f"₹{s['price']}")
                c2.metric("Signal", s['signal'])
                c3.metric("CPR Width", f"{s['cpr']['width_pct']}%")
                
                st.markdown(f"**Technical Levels:**")
                st.code(f"""
CPR: Pivot={s['cpr']['pivot']}, TC={s['cpr']['tc']}, BC={s['cpr']['bc']}
Camarilla: H3={s['camarilla']['h3']}, L3={s['camarilla']['l3']}, Center={s['camarilla']['center']}
                """)
                st.divider()

else:
    st.info("Click 'Run Daily Scan' to start searching for potential trades.")

st.markdown("---")
st.markdown("Automated by Streamlit & Yahoo Finance")
