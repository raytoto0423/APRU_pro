"""County -> nearest ASOS station mapping.

Jeonnam: explicit nearest-station map (team judgement from geography).
Other provinces: matched only when a station carries the county's own name (strip 시/군/구).
"""
import re

JEONNAM = {
    "강진군": 259, "고흥군": 262, "곡성군": 247, "광양시": 266, "구례군": 174, "나주시": 156,
    "담양군": 156, "목포시": 165, "무안군": 165, "보성군": 258, "순천시": 174, "신안군": 165,
    "여수시": 168, "영광군": 252, "영암군": 165, "완도군": 170, "장성군": 156, "장흥군": 260,
    "진도군": 268, "함평군": 252, "해남군": 261, "화순군": 156,
}
# other special cases (county name differs from station name)
SPECIAL = {("광주광역시", "광산구"): 156, ("울산광역시", "울주군"): 152, ("인천광역시", "강화군"): 201}
EXCLUDE = {("경기도", "광주시")}  # collides with Gwangju metropolitan station


def _strip(name):
    return re.sub(r"(시|군|구)$", "", name)


def build_map(counties, station_names):
    """counties: iterable of (province, county); station_names: {stnId: name}. Returns {(prov, county): stnId}."""
    by_name = {}
    for sid, nm in station_names.items():
        by_name.setdefault(_strip(nm), sid)
    out = {}
    for prov, c in counties:
        if (prov, c) in EXCLUDE:
            continue
        if prov == "전라남도" and c in JEONNAM:
            out[(prov, c)] = JEONNAM[c]
        elif (prov, c) in SPECIAL:
            out[(prov, c)] = SPECIAL[(prov, c)]
        elif _strip(c) in by_name and prov != "전라남도":
            out[(prov, c)] = by_name[_strip(c)]
    return out
