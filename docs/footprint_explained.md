# Volume Footprint [Verify Export v4] — 何が一致し、何が再現できなかったか

検証期間: 2026-10-28 〜 2026-11-10（8日 / 確定足11本）
対象: `pine/volume_footprint_verify_v4.pine`（Pine v6）→ `vf/footprint.py`（Python 移植）
結論の要約: **構造は完全再現。出来高の按分は再現不可。**

---

## 1. 再現できたもの（PASS）

Python 移植 `vf/footprint.py` の `derive()` が、Pine の出力と全項目で一致した。

| 項目 | 定義 | 一致 |
|---|---|---|
| `step` | `round(round(atr14 / 20 / tick) * tick, 10)` | 11/11 |
| `rows` | `ceil((high - low) / step) + 1` | 11/11 |
| `poc_idx` | `round((poc_price - low) / step)` | 11/11 |
| `rows_norm` | `rows * step / (high - low)` | 11/11 |
| `raw_volume` | `sum(volume)` の生値 | 11/11（誤差 0〜0.005%） |

代表例（day8, `t=1794182400`）:

high 2125.70 / low 2089.42 / atr14 23.26266204
step      1.16        ← Pine 1.16   ✓
rows     33           ← Pine 33     ✓
poc_idx  17.0         ← Pine 17.0   ✓
rows_norm 1.05512679  ← Pine 1.05512679 ✓
raw_volume 37519.3584 ← OHLCV 37519.3584 ✓


`tick` は 0.01 固定。ATR は `ta.atr(14)`（RMA of TR、初回14TRのSMAシード、インデックス13から出現）。

## 2. `rows_norm` の理論境界（新規に発見・実証）

`rows_norm` は 1 に近い値だが 1 ではない。その理由を式変形で説明できる。

`rows = ceil((high-low)/step) + 1` より
`(rows-2)*step < high-low ≤ (rows-1)*step`

両辺で `rows*step` を割ると:
rows/(rows-1)  ≤  rows_norm  <  rows/(rows-2)

**50本の実測で全て成立**。実測レンジは 1.027〜1.234。`rows` が小さいほど上限が緩む（rows=8 なら 1.143〜1.333）ので、`ltf_count` の少ないバーで `rows_norm` が大きく出るのは異常ではない。

## 3. 再現できなかったもの（FAIL）

### 3-1. `total_vol` の按分

`raw_volume`（実際の出来高）に対する `total_vol` の倍率が、**8日間・50本超の実測で 11倍〜1,245倍**と桁でばらつき、一切一致しなかった。

| 日 | シンボル | 倍率 |
|---|---|---|
| day1–2 | OANDA:BTCUSD | 133.5 / 143.2 / 151.1 / 133.2 |
| day3 | BINANCE:BTCUSDT | 1,245.4 / 211.9 / 24.3 |
| day3 | OANDA 1M | 20.5 |
| day3 | ETHUSDT | 11.4〜20.0 |
| day6 | ETHUSDT | 58〜63 |
| day8 | ETHUSDT | 66.1 / 70.8 / 79.3 |

50本実測での `total_vol / raw_volume` は **2.2%〜8.7%**。つまり按分は実際の出来高の 1/46〜1/11 程度にしかなっていない。

### 3-2. なぜ再現できないか（推定）

Pine 側で Lower TimeFrame を `request.security_lower_tf()` で取得し、その本数で割っているはずだが、その本数が**バーごとに 8〜182 と20倍以上ばらつく**。
day8 ltf_count: 33, 21, 12
day2 ltf_count: 8, 182, 41, 45

`request.security_lower_tf()` は「そのバーが属する下位足の配列」を返すが、返る本数は履歴の深さ・取得可能期間・バーの境界で変わる。**同じ1時間足でも、按分の分母が 8 のときと 182 のときがある**ため、`total_vol` は「そのバーで取得できた下位足の分だけ」の値になり、実際の出来高とは無関係になる。

## 4. この結果が意味すること（重要）

### `delta` は使えない

`total_vol` が狂っているので、そこから作られる `delta` も同じ倍率で狂う。実データで確認:
delta = total_vol × (2 × buy_ratio − 1)
bar 1794182400: 473.27271748 × (2×0.58909319 − 1) = 84.33075332
Pine の delta:  84.33075332   ✓ 恒等的に成立

**delta は total_vol の一次関数**であり、独立した情報を持たない。

### 暴落バーの例

`t=1794171600`（1時間で −4.5% 動いたバー）:

| 項目 | 値 |
|---|---:|
| raw_volume（実出来高、OHLCVと一致） | 80,489.94 |
| total_vol（按分後） | 920.18 |
| delta | **−569.19** |

「売り優勢 −569」と読むのは無意味。実際の売買差はこの数十倍あり得る。

### 使えるもの / 使えないもの

| 項目 | 判定 | 理由 |
|---|---|---|
| `step` / `rows` / `poc_idx` / `rows_norm` | **使える** | 価格構造のみに依存、出来高を含まない |
| `poc_price` | **使える** | 価格レベルとして妥当 |
| `raw_volume` | **使える** | OHLCV と完全一致 |
| `buy_ratio` | **条件付き** | buy+sell=1.0000 は構造的に正しいが、`ltf_count` の偏りで値自体が偏る可能性を排除できない |
| `total_vol` | **使えない** | 実出来高の 1/11〜1/46 |
| `delta` | **使えない** | total_vol の一次関数 |

## 5. 「デルタ拮抗 → ブレイクアウト」という仮説について

観察としては妥当。需給の「吸収（absorption）→ 解放（release）」として一般に知られる挙動で、拮抗＝大口が吸っている、ブレイク＝吸い切れずに走る、という読み方。

**ただしこのスクリプトでは検証できない。** 理由は §4 のとおり `delta` が `total_vol` の従属変数であり、`total_vol` 自体が正しくないため。「拮抗」の判定に使う閾値が、バーごとに 8〜182倍ばらつく分母の上に乗っている。

### 正しい検証経路

Binance の klines API には `taker_buy_base_asset_volume` がある。これは taker 側の実約定から直接集計された**推計を含まない買い出来高**。
GET /api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1000
→ [ openTime, open, high, low, close, volume, closeTime,
quoteVolume, trades, takerBuyBase, takerBuyQuote, ignore ]

delta_actual = 2 × takerBuyBase − volume

Pine を通さないので、移植問題も按分問題も発生しない。`|delta_actual| / volume` を「拮抗度」として定義し、拮抗バー（下位 20% など）の翌バー高安レンジを非拮抗バーと比較すれば、統計的に検証できる。

→ 6週間停止中のため、`parking_lot.md` に記録して後回し。

## 6. まとめ

- **成果物**: 価格構造4値の Python 完全再現（`pytest 5 passed`）、`rows_norm` 理論境界の導出と50本での実証
- **negative result**: 出来高按分は再現不可。倍率 11〜1,245倍、`total_vol/raw_volume` = 2.2%〜8.7%
- **副産物**: `delta` が `total_vol` の一次関数であることの証明（＝独立情報を持たない）
- **次の一手**: taker_buy ベースの delta 検証（別プロジェクト）