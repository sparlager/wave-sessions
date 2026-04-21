import json
import time
from playwright.sync_api import sync_playwright

URL = "https://ticketing.thewave.com/b2c/ticketSale/eventsCalendar"

def scrape():
    sessions = []
    seen = set()
    found_events = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            nonlocal found_events
            if "getEvents" not in response.url:
                return
            try:
                data = response.json()
            except:
                return

            events = data.get("events", [])
            if not events:
                return

            found_events = True

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

        page.on("response", handle_response)

        page.goto(URL)

        # IMPORTANT: wait up to 20s for getEvents to appear
        for _ in range(40):
            if found_events:
                break
            page.wait_for_timeout(500)

        browser.close()

    if not sessions:
        print("WARNING: No sessions found")

    sessions.sort(key=lambda s: (s["date"], s["time"], s["type"]))

    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=2)

if __name__ == "__main__":
    scrape()
