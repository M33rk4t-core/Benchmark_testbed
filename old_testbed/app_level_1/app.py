#!/usr/bin/env python
"""Level-1 synthetic target: shallow DOM, two vulns, one clean page.

Reflected XSS on ``/search?q=`` and a SQLite string-concat SQLi simulation on
``/user?id=``. ``/about`` is a static negative control.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from flask import Flask, request

app = Flask(__name__)

_USERS: tuple[tuple[int, str, str], ...] = (
    (1, "alice", "alice@example.local"),
    (2, "bob", "bob@example.local"),
    (3, "carol", "carol@example.local"),
)


def _user_db() -> sqlite3.Connection:
    """Return an in-memory users table for the SQLi simulation."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT, email TEXT)")
    conn.executemany("INSERT INTO users VALUES (?, ?, ?)", _USERS)
    return conn


def _layout(title: str, body: str) -> str:
    """Wrap ``body`` in a minimal HTML document."""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{title}</title></head><body>{body}</body></html>"
    )


@app.get("/")
def home() -> str:
    """Landing page exposing the search form and parameterized user links."""
    body = """
    <h1>Catalog</h1>
    <form action="/search" method="GET">
      <label>Search <input type="text" name="q" value=""></label>
      <button type="submit">Go</button>
    </form>
    <ul>
      <li><a href="/user?id=1">Alice</a></li>
      <li><a href="/user?id=2">Bob</a></li>
      <li><a href="/user?id=3">Carol</a></li>
    </ul>
    <p><a href="/about">About</a></p>
    """
    return _layout("Catalog", body)


@app.get("/search")
def search() -> str:
    """Reflect ``q`` without encoding (CWE-79)."""
    q = request.args.get("q", "")
    body = (
        "<h1>Search</h1>"
        f"<p>You searched for: {q}</p>"
        "<form action=\"/search\" method=\"GET\">"
        f"<input type=\"text\" name=\"q\" value=\"{q}\">"
        "<button type=\"submit\">Search</button></form>"
        "<p><a href=\"/\">Home</a></p>"
    )
    return _layout("Search", body)


@app.get("/user")
def user() -> str:
    """Concatenate ``id`` into SQL (CWE-89 simulation)."""
    user_id = request.args.get("id", "1")
    conn = _user_db()
    try:
        rows: list[Any] = conn.execute(
            f"SELECT id, name, email FROM users WHERE id = {user_id}"
        ).fetchall()
        err = ""
    except sqlite3.Error as exc:
        rows = []
        err = str(exc)
    finally:
        conn.close()
    items = "".join(
        f"<li>{row[0]} {row[1]} {row[2]}</li>" for row in rows
    ) or "<li>no rows</li>"
    error_html = f"<pre>{err}</pre>" if err else ""
    body = (
        "<h1>User lookup</h1>"
        f"{error_html}<ul>{items}</ul>"
        "<p><a href=\"/user?id=1\">id=1</a> "
        "<a href=\"/user?id=2\">id=2</a></p>"
        "<p><a href=\"/\">Home</a></p>"
    )
    return _layout("User", body)


@app.get("/about")
def about() -> str:
    """Static page with no injectable parameters."""
    body = (
        "<h1>About</h1>"
        "<p>This catalog is a synthetic DOM-pruner fixture.</p>"
        "<p><a href=\"/\">Home</a></p>"
    )
    return _layout("About", body)


def main() -> None:
    """Run the development server on PORT (default 5001)."""
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
