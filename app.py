import os
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
app.secret_key = os.environ.get('SECRET_KEY', 'mizoki-3-5-secret-key-change-in-production')

# Demo credentials (in production, use a proper database)
USERS = {
    'admin@mizoki3.com': 'mizoki2024',
    'demo@mizoki3.com': 'demo2024',
    'ceo@mediaintelligence.ai': 'mizoki3.5'
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== MAIN PAGES ====================

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


@app.route('/index.html')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/how-it-works.html')
def how_it_works():
    return send_from_directory('.', 'how-it-works.html')


@app.route('/platform.html')
def platform():
    return send_from_directory('.', 'platform.html')


@app.route('/security.html')
def security():
    return send_from_directory('.', 'security.html')


@app.route('/industries.html')
def industries():
    return send_from_directory('.', 'industries.html')


@app.route('/pricing.html')
def pricing():
    return send_from_directory('.', 'pricing.html')


@app.route('/case-studies.html')
def case_studies():
    return send_from_directory('.', 'case-studies.html')


@app.route('/resources.html')
def resources():
    return send_from_directory('.', 'resources.html')


@app.route('/roi.html')
def roi():
    return send_from_directory('.', 'roi.html')


@app.route('/walkthrough.html')
def walkthrough():
    return send_from_directory('.', 'walkthrough.html')


@app.route('/investor.html')
def investor():
    return send_from_directory('.', 'investor.html')


@app.route('/sales-one-pager.html')
def sales_one_pager():
    return send_from_directory('.', 'sales-one-pager.html')


@app.route('/demo-opener.html')
def demo_opener():
    return send_from_directory('.', 'demo-opener.html')


@app.route('/blogs.html')
def blogs_page():
    return send_from_directory('.', 'blogs.html')


# ==================== BLOG ROUTES ====================

@app.route('/blog/')
@app.route('/blog/index.html')
def blog_index():
    return send_from_directory('blog', 'index.html')


@app.route('/blog/<path:filename>')
def blog_post(filename):
    return send_from_directory('blog', filename)


# ==================== LOGIN/AUTH ====================

@app.route('/login', methods=['GET'])
@app.route('/login.html', methods=['GET'])
def login_page():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return send_from_directory('.', 'login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if email in USERS and USERS[email] == password:
        session['user'] = email
        # Redirect to the command center dashboard
        return redirect('https://mizoki.mizoki3.com/dashboard')
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login_page'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Dashboard — MIZ OKI 3.5</title>
        <link rel="icon" href="/assets/svg/favicon.svg" type="image/svg+xml"/>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/assets/css/styles.css"/>
        <style>
            .dashboard {{ min-height: 100vh; padding: 2rem; }}
            .dashboard-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }}
            .dashboard-card {{ background: linear-gradient(180deg, rgba(15,26,46,.85), rgba(11,18,32,.75)); border: 1px solid rgba(25,245,255,.18); border-radius: 12px; padding: 24px; margin-bottom: 1rem; }}
            .dashboard-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
            .stat {{ font-size: 2.5rem; font-weight: 700; color: var(--accent); }}
            .stat-label {{ color: var(--muted); font-size: 0.875rem; }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="dashboard-header">
                <div class="brand">
                    <div class="mark" aria-hidden="true"></div>
                    <span>MIZ OKI <small>3.5</small></span>
                </div>
                <div>
                    <span style="color: var(--muted); margin-right: 1rem;">Logged in as: {session['user']}</span>
                    <a href="/logout" class="btn secondary">Logout</a>
                </div>
            </div>

            <h1 style="margin-bottom: 0.5rem;">Decision Control Center</h1>
            <p style="color: var(--muted); margin-bottom: 2rem;">Verifiable Autonomous Decision Intelligence Dashboard</p>

            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <div class="stat">147</div>
                    <div class="stat-label">Decisions Processed Today</div>
                </div>
                <div class="dashboard-card">
                    <div class="stat">98.7%</div>
                    <div class="stat-label">Validation Success Rate</div>
                </div>
                <div class="dashboard-card">
                    <div class="stat">23ms</div>
                    <div class="stat-label">Avg Pipeline Latency</div>
                </div>
                <div class="dashboard-card">
                    <div class="stat">$1.2M</div>
                    <div class="stat-label">Value Protected</div>
                </div>
            </div>

            <div class="dashboard-card" style="margin-top: 2rem;">
                <h2 style="margin-bottom: 1rem;">SRDPV-DAL Pipeline Status</h2>
                <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.5rem; text-align: center;">
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">SENSE</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">REASON</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">PLAN</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">VALIDATE</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">DECIDE</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">ACT</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                    <div style="padding: 1rem; background: rgba(25,245,255,0.1); border-radius: 8px;">
                        <div style="color: var(--accent); font-weight: 600;">LEARN</div>
                        <div style="color: #4ade80; font-size: 0.75rem;">ACTIVE</div>
                    </div>
                </div>
            </div>

            <div class="dashboard-card" style="margin-top: 1rem;">
                <h2 style="margin-bottom: 1rem;">Quick Links</h2>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <a href="/" class="btn secondary">Homepage</a>
                    <a href="/blog/" class="btn secondary">Blog</a>
                    <a href="/how-it-works.html" class="btn secondary">How It Works</a>
                    <a href="/platform.html" class="btn secondary">Platform</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''


# ==================== TEMPLATES ====================

@app.route('/templates/<path:filename>')
def serve_template(filename):
    return render_template(filename)


# ==================== HEALTH CHECK ====================

@app.route('/health')
def health():
    return 'healthy', 200


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return '''
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
    ''', 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
