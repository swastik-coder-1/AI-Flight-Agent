import os
from typing import Annotated, Literal

from typing_extensions import TypedDict

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage
)

from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from flight_tools import (
    FlightSession,
    create_flight_tools
)


# ============================================================
# CHECK API KEYS
# ============================================================

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY is not set.")

if not os.getenv("SERPAPI_KEY"):
    raise ValueError("SERPAPI_KEY is not set.")


# ============================================================
# LANGGRAPH STATE
# ============================================================

class State(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are an AI Flight Booking Assistant.\n\n"

        "Your job is to search, compare, recommend, "
        "select and book flights.\n\n"

        "RULES:\n"

        "1. Use search_flights for flight searches.\n"

        "2. Use recommend_flight when the user asks for "
        "the cheapest, fastest, best, best-value, "
        "or non-stop flight.\n"

        "3. When the user chooses an option, ALWAYS use "
        "select_flight to store the exact flight.\n"

        "4. After select_flight succeeds, ALWAYS show the user "
        "the selected flight's airline, flight number, route, "
        "departure time, arrival time, price, and travel class.\n"

        "5. After displaying the selected flight details, ask "
        "for the passenger's full name.\n"

        "6. Never invent flight information.\n"

        "7. Only use information returned by the tools.\n"

        "8. Before booking, collect the passenger's "
        "full name.\n"

        "9. After receiving the passenger's name, DO NOT "
        "book immediately.\n"

        "10. Show the complete booking details and ask "
        "for explicit confirmation.\n"

        "11. Only when the user explicitly confirms the "
        "booking should you call confirm_booking.\n"

        "12. Only after confirm_booking succeeds may "
        "you call book_flight.\n"

        "13. Never call book_flight before confirmation.\n"

        "14. When displaying flight options, preserve "
        "the option_id returned by the tool.\n"

        "15. Never ask the user to select an option that "
        "was not displayed.\n"

        "16. After receiving the passenger's full name, ALWAYS use "
        "set_passenger_name to store it.\n"

        "17. After the passenger name is saved, DO NOT book yet.\n"

        "18. Show the complete booking details and ask for explicit "
        "confirmation.\n"

        "19. Only when the user explicitly confirms the booking "
        "should you call confirm_booking.\n"

        "20. Only after confirm_booking succeeds may you call "
        "book_flight.\n"

        "21. Never call book_flight before confirmation.\n"


    )
)


# ============================================================
# CREATE A COMPLETE AGENT FOR ONE SESSION
# ============================================================

def create_agent():

    # Each call creates a completely separate session
    session = FlightSession()

    # Tools close over this specific session
    tools = create_flight_tools(session)

    tool_node = ToolNode(tools)

    # Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    llm_with_tools = llm.bind_tools(tools)

    # --------------------------------------------------------
    # AGENT NODE
    # --------------------------------------------------------

    def agent_node(state: State):

        messages = state["messages"]

        if not any(
            isinstance(message, SystemMessage)
            for message in messages
        ):
            messages = [
                SYSTEM_PROMPT
            ] + messages

        response = llm_with_tools.invoke(
            messages
        )

        return {
            "messages": [response]
        }

    # --------------------------------------------------------
    # TOOL DECISION
    # --------------------------------------------------------

    def should_continue(
        state: State
    ) -> Literal["tools", END]:

        last_message = state["messages"][-1]

        if getattr(
            last_message,
            "tool_calls",
            None
        ):
            return "tools"

        return END

    # --------------------------------------------------------
    # BUILD GRAPH
    # --------------------------------------------------------

    workflow = StateGraph(State)

    workflow.add_node(
        "agent",
        agent_node
    )

    workflow.add_node(
        "tools",
        tool_node
    )

    workflow.add_edge(
        START,
        "agent"
    )

    workflow.add_conditional_edges(
        "agent",
        should_continue
    )

    workflow.add_edge(
        "tools",
        "agent"
    )

    compiled_app = workflow.compile()

    return compiled_app, session


# ============================================================
# TERMINAL MODE
# ============================================================

if __name__ == "__main__":

    app, session = create_agent()

    print("\n====================================")
    print("✈️ AI FLIGHT SEARCH AGENT")
    print("Type 'quit' to exit.")
    print("====================================\n")

    state = {
        "messages": []
    }

    while True:

        user_input = input("You: ")

        if user_input.lower().strip() in {
            "quit",
            "exit"
        }:
            print("Goodbye! ✈️")
            break

        if not user_input.strip():
            continue

        state["messages"].append(
            HumanMessage(
                content=user_input
            )
        )

        state = app.invoke(state)

        final_message = state["messages"][-1]

        print("\nAgent:")

        if isinstance(
            final_message.content,
            str
        ):
            print(final_message.content)

        elif isinstance(
            final_message.content,
            list
        ):

            for block in final_message.content:

                if (
                    isinstance(block, dict)
                    and block.get("type") == "text"
                ):
                    print(
                        block.get(
                            "text",
                            ""
                        )
                    )

        else:
            print(final_message.content)

        print()