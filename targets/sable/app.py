import os
from enum import Enum
from html import escape

import pymysql
import strawberry
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter

app = FastAPI(title="Sable Foundry")
PRESSES = {"harbor", "estuary", "ridge"}


def connect():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "bench"),
        password=os.environ.get("DB_PASSWORD", "bench-local-only"),
        database=os.environ.get("DB_NAME", "sable"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def clamp_edition(value: int) -> int:
    if value < 1:
        return 1
    if value > 30:
        return 30
    return value


def load_specimens(name: str, edition: int, press: str):
    if press not in PRESSES:
        press = "harbor"
    edition = clamp_edition(edition)
    conn = connect()
    try:
        with conn.cursor() as cur:
            if name:
                driver_name = name.replace("%", "%%")
                cur.execute(
                    "SELECT face_name, founder, cut_year, press_code FROM sb_specimens "
                    "WHERE press_code = %s AND face_name LIKE '%%"
                    + driver_name
                    + "%%' ORDER BY cut_year DESC LIMIT %s",
                    (press, edition),
                )
            else:
                cur.execute(
                    "SELECT face_name, founder, cut_year, press_code FROM sb_specimens "
                    "WHERE press_code = %s ORDER BY cut_year DESC LIMIT %s",
                    (press, edition),
                )
            return list(cur.fetchall())
    finally:
        conn.close()


@strawberry.enum
class PressCode(Enum):
    HARBOR = "harbor"
    ESTUARY = "estuary"
    RIDGE = "ridge"


@strawberry.type
class Specimen:
    face_name: str
    founder: str
    cut_year: int
    press_code: str


@strawberry.type
class Query:
    @strawberry.field
    def specimens(
        self,
        name: str = "",
        edition: int = 12,
        press: PressCode = PressCode.HARBOR,
    ) -> list[Specimen]:
        rows = load_specimens(name, edition, press.value)
        return [
            Specimen(
                face_name=row["face_name"],
                founder=row["founder"],
                cut_year=int(row["cut_year"]),
                press_code=row["press_code"],
            )
            for row in rows
        ]


schema = strawberry.Schema(query=Query)
app.include_router(GraphQLRouter(schema, graphql_ide=None), prefix="/graphql")


def page(title: str, body: str) -> str:
    css = (
        "body{margin:0;background:#f6f1e6;color:#241c14;font:18px/1.45 Georgia,serif}"
        "main{max-width:40rem;margin:0 auto;padding:2rem 1.2rem}"
        ".mark{letter-spacing:.18em;text-transform:uppercase;font-size:.72rem;color:#8a6232}"
        "h1{font-weight:500;font-size:2rem}"
        "form{display:flex;gap:.7rem;align-items:end;flex-wrap:wrap}"
        "label{display:flex;flex-direction:column;font-size:.85rem;gap:.25rem}"
        "input,select,button{font:inherit}"
        "input,select{border:1px solid #241c14;background:#fff;padding:.4rem .5rem}"
        "button{background:#241c14;color:#f6f1e6;border:0;padding:.5rem .8rem}"
        "li{list-style:none;padding:.55rem 0;border-top:1px solid #e4d8c4}"
        "ul{padding:0}.face{font-weight:650}"
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
        "<p class=\"mark\">Sable Foundry</p><h1>Specimen index</h1>"
        "<p>The index lists faces cut for the harbor, estuary, and ridge presses.</p>"
        "<p><a href=\"/specimens\">Open the specimen list</a></p>"
    )
    return page("Sable Foundry", body)


@app.get("/specimens", response_class=HTMLResponse)
def specimens_page(
    name: str = "",
    edition: str = "12",
    press: str = "harbor",
):
    if not (edition.isdigit() and 1 <= int(edition) <= 30):
        edition_value = 12
    else:
        edition_value = int(edition)
    rows = load_specimens(name, edition_value, press)
    items = []
    for row in rows:
        items.append(
            "<li><span class=\"face\">"
            + escape(str(row["face_name"]))
            + "</span> "
            + escape(str(row["founder"]))
            + " · "
            + escape(str(row["cut_year"]))
            + " · "
            + escape(str(row["press_code"]))
            + "</li>"
        )
    listing = "".join(items) or "<li>No face matches that name.</li>"
    options = []
    for code in ("harbor", "estuary", "ridge"):
        selected = " selected" if code == press or (press not in PRESSES and code == "harbor") else ""
        options.append(f"<option value=\"{code}\"{selected}>{code}</option>")
    body = (
        "<p class=\"mark\">Sable Foundry</p><h1>Specimens</h1>"
        "<form method=\"get\" action=\"/specimens\">"
        "<label>Face name <input name=\"name\" value=\""
        + escape(name, quote=True)
        + "\"></label>"
        "<label>Edition <input name=\"edition\" value=\""
        + str(edition_value)
        + "\" inputmode=\"numeric\"></label>"
        "<label>Press <select name=\"press\">"
        + "".join(options)
        + "</select></label>"
        "<button type=\"submit\">Look up</button></form><ul>"
        + listing
        + "</ul>"
    )
    return page("Sable specimens", body)
