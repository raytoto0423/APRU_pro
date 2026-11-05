"""Pieces shared by the analysis page (app.py) and the farmer page (pages/farmer.py)."""
import streamlit as st
from product import Engine

G9, G6, G1, GOLD, LINE = "#0F3D2E", "#1F8F5A", "#E8F3EC", "#E0A526", "#D6E6DB"

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


@st.cache_resource
def get_engine():
    return Engine()


FONT_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
.stApp, .stApp *:not([data-testid="stIconMaterial"]):not([class*="material"]):not(svg):not(svg *):not(code):not(pre) {
    font-family: 'Pretendard', 'Noto Sans KR', 'Malgun Gothic', 'NanumGothic', sans-serif;
}
</style>
"""
