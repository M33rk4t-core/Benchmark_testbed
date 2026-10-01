import os
from html import escape

import pymysql
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Waybill Desk")


def connect():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "bench"),
        password=os.environ.get("DB_PASSWORD", "bench-local-only"),
        database=os.environ.get("DB_NAME", "waybill"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def page(title: str, body: str) -> str:
    css = (
        "body{margin:0;background:#f7f1e8;color:#243044;font:18px/1.45 'Segoe UI',sans-serif}"
        "main{max-width:36rem;margin:0 auto;padding:2rem 1.2rem}"
        ".mark{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:#d85a30}"
        "h1{font-weight:560;font-size:1.8rem}"
        "form{display:flex;gap:.6rem;align-items:end;flex-wrap:wrap}"
        "label{display:flex;flex-direction:column;font-size:.85rem;gap:.25rem}"
        "input,button{font:inherit}input{border:1px solid #243044;padding:.4rem .5rem;background:#fff}"
        "button{background:#243044;color:#fff;border:0;padding:.5rem .8rem}"
        "li{padding:.45rem 0;border-top:1px solid #e2d8cb;list-style:none}"
        "ul{padding:0} .code{font-weight:650}"
    )
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"robots\" content=\"noindex\"><title>"
        + escape(title)
        + "</title><style>"
        + css
        + "</style></head><body><main>"
        + body
        + "</main></body></html>"
    )


@app.get("/", response_class=HTMLResponse)
def home():
    body = (
        "<p class=\"mark\">Waybill Desk</p><h1>Shipment lookup</h1>"
        "<p>The desk answers with the dock copy for a tracking code.</p>"
        "<p><a href=\"/track\">Open the desk</a></p>"
    )
    return page("Waybill Desk", body)


@app.get("/track", response_class=HTMLResponse)
def track(
    code: str = "",
    limit: int = Query(default=8, ge=1, le=20),
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            if code:
                # Double percent signs so the driver keeps them as LIKE wildcards.
                driver_code = code.replace("%", "%%")
                cur.execute(
                    "SELECT tracking_code, origin_city, dest_city, status_label, booked_on "
                    "FROM wb_shipments WHERE tracking_code LIKE '%%"
                    + driver_code
                    + "%%' ORDER BY booked_on DESC LIMIT %s",
                    (limit,),
                )
            else:
                cur.execute(
                    "SELECT tracking_code, origin_city, dest_city, status_label, booked_on "
                    "FROM wb_shipments ORDER BY booked_on DESC LIMIT %s",
                    (limit,),
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    items = []
    for row in rows:
        items.append(
            "<li><span class=\"code\">"
            + escape(str(row["tracking_code"]))
            + "</span> "
            + escape(str(row["origin_city"]))
            + " to "
            + escape(str(row["dest_city"]))
            + " · "
            + escape(str(row["status_label"]))
            + " · "
            + escape(str(row["booked_on"]))
            + "</li>"
        )
    listing = "".join(items) or "<li>No dock copy matches that code.</li>"
    body = (
        "<p class=\"mark\">Waybill Desk</p><h1>Dock copy</h1>"
        "<form method=\"get\" action=\"/track\">"
        "<label>Tracking code <input name=\"code\" value=\""
        + escape(code, quote=True)
        + "\"></label>"
        "<label>Limit <input name=\"limit\" value=\""
        + str(limit)
        + "\" inputmode=\"numeric\"></label>"
        "<button type=\"submit\">Find</button></form><ul>"
        + listing
        + "</ul>"
    )
    return page("Waybill Desk", body)
