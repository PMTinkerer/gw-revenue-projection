"""Projection log service for the GW revenue projection tool.

Serves the browser tool at / and persists every projection run (inputs,
address, computed outputs, and the exact assumption tables used) so past
projections sent to homeowners can always be looked up.

Runs on Railway: SQLite on a volume (DATA_DIR=/data), auth via a single
shared key (PROJECTIONS_API_KEY). See README "Projection log".
"""
import json
import logging
import os
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
log = logging.getLogger("projection-log")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", REPO_ROOT / "data"))
DB_PATH = DATA_DIR / "projections.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS projections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    address TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    bucket TEXT NOT NULL DEFAULT '',
    use_case TEXT NOT NULL DEFAULT '',
    framework_version TEXT NOT NULL DEFAULT '',
    inputs TEXT NOT NULL,
    outputs TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_projections_address ON projections(address);
CREATE INDEX IF NOT EXISTS idx_projections_created ON projections(created_at);
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
    log.info(f"projection log ready at {DB_PATH}")
    yield


app = FastAPI(title="GW Projection Log", lifespan=lifespan)

# The tool may be opened from file:// or another host; auth is the bearer
# key (no cookies), so a permissive CORS policy is safe here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def require_key(request: Request) -> None:
    expected = os.environ.get("PROJECTIONS_API_KEY", "")
    if not expected:
        raise HTTPException(503, "PROJECTIONS_API_KEY is not configured on the server")
    header = request.headers.get("authorization", "")
    token = header.removeprefix("Bearer ").strip()
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(401, "Invalid or missing API key")


class ProjectionIn(BaseModel):
    address: str = Field(min_length=3, max_length=300)
    label: str = ""
    bucket: str = ""
    use_case: str = ""
    framework_version: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


def _row_summary(r: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": r["id"],
        "created_at": r["created_at"],
        "address": r["address"],
        "label": r["label"],
        "bucket": r["bucket"],
        "use_case": r["use_case"],
        "framework_version": r["framework_version"],
        "inputs": json.loads(r["inputs"]),
        "notes": r["notes"],
    }


@app.get("/healthz")
async def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/projections", status_code=201)
async def create_projection(p: ProjectionIn, _: None = Depends(require_key)) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO projections (created_at, address, label, bucket, use_case,"
            " framework_version, inputs, outputs, notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (created_at, p.address.strip(), p.label.strip(), p.bucket, p.use_case,
             p.framework_version, json.dumps(p.inputs), json.dumps(p.outputs),
             p.notes.strip()),
        )
        await db.commit()
        log.info(f"saved projection id={cur.lastrowid} address={p.address.strip()!r}")
        return {"id": cur.lastrowid, "created_at": created_at}


@app.get("/api/projections")
async def list_projections(
    q: Optional[str] = Query(None, max_length=300),
    limit: int = Query(200, ge=1, le=1000),
    _: None = Depends(require_key),
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM projections"
    args: tuple = ()
    if q:
        sql += " WHERE address LIKE ? OR label LIKE ?"
        args = (f"%{q}%", f"%{q}%")
    sql += " ORDER BY id DESC LIMIT ?"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(sql, args + (limit,))
    return [_row_summary(r) for r in rows]


@app.get("/api/projections/{pid}")
async def get_projection(pid: int, _: None = Depends(require_key)) -> dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("SELECT * FROM projections WHERE id = ?", (pid,))
    if not rows:
        raise HTTPException(404, f"Projection {pid} not found")
    full = _row_summary(rows[0])
    full["outputs"] = json.loads(rows[0]["outputs"])
    return full


@app.delete("/api/projections/{pid}")
async def delete_projection(pid: int, _: None = Depends(require_key)) -> dict[str, bool]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM projections WHERE id = ?", (pid,))
        await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, f"Projection {pid} not found")
    log.info(f"deleted projection id={pid}")
    return {"deleted": True}


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(REPO_ROOT / "project_revenue.html", media_type="text/html")


@app.get("/project_revenue.html")
async def tool_page() -> FileResponse:
    return FileResponse(REPO_ROOT / "project_revenue.html", media_type="text/html")


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    log.error(f"unhandled error on {request.url.path}: {exc!r}")
    return JSONResponse({"detail": "internal error"}, status_code=500)
