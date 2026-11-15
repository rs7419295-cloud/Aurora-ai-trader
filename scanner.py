import os
import yfinance as yf
import pandas as pd
import requests

TOKEN = os.environ.get("BOT_TOKEN")
CHAT = os.environ.get("CHAT_ID")

def alert(m):
    if not TOKEN or not CHAT:
        return
    u = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(u, json={"chat_id": CHAT, "text": m, "parse_mode": "Markdown"})

stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "BTC-USD", "ETH-USD"]
out = ["🤖 *AURORA AI: CLOUD SCANNER*\n"]

for t in stocks:
    try:
        df = yf.download(t, period="3mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty or len(df) < 30:
            continue

        df['E20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['E50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        hl = df['High'] - df['Low']
        hc = (df['High'] - df['Close'].shift()).abs()
        lc = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()

        d = df['Close'].diff()
        g = (d.where(d > 0, 0)).rolling(window=14).mean()
        l = (-d.where(d < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (g / l)))

        p = float(df['Close'].iloc[-1])
        e20 = float(df['E20'].iloc[-1])
        e50 = float(df['E50'].iloc[-1])
        atr = float(df['ATR'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        
        cur = "$" if "USD" in t else "₹"

        if p > e20 and e20 > e50 and (48 <= rsi <= 68):
            sl = p - (1.5 * atr)
            tp = p + (2.5 * atr)
            out.append(f"🟢 *SIGNAL: {t}*\n   • Price: {cur}{p:.2f} (RSI: {rsi:.1f})\n   • Stop: {cur}{sl:.2f}\n   • Target: {cur}{tp:.2f}")
        else:
            out.append(f"⚪ *{t}*: No setup ({cur}{p:.2f})")
    except Exception:
        out.append(f"⚠️ *{t}*: Error")

alert("\n\n".join(out))
print("Done!")
