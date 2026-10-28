"""Build compact Delhi Metro network data from OpenStreetMap Overpass exports.

Usage: python3 build_metro.py routes.json entrances.json metro.json

routes.json  — route relations with their stop nodes:
  rel["route"="subway"]["network"~"Delhi Metro"]->.r; .r out body;
  node(r.r:"stop"); out body; node(r.r:"stop_entry_only"); out body; node(r.r:"stop_exit_only"); out body;
entrances.json — numbered station gates:
  node["railway"="subway_entrance"](28.38,76.80,28.92,77.50); out body;

Branches are written as through-running services (a Vaishali train runs on to
Dwarka Sector 21), so riders only see a change where they really change trains.
Data (c) OpenStreetMap contributors, ODbL.
"""
import json, re, sys, math

# (relation id, service id, line group, colour, flags, through-run onto service, joining station)
SERVICES = [
    (447214, "RED", "Red", "#E2231A", {}, None, None),
    (447210, "YEL", "Yellow", "#F4C300", {}, None, None),
    (447209, "BLU", "Blue", "#1A5DC8", {}, None, None),
    (2535795, "BLV", "Blue", "#1A5DC8", {"rev": True}, "BLU", "Yamuna Bank"),
    (8037666, "GRN", "Green", "#1B9E4B", {}, None, None),
    (2535796, "GRK", "Green", "#1B9E4B", {}, "GRN", "Ashok Park Main"),
    (2535797, "VIO", "Violet", "#7B3FA0", {}, None, None),
    (8241298, "PNK", "Pink", "#E5649A", {"ring": True}, None, None),
    (8385429, "MAG", "Magenta", "#B0207E", {}, None, None),
    (20300114, "MG4", "Magenta", "#B0207E", {}, None, None),
    (3537978, "GRY", "Grey", "#8A8F96", {}, None, None),
    (2535798, "AEX", "Airport Express", "#F07F13", {"ae": True}, None, None),
]
ALIAS = {
    "New Delhi Airport Express Terminal": "New Delhi",
    "IGI Airport": "IGI Airport T2/T3",
    "Millennium City Centre Gurugram": "Millennium City Centre",
}

def norm(n):
    n = re.sub(r"\s*\((?:[A-Za-z]+ Line)\)\s*$", "", n).strip()
    return ALIAS.get(n, n)

def hav(a, b, c, d):
    k = math.pi / 180
    x = math.sin((c - a) * k / 2) ** 2 + math.cos(a * k) * math.cos(c * k) * math.sin((d - b) * k / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))

d = json.load(open(sys.argv[1]))["elements"]
rels = {e["id"]: e for e in d if e["type"] == "relation"}
nodes = {e["id"]: e for e in d if e["type"] == "node"}

stations, index = [], {}
def sid(node):
    t = node["tags"]
    name = norm(t.get("name:en") or t.get("name"))
    if name not in index:
        index[name] = len(stations)
        stations.append({"n": name, "pts": [], "code": None})
    s = stations[index[name]]
    s["pts"].append((node["lat"], node["lon"]))
    if t.get("ref") and re.fullmatch(r"[A-Z0-9]{2,6}", t["ref"]) and not s["code"]:
        s["code"] = t["ref"]
    return index[name]

def stops_of(rid):
    out = []
    for m in rels[rid]["members"]:
        if m["type"] == "node" and m["role"].startswith("stop") and m["ref"] in nodes:
            s = sid(nodes[m["ref"]])
            if not out or out[-1] != s:
                out.append(s)
    return out

lines, by_id = [], {}
for rid, sid_, group, colour, flags, onto, join in SERVICES:
    stops = stops_of(rid)
    if flags.get("rev"):
        stops = stops[::-1]
    line = {"id": sid_, "g": group, "c": colour, "s": stops}
    line.update({k: v for k, v in flags.items() if k != "rev"})
    if onto:
        base = by_id[onto]["s"]
        j = index[join]
        assert stops[-1] == j, (sid_, "must end at", join)
        line["s"] = stops + base[base.index(j) + 1:]
    lines.append(line)
    by_id[sid_] = line

out_st = []
for s in stations:
    lat = sum(p[0] for p in s["pts"]) / len(s["pts"])
    lng = sum(p[1] for p in s["pts"]) / len(s["pts"])
    out_st.append([s["n"], round(lat, 5), round(lng, 5), s["code"] or ""])

# Numbered gates: skip lifts, sealed or locked gates; attach to the nearest station within 500 m.
gates = {}
for e in json.load(open(sys.argv[2]))["elements"]:
    t = e.get("tags", {})
    ref = (t.get("ref") or "").strip()
    name = (t.get("name") or t.get("description") or "").lower()
    if not re.fullmatch(r"\d{1,2}[A-Z]?", ref) or "lift" in name:
        continue
    if t.get("access") == "no" or t.get("locked") == "yes" or "sealed" in (t.get("description") or "").lower():
        continue
    i, best = min(((i, hav(e["lat"], e["lon"], s[1], s[2])) for i, s in enumerate(out_st)), key=lambda x: x[1])
    if best > 0.5:
        continue
    g = gates.setdefault(i, {})
    g.setdefault(ref, [round(e["lat"], 5), round(e["lon"], 5)])

out_gates = {str(i): [[r, *ll] for r, ll in sorted(g.items(), key=lambda kv: int(re.match(r"\d+", kv[0]).group()))] for i, g in gates.items()}
json.dump({"stations": out_st, "lines": lines, "gates": out_gates}, open(sys.argv[3], "w"), separators=(",", ":"), ensure_ascii=False)
print(len(out_st), "stations,", len(lines), "services,", len(out_gates), "stations with gates,", sum(len(v) for v in out_gates.values()), "gates")
