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


@app.route('/blogs')
@app.route('/blogs/')
@app.route('/blogs.html')
def blogs_page():
    return redirect(url_for('blog_index'), code=301)


# ==================== BLOG ROUTES ====================

@app.route('/blog')
def blog_index():
    return send_from_directory('blog', 'index.html')


@app.route('/blog/')
@app.route('/blog/index.html')
def blog_index_legacy():
    return redirect(url_for('blog_index'), code=301)


@app.route('/blog/relu-lens-meta-algorithm')
def blog_relu_lens_article():
    return send_from_directory('blog', 'relu-lens-meta-algorithm.html')


@app.route('/blog/relu-lens-meta-algorithm/')
@app.route('/blog/relu-lens-meta-algorithm.html')
@app.route('/blog/meta-relu-gate-go-deep-before-wide')
@app.route('/blog/meta-relu-gate-go-deep-before-wide/')
@app.route('/blog/meta-relu-gate-go-deep-before-wide.html')
@app.route('/blog/meta-relu-gate-go-deep-before-wide/index.html')
def legacy_blog_relu_lens_article():
    return redirect(url_for('blog_relu_lens_article'), code=301)


@app.route('/blog/<path:filename>')
def blog_post(filename):
    return send_from_directory('blog', filename)


# ==================== VERSION 1.1 ROUTES ====================

@app.route('/11/')
@app.route('/11/index.html')
def v11_home():
    return send_from_directory('11', 'index.html')


@app.route('/11/<path:filename>')
def v11_page(filename):
    return send_from_directory('11', filename)


# ==================== LOGIN/AUTH ====================

@app.route('/login', methods=['GET'])
@app.route('/login.html', methods=['GET'])
def login_page():
    if 'user' in session:
        return redirect('https://mizoki.mizoki3.com/dashboard')
    return send_from_directory('.', 'login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if email in USERS and USERS[email] == password:
        session['user'] = email
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
    # Redirect to the real MIZ OKI Command Center UI (Next.js app)
    return redirect('https://mizoki.mizoki3.com/dashboard')


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
