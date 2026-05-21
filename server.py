import os
import re
import logging
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

# ─── Playwright browser (singleton — ανοίγει μία φορά) ────────────────────────
_playwright = None
_browser    = None

def get_browser():
    global _playwright, _browser
    if _browser is None or not _browser.is_connected():
        log.info("Launching Chromium...")
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )
        log.info("Chromium ready.")
    return _browser


# ─── Scraping ──────────────────────────────────────────────────────────────────
def get_book_data(url: str) -> dict:
    browser = get_browser()
    page = browser.new_page()
    try:
        page.goto(url, wait_until="networkidle", timeout=20_000)
        text = page.locator("body").inner_text()
    finally:
        page.close()

    metabookers_match = re.search(
        r"Το θέλουν:\s*(\d+)\s*metabookers", text
    )
    price_match = re.search(
        r"(\d+,\d+)\s*€\s*Προσθήκη", text
    )

    return {
        "metabookers": int(metabookers_match.group(1)) if metabookers_match else 0,
        "used_price":  float(price_match.group(1).replace(",", ".")) if price_match else None,
    }


# ─── Routes ────────────────────────────────────────────────────────────────────
@app.route("/ping")
def ping():
    """Keep-alive endpoint — καλείται κάθε 5 λεπτά από το app."""
    return jsonify({"status": "ok"}), 200


@app.route("/book")
def book():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400

    log.info(f"Fetching: {url}")
    try:
        data = get_book_data(url)
        log.info(f"Result: {data}")
        return jsonify(data)
    except Exception as e:
        log.error(f"Error: {e}")
        # Browser crash → reset για την επόμενη κλήση
        global _browser, _playwright
        try:
            _browser.close()
        except Exception:
            pass
        _browser    = None
        _playwright = None
        return jsonify({"error": str(e)}), 500


# ─── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    log.info(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
