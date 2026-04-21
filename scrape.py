import json
from playwright.sync_api import sync_playwright

URL = "https://ticketing.thewave.com/b2c/ticketSale/eventsCalendar"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="domcontentloaded")

        # Give the calendar JS time to hydrate
        page.wait_for_timeout(5000)

        # Pull events from the page context
        events = page.evaluate("""
        () => {
          // The Wave calendar stores events on window in most builds
          const candidates = Object.values(window).filter(
            v => v && typeof v === 'object' && Array.isArray(v.events)
          );
          if (!candidates.length) return [];
          return candidates[0].events || [];
        }
        """)

        browser.close()

    sessions = []
    seen = set()

    for e in events:
        item = {
            "date": e.get("date"),
            "time": e.get("time"),
            "type": e.get("eventName"),
            "left": e.get("leftCapacity"),
            "right": e.get("rightCapacity"),
            "total": e.get("capacity"),
            "price": e.get("price"),
            "bookingUrl": e.get("eventUrl")
        }

        key = (item["date"], item["time"], item["type"], item["bookingUrl"])
        if key not in seen:
            seen.add(key)
            sessions.append(item)

    sessions.sort(key=lambda s: (s["date"], s["time"]))

    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=2)

if __name__ == "__main__":
    scrape()
