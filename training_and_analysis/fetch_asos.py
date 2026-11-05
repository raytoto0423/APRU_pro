"""Download KMA ASOS daily data (growing season Apr-Oct) per station-year.

Key is read from .env (KMA_KEY=...). Output: data/asos_daily/<stnId>_<year>.csv
Most recent years first so partial runs are already usable. Resumable.
"""
import os, sys, time, json
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = [l.split("=", 1)[1].strip() for l in open(os.path.join(HERE, ".env")) if l.startswith("KMA_KEY")][0]
URL = "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
OUT = os.path.join(HERE, "data", "asos_daily")
os.makedirs(OUT, exist_ok=True)
Y_FROM = int(sys.argv[1]) if len(sys.argv) > 1 else 2010
Y_TO = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 12
KEEP = ["stnId", "stnNm", "tm", "avgTa", "minTa", "maxTa", "sumRn", "hr1MaxRn",
        "avgWs", "maxWs", "maxInsWs", "sumSsHr", "avgRhm", "sumGsr"]


def call(params, tries=4):
    for k in range(tries):
        try:
            r = requests.get(URL, params=dict(serviceKey=KEY, dataType="JSON", dataCd="ASOS",
                                              dateCd="DAY", **params), timeout=90)
            if r.status_code == 200 and r.text.startswith("{"):
                return r.json()
        except Exception:
            pass
        time.sleep(2 * (k + 1))
    return None


def items_of(js):
    try:
        it = js["response"]["body"]["items"]
        if not it:
            return []
        it = it["item"]
        return it if isinstance(it, list) else [it]
    except Exception:
        return []


def fetch(task):
    sid, year = task
    path = os.path.join(OUT, f"{sid}_{year}.csv")
    if os.path.exists(path):
        return task, -1
    js = call(dict(pageNo=1, numOfRows=300, startDt=f"{year}0401", endDt=f"{year}1031", stnIds=str(sid)))
    if js is None:
        return task, None  # failure, will be retried on next run
    its = items_of(js)
    df = pd.DataFrame(its)
    for c in KEEP:
        if c not in df.columns:
            df[c] = ""
    df[KEEP].to_csv(path, index=False, encoding="utf-8-sig")  # empty file = station had no data that year
    return task, len(its)


if __name__ == "__main__":
    stations = json.load(open(os.path.join(OUT, "_stations.json")))
    tasks = [(s, y) for y in range(Y_TO, Y_FROM - 1, -1) for s in stations]
    print("tasks:", len(tasks), flush=True)
    done = fails = 0
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        for task, n in ex.map(fetch, tasks):
            done += 1
            if n is None:
                fails += 1
            if done % 20 == 0 or n is None:
                print(f"[{done}/{len(tasks)}] fails={fails} elapsed={int(time.time()-t0)}s last={task} n={n}", flush=True)
    print("DONE fails=", fails, flush=True)
