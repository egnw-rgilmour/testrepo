"""A simple notes API using FastAPI and SQLite."""

import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "notes.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the notes table on startup if it doesn't exist
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
    yield


app = FastAPI(title="Notes API", lifespan=lifespan)


class NoteIn(BaseModel):
    content: str


class NoteOut(BaseModel):
    id: int
    content: str
    created_at: str


@app.post("/notes", response_model=NoteOut, status_code=201)
def create_note(note: NoteIn):
    with get_db() as conn:
        cur = conn.execute("INSERT INTO notes (content) VALUES (?)", (note.content,))
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.get("/notes/count")
def count_notes():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    return {"count": count}


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return dict(row)


@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note: NoteIn):
    with get_db() as conn:
        cur = conn.execute("UPDATE notes SET content = ? WHERE id = ?", (note.content, note_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row)


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
