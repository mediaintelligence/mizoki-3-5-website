import hashlib
import json
import math
import os
import secrets
import threading
import time
from datetime import timedelta
from functools import lru_cache
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
from mizoki_runtime import (
    demo_capital,
    demo_counsel,
    demo_estate,
    demo_narrator,
    demo_nexus,
    demo_risk,
    demo_signal,
    demo_telemetry,
)
from mizoki_runtime import briefing_guide


BASE_DIR = Path(__file__).resolve().parent
CANONICAL_HOST = "mizoki3.com"
CANONICAL_BASE_URL = f"https://{CANONICAL_HOST}"
# D3 fix: both URLs are env-tunable and default to on-site destinations —
# the old mizoki.mizoki3.com subdomain redirect-looped.
EXTERNAL_DASHBOARD_URL = os.environ.get("MIZOKI_EXTERNAL_DASHBOARD_URL", "/console")
EXTERNAL_LOGIN_URL = os.environ.get("MIZOKI_EXTERNAL_LOGIN_URL", "/admin/login")
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


_BLOG_MANIFEST_PATH = BASE_DIR / "blog" / "posts.json"


def _load_blog_manifest() -> list[dict]:
    """Read blog/posts.json and return the list of post dicts (sorted newest first)."""
    if not _BLOG_MANIFEST_PATH.exists():
        return []
    try:
        with _BLOG_MANIFEST_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        posts = data.get("posts", []) if isinstance(data, dict) else []
        posts.sort(key=lambda p: p.get("published", ""), reverse=True)
        return posts
    except (json.JSONDecodeError, OSError):
        return []


def _xml_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _render_rss(posts: list[dict], base_url: str) -> str:
    """Render an RSS 2.0 feed from the manifest."""
    from datetime import datetime, timezone

    def to_rfc822(date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except (ValueError, TypeError):
            return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    items_xml: list[str] = []
    for p in posts:
        url = f"{base_url}/blog/{p['slug']}"
        items_xml.append(
            "    <item>\n"
            f"      <title>{_xml_escape(p['title'])}</title>\n"
            f"      <link>{_xml_escape(url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{_xml_escape(url)}</guid>\n"
            f"      <description>{_xml_escape(p.get('summary', ''))}</description>\n"
            f"      <pubDate>{to_rfc822(p.get('published', ''))}</pubDate>\n"
            f"      <author>research@mizoki3.com ({_xml_escape(p.get('author', 'MIZ OKI'))})</author>\n"
            + "".join(f"      <category>{_xml_escape(t)}</category>\n" for t in p.get("tags", []))
            + "    </item>"
        )
    body = "\n".join(items_xml)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        "    <title>MIZ OKI 3.5 Blog</title>\n"
        f"    <link>{_xml_escape(base_url)}/blog</link>\n"
        f"    <atom:link href=\"{_xml_escape(base_url)}/blog/feed.xml\" rel=\"self\" type=\"application/rss+xml\" />\n"
        "    <description>Research and field notes on threshold-aware media buying, decision intelligence, and causal autonomous systems.</description>\n"
        "    <language>en-us</language>\n"
        f"    <lastBuildDate>{to_rfc822(posts[0].get('published', '')) if posts else ''}</lastBuildDate>\n"
        f"{body}\n"
        "  </channel>\n"
        "</rss>\n"
    )


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


class DemoRateLimiter:
    """Stdlib in-memory token bucket keyed by client IP (first XFF hop).

    Buckets start with ``per_min`` tokens and refill at ``per_min``/minute;
    ``burst`` extra capacity accumulates only while a client is idle, so a
    cold client gets exactly ``per_min`` weighted requests in its first
    minute (the 31st weight-1 request 429s at the defaults). Telemetry has
    its own, separate bucket. All knobs are env-tunable so launch tuning
    needs no deploy.
    """

    def __init__(self, per_min: int, burst: int, telemetry_per_min: int) -> None:
        self.per_min = max(1, per_min)
        self.burst = max(0, burst)
        self.telemetry_per_min = max(1, telemetry_per_min)
        self._lock = threading.Lock()
        self._buckets: dict[tuple[str, str], list[float]] = {}

    @staticmethod
    def client_key() -> str:
        forwarded = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        return forwarded or (request.remote_addr or "unknown")

    def check(self, key: str, weight: float, bucket: str = "demo") -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        if bucket == "telemetry":
            start = capacity = float(self.telemetry_per_min)
            refill = self.telemetry_per_min / 60.0
        else:
            start = float(self.per_min)
            capacity = float(self.per_min + self.burst)
            refill = self.per_min / 60.0
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get((bucket, key), (start, now))
            tokens = min(capacity, tokens + (now - last) * refill)
            if tokens >= weight:
                self._buckets[(bucket, key)] = (tokens - weight, now)
                return True, 0
            self._buckets[(bucket, key)] = (tokens, now)
            return False, max(1, math.ceil((weight - tokens) / refill))


