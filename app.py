import json, os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from product import Engine, COVERAGE, SHOCK_EFFECT_PCT, UPLIFT_CAP_PCT, MAX_REPLACED, DEFAULT_PRICE

matplotlib.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

# brand palette (from the ClimateCredit logo)
G9, G6, G1, GOLD, LINE = "#0F3D2E", "#1F8F5A", "#E8F3EC", "#E0A526", "#D6E6DB"

st.set_page_config(page_title="ClimateCredit", page_icon=os.path.join(ASSETS, "icon.png"), layout="wide")

st.markdown(f"""
<style>
.stApp {{ background:#F5F9F6; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1400px; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.cc-tag {{ color:#4C6B5C; font-size:1.0rem; margin-top:10px; line-height:1.4; }}
.cc-pill {{ display:inline-block; background:{GOLD}; color:#fff; font-weight:700; font-size:.72rem; border-radius:999px; padding:2px 10px; margin-right:8px; vertical-align:middle; }}
.cc-sec {{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.2rem; color:{G9}; margin:4px 0 12px; }}
.cc-sec .n {{ background:{G6}; color:#fff; border-radius:50%; width:30px; height:30px; display:inline-flex; align-items:center; justify-content:center; font-size:.95rem; }}
.cc-card {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:14px 16px; height:100%; box-shadow:0 1px 2px rgba(15,61,46,.05); }}
.cc-card.hl {{ border:2px solid {G6}; background:linear-gradient(180deg,#fff 0%,{G1} 100%); }}
.cc-lab {{ font-size:.78rem; color:#5B7A6B; font-weight:600; }}
.cc-val {{ font-size:1.8rem; font-weight:800; color:{G9}; line-height:1.25; }}
.cc-unit {{ font-size:.9rem; font-weight:600; color:#5B7A6B; margin-left:4px; }}
.cc-delta {{ display:inline-block; background:#DDF3E6; color:#13724A; border-radius:999px; padding:1px 10px; font-size:.82rem; font-weight:700; margin-top:2px; }}
.cc-badge {{ display:inline-block; border-radius:12px; padding:2px 16px; font-size:1.5rem; font-weight:800; color:#fff; }}
.cc-call {{ border-left:6px solid {G6}; background:#fff; border-radius:10px; padding:12px 16px; color:{G9}; margin:14px 0; border-top:1px solid {LINE}; border-right:1px solid {LINE}; border-bottom:1px solid {LINE}; }}
.cc-call.warn {{ border-left-color:{GOLD}; background:#FFF8E5; }}
.cc-call.bad {{ border-left-color:#D73027; background:#FDECEA; }}
table.cc-t {{ width:100%; border-collapse:separate; border-spacing:0; border:1px solid {LINE}; border-radius:12px; overflow:hidden; background:#fff; }}
table.cc-t th {{ background:{G9}; color:#fff; padding:10px 12px; font-size:.85rem; text-align:right; }}
table.cc-t th:first-child, table.cc-t td:first-child {{ text-align:left; }}
table.cc-t td {{ padding:10px 12px; text-align:right; border-top:1px solid {LINE}; color:{G9}; font-variant-numeric:tabular-nums; }}
table.cc-t tr:nth-child(even) td {{ background:#F3F9F5; }}
table.cc-t td.pos {{ color:#13724A; font-weight:700; }}
.cc-foot {{ color:#6F8A7B; font-size:.78rem; margin-top:18px; text-align:center; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff; border-color:{LINE} !important; border-radius:14px; }}
</style>
""", unsafe_allow_html=True)

EN_NAME = {"강진군": "Gangjin", "고흥군": "Goheung", "곡성군": "Gokseong", "광양시": "Gwangyang", "구례군": "Gurye",
           "나주시": "Naju", "담양군": "Damyang", "목포시": "Mokpo", "무안군": "Muan", "보성군": "Boseong",
           "순천시": "Suncheon", "신안군": "Sinan", "여수시": "Yeosu", "영광군": "Yeonggwang", "영암군": "Yeongam",
           "완도군": "Wando", "장성군": "Jangseong", "장흥군": "Jangheung", "진도군": "Jindo", "함평군": "Hampyeong",
           "해남군": "Haenam", "화순군": "Hwasun",
           "광주": "Gwangju", "남원": "Namwon", "목포": "Mokpo", "여수": "Yeosu", "완도": "Wando", "순천": "Suncheon",
           "장흥": "Jangheung", "해남": "Haenam", "고흥": "Goheung"}
