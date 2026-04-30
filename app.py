"""Command-line interface for CS-4347 Airport Management Milestone 2."""

import argparse
from decimal import Decimal


def _format_value(value):
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return "" if value is None else str(value)


def _print_rows(rows, empty_message="No results found."):
    if not rows:
        print(empty_message)
        return

    columns = list(rows[0].keys())
    widths = {
        column: max(len(column), *(len(_format_value(row[column])) for row in rows))
        for column in columns
    }
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    divider = "-+-".join("-" * widths[column] for column in columns)
    print(header)
    print(divider)
    for row in rows:
        print(" | ".join(_format_value(row[column]).ljust(widths[column]) for column in columns))


def _cmd_flight(args):
    from queries import flight

    flight_row, legs, fares = flight(args.flight_number)
    if not flight_row:
        print(f"No flight found for {args.flight_number}.")
        return

    print("\nFlight")
    _print_rows([flight_row])
    print("\nLegs")
    _print_rows(legs, "No legs found for this flight.")
    print("\nFares")
    _print_rows(fares, "No fares found for this flight.")


def _cmd_trip(args):
    from queries import trip

    direct, connecting, error = trip(args.source, args.destination)
    if error:
        print(error)
        return

    print("\nDirect Flights")
    _print_rows(direct, "No direct flights found.")
    print("\nOne-Stop Connecting Flights")
    _print_rows(connecting, "No one-stop connecting flights found.")


def _cmd_aircraft_utilization(args):
    from queries import aircraft_utilization

    rows = aircraft_utilization(args.start_date, args.end_date)
    _print_rows(rows, "No airplanes found.")


def _cmd_seat_availability(args):
    from queries import seat_availability

    rows = seat_availability(args.flight_number, args.date)
    for row in rows:
        booked = row.get("booked_seats") or 0
        max_seats = row.get("Max_seats") or 0
        row["computed_remaining_seats"] = max_seats - booked
    _print_rows(rows, "No flight instances found for that flight and date.")


def _cmd_passenger(args):
    from queries import passenger_itinerary

    rows = passenger_itinerary(args.customer)
    _print_rows(rows, "No itinerary found for that customer.")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Airport Management System command-line queries"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    flight_parser = subparsers.add_parser("flight", help="Search by flight number")
    flight_parser.add_argument("flight_number", help='Example: "AA3478"')
    flight_parser.set_defaults(func=_cmd_flight)

    trip_parser = subparsers.add_parser("trip", help="Find direct and one-stop itineraries")
    trip_parser.add_argument("source", help='Source city or airport code, e.g. "DFW"')
    trip_parser.add_argument("destination", help='Destination city or airport code, e.g. "SFO"')
    trip_parser.set_defaults(func=_cmd_trip)

    utilization_parser = subparsers.add_parser(
        "aircraft-utilization",
        help="Count assigned flight instances for each airplane in a date range",
    )
    utilization_parser.add_argument("start_date", help="YYYY-MM-DD")
    utilization_parser.add_argument("end_date", help="YYYY-MM-DD")
    utilization_parser.set_defaults(func=_cmd_aircraft_utilization)

    seat_parser = subparsers.add_parser(
        "seat-availability",
        help="Compare airplane capacity with confirmed reservations",
    )
    seat_parser.add_argument("flight_number", help='Example: "AA3478"')
    seat_parser.add_argument("date", help="YYYY-MM-DD")
    seat_parser.set_defaults(func=_cmd_seat_availability)

    passenger_parser = subparsers.add_parser(
        "passenger-itinerary",
        help="List flight legs booked by a customer name or phone/ID",
    )
    passenger_parser.add_argument("customer", help='Example: "John Smith"')
    passenger_parser.set_defaults(func=_cmd_passenger)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