def _demo_rate_weight(path: str) -> tuple[float, str]:
    """Weight + bucket for a /api/demo/* request (closed decision #3)."""
    if path == "/api/demo/telemetry":
        return 1.0, "telemetry"
    if path.endswith("/stream"):
        return 3.0, "demo"
    if path.endswith("/export"):
        return 2.0, "demo"
    return 1.0, "demo"


# --- Deterministic demo-run registry (shared by run/export/narrate) --------
# Engine cores are lru_cached on their pure (scenario, seed) inputs; the
# Signal + Counsel engines predate the cache rule, so their caching wrapper
# lives here (§6.4) — SSE still paces frames, compute happens once.

_signal_pipeline = demo_signal.SignalFactoryPipeline()
_counsel_synthesizer = demo_counsel.LegalSynthesizer()
_capital_pipeline = demo_capital.CapitalDeskPipeline()
_estate_engine = demo_estate.EstateRoomEngine()
_risk_engine = demo_risk.RiskSentinelEngine()
_nexus_engine = demo_nexus.NexusRunEngine()


@lru_cache(maxsize=64)
def _cached_signal_run_json(scenario: str, seed: int) -> str:
    return json.dumps(_signal_pipeline.run(scenario, seed=seed))


def _signal_run(scenario: str, seed: int) -> dict:
    return json.loads(_cached_signal_run_json(scenario, seed))


@lru_cache(maxsize=64)
def _cached_counsel_scenario_json(scenario_id: str) -> str:
    return json.dumps(_counsel_synthesizer.synthesize(scenario_id=scenario_id))


def _counsel_scenario_run(scenario_id: str) -> dict:
    return json.loads(_cached_counsel_scenario_json(scenario_id))


# demo key -> (scenario ids, runner(scenario, seed) -> trace dict)
DEMO_RUN_REGISTRY: dict[str, dict] = {
    "signal": {
        "scenarios": lambda: set(demo_signal.SCENARIOS),
        "run": lambda scenario, seed: _signal_run(scenario, seed),
        "default_scenario": "ecommerce_roas",
    },
    "counsel": {
        "scenarios": lambda: {s["id"] for s in demo_counsel.list_scenarios()},
        "run": lambda scenario, seed: _counsel_scenario_run(scenario),
        "default_scenario": "trust_modification_gst",
    },
    "estate": {
        "scenarios": lambda: set(demo_estate.SCENARIOS),
        "run": lambda scenario, seed: _estate_engine.run(scenario, seed=seed),
        "default_scenario": "ct_estate_settlement",
    },
    "capital": {
        "scenarios": lambda: set(demo_capital.SCENARIOS),
        "run": lambda scenario, seed: _capital_pipeline.run(scenario, seed=seed),
        "default_scenario": "growth_reallocation",
    },
    "risk": {
        "scenarios": lambda: set(demo_risk.SCENARIOS),
        "run": lambda scenario, seed: _risk_engine.run(scenario, seed=seed),
        "default_scenario": "quarterly_close",
    },
    "nexus": {
        "scenarios": lambda: set(demo_nexus.SCENARIOS),
        "run": lambda scenario, seed: _nexus_engine.run(scenario, seed=seed),
        "default_scenario": "cpm_shock",
    },
}

