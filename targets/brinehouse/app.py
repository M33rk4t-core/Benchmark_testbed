import os
import subprocess
from html import escape

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Brinehouse Proofs")
CATALOG = "/srv/catalog/plates.txt"
PLATES = {"harbor-01.txt", "estuary-02.txt", "ridge-03.txt"}


def search_marks(mark: str) -> str:
    if not mark:
        return ""
    command = "grep -n -F -e " + mark + " " + CATALOG
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return completed.stdout


def plate_excerpt(plate: str, copies: int) -> str:
    chosen = plate if plate in PLATES else "harbor-01.txt"
    path = os.path.join("/srv/catalog", chosen)
    try:
        completed = subprocess.run(
            ["head", "-n", str(copies), path],
            shell=False,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return completed.stdout


def page(title: str, body: str) -> str:
    css = (
        "body{margin:0;background:#e7eef2;color:#102028;font:17px/1.45 'Segoe UI',sans-serif}"
        "main{max-width:40rem;margin:0 auto;padding:2rem 1.2rem}"
        ".mark{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:#1d4e89}"
        "h1{font-weight:560;font-size:1.8rem}"
        "form{display:flex;gap:.7rem;align-items:end;flex-wrap:wrap}"
        "label{display:flex;flex-direction:column;font-size:.85rem;gap:.25rem}"
        "input,select,button{font:inherit}"
        "input,select{border:1px solid #102028;background:#fff;padding:.4rem .5rem}"
        "button{background:#1d4e89;color:#fff;border:0;padding:.5rem .8rem}"
        "pre{white-space:pre-wrap;background:#fff;padding:.8rem;border-top:3px solid #1d4e89}"
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
        "<p class=\"mark\">Brinehouse</p><h1>Proof desk</h1>"
        "<p>The desk reads plate marks and prints a short excerpt for the stone.</p>"
        "<p><a href=\"/proofs\">Open the proof desk</a></p>"
    )
    return page("Brinehouse", body)


@app.get("/proofs", response_class=HTMLResponse)
def proofs(
    mark: str = "",
    plate: str = "harbor-01.txt",
    copies: int = Query(default=2, ge=1, le=12),
):
    found = search_marks(mark)
    excerpt = plate_excerpt(plate, copies)
    chosen = plate if plate in PLATES else "harbor-01.txt"
    options = []
    for name in ("harbor-01.txt", "estuary-02.txt", "ridge-03.txt"):
        selected = " selected" if name == chosen else ""
        options.append(f"<option value=\"{name}\"{selected}>{name}</option>")
    body = (
        "<p class=\"mark\">Brinehouse</p><h1>Plate proofs</h1>"
        "<form method=\"get\" action=\"/proofs\">"
        "<label>Mark <input name=\"mark\" value=\""
        + escape(mark, quote=True)
        + "\"></label>"
        "<label>Plate <select name=\"plate\">"
        + "".join(options)
        + "</select></label>"
        "<label>Lines <input name=\"copies\" value=\""
        + str(copies)
        + "\" inputmode=\"numeric\"></label>"
        "<button type=\"submit\">Pull proof</button></form>"
        "<h2>Marks</h2><pre>"
        + (escape(found) if found else "No mark is filed.")
        + "</pre><h2>Excerpt</h2><pre>"
        + (escape(excerpt) if excerpt else "The plate excerpt is empty.")
        + "</pre>"
    )
    return page("Brinehouse proofs", body)
