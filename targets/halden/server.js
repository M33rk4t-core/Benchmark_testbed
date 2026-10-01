const express = require("express");
const session = require("express-session");
const mysql = require("mysql2/promise");

const port = Number(process.env.PORT || 8085);
const pool = mysql.createPool({
  host: process.env.DB_HOST || "db",
  user: process.env.DB_USER || "bench",
  password: process.env.DB_PASSWORD || "bench-local-only",
  database: process.env.DB_NAME || "halden",
  charset: "utf8mb4",
  waitForConnections: true,
  connectionLimit: 4,
});

const app = express();
app.disable("x-powered-by");
app.use(express.urlencoded({ extended: false }));
app.use(
  session({
    secret: "halden-floor-local",
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true, sameSite: "lax" },
  })
);

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function strictInt(value, min, max) {
  if (typeof value !== "string" || !/^[0-9]{1,4}$/.test(value)) {
    return null;
  }
  const number = Number(value);
  if (!Number.isInteger(number) || number < min || number > max) {
    return null;
  }
  return number;
}

function layout(title, step, body) {
  const steps = ["Profile", "Materials", "Review"]
    .map((label, index) => {
      const mark = index + 1 === step ? " is-current" : "";
      return `<li class="step${mark}">${index + 1}. ${label}</li>`;
    })
    .join("");
  const css = `
    body{margin:0;background:#f6f3ee;color:#241910;font:18px/1.5 Georgia,serif}
    main{max-width:40rem;margin:0 auto;padding:2rem 1.2rem}
    .mark{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:#4a1c2b}
    h1{font-weight:500;font-size:2rem;margin:.2rem 0 1rem}
    ol.progress{display:flex;gap:1rem;padding:0;list-style:none;font-size:.9rem}
    .step{color:#7a675c}.is-current{color:#4a1c2b;font-weight:700}
    label{display:flex;flex-direction:column;gap:.3rem;margin:.8rem 0}
    input,select,textarea,button{font:inherit}
    input,select,textarea{border:1px solid #4a1c2b;background:#fff;padding:.45rem}
    button{background:#4a1c2b;color:#fff;border:0;padding:.55rem .9rem}
    .error{color:#4a1c2b}
    .sheet{background:#fff;border-top:3px solid #1e2a4a;padding:1rem}
  `;
  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
    <meta name="robots" content="noindex"><title>${escapeHtml(title)}</title>
    <style>${css}</style></head><body><main>
    <p class="mark">Halden Seminar</p><h1>${escapeHtml(title)}</h1>
    <ol class="progress">${steps}</ol>${body}</main></body></html>`;
}

async function programRows() {
  const [rows] = await pool.query(
    "SELECT code, title FROM hs_programs ORDER BY title"
  );
  return rows;
}

function programOptions(rows, selected) {
  return rows
    .map((row) => {
      const on = row.code === selected ? " selected" : "";
      return `<option value="${escapeHtml(row.code)}"${on}>${escapeHtml(row.title)}</option>`;
    })
    .join("");
}

app.get("/apply", async (req, res, next) => {
  try {
    const rows = await programRows();
    const state = req.session.application || {};
    const body = `<form method="post" action="/apply/profile">
      <label>Sponsoring reader <input name="advisor" maxlength="200"></label>
      <label>Program <select name="program">${programOptions(rows, state.program || "")}</select></label>
      <label>Essay pages <input name="pages" inputmode="numeric" value="12"></label>
      <button type="submit">Continue</button></form>`;
    res.type("html").send(layout("Visiting scholar profile", 1, body));
  } catch (error) {
    next(error);
  }
});

app.post("/apply/profile", async (req, res, next) => {
  try {
    const advisor = typeof req.body.advisor === "string" ? req.body.advisor.trim() : "";
    const program = typeof req.body.program === "string" ? req.body.program : "";
    const pages = strictInt(req.body.pages, 1, 80);
    const [found] = await pool.query(
      "SELECT code, title FROM hs_programs WHERE code = ? LIMIT 1",
      [program]
    );
    if (!advisor || !found.length || pages === null) {
      const rows = await programRows();
      const body = `<p class="error">The profile needs a reader, a listed program, and a page count from 1 to 80.</p>
        <form method="post" action="/apply/profile">
        <label>Sponsoring reader <input name="advisor" maxlength="200"></label>
        <label>Program <select name="program">${programOptions(rows, "")}</select></label>
        <label>Essay pages <input name="pages" inputmode="numeric"></label>
        <button type="submit">Continue</button></form>`;
      res.status(400).type("html").send(layout("Visiting scholar profile", 1, body));
      return;
    }
    req.session.application = {
      ...(req.session.application || {}),
      advisor,
      program: found[0].code,
      programTitle: found[0].title,
      pages,
    };
    req.session.save((err) => {
      if (err) {
        next(err);
        return;
      }
      res.redirect(303, "/apply/materials");
    });
  } catch (error) {
    next(error);
  }
});

app.get("/apply/materials", (req, res) => {
  const state = req.session.application || {};
  if (!state.advisor || !state.program) {
    res.redirect(303, "/apply");
    return;
  }
  const body = `<form method="post" action="/apply/materials">
    <label>Study statement <textarea name="statement" rows="6" maxlength="4000"></textarea></label>
    <label>File copies <input name="copies" inputmode="numeric" value="1"></label>
    <button type="submit">Continue to review</button></form>`;
  res.type("html").send(layout("Materials", 2, body));
});

app.post("/apply/materials", (req, res, next) => {
  const state = req.session.application || {};
  if (!state.advisor || !state.program) {
    res.redirect(303, "/apply");
    return;
  }
  const statement = typeof req.body.statement === "string" ? req.body.statement.trim() : "";
  const copies = strictInt(req.body.copies, 1, 12);
  if (!statement || statement.length > 4000 || copies === null) {
    const body = `<p class="error">Add a statement of at most 4000 characters and a copy count from 1 to 12.</p>
      <form method="post" action="/apply/materials">
      <label>Study statement <textarea name="statement" rows="6" maxlength="4000"></textarea></label>
      <label>File copies <input name="copies" inputmode="numeric"></label>
      <button type="submit">Continue to review</button></form>`;
    res.status(400).type("html").send(layout("Materials", 2, body));
    return;
  }
  req.session.application = { ...state, statement, copies };
  req.session.save((err) => {
    if (err) {
      next(err);
      return;
    }
    res.redirect(303, "/apply/review");
  });
});

function reviewMarkup(state) {
  return `<article class="sheet">
    <h2>Review sheet</h2>
    <p class="advisor-line">${state.advisor}</p>
    <p>${escapeHtml(state.programTitle)} · ${escapeHtml(state.pages)} pages · ${escapeHtml(state.copies)} copies</p>
    <p class="statement">${escapeHtml(state.statement)}</p>
    <p><a href="/apply">Start another file</a></p>
  </article>`;
}

app.get("/apply/review", (req, res) => {
  const state = req.session.application || {};
  if (!state.advisor || !state.statement) {
    res.redirect(303, "/apply");
    return;
  }
  res.type("html").send(layout("Review", 3, reviewMarkup(state)));
});

app.use((error, req, res, next) => {
  console.error(error);
  res
    .status(500)
    .type("html")
    .send(layout("Seminar desk", 1, "<p>The seminar desk could not read its program list.</p>"));
});

app.listen(port, "0.0.0.0");
