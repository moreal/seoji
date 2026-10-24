"use strict";

// Every value from the API is inserted with textContent; links are only set when they are
// https://, mailto: or same-origin paths.

const LABELS = {
  role: {
    author: "지은이", translator: "옮긴이", illustrator: "그림", editor: "엮은이",
    original_author: "원작", supervisor: "감수", photographer: "사진", other: "기타",
  },
  binding: { paper: "종이책", ebook: "전자책", audio: "오디오북", mixed: "혼합", other: "기타" },
  pubStatus: { published: "출간", announced: "출간 예정(미납본)" },
  source: { lod: "국가서지 LOD", nlseoji: "ISBN 서지정보(Seoji)" },
};

const state = { q: "", koreanOnly: false, offset: 0, limit: 20 };
const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "href") {
      if (/^(https:\/\/|mailto:[^\s]+$|\/(?![\/\\]))/.test(value)) node.setAttribute("href", value);
    } else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === "") continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

async function getJSON(path) {
  const response = await fetch(path, { headers: { accept: "application/json" } });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body && body.error ? body.error.message : `요청 실패 (${response.status})`;
    throw Object.assign(new Error(message), { status: response.status });
  }
  return body;
}

function cover(url, title) {
  if (!url) return el("div", { class: "cover cover-empty", "aria-hidden": "true" }, "표지 없음");
  const img = el("img", {
    class: "cover", src: url, alt: `${title} 표지`, loading: "lazy",
    referrerpolicy: "no-referrer", decoding: "async",
  });
  img.addEventListener("error", () => img.replaceWith(cover(null, title)), { once: true });
  return img;
}

function formatDate(value, precision) {
  if (!value) return null;
  if (precision === "year") return value.slice(0, 4);
  if (precision === "month") return value.slice(0, 7);
  return value;
}

const won = (n) => (n ? `${n.toLocaleString("ko-KR")}원` : null);

// ── search ─────────────────────────────────────────────────────────────

async function runSearch({ append = false } = {}) {
  if (!append) {
    state.offset = 0;
    $("result-list").replaceChildren();
  }
  $("status").textContent = "검색 중…";
  $("more").hidden = true;
  const params = new URLSearchParams({
    q: state.q, limit: state.limit, offset: state.offset, korean_only: state.koreanOnly,
  });
  try {
    const result = await getJSON(`/api/v1/search?${params}`);
    for (const item of result.items) $("result-list").append(resultItem(item));
    const shown = $("result-list").children.length;
    $("status").textContent = shown ? `“${result.query}” 검색 결과 ${shown}건${result.has_more ? " 이상" : ""}` :
      `“${result.query}”에 맞는 책이 없습니다.`;
    state.offset += result.items.length;
    $("more").hidden = !result.has_more || state.offset + state.limit > 1000;
  } catch (error) {
    $("status").textContent = error.message;
  }
}

function resultItem(item) {
  const title = item.volume_label ? `${item.title} ${item.volume_label}` : item.title;
  const meta = [item.publisher, item.pub_year, LABELS.binding[item.binding]].filter(Boolean).join(" · ");
  const button = el("button", { class: "card", type: "button" },
    cover(item.cover_url, item.title),
    el("span", { class: "card-text" },
      el("span", { class: "card-title" }, title),
      el("span", { class: "card-authors" }, item.authors || ""),
      el("span", { class: "card-meta" }, meta)));
  button.addEventListener("click", () => openBook(item.isbn13));
  return el("li", {}, button);
}

// ── detail ─────────────────────────────────────────────────────────────

function row(label, value) {
  if (value === null || value === undefined || value === "") return null;
  return [el("dt", {}, label), el("dd", {}, value)];
}

