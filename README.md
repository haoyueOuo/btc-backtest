# Crypto Quantitative Trading Project

個人量化交易研究專案，結合技術分析與程式開發，
涵蓋策略回測與即時訊號系統。

## 專案結構

### 1. BTC回測系統 (`btc_backtest/`)
- 策略：MA20/MA60均線 + 布林通道
- 回測期間：2020-2026（完整牛熊市週期）
- 參考指標：MACD、RSI

| 指標 | Buy & Hold | 本策略 |
|------|-----------|--------|
| 報酬率 | 938% | 870% |
| 最大回撤 | -76.6% | -46.6% |
| 夏普值 | 0.91 | 1.11 |

### 2. Telegram即時訊號Bot (`signal_bot/`)
- 串接Binance即時資料
- 支援多時間框架：15m、1h、4h、1d
- 自動推送買入/賣出訊號到Telegram
- 每小時自動掃描

## 使用技術
- Python 3.12
- ccxt（Binance API）
- pandas、numpy（資料處理）
- matplotlib（視覺化）
- Telegram Bot API（即時通知）