import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://ticketing.thewave.com/b2c/ticketSale/eventsCalendar"

sessions = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)

    # Screenshot proof
    page.screenshot(path="debug.png", full_page=True)

    # Try DOM scrape (safe)
    cards = page.query_selector_all("a")

    for c in cards:
        href = c.get_attribute("href")
        if href and "ticket" in href.lower():
            sessions.append({
                "bookingUrl": href
            })

    browser.close()

Path("sessions.json").write_text(json.dumps(sessions, indent=2))