function bookDetail(book) {
  const kdc = book.subjects.filter((s) => s.scheme === "kdc").map((s) => s.code).join(", ");
  const ksh = book.subjects.filter((s) => s.scheme === "ksh").map((s) => s.code).join(", ");
  const keywords = book.subjects.filter((s) => s.scheme === "nlk_keyword").map((s) => s.label);
  const addCode = book.ea_add_code &&
    [book.ea_add_code, book.add_code_labels.reader, book.add_code_labels.form].filter(Boolean).join(" · ");
  const size = book.width_mm && book.height_mm ? `${book.width_mm}×${book.height_mm}mm` :
    book.height_cm ? `${book.height_cm}cm` : null;

  const sets = book.sets.map((s) => {
    const button = el("button", { class: "link", type: "button" },
      s.title || s.set_isbn13, s.total_volumes ? ` (전 ${s.total_volumes}권)` : "");
    button.addEventListener("click", () => openSet(s.set_isbn13));
    return el("li", {}, button);
  });

  const sources = Object.entries(book.sources || {})
    .filter(([field]) => ["title", "publisher", "pub_date", "price_planned", "kdc"].includes(field))
    .map(([field, source]) => `${field}: ${LABELS.source[source] || source}`).join(", ");

  return [
    el("button", { class: "close", type: "button", "aria-label": "닫기" }, "×"),
    el("div", { class: "detail-head" },
      cover(book.cover_url, book.title),
      el("div", {},
        el("h2", {}, book.title, book.volume_label ? ` ${book.volume_label}` : ""),
        el("p", { class: "subtitle" }, book.remainder_of_title || ""),
        el("p", { class: "contributors" },
          book.contributors.map((c) => `${c.name}(${LABELS.role[c.role] || c.role})`).join(", ") ||
          book.responsibility_stmt || ""))),
    el("dl", { class: "facts" },
      row("ISBN", [book.isbn13, book.isbn10].filter(Boolean).join(" / ")),
      row("출판사", [book.publisher, book.publication_place].filter(Boolean).join(", ")),
      row("발행일", formatDate(book.pub_date, book.pub_date_precision)),
      row("상태", LABELS.pubStatus[book.pub_status]),
      row("형태", [LABELS.binding[book.binding], book.form].filter(Boolean).join(" · ")),
      row("판사항", book.edition_statement),
      row("총서", [book.series_title, book.series_no].filter(Boolean).join(" ")),
      row("쪽수", book.page_count ? `${book.page_count}쪽` : null),
      row("크기", size),
      row("가격", won(book.price_real) || won(book.price_planned)),
      row("부가기호", addCode),
      row("KDC", kdc),
      row("KSH", ksh),
      row("키워드", keywords.join(", ")),
      row("원서명", book.original_title)),
    sets.length ? el("section", {}, el("h3", {}, "세트"), el("ul", { class: "sets" }, sets)) : null,
    el("p", { class: "fine" }, sources ? `필드 출처 — ${sources}` : ""),
    book.links.nlk_lod ? el("p", { class: "fine" }, "국가서지 LOD: ",
      el("a", { href: book.links.nlk_lod.replace(/^http:/, "https:"), rel: "noopener" }, book.links.nlk_lod)) : null,
    el("p", { class: "fine" }, book.attribution),
  ];
}

function showDetail(children) {
  const panel = $("detail");
  panel.replaceChildren(...children.filter(Boolean));
  panel.hidden = false;
  panel.querySelector(".close")?.addEventListener("click", closeDetail);
  panel.scrollTop = 0;
}

function closeDetail() {
  $("detail").hidden = true;
  syncURL({ isbn: null });
}

async function openBook(isbn, { push = true } = {}) {
  try {
    showDetail(bookDetail(await getJSON(`/api/v1/books/${encodeURIComponent(isbn)}`)));
    if (push) syncURL({ isbn });
  } catch (error) {
    showDetail([el("button", { class: "close", type: "button", "aria-label": "닫기" }, "×"),
      el("p", {}, error.message)]);
  }
}

async function openSet(setIsbn) {
  try {
    const set = await getJSON(`/api/v1/sets/${encodeURIComponent(setIsbn)}`);
    const members = set.members.map((m) => {
      const button = el("button", { class: "link", type: "button" },
        [m.title, m.volume_label].filter(Boolean).join(" "));
      button.addEventListener("click", () => openBook(m.isbn13));
      return el("li", {}, button);
    });
    showDetail([
      el("button", { class: "close", type: "button", "aria-label": "닫기" }, "×"),
      el("h2", {}, set.title || set.set_isbn13),
      el("p", { class: "subtitle" }, set.set_expression || "", ` · 세트 ISBN ${set.set_isbn13}`),
      el("ol", { class: "sets" }, members),
      el("p", { class: "fine" }, set.attribution),
    ]);
  } catch (error) {
    $("status").textContent = error.message;
  }
}

// ── URL state and boot ─────────────────────────────────────────────────

function syncURL(changes) {
  const params = new URLSearchParams(location.search);
  for (const [key, value] of Object.entries(changes)) {
    if (value) params.set(key, value);
    else params.delete(key);
  }
  const query = params.toString();
  history.pushState(null, "", query ? `?${query}` : "/");
}

function restoreFromURL() {
  const params = new URLSearchParams(location.search);
  const q = params.get("q") || "";
  state.koreanOnly = params.get("korean_only") === "true";
  $("q").value = q;
  $("korean-only").checked = state.koreanOnly;
  if (q && q !== state.q) {
    state.q = q;
    runSearch();
  }
  const isbn = params.get("isbn");
  if (isbn) openBook(isbn, { push: false });
  else $("detail").hidden = true;
}

async function loadMeta() {
  try {
    const meta = await getJSON("/api/v1/meta");
    $("attribution").textContent = meta.attribution;
    $("notice").textContent = meta.notice;
    if (meta.contact) {
      $("contact").replaceChildren("게시중단·정정 요청: ",
        /^[^\s@]+@[^\s@]+$/.test(meta.contact) ? el("a", { href: `mailto:${meta.contact}` }, meta.contact) : meta.contact);
    }
  } catch {
    // footer stays empty; search still works
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    state.q = $("q").value.trim();
    state.koreanOnly = $("korean-only").checked;
    if (!state.q) return;
    syncURL({ q: state.q, korean_only: state.koreanOnly ? "true" : null, isbn: null });
    $("detail").hidden = true;
    runSearch();
  });
  $("more").addEventListener("click", () => runSearch({ append: true }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("detail").hidden) closeDetail();
  });
  window.addEventListener("popstate", () => {
    state.q = "";
    restoreFromURL();
  });
  loadMeta();
  restoreFromURL();
});
