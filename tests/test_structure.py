import pytest
from vf.footprint import derive, pr, MIN_TICK

# --- fixture: BINANCE:BTCUSDT 1H, v4 実測値 ---
BARS = [
    {"time":1792515600,"open":83028.14,"high":83224.01,"low":82881.69,"close":83029.84,
     "atr14":394.6387528,"poc_price":83138.18,"exp_step":19.73,"exp_rows":19,"exp_idx":13},
    {"time":1792519200,"open":83029.84,"high":83225.00,"low":82804.98,"close":83002.00,
     "atr14":396.451699,"poc_price":82824.80,"exp_step":19.82,"exp_rows":23,"exp_idx":1},
    {"time":1792522800,"open":83002.01,"high":83034.01,"low":82728.80,"close":82804.22,
     "atr14":389.9344348,"poc_price":82787.30,"exp_step":19.50,"exp_rows":17,"exp_idx":3},
]
BARS = BARS[:-1]  # 最後の1行（最新の未確定データ）を削る

@pytest.mark.parametrize("b", BARS, ids=[str(b["time"]) for b in BARS])
def test_structure(b):
    d = derive(b)
    assert d["step"] == pytest.approx(b["exp_step"], abs=1e-9), "step"
    assert d["rows"] == b["exp_rows"], "rows"
    assert d["poc_idx"] == pytest.approx(b["exp_idx"], abs=1e-9), "poc_idx"

def test_pr_matches_pine_round():
    assert pr(0.5) == 1 and pr(2.5) == 3 and pr(-0.5) == -1

def test_rows_norm_matches_pine():
    """Pine v4 実測値との照合（ETHUSDT 1H, t=1793534400）"""
    d = derive({"atr14": 8.64, "high": 2270.80, "low": 2255.31, "poc_price": 2260.04})
    assert d["rows"] == 38
    assert d["step"] == pytest.approx(0.43)
    assert round(d["rows_norm"], 2) == 1.05

def test_rows_norm_matches_pine():
    """Pine v4 実測値との照合（ETHUSDT 1H, t=1793534400）"""
    d = derive({"atr14": 8.64, "high": 2270.80, "low": 2255.31, "poc_price": 2260.04})
    assert d["rows"] == 38
    assert d["step"] == pytest.approx(0.43)
    assert round(d["rows_norm"], 2) == 1.05


def test_rows_norm_bounds():
    """ceil定義から導かれる理論境界。50本で成立を確認済み"""
    d = derive({"atr14": 8.64, "high": 2270.80, "low": 2255.31, "poc_price": 2260.04})
    r = d["rows"]
    assert r / (r - 1) <= d["rows_norm"] < r / (r - 2)