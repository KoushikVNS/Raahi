#!/usr/bin/env sh
# Fetch fresh network data and rebuild every generated file.
set -e
cd "$(dirname "$0")/.."
sh tools/fetch_osm.sh
python3 tools/build_metro.py build/routes.json build/entrances.json data/delhi-metro.json
python3 tools/build_platforms.py data/delhi-metro.json data/delhi-platforms.json
python3 tools/build_page.py
