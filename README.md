# ClimateCredit - prototype README

**Team T1 - ClimateCredit** | APRU / APAC Data, AI & Policy Hackathon: Financial Health Frontiers | Partner: Heungkuk Fire & Marine Insurance

ClimateCredit is a working prototype that sets a fairer **base yield** for rice crop insurance. Korea's rice insurance sets the base yield from the previous five years' average, so one bad-weather year can lower a farm's insured amount, and the cover it can claim after a loss, for years. The prototype uses the field's location and transplanting date to compute growth-stage weather, estimates how much that weather moved the yield, and replaces large weather-impact years with the yield expected under normal weather before the five-year average is taken.

## Open it (no installation)
| What | Link |
|---|---|
| Analysis page (English) | https://climatecredit-demo.streamlit.app/?lang=en |
| Analysis page (Korean) | https://climatecredit-demo.streamlit.app/ |
| Farmer-friendly page (English / Korean) | https://climatecredit-demo.streamlit.app/farmer?lang=en |
| Source code | https://github.com/raytoto0423/APRU_pro |

The app sleeps when idle: if it shows a "wake up" button, press it and wait about 30 seconds. Works in a desktop or phone browser.

## How to use it (2 minutes)
1. **Analysis page.** Open the "Introduction" panel to see how the insurance logic and the service flow work.
2. Section **1** shows the insured amount at 80% coverage and a table for 60-90% coverage (current five-year-average method vs weather-adjusted). Defaults: Yeonggwang, transplanting June 1, enrollment year 2025 (491 -> 499 kg/10a, +1.6%).
3. Section **2** (checklist box): change the location or the transplanting date and watch the numbers move. Untick three of the six "verified items" and the confidence drops to Low, so no adjustment is applied (safeguard).
4. Section **3** shows why: the five-year bars, the replaced year (2020, weather effect -8.3%) and an optional weather-curve explanation.
5. Section **4** shows validation (blocks A and B) and a box saying what is working, what is a team assumption and what is not validated.
6. **Farmer page** (link at the top right of the analysis page): the same result in plain words with big type, a traffic-light verdict, three next steps, and a short explanation of why a higher premium is not a loss.

## What is working, what is assumed
| Feature | Status |
|---|---|
| Weather recomputed live from location + transplanting date (KMA daily data, four growth stages) | Working. The model was trained with a June 1 date; other dates shift the stage windows but are not validated |
| Weather-effect model (ridge + small neural net, 72 inputs) | Working, leave-one-year-out validated |
| Replace large weather-impact years, adjusted base yield, insured amount by coverage level | Working. Thresholds (-7%, at most 2 replaced years, +7% cap) and price (2,500 KRW/kg) are **team assumptions** |
| Verification checklist -> confidence -> fallback to the five-year average | Working. Only the *number* of verified items is used |
| Variety, irrigation, cultivation method, past damage values | **Not in the model.** They are shown but do not change the result |
| Premium calculation | **Not included.** Insured amounts are the basis of cover, not claim payouts |
| Validation figures on the page | Pre-computed county-level results, not re-run on your inputs |

## Model
- **Target:** yield change (%) vs the county's previous five-year average. **Input:** 72 numbers per county-year = 4 growth stages x 9 weather variables as anomalies vs the station's normal (36) + the same values averaged over the previous five years (36).
- **Models:** ridge regression (alpha 300) and a small neural net (MLP 72 -> 16 -> 1, ReLU, dropout 0.3, AdamW, 5 seeds averaged), blended 50/50. No LSTM or CNN: the input is one row of summary numbers.
- **Training data:** 1,655 county-years, 78 counties, 2001-2025.
- **Validation (leave-one-year-out RMSE, % points):** five-year average 6.58 -> blend 5.45 nationwide (-17%); Jeonnam 7.20 -> 5.97 (-17%). Jeonnam back-test (22 counties, 2006-2025): of 131 adjusted cases, 67% had a base yield closer to the actual yield; mean error 26.7 -> 24.2 kg/10a. The back-test weather effects come from a model fitted on all years, so it is somewhat optimistic.
- **Honest limits:** county-level data only; June 1 training date; the neural-net half cannot be split by item; for enrollment year 2026 (2021-2025) none of the 22 Jeonnam counties gets an adjustment because 2020 leaves the five-year window.

## Data sources
- Statistics Korea (KOSIS), table DT_1ET0034: paddy-rice area, yield and production by county (kosis.kr).
- Korea Meteorological Administration, ASOS daily observations (Apr-Oct, 1996-2025), via the Public Data Portal (data.go.kr).
- Heungkuk Fire & Marine risk-management page and the Ministry of Agriculture's 2026 crop-insurance guidelines for the insurance background (see the Fact Sheet for the full source list).

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
`app.py` is the analysis page, `pages/farmer.py` the farmer page, `product.py` the quote and back-test engine, `npmodel.py` the numpy-only model inference, `data/` holds the trained weights (`model_np.npz`), a slimmed weather file, the yield table and pre-computed results. No API key is needed to run the app.

`training_and_analysis/` holds the scripts behind the numbers, for reading: `build_dataset.py` (72 features), `models.py`, `train_eval.py`, `train_eval2.py`, `train_final.py` (model comparison and final fit), `convert_model.py` (PyTorch to numpy weights), `fetch_asos.py` (weather download; reads a key from a local `.env` that is not in the repository), `simulate_benefit.py` and `optimize_base_model.py` (back-test simulation and rule tuning), `make_figures.py`. They need the raw downloaded data and PyTorch, so they are not runnable from this repository alone.

## AI use
Claude (Anthropic) assisted with code, data processing, analysis and drafting; ChatGPT gave feedback on wording and layout. All numbers shown come from the team's own data and code; confirm the full AI disclosure in the Fact Sheet.
