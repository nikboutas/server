import os
import re
import sys
import logging
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)

log.info("=== Xanabook Server Starting ===")

app = Flask(__name__)

log.info("Flask app created")


def get_book_data(url: str) -> dict:
    log.info(f"Opening browser for: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-zygote",
                "--single-process",
            ],
        )
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            page.wait_for_timeout(2000)
            text = page.locator("body").inner_text()
            log.info(f"Page loaded, text length: {len(text)}")
        finally:
            browser.close()

    metabookers_match = re.search(r"Το θέλουν:\s*(\d+)\s*metabookers", text)
    price_match       = re.search(r"(\d+,\d+)\s*€\s*Προσθήκη", text)

    result = {
        "metabookers": int(metabookers_match.group(1)) if metabookers_match else 0,
        "used_price":  float(price_match.group(1).replace(",", ".")) if price_match else None,
    }
    log.info(f"Result: {result}")
    return result


@app.route("/ping")
def ping():
    log.info("Ping received")
    return jsonify({"status": "ok"}), 200


@app.route("/book")
def book():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        data = get_book_data(url)
        return jsonify(data)
    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    log.info(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
