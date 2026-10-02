#!/usr/bin/env python
"""Level-2 synthetic target: Bootstrap-heavy DOM with mixed surfaces.

Vulnerable: ``/products?category=&sort=`` (SQL concat) and POST ``/contact``
(static CSRF token + trusted hidden ``account_id``). Negative control:
``/directory?email=`` uses a parameterized query and escaped output.
"""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Any

from flask import Flask, request
from markupsafe import escape

app = Flask(__name__)

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_SORT_ALLOWLIST: frozenset[str] = frozenset({"name", "price"})
_STATIC_CSRF = "fixed-token-0001"

_BOOTSTRAP = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
)

_SVG_CART = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
     class="bi bi-cart" viewBox="0 0 16 16" aria-hidden="true">
  <path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1
  .49.598l-1.5 8A.5.5 0 0 1 13 12H4a.5.5 0 0 1-.491-.408L1.01 3.607 0.61 2H.5a.5.5
  0 0 1-.5-.5zM3.102 4l1.313 7h8.17l1.313-7H3.102zM5 14a1 1 0 1 0 0 2 1 1 0 0 0
  0-2zm7 1a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
</svg>
"""

_PRODUCTS: tuple[tuple[str, str, int], ...] = (
    ("gifts", "Tech gifts", 12),
    ("gifts", "Travel gifts", 9),
    ("home", "Lamp", 40),
    ("home", "Chair", 85),
    ("pets", "Leash", 15),
)


def _product_db() -> sqlite3.Connection:
    """Return an in-memory products table."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE products (category TEXT, name TEXT, price INTEGER)"
    )
    conn.executemany("INSERT INTO products VALUES (?, ?, ?)", _PRODUCTS)
    return conn


def _staff_db() -> sqlite3.Connection:
    """Return an in-memory directory used by the safe lookup."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE staff (email TEXT, name TEXT)")
    conn.execute(
        "INSERT INTO staff VALUES ('user@example.local', 'Directory User')"
    )
    return conn


def _svg_grid(count: int) -> str:
    """Repeat small SVG icons to add presentation noise."""
    return "".join(_SVG_CART for _ in range(count))


def _nav_items(count: int) -> str:
    """Build a dense multi-level navbar."""
    dropdowns: list[str] = []
    for i in range(count):
        links = "".join(
            f'<li><a class="dropdown-item" href="/page/{i}-{j}">Topic {i}.{j}</a></li>'
            for j in range(4)
        )
        dropdowns.append(
            f"""
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                Dept {i}
              </a>
              <ul class="dropdown-menu">{links}</ul>
            </li>
            """
        )
    return "".join(dropdowns)


def _product_cards(count: int) -> str:
    """Repeat Bootstrap cards for token padding."""
    cards: list[str] = []
    for i in range(count):
        cards.append(
            f"""
            <div class="col-md-3 mb-3">
              <div class="card h-100">
                <div class="card-body">
                  <h5 class="card-title">Featured item {i}</h5>
                  <p class="card-text">Seasonal copy block {i} describing
                  shipping windows, gift wrap, and warehouse routing notes
                  that are purely presentational padding for the DOM.</p>
                  <a class="btn btn-outline-secondary" href="/promo/{i}">Details</a>
                </div>
              </div>
            </div>
            """
        )
    return "".join(cards)


def _footer_clutter() -> str:
    """Wide footer with many inert links."""
    columns: list[str] = []
    for col in range(4):
        links = "".join(
            f'<li><a href="/legal/{col}-{n}">Policy {col}.{n}</a></li>'
            for n in range(5)
        )
        columns.append(
            f"<div class=\"col-md-3\"><h6>Column {col}</h6><ul>{links}</ul></div>"
        )
    return f"<footer class=\"bg-light p-4 mt-5\"><div class=\"row\">{''.join(columns)}</div></footer>"


def _shell(title: str, inner: str) -> str:
    """Bootstrap 5 document chrome with navbar, icons, and footer."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="{_BOOTSTRAP}">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">{_svg_grid(2)} ShopLevel2</a>
    <ul class="navbar-nav me-auto">
      <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
      <li class="nav-item"><a class="nav-link" href="/products?category=gifts&amp;sort=name">Products</a></li>
      <li class="nav-item"><a class="nav-link" href="/directory?email=user@example.local">Directory</a></li>
      {_nav_items(2)}
    </ul>
    {_svg_grid(2)}
  </div>
