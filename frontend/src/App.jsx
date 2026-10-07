import { useState } from "react";
import {
  Plane,
  Send,
  Loader2,
  Sparkles,
  CheckCircle2
} from "lucide-react";

import "./App.css";


function App() {

  // ============================================================
  // STATE
  // ============================================================

  const [flightOptions, setFlightOptions] = useState([]);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your AI flight assistant. Tell me where you want to fly, when you want to travel, and I'll find the best options."
    }
  ]);

  const [input, setInput] = useState("");

  const [loading, setLoading] = useState(false);

  const [selectedFlight, setSelectedFlight] =
    useState(null);

  const [passengerName, setPassengerName] =
    useState("");

  const [bookingStatus, setBookingStatus] =
    useState("searching");

  const [bookingReference, setBookingReference] =
    useState(null);


  // ============================================================
  // SESSION ID
  // ============================================================

  const [sessionId] = useState(() => {

    let id = localStorage.getItem(
      "flight_agent_session"
    );

    if (!id) {

      id =
        "session-" +
        Math.random()
          .toString(36)
          .substring(2, 12);

      localStorage.setItem(
        "flight_agent_session",
        id
      );
    }

    return id;
  });


  // ============================================================
  // SEND MESSAGE
  // ============================================================

  async function sendMessage(customMessage = null) {

    const userMessage =
      customMessage !== null
        ? customMessage
        : input.trim();

    if (!userMessage || loading) {
      return;
    }

    // Clear normal input box
    if (customMessage === null) {
      setInput("");
    }

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: userMessage
      }
    ]);

    setLoading(true);

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/chat",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            session_id: sessionId,
            message: userMessage
          })
        }
      );

      const responseText =
        await response.text();

      if (!response.ok) {
        throw new Error(
          `Server returned ${response.status}: ${responseText}`
        );
      }

      const data =
        JSON.parse(responseText);


      // ========================================================
      // AI RESPONSE
      // ========================================================

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response
        }
      ]);


      // ========================================================
      // FLIGHT OPTIONS
      // ========================================================

      if (
        Array.isArray(data.flight_options)
      ) {

        setFlightOptions(
          data.flight_options
        );

      }


      // ========================================================
      // SELECTED FLIGHT
      // ========================================================

      if (
        data.selected_flight
      ) {

        setSelectedFlight(
          data.selected_flight
        );

      }


      // ========================================================
      // PASSENGER NAME
      // ========================================================

      if (
        data.passenger_name
      ) {

        setPassengerName(
          data.passenger_name
        );

      }


      // ========================================================
      // BOOKING STATUS
      // ========================================================

      if (
        data.booking_status
      ) {

        setBookingStatus(
          data.booking_status
        );

      }


      // ========================================================
      // BOOKING REFERENCE
      // ========================================================

      if (
        data.booking_reference
      ) {

        setBookingReference(
          data.booking_reference
        );

      }


      // ========================================================
      // NEW SEARCH
      // ========================================================

      if (
        Array.isArray(data.flight_options) &&
        data.flight_options.length > 0 &&
        !data.selected_flight
      ) {

        setSelectedFlight(null);

        setPassengerName("");

        setBookingReference(null);

      }

    } catch (error) {

      console.error(
        "Frontend error:",
        error
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            `Error: ${error.message}`
        }
      ]);

    } finally {

      setLoading(false);

    }
  }


  // ============================================================
  // ENTER KEY
  // ============================================================

  function handleKeyDown(event) {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      sendMessage();

    }

  }


  // ============================================================
  // FORMAT DATE/TIME
  // ============================================================

  function formatDateTime(value) {

    if (!value) {
      return "-";
    }

    return value.replace(
      " ",
      " • "
    );
  }


  // ============================================================
  // RESET FOR NEW SEARCH
  // ============================================================

  function startNewSearch() {

    setFlightOptions([]);

    setSelectedFlight(null);

    setPassengerName("");

    setBookingStatus("searching");

    setBookingReference(null);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content:
          "Sure! Where would you like to fly next?"
      }
    ]);

  }


  // ============================================================
  // MAIN UI
  // ============================================================

  return (

    <div className="app">


      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            <Plane size={22} />
          </div>

          <div>

            <h1>
              AI Flight Agent
            </h1>

            <p>
              Intelligent flight search & booking assistant
            </p>

          </div>

        </div>


        <div className="status">

          <span className="status-dot"></span>

          AI Online

        </div>

      </header>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="main">


        {/* ====================================================
            CHAT PANEL
        ==================================================== */}

        <section className="chat-panel">

          <div className="messages">


            {/* ==================================================
                CHAT MESSAGES
            ================================================== */}

            {messages.map(
              (message, index) => (

                <div
                  key={index}
                  className={
                    message.role === "user"
                      ? "message user-message"
                      : "message assistant-message"
                  }
                >

                  {message.role ===
                    "assistant" && (

                    <div className="avatar">

                      <Sparkles size={17} />

                    </div>

                  )}

                  <div className="message-content">

                    {message.content}

                  </div>

                </div>

              )
            )}


            {/* ==================================================
                LOADING
            ================================================== */}

            {loading && (

              <div className="message assistant-message">

                <div className="avatar">

                  <Sparkles size={17} />

                </div>

                <div className="message-content loading">

                  <Loader2
                    size={18}
                    className="spin"
                  />

                  Finding the best flights...

                </div>

              </div>

            )}


            {/* ==================================================
                FLIGHT OPTIONS
            ================================================== */}

            {flightOptions.length > 0 &&
              bookingStatus !== "confirmed" && (

                <div className="flight-options">

                  <h2>
                    Available Flights
                  </h2>


                  {flightOptions.map(
                    (flight) => (

                      <div
                        key={flight.option_id}
                        className="flight-option"
                      >


                        {/* TOP */}

                        <div className="flight-top">

                          <div>

                            <strong>
                              {flight.airline}
                            </strong>

                            <span>
                              {flight.flight_number}
                            </span>

                          </div>


                          <strong
                            className="flight-price"
                          >

                            ₹
                            {Number(
                              flight.price_inr
                            ).toLocaleString(
                              "en-IN"
                            )}

                          </strong>

                        </div>


                        {/* ROUTE */}

                        <div className="flight-route">

                          <div>

                            <small>
                              {flight.departure_airport}
                            </small>

                            <strong>
                              {formatDateTime(
                                flight.departure_time
                              )}
                            </strong>

                          </div>


                          <div className="flight-arrow">
                            →
                          </div>


                          <div>

                            <small>
                              {flight.arrival_airport}
                            </small>

                            <strong>
                              {formatDateTime(
                                flight.arrival_time
                              )}
                            </strong>

                          </div>

                        </div>


                        {/* META */}

                        <div className="flight-meta">

                          <span>
                            {flight.duration_minutes} min
                          </span>

                          <span>
                            {flight.stops === 0
                              ? "Non-stop"
                              : `${flight.stops} stop(s)`}
                          </span>

                          <span>
                            {flight.travel_class}
                          </span>

                          <span>
                            Option {flight.option_id}
                          </span>

                        </div>


                        {/* SELECT */}

                        <button
                          className="select-flight"
                          onClick={() =>
                            sendMessage(
                              `I want option ${flight.option_id}`
                            )
                          }
                          disabled={loading}
                        >
                          Select Flight
                        </button>

                      </div>

                    )
                  )}

                </div>

              )
            }

          </div>


          {/* ==================================================
              INPUT
          ================================================== */}

          {bookingStatus !== "confirmed" && (

            <div className="input-area">

              <input
                type="text"
                placeholder="Try: Find flights from DEL to BOM on 2026-10-20"
                value={input}
                onChange={(event) =>
                  setInput(
                    event.target.value
                  )
                }
                onKeyDown={handleKeyDown}
                disabled={loading}
              />


              <button
                onClick={() =>
                  sendMessage()
                }
                disabled={
                  loading ||
                  !input.trim()
                }
              >

                <Send size={18} />

              </button>

            </div>

          )}

        </section>


        {/* ====================================================
            RIGHT SIDEBAR
        ==================================================== */}

        {bookingStatus === "confirmed" ? (

          /* ==================================================
             BOOKING SUCCESS
             ================================================== */

          <aside className="flight-card booking-success">

            <div className="success-icon">

              <CheckCircle2 size={32} />

            </div>


            <div className="success-title">

              Booking Confirmed

            </div>


            <div className="pnr-label">

              Booking Reference

            </div>


            <div className="pnr">

              {bookingReference || "------"}

            </div>


            <div className="booking-details">

              <p>

                <span>
                  Passenger
                </span>

                <strong>
                  {passengerName}
                </strong>

              </p>


              <p>

                <span>
                  Flight
                </span>

                <strong>
                  {selectedFlight?.airline}{" "}
                  {selectedFlight?.flight_number}
                </strong>

              </p>


              <p>

                <span>
                  Route
                </span>

                <strong>

                  {selectedFlight?.departure_airport}

                  {" → "}

                  {selectedFlight?.arrival_airport}

                </strong>

              </p>


              <p>

                <span>
                  Departure
                </span>

                <strong>
                  {selectedFlight?.departure_time}
                </strong>

              </p>


              <p>

                <span>
                  Arrival
                </span>

                <strong>
                  {selectedFlight?.arrival_time}
                </strong>

              </p>


              <p>

                <span>
                  Total Price
                </span>

                <strong>

                  ₹
                  {Number(
                    selectedFlight?.price_inr || 0
                  ).toLocaleString(
                    "en-IN"
                  )}

                </strong>

              </p>

            </div>


            <button
              className="new-search-button"
              onClick={
                startNewSearch
              }
            >
              Search Another Flight
            </button>

          </aside>

        ) : selectedFlight ? (

          /* ==================================================
             SELECTED FLIGHT
             ================================================== */

          <aside className="flight-card">

            <div className="card-title">
              Selected Flight
            </div>


            <div className="airline">

              <Plane size={20} />

              <strong>
                {selectedFlight.airline}
              </strong>

            </div>


            <div className="flight-number">

              {selectedFlight.flight_number}

            </div>


            <div className="route">

              <div>

                <span>
                  {selectedFlight.departure_airport}
                </span>

                <strong>
                  {formatDateTime(
                    selectedFlight.departure_time
                  )}
                </strong>

              </div>


              <div className="arrow">
                →
              </div>


              <div>

                <span>
                  {selectedFlight.arrival_airport}
                </span>

                <strong>
                  {formatDateTime(
                    selectedFlight.arrival_time
                  )}
                </strong>

              </div>

            </div>


            <div className="details">

              <span>

                {selectedFlight.duration_minutes}
                {" "}min

              </span>


              <span>

                {selectedFlight.stops === 0
                  ? "Non-stop"
                  : `${selectedFlight.stops} stop(s)`}

              </span>


              <span>
                {selectedFlight.travel_class}
              </span>

            </div>


            <div className="price">

              ₹
              {Number(
                selectedFlight.price_inr
              ).toLocaleString(
                "en-IN"
              )}

            </div>


            {/* =================================================
                PASSENGER FORM
                ================================================= */}

            {bookingStatus ===
              "awaiting_passenger" && (

              <div className="passenger-form">

                <label>
                  Passenger Full Name
                </label>


                <input
                  type="text"
                  placeholder="Enter full name"
                  value={passengerName}
                  onChange={(event) =>
                    setPassengerName(
                      event.target.value
                    )
                  }
                />


                <button
                  className="review-booking"
                  disabled={
                    loading ||
                    !passengerName.trim()
                  }
                  onClick={() =>
                    sendMessage(
                      passengerName.trim()
                    )
                  }
                >
                  Continue to Review
                </button>

              </div>

            )}


            {/* =================================================
                CONFIRMATION
                ================================================= */}

            {bookingStatus ===
              "awaiting_confirmation" && (

              <div className="confirmation-box">

                <h3>
                  Confirm Booking
                </h3>


                <p>

                  Passenger:
                  <strong>
                    {" "}
                    {passengerName}
                  </strong>

                </p>


                <p>

                  Flight:
                  <strong>
                    {" "}
                    {selectedFlight.airline}{" "}
                    {selectedFlight.flight_number}
                  </strong>

                </p>


                <p>

                  Route:
                  <strong>

                    {" "}
                    {selectedFlight.departure_airport}

                    {" → "}

                    {selectedFlight.arrival_airport}

                  </strong>

                </p>


                <p>

                  Price:
                  <strong>

                    {" ₹"}

                    {Number(
                      selectedFlight.price_inr
                    ).toLocaleString(
                      "en-IN"
                    )}

                  </strong>

                </p>


                <div className="confirmation-actions">

                  <button
                    className="confirm-button"
                    disabled={loading}
                    onClick={() =>
                      sendMessage(
                        "Yes, I confirm the booking"
                      )
                    }
                  >
                    Confirm Booking
                  </button>


                  <button
                    className="cancel-button"
                    disabled={loading}
                    onClick={() =>
                      sendMessage(
                        "No, I do not want to book"
                      )
                    }
                  >
                    Cancel
                  </button>

                </div>

              </div>

            )}

          </aside>

        ) : null}

      </main>

    </div>
  );
}

export default App;