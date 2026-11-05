"""Farmer-friendly page: big type, result first, plain words, a few inputs."""
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from product import DEFAULT_PRICE  # noqa: E402
from shared import G9, G6, G1, GOLD, LINE, FONT_CSS, EN_PROV, en, get_engine  # noqa: E402

ASSETS = os.path.join(ROOT, "assets")
st.set_page_config(page_title="ClimateCredit", page_icon=os.path.join(ASSETS, "icon.png"), layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown(FONT_CSS, unsafe_allow_html=True)
st.markdown(f"""
<style>
html {{ font-size: 20px; }}
.stApp {{ background:#F5F9F6; }}
.block-container {{ max-width: 860px; padding-top: 1.2rem; padding-bottom: 3rem; }}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"], header[data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, footer {{ display:none !important; }}
.fm-title {{ font-size:2rem; font-weight:800; color:{G9}; line-height:1.3; margin:.4rem 0 .2rem; word-break:keep-all; }}
.fm-sub {{ font-size:1.1rem; color:#3D6553; margin-bottom:1rem; word-break:keep-all; }}
.fm-h {{ font-size:1.5rem; font-weight:800; color:{G9}; margin:1.6rem 0 .6rem; display:flex; align-items:center; gap:.6rem; word-break:keep-all; }}
.fm-h i {{ font-style:normal; background:{G6}; color:#fff; border-radius:50%; width:2.1rem; height:2.1rem; display:inline-flex; align-items:center; justify-content:center; font-size:1.1rem; flex:none; }}
.fm-verdict {{ border-radius:18px; padding:1rem 1.2rem; margin:.4rem 0 .8rem; border-left:10px solid {G6}; background:#fff; border-top:1px solid {LINE}; border-right:1px solid {LINE}; border-bottom:1px solid {LINE}; word-break:keep-all; }}
.fm-verdict.y {{ border-left-color:{GOLD}; background:#FFF8E5; }}
.fm-verdict.r {{ border-left-color:#D73027; background:#FDECEA; }}
.fm-verdict b {{ display:block; font-size:1.45rem; color:{G9}; line-height:1.35; }}
.fm-verdict span {{ display:block; font-size:1.1rem; color:#2F5A49; margin-top:.3rem; line-height:1.5; }}
.fm-big {{ background:linear-gradient(180deg,#fff 0%,{G1} 100%); border:3px solid {G6}; border-radius:20px; padding:1.1rem 1.3rem; margin:.4rem 0 1rem; }}
.fm-big .k {{ font-size:1.05rem; font-weight:700; color:#3D6553; }}
.fm-big .v {{ font-size:clamp(2rem, 9vw, 2.8rem); font-weight:800; color:{G9}; line-height:1.25; }}
.fm-big .d {{ display:inline-block; background:#DDF3E6; color:#13724A; border-radius:999px; padding:.15rem .9rem; font-size:1.15rem; font-weight:800; margin-top:.2rem; }}
.fm-big .d.n {{ background:#EEF2EF; color:#3D6553; }}
.fm-big .s {{ font-size:1rem; color:#3D6553; margin-top:.5rem; line-height:1.5; word-break:keep-all; }}
.fm-yield {{ display:flex; flex-wrap:wrap; gap:.6rem; margin-bottom:.4rem; }}
.fm-yield div {{ flex:1 1 11rem; background:#fff; border:1px solid {LINE}; border-radius:14px; padding:.7rem 1rem; }}
.fm-yield small {{ display:block; font-size:.9rem; color:#5B7A6B; font-weight:600; }}
.fm-yield b {{ font-size:1.6rem; color:{G9}; }}
.fm-yr {{ display:grid; grid-template-columns:4.2rem 1fr; gap:.2rem .7rem; align-items:center; background:#fff; border:1px solid {LINE}; border-radius:14px; padding:.55rem .9rem; margin-bottom:.45rem; }}
.fm-yr.hit {{ border-color:{GOLD}; background:#FFFBEF; }}
.fm-yr .y {{ font-weight:800; font-size:1.05rem; color:{G9}; }}
.fm-yr .bar {{ height:1.5rem; background:#EEF2EF; border-radius:8px; overflow:hidden; display:flex; }}
.fm-yr .bar i {{ display:block; height:100%; }}
.fm-yr .t {{ grid-column:2; font-size:.98rem; color:#2F5A49; line-height:1.4; word-break:keep-all; }}
.fm-pr {{ background:#fff; border:2px solid {GOLD}; border-radius:18px; padding:1rem 1.2rem; margin-bottom:.6rem; }}
.fm-pr .row {{ margin-bottom:.55rem; }}
.fm-pr .row span {{ display:block; font-size:1.02rem; font-weight:700; color:#2F5A49; margin-bottom:.2rem; }}
.fm-pr .b {{ border-radius:10px; padding:.5rem .9rem; font-size:1.3rem; font-weight:800; color:#fff; }}
.fm-pr .b.a {{ background:{G6}; }}
.fm-pr .b.p {{ background:{GOLD}; color:{G9}; }}
.fm-pr .eq {{ font-size:1.25rem; font-weight:800; color:{G9}; margin:.8rem 0 .4rem; line-height:1.4; word-break:keep-all; }}
.fm-pr ul {{ margin:.2rem 0 .6rem 1.1rem; padding:0; }}
.fm-pr li {{ font-size:1.02rem; color:#2F5A49; line-height:1.55; margin-bottom:.3rem; word-break:keep-all; }}
.fm-pr .w {{ font-size:.92rem; color:#6F8A7B; line-height:1.5; }}
.fm-step {{ display:flex; gap:.9rem; background:#fff; border:1px solid {LINE}; border-radius:16px; padding:.9rem 1.1rem; margin-bottom:.55rem; align-items:flex-start; }}
.fm-step .n {{ flex:none; background:{G6}; color:#fff; width:2.3rem; height:2.3rem; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.2rem; }}
.fm-step b {{ display:block; font-size:1.2rem; color:{G9}; line-height:1.35; }}
.fm-step span {{ display:block; font-size:1.02rem; color:#2F5A49; line-height:1.55; margin-top:.15rem; word-break:keep-all; }}
.fm-note {{ background:#FFF8E5; border-left:8px solid {GOLD}; border-radius:12px; padding:.8rem 1.1rem; font-size:1.02rem; line-height:1.55; color:{G9}; margin:1.2rem 0 .6rem; word-break:keep-all; }}
.fm-tbl {{ width:100%; border-collapse:separate; border-spacing:0; background:#fff; border:1px solid {LINE}; border-radius:12px; overflow:hidden; }}
.fm-tbl th {{ background:{G9}; color:#fff; padding:.55rem .6rem; font-size:.95rem; text-align:right; }}
.fm-tbl td {{ padding:.6rem; text-align:right; border-top:1px solid {LINE}; font-size:1.02rem; color:{G9}; white-space:nowrap; }}
.fm-tbl th:first-child, .fm-tbl td:first-child {{ text-align:left; font-weight:800; }}
.fm-tbl tr.r80 td {{ background:{G1}; font-weight:800; }}
div[data-baseweb="select"] > div {{ min-height:3.1rem; font-size:1.05rem; }}
.stSelectbox label p, .stNumberInput label p, .stRadio label p, .stCheckbox label p {{ font-size:1.05rem !important; font-weight:700; }}
.stNumberInput input {{ font-size:1.1rem; min-height:3.1rem; }}
[data-testid="stExpander"] summary p {{ font-size:1.1rem; font-weight:700; }}
a[data-testid="stPageLink-NavLink"] p {{ font-size:1rem; font-weight:700; }}
</style>
""", unsafe_allow_html=True)

TXT = {
    "ko": dict(
        title="내 논 보험 가입금액, 얼마일까요?", sub="논 위치와 모내기한 날만 고르면 알려 드려요.",
        back="← 전문가용 자세한 화면", prov="도·광역시", county="시·군", month="모내기한 달", day="모내기한 날",
        pyeong="논 넓이 (평)", year="어느 해 가입으로 볼까요?", years=["2025년 가입 (예시)", "올해 2026년 가입"],
        month_fmt="{m}월", h_res="내 가입금액", h_why="왜 이 금액인가요?", h_next="이제 무엇을 하면 되나요?", prem_h="보험료가 올라가도 손해가 아니에요",
        prem_a="받을 수 있는 보장 (가입금액)", prem_b="내가 내는 보험료", prem_about="안팎",
        prem_eq="같은 비율로 늘어요. 많이 내고 적게 받는 게 아니에요.",
        prem_pts=["보험료는 가입금액에 비례해요 (보험료율이 같다면).", "흉년 때문에 낮아졌던 보장을 되찾는 거예요. 내 논의 평소 수확량에 더 가깝게 보장돼요.", "보험료의 {s}%는 정부(국비)가 대신 내 줘요 (80% 보장 기준)."],
        prem_warn="정확한 보험료는 보험사가 알려 줘요. 이 화면은 보험료를 계산하지 않아요.", h_year="올해(2026년) 가입하면 어떨까요?",
        v_adj=("날씨 영향을 반영하면 가입금액이 더 높아져요", "상담할 때 이 기준으로 계산해 달라고 말씀해 보세요."),
        v_same=("지금 방식 그대로 가입하셔도 돼요", "최근 5년 중 날씨 피해가 컸던 해가 없어서 금액이 같아요."),
        v_fb=("서류로 확인할 것이 더 있어요", "확인된 항목이 {n}/6개라서, 지금은 기존 방식(5년 평균)으로 계산했어요."),
        big_k="{cov}% 보장 기준 가입금액 · 논 {py:,.0f}평", big_up="기존 방식보다 {d:,.0f}원 더 높아요", big_same="기존 방식과 같은 금액이에요",
        big_s="기존 방식(5년 평균) 가입금액: {r:,.0f}원", won="원",
        y_old="평소 수확량 (기존 방식)", y_new="평소 수확량 (날씨 영향 반영)", y_unit="kg · 10a(약 300평)당",
        why_lead="최근 5년 수확량으로 '평소 수확량'을 정해요. 날씨가 나빴던 해가 끼면 평소 수확량이 낮아져요.",
        why_hit="날씨가 나빴던 해예요 → 평년 날씨였다면 {n:.0f}kg으로 계산해요", why_ok="평소 수준이에요",
        year_fmt="{y}년", kg="{v:.0f}kg", legend_a="실제 수확량", legend_b="더해서 계산한 부분",
        s_adj=[("보험 가입 상담 때 이 화면을 보여 주세요", "\"날씨 영향을 반영한 평소 수확량({a:.0f}kg)으로 가입금액을 계산해 주세요\"라고 말씀해 보세요."),
               ("모내기한 날짜와 논 위치를 확인할 자료를 챙기세요", "날짜가 바뀌면 결과가 달라져요. 기록으로 확인되는 날짜를 정확히 말씀해 주세요."),
               ("최종 금액은 보험사가 정해요", "이 화면은 참고용이에요. 보험사 확인을 거쳐 최종 금액이 정해져요.")],
        s_same=[("지금 하시던 방식으로 가입하셔도 돼요", "최근 5년에 날씨 피해가 큰 해가 없어서, 계산해도 금액이 같아요."),
                ("모내기한 날짜와 논 위치는 정확히 알아 두세요", "나중에 날씨 영향을 반영할 때 필요해요."),
                ("최종 금액은 보험사가 정해요", "이 화면은 참고용이에요.")],
        s_fb=[("서류로 확인되는 항목을 더 체크해 보세요", "아래 '내 정보 확인'에서 확인 안 된 항목: {miss}. 4개 이상 확인되면 날씨 영향이 반영돼요."),
              ("가입 서류와 기록을 챙겨 두세요", "모내기한 날짜, 논 위치, 재배 방식, 과거 피해 기록 등 서류로 확인되는 것이 많을수록 정확해요."),
              ("최종 금액은 보험사가 정해요", "이 화면은 참고용이에요.")],
        check_t="내 정보 확인 (서류로 확인되는 것에 체크)", items=["품종", "모내기한 날", "물 관리(관개·배수)", "논 위치", "재배 방식", "과거 피해"],
        check_note="체크한 항목이 4개 미만이면 날씨 영향을 반영하지 않고 기존 방식으로 계산해요.",
        y26_adj="올해 가입 기준(2021~2025년)으로는 평소 수확량이 {b:.0f}kg → {a:.0f}kg로 올라가요. 80% 보장 가입금액 {amt:,.0f}원.",
        y26_same="올해 가입 기준(2021~2025년)에는 날씨 피해가 큰 해가 없어서 기존 방식과 같아요. 80% 보장 가입금액 {amt:,.0f}원.",
        y26_ft="올해 날씨는 예측하지 않아요. 평소 수확량은 가입 직전 5년 기록으로 정해져요.",
        tbl_t="보장수준별 금액 자세히 보기", tbl_cols=["보장", "기존 방식", "날씨 반영", "차이", "국비 지원"],
        note="이 금액은 가입 기준 금액이에요. 사고가 났을 때 받는 돈이 아니고, 최종 금액은 보험사가 확인한 뒤 정해져요. 지금은 시연용 프로토타입이에요. (가격 {p:,}원/kg은 팀 가정)",
        missing="이 시군은 최근 5년 기록이 부족해서 계산하지 못했어요.", lang="언어 / Language",
    ),
    "en": dict(
        title="How much is my rice insurance amount?", sub="Pick your field's location and transplanting date. We do the rest.",
        back="← Detailed expert view", prov="Province", county="City / county", month="Transplanting month", day="Transplanting day",
        pyeong="Paddy size (pyeong)", year="Which enrollment year?", years=["2025 enrollment (example)", "This year, 2026"],
        month_fmt="{m}", h_res="Your insured amount", h_why="Why this amount?", h_next="What should you do now?", prem_h="A higher premium is not a loss",
        prem_a="Cover you can claim (insured amount)", prem_b="Premium you pay", prem_about="or so",
        prem_eq="They rise by the same share. You are not paying more to get less.",
        prem_pts=["The premium is proportional to the insured amount (at the same premium rate).", "You get back cover that a bad year had pushed down, so it matches what your field normally yields.", "The government pays {s}% of the premium (at 80% coverage)."],
        prem_warn="The insurer gives the exact premium. This screen does not calculate premiums.", h_year="What if you enroll this year (2026)?",
        v_adj=("Counting the weather's effect raises your insured amount", "At your consultation, ask them to calculate on this basis."),
        v_same=("You can keep enrolling the usual way", "No year in the last 5 had large weather damage, so the amount is the same."),
        v_fb=("More items need to be checked against records", "Only {n}/6 items are verified, so the current method (5-year average) was used."),
        big_k="Insured amount at {cov}% coverage · {py:,.0f} pyeong", big_up="{d:,.0f} KRW higher than the current method", big_same="Same as the current method",
        big_s="Current method (5-year average): {r:,.0f} KRW", won=" KRW",
        y_old="Normal yield (current method)", y_new="Normal yield (weather counted)", y_unit="kg per 10 ares (about 300 pyeong)",
        why_lead="Your 'normal yield' is set from the last 5 years. One bad-weather year pulls it down.",
        why_hit="Bad-weather year → counted as {n:.0f} kg, what normal weather would give", why_ok="A normal year",
        year_fmt="{y}", kg="{v:.0f} kg", legend_a="Actual yield", legend_b="Added back",
        s_adj=[("Show this screen at your insurance consultation", "Ask them to calculate the insured amount on the weather-adjusted normal yield ({a:.0f} kg)."),
               ("Bring proof of your transplanting date and field location", "The result changes with the date. Give the date you can show in records."),
               ("The insurer sets the final amount", "This screen is a guide. The final amount is set after the insurer checks.")],
        s_same=[("You can enroll the usual way", "No large weather damage in the last 5 years, so the amount is the same."),
                ("Keep your transplanting date and field location on record", "They matter when weather is counted later."),
                ("The insurer sets the final amount", "This screen is a guide.")],
        s_fb=[("Verify more items against records", "Not verified yet: {miss}. With 4 or more verified, the weather effect is counted."),
              ("Gather your enrollment papers and records", "Transplanting date, field location, method and past damage records. The more you can show, the better."),
              ("The insurer sets the final amount", "This screen is a guide.")],
        check_t="Check my information (tick what records can confirm)", items=["Variety", "Transplant date", "Irrigation", "Field location", "Method", "Past damage"],
        check_note="With fewer than 4 ticked, the weather is not counted and the current method is used.",
        y26_adj="For enrollment this year (using 2021-2025), the normal yield goes {b:.0f} → {a:.0f} kg. Insured amount at 80%: {amt:,.0f} KRW.",
        y26_same="For enrollment this year (using 2021-2025) no year had large weather damage, so it equals the current method. Insured amount at 80%: {amt:,.0f} KRW.",
        y26_ft="We do not forecast this year's weather. The normal yield comes from the 5 years before enrollment.",
        tbl_t="See amounts by coverage level", tbl_cols=["Coverage", "Current", "Weather counted", "Difference", "Govt. share"],
        note="This is the basis of cover, not money paid after a loss. The insurer sets the final amount after checking. This is a demo prototype. (Price {p:,} KRW/kg is a team assumption)",
        missing="Not enough yield history for this county to calculate.", lang="Language",
    ),
}

qp = st.query_params.get("lang")
default = qp or st.session_state.get("_lang", "ko")
top1, top2 = st.columns([3, 2])
with top1:
    st.image(os.path.join(ASSETS, "logo.png"), width=230)
with top2:
    label = st.radio("언어 / Language", ["한국어", "English"], index=1 if default == "en" else 0, horizontal=True, key="farmer_lang")
L = "en" if label == "English" else "ko"
st.session_state["_lang"] = L
t = TXT[L]
disp = en if L == "en" else (lambda c: c)
disp_prov = (lambda p: EN_PROV.get(p, p)) if L == "en" else (lambda p: p)

try:
    st.page_link("app.py", label=t["back"])
except Exception:
    st.markdown(f"<a href='/' target='_self' style='font-weight:700'>{t['back']}</a>", unsafe_allow_html=True)
st.markdown(f"<div class='fm-title'>{t['title']}</div><div class='fm-sub'>{t['sub']}</div>", unsafe_allow_html=True)

eng = get_engine()
skip = {"전라남도", "광주광역시", "울산광역시", "인천광역시", "제주도"}
provs = ["전라남도"] + sorted({p for (p, _) in eng.cmap if p not in skip})
c1, c2 = st.columns(2)
prov = c1.selectbox(t["prov"], provs, index=0, format_func=disp_prov)
cl = eng.counties(prov)
county = c2.selectbox(t["county"], cl, index=cl.index("영광군") if "영광군" in cl else 0, format_func=disp, key=f"fcounty_{prov}")
c3, c4 = st.columns(2)
t_month = c3.selectbox(t["month"], [5, 6], index=1, format_func=lambda m: t["month_fmt"].format(m=m if L == "ko" else ["", "", "", "", "", "May", "Jun"][m]))
t_day = c4.selectbox(t["day"], list(range(1, 32 if t_month == 5 else 31)), index=0)
pyeong = st.number_input(t["pyeong"], 100, 100000, 3025, 100)
ychoice = st.radio(t["year"], t["years"], index=0, horizontal=True)
target_year = 2025 if ychoice == t["years"][0] else 2026

# checklist (below the result in the page, but read here so the result can use it)
res_box = st.container()
with st.expander(t["check_t"], expanded=False):
    verified = [st.checkbox(lab, value=True, key=f"fv{i}") for i, lab in enumerate(t["items"])]
    st.caption(t["check_note"])
n_ok = sum(verified)

area_ha = pyeong * 400 / 121 / 10000        # 1 pyeong = 400/121 m2
md = (t_month, t_day)
q = eng.quote(prov, county, target_year, md, n_ok, 6, area_ha, DEFAULT_PRICE)

with res_box:
    if "regional_base" not in q:
        st.markdown(f"<div class='fm-verdict y'><b>{t['missing']}</b></div>", unsafe_allow_html=True)
    else:
        tb = q["table"]
        r80 = next((r for r in tb if int(r["coverage"]) == 80), tb[len(tb) // 2])
        up = q["uplift_pct"]
        adj = q["regional_base"] if q["fallback"] else q["adjusted_base"]
        if q["fallback"]:
            kind, (vt, vs) = "r", t["v_fb"]
            vs = vs.format(n=n_ok)
        elif up > 0.05:
            kind, (vt, vs) = "", t["v_adj"]
        else:
            kind, (vt, vs) = "y", t["v_same"]
        d80 = float(r80["diff"])
        st.markdown(f"<div class='fm-h'><i>1</i>{t['h_res']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fm-verdict {kind}'><b>{vt}</b><span>{vs}</span></div>", unsafe_allow_html=True)
        delta = (f"<span class='d'>{t['big_up'].format(d=d80)}</span>" if d80 > 0.5 else f"<span class='d n'>{t['big_same']}</span>")
        st.markdown(f"<div class='fm-big'><div class='k'>{t['big_k'].format(cov=int(r80['coverage']), py=pyeong)}</div>"
                    f"<div class='v'>{r80['personal_amt']:,.0f}{t['won']}</div>{delta}"
                    f"<div class='s'>{t['big_s'].format(r=r80['regional_amt'])}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fm-yield'><div><small>{t['y_old']}</small><b>{q['regional_base']:.0f}</b> <small style='display:inline'>{t['y_unit']}</small></div>"
                    f"<div><small>{t['y_new']}</small><b>{adj:.0f}</b> <small style='display:inline'>{t['y_unit']}</small></div></div>", unsafe_allow_html=True)

        # ---- why ----
        st.markdown(f"<div class='fm-h'><i>2</i>{t['h_why']}</div><div class='fm-sub'>{t['why_lead']}</div>", unsafe_allow_html=True)
        yrs, act, nor = q["years"], q["actual"], q["normal"]
        mx = max(max(act), max(nor)) * 1.02
        rep_years = set(q["replaced_years"]) if not q["fallback"] else set()
        rows = ""
        for i, y in enumerate(yrs):
            hit = y in rep_years
            a_w = act[i] / mx * 100
            add_w = max(nor[i] - act[i], 0) / mx * 100 if hit else 0
            bar = f"<i style='width:{a_w:.1f}%;background:#8FB9A2'></i>" + (f"<i style='width:{add_w:.1f}%;background:{GOLD}'></i>" if hit else "")
            txt = (t["why_hit"].format(n=nor[i]) if hit else t["why_ok"])
            rows += (f"<div class='fm-yr {'hit' if hit else ''}'><span class='y'>{t['year_fmt'].format(y=y)}</span><div class='bar'>{bar}</div>"
                     f"<div class='t'><b>{t['kg'].format(v=act[i])}</b> · {txt}</div></div>")
        st.markdown(rows, unsafe_allow_html=True)

        # ---- why a higher premium is not a loss (only when the amount goes up) ----
        shows_prem = (not q["fallback"]) and up > 0.05
        nxt_no = 3
        if shows_prem:
            nxt_no = 4
            sub80 = int(r80["subsidy_pct"])
            pts = "".join(f"<li>{pt.format(s=sub80)}</li>" for pt in t["prem_pts"])
            st.markdown(f"<div class='fm-h'><i>3</i>{t['prem_h']}</div>"
                        f"<div class='fm-pr'><div class='row'><span>{t['prem_a']}</span><div class='b a'>+{up:.1f}%</div></div>"
                        f"<div class='row'><span>{t['prem_b']}</span><div class='b p'>+{up:.1f}% {t['prem_about']}</div></div>"
                        f"<div class='eq'>{t['prem_eq']}</div><ul>{pts}</ul><div class='w'>{t['prem_warn']}</div></div>", unsafe_allow_html=True)

        # ---- next ----
        st.markdown(f"<div class='fm-h'><i>{nxt_no}</i>{t['h_next']}</div>", unsafe_allow_html=True)
        miss = ", ".join(lab for lab, ok in zip(t["items"], verified) if not ok)
        steps = t["s_fb"] if q["fallback"] else (t["s_adj"] if up > 0.05 else t["s_same"])
        html = ""
        for k, (hd, bd) in enumerate(steps, 1):
            html += f"<div class='fm-step'><div class='n'>{k}</div><div><b>{hd}</b><span>{bd.format(a=adj, miss=miss)}</span></div></div>"
        st.markdown(html, unsafe_allow_html=True)

        # ---- this year ----
        if target_year != 2026:
            q26 = eng.quote(prov, county, 2026, md, n_ok, 6, area_ha, DEFAULT_PRICE)
            if "regional_base" in q26:
                r26 = next((r for r in q26["table"] if int(r["coverage"]) == 80), q26["table"][len(q26["table"]) // 2])
                has = (not q26["fallback"]) and q26["uplift_pct"] > 0.05
                msg = (t["y26_adj"] if has else t["y26_same"]).format(b=q26["regional_base"], a=q26["adjusted_base"], amt=float(r26["personal_amt"]))
                st.markdown(f"<div class='fm-h'><i>{nxt_no + 1}</i>{t['h_year']}</div>"
                            f"<div class='fm-step'><div class='n' style='background:{GOLD}'>!</div><div><b>{msg}</b><span>{t['y26_ft']}</span></div></div>",
                            unsafe_allow_html=True)

        with st.expander(t["tbl_t"], expanded=False):
            hd = "".join(f"<th>{c}</th>" for c in t["tbl_cols"])
            body = ""
            for r in tb:
                cls = " class='r80'" if int(r["coverage"]) == int(r80["coverage"]) else ""
                body += (f"<tr{cls}><td>{int(r['coverage'])}%</td><td>{r['regional_amt']:,.0f}</td><td>{r['personal_amt']:,.0f}</td>"
                         f"<td>{r['diff']:+,.0f}</td><td>{int(r['subsidy_pct'])}%</td></tr>")
            st.markdown(f"<table class='fm-tbl'><tr>{hd}</tr>{body}</table>", unsafe_allow_html=True)
st.markdown(f"<div class='fm-note'>{t['note'].format(p=DEFAULT_PRICE)}</div>", unsafe_allow_html=True)
