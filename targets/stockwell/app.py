import os
from decimal import Decimal

import pymysql
from flask import Flask, render_template, request

app = Flask(__name__)
PER_PAGE = 8
ALLOWED_STATUS = ("in_service", "in_repair", "surplus", "archived")


def connect():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "bench"),
        password=os.environ.get("DB_PASSWORD", "bench-local-only"),
        database=os.environ.get("DB_NAME", "stockwell"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def sql_literal(conn, value: str) -> str:
    return "'" + conn.escape_string(value) + "'"


def parse_page(raw: str) -> int:
    if isinstance(raw, str) and raw.isdigit():
        page = int(raw)
        if 1 <= page <= 200:
            return page
    return 1


def money(value) -> str:
    return f"{Decimal(value or 0):.2f}"


def allocations(book_value: str):
    amount = Decimal(book_value)
    splits = (("General fund", "0.60"), ("Works fund", "0.25"), ("Reserve", "0.15"))
    return [
        {"fund": name, "share": f"{(amount * Decimal(rate)).quantize(Decimal('0.01')):.2f}"}
        for name, rate in splits
    ]


@app.get("/")
def home():
    return render_template("home.html", title="Stockwell Register")


@app.get("/holdings")
def holdings():
    order = request.args.get("order", "")
    if not isinstance(order, str) or order == "":
        order = "asset_tag"
    status = request.args.get("status", "")
    if status not in ALLOWED_STATUS:
        status = ""
    term = request.args.get("q", "")
    if not isinstance(term, str):
        term = ""
    page = parse_page(request.args.get("page", "1"))
    offset = (page - 1) * PER_PAGE
    rows = []
    summary = []
    error = ""
    conn = connect()
    try:
        where = ["1=1"]
        if status:
            where.append("status_label = " + sql_literal(conn, status))
        if term:
            like = "%" + term + "%"
            where.append(
                "(asset_name LIKE "
                + sql_literal(conn, like)
                + " OR asset_tag LIKE "
                + sql_literal(conn, like)
                + ")"
            )
        where_sql = " AND ".join(where)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status_label, COUNT(*) AS holdings, SUM(book_value) AS total_value "
                f"FROM sw_holdings WHERE {where_sql} GROUP BY status_label ORDER BY status_label"
            )
            summary = list(cur.fetchall())
            cur.execute(
                "SELECT asset_tag, asset_name, site_name, category_name, status_label, acquired_on, book_value "
                f"FROM sw_holdings WHERE {where_sql} ORDER BY {order} LIMIT {PER_PAGE} OFFSET {offset}"
            )
            rows = list(cur.fetchall())
    except pymysql.Error:
        error = "The register could not apply that sort."
        rows = []
        summary = []
    finally:
        conn.close()

    for band in summary:
        band["total_value"] = money(band["total_value"])
        band["holdings"] = int(band["holdings"])
    for row in rows:
        row["book_value"] = money(row["book_value"])
        row["acquired_on"] = row["acquired_on"].isoformat()
        row["allocations"] = allocations(row["book_value"])

    return render_template(
        "holdings.html",
        title="Holdings grid",
        order=order,
        term=term,
        status=status,
        page=page,
        statuses=ALLOWED_STATUS,
        summary=summary,
        rows=rows,
        error=error,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8086")), debug=False)
