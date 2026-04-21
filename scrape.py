import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright
URL = "https://ticketing.thewave.com/b2c/ticketSale/eventsCalendar"
OUT = Path("sessions.json")
def scrape():
    sessions=[]; seen=set()
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True); page=b.new_page()
        def h(r):
            if 'events' not in r.url.lower(): return
            try: data=r.json()
            except: return
            for e in data.get('events', []):
                i={"date":e.get('date'),"time":e.get('time'),"type":e.get('eventName'),"left":e.get('leftCapacity'),"right":e.get('rightCapacity'),"total":e.get('capacity'),"price":e.get('price'),"bookingUrl":e.get('eventUrl')}
                k=(i['date'],i['time'],i['type'],i['bookingUrl'])
                if k not in seen: seen.add(k); sessions.append(i)
        page.on('response', h); page.goto(URL)
        time.sleep(5); b.close()
    OUT.write_text(json.dumps(sorted(sessions,key=lambda x:(x['date'],x['time'])),indent=2))
if __name__=='__main__': scrape()