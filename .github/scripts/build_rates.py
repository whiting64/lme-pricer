!/usr/bin/env python3
"""Fetch the latest US Treasury par yield curve (CMT) and write rates.json.
Source: home.treasury.gov daily interest-rate XML feed (free, no key).
Run by GitHub Actions on a schedule; commits rates.json to the repo so the
static page can read it same-origin (no CORS, no secrets)."""
import urllib.request, xml.etree.ElementTree as ET, json, datetime, sys

ATOM = "{http://www.w3.org/2005/Atom}"
M    = "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}"
D    = "{http://schemas.microsoft.com/ado/2007/08/dataservices}"

# CMT tenor element -> maturity in years
TENORS = [
    ("BC_1MONTH",   1/12),
    ("BC_1_5MONTH", 1.5/12),
    ("BC_2MONTH",   2/12),
    ("BC_3MONTH",   3/12),
    ("BC_4MONTH",   4/12),
    ("BC_6MONTH",   6/12),
    ("BC_1YEAR",    1.0),
    ("BC_2YEAR",    2.0),
    ("BC_3YEAR",    3.0),
]

BASE = ("https://home.treasury.gov/resource-center/data-chart-center/"
        "interest-rates/pages/xml?data=daily_treasury_yield_curve"
        "&field_tdr_date_value=%d")

def fetch(year):
    req = urllib.request.Request(BASE % year, headers={"User-Agent": "lme-pricer-rates/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def entries(year):
    root = ET.fromstring(fetch(year))
    return root.findall(ATOM + "entry")

def props(e):
    return e.find(ATOM + "content/" + M + "properties")

def text(p, tag):
    el = p.find(D + tag)
    return el.text if el is not None else None

def main():
    y = datetime.date.today().year
    es = entries(y) or entries(y - 1)
    if not es:
        sys.exit("no entries returned from Treasury feed")

    latest, latest_date = None, ""
    for e in es:
        p = props(e)
        d = (text(p, "NEW_DATE") or "")[:10]
        if d > latest_date:
            latest_date, latest = d, p

    curve = []
    for tag, t in TENORS:
        v = text(latest, tag)
        if v not in (None, ""):
            try:
                curve.append({"t": round(t, 4), "r": float(v)})
            except ValueError:
                pass

    if not curve:
        sys.exit("no curve points parsed")

    out = {"asof": latest_date, "curve": curve}
    with open("rates.json", "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(json.dumps(out))

if __name__ == "__main__":
    main()
