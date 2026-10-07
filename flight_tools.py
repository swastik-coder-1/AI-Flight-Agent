import os
import json
import serpapi

from langchain_core.tools import tool


# ============================================================
# SESSION STATE
# ============================================================

class FlightSession:
    def __init__(self):
        self.last_search_results = []
        self.selected_flight = None
        self.passenger_name = None
        self.booking_confirmed = False
        self.booking_reference = None


# ============================================================
# SERPAPI CLIENT
# ============================================================

def get_serpapi_client():
    api_key = os.getenv("SERPAPI_KEY")

    if not api_key:
        raise ValueError("SERPAPI_KEY is not set.")

    return serpapi.Client(api_key=api_key)


# ============================================================
# CREATE TOOLS FOR ONE USER SESSION
# ============================================================

def create_flight_tools(session: FlightSession):

    # --------------------------------------------------------
    # SEARCH FLIGHTS
    # --------------------------------------------------------

    @tool
    def search_flights(
        origin: str,
        destination: str,
        date: str
    ) -> str:
        """
        Search real flight options using Google Flights
        through SerpApi.
        """

        client = get_serpapi_client()

        results = client.search({
            "engine": "google_flights",
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "type": "2",
            "outbound_date": date,
            "currency": "INR",
            "hl": "en",
            "gl": "in"
        })

        flights = []

        all_options = []

        all_options.extend(
            results.get("best_flights", [])
        )

        all_options.extend(
            results.get("other_flights", [])
        )

        # Keep maximum 10 options
        for index, option in enumerate(all_options[:10]):

            segments = option.get("flights", [])

            if not segments:
                continue

            first_segment = segments[0]
            last_segment = segments[-1]

            departure = first_segment.get(
                "departure_airport", {}
            )

            arrival = last_segment.get(
                "arrival_airport", {}
            )

            flight_info = {
                "option_id": index + 1,

                "airline": first_segment.get(
                    "airline"
                ),

                "flight_number": first_segment.get(
                    "flight_number"
                ),

                "departure_airport": departure.get(
                    "id"
                ),

                "departure_time": departure.get(
                    "time"
                ),

                "arrival_airport": arrival.get(
                    "id"
                ),

                "arrival_time": arrival.get(
                    "time"
                ),

                "duration_minutes": option.get(
                    "total_duration"
                ),

                "price_inr": option.get(
                    "price"
                ),

                "stops": max(
                    0,
                    len(segments) - 1
                ),

                "travel_class": first_segment.get(
                    "travel_class"
                ),

                # Keep internally for future booking flow
                "booking_token": option.get(
                    "booking_token"
                )
            }

            flights.append(flight_info)

        if not flights:

            session.last_search_results = []
            session.selected_flight = None
            session.booking_confirmed = False

            return json.dumps({
                "status": "NO_RESULTS",
                "message": (
                    f"No flights found from "
                    f"{origin} to {destination} "
                    f"on {date}."
                )
            })

        # Save latest search in this user's session
        session.last_search_results = flights

        # Reset old selection
        session.selected_flight = None
        session.passenger_name = None
        session.booking_confirmed = False

        return json.dumps({
            "status": "SUCCESS",
            "origin": origin.upper(),
            "destination": destination.upper(),
            "date": date,
            "flights": flights,
            "price_insights": results.get(
                "price_insights",
                {}
            )
        }, indent=2)


    # --------------------------------------------------------
    # RECOMMEND FLIGHT
    # --------------------------------------------------------

    @tool
    def recommend_flight(
        preference: str = "best"
    ) -> str:
        """
        Recommend flights from the latest search.

        Preferences:
        - cheapest
        - fastest
        - nonstop
        - best
        """

        flights = session.last_search_results

        if not flights:
            return (
                "No flight search has been performed yet."
            )

        preference = preference.lower().strip()

        # Cheapest
        if preference in {
            "cheapest",
            "lowest price",
            "lowest"
        }:

            ranked = sorted(
                flights,
                key=lambda f: f.get(
                    "price_inr",
                    float("inf")
                )
            )

        # Fastest
        elif preference in {
            "fastest",
            "quickest"
        }:

            ranked = sorted(
                flights,
                key=lambda f: f.get(
                    "duration_minutes",
                    float("inf")
                )
            )

        # Non-stop
        elif preference in {
            "nonstop",
            "non-stop",
            "direct"
        }:

            ranked = sorted(
                flights,
                key=lambda f: (
                    f.get("stops", 999),
                    f.get(
                        "price_inr",
                        float("inf")
                    )
                )
            )

        # Best value
        else:

            max_price = max(
                f.get("price_inr", 0)
                for f in flights
            ) or 1

            max_duration = max(
                f.get("duration_minutes", 0)
                for f in flights
            ) or 1

            ranked = []

            for flight in flights:

                price_score = (
                    flight.get(
                        "price_inr",
                        max_price
                    ) / max_price
                )

                duration_score = (
                    flight.get(
                        "duration_minutes",
                        max_duration
                    ) / max_duration
                )

                stops_score = min(
                    flight.get("stops", 0),
                    2
                ) / 2

                score = (
                    0.5 * price_score
                    + 0.3 * duration_score
                    + 0.2 * stops_score
                )

                flight_copy = flight.copy()

                flight_copy["value_score"] = round(
                    score,
                    4
                )

                ranked.append(flight_copy)

            ranked.sort(
                key=lambda f: f["value_score"]
            )

        return json.dumps({
            "preference": preference,
            "recommended": ranked[0],
            "alternatives": ranked[1:4]
        }, indent=2)


    # --------------------------------------------------------
    # SELECT FLIGHT
    # --------------------------------------------------------

    @tool
    def select_flight(
        option_id: int
    ) -> str:
        """
        Select one flight from the latest search results.
        """

        selected = next(
            (
                flight
                for flight in session.last_search_results
                if flight.get("option_id")
                == option_id
            ),
            None
        )

        if selected is None:

            available = [
                flight.get("option_id")
                for flight
                in session.last_search_results
            ]

            return (
                f"Option {option_id} was not found. "
                f"Available option IDs are: "
                f"{available}"
            )

        session.selected_flight = selected

        # New selection requires new confirmation
        session.booking_confirmed = False

        return json.dumps({
        "status": "SELECTED",
        "message": "Flight successfully selected.",
        "flight": selected
        }, indent=2)


    # --------------------------------------------------------
    # GET SELECTED FLIGHT
    # --------------------------------------------------------

    @tool
    def get_selected_flight() -> str:
        """
        Return the currently selected flight.
        """

        if session.selected_flight is None:
            return (
                "No flight has been selected."
            )

        return json.dumps({
            "status": "SELECTED",
            "flight": session.selected_flight
        }, indent=2)

    @tool
    def set_passenger_name(passenger_name: str) -> str:
        """
        Store the passenger's full name before booking.
        """

        passenger_name = passenger_name.strip()

        if not passenger_name:
            return "Passenger name cannot be empty."

        if session.selected_flight is None:
            return "No flight has been selected."

        session.passenger_name = passenger_name

        return json.dumps({
            "status": "PASSENGER_SAVED",
            "passenger_name": passenger_name
        }, indent=2)

    # --------------------------------------------------------
    # CONFIRM BOOKING
    # --------------------------------------------------------

    @tool
    def confirm_booking() -> str:
        """
        Mark the current booking as explicitly
        confirmed by the user.
        """

        if session.selected_flight is None:
            return (
                "No flight has been selected."
            )

        session.booking_confirmed = True

        return json.dumps({
            "status": "CONFIRMED",
            "message": (
                "User confirmation received."
            )
        }, indent=2)


    # --------------------------------------------------------
    # BOOK FLIGHT
    # --------------------------------------------------------

    @tool
    def book_flight(
        passenger_name: str
    ) -> str:
        """
        Create a MOCK booking after explicit
        user confirmation.

        This does NOT create a real airline
        reservation.
        """

        if session.selected_flight is None:

            return json.dumps({
                "status": "FAILED",
                "message": (
                    "No flight has been selected."
                )
            }, indent=2)

        if not session.booking_confirmed:

            return json.dumps({
                "status": "FAILED",
                "message": (
                    "Booking cannot proceed without "
                    "explicit user confirmation."
                )
            }, indent=2)

        import random
        import string

        # Generate PNR FIRST
        pnr = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        # Store booking information
        session.passenger_name = passenger_name
        session.booking_reference = pnr

        return json.dumps({
            "status": "SUCCESS",
            "booking_reference": pnr,
            "passenger": passenger_name,
            "flight_details": session.selected_flight
        }, indent=2)

    # ========================================================
    # RETURN ALL TOOLS
    # ========================================================

    return [
        search_flights,
        recommend_flight,
        select_flight,
        get_selected_flight,
        set_passenger_name,
        confirm_booking,
        book_flight
    ]