"""Inline the metro network into the page: python3 tools/build_page.py  ->  index.html"""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
page = (root / "src/app.html").read_text()
metro_data = json.loads((root / "data/delhi-metro.json").read_text())
plat = root / "data/delhi-platforms.json"
if plat.exists():
    metro_data["platforms"] = json.loads(plat.read_text())
metro = json.dumps(metro_data, ensure_ascii=False, separators=(",", ":"))
assert "/*METRO_JSON*/null" in page
(root / "index.html").write_text(page.replace("/*METRO_JSON*/null", metro))
print("wrote index.html", len(page) + len(metro), "bytes")
