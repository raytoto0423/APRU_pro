import json, os
import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
import matplotlib.pyplot as plt
from product import Engine, COVERAGE, SHOCK_EFFECT_PCT, UPLIFT_CAP_PCT, MAX_REPLACED, DEFAULT_PRICE

matplotlib.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="ClimateCredit", layout="wide")

EN_NAME = {"강진군": "Gangjin", "고흥군": "Goheung", "곡성군": "Gokseong", "광양시": "Gwangyang", "구례군": "Gurye",
           "나주시": "Naju", "담양군": "Damyang", "목포시": "Mokpo", "무안군": "Muan", "보성군": "Boseong",
           "순천시": "Suncheon", "신안군": "Sinan", "여수시": "Yeosu", "영광군": "Yeonggwang", "영암군": "Yeongam",
           "완도군": "Wando", "장성군": "Jangseong", "장흥군": "Jangheung", "진도군": "Jindo", "함평군": "Hampyeong",
           "해남군": "Haenam", "화순군": "Hwasun",
           "광주": "Gwangju", "남원": "Namwon", "목포": "Mokpo", "여수": "Yeosu", "완도": "Wando", "순천": "Suncheon",
           "영광군": "Yeonggwang", "보성군": "Boseong", "강진군": "Gangjin", "장흥": "Jangheung", "해남": "Haenam",
           "고흥": "Goheung", "광양시": "Gwangyang", "진도군": "Jindo"}

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
        title="ClimateCredit · 농가별 맞춤 보험가입금액 (프로토타입)",
        sub="흥국화재 계리 담당자 검토용 시제품 · 쌀(논벼) · 전남 파일럿",
        h1="① 가입 체크리스트", prov="논 위치 ① 도·광역시", county="논 위치 ② 시·군", variety="품종",
        other_prov="전남 외 지역은 같은 모델로 계산한 참고용이며, 파일럿 검증은 전남에서 했습니다.",
        varieties=["조생종", "중생종", "중만생종"], tdate="이앙일", irrig="관개·배수", irrigs=["양호", "보통", "불량"],
        method="재배방식", methods=["기계이앙", "손이앙", "직파"], past="최근 5년 피해 경험 (회)", area="재배면적 (ha)",
        verified="**기록으로 확인된 항목** (가입·공제 기록과 대조 가능한 것만 체크)",
        items=["품종", "이앙일", "관개·배수", "논 위치", "재배방식", "과거 피해"], price="가입가격 (원/kg, 팀 가정)",
        year="가입 기준 연도 (직전 5년 이력 사용)",
        note="모델에 직접 반영되는 입력은 **논 위치(관측소)와 이앙일**(생육 단계별 기상 계산)이에요. 나머지 항목은 신뢰도 판정에 쓰이고, 모델 반영은 검증 후 단계로 남겨 뒀어요.",
        h2="② 농가별 기상 노출과 맞춤 기준수확량", missing="이 시군은 최근 5년 기록이 부족해 지역 수치를 그대로 사용합니다.",
        m_reg="지역 기준수확량", m_adj="맞춤 기준수확량", m_stn="가장 가까운 관측소", own=" (동일 지역)", near=" (인접)", m_conf="신뢰도",
        fb="체크리스트 확인 항목이 부족해 **지역 수치로 대체**했습니다. (신뢰도 Low)",
        replaced="{ys}년은 기상 영향이 컸던 해로 판정되어 **평년 날씨였다면의 수확량으로 대체**했습니다 (최근 5년 중 최대 {mx}개, 상한 +{cap:.0f}%).",
        noshock="최근 5년 중 기상 영향이 큰 해가 없어 지역 기준과 같은 값을 사용합니다.",
        actual="실제 수확량", used="맞춤 기준에 쓴 값", wx="기상", unit="kg/10a",
        h3="③ 보장수준별 가입금액 (지역 수치 vs 맞춤)", cols=["보장수준", "지역 가입금액", "맞춤 가입금액", "차이", "국비 보조율"], won="원",
        cap_amt="가입금액 = 기준수확량 × 면적({a:.1f}ha) × 보장수준 × 가입가격({p:,}원/kg, 팀 가정). 맞춤값은 계리 담당자 검토 후 확정됩니다.",
        h4="④ 검증 — 연도 하나씩 빼고 예측한 결과 (2001~2025, 전국 78개 시군)",
        v1="5개년 평균 방식 오차", v2="기상 모델 오차", v3="전남 시군만 (기준선)", v4="전남 시군만 (모델)",
        bt="전남 22개 시군 × 2006~2025 백테스트: 기상 영향이 큰 해를 대체한 {n}건에서 맞춤 기준수확량이 다음 해 실제 수확량에 더 가까운 비율 {c:.0f}%, 평균 오차 {e1:.1f} → {e2:.1f} kg/10a. 평균 기준수확량 상승 {u:+.1f}%.",
        exp="가정과 한계 (팀 가정은 검증 전 값)",
        assume=("- 학습 기상은 이앙일을 **6월 1일**로 고정한 값이고, 시연에서만 농가 입력 이앙일로 생육 구간을 옮겨 계산합니다.\n"
                "- 생육 단계 구간(분얼·유수형성·출수·등숙)과 기상 변수는 일반적 기준으로 정한 **팀 가정**입니다.\n"
                "- 이상기후 해 판정 기준 {thr:.0f}%, 대체 최대 {mx}개, 상한 +{cap:.0f}%는 팀 가정입니다.\n"
                "- 기상은 **기상청 일자료(ASOS 4~10월)**, 수확량은 통계청 시군별 논벼 단수(1996~2025)입니다.\n"
                "- 관개·배수, 재배방식, 과거 피해는 아직 모델에 반영하지 않고 신뢰도 판정에만 사용합니다.\n"
                "- 보험사 실제 가입·공제 자료로 재검증하기 전의 프로토타입입니다."),
    ),
    "en": dict(
        title="ClimateCredit · Farm-specific insured amount (prototype)",
        sub="Prototype for Heungkuk Fire & Marine actuaries · Rice (paddy) · Jeonnam pilot",
        h1="① Enrollment checklist", prov="Field location ① Province", county="Field location ② City / county", variety="Rice variety",
        other_prov="Outside Jeonnam the same model is applied for reference only; the pilot was validated in Jeonnam.",
        varieties=["Early-maturing", "Mid-maturing", "Mid-late maturing"], tdate="Transplanting date", irrig="Irrigation / drainage",
        irrigs=["Good", "Fair", "Poor"], method="Cultivation method", methods=["Machine transplant", "Hand transplant", "Direct seeding"],
        past="Damage events in the last 5 years", area="Paddy area (ha)",
        verified="**Items verified against records** (tick only what can be checked against enrollment/claims records)",
        items=["Variety", "Transplant date", "Irrigation/drainage", "Field location", "Method", "Past damage"],
        price="Insured price (KRW/kg, team assumption)", year="Enrollment year (uses the previous 5 years)",
        note="Inputs used **directly by the model**: **field location (weather station) and transplanting date** (growth-stage weather). "
             "The other items only affect the confidence label for now; adding them to the model is a post-validation step.",
        h2="② Farm-specific weather exposure and personalised base yield",
        missing="Not enough yield history for this county, so the regional figure is used.",
        m_reg="Regional base yield", m_adj="Personalised base yield", m_stn="Nearest weather station", own=" (same area)", near=" (nearby)",
        m_conf="Confidence",
        fb="Too few checklist items are verified, so the **regional figure is used** (confidence Low).",
        replaced="{ys}: weather impact was large, so the yield is **replaced by the yield expected under normal weather** "
                 "(at most {mx} of the last 5 years, capped at +{cap:.0f}%).",
        noshock="No year in the last 5 had a large weather impact, so the personalised value equals the regional one.",
        actual="Actual yield", used="Value used for base yield", wx="weather", unit="kg/10a",
        h3="③ Insured amount by coverage level (regional vs personalised)",
        cols=["Coverage", "Regional amount", "Personalised amount", "Difference", "National subsidy"], won=" KRW",
        cap_amt="Insured amount = base yield × area ({a:.1f} ha) × coverage × price ({p:,} KRW/kg, team assumption). Final figures are confirmed after actuarial review.",
        h4="④ Validation — leave-one-year-out prediction (2001–2025, 78 counties nationwide)",
        v1="5-year-average error", v2="Weather model error", v3="Jeonnam only (baseline)", v4="Jeonnam only (model)",
        bt="Jeonnam backtest, 22 counties × 2006–2025: in the {n} cases where shock years were replaced, the personalised base was closer to the next year's actual yield in {c:.0f}% of cases; "
           "mean error {e1:.1f} → {e2:.1f} kg/10a. Average base-yield uplift {u:+.1f}%.",
        exp="Assumptions and limitations (team assumptions are not yet validated)",
        assume=("- Training weather uses a **fixed June 1 transplanting date**; in the demo the growth-stage windows shift to the farm's entered date.\n"
                "- Growth-stage windows (tillering, panicle initiation, heading, ripening) and weather variables are **team assumptions** based on typical practice.\n"
                "- Shock threshold {thr:.0f}%, at most {mx} replaced years and the +{cap:.0f}% cap are team assumptions.\n"
                "- Weather: **KMA ASOS daily data (Apr–Oct)**; yield: Statistics Korea county paddy-rice yield (1996–2025).\n"
                "- Irrigation/drainage, cultivation method and past damage are not yet in the model; they only drive the confidence label.\n"
                "- A prototype until re-validated with the insurer's own enrollment and claims data."),
    ),
}


