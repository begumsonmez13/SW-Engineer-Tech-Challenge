from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import Optional

app = FastAPI()
DISPATCH_URL = "http://localhost:8000/series"
DB_PATH = "series.db"

# Initialize the SQL database
def init_db():
    conn = sqlite3.connect(DB_PATH) # Connection to database file (creates it if it doesn't exist)
    cur = conn.cursor() # Create a cursor object for SQL commands
    # SeriesInstanceUID is the unique identifier for the series
    cur.execute("""
    CREATE TABLE IF NOT EXISTS series (
        SeriesInstanceUID TEXT PRIMARY KEY,
        PatientID TEXT,
        PatientName TEXT,
        StudyInstanceUID TEXT,
        NumInstances INTEGER
    );
    """)
    conn.commit()
    conn.close()

init_db()


# API Server using FastAPI
app = FastAPI()

class SeriesMetadata(BaseModel):
    PatientID: Optional[str] = None
    PatientName: Optional[str] = None
    StudyInstanceUID: Optional[str] = None
    SeriesInstanceUID: str
    NumInstances: int

# Endpoint to receive series metadata sent over HTTP
@app.post("/series")
def receive_series(data: SeriesMetadata):
    # Upsert by SeriesInstanceUID
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # Here, if we have the same SeriesInstanceUID, we update the existing record
        # excluded. means use the value from the previous insert statement
        cur.execute("""
            INSERT INTO series (SeriesInstanceUID, PatientID, PatientName, StudyInstanceUID, NumInstances)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(SeriesInstanceUID) DO UPDATE SET
                PatientID=excluded.PatientID,
                PatientName=excluded.PatientName,
                StudyInstanceUID=excluded.StudyInstanceUID,
                NumInstances=excluded.NumInstances;
        """, (
            data.SeriesInstanceUID,
            data.PatientID,
            data.PatientName,
            data.StudyInstanceUID,
            data.NumInstances,
        ))
        conn.commit()
    finally:
        conn.close()
    print(f"Received series {data.SeriesInstanceUID} with {data.NumInstances} instances")
    return {"status": "ok"}

# List all series in the database - Diagnostics
@app.get("/series")
def list_series():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT SeriesInstanceUID, PatientID, PatientName, StudyInstanceUID, NumInstances FROM series ORDER BY rowid DESC")
        rows = cur.fetchall()
    finally:
        conn.close()
    return [
        {
            "SeriesInstanceUID": r[0],
            "PatientID": r[1],
            "PatientName": r[2],
            "StudyInstanceUID": r[3],
            "NumInstances": r[4],
        }
        for r in rows
    ]

# Additional endpoints for fetching metadata - Diagnostics
@app.get("/series/{series_uid}")
def get_series(series_uid: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT SeriesInstanceUID, PatientID, PatientName, StudyInstanceUID, NumInstances FROM series WHERE SeriesInstanceUID=?", (series_uid,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Series not found")
    return {
        "SeriesInstanceUID": row[0],
        "PatientID": row[1],
        "PatientName": row[2],
        "StudyInstanceUID": row[3],
        "NumInstances": row[4],
    }


