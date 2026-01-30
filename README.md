# 📈 Camarilla & CPR Stock Scanner

A Streamlit dashboard to identify swing trading setups based on:
- **Camarilla Pivots** (Price near Central Pivot)
- **Central Pivot Range (CPR)** (Identifying "Tight CPR")
- **Candlestick Patterns** (Doji/Hammer)
- **EMAs** (8 & 20 Day Support)

## 🚀 Quick Start (Local)

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run Scanner & Dashboard**:
   ```bash
   streamlit run app.py
   ```

## 🌐 Deploy to Streamlit Cloud

1. **Push to GitHub**:
   - Commit this code to a new GitHub repository.

2. **Connect Streamlit**:
   - Go to [share.streamlit.io](https://share.streamlit.io/).
   - Click "New App".
   - Select your GitHub repository.
   - Set **Main file path** to `backend/app.py`.
   - Click **Deploy**!

## ⚙️ Configuration
- The scanner fetches data for **Nifty 500** stocks via Yahoo Finance.
- Scans are triggered manually via the dashboard button.
