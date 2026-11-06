# -*- coding: utf-8 -*-
"""Export absensi -> JSON (data feed for dashboard web).

Reads database_testing.db (DEV) or database_absensi.db (PROD), joins the
absensi table with the users table, sorts newest first, and writes
absensi_data.json that the dashboard web page can fetch.
"""

import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DEV = os.path.join(BASE_DIR, "database_testing.db")
DB_PROD = os.path.join(BASE_DIR, "database_absensi.db")
OUT_JSON = os.path.join(BASE_DIR, "absensi_data.json")

STATUS_RANK = {"Hadir": 0, "Sakit": 1, "Izin": 1, "Lembur": 2, "Lembur Libur": 2}


def pick_db():
    if os.path.exists(DB_DEV):
        return DB_DEV, "database_testing.db"
    if os.path.exists(DB_PROD):
        return DB_PROD, "database_absensi.db"
    raise SystemExit("Tidak menemukan database (database_testing.db / database_absensi.db).")


def load(conn):
    cur = conn.cursor()
    cur.execute("SELECT user_id, nama, divisi, shift FROM users")
    users = {row[0]: {"nama": row[1], "divisi": row[2], "shift": row[3]} for row in cur.fetchall()}

    cur.execute("SELECT id, user_id, tanggal, status, waktu_masuk, waktu_pulang, mulai_lembur, selesai_lembur FROM absensi")
    raw = cur.fetchall()
    cols = ["id", "user_id", "tanggal", "status", "waktu_masuk", "waktu_pulang", "mulai_lembur", "selesai_lembur"]
    entries = []
    for row in raw:
        d = dict(zip(cols, row))
        u = users.get(d["user_id"], {})
        entries.append({
            "id": d["id"],
            "user_id": d["user_id"],
            "nama": u.get("nama", "—"),
            "divisi": u.get("divisi", "—"),
            "shift": u.get("shift", "—"),
            "tanggal": d["tanggal"],
            "status": d["status"],
            "waktu_masuk": d["waktu_masuk"],
            "waktu_pulang": d["waktu_pulang"],
        })
    entries.sort(key=lambda e: str(e.get("id", "")), reverse=True)
    return entries


def main():
    db_path, db_name = pick_db()
    conn = sqlite3.connect(db_path)
    try:
        entries = load(conn)
    finally:
        conn.close()

    payload = {
        "updated_at": "auto-export-" + os.path.splitext(db_name)[0],
        "db": db_name,
        "entries": entries,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("OK: exported %d entries -> %s" % (len(entries), OUT_JSON))


if __name__ == "__main__":
    main()