@st.cache_resource
def get_engine():
    return Engine()


@st.cache_data
def get_backtest(thr):
    p = os.path.join(HERE, "data", "backtest_jeonnam.csv")
    return pd.read_csv(p, encoding="utf-8-sig") if os.path.exists(p) else None


eng = get_engine()
res = json.load(open(os.path.join(HERE, "data", "results.json"), encoding="utf-8"))

qp_lang = st.query_params.get("lang", "ko")
top1, top2 = st.columns([6, 1])
with top2:
    lang_label = st.radio("Language / 언어", ["한국어", "English"], index=1 if qp_lang == "en" else 0, horizontal=True)
L = "en" if lang_label == "English" else "ko"
t = TXT[L]
disp = en if L == "en" else (lambda c: c)
disp_prov = (lambda p: EN_PROV.get(p, p)) if L == "en" else (lambda p: p)

with top1:
    st.title(t["title"])
    st.caption(t["sub"])

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader(t["h1"])
    skip = {"전라남도", "광주광역시", "울산광역시", "인천광역시", "제주도"}   # too little history / too little paddy for this model
    provs = ["전라남도"] + sorted({p for (p, _) in eng.cmap if p not in skip})
    prov = st.selectbox(t["prov"], provs, index=0, format_func=disp_prov)
    cl = eng.counties(prov)
    county = st.selectbox(t["county"], cl, index=cl.index("영광군") if "영광군" in cl else 0, format_func=disp, key=f"county_{prov}")
    if prov != "전라남도":
        st.caption(t["other_prov"])
    st.selectbox(t["variety"], t["varieties"], index=2)
    d = st.date_input(t["tdate"], value=dt.date(2025, 6, 1), min_value=dt.date(2025, 5, 1), max_value=dt.date(2025, 6, 30))
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