EN_PROV = {"전라남도": "Jeollanam-do", "전라북도": "Jeollabuk-do", "경상남도": "Gyeongsangnam-do", "경상북도": "Gyeongsangbuk-do",
           "강원도": "Gangwon-do", "경기도": "Gyeonggi-do", "충청남도": "Chungcheongnam-do", "충청북도": "Chungcheongbuk-do",
           "제주도": "Jeju-do", "인천광역시": "Incheon", "울산광역시": "Ulsan", "광주광역시": "Gwangju"}


def en(name):
    """English display name for a county/station: explicit table first, else romanization of the stem."""
    if name in EN_NAME:
        return EN_NAME[name]
    base = name.rstrip("시군구") or name
    if base in EN_NAME:
        return EN_NAME[base]
    try:
        from korean_romanizer.romanizer import Romanizer
        return Romanizer(base).romanize().capitalize()
    except Exception:
        return name


TXT = {
    "ko": dict(
        tag="농가마다 다른 기상 노출을 반영한 맞춤 보험가입금액", pill="프로토타입", sub="흥국화재 계리 담당자 검토용 · 쌀(논벼) · 전남 파일럿",
        h1="① 가입 체크리스트", prov="논 위치 ① 도·광역시", county="논 위치 ② 시·군", variety="품종",
        other_prov="전남 외 지역은 같은 모델로 계산한 참고용이며, 파일럿 검증은 전남에서 했습니다.",
        varieties=["조생종", "중생종", "중만생종"], tdate="이앙일 (월·일만 사용, 연도 무관)", tmonth="월", tday="일",
        irrig="관개·배수", irrigs=["양호", "보통", "불량"],
        method="재배방식", methods=["기계이앙", "손이앙", "직파"], past="최근 5년 피해 경험 (회)", area="재배면적 (ha)",
        verified="**기록으로 확인된 항목** (가입·공제 기록과 대조 가능한 것만 체크)",
        items=["품종", "이앙일", "관개·배수", "논 위치", "재배방식", "과거 피해"], price="가입가격 (원/kg, 팀 가정)",
        year="가입 기준 연도 (직전 5년 이력 사용)",
        note="모델에 직접 반영되는 입력은 **논 위치(관측소)와 이앙일**(생육 단계별 기상 계산)이에요. 나머지 항목은 신뢰도 판정에 쓰이고, 모델 반영은 검증 후 단계로 남겨 뒀어요.",
        h2="② 농가별 기상 노출과 맞춤 기준수확량", missing="이 시군은 최근 5년 기록이 부족해 5개년 평균을 그대로 사용합니다.",
        m_reg="5개년 평균 (현행 방식)", m_adj="기상 보정 후 (맞춤)", m_stn="가장 가까운 관측소", own=" · 동일 지역", near=" · 인접", m_conf="신뢰도",
        fb="체크리스트 확인 항목이 부족해 **5개년 평균으로 대체**했습니다. (신뢰도 Low)",
        replaced="**{ys}년**은 기상 영향이 컸던 해로 판정되어 **평년 날씨였다면의 수확량으로 대체**했습니다 (최근 5년 중 최대 {mx}개, 상한 +{cap:.0f}%).",
        noshock="최근 5년 중 기상 영향이 큰 해가 없어 5개년 평균과 같은 값을 사용합니다.",
        actual="실제 수확량", used="기준에 쓴 값", rep_lbl="평년 날씨 기준으로 대체한 해", wx="기상", unit="kg/10a",
        h3="③ 보장수준별 가입금액 (5개년 평균 vs 기상 보정 후)", cols=["보장수준", "5개년 평균 기준", "기상 보정 후", "차이", "국비 보조율"], won="원",
        cap_amt="가입금액 = 기준수확량 × 면적({a:.1f}ha) × 보장수준 × 가입가격({p:,}원/kg, 팀 가정). 맞춤값은 계리 담당자 검토 후 확정됩니다.",
        h4="④ 검증 — 연도 하나씩 빼고 예측한 결과 (2001~2025, 전국 78개 시군)",
        v1="5개년 평균 방식 오차", v2="기상 모델 오차", v3="전남 시군만 · 기준선", v4="전남 시군만 · 모델",
        bt="전남 22개 시군 × 2006~2025 백테스트: 기상 영향이 큰 해를 대체한 {n}건에서 맞춤 기준수확량이 다음 해 실제 수확량에 더 가까운 비율 {c:.0f}%, 평균 오차 {e1:.1f} → {e2:.1f} kg/10a. 평균 기준수확량 상승 {u:+.1f}%.",
        exp="가정과 한계 (팀 가정은 검증 전 값)",
        assume=("- 학습 기상은 이앙일을 **6월 1일**로 고정한 값이고, 시연에서만 농가 입력 이앙일로 생육 구간을 옮겨 계산합니다.\n"
                "- 생육 단계 구간(분얼·유수형성·출수·등숙)과 기상 변수는 일반적 기준으로 정한 **팀 가정**입니다.\n"
                "- 이상기후 해 판정 기준 {thr:.0f}%, 대체 최대 {mx}개, 상한 +{cap:.0f}%는 팀 가정입니다.\n"
                "- 기상은 **기상청 일자료(ASOS 4~10월)**, 수확량은 통계청 시군별 논벼 단수(1996~2025)입니다.\n"
                "- 관개·배수, 재배방식, 과거 피해는 아직 모델에 반영하지 않고 신뢰도 판정에만 사용합니다.\n"
                "- 보험사 실제 가입·공제 자료로 재검증하기 전의 프로토타입입니다."),
        foot="ClimateCredit · APRU 해커톤 프로토타입 · 데이터: 통계청(KOSIS), 기상청(ASOS)",
    ),
    "en": dict(
        tag="Insured amounts that reflect each farm's own weather exposure", pill="PROTOTYPE",
        sub="For Heungkuk Fire & Marine actuaries · Rice (paddy) · Jeonnam pilot",
        h1="① Enrollment checklist", prov="Field location ① Province", county="Field location ② City / county", variety="Rice variety",
        other_prov="Outside Jeonnam the same model is applied for reference only; the pilot was validated in Jeonnam.",
        varieties=["Early-maturing", "Mid-maturing", "Mid-late maturing"], tdate="Transplanting date (month/day only, year not used)",
        tmonth="Month", tday="Day", irrig="Irrigation / drainage",
        irrigs=["Good", "Fair", "Poor"], method="Cultivation method", methods=["Machine transplant", "Hand transplant", "Direct seeding"],
        past="Damage events in the last 5 years", area="Paddy area (ha)",
        verified="**Items verified against records** (tick only what can be checked against enrollment/claims records)",
        items=["Variety", "Transplant date", "Irrigation/drainage", "Field location", "Method", "Past damage"],
        price="Insured price (KRW/kg, team assumption)", year="Enrollment year (uses the previous 5 years)",
        note="Inputs used **directly by the model**: **field location (weather station) and transplanting date** (growth-stage weather). "
             "The other items only affect the confidence label for now; adding them to the model is a post-validation step.",
        h2="② Farm-specific weather exposure and personalised base yield",
        missing="Not enough yield history for this county, so the 5-year average is used.",
        m_reg="5-year average (current method)", m_adj="After weather adjustment (personalised)", m_stn="Nearest weather station", own=" · same area", near=" · nearby",
        m_conf="Confidence",
        fb="Too few checklist items are verified, so the **5-year average is used** (confidence Low).",
        replaced="**{ys}**: weather impact was large, so the yield is **replaced by the yield expected under normal weather** "
                 "(at most {mx} of the last 5 years, capped at +{cap:.0f}%).",
        noshock="No year in the last 5 had a large weather impact, so the adjusted value equals the 5-year average.",
        actual="Actual yield", used="Value used for base yield", rep_lbl="Replaced with normal-weather yield", wx="weather", unit="kg/10a",
        h3="③ Insured amount by coverage level (5-year average vs weather-adjusted)",
        cols=["Coverage", "5-year average basis", "After weather adjustment", "Difference", "National subsidy"], won=" KRW",
        cap_amt="Insured amount = base yield × area ({a:.1f} ha) × coverage × price ({p:,} KRW/kg, team assumption). Final figures are confirmed after actuarial review.",
        h4="④ Validation — leave-one-year-out prediction (2001–2025, 78 counties nationwide)",
        v1="5-year-average error", v2="Weather model error", v3="Jeonnam only · baseline", v4="Jeonnam only · model",
        bt="Jeonnam backtest, 22 counties × 2006–2025: in the {n} cases where shock years were replaced, the personalised base was closer to the next year's actual yield in {c:.0f}% of cases; "
           "mean error {e1:.1f} → {e2:.1f} kg/10a. Average base-yield uplift {u:+.1f}%.",
        exp="Assumptions and limitations (team assumptions are not yet validated)",
        assume=("- Training weather uses a **fixed June 1 transplanting date**; in the demo the growth-stage windows shift to the farm's entered date.\n"
                "- Growth-stage windows (tillering, panicle initiation, heading, ripening) and weather variables are **team assumptions** based on typical practice.\n"
                "- Shock threshold {thr:.0f}%, at most {mx} replaced years and the +{cap:.0f}% cap are team assumptions.\n"
                "- Weather: **KMA ASOS daily data (Apr–Oct)**; yield: Statistics Korea county paddy-rice yield (1996–2025).\n"
                "- Irrigation/drainage, cultivation method and past damage are not yet in the model; they only drive the confidence label.\n"
                "- A prototype until re-validated with the insurer's own enrollment and claims data."),
        foot="ClimateCredit · APRU hackathon prototype · Data: Statistics Korea (KOSIS), Korea Meteorological Administration (ASOS)",
    ),
}


