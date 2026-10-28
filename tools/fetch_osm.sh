#!/usr/bin/env sh
# Download the OpenStreetMap inputs that build_metro.py needs into build/.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
UA="RaahiDelhiPlanner (https://github.com/KoushikVNS/Raahi)"
API="https://overpass-api.de/api/interpreter"

echo "Fetching metro routes and stops..."
curl -sS -m 180 -A "$UA" -X POST "$API" --data-urlencode 'data=[out:json][timeout:160];rel["route"="subway"]["network"~"Delhi Metro"]->.r;.r out body;node(r.r:"stop");out body;node(r.r:"stop_entry_only");out body;node(r.r:"stop_exit_only");out body;' -o build/routes.json

echo "Fetching station entrances..."
curl -sS -m 150 -A "$UA" -X POST "$API" --data-urlencode 'data=[out:json][timeout:110];node["railway"="subway_entrance"](28.38,76.80,28.92,77.50);out body;' -o build/entrances.json

echo "Saved build/routes.json and build/entrances.json"
