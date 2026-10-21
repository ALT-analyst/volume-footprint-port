import math
import pytest

# Pine の math.round は 0 から遠い方へ（銀行丸め禁止）
def pr(x: float) -> int:
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)

MIN_TICK = 0.01

def derive(bar):
    """step / rows / poc_idx を Pine と同一手順で導出"""
    step = pr(pr(bar["atr14"] / 20.0 / MIN_TICK)) * MIN_TICK
    step = round(step, 10)                       # 浮動小数の末尾誤差を落とす
    rows = math.ceil((bar["high"] - bar["low"]) / step) + 1
    poc_idx = (bar["poc_price"] - bar["low"]) / step
    return {"step": step, "rows": rows, "poc_idx": poc_idx}

# --- fixture: BINANCE:BTCUSDT 1H, v4 実測値 ---
BARS = [
    {"time":1792515600,"open":83028.14,"high":83224.01,"low":82881.69,"close":83029.84,
     "atr14":394.6387528,"poc_price":83138.18,"exp_step":19.73,"exp_rows":19,"exp_idx":13},
    {"time":1792519200,"open":83029.84,"high":83225.00,"low":82804.98,"close":83002.00,
     "atr14":396.451699,"poc_price":82824.80,"exp_step":19.82,"exp_rows":23,"exp_idx":1},
    {"time":1792522800,"open":83002.01,"high":83034.01,"low":82728.80,"close":82804.22,
     "atr14":389.9344348,"poc_price":82787.30,"exp_step":19.50,"exp_rows":17,"exp_idx":3},
]

@pytest.mark.parametrize("b", BARS, ids=[str(b["time"]) for b in BARS])
def test_structure(b):
    d = derive(b)
    # 1 step（atr14 → tick丸め）
    assert d["step"] == pytest.approx(b["exp_step"], abs=1e-9), "step"
    # 2 rows（切り上げ＋1）
    assert d["rows"] == b["exp_rows"], "rows"
    # 3 poc_idx（整数であること＝Pineの丸めと一致）
    assert d["poc_idx"] == pytest.approx(b["exp_idx"], abs=1e-9), "poc_idx"

def test_pr_matches_pine_round():
    assert pr(0.5) == 1 and pr(2.5) == 3 and pr(-0.5) == -1   # Python round() は 2 になる