import os
import serpapi

api_key = os.getenv("SERPAPI_KEY")

if not api_key:
    raise ValueError("SERPAPI_KEY is not set.")


client = serpapi.Client(api_key=api_key)

results = client.search({
    "engine": "google_flights",
    "departure_id": "DEL",
    "arrival_id": "BOM",
    "type": "2",
    "outbound_date": "2026-10-20",
    "currency": "INR",
    "hl": "en",
    "gl": "in"
})

print(results)