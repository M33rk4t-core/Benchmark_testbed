const fs = require("fs");
const path = require("path");
const express = require("express");
const mysql = require("mysql2/promise");

const port = Number(process.env.PORT || 8087);
const pool = mysql.createPool({
  host: process.env.DB_HOST || "db",
  user: process.env.DB_USER || "bench",
  password: process.env.DB_PASSWORD || "bench-local-only",
  database: process.env.DB_NAME || "vellum",
  charset: "utf8mb4",
  waitForConnections: true,
  connectionLimit: 4,
});

const css = fs.readFileSync(path.join(__dirname, "public", "room.css"), "utf8");
const client = fs.readFileSync(path.join(__dirname, "public", "room.js"), "utf8");
const shelves = ["west-cloister", "east-stack", "scriptorium", "annex"];
const shelfSet = new Set(shelves);

const app = express();
app.disable("x-powered-by");
app.use(express.static(path.join(__dirname, "public")));

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function clampInt(value, min, max, fallback) {
  if (typeof value !== "string" || !/^[0-9]{1,4}$/.test(value)) {
    return fallback;
  }
  const number = Number(value);
  if (!Number.isInteger(number) || number < min || number > max) {
    return fallback;
  }
  return number;
}

function boundedSiglum(value) {
  if (typeof value !== "string") {
    return "";
  }
  return /^[A-Za-z0-9-]{2,16}$/.test(value) ? value : "";
}

function shadowCard(folio, gloss, leaf) {
  const current = Number(folio.leaf_no) === leaf ? " data-current=\"true\"" : "";
  const notes = [
    "Catchword visible in the lower margin.",
    "A later hand corrected the place name.",
    "Ruling is drypoint, about twenty-eight lines.",
  ];
  const apparatus = notes
    .map((note, index) => `<li data-note="${index + 1}">${escapeHtml(note)}</li>`)
    .join("");
  return `<folio-card data-leaf="${Number(folio.leaf_no)}"${current}>
    <template shadowrootmode="open">
      <style>
        :host{display:block;padding:.8rem 1rem}
        h2{font-size:1.15rem;margin:.2rem 0}
        .siglum{letter-spacing:.08em;text-transform:uppercase;font-size:.75rem;color:#6e1e2a}
        .gloss{margin-bottom:0}
        ol{margin:.4rem 0 0;padding-left:1.1rem;font-size:.92rem}
      </style>
      <p class="siglum">${escapeHtml(folio.siglum)} · leaf ${Number(folio.leaf_no)}</p>
      <h2>${escapeHtml(folio.work_title)}</h2>
      <p>${escapeHtml(folio.scribe_name)} · ${escapeHtml(folio.century_label)}</p>
      <p class="incipit">${escapeHtml(folio.incipit)}</p>
      <p class="gloss">${gloss}</p>
      <ol class="apparatus">${apparatus}</ol>
    </template>
  </folio-card>`;
}

function readingTree(folios, gloss, leaf) {
  const cards = folios.map((folio) => shadowCard(folio, gloss, leaf)).join("");
  return `<archive-room>
    <wing-block data-wing="reading">
      <bay-row data-bay="1">
        <shelf-rail>
          <gathering-set>
            ${cards || "<p>No leaf is filed on this shelf.</p>"}
          </gathering-set>
        </shelf-rail>
      </bay-row>
    </wing-block>
  </archive-room>`;
}

app.get("/reading-room", async (req, res, next) => {
  try {
    const shelf = shelfSet.has(req.query.shelf) ? String(req.query.shelf) : "west-cloister";
    const leaf = clampInt(req.query.leaf, 1, 40, 1);
    const siglum = boundedSiglum(req.query.siglum);
    const gloss = typeof req.query.gloss === "string" ? req.query.gloss : "";
    const params = [shelf];
    let sql = `SELECT siglum, work_title, scribe_name, leaf_no, century_label, incipit
               FROM vm_folios WHERE shelf_code = ?`;
    if (siglum) {
      sql += " AND siglum = ?";
      params.push(siglum);
    }
    sql += " ORDER BY leaf_no, id";
    const [folios] = await pool.query(sql, params);
    const options = shelves
      .map((code) => {
        const selected = code === shelf ? " selected" : "";
        return `<option value="${escapeHtml(code)}"${selected}>${escapeHtml(code)}</option>`;
      })
      .join("");
    const href =
      "/reading-room?shelf=" +
      encodeURIComponent(shelf) +
      "&leaf=" +
      leaf +
      (siglum ? "&siglum=" + encodeURIComponent(siglum) : "");
    const body = `<p class="mark">Vellum Room</p>
      <h1>Reading room</h1>
      <p class="desk-note">Ask the desk for a shelf, a leaf, and a short gloss to pin beside the incipit.</p>
      <form method="get" action="/reading-room">
        <label>Gloss <input name="gloss" value="${escapeHtml(gloss)}"></label>
        <label>Shelf <select name="shelf">${options}</select></label>
        <label>Leaf <input name="leaf" value="${leaf}" inputmode="numeric"></label>
        <label>Siglum <input name="siglum" value="${escapeHtml(siglum)}"></label>
        <button type="submit">Bring the gathering</button>
      </form>
      <p><a href="${escapeHtml(href)}">Keep this gathering</a></p>
      ${readingTree(folios, gloss, leaf)}`;
    res.type("html").send(`<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
      <meta name="robots" content="noindex"><title>Vellum Room</title>
      <style>${css}</style></head><body><main>${body}</main>
      <script>${client}</script></body></html>`);
  } catch (error) {
    next(error);
  }
});

app.use((error, req, res, next) => {
  if (res.headersSent) {
    next(error);
    return;
  }
  console.error(error);
  res.status(500).type("html").send("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Vellum Room</title></head><body><p>The reading room could not open the shelf list.</p></body></html>");
});

app.listen(port, "0.0.0.0");