@st.cache_resource
def get_engine():
    return Engine()


@st.cache_data
def get_backtest(thr):
    p = os.path.join(HERE, "data", "backtest_jeonnam.csv")
    return pd.read_csv(p, encoding="utf-8-sig") if os.path.exists(p) else None


def sec(title):
    num, rest = title[0], title[1:].strip()
    st.markdown(f"<div class='cc-sec'><span class='n'>{'①②③④'.index(num) + 1}</span>{rest}</div>", unsafe_allow_html=True)


def card(label, value, unit="", delta=None, hl=False):
    d = f"<div><span class='cc-delta'>{delta}</span></div>" if delta else ""
    u = f"<span class='cc-unit'>{unit}</span>" if unit else ""
    return f"<div class='cc-card{' hl' if hl else ''}'><div class='cc-lab'>{label}</div><div class='cc-val'>{value}{u}</div>{d}</div>"


eng = get_engine()
res = json.load(open(os.path.join(HERE, "data", "results.json"), encoding="utf-8"))

qp_lang = st.query_params.get("lang", "ko")
h1c, h2c, h3c = st.columns([2.4, 5, 1.6])
with h3c:
    lang_label = st.radio("Language / 언어", ["한국어", "English"], index=1 if qp_lang == "en" else 0, horizontal=True)