md = (d.month, d.day)
q = eng.quote(prov, county, target_year, md, sum(verified), 6, area, price)

with right:
    st.subheader(t["h2"])
    if "regional_base" not in q:
        st.warning(t["missing"])
    else:
        conf = q["confidence"]
        colr = {"High": "#1a9850", "Medium": "#f4a300", "Low": "#d73027"}[conf]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["m_reg"], f"{q['regional_base']:.0f} kg/10a")
        c2.metric(t["m_adj"], f"{(q['adjusted_base'] if not q['fallback'] else q['regional_base']):.0f} kg/10a", f"{q['uplift_pct']:+.1f}%")
        sn = q["station_name"]
        sname = en(sn) if (L == "en" and sn) else sn
        c3.metric(t["m_stn"] + (t["own"] if q["own_station"] else t["near"]), f"{sname}")
        c4.markdown(f"**{t['m_conf']}**<div style='font-size:2rem;font-weight:700;color:{colr}'>{conf}</div>", unsafe_allow_html=True)

        if q["fallback"]:
            st.error(t["fb"])
        elif q["replaced_years"]:
            ys = ", ".join(str(y) for y in q["replaced_years"]) + ("" if L == "en" else "")
            st.success(t["replaced"].format(ys=ys, mx=MAX_REPLACED, cap=UPLIFT_CAP_PCT))
        else:
            st.info(t["noshock"])

        yrs = q["years"]
        fig, ax = plt.subplots(figsize=(7, 3))
        x = np.arange(len(yrs))
        ax.bar(x - 0.2, q["actual"], 0.4, label=t["actual"], color="#9aa5b1")
        norm = [q["normal"][i] if yrs[i] in q["replaced_years"] else q["actual"][i] for i in range(len(yrs))]
        ax.bar(x + 0.2, norm, 0.4, label=t["used"], color="#2b7bba")
        for i, e in enumerate(q["effect_pct"]):
            ax.text(x[i], max(q["actual"][i], norm[i]) + 2, f"{t['wx']} {e:+.1f}%", ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(yrs)
        lo = min(min(q["actual"]), min(norm))
        ax.set_ylim(lo * 0.85, max(max(q["actual"]), max(norm)) * 1.06)
        ax.set_ylabel(t["unit"])
        ax.legend(fontsize=8, loc="lower right")
        ax.spines[["top", "right"]].set_visible(False)
        st.pyplot(fig)

        st.subheader(t["h3"])
        tb = pd.DataFrame(q["table"])
        out = pd.DataFrame({
            t["cols"][0]: tb["coverage"].astype(str) + "%",
            t["cols"][1]: tb["regional_amt"].map(lambda v: f"{v:,.0f}{t['won']}"),
            t["cols"][2]: tb["personal_amt"].map(lambda v: f"{v:,.0f}{t['won']}"),
            t["cols"][3]: tb["diff"].map(lambda v: f"{v:+,.0f}{t['won']}"),
            t["cols"][4]: tb["subsidy_pct"].astype(str) + "%"})
        st.dataframe(out, hide_index=True, use_container_width=True)
        st.caption(t["cap_amt"].format(a=area, p=price))

st.divider()
st.subheader(t["h4"])
sc = res["scores"]
a, b, c, dd = st.columns(4)
a.metric(t["v1"], f"{sc['baseline_5yr_avg']['rmse']:.2f}%")
b.metric(t["v2"], f"{sc[res['best_model']]['rmse']:.2f}%", f"{-res['improvement_pct_vs_baseline']:.1f}%")
c.metric(t["v3"], f"{sc['baseline_5yr_avg']['rmse_jeonnam']:.2f}%")
dd.metric(t["v4"], f"{sc[res['best_model']]['rmse_jeonnam']:.2f}%", f"{-res['improvement_pct_vs_baseline_jeonnam']:.1f}%")
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
