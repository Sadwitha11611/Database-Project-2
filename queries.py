"""
queries.py - All database query functions for Airport Management System
CS-4347 Database Systems - Milestone 2

Implements:
  - flight(flight_number)           : Search flight by number
  - trip(src, dst)                  : Travel itinerary between two airports (direct + 1-stop)
  - aircraft_utilization(start, end): Infrastructure report
  - seat_availability(flight, date) : Seat availability check
  - passenger_itinerary(name)       : Passenger booking retrieval
"""

from db import get_connection, close_connection


def _conn():
    return get_connection()


# ─────────────────────────────────────────────────────────────────────────────
# 1. FLIGHT SEARCH BY NUMBER
# ─────────────────────────────────────────────────────────────────────────────

def flight(flight_number: str):
    """
    Given a flight number, return the full details of that flight including
    all legs, departure/arrival airports, scheduled times, and available fares.

    Usage: flight("AA3478")
    """
    conn = _conn()
    cursor = conn.cursor(dictionary=True)

    # Flight header
    cursor.execute("""
        SELECT f.Number, f.Airline, f.Weekdays
        FROM FLIGHT f
        WHERE f.Number = %s
    """, (flight_number,))
    flight_row = cursor.fetchone()

    if not flight_row:
        close_connection(conn, cursor)
        return None, None, None

    # Flight legs
    cursor.execute("""
        SELECT
            fl.Leg_no,
            fl.Number,
            dep.Airport_code AS Dep_code,
            dep.City         AS Dep_city,
            dep.Name         AS Dep_name,
            arr.Airport_code AS Arr_code,
            arr.City         AS Arr_city,
            arr.Name         AS Arr_name,
            fl.Scheduled_dep_time,
            fl.Scheduled_arr_time
        FROM FLIGHT_LEG fl
        JOIN AIRPORT dep ON fl.Dep_airport_code = dep.Airport_code
        JOIN AIRPORT arr ON fl.Arr_airport_code = arr.Airport_code
        WHERE fl.Number = %s
        ORDER BY fl.Leg_no
    """, (flight_number,))
    legs = cursor.fetchall()

    # Fares
    cursor.execute("""
        SELECT Code, Amount, Restriction
        FROM FARE
        WHERE Number = %s
        ORDER BY Amount
    """, (flight_number,))
    fares = cursor.fetchall()

    close_connection(conn, cursor)
    return flight_row, legs, fares


