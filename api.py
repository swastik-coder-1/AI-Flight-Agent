from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import HumanMessage

from app import create_agent


# ============================================================
# FASTAPI APP
# ============================================================

api = FastAPI(
    title="AI Flight Booking Agent",
    description="Agentic AI flight search and booking API",
    version="1.0.0"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


# ============================================================
# SESSION STORAGE
# ============================================================

sessions = {}


# ============================================================
# ROOT
# ============================================================

@api.get("/")
def root():

    return {
        "message": (
            "AI Flight Booking Agent API is running."
        )
    }


# ============================================================
# CHAT
# ============================================================

@api.post("/chat")
def chat(request: ChatRequest):

    # --------------------------------------------------------
    # CREATE NEW SESSION
    # --------------------------------------------------------

    if request.session_id not in sessions:

        agent, flight_session = create_agent()

        sessions[request.session_id] = {
            "app": agent,
            "flight_session": flight_session,
            "state": {
                "messages": []
            }
        }

    # --------------------------------------------------------
    # GET USER'S SESSION
    # --------------------------------------------------------

    user_session = sessions[
        request.session_id
    ]

    agent = user_session["app"]
    state = user_session["state"]

    # --------------------------------------------------------
    # ADD USER MESSAGE
    # --------------------------------------------------------

    state["messages"].append(
        HumanMessage(
            content=request.message
        )
    )

    # --------------------------------------------------------
    # RUN AGENT
    # --------------------------------------------------------

    result = agent.invoke(state)

    # Save updated conversation state
    user_session["state"] = result

    # --------------------------------------------------------
    # EXTRACT FINAL RESPONSE
    # --------------------------------------------------------

    final_message = result["messages"][-1]

    content = final_message.content

    if isinstance(content, str):

        response_text = content

    elif isinstance(content, list):

        text_parts = []

        for block in content:

            if (
                isinstance(block, dict)
                and block.get("type") == "text"
            ):

                text_parts.append(
                    block.get(
                        "text",
                        ""
                    )
                )

        response_text = "\n".join(
            text_parts
        )

    else:

        response_text = str(content)

    flight_session = user_session["flight_session"]

    flight_options = flight_session.last_search_results
    selected_flight = flight_session.selected_flight
    passenger_name = flight_session.passenger_name
    booking_confirmed = flight_session.booking_confirmed
    booking_reference = flight_session.booking_reference

    if selected_flight is None:
        booking_status = "searching"

    elif passenger_name is None:
        booking_status = "awaiting_passenger"

    elif not booking_confirmed:
        booking_status = "awaiting_confirmation"

    else:
        booking_status = "confirmed"

    booking_reference = (
        flight_session.booking_reference
    )   

    if booking_status == "confirmed":
        # Find the latest successful booking message/result
        if (
            isinstance(final_message.content, str)
            and "Booking Reference" in final_message.content
        ):
            import re

            match = re.search(
                r"Booking Reference:\**\s*([A-Z0-9]+)",
                final_message.content
            )

            if match:
                booking_reference = match.group(1)
    
    return {
    "session_id": request.session_id,
    "response": response_text,
    "flight_options": flight_options,
    "selected_flight": selected_flight,
    "passenger_name": passenger_name,
    "booking_status": booking_status,
    "booking_reference": booking_reference

}