L = "en" if lang_label == "English" else "ko"
t = TXT[L]
disp = en if L == "en" else (lambda c: c)
disp_prov = (lambda p: EN_PROV.get(p, p)) if L == "en" else (lambda p: p)
with h1c:
    st.image(os.path.join(ASSETS, "logo.png"), width=300)
with h2c:
    st.markdown(f"<div class='cc-tag'><span class='cc-pill'>{t['pill']}</span><b style='color:{G9}'>{t['tag']}</b><br>{t['sub']}</div>",
                unsafe_allow_html=True)

st.write("")
left, right = st.columns([1, 2.1], gap="large")

with left:
    with st.container(border=True):
        sec(t["h1"])
        skip = {"전라남도", "광주광역시", "울산광역시", "인천광역시", "제주도"}   # too little history / too little paddy for this model
        provs = ["전라남도"] + sorted({p for (p, _) in eng.cmap if p not in skip})
        prov = st.selectbox(t["prov"], provs, index=0, format_func=disp_prov)
        cl = eng.counties(prov)
        county = st.selectbox(t["county"], cl, index=cl.index("영광군") if "영광군" in cl else 0, format_func=disp, key=f"county_{prov}")
        if prov != "전라남도":
            st.caption(t["other_prov"])
        st.selectbox(t["variety"], t["varieties"], index=2)
        st.markdown(f"**{t['tdate']}**")
        mc1, mc2 = st.columns(2)
        t_month = mc1.selectbox(t["tmonth"], [5, 6], index=1, format_func=lambda m: (f"{m}월" if L == "ko" else ["", "", "", "", "", "May", "Jun"][m]))
        t_day = mc2.selectbox(t["tday"], list(range(1, 32 if t_month == 5 else 31)), index=0)
        st.selectbox(t["irrig"], t["irrigs"])
        st.selectbox(t["method"], t["methods"])
        st.slider(t["past"], 0, 5, 1)
        area = st.number_input(t["area"], 0.1, 50.0, 1.0, 0.1)
        st.markdown(t["verified"])
        cols = st.columns(2)
        verified = [cols[i % 2].checkbox(lab, value=True, key=f"v{i}") for i, lab in enumerate(t["items"])]
        price = st.number_input(t["price"], 1000, 5000, DEFAULT_PRICE, 50)
        target_year = st.selectbox(t["year"], [2025, 2026, 2024, 2023, 2022], index=0)
        st.caption(t["note"])

