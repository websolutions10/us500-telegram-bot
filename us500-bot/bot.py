import yfinance as yf
import pandas as pd
import time
import requests
from ta.trend import TEMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# Configuration Telegram
BOT_TOKEN = "7791134031:AAGnmuP1tETKSq4TI4DcZwQTuiVE_0DrZv0"
CHAT_ID = "553794959"
MAX_SIGNALS_PER_DAY = 3
sent_today = 0
last_signal_time = ""

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

def fetch_data():
    data = yf.download("^GSPC", interval="15m", period="2d")
    return data

def apply_indicators(df):
    df["TEMA50"] = TEMAIndicator(df["Close"], window=50).tema()
    df["RSI14"] = RSIIndicator(df["Close"], window=14).rsi()
    bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["Volume_MA20"] = df["Volume"].rolling(20).mean()
    return df

def check_signal(df):
    global sent_today, last_signal_time
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    if sent_today >= MAX_SIGNALS_PER_DAY:
        return

    buy = (
        latest["Close"] > latest["TEMA50"] > prev["TEMA50"] and
        latest["RSI14"] > 55 and
        latest["Close"] > latest["bb_upper"] and
        latest["Volume"] > latest["Volume_MA20"]
    )

    sell = (
        latest["Close"] < latest["TEMA50"] < prev["TEMA50"] and
        latest["RSI14"] < 45 and
        latest["Close"] < latest["bb_lower"] and
        latest["Volume"] > latest["Volume_MA20"]
    )

    if buy or sell:
        signal_type = "📈 ACHAT (LONG)" if buy else "📉 VENTE (SHORT)"
        price = round(latest["Close"], 2)
        time_str = latest.name.strftime("%Y-%m-%d %H:%M")
        rsi_val = round(latest["RSI14"], 1)
        message = (
            f"🟢 Signal détecté - US500\n"
            f"{signal_type}\n"
            f"🕒 Heure : {time_str}\n"
            f"💰 Prix : {price}\n"
            f"📊 RSI: {rsi_val} | Volume > MA20 | Bollinger cassé | TEMA confirmée"
        )
        send_telegram_message(message)
        sent_today += 1
        last_signal_time = time_str

def main_loop():
    global sent_today
    while True:
        try:
            df = fetch_data()
            df = apply_indicators(df)
            check_signal(df)
        except Exception as e:
            print("Erreur :", e)
        time.sleep(600)  # Toutes les 10 minutes
        if pd.Timestamp.now().strftime("%H:%M") == "00:00":
            sent_today = 0

if __name__ == "__main__":
    main_loop()
