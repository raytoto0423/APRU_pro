"""Slide-ready figures (English) for the model explanation. Output: figures/*.png"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Patch

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from product import Engine  # noqa: E402

G9, G6, G1, GOLD, RED, GRAY, LINE = "#0F3D2E", "#1F8F5A", "#E8F3EC", "#E0A526", "#D73027", "#B7CFC1", "#D6E6DB"
OUT = "figures"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": LINE, "axes.labelcolor": G9, "xtick.color": G9, "ytick.color": G9,
                     "text.color": G9, "axes.spines.top": False, "axes.spines.right": False})
res = json.load(open("data/results.json", encoding="utf-8"))
cv = pd.read_csv("data/train_table_cv.csv", encoding="utf-8-sig")


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


# ---------- 1. pipeline ----------
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.axis("off")


def box(x, y, w, h, text, fc="white", ec=G6, fs=10.5, bold=False, tc=G9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=1.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.35)


def arrow(x0, y0, x1, y1, color=G6):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16, lw=2, color=color))


ax.text(1, 58, "Model: how the weather effect on yield is learned", fontsize=14, fontweight="bold")
box(1, 38, 21, 12, "Statistics Korea (KOSIS)\ncounty paddy-rice yield\n78 counties, 2001-2025", fs=9.2)
box(1, 18, 21, 12, "KMA ASOS daily weather\nApr-Oct, nearest\nstation per county", fs=9.2)
box(27, 20, 24, 28, "72 features\n\n4 growth stages x 9 weather\nvariables, as anomalies vs\nthe station's normal (36)\n\n+ 5-year mean anomalies\n(36)\n\nTarget: yield change (%)\nvs the 5-year average", fc=G1, fs=9.2)
box(57, 36, 19, 12, "Ridge regression\nalpha = 300", fs=10, bold=True)
box(57, 16, 19, 16, "Neural net x 5 seeds\n72 -> 16 -> 1\nReLU, dropout 0.3\nAdamW, 200 epochs", fs=9, bold=True)
ax.add_patch(Circle((84, 34), 5.6, fc=G6, ec=G6))
ax.text(84, 34, "50 / 50\nblend", ha="center", va="center", color="white", fontsize=10.5, fontweight="bold")
box(92, 28, 7, 12, "Weather\neffect\n(%)", fc=GOLD, ec=GOLD, fs=9, bold=True)
arrow(22.6, 44, 26.5, 40)
arrow(22.6, 24, 26.5, 28)
arrow(51.6, 40, 56.4, 42)
arrow(51.6, 28, 56.4, 24)
arrow(76.7, 42, 80.3, 37.5)
arrow(76.7, 24, 80.3, 30.5)
arrow(89.9, 34, 91.8, 34)
ax.text(1, 11, "Validation: leave-one-year-out (each year predicted by a model trained on the other years).", fontsize=10, color="#3D6553")
ax.text(1, 6.5, "Product logic on top: years whose weather effect is <= -7% (at most 2 of 5) are replaced by the yield expected under normal weather,\n"
        "capped at +7%, then the adjusted base yield sets the insured amount. Training used a June 1 transplanting date.",
        fontsize=9.6, color="#3D6553", linespacing=1.4)
save(fig, "fig1_model_pipeline.png")

# ---------- 2. model comparison ----------
names = ["5-year average\n(current method)", "Lasso", "Gradient\nboosting", "Ridge", "Neural net\n(5 seeds)", "Ridge + net\nblend (chosen)"]
nat = [6.579, 5.632, 5.811, 5.558, 5.497, 5.451]
jn = [7.198, 6.146, 6.230, 6.065, 6.022, 5.975]
x = np.arange(len(names))
fig, ax = plt.subplots(figsize=(10, 5.4))
ax.bar(x - 0.2, nat, 0.38, color=[GRAY] + [G6] * 4 + [G9], label="Nationwide (78 counties)")
ax.bar(x + 0.2, jn, 0.38, color=[LINE] + ["#7DBE9C"] * 4 + ["#2F6B55"], label="Jeonnam")
for i in range(len(names)):
    ax.text(x[i] - 0.2, nat[i] + 0.06, f"{nat[i]:.2f}", ha="center", fontsize=9, fontweight="bold" if i == 5 else "normal")
    ax.text(x[i] + 0.2, jn[i] + 0.06, f"{jn[i]:.2f}", ha="center", fontsize=9, fontweight="bold" if i == 5 else "normal")
ax.set_xticks(x)
ax.set_xticklabels(names, fontsize=9.5)
ax.set_ylim(4.6, 7.7)
ax.set_ylabel("Leave-one-year-out RMSE (% points) - lower is better")
ax.set_title("The weather model cuts the error of the 5-year average by about 17%", fontsize=13, fontweight="bold", loc="left")
ax.legend(handles=[Patch(color=G6, label="Nationwide (darker bar)"), Patch(color="#7DBE9C", label="Jeonnam (lighter bar)")], frameon=False, loc="upper right")
ax.text(0.0, -0.2, "Axis starts at 4.6. RMSE = error of the predicted yield change vs the 5-year average. 1,655 county-years, 2001-2025.",
        transform=ax.transAxes, fontsize=8.5, color="#5B7A6B")
save(fig, "fig2_model_comparison.png")

# ---------- 3. predicted vs actual ----------
jn_mask = (cv["province"] == "전라남도").values
fig, ax = plt.subplots(figsize=(7.4, 6.2))
ax.scatter(cv.loc[~jn_mask, "pred_dev_cv"], cv.loc[~jn_mask, "dev_pct"], s=12, color=GRAY, alpha=0.7, label="Other provinces")
ax.scatter(cv.loc[jn_mask, "pred_dev_cv"], cv.loc[jn_mask, "dev_pct"], s=16, color=G6, alpha=0.85, label="Jeonnam")
lim = (-32, 28)
ax.plot(lim, lim, color=G9, lw=1.4, ls="--", label="Perfect prediction")
ax.axhline(0, color=LINE, lw=1)
ax.axvline(0, color=LINE, lw=1)
ax.set_xlim(-16, 16)
ax.set_ylim(*lim)
ax.set_xlabel("Predicted yield change vs 5-year average (%), out-of-sample")
ax.set_ylabel("Actual yield change vs 5-year average (%)")
r = np.corrcoef(cv["pred_dev_cv"], cv["dev_pct"])[0, 1]
ax.set_title("Out-of-sample predictions follow the actual yield changes", fontsize=12.5, fontweight="bold", loc="left")
ax.text(0.03, 0.04, f"Correlation {r:.2f} | RMSE {res['scores']['blend_ridge_mlp']['rmse']:.2f} vs {res['scores']['baseline_5yr_avg']['rmse']:.2f} for the 5-year average\n"
        f"(about {100 * (1 - (res['scores']['blend_ridge_mlp']['rmse'] / res['scores']['baseline_5yr_avg']['rmse']) ** 2):.0f}% of the variance in yield change)",
        transform=ax.transAxes, fontsize=9, color=G9, va="bottom", bbox=dict(fc="white", ec=LINE, boxstyle="round,pad=0.4"))
ax.legend(frameon=False, loc="upper left", fontsize=9)
save(fig, "fig3_predicted_vs_actual.png")

# ---------- 4. ridge coefficients ----------
z = np.load("data/model_np.npz", allow_pickle=True)
cols, coef = [str(c) for c in z["cols"]], z["r_coef"]
STG = {"S1_tiller": "Tillering", "S2_panicle": "Panicle init.", "S3_heading": "Heading", "S4_ripen": "Ripening"}
VAR = {"tmean": "mean temp", "tmax": "max temp", "tmin": "min temp", "rain": "rainfall", "sun": "sunshine", "hot": "hot days (>=33C)",
       "heavy": "heavy-rain days", "wind": "peak gust", "coldnight": "cold nights"}


def label(c):
    parts = c.split("_")
    stage = STG["_".join(parts[:2])]
    var = VAR[parts[2]]
    when = "5-yr mean" if parts[3] == "lag5" else "this year"
    return f"{stage} - {var} ({when})"


order = np.argsort(-np.abs(coef))[:12][::-1]
fig, ax = plt.subplots(figsize=(9.6, 5.6))
ax.barh([label(cols[i]) for i in order], [coef[i] for i in order], color=[G6 if coef[i] > 0 else RED for i in order], height=0.65)
for k, i in enumerate(order):
    ax.text(coef[i] + (0.02 if coef[i] >= 0 else -0.02), k, f"{coef[i]:+.2f}", va="center", ha="left" if coef[i] >= 0 else "right", fontsize=8.5)
ax.axvline(0, color=LINE, lw=1)
ax.set_xlim(-1.4, 1.05)
ax.set_xlabel("Ridge coefficient: effect on yield change (% points) per 1 standard deviation")
ax.set_title("Which weather items the linear half of the model leans on most", fontsize=12.5, fontweight="bold", loc="left")
ax.text(0, -0.17, "Green raises yield, red lowers it. Half of the model (ridge) can be read item by item; the neural-net half cannot.",
        transform=ax.transAxes, fontsize=8.5, color="#5B7A6B")
save(fig, "fig4_ridge_coefficients.png")

# ---------- 5. backtest ----------
bt = pd.read_csv("data/backtest_jeonnam.csv", encoding="utf-8-sig")
adj = bt[bt.replaced > 0]
mae_r, mae_a = (adj.y - adj.regional).abs().mean(), (adj.y - adj.adjusted).abs().mean()
closer = ((adj.y - adj.adjusted).abs() < (adj.y - adj.regional).abs()).mean() * 100
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.8), gridspec_kw={"width_ratios": [1.2, 1]})
a1.bar(["5-year average", "ClimateCredit\nadjusted base yield"], [mae_r, mae_a], color=[GRAY, G6], width=0.55)
for i, v in enumerate([mae_r, mae_a]):
    a1.text(i, v + 0.3, f"{v:.1f}", ha="center", fontsize=12, fontweight="bold")
a1.set_ylim(20, 29)
a1.set_ylabel("Mean error vs the year's actual yield (kg/10a)")
a1.set_title(f"Error {mae_r:.1f} -> {mae_a:.1f} kg/10a ({100 * (mae_a / mae_r - 1):+.0f}%)", fontsize=11.5, fontweight="bold", loc="left")
a2.pie([closer, 100 - closer], colors=[G6, GRAY], startangle=90, counterclock=False, wedgeprops=dict(width=0.38, edgecolor="white"))
a2.text(0, 0, f"{closer:.0f}%", ha="center", va="center", fontsize=22, fontweight="bold")
a2.set_title(f"Closer to the actual yield\nin {int(round(closer * len(adj) / 100))} of {len(adj)} adjusted cases", fontsize=11.5, fontweight="bold")
fig.suptitle("Jeonnam back-test: 22 counties x 2006-2025 (365 county-years, 131 adjusted)", fontsize=12.5, fontweight="bold", x=0.02, y=1.04, ha="left")
fig.text(0.02, -0.03, "Axis starts at 20. Weather effects come from a model fitted on all years, so this is somewhat optimistic.", fontsize=8.5, color="#5B7A6B")
save(fig, "fig5_backtest.png")

# ---------- 6. tuning trade-off ----------
rules = [("5-year average", 0.00, 1.8), ("Current rule\n(-7%, max 2, cap +7%)", 0.59, -0.9), ("Looser\n(-5%, max 3)", 1.09, -3.3),
         ("Loosest\n(any year, cap +10%)", 1.77, -6.5)]
fig, ax = plt.subplots(figsize=(9.6, 5.4))
ax.axhspan(-2, 2, color=G1, zorder=0)
ax.axhline(0, color=G9, lw=1)
for name, u, bias in rules:
    cur = name.startswith("Current")
    ax.scatter(u, bias, s=260 if cur else 140, color=G9 if cur else (GRAY if name.startswith("5") else GOLD), zorder=3)
    ax.annotate(name, (u, bias), xytext=(10, 10 if bias > -5 else -34), textcoords="offset points", fontsize=9.5, fontweight="bold" if cur else "normal")
ax.set_xlabel("Average rise of the base yield vs the 5-year average (%) - more farmer benefit ->")
ax.set_ylabel("Bias: actual yield - base yield (kg/10a)\nnegative = base above what farms actually harvest")
ax.set_xlim(-0.2, 2.4)
ax.set_ylim(-9, 4)
ax.invert_yaxis()
ax.set_title("More payout means the base drifts above actual yields; we tuned for accuracy", fontsize=12.5, fontweight="bold", loc="left")
ax.text(0.01, 0.97, "Shaded: base within +/-2 kg/10a of actual yields (balanced)", transform=ax.transAxes, fontsize=9, color="#3D6553", va="top")
ax.text(0.0, -0.17, "Jeonnam back-test, 365 county-years. The y-axis is flipped so that 'base too high' points down.", transform=ax.transAxes, fontsize=8.5, color="#5B7A6B")
save(fig, "fig6_tuning_tradeoff.png")

# ---------- 7. Yeonggwang example ----------
e = Engine()
q = e.quote("전라남도", "영광군", 2025, (6, 1), 6)
yrs, act, nor = q["years"], q["actual"], q["normal"]
rep = [y in q["replaced_years"] for y in yrs]
used = [nor[i] if rep[i] else act[i] for i in range(len(yrs))]
fig, ax = plt.subplots(figsize=(9.6, 5.2))
xx = np.arange(len(yrs))
ax.bar(xx - 0.2, act, 0.38, color=GRAY, label="Actual yield")
ax.bar(xx + 0.2, used, 0.38, color=[GOLD if r else G6 for r in rep], label="Value used for the base yield")
for i in range(len(yrs)):
    ax.text(xx[i] - 0.2, act[i] - 3, f"{act[i]:.0f}", ha="center", va="top", fontsize=9, color=G9)
    ax.text(xx[i] + 0.2, used[i] - 3, f"{used[i]:.0f}", ha="center", va="top", fontsize=9, color="white" if not rep[i] else G9, fontweight="bold")
    ax.text(xx[i], max(act[i], used[i]) + 2, f"weather {q['effect_pct'][i]:+.1f}%", ha="center", fontsize=9,
            color=RED if rep[i] else G9, fontweight="bold" if rep[i] else "normal")
ax.set_xticks(xx)
ax.set_xticklabels(yrs)
ax.set_ylim(380, 545)
ax.set_ylabel("Yield (kg/10a), axis starts at 380")
ax.legend(handles=[Patch(color=GRAY, label="Actual yield"), Patch(color=G6, label="Value used for the base yield"),
                   Patch(color=GOLD, label="Replaced: yield expected under normal weather")], frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=9)
ax.set_title(f"Example: Yeonggwang, enrollment 2025 - base yield {q['regional_base']:.0f} -> {q['adjusted_base']:.0f} kg/10a ({q['uplift_pct']:+.1f}%)",
             fontsize=12.5, fontweight="bold", loc="left")
save(fig, "fig7_example_yeonggwang.png")