md = (t_month, t_day)
q = eng.quote(prov, county, target_year, md, sum(verified), 6, area, price)

with right:
    sec(t["h2"])
    if "regional_base" not in q:
        st.markdown(f"<div class='cc-call warn'>{t['missing']}</div>", unsafe_allow_html=True)
    else:
        conf = q["confidence"]
        bcol = {"High": G6, "Medium": GOLD, "Low": "#D73027"}[conf]
        sn = q["station_name"]
        sname = en(sn) if (L == "en" and sn) else sn
        adj = q["adjusted_base"] if not q["fallback"] else q["regional_base"]
        c1, c2, c3, c4 = st.columns([1.15, 1.25, 1, 0.8])
        c1.markdown(card(t["m_reg"], f"{q['regional_base']:.0f}", "kg/10a"), unsafe_allow_html=True)
        c2.markdown(card(t["m_adj"], f"{adj:.0f}", "kg/10a", f"▲ {q['uplift_pct']:+.1f}%" if q["uplift_pct"] > 0.05 else "± 0.0%", hl=True), unsafe_allow_html=True)
        c3.markdown(card(t["m_stn"] + (t["own"] if q["own_station"] else t["near"]), sname), unsafe_allow_html=True)
        c4.markdown(f"<div class='cc-card'><div class='cc-lab'>{t['m_conf']}</div><div style='margin-top:6px'><span class='cc-badge' style='background:{bcol}'>{conf}</span></div></div>",
                    unsafe_allow_html=True)

        if q["fallback"]:
            st.markdown(f"<div class='cc-call bad'>{t['fb']}</div>".replace("**", ""), unsafe_allow_html=True)
        elif q["replaced_years"]:
            ys = ", ".join(str(y) for y in q["replaced_years"])
            msg = t["replaced"].format(ys=ys, mx=MAX_REPLACED, cap=UPLIFT_CAP_PCT)
            msg = msg.replace("**", "<b>", 1).replace("**", "</b>", 1).replace("**", "<b>", 1).replace("**", "</b>", 1)
            st.markdown(f"<div class='cc-call'>{msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='cc-call warn'>{t['noshock']}</div>", unsafe_allow_html=True)

        yrs = q["years"]
        fig, ax = plt.subplots(figsize=(7.4, 3.1))
        fig.patch.set_facecolor("white")
        x = np.arange(len(yrs))
        rep = [y in q["replaced_years"] for y in yrs]
        norm = [q["normal"][i] if rep[i] else q["actual"][i] for i in range(len(yrs))]
        ax.bar(x - 0.2, q["actual"], 0.4, color="#B7CFC1")
        ax.bar(x + 0.2, norm, 0.4, color=[GOLD if r else G6 for r in rep])
        for i, e in enumerate(q["effect_pct"]):
            ax.text(x[i], max(q["actual"][i], norm[i]) + 2, f"{t['wx']} {e:+.1f}%", ha="center", fontsize=8.5,
                    color="#B23A2E" if e <= SHOCK_EFFECT_PCT else G9, fontweight="bold" if e <= SHOCK_EFFECT_PCT else "normal")
        ax.set_xticks(x)
        ax.set_xticklabels(yrs, color=G9)
        lo = min(min(q["actual"]), min(norm))
        ax.set_ylim(lo * 0.85, max(max(q["actual"]), max(norm)) * 1.07)
        ax.set_ylabel(t["unit"], color=G9)
        ax.tick_params(colors=G9)
        ax.legend(handles=[Patch(color="#B7CFC1", label=t["actual"]), Patch(color=G6, label=t["used"]),
                           Patch(color=GOLD, label=t["rep_lbl"])], fontsize=8, loc="lower right", frameon=False, ncol=1)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(LINE)
        fig.tight_layout()
        with st.container(border=True):
            st.pyplot(fig)

        sec(t["h3"])
        tb = pd.DataFrame(q["table"])
        rows = ""
        for _, r in tb.iterrows():
            pos = "pos" if r["diff"] > 0 else ""
            rows += (f"<tr><td><b>{int(r['coverage'])}%</b></td><td>{r['regional_amt']:,.0f}{t['won']}</td>"
                     f"<td><b>{r['personal_amt']:,.0f}{t['won']}</b></td><td class='{pos}'>{r['diff']:+,.0f}{t['won']}</td>"
                     f"<td>{int(r['subsidy_pct'])}%</td></tr>")
        head = "".join(f"<th>{c}</th>" for c in t["cols"])
        st.markdown(f"<table class='cc-t'><tr>{head}</tr>{rows}</table>", unsafe_allow_html=True)
        st.caption(t["cap_amt"].format(a=area, p=price))

