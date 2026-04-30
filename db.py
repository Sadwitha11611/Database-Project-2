"""Database connection manager for the Airport Management System."""

from configparser import ConfigParser
from pathlib import Path
import getpass
import sys

try:
    import mysql.connector
    from mysql.connector import Error
except ModuleNotFoundError:
    mysql = None
    Error = Exception


CONFIG_PATH = Path(__file__).with_name("config.ini")
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": "3306",
    "user": "root",
    "password": "",
    "database": "airport_db",
}


def _read_config():
    """Read database settings from config.ini, falling back to local defaults."""
    config = DEFAULT_CONFIG.copy()
    parser = ConfigParser()
    if CONFIG_PATH.exists():
        parser.read(CONFIG_PATH)
        if parser.has_section("database"):
            config.update({key: value for key, value in parser.items("database")})
    config["port"] = int(config["port"])
    return config


def _prompt_for_password_if_needed(config):
    if config.get("password") or not sys.stdin.isatty():
        return config

    config = config.copy()
    user = config.get("user", "root")
    host = config.get("host", "localhost")
    config["password"] = getpass.getpass(f"MySQL password for {user}@{host}: ")
    return config


def get_connection(host=None, port=None, user=None, password=None, database=None):
    """Create and return a MySQL database connection."""
    if mysql is None:
        print("[ERROR] Missing Python package: mysql-connector-python")
        print("Install it with: python3 -m pip install -r requirements.txt")
        sys.exit(1)

    config = _read_config()
    if host is not None:
        config["host"] = host
    if port is not None:
        config["port"] = port
    if user is not None:
        config["user"] = user
    if password is not None:
        config["password"] = password
    if database is not None:
        config["database"] = database
    config = _prompt_for_password_if_needed(config)

    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[ERROR] Could not connect to MySQL: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL is running")
        print(f"  2. The database '{config['database']}' exists")
        print(f"  3. Your credentials in {CONFIG_PATH.name} are correct")
        sys.exit(1)


def close_connection(conn, cursor=None):
    """Safely close cursor and connection."""
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
