# CS-4347 Airport Management System - Milestone 2

This project implements the Milestone 2 command-line logic for an Airport Management System backed by MySQL. The `data/` folder contains the professor-provided CSV files.

## Requirements

- Python 3.10 or newer
- MySQL Server
- `mysql-connector-python`

Install the Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

## Database Setup

Edit `config.ini` if your MySQL user, password, host, port, or database name differ from the defaults.
If `password` is left blank, the setup script and app will ask for your MySQL password when they connect.

Create the schema and load the professor CSV files:

```bash
python3 setup_database.py
```

The setup script:

- recreates the `airport_db` database
- creates the schema in `schema.sql`
- loads all CSVs from `data/`
- inserts four demo reservations so the passenger itinerary and booking queries have sample customers

You can also load the optional reservation rows separately after loading the CSVs:

```bash
mysql -u root -p airport_db < sample_data.sql
```

## Running Queries

All Milestone 2 features are available from `app.py`.

Search for a flight by number:

```bash
python3 app.py flight 1000
```

Find direct and one-stop itineraries between two airports or cities:

```bash
python3 app.py trip DFW MEX
python3 app.py trip Dallas "Mexico City"
```

Run the aircraft utilization report:

```bash
python3 app.py aircraft-utilization 2025-10-01 2025-10-31
```

Check seat availability for a specific flight instance:

```bash
python3 app.py seat-availability 1000 2025-10-04
```

Retrieve a passenger itinerary by customer name or phone/ID value:

```bash
python3 app.py passenger-itinerary "John Smith"
python3 app.py passenger-itinerary 2145550101
```

## Implemented Features

- Travel itinerary search between two airports by city name or airport code
- Direct flights and one-stop connecting flights
- Flight lookup by flight number with legs and fares
- Aircraft utilization report for a date range
- Seat availability for a flight number and date
- Passenger itinerary lookup with connection airports, scheduled times, and seat assignments

## Main Files

- `app.py` - command-line interface
- `queries.py` - SQL query functions
- `db.py` - MySQL connection helper using `config.ini`
- `schema.sql` - database schema matching the professor CSV files
- `setup_database.py` - CSV loader and database setup script
- `data/` - professor-provided CSV files
- `sample_data.sql` - optional reservation demo rows
- `requirements.txt` - Python dependency list
