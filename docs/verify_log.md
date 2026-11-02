# 検証ログ — Volume Footprint [Verify Export v4]

対象: BINANCE:ETHUSDT 1H / 検証期間: 2026-10-29 〜 2026-11-02

## 検証済み（Pine と一致）

| 項目 | 定義 | 状態 |
|---|---|---|
| step | round(atr14/20/0.01)*0.01 | 一致 |
| rows | ceil((high-low)/step)+1 | 一致 |
| poc_idx | (poc_price-low)/step | 整数で一致 |
| rows_norm | rows*step/(high-low) | 一致 |
| rows_norm 境界 | rows/(rows-1) ≤ n < rows/(rows-2) | 50本で成立 |
| raw_volume | OHLCV出来高 | 完全一致（誤差0） |
| buy_ratio+sell_ratio | — | 常に1.0 |

## 未再現（環境依存）

| 項目 | 実測 |
|---|---|
| total_vol（按分合計） | raw_volume の 2.2%〜8.7%（11〜45倍の乖離） |

原因: 入力段は一致するため、按分アルゴリズム内部で失われている。
一定係数ではない / rows・step・値幅・出来高と無相関。

## 注意

Pineのプロット書き出しは OHLCV と約7本ずれる（重複あり）。
突き合わせは時刻ではなく raw_volume の値で行うこと。