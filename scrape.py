import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://ticketing.thewave.com/b2c/ticketSale/eventsCalendar"

OUT_JSON = Path("sessions.json")
DEBUG_LOG = Path("debug.log")
DEBUG_PNG = Path("debug.png")

def log(line: str):
    DEBUG_LOG.write_text((DEBUG_LOG.read_text() if DEBUG_LOG.exists() else "") + line + "\n", encoding="utf-8")

def try_extract_events(obj):
    """
    Returns list of event dicts if obj looks like {"events":[...]} (possibly nested),
    else None.
    """
    if isinstance(obj, dict):
        if "events" in obj and isinstance(obj["events"], list):
            return obj["events"]
        # search nested dict/list
        for v in obj.values():
            got = try_extract_events(v)
            if got is not None:
                return got
    if isinstance(obj, list):
        for v in obj:
            got = try_extract_events(v)
            if got is not None:
                return got
    return None

def normalize(events):
    sessions = []
    seen = set()
    for e in events:
        if not isinstance(e, dict):
            continue
        item = {
            "date": e.get("date"),
            "time": e.get("time"),
            "type": e.get("eventName") or e.get("name") or e.get("title"),
            "left": e.get("leftCapacity"),
            "right": e.get("rightCapacity"),
            "total": e.get("capacity"),
            "price": e.get("price"),
            "bookingUrl": e.get("eventUrl") or e.get("url"),
        }
        key = (item["date"], item["time"], item["type"], item["bookingUrl"])
        if key in seen:
            continue
        seen.add(key)
        sessions.append(item)

    sessions.sort(key=lambda s: (s.get("date") or "", s.get("time") or "", s.get("type") or ""))
    return sessions

def scrape():
    DEBUG_LOG.write_text("", encoding="utf-8")

    captured_events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def on_response(resp):
            ct = (resp.headers.get("content-type") or "").lower()
            url = resp.url
            # log every response that might matter
            if any(x in url.lower() for x in ["event", "calendar", "getevents", "ticketsale"]):
                log(f"RESP {resp.status} {ct} {url}")

            # only attempt JSON-ish responses
            if "application/json" not in ct and "json" not in ct:
                return

            try:
                data = resp.json()
            except Exception:
                # sometimes JSON comes as text
                try:
                    txt = resp.text()
                    # very light heuristic: look for "events":[
                    if "\"events\"" in txt:
                        data = json.loads(txt)
                    else:
                        return
                except Exception:
                    return

            events = try_extract_events(data)
            if events:
                log(f"FOUND events list: {len(events)} items from {url}")
                captured_events.extend(events)

        page.on("response", on_response)

        log("Navigating...")
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)  # let XHR/fetch complete
        page.screenshot(path=str(DEBUG_PNG), full_page=True)

        browser.close()

    sessions = normalize(captured_events)

    log(f"FINAL sessions extracted: {len(sessions)}")
    OUT_JSON.write_text(json.dumps(sessions, indent=2), encoding="utf-8")

if __name__ == "__main__":
    scrape()
