# db_utils.py
import sqlite3
import logging
from config import DB_FILE

def init_db():
    """Initialize the database and create the conversations table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create a table to store conversations if it doesn't already exist
    c.execute('''CREATE TABLE IF NOT EXISTS conversations 
                 (session_id TEXT, session_name TEXT, role TEXT, content TEXT)''')
    conn.commit()
    return conn, c

def store_message_in_db(session_id, session_name, role, content):
    """Store a conversation message in the database."""
    try:
        conn, c = init_db()
        c.execute("INSERT INTO conversations (session_id, session_name, role, content) VALUES (?, ?, ?, ?)",
                  (session_id, session_name, role, content))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error storing message: {e}")

def retrieve_messages_from_db(session_id):
    """Retrieve all messages for a given session ID."""
    try:
        conn, c = init_db()
        c.execute("SELECT role, content FROM conversations WHERE session_id=?", (session_id,))
        rows = c.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        logging.error(f"Error retrieving messages: {e}")
        return []

def retrieve_session_names():
    """Retrieve all session names and IDs."""
    try:
        conn, c = init_db()
        c.execute("SELECT DISTINCT session_id, session_name FROM conversations")
        rows = c.fetchall()  # Fetch all session names
        conn.close()
        return rows
    except sqlite3.Error as e:
        logging.error(f"Error retrieving session names: {e}")
        return []

def delete_session_from_db(session_id):
    """Delete a session from the database."""
    try:
        conn, c = init_db()
        c.execute("DELETE FROM conversations WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error deleting session: {e}")

def delete_all_sessions_from_db():
    """Delete all sessions from the database."""
    try:
        conn, c = init_db()
        c.execute("DELETE FROM conversations")
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error deleting all sessions: {e}")
