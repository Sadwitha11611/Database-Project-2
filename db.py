"""
db.py - Database connection manager for Airport Management System
CS-4347 Database Systems - Milestone 2
"""

import mysql.connector
from mysql.connector import Error
import sys


def get_connection(host='localhost', port=3306, user='root', password='', database='airport_db'):
    """
    Create and return a MySQL database connection.
    Reads from config if available, otherwise uses provided defaults.
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[ERROR] Could not connect to MySQL: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL is running")
        print("  2. The database 'airport_db' exists (run setup.py first)")
        print("  3. Your credentials in config.ini are correct")
        sys.exit(1)


def close_connection(conn, cursor=None):
    """Safely close cursor and connection."""
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
