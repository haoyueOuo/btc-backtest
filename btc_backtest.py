import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

SYMBOL = 'ETH/USDT'

# 抓取歷史資料
exchange = ccxt.binance()
since = exchange.parse8601('2020-01-01T00:00:00Z')

all_ohlcv = []
while True:
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe='1d', since=since, limit=1000)
    if not ohlcv:
        break
    all_ohlcv += ohlcv
    since = ohlcv[-1][0] + 1
    if len(ohlcv) < 1000:
        break

# 整理資料
df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
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

# MACD（僅參考）
ema12 = df['close'].ewm(span=12).mean()
ema26 = df['close'].ewm(span=26).mean()
df['MACD'] = ema12 - ema26
df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
df['MACD_hist'] = df['MACD'] - df['MACD_signal']

# RSI（僅參考）
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# 產生訊號（只用MA+布林通道決定）
buy_condition = (
    (df['MA20'] > df['MA60']) &
    (df['close'] > df['BB_lower'])
)
sell_condition = (
    (df['MA20'] < df['MA60']) |
    (df['close'] > df['BB_upper'])
)

df['signal'] = 0
df.loc[buy_condition, 'signal'] = 1
df.loc[sell_condition, 'signal'] = -1

# 計算報酬
df['return'] = df['close'].pct_change()
df['strategy_return'] = df['signal'].shift(1) * df['return']
df.loc[df['signal'].shift(1) == -1, 'strategy_return'] = 0

# 累積報酬
df['cumulative_market'] = (1 + df['return']).cumprod()
df['cumulative_strategy'] = (1 + df['strategy_return']).cumprod()

# 最大回撤
def max_drawdown(returns):
    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return drawdown.min()

market_dd = max_drawdown(df['return'].dropna())
strategy_dd = max_drawdown(df['strategy_return'].dropna())

# 夏普值
sharpe_market = df['return'].mean() / df['return'].std() * np.sqrt(365)
sharpe_strategy = df['strategy_return'].mean() / df['strategy_return'].std() * np.sqrt(365)

# 畫圖
fig, axes = plt.subplots(4, 1, figsize=(14, 16))

# 圖一：價格+均線+布林
axes[0].plot(df['close'], label=f'{SYMBOL} Price', color='black', linewidth=0.8)
axes[0].plot(df['MA20'], label='MA20', color='blue', linewidth=1)
axes[0].plot(df['MA60'], label='MA60', color='orange', linewidth=1)
axes[0].fill_between(df.index, df['BB_upper'], df['BB_lower'], alpha=0.1, color='purple', label='Bollinger Band')
axes[0].set_title(f'{SYMBOL} Price with MA & Bollinger Bands (2020-2026)')
axes[0].legend()
axes[0].grid(True)

# 圖二：累積報酬
axes[1].plot(df['cumulative_market'], label='Buy & Hold', color='blue')
axes[1].plot(df['cumulative_strategy'], label='MA+BB Strategy', color='orange')
axes[1].set_title('Cumulative Return Comparison')
axes[1].legend()
axes[1].grid(True)

# 圖三：MACD（參考）
axes[2].plot(df['MACD'], label='MACD', color='blue', linewidth=0.8)
axes[2].plot(df['MACD_signal'], label='Signal', color='orange', linewidth=0.8)
axes[2].bar(df.index, df['MACD_hist'], label='Histogram', color='gray', alpha=0.5)
axes[2].set_title('MACD (參考指標)')
axes[2].legend()
axes[2].grid(True)

# 圖四：RSI（參考）
axes[3].plot(df['RSI'], label='RSI', color='purple', linewidth=0.8)
axes[3].axhline(y=70, color='red', linestyle='--', linewidth=0.8, label='Overbought (70)')
axes[3].axhline(y=30, color='green', linestyle='--', linewidth=0.8, label='Oversold (30)')
axes[3].set_title('RSI (參考指標)')
axes[3].legend()
axes[3].grid(True)

plt.tight_layout()
plt.savefig('backtest_result.png', dpi=150)
plt.show()

print(f"=== {SYMBOL} 策略績效（2020-2026）===")
print(f"市場報酬:       {(df['cumulative_market'].iloc[-1]-1)*100:.1f}%")
print(f"策略報酬:       {(df['cumulative_strategy'].iloc[-1]-1)*100:.1f}%")
print(f"市場最大回撤:   {market_dd*100:.1f}%")
print(f"策略最大回撤:   {strategy_dd*100:.1f}%")
print(f"市場夏普值:     {sharpe_market:.2f}")
print(f"策略夏普值:     {sharpe_strategy:.2f}")