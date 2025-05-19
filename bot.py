import os
import json
import requests
import time
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()
TP_TOKEN = os.getenv("TP_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")

# Initialize Telegram bot
bot = Bot(token=TG_TOKEN)
seen_tickets = set()

# Load cities and airports data from the data/ folder
with open("data/cities.json", encoding="utf-8") as f:
    cities_data = {
        city["code"]: city["name_translations"].get("en", city["code"])
        for city in json.load(f) if city.get("has_flightable_airport")
    }

with open("data/airports.json", encoding="utf-8") as f:
    airports_data = {
        airport["code"]: airport["name_translations"].get("en", airport["code"])
        for airport in json.load(f)
    }

# Define departure airports manually
departure_airports = ["AMS"]

async def fetch_and_notify():
    global seen_tickets
    print("🔍 fetch_and_notify started")

    all_messages = []

    for origin in departure_airports:
        params = {
            "origin": origin,
            "currency": "eur",
            "limit": 30,
            "page": 1,
            "one_way": "true",
            "market": "nl",
            "sorting": "price",
            "token": TP_TOKEN
        }

        response = requests.get("https://api.travelpayouts.com/aviasales/v3/prices_for_dates", params=params)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch data for {origin}")
            continue

        data = response.json()
        if not data.get("success", True):
            print(f"❌ API error for {origin}: {data.get('error')}")
            continue

        tickets = data.get("data", [])
        city_from = cities_data.get(origin, origin)
        airport_from = airports_data.get(origin, origin)

        print(f"✅ Retrieved {len(tickets)} tickets from {city_from} ({origin})")

        for ticket in tickets:
            price = ticket.get("price")
            if price is None or price > 100:
                continue  # 🎯 Price filter

            dest = ticket.get("destination")
            date = ticket.get("departure_at", "")[:10]
            if not dest or not date:
                continue

            city_to = cities_data.get(dest, dest)
            airport_to = airports_data.get(dest, dest)

            ticket_id = f"{origin}-{dest}-{price}-{date}"
            if ticket_id in seen_tickets:
                continue
            seen_tickets.add(ticket_id)

            ddmm = date[8:10] + date[5:7]
            link = f"https://www.aviasales.com/search/{origin}{ddmm}{dest}1"

            msg = (
                f"✈️ *{city_from}* ({airport_from}) → *{city_to}* ({airport_to})\n"
                f"Price: *€{price}*\n"
                f"Departure: {date} [Book here]({link})"
            )
            all_messages.append(msg)

    if all_messages:
        full_message = "\n\n".join(all_messages)
        try:
            await bot.send_message(chat_id=158367660, text=full_message, parse_mode="Markdown")
            print("📤 Message with tickets sent.")
        except Exception as e:
            print("❌ Failed to send message:", e)
    else:
        print("🔕 No matching tickets found.")

async def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.create_task(fetch_and_notify()), trigger="interval", hours=8)
    scheduler.start()
    print("✅ Scheduler is running. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("⛔ Bot stopped.")

if __name__ == "__main__":
    async def start():
        await bot.send_message(chat_id=158367660, text="👋 Bot started and will check for new tickets every 8 hours.")
        await fetch_and_notify()
        await main()

    asyncio.run(start())
