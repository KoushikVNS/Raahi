# Raahi · राही

**A commute, trip and budget planner for New Delhi.** Search any place and compare every way to get there: Delhi Metro (with line changes, platform numbers, branch warnings and exit gates), Airport Express, DTC buses, autos, cabs, bike taxis, e-rickshaws and walking. Each option comes with time and cost. You can also see what's nearby, find the right market or eatery for what you need, plan a full day, and keep your monthly and per-trip budget in check.

It is a single static page: no backend, no build step, no API keys.

---

## Features

### Home dashboard
- **Welcome screen** with the date, a greeting and a "Where are you headed?" search.
- **Surprise me** picks a random place you haven't visited that's open now and shows the route there. There's also a one-tap button for your regular commute.
- **Budget ring:** an animated view of what's left this month, how much you can spend per day and your biggest spending category. You can log spending from here in two taps.
- **Your plan at a glance:** today's stops with a live **Now / Next** line ("Next: Jama Masjid at 12:10 · leave by 11:52"), and a tick for each stop as you visit it.
- **Ready-made days:** load a full plan in one tap (Old Delhi heritage, Mughal tombs & gardens, Lutyens' Delhi, Qutub to Hauz Khas).
- **Discover:** a carousel of random places you haven't been to yet, with travel time and fare from your starting point.
  - Filter by monuments, gardens, temples, museums, markets, food, free entry or open now, and press Shuffle for new picks.
  - Places you mark as visited, or already have in your trip, are left out.
- **Explored:** how many of the 45 sights you've visited, broken down by kind of place, with recent visits you can undo.
- **Travel tips** you can flip through: women's coach, smart-card savings, Sunday fares, branch lines and more.

### Routes for every way of getting around
- **Metro routing over the real network:** 244 stations and 12 services, including through-running branches. A Vaishali train runs on to Dwarka Sector 21, so you only see a change where you actually change trains.
- **Platform numbers with direction and next stop** at every boarding, e.g. *"Platform 3, towards Vaishali (next stop Barakhamba Road)"*. 231 of 244 stations are covered.
- **Branch warnings** where one line splits in two:
  - *Blue Line at Yamuna Bank* (Vaishali vs Noida Electronic City trains)
  - *Green Line at Ashok Park Main* (Inderlok vs Kirti Nagar trains)

  Raahi tells you which destination to look for on the train, and which platform to switch to if you board the wrong one.
- **Exit gates:** picks the numbered gate closest to where you're going (386 gates at 132 stations).
- **Fares:** DMRC fare slabs revised on 25 Aug 2025, Sunday and holiday fares, and the smart-card discount. Airport Express fares are approximated.
- **Travel times:** waits differ by line, interchanges have their own walking times, and train speeds are calibrated per line.
- **Other ways to travel:** Airport Express, DTC/cluster bus (AC and non-AC fares, free travel for women), auto-rickshaw at the meter rate, cab, bike taxi, shared e-rickshaw and walking.
- Sort options by **Best mix**, **Cheapest** or **Fastest**.

### Places
- About 45 sights with ticket prices (Indian, foreign and child), opening hours, weekly closing days, how long to plan and practical tips.
- **Nearby:** sights, markets and food within 3.5 km of anywhere.

### Shops & food by need
- 64 checked places across 18 needs. These include clothes, ethnic and wedding wear, wholesale, electronic components, speakers and audio, mobiles, laptops and PC parts, electrical goods, cameras, music instruments, books, jewellery, home and furniture, spices, street food, non-veg, veg food and sweets.
- Each place shows whether it's open now, its weekly off day, the nearest metro station and gate, and travel time and fare from where you are.

### Trip planner
- Add places, set the date, start time and number of people, and choose cheapest, best mix, fastest or cab.
- Raahi builds a timed day plan and warns about closed days and closing times. **Best order** reorders the stops to cut travel time.
- The total covers tickets, travel and food, and is checked against your trip budget. It also suggests when a metro Tourist Card would pay off.

### Budget
- Set a monthly budget and a per-trip budget.
- Saved trips are logged automatically, and you can add other spending by hand.
- The month view shows spending by category and how much you can spend per day for the rest of the month.
- A **regular commute** calculator compares the monthly cost of each way of travelling a route you take often.

### Works on phones
- Built for phones held upright: compact header, four equal tabs, 16 px form text (so iOS doesn't zoom when you tap a box), large tap targets.
- A modern, layered look: glass header that stays put, pill controls, soft depth and gradient accents. Phones get a floating tab bar.
- Light and dark themes, and gentle animations that switch off if your device is set to reduce motion.

---

## Running it

The page needs a web server, because browsers block loading `data/guide.json` from a `file://` page.

```bash
git clone https://github.com/KoushikVNS/Raahi.git
cd Raahi
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

Opening `index.html` directly mostly works too, except the Shops & food list.

### Deploying on GitHub Pages

In **Settings → Pages**, choose **Deploy from a branch**, then **main** and **/ (root)**. The site will be served at `https://<user>.github.io/Raahi/`.

### Where your data is saved

Budgets, trips and spending are saved in your browser's `localStorage`. Nothing leaves your device.

Three features only work when the page runs on a host that provides them through its runtime API:
- **Sync across devices**
- **A live, shared shop list**
- **The AI assistant**

On a plain web server these turn off by themselves: your data stays in the browser, the shop list comes from `data/guide.json`, and the assistant is hidden.

---

## Project structure

```
index.html                 Built page (open or deploy this)
src/app.html               Page source: markup, styles and the app script
data/delhi-metro.json      Stations, services (line order) and numbered gates
data/delhi-platforms.json  Platform number per station and direction (keyed by next station)
data/guide.json            Shops & food list (sources listed per entry)
tools/build_page.py        Inlines the metro data into src/app.html  →  index.html
tools/build_metro.py       Builds delhi-metro.json from OpenStreetMap exports
tools/build_platforms.py   Builds delhi-platforms.json from Wikipedia station layouts
tools/build_guide.py       Geocodes researched shop/food entries into guide.json
tools/fetch_osm.sh         Downloads the OpenStreetMap inputs into build/
tools/rebuild.sh           Fetches fresh data and rebuilds everything
```

All tools use only the Python 3 standard library.

### Editing the page

Edit `src/app.html`, then run:

```bash
python3 tools/build_page.py
```

### Refreshing the metro data

When a new line or station opens:

```bash
sh tools/rebuild.sh
```

This downloads the current network and gates from OpenStreetMap, rebuilds the platform table from Wikipedia, and rebuilds `index.html`.

### Updating the shop list

1. Edit `data/guide.json` directly, or prepare entries in the research format and run:

   ```bash
   python3 tools/build_guide.py research.json data/delhi-metro.json data/guide.json
   ```

2. Each entry needs `id`, `name`, `cats`, `lat`, `lng`. Leave hours and gate numbers as `null` unless a source confirms them; the page then shows "Hours not published" instead of guessing.

---

## How the numbers are worked out

| What | How |
|---|---|
| Metro route | Shortest time over (station, service) pairs. It includes the first wait, per-interchange walking time and the next train's wait. Speeds are 40 km/h plus 30 s dwell per stop (80 km/h on the Airport Express). |
| Metro fare | DMRC distance slabs (₹11 / 21 / 32 / 43 / 54 / 64; Sundays ₹11 / 11 / 21 / 32 / 43 / 54), using the shortest track distance between where you enter and exit. Smart card −10%. |
| Platform | Wikipedia station layout tables. Each row is checked against the terminal it says it faces, and rows that contradict it are corrected. |
| Exit gate | The open, numbered gate closest to your destination. Sealed gates and lifts are skipped. |
| Auto | Delhi meter tariff: ₹30 for the first 1.5 km, then ₹11/km. Night surcharge 25%. |
| Bus | DTC distance slabs: non-AC ₹5 / 10 / 15, AC ₹10 / 15 / 20 / 25. |
| Cab, bike taxi | Typical app pricing, shown as a range because of surge pricing. |

All prices and times are **estimates**. Check official sources before you travel; the screens at a station always have the final word on platforms.

---

## Roadmap
- More cities: Mumbai, Bengaluru and Jaipur (already listed in the city menu).
- Scheduled train times from the official GTFS feed.
- Live bus route numbers.

---

## Data sources and licences

- **Metro network, stations and gates:** © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. `data/delhi-metro.json` is a derived database and is available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).
- **Platform numbers:** derived from station articles listed in [List of Delhi Metro stations](https://en.wikipedia.org/wiki/List_of_Delhi_Metro_stations) on Wikipedia, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- **Geocoding:** [Nominatim](https://nominatim.org/) / OpenStreetMap.
- **Fares and tickets:** DMRC fare revision of 25 Aug 2025, Archaeological Survey of India ticket rates, and the Delhi Transport Department auto tariff.
- **Shops & food:** compiled from public sources, linked on each entry.
- **Fonts:** Archivo, IBM Plex Sans, IBM Plex Mono and Hind, via Google Fonts (SIL Open Font License).

## Licence

The code is released under the [MIT License](LICENSE). The data files keep the licences of their sources, listed above.

© 2026 Kaushik Chakraborty
