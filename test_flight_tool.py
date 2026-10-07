from flight_tools import search_flights


result = search_flights.invoke({
    "origin": "DEL",
    "destination": "BOM",
    "date": "2026-10-20"
})

print(result)