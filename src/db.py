"""Reusable MySQL helpers for Emergency Resource Management."""
import os
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load local .env settings when present; environment variables still take precedence.
load_dotenv()


def get_connection():
    """Create a new connection using environment variables."""
    config = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "emergency_resource_db"),
        "connection_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
    }
    try:
        return mysql.connector.connect(**config)
    except Error as exc:
        raise RuntimeError(
            "Could not connect to MySQL. Check that MySQL is running and "
            "DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME are correct."
        ) from exc


@contextmanager
def cursor(*, dictionary=True):
    """Yield a cursor and always close its cursor and connection."""
    conn = get_connection()
    cur = None
    try:
        cur = conn.cursor(dictionary=dictionary)
        yield conn, cur
    finally:
        if cur is not None:
            cur.close()
        conn.close()


def fetch_all(query, params=()):
    with cursor() as (_, cur):
        cur.execute(query, params)
        return cur.fetchall()


def fetch_one(query, params=()):
    with cursor() as (_, cur):
        cur.execute(query, params)
        return cur.fetchone()


def execute_write(query, params=()):
    """Run one write statement and return its generated ID (or None)."""
    with cursor() as (conn, cur):
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid
