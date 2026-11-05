"""Simulate what following ClimateCredit's adjusted base yield would have meant for a farmer.

Data: data/backtest_jeonnam.csv (22 Jeonnam counties x 2006-2025). For each county-year:
  y         actual yield of that year (kg/10a)
  regional  base yield from the previous 5 years (current method)
  adjusted  base yield after replacing large-weather-impact years (ClimateCredit)
Assumptions (team assumptions, NOT the insurer's policy rules):
  price 2,500 KRW/kg; 1 ha = 10 x 10a
  stylized claim rule: payout = max(0, coverage x base yield - actual yield) x price (per 10a, x10 for ha)
  national premium subsidy by coverage: 60%:65, 70%:60, 80%:50, 85%:38, 90%:33
The weather effects behind 'adjusted' come from a model fitted on all years, so results are somewhat optimistic.
"""
import sys
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
P = 2500
SUB = {60: .65, 70: .60, 80: .50, 85: .38, 90: .33}
b = pd.read_csv("data/backtest_jeonnam.csv", encoding="utf-8-sig")
n = len(b)
adj = b[b.replaced > 0]
up = b.adjusted - b.regional

print(f"county-years: {n} ({b.county.nunique()} counties, {b.year.min()}-{b.year.max()}); adjusted cases: {len(adj)} ({100 * len(adj) / n:.0f}%)")
print(f"base-yield uplift: all {100 * (up / b.regional).mean():.2f}% | adjusted cases {100 * ((adj.adjusted - adj.regional) / adj.regional).mean():.2f}% "
      f"({(adj.adjusted - adj.regional).mean():.1f} kg/10a, max {100 * ((adj.adjusted - adj.regional) / adj.regional).max():.2f}%)")
mae_r, mae_a = (adj.y - adj.regional).abs().mean(), (adj.y - adj.adjusted).abs().mean()
closer = ((adj.y - adj.adjusted).abs() < (adj.y - adj.regional).abs()).mean()
print(f"base-yield error in adjusted cases: {mae_r:.1f} -> {mae_a:.1f} kg/10a ({100 * (mae_a / mae_r - 1):+.0f}%), closer in {100 * closer:.0f}%")
print()
print("| Coverage | Extra insured amount, adjusted cases (KRW/ha) | Extra insured amount, all county-years (KRW/ha) | Loss events (reg -> adj) | Extra payout per county-year (KRW/ha) | Break-even premium rate before subsidy | Farmer break-even rate after subsidy |")
print("|---|---|---|---|---|---|---|")
for cov in (60, 70, 80, 85, 90):
    c = cov / 100
    ex_adj = (adj.adjusted - adj.regional).mean() * 10 * P * c
    ex_all = up.mean() * 10 * P * c
    pr = np.maximum(0, c * b.regional - b.y)
    pa = np.maximum(0, c * b.adjusted - b.y)
    ev_r, ev_a = int((pr > 0).sum()), int((pa > 0).sum())
    extra_pay = (pa - pr).mean() * 10 * P
    be = extra_pay / ex_all if ex_all else float("nan")
    print(f"| {cov}% | {ex_adj:,.0f} | {ex_all:,.0f} | {ev_r} -> {ev_a} | {extra_pay:,.0f} | {100 * be:.1f}% | {100 * be / (1 - SUB[cov]):.1f}% |")
print()
dev = 100 * (b.y - b.regional) / b.regional
print(f"actual below 90% of base: {(b.y < 0.9 * b.regional).sum()} of {n}; below 80%: {(b.y < 0.8 * b.regional).sum()} of {n} (worst {dev.min():.1f}%)")
print("years with adjustments:", adj.groupby("year").size().to_dict())
