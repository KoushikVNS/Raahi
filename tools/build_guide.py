"""Turn researched shop/food entries into the page's guide document (catalog/guide).

Usage: python3 build_guide.py research.json data/delhi-metro.json data/guide.json
Each entry is geocoded with OpenStreetMap Nominatim (1 request a second) and checked
against its stated nearest metro station; a point more than 3 km from that station is
rejected in favour of the next, coarser query.
"""
import json, math, re, sys, time, urllib.parse, urllib.request, datetime

KNOWN = {"clothing", "ethnic", "wholesale", "electronics_components", "audio", "mobiles", "computers", "electrical", "books",
         "street_food", "non_veg", "veg_food", "sweets", "spices_dryfruits", "jewellery", "furniture_home", "music_instruments", "cameras"}
DAYS = {"sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4, "friday": 5, "saturday": 6}

def hav(a, b, c, d):
    k = math.pi / 180
    x = math.sin((c - a) * k / 2) ** 2 + math.cos(a * k) * math.cos(c * k) * math.sin((d - b) * k / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "jsonv2", "limit": 1, "viewbox": "76.84,28.90,77.45,28.40", "bounded": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "RaahiDelhiPlanner/0.2 (personal project)"})
    time.sleep(1.1)
    try:
        r = json.load(urllib.request.urlopen(req, timeout=30))
        return (float(r[0]["lat"]), float(r[0]["lon"])) if r else None
    except Exception:
        return None

def hhmm(v):
    return v if isinstance(v, str) and re.fullmatch(r"\d\d:\d\d", v) else None

research = json.load(open(sys.argv[1]))
metro = json.load(open(sys.argv[2]))
stations = {norm(s[0]): s for s in metro["stations"]}

ALIAS = {"r k ashram marg": "ramakrishna ashram marg", "rk ashram marg": "ramakrishna ashram marg", "aiims": "a i i m s", "ina": "dilli haat ina"}

def station(name):
    n = norm(name).removesuffix(" metro station").removesuffix(" metro")
    n = ALIAS.get(n, n)
    return stations.get(n) or next((s for k, s in stations.items() if k.startswith(n) or n.startswith(k)), None) if n else None

items = []
for e in research:
    name = (e.get("name") or "").strip()
    if not name:
        continue
    st = station(e.get("nearest_metro_station") or "")
    area = e.get("area") or ""
    point = None
    for q in (f"{name}, {area}, Delhi", f"{e.get('address_or_landmark') or ''}, {area}, Delhi", f"{area}, Delhi"):
        p = geocode(q)
        if p and (not st or hav(p[0], p[1], st[1], st[2]) <= 3):
            point = p
            break
    if not point and st:
        point = (st[1], st[2])
    if not point:
        print("skip (no location):", name)
        continue
    closed = []
    for part in re.split(r"[,/&]| and ", str(e.get("closed_day") or "").lower()):
        part = part.strip()
        span = re.fullmatch(r"(\w+)\s*(?:-|–|to)\s*(\w+)", part)
        if span and span.group(1) in DAYS and span.group(2) in DAYS:
            a, b = DAYS[span.group(1)], DAYS[span.group(2)]
            closed += [d % 7 for d in range(a, b + 1 if b >= a else b + 8)]
        elif part in DAYS:
            closed.append(DAYS[part])
    if not st:
        st = min(metro["stations"], key=lambda s: hav(point[0], point[1], s[1], s[2]))
    gate = e.get("metro_gate")
    items.append({
        "id": e.get("id") or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
        "name": name, "cats": [c for c in e.get("categories") or [] if c in KNOWN], "area": area,
        "addr": e.get("address_or_landmark") or "", "buy": e.get("what_to_buy") or "",
        "price": int(e.get("price_level") or 1), "spend": e.get("typical_spend_inr") or "",
        "open": hhmm(e.get("open")), "close": hhmm(e.get("close")), "closed": closed,
        "metro": st[0] if st else (e.get("nearest_metro_station") or ""), "gate": str(gate) if gate not in (None, "") else None,
        "walk": int(e["walk_minutes_from_metro"]) if isinstance(e.get("walk_minutes_from_metro"), (int, float)) else None,
        "tip": e.get("tip") or "", "sources": (e.get("sources") or [])[:2],
        "lat": round(point[0], 5), "lng": round(point[1], 5),
    })
    print("ok:", name, items[-1]["lat"], items[-1]["lng"], "| metro:", items[-1]["metro"])

doc = {"updated": datetime.date.today().isoformat(), "items": [i for i in items if i["cats"]]}
json.dump(doc, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
print(len(doc["items"]), "entries written")
