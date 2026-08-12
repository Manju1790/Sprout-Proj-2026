import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from database import (
    init_db,
    create_ticket,
    get_ticket,
    get_tickets,
    update_status,
    get_stats,
)
from graph import build_graph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

init_db()
ticket_graph = build_graph()

VALID_STATUSES = {
    "Open",
    "In Progress",
    "Resolved",
    "Closed",
}


def validate_ticket(data):
    required = ["name", "email", "subject", "description"]

    for field in required:
        if not str(data.get(field, "")).strip():
            return f"{field} is required"

    return None


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Smart Support Ticket API"
    })


@app.get("/api/stats")
def stats():
    return jsonify(get_stats())


@app.get("/api/tickets")
def tickets():
    result = get_tickets(
        status=request.args.get("status"),
        category=request.args.get("category"),
        priority=request.args.get("priority"),
        search=request.args.get("search"),
    )
    return jsonify(result)


@app.get("/api/tickets/<int:ticket_id>")
def ticket(ticket_id):
    result = get_ticket(ticket_id)

    if not result:
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify(result)


@app.post("/api/tickets/analyze")
def analyze():
    data = request.get_json(silent=True) or {}

    if not data.get("subject") or not data.get("description"):
        return jsonify({
            "error": "subject and description are required"
        }), 400

    state = {
        "subject": data["subject"],
        "description": data["description"],
    }

    result = ticket_graph.invoke(state)
    return jsonify(result)


@app.post("/api/tickets")
def create():
    data = request.get_json(silent=True) or {}

    error = validate_ticket(data)

    if error:
        return jsonify({"error": error}), 400

    state = {
        "subject": data["subject"],
        "description": data["description"],
    }

    analysis = ticket_graph.invoke(state)

    ticket_data = {
        **data,
        **analysis,
    }

    result = create_ticket(ticket_data)

    return jsonify(result), 201


@app.patch("/api/tickets/<int:ticket_id>/status")
def change_status(ticket_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in VALID_STATUSES:
        return jsonify({
            "error": "Invalid status",
            "allowed": sorted(VALID_STATUSES)
        }), 400

    if not update_status(ticket_id, status):
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify(get_ticket(ticket_id))


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "API route not found"}), 404

    requested = os.path.join(STATIC_DIR, path)

    if path and os.path.isfile(requested):
        return send_from_directory(STATIC_DIR, path)

    index_path = os.path.join(STATIC_DIR, "index.html")

    if os.path.isfile(index_path):
        return send_from_directory(STATIC_DIR, "index.html")

    return """
    <h2>React frontend has not been built.</h2>
    <p>For development, run:</p>
    <pre>cd frontend
npm install
npm run dev</pre>
    """, 503


if __name__ == "__main__":
    app.run(debug=True)
