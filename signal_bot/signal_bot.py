import ccxt
import pandas as pd
import numpy as np
import requests
import time

# 設定
TELEGRAM_TOKEN = "8609203120:AAEzpmQrTjeMgP3LDg-znYPW8clH4sjcYUQ"
CHAT_ID = "8130493195"
SYMBOL = "BTC/USDT"

# 時間框架設定
TIMEFRAMES = {
    "15m": "15分鐘",
    "1h":  "1小時",
    "4h":  "4小時",
    "1d":  "日線"
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_signal(symbol, timeframe, limit=100):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)

    # 均線
    df['MA20'] = df['close'].rolling(20).mean()
    df['MA60'] = df['close'].rolling(60).mean()

    # 布林通道
    df['BB_mid'] = df['close'].rolling(20).mean()
    df['BB_std'] = df['close'].rolling(20).std()
    df['BB_upper'] = df['BB_mid'] + 2 * df['BB_std']
    df['BB_lower'] = df['BB_mid'] - 2 * df['BB_std']

    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 訊號
    last = df.iloc[-1]
    ma_bull = last['MA20'] > last['MA60']
    bb_ok = last['close'] > last['BB_lower']
    macd_bull = last['MACD'] > last['MACD_signal']
    rsi_ok = 30 < last['RSI'] < 70

    if ma_bull and bb_ok and macd_bull and rsi_ok:
        signal = "🟢 買入"
    elif not ma_bull or last['close'] > last['BB_upper'] or not macd_bull:
        signal = "🔴 賣出/觀望"
    else:
        signal = "🟡 中性"

    return {
        "signal": signal,
        "price": last['close'],
        "MA20": last['MA20'],
        "MA60": last['MA60'],
        "RSI": last['RSI'],
        "MACD": last['MACD'],
        "BB_upper": last['BB_upper'],
        "BB_lower": last['BB_lower']
    }

def scan_and_notify():
    msg = f"📊 *BTC/USDT 多時間框架分析*\n"
    msg += f"{'='*30}\n"

    for tf, tf_name in TIMEFRAMES.items():
        try:
            result = get_signal(SYMBOL, tf)
            msg += f"\n*{tf_name} ({tf})*\n"
            msg += f"訊號：{result['signal']}\n"
            msg += f"現價：${result['price']:,.0f}\n"
            msg += f"RSI：{result['RSI']:.1f}\n"
            msg += f"MACD：{'正' if result['MACD'] > 0 else '負'}\n"
        except Exception as e:
            msg += f"\n*{tf_name}*：資料取得失敗\n"

    msg += f"\n{'='*30}\n"
    msg += f"⏰ 掃描時間：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
    send_telegram(msg)
    print("訊號已發送")

# 主程式：每小時掃描一次
if __name__ == "__main__":
    print("Bot啟動，開始監控BTC...")
    send_telegram("🚀 BTC Signal Bot 已啟動！每小時自動推送訊號。")
    while True:
        scan_and_notify()
        time.sleep(3600)  # 每小時執行一次