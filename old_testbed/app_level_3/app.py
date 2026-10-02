#!/usr/bin/env python
"""Level-3 synthetic target: nested enterprise chrome and data-* surfaces.

The dashboard exposes ``data-action`` / ``data-param`` widgets that POST
``role`` to ``/api/v1/update`` without authorization (parameter manipulation).
``/help`` is a clean negative control.
"""

from __future__ import annotations

import os
from typing import Any

from flask import Flask, jsonify, request
from markupsafe import escape

app = Flask(__name__)

_BOOTSTRAP = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
)
_ALLOWED_ROLES: frozenset[str] = frozenset({"viewer", "editor", "admin"})


def _modal(dept: int, card: int) -> str:
    """Nested modal markup used as layout padding."""
    mid = f"modal-{dept}-{card}"
    rows = "".join(
        f"<tr><td>metric-{dept}-{card}-{r}</td><td>{r * dept}</td>"
        f"<td>note {dept}.{card}.{r} audit trail placeholder</td></tr>"
        for r in range(3)
    )
    return f"""
    <div class="modal fade" id="{mid}" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header"><h5>Dept {dept} card {card}</h5></div>
          <div class="modal-body">
            <p>Capacity planning notes for org unit {dept} panel {card}. This
            copy exists so the raw DOM exceeds 10k tokens before pruning.</p>
            <table class="table table-sm"><tbody>{rows}</tbody></table>
          </div>
        </div>
      </div>
    </div>
    """


def _tab_panel(dept: int) -> str:
    """Tabbed card cluster for one department."""
    tabs = "".join(
        f"""
        <li class="nav-item">
          <button class="nav-link {"active" if t == 0 else ""}" data-bs-toggle="tab"
                  data-bs-target="#tab-{dept}-{t}">Pane {t}</button>
        </li>
        """
        for t in range(3)
    )
    panes = "".join(
        f"""
        <div class="tab-pane fade {"show active" if t == 0 else ""}" id="tab-{dept}-{t}">
          <div class="row">
            {''.join(
                f'''
                <div class="col-md-4">
                  <div class="card mb-3">
                    <div class="card-header">Widget {dept}.{t}.{c}</div>
                    <div class="card-body">
                      <p>KPI sparkline placeholder for department {dept}
                      tab {t} card {c}. Includes nested badges
                      <span class="badge bg-info">ok</span>
                      <span class="badge bg-warning">lag</span>.</p>
                      <button class="btn btn-sm btn-outline-dark"
                              data-bs-toggle="modal"
                              data-bs-target="#modal-{dept}-{c}">Open</button>
                    </div>
                  </div>
                </div>
                {_modal(dept, c)}
                '''
                for c in range(2)
            )}
          </div>
        </div>
        """
        for t in range(3)
    )
    return f"""
    <section class="mb-4">
      <h2>Department {dept}</h2>
      <ul class="nav nav-tabs">{tabs}</ul>
      <div class="tab-content border p-3">{panes}</div>
    </section>
    """


def _enterprise_clutter() -> str:
    """Heavy nested layout targeting 10k+ tokenizer tokens."""
    return "".join(_tab_panel(dept) for dept in range(4))


def _role_widget() -> str:
    """Non-standard markup that still carries an update endpoint and param."""
    return """
    <section class="alert alert-light">
      <h2>Access review</h2>
      <p>Role changes are submitted from this widget.</p>
      <div id="role-widget"
           data-action="/api/v1/update"
           data-param="role"
           data-method="POST"
           data-user="1"
           onclick="this.querySelector('form').submit()">
        <form action="/api/v1/update" method="POST">
          <input type="hidden" name="user_id" value="1">
          <label>Role
            <select name="role">
              <option value="viewer" selected>Viewer</option>
              <option value="editor">Editor</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button type="submit">Apply</button>
        </form>
      </div>
      <div data-action="/api/v1/update" data-param="role"
           data-user="2" onclick="fetch(this.dataset.action, {method:'POST',
           body: new URLSearchParams({user_id: this.dataset.user, role: 'admin'})})">
        Quick-promote user 2
      </div>
    </section>
    """


def _shell(title: str, inner: str) -> str:
    """Enterprise chrome wrapping ``inner``."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="{_BOOTSTRAP}">
</head>
<body>
<nav class="navbar navbar-dark bg-primary mb-3">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">Contoso Workspace</a>
    <a class="nav-link text-white" href="/help">Help</a>
  </div>
</nav>
<main class="container-fluid">{inner}</main>
</body>
</html>
"""


@app.get("/")
def home() -> str:
    """Dashboard with data-* update widgets plus nested layout noise."""
    inner = "<h1>Workspace</h1>" + _role_widget() + _enterprise_clutter()
    return _shell("Workspace", inner)


@app.post("/api/v1/update")
def update_role() -> tuple[Any, int]:
    """Trust client-supplied ``role`` with no authorization check (CWE-284)."""
    payload = request.get_json(silent=True) or {}
    role = (
        request.form.get("role")
        or request.args.get("role")
        or str(payload.get("role", ""))
    )
    user_id = (
        request.form.get("user_id")
        or request.args.get("user_id")
        or str(payload.get("user_id", "1"))
    )
    if role not in _ALLOWED_ROLES:
        role = "viewer"
    return jsonify(
        {
            "ok": True,
            "user_id": user_id,
            "role": role,
            "note": "role accepted from client without authorization",
        }
    ), 200


@app.get("/help")
def help_page() -> str:
    """Static help page with no injectable parameters."""
    inner = (
        "<h1>Help</h1>"
        "<p>Use the access review widget only from an authorized session.</p>"
        "<p><a href=\"/\">Home</a></p>"
    )
    return _shell("Help", inner)


def main() -> None:
    """Run the development server on PORT (default 5003)."""
    port = int(os.environ.get("PORT", "5003"))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