# ─────────────────────────────────────────────────────────────────────────────
# 2. TRIP / TRAVEL ITINERARY SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def trip(src: str, dst: str):
    """
    Find all travel itineraries between src and dst airports.
    Supports:
      - Lookup by 3-letter airport code (e.g. "DFW") or city name (e.g. "Dallas")
      - Direct flights (single leg)
      - One-stop connecting flights (two legs)

    Usage: trip("DFW", "SFO")  or  trip("Dallas", "San Francisco")
    """
    conn = _conn()
    cursor = conn.cursor(dictionary=True)

    # Resolve airport codes from either code or city name
    def resolve_airports(identifier):
        identifier = identifier.strip()
        # Try exact code match first (case-insensitive)
        cursor.execute("""
            SELECT Airport_code, City, Name FROM AIRPORT
            WHERE UPPER(Airport_code) = UPPER(%s)
        """, (identifier,))
        rows = cursor.fetchall()
        if rows:
            return rows
        # Try city name match
        cursor.execute("""
            SELECT Airport_code, City, Name FROM AIRPORT
            WHERE City LIKE %s
        """, (f"%{identifier}%",))
        return cursor.fetchall()

    src_airports = resolve_airports(src)
    dst_airports = resolve_airports(dst)

    if not src_airports:
        close_connection(conn, cursor)
        return None, None, f"No airport found matching '{src}'"

    if not dst_airports:
        close_connection(conn, cursor)
        return None, None, f"No airport found matching '{dst}'"

    src_codes = [a['Airport_code'] for a in src_airports]
    dst_codes = [a['Airport_code'] for a in dst_airports]

    src_placeholder = ','.join(['%s'] * len(src_codes))
    dst_placeholder = ','.join(['%s'] * len(dst_codes))

    # ── Direct flights ────────────────────────────────────────────────────────
    cursor.execute(f"""
        SELECT
            f.Number AS flight_number,
            f.Airline,
            f.Weekdays,
            fl.Leg_no,
            dep.Airport_code AS dep_code,
            dep.City         AS dep_city,
            arr.Airport_code AS arr_code,
            arr.City         AS arr_city,
            fl.Scheduled_dep_time,
            fl.Scheduled_arr_time,
            'DIRECT' AS type
        FROM FLIGHT_LEG fl
        JOIN FLIGHT f   ON fl.Number = f.Number
        JOIN AIRPORT dep ON fl.Dep_airport_code = dep.Airport_code
        JOIN AIRPORT arr ON fl.Arr_airport_code = arr.Airport_code
        WHERE fl.Dep_airport_code IN ({src_placeholder})
          AND fl.Arr_airport_code IN ({dst_placeholder})
        ORDER BY fl.Scheduled_dep_time
    """, src_codes + dst_codes)
    direct_flights = cursor.fetchall()

    # ── Connecting flights (two legs, one stop) ───────────────────────────────
    cursor.execute(f"""
        SELECT
            leg1.Number    AS flight1_number,
            f1.Airline     AS airline1,
            dep1.Airport_code AS dep1_code,
            dep1.City         AS dep1_city,
            con.Airport_code  AS con_code,
            con.City          AS con_city,
            leg1.Scheduled_dep_time AS dep1_time,
            leg1.Scheduled_arr_time AS arr1_time,

            leg2.Number    AS flight2_number,
            f2.Airline     AS airline2,
            arr2.Airport_code AS arr2_code,
            arr2.City         AS arr2_city,
            leg2.Scheduled_dep_time AS dep2_time,
            leg2.Scheduled_arr_time AS arr2_time,

            'CONNECTING' AS type
        FROM FLIGHT_LEG leg1
        JOIN FLIGHT_LEG leg2
            ON  leg1.Arr_airport_code = leg2.Dep_airport_code
            AND leg1.Number != leg2.Number
        JOIN FLIGHT  f1  ON leg1.Number = f1.Number
        JOIN FLIGHT  f2  ON leg2.Number = f2.Number
        JOIN AIRPORT dep1 ON leg1.Dep_airport_code = dep1.Airport_code
        JOIN AIRPORT con  ON leg1.Arr_airport_code = con.Airport_code
        JOIN AIRPORT arr2 ON leg2.Arr_airport_code = arr2.Airport_code
        WHERE leg1.Dep_airport_code IN ({src_placeholder})
          AND leg2.Arr_airport_code IN ({dst_placeholder})
          AND leg1.Arr_airport_code NOT IN ({src_placeholder})
          AND leg1.Arr_airport_code NOT IN ({dst_placeholder})
          AND leg2.Scheduled_dep_time > leg1.Scheduled_arr_time
        ORDER BY leg1.Scheduled_dep_time, leg2.Scheduled_dep_time
    """, src_codes + dst_codes + src_codes + dst_codes)
    connecting_flights = cursor.fetchall()

    close_connection(conn, cursor)
    return direct_flights, connecting_flights, None


# ─────────────────────────────────────────────────────────────────────────────
# 3. AIRCRAFT UTILIZATION REPORT
# ─────────────────────────────────────────────────────────────────────────────

