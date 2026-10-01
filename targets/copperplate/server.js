const fs = require("fs");
const path = require("path");
const express = require("express");

const port = Number(process.env.PORT || 8091);
const drawingsRoot = path.join(__dirname, "drawings");
const plates = new Set(["harbor", "estuary", "ridge"]);
const app = express();
app.disable("x-powered-by");

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function readSheet(sheet) {
  if (typeof sheet !== "string" || sheet === "") {
    return "";
  }
  const target = path.join(drawingsRoot, sheet);
  try {
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      return "";
    }
    return fs.readFileSync(target, "utf8").slice(0, 4000);
  } catch {
    return "";
  }
}

function readPlate(plate) {
  const chosen = plates.has(plate) ? plate : "harbor";
  const target = path.join(drawingsRoot, `${chosen}.txt`);
  return fs.readFileSync(target, "utf8");
}

function page(title, body) {
  const css = `
    body{margin:0;background:#f4f0ea;color:#2a241e;font:18px/1.5 Georgia,serif}
    main{max-width:40rem;margin:0 auto;padding:2rem 1.2rem}
    .mark{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:#7a4b2a}
    h1{font-weight:500;font-size:2rem}
    form{display:flex;gap:.7rem;align-items:end;flex-wrap:wrap}
    label{display:flex;flex-direction:column;font-size:.85rem;gap:.25rem}
    input,select,button{font:inherit}
    input,select{border:1px solid #2a241e;background:#fff;padding:.4rem .5rem}
    button{background:#7a4b2a;color:#fff;border:0;padding:.5rem .8rem}
    pre{white-space:pre-wrap;background:#fff;padding:.8rem;border-top:3px solid #7a4b2a}
  `;
  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
    <meta name="robots" content="noindex"><title>${escapeHtml(title)}</title>
    <style>${css}</style></head><body><main>${body}</main></body></html>`;
}

app.get("/", (req, res) => {
  const body = `<p class="mark">Copperplate Desk</p><h1>Drawing file</h1>
    <p>The desk keeps the harbor, estuary, and ridge plates.</p>
    <p><a href="/drawings">Open the drawings</a></p>`;
  res.type("html").send(page("Copperplate Desk", body));
});

function drawingsPage(req, res) {
  const sheet = typeof req.query.sheet === "string" ? req.query.sheet : "";
  const plate = typeof req.query.plate === "string" ? req.query.plate : "harbor";
  const sheetText = readSheet(sheet);
  const plateText = readPlate(plate);
  const chosen = plates.has(plate) ? plate : "harbor";
  const options = ["harbor", "estuary", "ridge"]
    .map((code) => {
      const selected = code === chosen ? " selected" : "";
      return `<option value="${code}"${selected}>${code}</option>`;
    })
    .join("");
  const body = `<p class="mark">Copperplate Desk</p><h1>Stored plates</h1>
    <form method="get" action="/drawings">
      <label>Sheet <input name="sheet" value="${escapeHtml(sheet)}"></label>
      <label>Plate <select name="plate">${options}</select></label>
      <button type="submit">Open</button>
    </form>
    <h2>Sheet</h2><pre>${sheetText ? escapeHtml(sheetText) : "No sheet is open."}</pre>
    <h2>Plate note</h2><pre>${escapeHtml(plateText)}</pre>`;
  res.type("html").send(page("Copperplate drawings", body));
}

app.get("/drawings", drawingsPage);

app.listen(port, "0.0.0.0");
