import json
import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from functools import wraps

from mizoki_runtime import BossRuntime, create_runtime


BASE_DIR = Path(__file__).resolve().parent
EXTERNAL_DASHBOARD_URL = "https://miz-oki-command-center-ui-ehqxake3ia-uc.a.run.app/dashboard"
EXTERNAL_LOGIN_URL = "https://miz-oki-command-center-ui-ehqxake3ia-uc.a.run.app/login"
TOP_LEVEL_STATIC_EXTENSIONS = {
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".map",
    ".md",
    ".pdf",
    ".png",
    ".svg",
    ".txt",
    ".xml",
    ".zip",
}
ALLOWED_TEMPLATES = {
    "contact.html",
    "index.html",
    "intelligence.html",
    "vision.html",
}


def _load_demo_users() -> dict[str, str]:
    raw_payload = os.environ.get("MIZOKI_DEMO_USERS_JSON", "").strip()
    if not raw_payload:
        return {}

    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("MIZOKI_DEMO_USERS_JSON must be valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("MIZOKI_DEMO_USERS_JSON must be an object of {email: password}.")

    users: dict[str, str] = {}
    for email, password in parsed.items():
        if not isinstance(email, str) or not isinstance(password, str):
            raise RuntimeError("All MIZOKI_DEMO_USERS_JSON keys and values must be strings.")
        users[email.strip().lower()] = password
    return users


def create_app(runtime: BossRuntime | None = None) -> Flask:
    app = Flask(__name__, static_folder="assets", static_url_path="/assets")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("ENVIRONMENT", "").lower() == "production",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        JSON_SORT_KEYS=False,
    )

    app.config["MIZOKI_DEMO_USERS"] = _load_demo_users()
    app.extensions["boss_runtime"] = runtime or create_runtime(BASE_DIR)

    def get_runtime() -> BossRuntime:
        return app.extensions["boss_runtime"]

    def login_required(view_func):
        @wraps(view_func)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login_page"))
            return view_func(*args, **kwargs)

        return decorated_function

    def json_error(message: str, status_code: int):
        if request.path.startswith("/api/"):
            return jsonify({"error": message}), status_code
        return message, status_code

    def require_json_payload() -> dict:
        if not request.is_json:
            abort(400, description="Request must use application/json.")
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            abort(400, description="JSON body must be an object.")
        return payload

    def run_runtime_call(operation):
        try:
            return operation()
        except ValueError as exc:
            abort(400, description=str(exc))

    def serve_page(filename: str):
        return send_from_directory(BASE_DIR, filename)

    @app.route("/")
    def home():
        return serve_page("index.html")

    @app.route("/index.html")
    def index():
        return serve_page("index.html")

    def serve_dir_page(dirname: str):
        return send_from_directory(BASE_DIR / dirname, "index.html")

    @app.route("/counsel")
    @app.route("/counsel/")
    @app.route("/counsel.html")
    def counsel():
        return serve_dir_page("counsel")

    @app.route("/estate")
    @app.route("/estate/")
    @app.route("/estate.html")
    def estate():
        return serve_dir_page("estate")

    @app.route("/capital")
    @app.route("/capital/")
    @app.route("/capital.html")
    def capital():
        return serve_dir_page("capital")

    @app.route("/signal")
    @app.route("/signal/")
    @app.route("/signal.html")
    def signal():
        return serve_dir_page("signal")

    @app.route("/risk")
    @app.route("/risk/")
    @app.route("/risk.html")
    def risk():
        return serve_dir_page("risk")

    @app.route("/privacy")
    @app.route("/privacy/")
    def privacy():
        return serve_dir_page("privacy")

    @app.route("/terms")
    @app.route("/terms/")
    def terms():
        return serve_dir_page("terms")

    @app.route("/how-it-works.html")
    @app.route("/platform.html")
    @app.route("/security.html")
    @app.route("/industries.html")
    @app.route("/pricing.html")
    @app.route("/case-studies.html")
    @app.route("/resources.html")
    @app.route("/roi.html")
    @app.route("/walkthrough.html")
    @app.route("/investor.html")
    @app.route("/sales-one-pager.html")
    @app.route("/demo-opener.html")
    def legacy_marketing_page():
        return redirect(url_for("home"), code=301)

    @app.route("/blogs")
    @app.route("/blogs/")
    @app.route("/blogs.html")
    def blogs_page():
        return redirect(url_for("blog_index"), code=301)

    @app.route("/blog")
    def blog_index():
        return send_from_directory(BASE_DIR / "blog", "index.html")

    @app.route("/blog/")
    @app.route("/blog/index.html")
    def blog_index_legacy():
        return redirect(url_for("blog_index"), code=301)

    @app.route("/blog/relu-lens-meta-algorithm")
    def blog_relu_lens_article():
        return send_from_directory(BASE_DIR / "blog", "relu-lens-meta-algorithm.html")

    @app.route("/blog/relu-lens-meta-algorithm/")
    @app.route("/blog/relu-lens-meta-algorithm.html")
    @app.route("/blog/meta-relu-gate-go-deep-before-wide")
    @app.route("/blog/meta-relu-gate-go-deep-before-wide/")
    @app.route("/blog/meta-relu-gate-go-deep-before-wide.html")
    @app.route("/blog/meta-relu-gate-go-deep-before-wide/index.html")
    def legacy_blog_relu_lens_article():
        return redirect(url_for("blog_relu_lens_article"), code=301)

    @app.route("/blog/<path:filename>")
    def blog_post(filename: str):
        blog_dir = BASE_DIR / "blog"
        if (blog_dir / filename).is_file():
            return send_from_directory(blog_dir, filename)
        # Directory-style articles (blog/<slug>/index.html)
        slug = filename.rstrip("/")
        if (blog_dir / slug / "index.html").is_file():
            return send_from_directory(blog_dir, f"{slug}/index.html")
        if (blog_dir / f"{filename}.html").is_file():
            return send_from_directory(blog_dir, f"{filename}.html")
        return send_from_directory(blog_dir, filename)

    @app.route("/11/")
    @app.route("/11/index.html")
    def v11_home():
        return send_from_directory(BASE_DIR / "11", "index.html")

    @app.route("/11/<path:filename>")
    def v11_page(filename: str):
        return send_from_directory(BASE_DIR / "11", filename)

    @app.route("/console")
    @app.route("/console/")
    @app.route("/console/index.html")
    def console_home():
        return send_from_directory(BASE_DIR / "mizoki3-site" / "console", "index.html")

    @app.route("/console/<path:filename>")
    def console_asset(filename: str):
        return send_from_directory(BASE_DIR / "mizoki3-site" / "console", filename)

    @app.route("/infrastructure/main.tf")
    def infrastructure_terraform():
        return send_from_directory(
            BASE_DIR / "mizoki3-site" / "infrastructure",
            "main.tf",
            mimetype="text/plain",
        )

    @app.route("/1")
    @app.route("/1/")
    @app.route("/1/index.html")
    def app1_home():
        return send_from_directory(BASE_DIR / "1", "index.html")

    @app.route("/1/<path:filename>")
    def app1_asset(filename: str):
        static_dir = BASE_DIR / "1"
        target = static_dir / filename
        if not target.is_file():
            return send_from_directory(static_dir, "index.html")
        return send_from_directory(static_dir, filename)

    @app.route("/2")
    @app.route("/2/")
    @app.route("/2/index.html")
    def app2_home():
        return send_from_directory(BASE_DIR / "2", "index.html")

    @app.route("/2/<path:filename>")
    def app2_asset(filename: str):
        static_dir = BASE_DIR / "2"
        target = static_dir / filename
        if not target.is_file():
            return send_from_directory(static_dir, "index.html")
        return send_from_directory(static_dir, filename)

    @app.route("/3")
    @app.route("/3/")
    @app.route("/3/index.html")
    def app3_home():
        return send_from_directory(BASE_DIR / "3", "index.html")

    @app.route("/3/<path:filename>")
    def app3_asset(filename: str):
        static_dir = BASE_DIR / "3"
        target = static_dir / filename
        if not target.is_file():
            return send_from_directory(static_dir, "index.html")
        return send_from_directory(static_dir, filename)

    @app.route("/4")
    @app.route("/4/")
    @app.route("/4/index.html")
    def app4_home():
        return send_from_directory(BASE_DIR / "4", "index.html")

    @app.route("/4/<path:filename>")
    def app4_asset(filename: str):
        static_dir = BASE_DIR / "4"
        target = static_dir / filename
        if target.is_file():
            return send_from_directory(static_dir, filename)
        # Directory-style pages (counsel/index.html, blog/<slug>/index.html)
        page = target / "index.html"
        if page.is_file():
            return send_from_directory(static_dir, f"{filename.rstrip('/')}/index.html")
        return send_from_directory(static_dir, "index.html")

    @app.route("/login", methods=["GET"])
    @app.route("/login.html", methods=["GET"])
    def login_page():
        if "user" in session:
            return redirect(EXTERNAL_DASHBOARD_URL)
        return redirect(EXTERNAL_LOGIN_URL, code=302)

    @app.route("/login", methods=["POST"])
    def login():
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        demo_users = app.config["MIZOKI_DEMO_USERS"]

        if not demo_users:
            flash("Local demo login is disabled. Redirecting to the command center login.", "info")
            return redirect(EXTERNAL_LOGIN_URL)

        if email in demo_users and demo_users[email] == password:
            session.permanent = True
            session["user"] = email
            return redirect(EXTERNAL_DASHBOARD_URL)

        flash("Invalid email or password.", "error")
        return redirect(url_for("login_page"))

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        flash("You have been logged out.", "info")
        return redirect(url_for("home"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return redirect(EXTERNAL_DASHBOARD_URL)

    @app.route("/templates/<path:filename>")
    def serve_template(filename: str):
        if filename not in ALLOWED_TEMPLATES:
            abort(404)
        return render_template(filename)

    @app.route("/api/health")
    def api_health():
        return jsonify(get_runtime().health_snapshot())

    @app.route("/health")
    def health():
        return "healthy", 200

    @app.route("/api/mcp/tools", methods=["GET"])
    def list_mcp_tools():
        return jsonify({"tools": get_runtime().list_tools()})

    @app.route("/api/mcp/call", methods=["POST"])
    def call_mcp_tool():
        payload = require_json_payload()
        tool_name = payload.get("name")
        arguments = payload.get("arguments", {})
        if not isinstance(tool_name, str) or not tool_name.strip():
            abort(400, description="Field 'name' must be a non-empty string.")
        if not isinstance(arguments, dict):
            abort(400, description="Field 'arguments' must be an object.")
        return jsonify(run_runtime_call(lambda: get_runtime().call_tool(tool_name, arguments)))

    @app.route("/api/boss/discover", methods=["GET"])
    def discover_boss_capabilities():
        return jsonify(get_runtime().discover())

    @app.route("/api/boss/graph/subagents", methods=["GET"])
    def list_graph_subagents():
        return jsonify({"subagents": get_runtime().list_subagents()})

    @app.route("/api/boss/graph/context", methods=["POST"])
    def boss_graph_context():
        payload = require_json_payload()
        intent = payload.get("intent", "")
        top_k = payload.get("top_k", 3)
        constraints = payload.get("constraints", [])
        if not isinstance(intent, str) or not intent.strip():
            abort(400, description="Field 'intent' must be a non-empty string.")
        if not isinstance(top_k, int):
            abort(400, description="Field 'top_k' must be an integer.")
        if not isinstance(constraints, list):
            abort(400, description="Field 'constraints' must be an array.")
        return jsonify(
            {
                "context": run_runtime_call(
                    lambda: get_runtime().graph_context(intent, top_k=top_k, constraints=constraints)
                )
            }
        )

    @app.route("/api/boss/graph/simulate", methods=["POST"])
    def boss_graph_simulation():
        payload = require_json_payload()
        intent = payload.get("intent", "")
        proposed_action = payload.get("proposed_action", "")
        top_k = payload.get("top_k", 3)
        constraints = payload.get("constraints", [])
        if not isinstance(intent, str) or not intent.strip():
            abort(400, description="Field 'intent' must be a non-empty string.")
        if not isinstance(proposed_action, str):
            abort(400, description="Field 'proposed_action' must be a string.")
        if not isinstance(top_k, int):
            abort(400, description="Field 'top_k' must be an integer.")
        if not isinstance(constraints, list):
            abort(400, description="Field 'constraints' must be an array.")
        return jsonify(
            run_runtime_call(
                lambda: get_runtime().simulate_graph_action(
                    intent,
                    proposed_action=proposed_action,
                    constraints=constraints,
                    top_k=top_k,
                )
            )
        )

    @app.route("/api/boss/graph/loop", methods=["POST"])
    def boss_graph_loop():
        payload = require_json_payload()
        intent = payload.get("intent", "")
        goal = payload.get("goal", "")
        proposed_action = payload.get("proposed_action", "")
        top_k = payload.get("top_k", 3)
        constraints = payload.get("constraints", [])
        if not isinstance(intent, str) or not intent.strip():
            abort(400, description="Field 'intent' must be a non-empty string.")
        if not isinstance(goal, str):
            abort(400, description="Field 'goal' must be a string.")
        if not isinstance(proposed_action, str):
            abort(400, description="Field 'proposed_action' must be a string.")
        if not isinstance(top_k, int):
            abort(400, description="Field 'top_k' must be an integer.")
        if not isinstance(constraints, list):
            abort(400, description="Field 'constraints' must be an array.")
        return jsonify(
            run_runtime_call(
                lambda: get_runtime().run_decision_loop(
                    intent,
                    goal=goal,
                    proposed_action=proposed_action,
                    constraints=constraints,
                    top_k=top_k,
                )
            )
        )

    @app.route("/api/boss/programmatic/ingest", methods=["POST"])
    def boss_programmatic_ingest():
        payload = require_json_payload()
        events = payload.get("events")
        if not isinstance(events, list):
            abort(400, description="Field 'events' must be an array of bidstream records.")
        return jsonify(run_runtime_call(lambda: get_runtime().ingest_bidstream(events)))

    @app.route("/api/boss/programmatic/run", methods=["POST"])
    def boss_programmatic_run():
        payload = require_json_payload()
        events = payload.get("events")
        objective = payload.get("objective", "")
        constraints = payload.get("constraints", [])
        budget = payload.get("budget")
        auto_execute = payload.get("auto_execute", False)
        max_actions = payload.get("max_actions", 3)
        if not isinstance(events, list):
            abort(400, description="Field 'events' must be an array of bidstream records.")
        if not isinstance(objective, str):
            abort(400, description="Field 'objective' must be a string.")
        if not isinstance(constraints, list):
            abort(400, description="Field 'constraints' must be an array.")
        if budget is not None and (isinstance(budget, bool) or not isinstance(budget, (int, float))):
            abort(400, description="Field 'budget' must be a number.")
        if not isinstance(auto_execute, bool):
            abort(400, description="Field 'auto_execute' must be a boolean.")
        if not isinstance(max_actions, int) or isinstance(max_actions, bool):
            abort(400, description="Field 'max_actions' must be an integer.")
        return jsonify(
            run_runtime_call(
                lambda: get_runtime().run_programmatic_pipeline(
                    events,
                    objective=objective,
                    constraints=constraints,
                    budget=budget,
                    auto_execute=auto_execute,
                    max_actions=max_actions,
                )
            )
        )

    @app.route("/api/boss/programmatic/runs", methods=["GET"])
    def boss_programmatic_runs():
        limit = request.args.get("limit", default=5, type=int)
        limit = max(1, min(limit, 25))
        return jsonify({"runs": get_runtime().recent_programmatic_runs(limit=limit)})

    @app.route("/schemas/journey-event.json", methods=["GET"])
    def journey_event_schema():
        schema_path = BASE_DIR / "schemas" / "journey-event.json"
        if not schema_path.is_file():
            abort(404)
        return send_from_directory(
            schema_path.parent,
            schema_path.name,
            mimetype="application/schema+json",
        )

    @app.route("/api/boss/journey/normalize", methods=["POST"])
    def boss_journey_normalize():
        payload = require_json_payload()
        source = payload.get("source", "")
        record = payload.get("payload")
        if not isinstance(source, str) or not source.strip():
            abort(400, description="Field 'source' must be a non-empty string.")
        if not isinstance(record, dict):
            abort(400, description="Field 'payload' must be an object.")
        return jsonify(run_runtime_call(lambda: get_runtime().normalize_journey_event(source, record)))

    @app.route("/api/boss/journey/ingest", methods=["POST"])
    def boss_journey_ingest():
        payload = require_json_payload()
        source = payload.get("source", "")
        events = payload.get("events")
        replay = payload.get("replay", False)
        if not isinstance(source, str) or not source.strip():
            abort(400, description="Field 'source' must be a non-empty string.")
        if not isinstance(events, list):
            abort(400, description="Field 'events' must be an array of source records.")
        if not isinstance(replay, bool):
            abort(400, description="Field 'replay' must be a boolean.")
        return jsonify(
            run_runtime_call(lambda: get_runtime().ingest_journey_events(source, events, replay=replay))
        )

    @app.route("/api/boss/journey/events", methods=["GET"])
    def boss_journey_events():
        limit = request.args.get("limit", default=10, type=int)
        limit = max(1, min(limit, 100))
        return jsonify({"events": get_runtime().recent_journey_events(limit=limit)})

    @app.route("/schemas/canonical-event-envelope.json", methods=["GET"])
    def canonical_envelope_schema():
        schema_path = BASE_DIR / "schemas" / "canonical-event-envelope.json"
        if not schema_path.is_file():
            abort(404)
        return send_from_directory(
            schema_path.parent,
            schema_path.name,
            mimetype="application/schema+json",
        )

    @app.route("/api/boss/journey/envelope", methods=["POST"])
    def boss_journey_envelope():
        payload = require_json_payload()
        source = payload.get("source", "")
        record = payload.get("payload")
        if not isinstance(source, str) or not source.strip():
            abort(400, description="Field 'source' must be a non-empty string.")
        if not isinstance(record, dict):
            abort(400, description="Field 'payload' must be an object.")
        context = {
            key: payload[key]
            for key in ("business_context", "reasoning_context", "causal", "intelligence")
            if isinstance(payload.get(key), dict)
        }
        return jsonify(run_runtime_call(lambda: get_runtime().build_journey_envelope(source, record, **context)))

    @app.route("/api/boss/skills/learn", methods=["POST"])
    def learn_boss_skill():
        payload = require_json_payload()
        required_fields = ("name", "description", "trigger_phrases")
        for field in required_fields:
            if field not in payload:
                abort(400, description=f"Missing required field: {field}")
        return jsonify({"skill": run_runtime_call(lambda: get_runtime().learn_skill(payload))})

    @app.route("/api/boss/skills/learn-from-loop", methods=["POST"])
    def learn_boss_skill_from_loop():
        payload = require_json_payload()
        trace_id = payload.get("trace_id", "")
        name = payload.get("name", "")
        description = payload.get("description", "")
        if not isinstance(trace_id, str):
            abort(400, description="Field 'trace_id' must be a string.")
        if not isinstance(name, str):
            abort(400, description="Field 'name' must be a string.")
        if not isinstance(description, str):
            abort(400, description="Field 'description' must be a string.")
        return jsonify(
            {
                "skill": run_runtime_call(
                    lambda: get_runtime().learn_skill_from_loop(
                        trace_id=trace_id,
                        name=name,
                        description=description,
                    )
                )
            }
        )

    @app.route("/api/boss/execute", methods=["POST"])
    def execute_with_boss():
        payload = require_json_payload()
        intent = payload.get("intent", "")
        arguments = payload.get("arguments", {})
        if not isinstance(intent, str) or not intent.strip():
            abort(400, description="Field 'intent' must be a non-empty string.")
        if not isinstance(arguments, dict):
            abort(400, description="Field 'arguments' must be an object.")
        return jsonify(run_runtime_call(lambda: get_runtime().execute(intent, arguments)))

    @app.route("/api/boss/traces", methods=["GET"])
    def boss_traces():
        limit = request.args.get("limit", default=5, type=int)
        limit = max(1, min(limit, 25))
        return jsonify({"traces": get_runtime().recent_traces(limit=limit)})

    @app.route("/<path:filename>")
    def top_level_static(filename: str):
        path = BASE_DIR / filename
        if path.is_file() and path.suffix.lower() in TOP_LEVEL_STATIC_EXTENSIONS and path.parent == BASE_DIR:
            return send_from_directory(BASE_DIR, filename)
        abort(404)

    @app.errorhandler(400)
    def bad_request(error):
        return json_error(getattr(error, "description", "Bad request"), 400)

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        page = BASE_DIR / "404.html"
        if page.is_file():
            return send_from_directory(BASE_DIR, "404.html"), 404
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(_error):
        return json_error("Internal server error", 500)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