st.write("")
sec(t["h4"])
sc = res["scores"]
best = res["best_model"]
v = st.columns(4)
v[0].markdown(card(t["v1"], f"{sc['baseline_5yr_avg']['rmse']:.2f}", "%"), unsafe_allow_html=True)
v[1].markdown(card(t["v2"], f"{sc[best]['rmse']:.2f}", "%", f"▼ {res['improvement_pct_vs_baseline']:.1f}%", hl=True), unsafe_allow_html=True)
v[2].markdown(card(t["v3"], f"{sc['baseline_5yr_avg']['rmse_jeonnam']:.2f}", "%"), unsafe_allow_html=True)
v[3].markdown(card(t["v4"], f"{sc[best]['rmse_jeonnam']:.2f}", "%", f"▼ {res['improvement_pct_vs_baseline_jeonnam']:.1f}%", hl=True), unsafe_allow_html=True)
bt = get_backtest(SHOCK_EFFECT_PCT)
if bt is not None:
    bt = bt.copy()
    bt["er"] = (bt.y - bt.regional).abs()
    bt["ea"] = (bt.y - bt.adjusted).abs()
    r = bt[bt.replaced > 0]
    st.caption(t["bt"].format(n=len(r), c=100 * (r.ea < r.er).mean(), e1=r.er.mean(), e2=r.ea.mean(),
                              u=100 * (r.adjusted / r.regional - 1).mean()))
with st.expander(t["exp"]):
    st.markdown(t["assume"].format(thr=SHOCK_EFFECT_PCT, mx=MAX_REPLACED, cap=UPLIFT_CAP_PCT))
st.markdown(f"<div class='cc-foot'>{t['foot']}</div>", unsafe_allow_html=True)
