"""Volume Footprint [Verify Export v4] の構造値移植。

検証済み: step / rows / poc_idx / rows_norm は Pine と一致。
未再現  : total_vol(按分後) は環境依存 (11.4x - 1245.4x)。
"""
import math

MIN_TICK = 0.01


def pr(x: float) -> int:
    """Pine の math.round は 0 から遠い方へ（銀行丸め禁止）"""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def derive(bar):
    """step / rows / poc_idx / rows_norm を Pine と同一手順で導出"""
    step = pr(pr(bar["atr14"] / 20.0 / MIN_TICK)) * MIN_TICK
    step = round(step, 10)                       # 浮動小数の末尾誤差を落とす
    rng = bar["high"] - bar["low"]
    rows = math.ceil(rng / step) + 1
    poc_idx = (bar["poc_price"] - bar["low"]) / step
    # rows_norm = rows*step/(high-low)。Pine v4 と同定義。1.05前後が正常、rng==0 は 1.0
    rows_norm = rows * step / rng if rng != 0 else 1.0
    return {"step": step, "rows": rows, "poc_idx": poc_idx, "rows_norm": rows_norm}