</nav>
<main class="container py-4">{inner}</main>
{_footer_clutter()}
</body>
</html>
"""


def _filter_panel(category: str, sort: str) -> str:
    """GET filter form plus parameterized category links."""
    cat = escape(category)
    srt = escape(sort)
    return f"""
    <form class="row g-2 mb-4" action="/products" method="GET">
      <div class="col-md-4">
        <label class="form-label">Category
          <input class="form-control" type="text" name="category" value="{cat}">
        </label>
      </div>
      <div class="col-md-4">
        <label class="form-label">Sort
          <select class="form-select" name="sort">
            <option value="name" {"selected" if sort == "name" else ""}>Name</option>
            <option value="price" {"selected" if sort == "price" else ""}>Price</option>
          </select>
        </label>
      </div>
      <div class="col-md-4 d-flex align-items-end">
        <button class="btn btn-primary" type="submit">Filter</button>
      </div>
    </form>
    <p>
      <a href="/products?category=gifts&amp;sort=name">Gifts</a>
      <a href="/products?category=home&amp;sort=price">Home</a>
      <a href="/products?category=pets&amp;sort=name">Pets</a>
    </p>
    """


def _contact_form() -> str:
    """Contact form with a static CSRF token and trusted hidden account id."""
    return f"""
    <form action="/contact" method="POST" class="mb-4">
      <input type="hidden" name="csrf_token" value="{_STATIC_CSRF}">
      <input type="hidden" name="account_id" value="42">
      <div class="mb-2">
        <label>Message <textarea class="form-control" name="message"></textarea></label>
      </div>
      <button class="btn btn-secondary" type="submit">Send</button>
    </form>
    """


def _directory_form(email: str) -> str:
    """Negative-control lookup form (validated email)."""
    return f"""
    <form action="/directory" method="GET" class="mb-4">
      <label>Staff email
        <input class="form-control" type="email" name="email" value="{escape(email)}">
      </label>
      <button class="btn btn-outline-primary" type="submit">Lookup</button>
    </form>
    """


@app.get("/")
def home() -> str:
    """Heavy homepage exposing products, contact, and directory surfaces."""
    inner = (
        "<h1>Storefront</h1>"
        + _filter_panel("gifts", "name")
        + "<h2>Contact</h2>"
        + _contact_form()
        + "<h2>Staff directory</h2>"
        + _directory_form("user@example.local")
        + f'<div class="row">{_product_cards(3)}</div>'
        + _svg_grid(4)
    )
    return _shell("Storefront", inner)


@app.get("/products")
def products() -> str:
    """Filter products by concatenating ``category`` into SQL (CWE-89)."""
    category = request.args.get("category", "gifts")
    sort = request.args.get("sort", "name")
    order = sort if sort in _SORT_ALLOWLIST else "name"
    conn = _product_db()
    try:
        rows: list[Any] = conn.execute(
            f"SELECT name, price FROM products WHERE category = '{category}' "
            f"ORDER BY {order}"
        ).fetchall()
        err = ""
    except sqlite3.Error as exc:
        rows = []
        err = str(exc)
    finally:
        conn.close()
    items = "".join(f"<li>{escape(str(r[0]))} — {escape(str(r[1]))}</li>" for r in rows)
    err_html = f"<pre>{escape(err)}</pre>" if err else ""
    inner = (
        "<h1>Products</h1>"
        + _filter_panel(category, sort)
        + err_html
        + f"<ul>{items or '<li>no matches</li>'}</ul>"
        + f'<div class="row">{_product_cards(4)}</div>'
    )
    return _shell("Products", inner)


@app.post("/contact")
def contact() -> str:
    """Accept a static CSRF token and client-supplied ``account_id`` (CWE-352)."""
    token = request.form.get("csrf_token", "")
    account_id = request.form.get("account_id", "")
    message = request.form.get("message", "")
    inner = (
        "<h1>Message queued</h1>"
        f"<p>csrf accepted: {escape(token)}</p>"
        f"<p>routed to account_id={escape(account_id)} without server-side CSRF "
        "rotation or ownership checks.</p>"
        f"<p>length={len(message)}</p>"
        "<p><a href=\"/\">Home</a></p>"
    )
    return _shell("Contact", inner)


@app.get("/directory")
def directory() -> str:
    """Look up staff by allowlisted email with a bound parameter (safe)."""
    email = request.args.get("email", "")
    if not _EMAIL_RE.match(email):
        inner = (
            "<h1>Directory</h1><p>Enter a valid email address.</p>"
            + _directory_form(email)
        )
        return _shell("Directory", inner)
    conn = _staff_db()
    try:
        row = conn.execute(
            "SELECT name, email FROM staff WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        result = "<p>No directory entry.</p>"
    else:
        result = f"<p>{escape(str(row[0]))} &lt;{escape(str(row[1]))}&gt;</p>"
    inner = "<h1>Directory</h1>" + _directory_form(email) + result
    return _shell("Directory", inner)


def main() -> None:
    """Run the development server on PORT (default 5002)."""
    port = int(os.environ.get("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
