"""Minimal checkout service demo.

Exposes a single /checkout endpoint that calls out to a (simulated)
downstream payment gateway and retries on transient failures.
"""

import time

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

PAYMENT_GATEWAY_URL = "https://payments.internal.example.com/charge"

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 0.5


def call_payment_gateway(order_id: str, amount_cents: int) -> dict:
    """Call the payment gateway, retrying transient failures with backoff."""
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                PAYMENT_GATEWAY_URL,
                json={"order_id": order_id, "amount_cents": amount_cents},
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(BASE_BACKOFF_SECONDS * (2**attempt))

    raise RuntimeError(f"payment gateway failed after {MAX_RETRIES} attempts") from last_error


@app.route("/checkout", methods=["POST"])
def checkout():
    payload = request.get_json(force=True)
    order_id = payload["order_id"]
    amount_cents = payload["amount_cents"]

    result = call_payment_gateway(order_id, amount_cents)
    return jsonify({"status": "charged", "order_id": order_id, "gateway": result})


if __name__ == "__main__":
    app.run(port=8090)
