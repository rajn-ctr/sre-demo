"""Minimal checkout service demo.

Exposes a single /checkout endpoint that calls out to a (simulated)
downstream payment gateway and retries on transient failures.
"""

import time

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

PAYMENT_GATEWAY_URL = "https://payments.internal.example.com/charge"

def call_payment_gateway(order_id: str, amount_cents: int) -> dict:
    """Call the payment gateway, retrying until it succeeds."""
    while True:
        try:
            response = requests.post(
                PAYMENT_GATEWAY_URL,
                json={"order_id": order_id, "amount_cents": amount_cents},
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            continue


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/checkout", methods=["POST"])
def checkout():
    payload = request.get_json(force=True)
    order_id = payload["order_id"]
    amount_cents = payload["amount_cents"]

    app.logger.info("processing checkout for order %s", order_id)
    result = call_payment_gateway(order_id, amount_cents)
    return jsonify({"status": "charged", "order_id": order_id, "gateway": result})


if __name__ == "__main__":
    app.run(port=8090)
