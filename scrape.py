import json, time
from playwright.sync_api import sync_playwright

URL = "https://ticketing.thewave.com/b2c/ticketSale/eventsCalendar"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    events = page.evaluate("""
      () => {
        for (const k of Object.keys(window)) {
          const v = window[k];
          if (v && typeof v === 'object' && Array.isArray(v.events)) {
            return v.events;
          }
        }
        return [];
      }
    """)

    browser.close()

sessions = []
for e in events:
    sessions.append({
        "date": e.get("date"),
        "time": e.get("time"),
        "type": e.get("eventName"),
        "left": e.get("leftCapacity"),
        "right": e.get("rightCapacity"),
        "total": e.get("capacity"),
        "price": e.get("price"),
        "bookingUrl": e.get("eventUrl")
    })

with open("sessions.json", "w") as f:
    json.dump(sessions, f, indent=2)
