"""Creating and loading the airport database from the CSV files."""

# importing libraries for config reading and CSV handling 
from configparser import ConfigParser
from pathlib import Path
import csv
import getpass
import sys

#importing mySQL connector, exit if not installed
try:
    import mysql.connector
    from mysql.connector import Error
except ModuleNotFoundError:
    print("[ERROR] Missing Python package: mysql-connector-python")
    print("Install it with: python3 -m pip install -r requirements.txt")
    sys.exit(1)

#defining base directory and file paths
BASE_DIR = Path(__file__).resolve().parent
#folder where the CSV files are stored
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config.ini"
SCHEMA_PATH = BASE_DIR / "schema.sql"
#this is the number of rows inserted at once 
#for efficiency
BATCH_SIZE = 1000

#order in which CSV files should be loaded 
#this is important due to dependencies
LOAD_ORDER = [
    ("AIRPORT.csv", "AIRPORT", ["Airport_code", "Name", "City", "State"]),
    ("AIRPLANE_TYPE.csv", "AIRPLANE_TYPE", ["Type_name", "Company", "Max_seats"]),
    ("AIRPLANE.csv", "AIRPLANE", ["Airplane_id", "Total_no_of_seats", "Type_name"]),
    ("CAN_LAND.csv", "CAN_LAND", ["Airport_code", "Type_name"]),
    ("FLIGHT.csv", "FLIGHT", ["Number", "Airline", "Weekdays"]),
    (
        "FLIGHT_LEG.csv",
        "FLIGHT_LEG",
        [
            #maps the CSV column to the database column
            #because they defer in this case
            ("Flight_number", "Number"),
            "Leg_no",
            "Dep_airport_code",
            "Arr_airport_code",
            "Scheduled_dep_time",
            "Scheduled_arr_time",
        ],
    ),
    ("FARE.csv", "FARE", [("Flight_number", "Number"), "Code", "Amount", ("Restrictions", "Restriction")]),
    (
        "LEG_INSTANCE.csv",
        "LEG_INSTANCE",
        [
            "Date",
            ("Flight_number", "Number"),
            "Leg_no",
            "No_of_avail_seats",
            "Airplane_id",
            "Dep_time",
            "Arr_time",
        ],
    ),
    ("SEAT.csv", "SEAT", ["Airplane_id", "Seat_no", "Class"]),
]

#read the database configuration from config.ini
#ensure the required section and keys are present and convert port to integer
def read_config():
    parser = ConfigParser()
    parser.read(CONFIG_PATH)
    #ensure config has database section
    if not parser.has_section("database"):
        raise RuntimeError("config.ini must include a [database] section")

    config = dict(parser.items("database"))
    #default MySQL port
    config["port"] = int(config.get("port", 3306))
    return config

#prompt the user for password if it's not required in the config file
def prompt_for_password_if_needed(config):
    if config.get("password"):
         #already exists
        return config
    #only prompt if running interactively 
    if not sys.stdin.isatty():
        return config

    config = config.copy()
    user = config.get("user", "root")
    host = config.get("host", "localhost")
    #securely ask for password
    config["password"] = getpass.getpass(f"MySQL password for {user}@{host}: ")
    return config

#connecting to mySQL server without selecting a database
def connect_without_database(config):
    server_config = config.copy()
    #remove the database name
    server_config.pop("database", None)
    return mysql.connector.connect(**server_config)

#split the SQL script into individual statements
def split_sql_script(script):
    statements = []
    current = []
    for line in script.splitlines():
        stripped = line.strip()
        #skip empty lines and comments
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        #if line ends with ; → end of SQL statement
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []
    #add leftover statement
    if current:
        statements.append("\n".join(current))
    return statements

#run schema.sql to create tables 
def run_schema(cursor):
    script = SCHEMA_PATH.read_text(encoding="utf-8")
    #execute each SQL statement separately
    for statement in split_sql_script(script):
        cursor.execute(statement)

#extract column names for SQL INSERT
def column_names(columns):
    names = []
    for column in columns:
        # If tuple → use second value (DB column name)
        names.append(column[1] if isinstance(column, tuple) else column)
    return names

#extract values from CSV row based on the specified columns
def row_values(row, columns):
    values = []
    for column in columns:
        #if tuple → first value is CSV column name
        source = column[0] if isinstance(column, tuple) else column
        value = row[source]
        #convert empty string to NULL
        values.append(None if value == "" else value)
    return values

#insert a batch of rows into a table 
def insert_batch(cursor, table, columns, batch):
    names = column_names(columns)
    # %s for each column
    placeholders = ", ".join(["%s"] * len(names))
    column_list = ", ".join(names)
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
    #insert many rows at once for efficiency
    cursor.executemany(sql, batch)

#load a CSV file into a database table 
def load_csv(cursor, filename, table, columns):
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required data file: {path}")

    count = 0
    batch = []
    #open CSV file
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            batch.append(row_values(row, columns))
            #insert in batches for efficienct
            if len(batch) == BATCH_SIZE:
                insert_batch(cursor, table, columns, batch)
                count += len(batch)
                batch = []
    #insert remaining rows
    if batch:
        insert_batch(cursor, table, columns, batch)
        count += len(batch)
    print(f"Loaded {count:>6} rows into {table}")

#add some sample reservation data 
def add_demo_reservations(cursor):
    reservations = [
        ("2025-10-04", "1000", 1, "PLNEDAB43C9", "1A", "John Smith", "2145550101"),
        ("2025-10-04", "1000", 1, "PLNEDAB43C9", "1B", "Priya Narayan", "2145550102"),
        ("2025-10-04", "1000", 2, "PLNEDAB43C9", "1A", "John Smith", "2145550101"),
        ("2025-10-04", "1000", 2, "PLNEDAB43C9", "1C", "Maria Garcia", "2145550103"),
    ]
    #INSERT IGNORE avoids duplicate errors 
    cursor.executemany("""
        INSERT IGNORE INTO RESERVATION
        (Date, Number, Leg_no, Airplane_id, Seat_no, Customer_name, Cphone)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, reservations)
    print(f"Loaded {len(reservations):>6} rows into RESERVATION")

#main function 
#controls entire workflow 
def main():
    config = prompt_for_password_if_needed(read_config())
    try:
        #connect to mySQL server
        conn = connect_without_database(config)
    except Error as exc:
        print(f"[ERROR] Could not connect to MySQL: {exc}")
        print("\nCheck config.ini, or rerun and enter the MySQL password for that user.")
        sys.exit(1)

    try:
        cursor = conn.cursor()
        #creating tables
        run_schema(cursor)
        #select database
        conn.database = config["database"]
        #load all CSV files in order
        for filename, table, columns in LOAD_ORDER:
            load_csv(cursor, filename, table, columns)
        #adding sample data
        add_demo_reservations(cursor)
        #saving changes
        conn.commit()
    except Error as exc:
        #undo changes if error
        conn.rollback()
        print(f"[ERROR] Database setup failed: {exc}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    print("\nDatabase setup complete.")

#run program 
if __name__ == "__main__":
    main()