def aircraft_utilization(start_date: str, end_date: str):
    """
    For a given time period, list every airplane (by registration number and type)
    along with the total number of flights it was assigned to.

    Usage: aircraft_utilization("2026-04-01", "2026-04-30")
    """
    conn = _conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.Airplane_id,
            a.Type_name,
            t.Company,
            a.Total_no_of_seats,
            COUNT(li.Date) AS total_flights
        FROM AIRPLANE a
        LEFT JOIN AIRPLANE_TYPE t ON a.Type_name = t.Type_name
        LEFT JOIN LEG_INSTANCE li
            ON a.Airplane_id = li.Airplane_id
            AND li.Date BETWEEN %s AND %s
        GROUP BY a.Airplane_id, a.Type_name, t.Company, a.Total_no_of_seats
        ORDER BY total_flights DESC, a.Airplane_id
    """, (start_date, end_date))
    rows = cursor.fetchall()

    close_connection(conn, cursor)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 4. SEAT AVAILABILITY CHECK
# ─────────────────────────────────────────────────────────────────────────────

def seat_availability(flight_number: str, date: str):
    """
    For a chosen flight instance (specific flight number + date), count seats
    on the assigned airplane type versus confirmed reservations to determine
    remaining capacity.

    Usage: seat_availability("AA3478", "2026-05-01")
    """
    conn = _conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            li.Date,
            li.Leg_no,
            li.Number AS flight_number,
            li.Airplane_id,
            a.Type_name,
            t.Max_seats,
            li.No_of_avail_seats,
            dep.Airport_code AS dep_code,
            dep.City         AS dep_city,
            arr.Airport_code AS arr_code,
            arr.City         AS arr_city,
            fl.Scheduled_dep_time,
            fl.Scheduled_arr_time,
            COUNT(s.Seat_no) AS booked_seats
        FROM LEG_INSTANCE li
        JOIN FLIGHT_LEG fl
            ON li.Leg_no = fl.Leg_no AND li.Number = fl.Number
        JOIN AIRPORT dep ON fl.Dep_airport_code = dep.Airport_code
        JOIN AIRPORT arr ON fl.Arr_airport_code = arr.Airport_code
        JOIN AIRPLANE a  ON li.Airplane_id = a.Airplane_id
        JOIN AIRPLANE_TYPE t ON a.Type_name = t.Type_name
        LEFT JOIN SEAT s
            ON s.Date = li.Date AND s.Leg_no = li.Leg_no AND s.Number = li.Number
        WHERE li.Number = %s AND li.Date = %s
        GROUP BY
            li.Date, li.Leg_no, li.Number, li.Airplane_id,
            a.Type_name, t.Max_seats, li.No_of_avail_seats,
            dep.Airport_code, dep.City, arr.Airport_code, arr.City,
            fl.Scheduled_dep_time, fl.Scheduled_arr_time
        ORDER BY li.Leg_no
    """, (flight_number, date))
    rows = cursor.fetchall()

    close_connection(conn, cursor)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 5. PASSENGER ITINERARY RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────────

def passenger_itinerary(customer_name: str):
    """
    Given a customer name, return all flight legs they are booked on,
    including connection airports, scheduled times, and seat assignments.

    Usage: passenger_itinerary("John Smith")
    """
    conn = _conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.Customer_name,
            s.Cphone,
            s.Date,
            s.Number AS flight_number,
            f.Airline,
            s.Leg_no,
            s.Seat_no,
            dep.Airport_code AS dep_code,
            dep.City         AS dep_city,
            dep.Name         AS dep_name,
            arr.Airport_code AS arr_code,
            arr.City         AS arr_city,
            arr.Name         AS arr_name,
            fl.Scheduled_dep_time,
            fl.Scheduled_arr_time
        FROM SEAT s
        JOIN FLIGHT_LEG fl ON s.Leg_no = fl.Leg_no AND s.Number = fl.Number
        JOIN FLIGHT f       ON s.Number = f.Number
        JOIN AIRPORT dep    ON fl.Dep_airport_code = dep.Airport_code
        JOIN AIRPORT arr    ON fl.Arr_airport_code = arr.Airport_code
        WHERE s.Customer_name LIKE %s
        ORDER BY s.Date, s.Number, s.Leg_no
    """, (f"%{customer_name}%",))
    rows = cursor.fetchall()

    close_connection(conn, cursor)
    return rows