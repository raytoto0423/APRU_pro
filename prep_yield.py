"""KOSIS county paddy-rice file -> long table (province, county, year, area_ha, yield_kg_10a)."""
import glob, os, re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROV_PAT = re.compile(r"(도|광역시|특별시|특별자치시|특별자치도)$")


def load_yield():
    path = sorted(glob.glob(os.path.join(HERE, "data", "101_DT_1ET0034_*.csv")))[-1]
    df = pd.read_csv(path, encoding="cp949")
    yr_cols = [c for c in df.columns if "년" in c]
    rows, province = [], None
    for _, r in df.iterrows():
        name = r["행정구역별"]
        if name == "전국":
            province = "전국"
        elif PROV_PAT.search(name) and name not in ("강화군",):
            province = name
        item = r["항목"]
        key = "area_ha" if "재배면적" in item else ("yield" if "10a" in item else "prod_t")
        for c in yr_cols:
            rows.append((province, name, int(c.split()[0]), key, r[c]))
    long = pd.DataFrame(rows, columns=["province", "region", "year", "k", "v"])
    wide = long.pivot_table(index=["province", "region", "year"], columns="k", values="v", aggfunc="first").reset_index()
    wide = wide[~wide["region"].eq("전국")]
    is_prov = wide["region"].apply(lambda s: bool(PROV_PAT.search(s)) and s != "강화군")
    counties = wide[~is_prov & wide["yield"].notna()].copy()
    counties = counties.rename(columns={"region": "county", "yield": "yield_kg10a"})
    return counties[["province", "county", "year", "area_ha", "yield_kg10a"]]


if __name__ == "__main__":
    d = load_yield()
    print(d.shape, d.year.min(), d.year.max(), d.county.nunique())
    print(d[d.province == "전라남도"].county.unique())
