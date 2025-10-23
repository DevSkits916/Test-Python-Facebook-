import json
import os
import threading
import time
from datetime import datetime
from queue import Queue, Empty
from typing import Dict, Optional

from flask import Flask, jsonify, render_template, request, Response

from browser_engine import BrowserAutomationEngine, AutomationError
from content_manager import ContentManager, ContentItem


os.environ.setdefault("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
os.environ.setdefault("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

app = Flask(__name__)

# Thread coordination primitives
_automation_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_status_queue: "Queue[Dict[str, str]]" = Queue()
_current_state: Dict[str, str] = {
    "status": "idle",
    "message": "Automation idle.",
    "last_update": datetime.utcnow().isoformat(),
    "progress": "0"
}

CONTENT_SOURCE = os.getenv("CONTENT_SOURCE", "data/post_variations.csv")


def log_status(message: str, status: str = "info", progress: Optional[float] = None) -> None:
    """Push a status update to the streaming queue."""
    payload = {
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if progress is not None:
        payload["progress"] = f"{progress:.2f}"
    else:
        payload["progress"] = _current_state.get("progress", "0")
    _status_queue.put(payload)
    _current_state.update({
        "status": status,
        "message": message,
        "last_update": payload["timestamp"],
        "progress": payload["progress"],
    })


def automation_worker(credentials: Dict[str, str], configuration: Dict[str, str]) -> None:
    """Background automation thread."""
    engine: Optional[BrowserAutomationEngine] = None
    try:
        log_status("Loading content variations", "info", 0)
        content_manager = ContentManager(CONTENT_SOURCE)
        engine = BrowserAutomationEngine(configuration=configuration, status_callback=log_status)

        log_status("Setting up browser", "info")
        engine.setup_browser()

        total_items = content_manager.remaining_items
        processed = 0
        log_status("Starting posting workflow", "running", 0)

        while not _stop_event.is_set() and content_manager.has_content:
            content: ContentItem = content_manager.next_content()
            try:
                engine.human_like_interaction()
                engine.platform_login(credentials)
                engine.navigate_interface(content)
                engine.submit_content(content)
                content_manager.mark_used(content)
                processed += 1
                progress = (processed / total_items) * 100 if total_items else 100
                log_status(f"Posted variation '{content.title}'", "running", progress)
            except AutomationError as error:
                log_status(f"Automation error: {error}", "error")
                engine.recover_from_error(error)
            except Exception as exc:  # pylint: disable=broad-except
                log_status(f"Unexpected error: {exc}", "error")
                engine.capture_debug_artifacts(reason=str(exc))
                engine.recover_from_error(exc)
            time.sleep(engine.random_delay())

        if _stop_event.is_set():
            log_status("Automation stopped by user", "stopped", float(_current_state.get("progress", "0")))
        else:
            log_status("Automation completed all content", "complete", 100)
    finally:
        if engine:
            engine.shutdown()
        _stop_event.clear()
        global _automation_thread  # pylint: disable=global-statement
        _automation_thread = None


@app.route("/")
def dashboard():
    return render_template("dashboard.html", state=_current_state)


@app.route("/configuration")
def configuration_page():
    return render_template("configuration.html")


@app.route("/results")
def results_page():
    return render_template("results.html", state=_current_state)


@app.route("/start-campaign", methods=["POST"])
def start_automation_campaign():
    global _automation_thread  # pylint: disable=global-statement
    if _automation_thread and _automation_thread.is_alive():
        return jsonify({"status": "error", "message": "Automation already running"}), 409

    payload = request.json or {}
    credentials = payload.get("credentials", {})
    configuration = payload.get("configuration", {})

    _stop_event.clear()
    _automation_thread = threading.Thread(
        target=automation_worker,
        args=(credentials, configuration),
        daemon=True,
        name="automation-worker",
    )
    _automation_thread.start()
    log_status("Automation campaign started", "running", 0)
    return jsonify({"status": "ok", "message": "Automation started"})


@app.route("/automation-status")
def real_time_status():
    def event_stream():
        while True:
            try:
                update = _status_queue.get(timeout=1)
            except Empty:
                if not (_automation_thread and _automation_thread.is_alive()):
                    # Send heartbeat
                    heartbeat = {
                        "status": _current_state.get("status", "idle"),
                        "message": _current_state.get("message", "Idle"),
                        "timestamp": datetime.utcnow().isoformat(),
                        "progress": _current_state.get("progress", "0"),
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
                continue
            yield f"data: {json.dumps(update)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/emergency-stop", methods=["POST"])
def stop_automation():
    _stop_event.set()
    if _automation_thread and _automation_thread.is_alive():
        log_status("Emergency stop requested", "warning")
    return jsonify({"status": "ok", "message": "Stop signal sent"})


@app.route("/status")
def status_snapshot():
    return jsonify(_current_state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
