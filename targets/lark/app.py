import os
from html import escape

from flask import Flask, request
from jinja2 import BaseLoader, Environment, TemplateError

app = Flask(__name__)
notice_env = Environment(loader=BaseLoader(), autoescape=False)
letterhead_env = Environment(loader=BaseLoader(), autoescape=True)


def render_notice(body: str) -> str:
    if not body or len(body) > 4000:
        return ""
    try:
        return notice_env.from_string(body).render(office="Lark Notices", day="Thursday")
    except TemplateError:
        return ""


def render_subject(subject: str) -> str:
    if not subject or len(subject) > 160:
        subject = "Thursday proof"
    return letterhead_env.from_string("<h2>{{ subject }}</h2>").render(subject=subject)


def page(title: str, body: str) -> str:
    css = (
        "body{margin:0;background:#f3f7f2;color:#1c2b22;font:18px/1.5 Georgia,serif}"
        "main{max-width:38rem;margin:0 auto;padding:2rem 1.2rem}"
        ".mark{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:#2f6b45}"
        "h1{font-weight:500;font-size:2rem}"
        "label{display:flex;flex-direction:column;gap:.3rem;margin:.7rem 0}"
        "input,textarea,button{font:inherit}"
        "input,textarea{border:1px solid #1c2b22;background:#fff;padding:.45rem}"
        "button{background:#2f6b45;color:#fff;border:0;padding:.55rem .9rem}"
        ".sheet{background:#fff;border-top:3px solid #2f6b45;padding:1rem}"
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


@app.get("/")
def home():
    body = (
        "<p class=\"mark\">Lark Notices</p><h1>Works circulars</h1>"
        "<p>The office sets the Thursday notice for the yard and the pier store.</p>"
        "<p><a href=\"/notices\">Open the notice desk</a></p>"
    )
    return page("Lark Notices", body)


@app.route("/notices", methods=["GET", "POST"])
def notices():
    source = request.form if request.method == "POST" else request.args
    raw_body = source.get("body", "")
    raw_subject = source.get("subject", "")
    if not isinstance(raw_body, str):
        raw_body = ""
    if not isinstance(raw_subject, str):
        raw_subject = ""
    notice = render_notice(raw_body.strip())
    subject_html = render_subject(raw_subject.strip())
    shown_subject = raw_subject.strip() if raw_subject.strip() and len(raw_subject.strip()) <= 160 else "Thursday proof"
    form = (
        "<form method=\"post\" action=\"/notices\">"
        "<label>Subject <input name=\"subject\" value=\""
        + escape(shown_subject, quote=True)
        + "\"></label>"
        "<label>Notice <textarea name=\"body\" rows=\"6\">"
        + escape(raw_body)
        + "</textarea></label>"
        "<button type=\"submit\">Set the notice</button></form>"
    )
    sheet = "<article class=\"sheet\">" + subject_html + notice + "</article>"
    body = "<p class=\"mark\">Lark Notices</p><h1>Thursday circular</h1>" + form + sheet
    return page("Lark notice", body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8090")), debug=False)
