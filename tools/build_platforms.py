"""Platform numbers per station and direction, from Wikipedia "Station layout" tables.

Usage: python3 build_platforms.py data/delhi-metro.json data/delhi-platforms.json

Each layout row reads like "Platform 3 · Towards Noida Electronic City / Vaishali · Next Station: Ramakrishna Ashram Marg".
We keep (platform number, next station), because the next station tells us the direction of travel
regardless of how the terminal is named. Text (c) Wikipedia contributors, CC BY-SA.
"""
import json, re, sys, time, urllib.parse, urllib.request

API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "RaahiDelhiPlanner/0.3 (personal trip planner)"}
# Our station name (normalised) -> Wikipedia's article name (normalised), where they differ.
ALIAS = {
    "pul bangash": "pulbangash", "rajendra nagar": "major mohit sharma rajendra nagar", "gtb nagar": "guru tegh bahadur nagar",
    "vishwa vidyalaya": "vishwavidyalaya", "chawri bazaar": "chawri bazar", "a i i m s": "aiims", "m g road": "mg road",
    "millennium city centre": "millennium city centre gurugram", "noida golf course": "golf course", "barakhambha road": "barakhamba road",
    "surajmal stadium": "maharaja surajmal stadium", "satguru ramsingh marg": "satguru ram singh marg", "lal quila": "lal qila",
    "govind puri": "govindpuri", "tughlakabad": "tughlakabad station", "badarpur": "badarpur border", "n h p c chowk": "nhpc chowk",
    "mewala maharajpur": "mewla maharajpur", "badhkal mor": "badkhal mor", "delhi cantt": "delhi cantonment",
    "dashrath puri": "dashrathpuri", "north pitampura prashant vihar": "uttari pitampura prashant vihar", "igi airport t2 t3": "igi airport",
}

def norm(x):
    x = re.sub(r"\(.*?\)", "", x.lower()).replace("metro station", "")
    return re.sub(r"[^a-z0-9]+", " ", x).strip()

def api(params):
    url = API + "?" + urllib.parse.urlencode({"format": "json", "formatversion": 2, **params})
    time.sleep(0.5)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))

stations = [s[0] for s in json.load(open(sys.argv[1]))["stations"]]
links = [l["title"] for l in api({"action": "parse", "page": "List of Delhi Metro stations", "prop": "links"})["parse"]["links"]
         if l.get("ns") == 0 and "metro station" in l["title"].lower()]
title_by_norm = {norm(t): t for t in links}
# Any spelling we may meet in a layout table -> our station index.
lookup = {}
for i, s in enumerate(stations):
    lookup[norm(s)] = i
    if norm(s) in ALIAS:
        lookup[ALIAS[norm(s)]] = i
titles = {}
for i, s in enumerate(stations):
    t = title_by_norm.get(ALIAS.get(norm(s), norm(s)))
    if t:
        titles[t] = i

content = {}
names = list(titles)
for k in range(0, len(names), 40):
    r = api({"action": "query", "redirects": 1, "prop": "revisions", "rvprop": "content", "rvslots": "main", "titles": "|".join(names[k:k + 40])})
    back = {x["to"]: x["from"] for x in r["query"].get("redirects", [])}
    for p in r["query"]["pages"]:
        if "revisions" in p:
            content[back.get(p["title"], p["title"])] = p["revisions"][0]["slots"]["main"]["content"]

REF = re.compile(r"\{\{\s*stl\s*\|\s*Delhi Metro\s*\|\s*([^}|]+)|\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
LTL = re.compile(r"\{\{\s*ltl\s*\|\s*Delhi Metro\s*\|\s*([^}|]+)\|\s*([LR])\s*(?:\|\s*type\s*=\s*(\w+))?", re.I)
COLOUR = re.compile(r"Delhi Metro\s*\|\s*(Red|Yellow|Blue|Green|Violet|Pink|Magenta|Grey|Airport Express|Orange)", re.I)
services = json.load(open(sys.argv[1]))["lines"]
# Which terminal each side of a line's diagram means on Wikipedia (arrow "→" = R, "←" = L).
SIDES = {("yellow", "L"): ["Samaypur Badli"], ("yellow", "R"): ["Millennium City Centre"],
         ("blue", "L"): ["Dwarka Sector 21"], ("blue", "R"): ["Noida Electronic City", "Vaishali"],
         ("blue", "R", "main"): ["Noida Electronic City"], ("blue", "R", "branch"): ["Vaishali"],
         ("red", "L"): ["Rithala"], ("red", "R"): ["Shaheed Sthal"],
         ("violet", "L"): ["Kashmere Gate"], ("violet", "R"): ["Raja Nahar Singh"]}

def next_toward(i, term):
    """Neighbour of station i on the way to terminal `term` (an index), on any service that has both."""
    for L in services:
        if i in L["s"] and term in L["s"] and i != term:
            a, b = L["s"].index(i), L["s"].index(term)
            j = a + (1 if b > a else -1)
            if 0 <= j < len(L["s"]):
                return L["s"][j]
    return None

out, missing, fixed, checked = {}, [], 0, 0
for title, i in titles.items():
    text = content.get(title, "")
    hits = list(re.finditer(r"Platform\s*(\d{1,2}[A-Z]?)\b", text))
    rows = []
    for j, h in enumerate(hits):
        chunk = text[h.end(): hits[j + 1].start() if j + 1 < len(hits) else h.end() + 600]
        if re.search(r"terminates", chunk[:200], re.I):
            continue
        tw = re.search(r"Towards(.*?)(?:Next\s*Station|$)", chunk, re.I | re.S)
        towards = tw.group(1) if tw else ""
        colour = COLOUR.search(text[max(0, h.start() - 160): h.start()])
        line = (colour.group(1).lower() if colour else "")
        # 1. terminal names written in the row; 2. the line-terminus template or arrow; 3. the stated next station
        terms = [lookup.get(norm(m.group(2) or m.group(1))) for m in re.finditer(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", towards)]
        terms = [t for t in terms if t is not None and t != i]
        if not terms:
            lt = LTL.search(towards)
            side = lt.group(2).upper() if lt else ("R" if "→" in towards or "&rarr;" in towards else "L" if "←" in towards or "&larr;" in towards else None)
            key = (line, side, (lt.group(3) or "").lower()) if lt and lt.group(3) else (line, side)
            terms = [lookup.get(norm(n)) for n in SIDES.get(key, [])]
            terms = [t for t in terms if t is not None]
        derived = {next_toward(i, t) for t in terms} - {None}
        stated = None
        ns = re.search(r"Next\s*Station", chunk, re.I)
        if ns:
            m = REF.search(chunk, ns.end())
            if m:
                stated = lookup.get(norm(m.group(1) or m.group(3) or m.group(2)))
        if derived:
            checked += 1
            if stated is not None and stated not in derived:
                fixed += 1
            nexts = derived
        else:
            nexts = {stated} if stated is not None else set()
        for nx in nexts:
            if nx != i and [h.group(1), nx] not in rows:
                rows.append([h.group(1), nx])
    if rows:
        out[str(i)] = rows
    else:
        missing.append(stations[i])

json.dump(out, open(sys.argv[2], "w"), separators=(",", ":"))
print(len(out), "of", len(stations), "stations with platform numbers;", sum(len(v) for v in out.values()), "platform rows")
print(checked, "rows checked against the terminal they face;", fixed, "had a wrong 'next station' on Wikipedia and were corrected")
print("no layout found:", missing)
