from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)


def get_book_data(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=20000)
        text = page.locator("body").inner_text()
        browser.close()

    metabookers_match = re.search(
        r"Το θέλουν:\s*(\d+)\s*metabookers",
        text
    )

    price_match = re.search(
        r"(\d+,\d+)\s*€\s*Προσθήκη",
        text
    )

    metabookers = (
        int(metabookers_match.group(1))
        if metabookers_match
        else 0
    )

    used_price = (
        float(price_match.group(1).replace(",", "."))
        if price_match
        else None
    )

    return {
        "metabookers": metabookers,
        "used_price": used_price
    }


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})


@app.route("/book")
def book():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        data = get_book_data(url)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
