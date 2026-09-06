"""
CrediFlow SQLite Database Module
Persists audit runs, benchmark results, human gate decisions, and notice dispatches to disk.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

def _get_db_path() -> str:
    if os.environ.get("VERCEL"):
        return "/tmp/crediflow.db"
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/crediflow.db"))
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        return local_path
    except Exception:
        return "/tmp/crediflow.db"

DB_PATH = _get_db_path()


def get_connection() -> sqlite3.Connection:
    db_path = _get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema with audit, benchmark, gate, and notice tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benchmark_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        count INTEGER NOT NULL,
        runtime_ms REAL NOT NULL,
        throughput_per_sec REAL NOT NULL,
        total_exposure_inr REAL NOT NULL,
        discrepancies_count INTEGER NOT NULL,
        cost_usd REAL NOT NULL,
        cost_inr REAL NOT NULL,
        retries INTEGER NOT NULL DEFAULT 0,
        escalations INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        supplier_gstin TEXT NOT NULL,
        itc_exposure_rupees REAL NOT NULL,
        mismatch_type TEXT NOT NULL,
        execution_engine TEXT NOT NULL,
        root_cause_code TEXT,
        audit_verdict TEXT,
        requires_human_review INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS human_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gate_id TEXT NOT NULL UNIQUE,
        invoice_number TEXT NOT NULL,
        decision TEXT NOT NULL,
        decided_by TEXT NOT NULL,
        note TEXT,
        decided_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notice_dispatches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        channel TEXT NOT NULL,
        pdf_path TEXT NOT NULL,
        status TEXT NOT NULL,
        dispatched_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def log_benchmark_run(metrics: Dict[str, Any]) -> int:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO benchmark_runs (
        run_id, count, runtime_ms, throughput_per_sec, total_exposure_inr,
        discrepancies_count, cost_usd, cost_inr, retries, escalations, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics.get("run_id", "run-1"),
        metrics.get("count", 1000),
        metrics.get("runtime_ms", 0.0),
        metrics.get("throughput_per_sec", 0.0),
        metrics.get("total_exposure_inr", 0.0),
        metrics.get("discrepancies_count", 0),
        metrics.get("cost_usd", 0.0),
        metrics.get("cost_inr", 0.0),
        metrics.get("retries", 0),
        metrics.get("escalations", 0),
        now
    ))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def log_human_decision(gate_id: str, invoice_number: str, decision: str, decided_by: str, note: Optional[str] = None):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT OR REPLACE INTO human_decisions (gate_id, invoice_number, decision, decided_by, note, decided_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (gate_id, invoice_number, decision, decided_by, note, now))
    conn.commit()
    conn.close()


def log_notice_dispatch(invoice_number: str, supplier_name: str, channel: str, pdf_path: str, status: str = "DISPATCHED"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO notice_dispatches (invoice_number, supplier_name, channel, pdf_path, status, dispatched_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (invoice_number, supplier_name, channel, pdf_path, status, now))
    conn.commit()
    conn.close()


def get_db_summary() -> Dict[str, Any]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    bench_count = cursor.execute("SELECT COUNT(*) FROM benchmark_runs").fetchone()[0]
    audit_count = cursor.execute("SELECT COUNT(*) FROM audit_ledger").fetchone()[0]
    decision_count = cursor.execute("SELECT COUNT(*) FROM human_decisions").fetchone()[0]
    notice_count = cursor.execute("SELECT COUNT(*) FROM notice_dispatches").fetchone()[0]
    
    last_bench = cursor.execute("SELECT * FROM benchmark_runs ORDER BY id DESC LIMIT 1").fetchone()
    last_bench_dict = dict(last_bench) if last_bench else None
    conn.close()
    
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "db_path": DB_PATH,
        "database_path": DB_PATH,
        "database_exists": os.path.exists(DB_PATH),
        "db_size_bytes": db_size,
        "database_size_bytes": db_size,
        "tables": {
            "benchmark_runs": bench_count,
            "audit_ledger": audit_count,
            "human_decisions": decision_count,
            "notice_dispatches": notice_count,
        },
        "latest_benchmark": last_bench_dict,
        "last_benchmark": last_bench_dict
    }
