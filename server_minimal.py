import os
import sys
print("=== PYTHON STARTED ===", flush=True)

from flask import Flask, jsonify
app = Flask(__name__)

print("=== FLASK CREATED ===", flush=True)

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

@app.route("/book")
def book():
    return jsonify({"metabookers": 0, "used_price": None})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"=== STARTING ON PORT {port} ===", flush=True)
    app.run(host="0.0.0.0", port=port)