# Demo page filename per pretty route (share-embedding targets, §5.1).
DEMO_PAGE_FILES: dict[str, str] = {
    "signal": "demo-signal.html",
    "counsel": "demo-counsel.html",
    "estate": "demo-estate.html",
    "capital": "demo-capital.html",
    "risk": "demo-risk.html",
    "nexus": "demo-nexus.html",
}


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
    if app.config["MIZOKI_DEMO_USERS"]:
        app.logger.info(
            "Admin login enabled with %d user(s).", len(app.config["MIZOKI_DEMO_USERS"])
        )
    else:
        app.logger.warning(
            "Admin login DISABLED: MIZOKI_DEMO_USERS_JSON is empty or unset. "
            "If this is production, the mizoki-website-demo-users secret has no "
            "usable value — see docs/PRODUCTION_SECRETS_SETUP.md."
        )
    app.config["REQUIRE_API_AUTH"] = os.environ.get(
        "MIZOKI_REQUIRE_AUTH_FOR_APIS", ""
    ).strip().lower() in ("1", "true", "yes", "on")
    # Canonical host = apex (closed decision #1); kill-switch honored.
    app.config["CANONICAL_REDIRECT_ENABLED"] = (
        os.environ.get("MIZOKI_CANONICAL_REDIRECT", "").strip().lower() != "off"
    )
    # Public demo-API rate limits (closed decision #3) — env-tunable.
    app.config.setdefault(
        "DEMO_RATE_PER_MIN", int(os.environ.get("MIZOKI_DEMO_RATE_PER_MIN", "30"))
    )
    app.config.setdefault(
        "DEMO_RATE_BURST", int(os.environ.get("MIZOKI_DEMO_RATE_BURST", "10"))
    )
    app.config.setdefault(
        "DEMO_TELEMETRY_RATE_PER_MIN",
        int(os.environ.get("MIZOKI_DEMO_TELEMETRY_RATE_PER_MIN", "10")),
    )
    app.extensions["boss_runtime"] = runtime or create_runtime(BASE_DIR)
    app.extensions["demo_rate_limiter"] = DemoRateLimiter(
        per_min=app.config["DEMO_RATE_PER_MIN"],
        burst=app.config["DEMO_RATE_BURST"],
        telemetry_per_min=app.config["DEMO_TELEMETRY_RATE_PER_MIN"],
    )

    @app.before_request
    def _canonical_host_redirect():
        # www.* 308-redirects to the same path on the apex (§6.1), unless
        # MIZOKI_CANONICAL_REDIRECT=off.
        if not app.config.get("CANONICAL_REDIRECT_ENABLED"):
            return None
        host = (request.host or "").split(":")[0]
        if not host.startswith("www."):
            return None
        query = request.query_string.decode()
        target = CANONICAL_BASE_URL + request.path + (f"?{query}" if query else "")
        return redirect(target, code=308)

    @app.before_request
    def _demo_api_rate_limit():
        # One decorator's worth of limiting for the whole public demo API.
        # Bypassed under TESTING except when a test opts in explicitly.
        path = request.path
        if not path.startswith("/api/demo/"):
            return None
        if app.config.get("TESTING") and not app.config.get("DEMO_RATE_LIMIT_ENFORCE_IN_TESTS"):
            return None
        weight, bucket = _demo_rate_weight(path)
        limiter: DemoRateLimiter = app.extensions["demo_rate_limiter"]
        allowed, retry_after = limiter.check(limiter.client_key(), weight, bucket)
        if allowed:
            return None
        response = jsonify({
            "error": "Rate limit exceeded — the public demo API allows "
                     f"{app.config['DEMO_RATE_PER_MIN']} weighted requests per minute per IP.",
            "retry_after_seconds": retry_after,
        })
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    # Opt-in: gate /api/mcp/* and /api/boss/* behind admin session.
    # Off by default so the public site's chat demo keeps working.
    # Turn on by setting MIZOKI_REQUIRE_AUTH_FOR_APIS=true in the env.
    _AUTH_GATED_API_PREFIXES = ("/api/mcp/", "/api/boss/")
    _PUBLIC_API_PATHS = {"/api/health"}

    @app.before_request
    def _maybe_require_api_auth():
        if not app.config.get("REQUIRE_API_AUTH"):
            return None
        path = request.path
        if path in _PUBLIC_API_PATHS:
            return None
        if not path.startswith(_AUTH_GATED_API_PREFIXES):
            return None
        if "user" in session:
            return None
        return jsonify({
            "error": "Authentication required",
            "hint": "Sign in at /admin/login to obtain a session cookie.",
        }), 401

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

    @app.route("/privacy")
    @app.route("/privacy.html")
    def privacy_page():
        return serve_page("privacy.html")

    @app.route("/terms")
    @app.route("/terms.html")
    def terms_page():
        return serve_page("terms.html")

    # Canonical path is /executive-briefing/ (trailing slash): the module's
    # asset links are relative, so serving the page at the bare path would make
    # css/ and js/ resolve against the site root and 404. No bare-path route —
    # Werkzeug's default strict_slashes redirects /executive-briefing here.
    @app.route("/executive-briefing/")
    def executive_briefing():
        return send_from_directory(BASE_DIR / "executive-briefing", "index.html")

    @app.route("/executive-briefing/<path:filename>")
    def executive_briefing_assets(filename: str):
        base = (BASE_DIR / "executive-briefing").resolve()
        target = (base / filename).resolve()
        allowed = {".html", ".css", ".js", ".svg", ".png", ".md"}
        if not str(target).startswith(str(base) + "/") or not target.is_file() or target.suffix.lower() not in allowed:
            abort(404)
        return send_from_directory(base, filename)

    @app.route("/pricing")
    @app.route("/pricing.html")
    def pricing():
        return serve_page("pricing.html")

    # Media-buyer landing: hero + scenario simulator + 90-sec storyboard.
    @app.route("/media-buying")
    @app.route("/media-buying.html")
    def media_buying():
        return serve_page("media-buying.html")

    # ===== Live product demos (public) ==============================

    def serve_demo_page(demo_key: str):
        """Serve a demo page, embedding sanitized ?scenario=&seed= params as
        data attributes on <body> so the page's JS can autorun a shared,
        deterministic replay (§5.1)."""
        filename = DEMO_PAGE_FILES[demo_key]
        text = (BASE_DIR / filename).read_text(encoding="utf-8")
        attrs = []
        scenario = request.args.get("scenario", "")
        if scenario and scenario in DEMO_RUN_REGISTRY[demo_key]["scenarios"]():
            attrs.append(f'data-scenario="{scenario}"')
        seed_raw = request.args.get("seed")
        if seed_raw is not None:
            try:
                attrs.append(f'data-seed="{int(seed_raw)}"')
            except (TypeError, ValueError):
                pass
        if attrs:
            text = text.replace("<body", "<body " + " ".join(attrs), 1)
        return app.response_class(text, mimetype="text/html")

    # D6 fix: the pretty demo routes tolerate trailing slashes.
    @app.route("/demo", strict_slashes=False)
    @app.route("/demo.html")
    def demo_hub():
        return serve_page("demo.html")

    @app.route("/demo/signal", strict_slashes=False)
    @app.route("/demo-signal.html")
    def demo_signal_page():
        return serve_demo_page("signal")

    @app.route("/demo/counsel", strict_slashes=False)
    @app.route("/demo-counsel.html")
    def demo_counsel_page():
        return serve_demo_page("counsel")

    @app.route("/demo/estate", strict_slashes=False)
    @app.route("/demo-estate.html")
    def demo_estate_page():
        return serve_demo_page("estate")

    @app.route("/demo/capital", strict_slashes=False)
    @app.route("/demo-capital.html")
    def demo_capital_page():
        return serve_demo_page("capital")

    @app.route("/demo/risk", strict_slashes=False)
    @app.route("/demo-risk.html")
    def demo_risk_page():
        return serve_demo_page("risk")

    @app.route("/demo/nexus", strict_slashes=False)
    @app.route("/demo-nexus.html")
    def demo_nexus_page():
        return serve_demo_page("nexus")

    # D2 fix: the walkthrough is a real page again (was 301-swallowed).
    @app.route("/walkthrough")
    @app.route("/walkthrough.html")
    def walkthrough_page():
        return serve_page("walkthrough.html")

    # §5.6: real lead path — the contact template becomes a real route.
    @app.route("/contact")
    @app.route("/contact.html")
    def contact_page():
        source = request.args.get("source", "")
        # Sanitize: the echoed value is attribute-safe by construction.
        source = "".join(ch for ch in source if ch.isalnum() or ch in "-_")[:64]
        return render_template("contact.html", source=source)

    @app.route("/favicon.ico")
    def favicon_ico():
        # Pages link the SVG explicitly, but browsers, crawlers and older clients
        # still request bare /favicon.ico — serve the real multi-size ICO so this
        # is not a site-wide 404. Regenerate via scripts/generate_favicon.py.
        return send_from_directory(
            BASE_DIR / "assets" / "img",
            "favicon.ico",
            mimetype="image/x-icon",
        )

    @app.route("/apple-touch-icon.png")
    @app.route("/apple-touch-icon-precomposed.png")
    def apple_touch_icon():
        # iOS requests these at the root regardless of <link rel="apple-touch-icon">.
        return send_from_directory(
            BASE_DIR / "assets" / "img", "apple-touch-icon.png", mimetype="image/png"
        )

    @app.route("/robots.txt")
    def robots_txt():
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            f"\nSitemap: {CANONICAL_BASE_URL}/sitemap.xml\n"
        )
        return app.response_class(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap_xml():
        # The demos are the marketing asset — index them (closed decision #2).
        pages = [
            "/", "/counsel", "/estate", "/capital", "/signal", "/risk",
            "/pricing", "/media-buying", "/executive-briefing/",
            "/demo", "/demo/signal", "/demo/counsel", "/demo/estate",
            "/demo/capital", "/demo/risk", "/demo/nexus",
            "/walkthrough.html", "/blog",
        ]
        posts = _load_blog_manifest()
        blog_lastmod = posts[0].get("updated", posts[0].get("published", "")) if posts else ""
        entries = []
        for path in pages:
            lastmod = (
                f"\n    <lastmod>{_xml_escape(blog_lastmod)}</lastmod>"
                if path == "/blog" and blog_lastmod
                else ""
            )
            entries.append(
                "  <url>\n"
                f"    <loc>{_xml_escape(CANONICAL_BASE_URL + path)}</loc>{lastmod}\n"
                "  </url>"
            )
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries)
            + "\n</urlset>\n"
        )
        return app.response_class(body, mimetype="application/xml")

    @app.route("/how-it-works.html")
    @app.route("/platform.html")
    @app.route("/security.html")
    @app.route("/industries.html")
    @app.route("/case-studies.html")
    @app.route("/resources.html")
    @app.route("/roi.html")
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

    @app.route("/blog/feed.xml")
    @app.route("/blog/rss.xml")
    @app.route("/rss.xml")
    def blog_rss_feed():
        from flask import Response
        manifest = _load_blog_manifest()
        rss = _render_rss(manifest, base_url=request.url_root.rstrip("/"))
        return Response(rss, mimetype="application/rss+xml; charset=utf-8")

    @app.route("/blog/feed.json")
    def blog_json_feed():
        manifest = _load_blog_manifest()
        base = request.url_root.rstrip("/")
        items = []
        for post in manifest:
            items.append({
                "id": f"{base}/blog/{post['slug']}",
                "url": f"{base}/blog/{post['slug']}",
                "title": post["title"],
                "summary": post.get("summary", ""),
                "content_text": post.get("summary", ""),
                "date_published": f"{post['published']}T09:00:00Z",
                "date_modified": f"{post.get('updated', post['published'])}T09:00:00Z",
                "authors": [{"name": post.get("author", "MIZ OKI")}],
                "tags": post.get("tags", []),
                "image": f"{base}{post['image']}" if post.get("image") else None,
            })
        return jsonify({
            "version": "https://jsonfeed.org/version/1.1",
            "title": "MIZ OKI 3.5 Blog",
            "home_page_url": f"{base}/blog",
            "feed_url": f"{base}/blog/feed.json",
            "description": "Research and field notes on threshold-aware media buying, decision intelligence, and causal autonomous systems.",
            "language": "en",
            "items": items,
        })

    @app.route("/blog/posts.json")
    def blog_posts_manifest():
        # Raw manifest passthrough (handy for client-side blog listings)
        return send_from_directory(BASE_DIR / "blog", "posts.json", mimetype="application/json")

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

    # ===== Admin (local backend) ====================================
    @app.route("/admin")
    @app.route("/admin/")
    def admin_home():
        if "user" not in session:
            return redirect(url_for("admin_login_page"))
        runtime = get_runtime()
        try:
            health = runtime.health_snapshot()
        except Exception:
            health = {"status": "unknown", "version": "?", "skills_count": 0}
        try:
            tools = runtime.list_tools()
        except Exception:
            tools = []
        # Decision traces — runtime exposes either recent_traces() or trace storage
        traces = []
        for attr in ("recent_traces", "list_traces", "get_recent_traces"):
            if hasattr(runtime, attr):
                try:
                    traces = list(getattr(runtime, attr)(limit=50)) or []
                    break
                except TypeError:
                    try:
                        traces = list(getattr(runtime, attr)()) or []
                        break
                    except Exception:
                        pass
                except Exception:
                    pass
        return render_template(
            "admin_dashboard.html",
            user_email=session.get("user"),
            health=health,
            tools=tools,
            traces=traces[:50],
        )

    @app.route("/admin/login", methods=["GET"])
    def admin_login_page():
        if "user" in session:
            return redirect(url_for("admin_home"))
        return render_template("admin_login.html")

    @app.route("/admin/login", methods=["POST"])
    def admin_login_post():
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        demo_users = app.config.get("MIZOKI_DEMO_USERS", {})

        if not demo_users:
            flash(
                "Local admin login is disabled. Set MIZOKI_DEMO_USERS_JSON to enable it.",
                "warning",
            )
            return redirect(url_for("admin_login_page"))

        if email in demo_users and demo_users[email] == password:
            session.permanent = True
            session["user"] = email
            return redirect(url_for("admin_home"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("admin_login_page"))

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("user", None)
        flash("You have been signed out.", "info")
        return redirect(url_for("admin_login_page"))

    @app.route("/templates/<path:filename>")
    def serve_template(filename: str):
        if filename not in ALLOWED_TEMPLATES:
            abort(404)
        return render_template(filename)

    @app.route("/api/health")
    def api_health():
        snapshot = get_runtime().health_snapshot()
        # Non-sensitive operational signal: lets deploy verification (and ops)
        # detect an empty/missing MIZOKI_DEMO_USERS_JSON secret without probing
        # the login form.
        snapshot["admin_login_enabled"] = bool(app.config.get("MIZOKI_DEMO_USERS"))
        return jsonify(snapshot)

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

    # ===== Canonical reasoning substrate (JourneyEvent v1 → Envelope v2 →
    # ===== identity clusters) + Virtuoso model plane ==================
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

    @app.route("/api/boss/identity/resolve", methods=["POST"])
    def boss_identity_resolve():
        payload = require_json_payload()
        actor = payload.get("actor")
        if not isinstance(actor, dict):
            abort(400, description="Field 'actor' must be an object.")
        return jsonify(run_runtime_call(lambda: get_runtime().resolve_identity(actor)))

    @app.route("/api/boss/identity/stats", methods=["GET"])
    def boss_identity_stats():
        return jsonify(run_runtime_call(lambda: get_runtime().identity_cluster_stats()))

    @app.route("/api/boss/virtuoso/registry", methods=["GET"])
    def boss_virtuoso_registry():
        return jsonify(run_runtime_call(lambda: get_runtime().virtuoso_registry()))

    @app.route("/api/boss/virtuoso/resolve", methods=["POST"])
    def boss_virtuoso_resolve():
        payload = require_json_payload()
        role = payload.get("role")
        if not isinstance(role, str) or not role.strip():
            abort(400, description="Field 'role' must be a non-empty string.")
        return jsonify(run_runtime_call(lambda: get_runtime().resolve_virtuoso_model(role)))

    @app.route("/api/boss/virtuoso/scan", methods=["POST"])
    def boss_virtuoso_scan():
        payload = require_json_payload()
        text = payload.get("text")
        source = payload.get("source", "inline")
        if not isinstance(text, str):
            abort(400, description="Field 'text' must be a string.")
        if not isinstance(source, str):
            abort(400, description="Field 'source' must be a string.")
        return jsonify(run_runtime_call(lambda: get_runtime().scan_legacy_model_strings(text, source=source)))

    @app.route("/api/boss/virtuoso/traces", methods=["GET"])
    def boss_virtuoso_traces():
        limit = request.args.get("limit", default=10, type=int)
        limit = max(1, min(limit, 100))
        return jsonify({"traces": run_runtime_call(lambda: get_runtime().recent_reasoning_traces(limit=limit))})

    # ===== Demo APIs (public — intentionally NOT auth-gated) =========
    demo_pipeline = _signal_pipeline
    demo_synthesizer = _counsel_synthesizer

    def _validated_demo_scenario(demo_key: str, scenario) -> str:
        known_ids = DEMO_RUN_REGISTRY[demo_key]["scenarios"]()
        if not isinstance(scenario, str) or scenario not in known_ids:
            known = ", ".join(sorted(known_ids))
            abort(400, description=f"Field 'scenario' must be one of: {known}.")
        return scenario

    def _validated_signal_scenario(scenario) -> str:
        return _validated_demo_scenario("signal", scenario)

    def _validated_seed(seed) -> int:
        if seed is None:
            return demo_signal.DEFAULT_SEED
        if isinstance(seed, bool) or not isinstance(seed, int):
            abort(400, description="Field 'seed' must be an integer.")
        return seed

    def _run_payload_args(demo_key: str) -> tuple[str, int]:
        payload = require_json_payload()
        scenario = payload.get("scenario")
        if scenario is None:
            scenario = payload.get("scenario_id")
        scenario = _validated_demo_scenario(demo_key, scenario)
        seed = _validated_seed(payload.get("seed"))
        return scenario, seed

    def _stream_query_args(demo_key: str, default_scenario: str) -> tuple[str, int]:
        scenario = _validated_demo_scenario(
            demo_key, request.args.get("scenario", default_scenario)
        )
        try:
            seed = int(request.args.get("seed", demo_signal.DEFAULT_SEED))
        except (TypeError, ValueError):
            abort(400, description="Query parameter 'seed' must be an integer.")
        return scenario, seed

    def _sse_response(frame_iterator):
        from flask import Response

        # Pacing happens here in the Flask layer (never in the engine) so
        # tests can consume frames instantly under TESTING.
        paced = not app.config.get("TESTING")

        def generate():
            for frame in frame_iterator:
                yield f"event: {frame['type']}\ndata: {json.dumps(frame['data'])}\n\n"
                if paced and frame["delay_hint_ms"]:
                    time.sleep(min(frame["delay_hint_ms"], 1500) / 1000.0)

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.route("/api/demo/signal/scenarios", methods=["GET"])
    def demo_signal_scenarios():
        return jsonify({"scenarios": demo_signal.list_scenarios()})

    @app.route("/api/demo/signal/run", methods=["POST"])
    def demo_signal_run():
        payload = require_json_payload()
        scenario = _validated_signal_scenario(payload.get("scenario"))
        seed = _validated_seed(payload.get("seed"))
        return jsonify(run_runtime_call(lambda: _signal_run(scenario, seed)))

    @app.route("/api/demo/signal/stream", methods=["GET"])
    def demo_signal_stream():
        scenario, seed = _stream_query_args("signal", "ecommerce_roas")
        return _sse_response(demo_pipeline.run_streaming(scenario, seed=seed))

    @app.route("/api/demo/counsel/scenarios", methods=["GET"])
    def demo_counsel_scenarios():
        return jsonify({"scenarios": demo_counsel.list_scenarios()})

    @app.route("/api/demo/counsel/query", methods=["POST"])
    def demo_counsel_query():
        payload = require_json_payload()
        scenario_id = payload.get("scenario_id")
        query = payload.get("query")
        if scenario_id is not None and not isinstance(scenario_id, str):
            abort(400, description="Field 'scenario_id' must be a string.")
        if query is not None and not isinstance(query, str):
            abort(400, description="Field 'query' must be a string.")
        if not (scenario_id and scenario_id.strip()) and not (query and query.strip()):
            abort(400, description="Provide 'scenario_id' or 'query'.")
        if query and len(query) > demo_counsel.MAX_QUERY_LENGTH:
            abort(400, description=f"Field 'query' must be at most {demo_counsel.MAX_QUERY_LENGTH} characters.")
        return jsonify(
            run_runtime_call(
                lambda: demo_synthesizer.synthesize(
                    scenario_id=(scenario_id or "").strip() or None,
                    free_text=query if (query and query.strip()) else None,
                )
            )
        )

    # ---- Estate Room ------------------------------------------------

    @app.route("/api/demo/estate/scenarios", methods=["GET"])
    def demo_estate_scenarios():
        return jsonify({"scenarios": demo_estate.list_scenarios()})

    @app.route("/api/demo/estate/run", methods=["POST"])
    def demo_estate_run():
        scenario, seed = _run_payload_args("estate")
        return jsonify(run_runtime_call(lambda: _estate_engine.run(scenario, seed=seed)))

    # ---- Capital Desk (Signal pattern, with SSE) --------------------

    @app.route("/api/demo/capital/scenarios", methods=["GET"])
    def demo_capital_scenarios():
        return jsonify({"scenarios": demo_capital.list_scenarios()})

    @app.route("/api/demo/capital/run", methods=["POST"])
    def demo_capital_run():
        scenario, seed = _run_payload_args("capital")
        return jsonify(run_runtime_call(lambda: _capital_pipeline.run(scenario, seed=seed)))

    @app.route("/api/demo/capital/stream", methods=["GET"])
    def demo_capital_stream():
        scenario, seed = _stream_query_args("capital", "growth_reallocation")
        return _sse_response(_capital_pipeline.run_streaming(scenario, seed=seed))

    # ---- Risk Sentinel ----------------------------------------------

    @app.route("/api/demo/risk/scenarios", methods=["GET"])
    def demo_risk_scenarios():
        return jsonify({"scenarios": demo_risk.list_scenarios()})

    @app.route("/api/demo/risk/run", methods=["POST"])
    def demo_risk_run():
        scenario, seed = _run_payload_args("risk")
        return jsonify(run_runtime_call(lambda: _risk_engine.run(scenario, seed=seed)))

    # ---- The Nexus Run (flagship) -----------------------------------

    @app.route("/api/demo/nexus/scenarios", methods=["GET"])
    def demo_nexus_scenarios():
        return jsonify({"scenarios": demo_nexus.list_scenarios()})

    @app.route("/api/demo/nexus/run", methods=["POST"])
    def demo_nexus_run():
        scenario, seed = _run_payload_args("nexus")
        return jsonify(run_runtime_call(lambda: _nexus_engine.run(scenario, seed=seed)))

    @app.route("/api/demo/nexus/stream", methods=["GET"])
    def demo_nexus_stream():
        scenario, seed = _stream_query_args("nexus", "cpm_shock")
        return _sse_response(_nexus_engine.run_streaming(scenario, seed=seed))

    # ---- Trace Narrator (§5.3) — the Boss-chat answer ---------------

    @app.route("/api/demo/<demo_key>/narrate", methods=["GET"])
    def demo_narrate(demo_key: str):
        if demo_key not in DEMO_RUN_REGISTRY:
            abort(404)
        scenario = _validated_demo_scenario(
            demo_key,
            request.args.get("scenario", DEMO_RUN_REGISTRY[demo_key]["default_scenario"]),
        )
        try:
            seed = int(request.args.get("seed", demo_signal.DEFAULT_SEED))
        except (TypeError, ValueError):
            abort(400, description="Query parameter 'seed' must be an integer.")
        return jsonify(run_runtime_call(lambda: demo_narrator.narrate(demo_key, scenario, seed=seed)))

    # ---- Signed audit export (§5.5) ---------------------------------

    @app.route("/api/demo/<demo_key>/export", methods=["GET"])
    def demo_export(demo_key: str):
        if demo_key not in DEMO_RUN_REGISTRY:
            abort(404)
        scenario = _validated_demo_scenario(
            demo_key,
            request.args.get("scenario", DEMO_RUN_REGISTRY[demo_key]["default_scenario"]),
        )
        try:
            seed = int(request.args.get("seed", demo_signal.DEFAULT_SEED))
        except (TypeError, ValueError):
            abort(400, description="Query parameter 'seed' must be an integer.")
        trace = run_runtime_call(lambda: DEMO_RUN_REGISTRY[demo_key]["run"](scenario, seed))
        digest = hashlib.sha256(
            json.dumps(trace, sort_keys=True).encode("utf-8")
        ).hexdigest()
        from datetime import datetime, timezone

        return jsonify({
            "trace": trace,
            "integrity": {
                "algo": "sha256",
                "digest": digest,
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        })

    # ---- Cookieless telemetry (§6.6) --------------------------------

    @app.route("/api/demo/telemetry", methods=["POST"])
    def demo_telemetry_ingest():
        payload = require_json_payload()
        extra_keys = set(payload) - {"event", "demo", "scenario"}
        if extra_keys:
            abort(400, description=f"Unexpected fields: {', '.join(sorted(extra_keys))}.")
        for field_name in ("event", "demo", "scenario"):
            if not isinstance(payload.get(field_name), str):
                abort(400, description=f"Field '{field_name}' must be a string.")
        telemetry_path = get_runtime().data_dir / "demo_telemetry.jsonl"
        row = run_runtime_call(
            lambda: demo_telemetry.record_event(
                telemetry_path, payload["event"], payload["demo"], payload["scenario"]
            )
        )
        return jsonify({"status": "recorded", "event": row["event"]})

    # ---- Executive Briefing guide agent (Decision Concierge) --------------
    # Public like /api/demo/*: the guide runs on the anonymous briefing page.
    # Q&A is allowlist-retrieval only (mizoki_runtime.briefing_guide) and every
    # interaction lands in the guide memory ledger for aggregation.

    @app.route("/api/briefing/guide/event", methods=["POST"])
    def briefing_guide_event():
        payload = require_json_payload()
        extra = set(payload) - {"session", "event", "stage", "domain", "role", "payload"}
        if extra:
            abort(400, description=f"Unexpected fields: {', '.join(sorted(extra))}.")
        for field_name in ("session", "event"):
            if not isinstance(payload.get(field_name), str) or not payload[field_name]:
                abort(400, description=f"Field '{field_name}' must be a non-empty string.")
        if payload["event"] not in briefing_guide.ALLOWED_EVENTS:
            abort(400, description="Unknown guide event.")
        detail = payload.get("payload")
        if detail is not None and not isinstance(detail, dict):
            abort(400, description="Field 'payload' must be an object.")
        ledger = get_runtime().data_dir / "guide_interactions.jsonl"
        row = run_runtime_call(
            lambda: briefing_guide.record_event(
                ledger,
                payload["session"],
                payload["event"],
                stage=str(payload.get("stage", "")),
                domain=str(payload.get("domain", "")),
                role=str(payload.get("role", "")),
                payload=detail,
            )
        )
        return jsonify({"status": "recorded", "event": row["event"]})

    @app.route("/api/briefing/guide/ask", methods=["POST"])
    def briefing_guide_ask():
        payload = require_json_payload()
        extra = set(payload) - {"session", "question", "stage", "domain", "role"}
        if extra:
            abort(400, description=f"Unexpected fields: {', '.join(sorted(extra))}.")
        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            abort(400, description="Field 'question' must be a non-empty string.")
        if len(question) > 500:
            abort(400, description="Field 'question' is too long (500 chars max).")
        session = payload.get("session")
        if not isinstance(session, str) or not session:
            abort(400, description="Field 'session' must be a non-empty string.")
        domain = str(payload.get("domain", ""))
        role = str(payload.get("role", ""))
        stage = str(payload.get("stage", ""))
        answer = run_runtime_call(lambda: briefing_guide.answer_question(question, domain=domain, role=role))
        ledger = get_runtime().data_dir / "guide_interactions.jsonl"
        briefing_guide.record_event(
            ledger, session, "question_asked", stage=stage, domain=domain, role=role,
            payload={"topic": answer["topic"], "kind": answer["kind"], "q": question[:120]},
        )
        if answer["kind"] == "objection":
            briefing_guide.record_event(
                ledger, session, "objection_raised", stage=stage, domain=domain, role=role,
                payload={"objection": answer["topic"]},
            )
        return jsonify(answer)

    @app.route("/api/briefing/guide/summary", methods=["GET"])
    def briefing_guide_summary():
        ledger = get_runtime().data_dir / "guide_interactions.jsonl"
        return jsonify(run_runtime_call(lambda: briefing_guide.summarize(ledger)))

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

    @app.route("/api/boss/google-ads/validate", methods=["POST"])
    def boss_google_ads_validate():
        payload = require_json_payload()
        query = payload.get("query")
        api_version = payload.get("api_version")
        as_of = payload.get("as_of")
        if not isinstance(query, str) or not query.strip():
            abort(400, description="Field 'query' must be a non-empty GAQL string.")
        return jsonify(
            run_runtime_call(
                lambda: get_runtime().validate_gaql(query, api_version=api_version, as_of=as_of)
            )
        )

    @app.route("/api/boss/google-ads/validate-batch", methods=["POST"])
    def boss_google_ads_validate_batch():
        payload = require_json_payload()
        queries = payload.get("queries")
        api_version = payload.get("api_version")
        as_of = payload.get("as_of")
        if not isinstance(queries, list) or not queries:
            abort(400, description="Field 'queries' must be a non-empty array of GAQL strings.")
        return jsonify(
            run_runtime_call(
                lambda: get_runtime().validate_gaql_batch(queries, api_version=api_version, as_of=as_of)
            )
        )

    @app.route("/api/boss/google-ads/versions", methods=["GET"])
    def boss_google_ads_versions():
        api_version = request.args.get("api_version", default=None)
        as_of = request.args.get("as_of", default=None)
        return jsonify(
            run_runtime_call(
                lambda: get_runtime().google_ads_version_status(api_version=api_version, as_of=as_of)
            )
        )

    @app.route("/api/boss/google-ads/fields", methods=["GET"])
    def boss_google_ads_fields():
        resource = request.args.get("resource", default=None)
        return jsonify(
            run_runtime_call(lambda: get_runtime().google_ads_field_metadata(resource=resource))
        )

    @app.route("/api/boss/google-ads/validations", methods=["GET"])
    def boss_google_ads_validations():
        limit = request.args.get("limit", default=10, type=int)
        limit = max(1, min(limit, 100))
        return jsonify({"validations": get_runtime().recent_gaql_validations(limit=limit)})

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
