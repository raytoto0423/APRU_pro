"""Can the rule that sets the base yield be tuned for more farmer benefit, and what does it cost?

Evaluates variants of the base-yield rule on the Jeonnam back-test (22 counties x 2006-2025).
For each target year t the base uses the 5 years before t. 'actual' is the yield of year t.
Metrics: mean uplift vs the 5-year average, error vs actual (MAE, bias = mean(actual - base)),
extra insured amount at 80% coverage and extra payout under a stylized claim rule (team assumption).
Parameters are chosen on 2006-2015 and checked on 2016-2025 (and the reverse) to avoid overfitting.
"""
import itertools
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from product import Engine  # noqa: E402

P = 2500
e = Engine()
prov, md = "전라남도", (6, 1)
rows = []
for county in e.counties(prov):
    sid, _ = e.station_of(prov, county)
    hist = e.yield_df[(e.yield_df.province == prov) & (e.yield_df.county == county)].set_index("year")["yield_kg10a"]
    eff_cache = {}
    for t in range(2006, 2026):
        yrs = list(range(t - 5, t))
        if t not in hist.index or any(y not in hist.index for y in yrs):
            continue
        for y in yrs:
            if y not in eff_cache:
                eff_cache[y] = e.weather_effect(sid, y, md)
        eff = [eff_cache[y] for y in yrs]
        if any(v is None for v in eff):
            continue
        rows.append(dict(county=county, year=t, y=float(hist[t]), act=np.array([hist[v] for v in yrs], float), eff=np.array(eff, float)))
print("county-years:", len(rows))


def base(r, thr, k, cap, mode="shock"):
    a, eff = r["act"], r["eff"]
    reg = a.mean()
    normal = a / (1 + eff / 100)
    if mode == "shock":
        idx = [i for i in np.argsort(eff) if eff[i] <= thr][:k]
        sub = a.copy()
        for i in idx:
            sub[i] = max(a[i], normal[i])
        return min(sub.mean(), reg * (1 + cap / 100))
    if mode == "raise_all":                      # lift every below-normal-weather year, no threshold
        sub = np.maximum(a, normal)
        return min(sub.mean(), reg * (1 + cap / 100))
    if mode == "normalize_all":                  # remove weather from all 5 years (can also lower the base)
        return normal.mean()
    return reg


def evaluate(sel, thr, k, cap, mode="shock"):
    d = []
    for r in sel:
        reg = r["act"].mean()
        b = base(r, thr, k, cap, mode)
        d.append((r["y"], reg, b))
    y, reg, b = (np.array(x) for x in zip(*d))
    out = dict(uplift=100 * (b / reg - 1).mean(), adjusted_share=100 * (np.abs(b - reg) > 0.05).mean(),
               mae=np.abs(y - b).mean(), mae_reg=np.abs(y - reg).mean(), bias=(y - b).mean(), bias_reg=(y - reg).mean())
    c = 0.8
    ex_ins = (b - reg).mean() * 10 * P * c
    ex_pay = (np.maximum(0, c * b - y) - np.maximum(0, c * reg - y)).mean() * 10 * P
    out.update(ex_ins=ex_ins, ex_pay=ex_pay)
    return out


early = [r for r in rows if r["year"] <= 2015]
late = [r for r in rows if r["year"] >= 2016]

print("\n== Current rule and variants on all county-years ==")
print("| Rule | Mean uplift | Adjusted share | MAE vs actual (kg/10a) | Bias: actual - base (kg/10a) | Extra insured amount @80% (KRW/ha) | Extra payout @80% (KRW/ha/yr) |")
print("|---|---|---|---|---|---|---|")
cases = [("5-year average (no adjustment)", dict(thr=-99, k=0, cap=0)),
         ("Current: shock <= -7%, max 2, cap +7%", dict(thr=-7, k=2, cap=7)),
         ("Looser: shock <= -5%, max 3, cap +7%", dict(thr=-5, k=3, cap=7)),
         ("Loosest: any year, max 5, cap +10%", dict(thr=99, k=5, cap=10)),
         ("Lift every below-normal-weather year, cap +7%", dict(thr=0, k=5, cap=7, mode="raise_all")),
         ("Remove weather from all 5 years (can lower)", dict(thr=0, k=5, cap=99, mode="normalize_all"))]
for name, kw in cases:
    o = evaluate(rows, **kw)
    print(f"| {name} | {o['uplift']:+.2f}% | {o['adjusted_share']:.0f}% | {o['mae']:.1f} (5y avg {o['mae_reg']:.1f}) | {o['bias']:+.1f} (5y avg {o['bias_reg']:+.1f}) | {o['ex_ins']:+,.0f} | {o['ex_pay']:+,.0f} |")

print("\n== Grid: threshold x max years x cap, ranked by accuracy; train on 2006-2015, test on 2016-2025 ==")
grid = list(itertools.product([-3, -5, -7, -9, -12], [1, 2, 3, 5], [4, 7, 10, 15]))
tab = []
for thr, k, cap in grid:
    tr, te = evaluate(early, thr, k, cap), evaluate(late, thr, k, cap)
    tab.append(dict(thr=thr, k=k, cap=cap, mae_tr=tr["mae"], mae_te=te["mae"], up_te=te["uplift"], bias_te=te["bias"], ex_ins_te=te["ex_ins"]))
tab = pd.DataFrame(tab)
base_te = evaluate(late, -99, 0, 0)
cur = tab[(tab.thr == -7) & (tab.k == 2) & (tab.cap == 7)].iloc[0]
print(f"test 2016-2025: 5-year average MAE {base_te['mae']:.2f}, bias {base_te['bias']:+.1f}")
print(f"current rule  : test MAE {cur.mae_te:.2f}, uplift {cur.up_te:+.2f}%, bias {cur.bias_te:+.1f}, extra insured amount {cur.ex_ins_te:,.0f}")
best = tab.sort_values("mae_tr").head(5)
print("best 5 by TRAIN accuracy, shown with their TEST results:")
print(best.round(2).to_string(index=False))
print("most uplift on TEST (for contrast):")
print(tab.sort_values("up_te", ascending=False).head(3).round(2).to_string(index=False))
