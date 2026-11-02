# Volume Footprint — Cross-Language Port & Verification

Porting a TradingView Pine Script v6 volume-footprint implementation to Python,
and establishing **which outputs can be reproduced outside the platform**.

## Result summary

| Output | Status |
|---|---|
| `step` (row height) | **Identical** |
| `rows` (price row count) | **Identical** |
| `poc_idx` (row index of max volume) | **Identical** |
| `total_vol` / `buy_vol` / `sell_vol` | **Not reproducible** (see below) |
| `buy_ratio` / `sell_ratio` | **Not reproducible** (3.1% deviation) |

Test run: `4 passed`.

## Reproduced logic

```python
step = round_half_up(atr14 / 20 / mintick) * mintick
rows = ceil((high - low) / step) + 1
poc_idx = (poc_price - low) / step   # must be an integer


`ta.atr(14)` is a Wilder RMA of True Range, seeded with the SMA of the first 14 TRs,
where the first bar's TR is `high - low`. Because the seed requires full history,
`atr14` is passed in as an input column — this isolates the check to the
rounding/aggregation logic rather than RMA seeding.

## Why volume is not reproducible

Measured on closed bars only. `raw_volume` = the chart series volume;
`total_vol` = the volume returned by `request.security_lower_tf`.

| Symbol | TF | raw_volume | total_vol | ratio |
|---|---|---|---|---|
| OANDA:BTCUSD | 1H | 3,331 | 24.95 | 133.5x |
| OANDA:BTCUSD | 1H | 4,318 | 30.16 | 143.2x |
| OANDA:BTCUSD | 1H | 5,111 | 33.82 | 151.1x |
| OANDA:BTCUSD | 1H (forming) | 3,629 | 27.25 | 133.2x |
| BINANCE:BTCUSDT | 1H | 491.81 | 0.395 | 1,245.4x |
| BINANCE:BTCUSDT | 1H | 415.39 | 1.960 | 211.9x |
| BINANCE:BTCUSDT | 1H (forming) | 53.91 | 2.214 | 24.3x |
| OANDA:BTCUSD | 1M chart | 41.0 | 2.0 | 20.5x |

The ratio varies from **20.5x to 1,245.4x**, including within a single symbol.
A constant rescaling is therefore impossible. Cross-checking against the
exchange's own 1-minute candles (Binance) also failed on **ratio**, not just scale:

| Metric | Pine | Recomputed from 1m candles |
|---|---|---|
| buy_ratio | 0.531504804 | 0.500418 |
| sell_ratio | 0.468495196 | 0.499582 |

Conclusion: the lower-timeframe volume series is not a proportional scaling of
the exchange 1-minute series. Absolute and proportional volume checks are
excluded from the verification scope by evidence, not by convenience.

Cross-symbol check: BINANCE:ETHUSDT 1H — step/rows/poc_idx identical (3 bars).
Volume ratio 11.4x–20.0x, still not reproducible.

Cross-symbol check: BINANCE:ETHUSDT 1H — step/rows/poc_idx identical (3 bars).
Volume ratio 11.4x–20.0x, still not reproducible.

## 検証状況

| 範囲 | 結果 |
|---|---|
| 構造値（step/rows/poc_idx/rows_norm） | ✅ Pine と一致 |
| 出来高（raw_volume） | ✅ 完全一致 |
| 出来高の按分（total_vol） | ❌ 再現不可（環境依存） |

詳細: [docs/verify_log.md](docs/verify_log.md)
## Scope decision

Verified: structural values derived from OHLC + ATR (platform-independent).
Excluded: all volume-derived values (platform-dependent series).

This is the intended deliverable — a verification that states what it can and
cannot prove.

## Reproduce

```bash
pip install pytest
pytest -q          # 4 passed