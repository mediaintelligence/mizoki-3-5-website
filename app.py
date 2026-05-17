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
EXTERNAL_DASHBOARD_URL = "https://mizoki.mizoki3.com/dashboard"
EXTERNAL_LOGIN_URL = "https://mizoki.mizoki3.com/login"
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

    @app.route("/counsel")
    @app.route("/counsel.html")
    def counsel():
        return serve_page("counsel.html")

    @app.route("/estate")
    @app.route("/estate.html")
    def estate():
        return serve_page("estate.html")

    @app.route("/capital")
    @app.route("/capital.html")
    def capital():
        return serve_page("capital.html")

    @app.route("/signal")
    @app.route("/signal.html")
    def signal():
        return serve_page("signal.html")

    @app.route("/risk")
    @app.route("/risk.html")
    def risk():
        return serve_page("risk.html")

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
        return send_from_directory(BASE_DIR / "blog", filename)

    @app.route("/11/")
    @app.route("/11/index.html")
    def v11_home():
        return send_from_directory(BASE_DIR / "11", "index.html")

    @app.route("/11/<path:filename>")
    def v11_page(filename: str):
        return send_from_directory(BASE_DIR / "11", filename)

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
        return (
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>404 - Page Not Found</title>
                <link rel="stylesheet" href="/assets/css/styles.css"/>
                <style>
                    .error-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; text-align: center; }
                </style>
            </head>
            <body>
                <div class="error-page">
                    <div>
                        <h1 style="font-size: 4rem; color: var(--accent);">404</h1>
                        <p style="color: var(--muted);">Page not found</p>
                        <a href="/" class="btn primary" style="margin-top: 1rem;">Go Home</a>
                    </div>
                </div>
            </body>
            </html>
            """,
            404,
        )

    @app.errorhandler(500)
    def internal_error(_error):
        return json_error("Internal server error", 500)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
