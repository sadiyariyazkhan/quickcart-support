import csv
import json
import sqlite3
import secrets
import re
from contextlib import contextmanager
from .config import DB_PATH, ORDERS_CSV
from .language import mask_mobile

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Orders Table (from CSV)
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY, customer_name TEXT, mobile TEXT, city TEXT,
        item TEXT, category TEXT, amount_inr REAL, payment_method TEXT,
        order_date TEXT, promised_date TEXT, status TEXT)""")

    # Load CSV if empty
    count = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if count == 0:
        with open(ORDERS_CSV, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          tuple(row.values()))

    # Tickets Table
    c.execute("""CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY, session_id TEXT,
        name TEXT, mobile TEXT, order_id TEXT,
        issue TEXT, summary TEXT, category TEXT,
        status TEXT DEFAULT 'Open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # Sessions Table (State persistence)
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        state TEXT NOT NULL,
        escalated INTEGER DEFAULT 0,
        language TEXT DEFAULT 'en',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # Turns Table (for GET /sessions/{id})
    c.execute("""CREATE TABLE IF NOT EXISTS turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, role TEXT, text TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# --- Orders (CSV Validation) ---
def get_order(order_id: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
        return dict(row) if row else None

def validate_order_owner(order_id: str, mobile: str):
    """TASK.md §1a: must exist in CSV AND belong to mobile."""
    order = get_order(order_id)
    if not order:
        return False, "I couldn't find that order ID. Please check and try again."
    if order["mobile"] != mobile:
        return False, "That order does not belong to this mobile number. (§9.2)"
    return True, order

# --- Tickets ---
def create_ticket(session_id, name, mobile, order_id, issue, summary, category):
    ticket_id = "TKT-" + "".join(secrets.choice("0123456789") for _ in range(6))
    with get_db() as db:
        db.execute("""INSERT INTO tickets
            (ticket_id, session_id, name, mobile, order_id, issue, summary, category)
            VALUES (?,?,?,?,?,?,?,?)""",
            (ticket_id, session_id, name, mobile, order_id, issue, summary, category))
    return ticket_id

def get_ticket(ticket_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        return dict(row) if row else None

def list_tickets(category=None, status=None, page=1, page_size=20):
    q = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if category: q += " AND category=?"; params.append(category)
    if status:   q += " AND status=?";   params.append(status)
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [page_size, (page - 1) * page_size]
    with get_db() as db:
        rows = db.execute(q, params).fetchall()
        total = db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    return [dict(r) for r in rows], total

# --- Sessions ---
def get_state(session_id):
    with get_db() as db:
        row = db.execute("SELECT state FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        return json.loads(row["state"]) if row else None

def save_state(session_id, state, escalated=False, language="en"):
    with get_db() as db:
        db.execute("""INSERT INTO sessions (session_id, state, escalated, language)
                      VALUES (?,?,?,?)
                      ON CONFLICT(session_id) DO UPDATE SET
                        state=excluded.state, escalated=excluded.escalated,
                        language=excluded.language, updated_at=CURRENT_TIMESTAMP""",
                   (session_id, json.dumps(state), int(escalated), language))

def log_turn(session_id, role, text):
    # TASK.md §4: Mask mobile numbers in logs
    text = re.sub(r"\b[6-9]\d{9}\b", lambda m: mask_mobile(m.group(0)), text)
    with get_db() as db:
        db.execute("INSERT INTO turns (session_id, role, text) VALUES (?,?,?)",
                   (session_id, role, text))

def get_turns(session_id):
    with get_db() as db:
        rows = db.execute("SELECT role, text, timestamp FROM turns WHERE session_id=? ORDER BY id",
                          (session_id,)).fetchall()
    return [dict(r) for r in rows]