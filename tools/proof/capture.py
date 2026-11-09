#!/usr/bin/env python3
"""Proof screenshots for scripts: open every source, highlight the exact line, save a PNG.

Usage
-----
    python tools/proof/capture.py scripts/2026-11-10-paper-leak-long/          # capture all
    python tools/proof/capture.py scripts/2026-11-10-paper-leak-long/ --only L07
    python tools/proof/capture.py scripts/2026-11-10-paper-leak-long/ --links  # print deep links only
    python tools/proof/capture.py scripts/2026-11-10-paper-leak-long/ --fill-links  # (LINK:L07) -> URL

Each script folder has:
    script.md      the script; every factual line carries a marker  <!--proof:L07-->
    sources.json   one entry per marker (url, exact text to highlight, page for PDFs)
    proof/         output: L07.png ... and report.md

What it does per source
    html -> opens the page in headless Chromium, finds the exact text, draws a yellow
            highlight + red box on it, scrolls it to the middle, adds a footer strip with
            the URL and capture time, saves the screenshot.
    pdf  -> downloads the PDF, finds the text with PyMuPDF, adds a real highlight
            annotation, renders that part of the page.
Then it replaces each <!--proof:ID--> marker line in script.md with the image.

If the text is not found on the page, the screenshot is saved as ID-unverified.png and is
NOT put into the script: a human must check that line (the quote may have changed).

Setup (own laptop):  pip install playwright pymupdf requests && playwright install chromium
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

FOOTER_CSS = (
    "position:fixed;left:0;right:0;bottom:0;z-index:2147483647;"
    "background:#111;color:#fff;font:14px/1.4 Arial,sans-serif;padding:8px 14px;"
    "border-top:3px solid #ffd400;word-break:break-all"
)

HIGHLIGHT_JS = r"""
([needle, footer, footerCss]) => {
  const norm = s => s.replace(/[‘’]/g, "'").replace(/[“”]/g, '"')
                     .replace(/[–—]/g, '-').replace(/\s+/g, ' ').toLowerCase();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: n => {
      const p = n.parentElement;
      if (!p || ['SCRIPT','STYLE','NOSCRIPT'].includes(p.tagName)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  // Build one normalised string with a map back to (node, offset).
  let text = '', map = [], prevSpace = true, n;
  while ((n = walker.nextNode())) {
    const raw = n.nodeValue;
    for (let i = 0; i < raw.length; i++) {
      let c = norm(raw[i]);
      if (c === ' ') { if (prevSpace) continue; prevSpace = true; } else { prevSpace = false; }
      text += c; map.push([n, i]);
    }
    if (!prevSpace) { text += ' '; map.push([n, raw.length]); prevSpace = true; }
  }
  const target = norm(needle).trim();
  let idx = text.indexOf(target);
  if (idx < 0) return {found: false};
  const [sn, so] = map[idx];
  const [en, eo] = map[idx + target.length - 1];
  const range = document.createRange();
  range.setStart(sn, so);
  range.setEnd(en, Math.min(eo + 1, en.nodeValue.length));
  const el = sn.parentElement;
  el.scrollIntoView({block: 'center'});
  const rects = Array.from(range.getClientRects()).filter(r => r.width > 0 && r.height > 0);
  if (!rects.length) return {found: false};
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
  for (const r of rects) {
    const d = document.createElement('div');
    d.style.cssText = `position:absolute;left:${r.left + scrollX}px;top:${r.top + scrollY}px;` +
      `width:${r.width}px;height:${r.height}px;background:rgba(255,230,0,.55);` +
      `z-index:2147483646;pointer-events:none;mix-blend-mode:multiply`;
    document.body.appendChild(d);
    minX = Math.min(minX, r.left); minY = Math.min(minY, r.top);
    maxX = Math.max(maxX, r.right); maxY = Math.max(maxY, r.bottom);
  }
  const box = document.createElement('div');
  box.style.cssText = `position:absolute;left:${minX + scrollX - 6}px;top:${minY + scrollY - 6}px;` +
    `width:${maxX - minX + 12}px;height:${maxY - minY + 12}px;border:3px solid #e00000;` +
    `border-radius:6px;z-index:2147483646;pointer-events:none`;
  document.body.appendChild(box);
  const f = document.createElement('div');
  f.style.cssText = footerCss; f.textContent = footer;
  document.body.appendChild(f);
  return {found: true};
}
"""


def text_fragment(highlight: str) -> str:
    """Chrome/Edge/Android 'scroll to text' fragment. Long quotes use start,end form."""
    words = highlight.split()
    # '-', ',' and '&' are syntax inside a text fragment, so they must be percent-encoded.
    q = lambda s: urllib.parse.quote(s, safe="").replace("-", "%2D")
    if len(words) > 12:
        return f"#:~:text={q(' '.join(words[:6]))},{q(' '.join(words[-6:]))}"
    return f"#:~:text={q(highlight)}"


def deep_link(src: dict) -> str:
    url = src["url"].split("#")[0]
    if src.get("type") == "pdf":
        return f"{url}#page={src.get('page', 1)}"
    return url + text_fragment(src["highlight"])


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _verify_arg():
    for k in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        if os.environ.get(k):
            return os.environ[k]
    return "/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").exists() else True


def capture_pdf(src: dict, out: Path, cache: Path) -> str:
    import pymupdf  # PyMuPDF
    import requests

    cache.mkdir(parents=True, exist_ok=True)
    pdf_path = cache / (re.sub(r"[^A-Za-z0-9]+", "_", src["url"])[-120:] + ".pdf")
    if src["url"].startswith("file://"):
        pdf_path = Path(urllib.parse.urlparse(src["url"]).path)
    elif not pdf_path.exists():
        r = requests.get(src["url"], timeout=60, verify=_verify_arg(),
                         headers={"User-Agent": "Mozilla/5.0 (proof-capture)"})
        r.raise_for_status()
        pdf_path.write_bytes(r.content)
    doc = pymupdf.open(pdf_path)
    pages = [src["page"] - 1] if src.get("page") else range(len(doc))
    needle = " ".join(src["highlight"].split())
    for pno in pages:
        page = doc[pno]
        quads = page.search_for(needle, quads=True)
        if not quads:  # fall back to the first 6 words
            quads = page.search_for(" ".join(needle.split()[:6]), quads=True)
        if not quads:
            continue
        annot = page.add_highlight_annot(quads)
        annot.set_colors(stroke=(1, 0.85, 0))
        annot.update()
        rect = quads[0].rect
        for qd in quads[1:]:
            rect |= qd.rect
        clip = pymupdf.Rect(page.rect.x0, max(page.rect.y0, rect.y0 - 140),
                            page.rect.x1, min(page.rect.y1, rect.y1 + 140))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5), clip=clip)
        pix.save(out)
        src["found_page"] = pno + 1
        return "ok"
    # Not found: save page 1 (or given page) for a human to check.
    page = doc[pages[0] if isinstance(pages, list) else 0]
    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(out.with_name(out.stem + "-unverified.png"))
    return "text-not-found"


def capture_html(src: dict, out: Path, browser) -> str:
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1.5)
    try:
        page.goto(src["url"], wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        footer = f"Source: {src['url']}  ·  captured {now_utc()}"
        res = page.evaluate(HIGHLIGHT_JS, [src["highlight"], footer, FOOTER_CSS])
        page.wait_for_timeout(400)
        if res.get("found"):
            page.screenshot(path=str(out))
            return "ok"
        page.screenshot(path=str(out.with_name(out.stem + "-unverified.png")))
        return "text-not-found"
    finally:
        page.close()


def launch_browser(pw):
    try:
        return pw.chromium.launch()
    except Exception:
        for cand in sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux*/chrome")):
            return pw.chromium.launch(executable_path=str(cand))
        raise


def update_script(script: Path, done: dict[str, str]) -> None:
    text = script.read_text(encoding="utf-8")
    for sid, rel in done.items():
        text = re.sub(rf"(<!--proof:{re.escape(sid)}-->).*$", rf"\1![{sid} proof]({rel})",
                      text, flags=re.M)
    script.write_text(text, encoding="utf-8")


def renumber(script: Path, meta_path: Path, meta: dict) -> None:
    """After inserting lines (e.g. **L18x**), renumber labels L01.. in order and remap proof ids.

    A label's first marker gets the label id, the next ones get b, c, d ... suffixes.
    """
    lines = script.read_text(encoding="utf-8").splitlines(keepends=True)
    label_re = re.compile(r"^\*\*(L[0-9]+[a-z]?)\*\*")
    labels = [m.group(1) for ln in lines if (m := label_re.match(ln))]
    width = max(2, len(str(len(labels))))
    new_label = {old: f"L{i:0{width}d}" for i, old in enumerate(labels, 1)}
    id_map, cur, count, out = {}, None, 0, []
    for ln in lines:
        m = label_re.match(ln)
        if m:
            cur, count = new_label[m.group(1)], 0
            ln = ln.replace(f"**{m.group(1)}**", f"**{cur}**", 1)

        def sub(mm):
            nonlocal count
            new = cur + ("" if count == 0 else "bcdefghij"[count - 1])
            count += 1
            id_map[mm.group(1)] = new
            return f"<!--proof:{new}-->"
        out.append(re.sub(r"<!--proof:([A-Za-z0-9_-]+)-->", sub, ln))
    script.write_text("".join(out), encoding="utf-8")
    for s in meta["sources"]:
        s["id"] = id_map.get(s["id"], s["id"])
    meta["sources"].sort(key=lambda s: (int(re.sub(r"\D", "", s["id"]) or 0), s["id"]))
    meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    old_png = {o: n for o, n in id_map.items() if o != n}
    if old_png:
        print("Renumbered:", ", ".join(f"{o}->{n}" for o, n in old_png.items()))
        print("Re-run capture with --force so PNG names match the new ids.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--only", nargs="*", help="capture only these ids")
    ap.add_argument("--links", action="store_true", help="print deep links and exit")
    ap.add_argument("--force", action="store_true", help="re-capture even if PNG exists")
    ap.add_argument("--fill-links", action="store_true",
                    help="only replace (LINK:ID) placeholders in script.md with deep links")
    ap.add_argument("--renumber", action="store_true",
                    help="renumber **Lnn** labels in order and remap proof ids, then exit")
    a = ap.parse_args()

    meta_path = a.folder / "sources.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    sources = meta["sources"]
    script = a.folder / meta.get("script", "script.md")

    if a.renumber:
        renumber(script, meta_path, meta)
        return 0

    markers = set(re.findall(r"<!--proof:([A-Za-z0-9_-]+)-->", script.read_text(encoding="utf-8")))
    ids = {s["id"] for s in sources}
    if markers - ids:
        print("ERROR: markers without a sources.json entry:", sorted(markers - ids))
        return 2

    if a.links:
        for s in sources:
            print(f"{s['id']}\t{deep_link(s)}")
        return 0

    # Writing aid: "(LINK:L07)" in script.md becomes the deep link for L07.
    by_id = {s["id"]: s for s in sources}
    text = script.read_text(encoding="utf-8")
    filled = re.sub(r"\(LINK:([A-Za-z0-9_-]+)\)",
                    lambda m: f"({deep_link(by_id[m.group(1)])})" if m.group(1) in by_id else m.group(0), text)
    if filled != text:
        script.write_text(filled, encoding="utf-8")
        print("Filled LINK: placeholders in", script)
    if a.fill_links:
        return 0

    proof = a.folder / "proof"
    proof.mkdir(exist_ok=True)
    todo = [s for s in sources if not a.only or s["id"] in a.only]
    results, done, browser, pw_ctx = {}, {}, None, None
    try:
        for s in todo:
            out = proof / f"{s['id']}.png"
            if out.exists() and not a.force:
                results[s["id"]] = "ok (cached)"
                done[s["id"]] = f"proof/{out.name}"
                continue
            try:
                if s.get("type") == "pdf":
                    status = capture_pdf(s, out, proof / ".cache")
                else:
                    if browser is None:
                        from playwright.sync_api import sync_playwright
                        pw_ctx = sync_playwright().start()
                        browser = launch_browser(pw_ctx)
                    status = capture_html(s, out, browser)
            except Exception as e:  # blocked host, timeout, 403 ...
                msg = str(e).splitlines()[0] if str(e) else type(e).__name__
                if "ERR_TUNNEL_CONNECTION_FAILED" in msg or "ProxyError" in msg or "Tunnel connection failed" in msg:
                    status = "failed: site blocked by this machine's network"
                else:
                    status = f"failed: {type(e).__name__}: {msg[:120]}"
            results[s["id"]] = status
            if status == "ok":
                done[s["id"]] = f"proof/{out.name}"
            print(f"{s['id']:>5}  {status}")
    finally:
        if browser:
            browser.close()
        if pw_ctx:
            pw_ctx.stop()

    update_script(script, done)
    lines = [f"# Proof report ({now_utc()})", "",
             "| ID | Status | Deep link |", "|---|---|---|"]
    for s in sources:
        st = results.get(s["id"], "not run")
        lines.append(f"| {s['id']} | {st} | [open]({deep_link(s)}) |")
    (proof / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [s["id"] for s in sources if not str(results.get(s["id"], "")).startswith("ok")]
    print(f"\n{len(sources) - len(missing)}/{len(sources)} proofs ready. Missing: {missing or 'none'}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
