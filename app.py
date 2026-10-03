from __future__ import annotations

import heapq
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

APP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR / "templates"
if not (TEMPLATE_DIR / "index.html").is_file():
    TEMPLATE_DIR = APP_DIR
app = Flask(__name__, template_folder=str(TEMPLATE_DIR))


def simulate(calls, start_floor, travel_time, dwell_time, strategy):
    """Schedule one pickup at a time and return a decision trace and metrics."""
    pending = [dict(call, done=False) for call in calls]
    now = 0
    floor = start_floor
    events, choices, waits = [], [], []
    travel = 0

    while any(not call["done"] for call in pending):
        ready = [c for c in pending if not c["done"] and c["release"] <= now]
        if not ready:
            now = min(c["release"] for c in pending if not c["done"])
            ready = [c for c in pending if not c["done"] and c["release"] <= now]

        if strategy == "greedy":
            # Locally minimize the next pickup leg; ties go to earlier calls.
            chosen = min(ready, key=lambda c: (abs(c["floor"] - floor), c["release"], c["id"]))
            reason = f"Nearest available: {abs(chosen['floor'] - floor)} floor(s) away."
        else:
            # Heap ordering: highest priority, longest wait, nearest, then call ID.
            priority_queue = [
                (-c["priority"], c["release"], abs(c["floor"] - floor), c["id"], c)
                for c in ready
            ]
            heapq.heapify(priority_queue)
            chosen = heapq.heappop(priority_queue)[-1]
            distance = abs(chosen["floor"] - floor)
            waited = max(0, now - chosen["release"])
            reason = (
                f"Priority {chosen['priority']} call; {waited}s waiting so far. "
                f"Distance: {distance} floor(s)."
            )

        distance = abs(chosen["floor"] - floor)
        arrival = now + distance * travel_time
        wait = arrival - chosen["release"]
        travel += distance * travel_time
        events.append({"call": {k: chosen[k] for k in ("id", "floor", "release", "priority")},
                       "arrival": arrival, "wait": wait})
        choices.append({"id": chosen["id"], "at": now, "from": floor,
                        "to": chosen["floor"], "dist": distance,
                        "priority": chosen["priority"], "wait": wait, "rule": reason})
        waits.append(wait)
        chosen["done"] = True
        now = arrival + dwell_time
        floor = chosen["floor"]

    return {
        "events": events,
        "choices": choices,
        "avg": sum(waits) / len(waits) if waits else 0,
        "max": max(waits, default=0),
        "travel": travel,
        "elapsed": now,
    }


@app.errorhandler(Exception)
def show_application_error(error):
    """Show a useful diagnostic for this local educational prototype."""
    from werkzeug.exceptions import HTTPException
    if isinstance(error, HTTPException):
        return error
    app.logger.exception("Unhandled error on %s", request.path)
    return (
        "LiftLab encountered an application error.\n"
        f"Request: {request.method} {request.path}\n"
        f"Error: {type(error).__name__}: {error}\n\n"
        "The full traceback is printed in the PowerShell window running app.py.\n",
        500,
        {"Content-Type": "text/plain; charset=utf-8"},
    )

@app.get("/")
def index():
    return send_from_directory(TEMPLATE_DIR, "index.html")


@app.post("/api/schedule")
def schedule():
    data = request.get_json(silent=True) or {}
    try:
        floors = int(data.get("floor_count", 20))
        start = int(data.get("start_floor", 1))
        speed = int(data.get("travel_time", 3))
        dwell = int(data.get("dwell_time", 8))
        raw_calls = data.get("calls", [])
        if not isinstance(raw_calls, list) or not 1 <= len(raw_calls) <= 20:
            raise ValueError("Provide between 1 and 20 elevator calls.")
        if not 2 <= floors <= 60:
            raise ValueError("Building floors must be between 2 and 60.")
        if not 1 <= start <= floors:
            raise ValueError("Current floor must be inside the building.")
        if not 1 <= speed <= 30 or not 0 <= dwell <= 60:
            raise ValueError("Check the travel and door-time settings.")
        calls = []
        for call_id, item in enumerate(raw_calls, 1):
            floor = int(item["floor"])
            release = int(item.get("release", 0))
            priority = int(item.get("priority", 3))
            if not 1 <= floor <= floors:
                raise ValueError(f"Call #{call_id} is outside the building.")
            if not 0 <= release <= 600 or not 1 <= priority <= 5:
                raise ValueError(f"Call #{call_id} has an invalid release time or priority.")
            calls.append({"id": call_id, "floor": floor, "release": release, "priority": priority})
        return jsonify({
            "greedy": simulate(calls, start, speed, dwell, "greedy"),
            "priority": simulate(calls, start, speed, dwell, "priority"),
        })
    except (TypeError, ValueError, KeyError) as error:
        return jsonify({"error": str(error) or "Invalid scheduling input."}), 400


if __name__ == "__main__":
    app.run(debug=False)







