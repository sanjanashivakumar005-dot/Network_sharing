from flask import Flask, request, redirect, url_for, session, send_from_directory, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-for-production-2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY,
                     username
                     TEXT
                     UNIQUE,
                     password
                     TEXT
                 )''')
    conn.commit()
    conn.close()


init_db()

# HTML Templates embedded as strings
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FileShare - Home</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/minty/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('home') }}">🌐 FileShare</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('logout') }}">Logout ({{ username }})</a>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-md-8">
                <h1 class="mb-4">Welcome, {{ username }}! 👋</h1>

                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                <!-- Upload Form -->
                <div class="card shadow mb-4">
                    <div class="card-header bg-success text-white">
                        <h5>📁 Upload New File</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="{{ url_for('upload_file') }}" enctype="multipart/form-data">
                            <div class="mb-3">
                                <input type="file" class="form-control" name="file" required>
                            </div>
                            <button type="submit" class="btn btn-success btn-lg w-100">🚀 Upload File</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- Files List -->
        <h3 class="mb-3">📋 Shared Files ({{ files|length }})</h3>
        {% if files %}
            <div class="row">
                {% for file in files %}
                    <div class="col-md-6 col-lg-4 mb-4">
                        <div class="card h-100 shadow">
                            <div class="card-body">
                                <h6 class="card-title">{{ file }}</h6>
                                <p class="card-text text-muted small">{{ file|length }} bytes</p>
                                <div class="btn-group w-100" role="group">
                                    <a href="{{ url_for('download_file', filename=file) }}" class="btn btn-primary btn-sm">⬇️ Download</a>
                                    <a href="{{ url_for('delete_file', filename=file) }}" class="btn btn-danger btn-sm" 
                                       onclick="return confirm('Delete {{ file }}?')">🗑️ Delete</a>
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="alert alert-info text-center">
                <h4>📂 No files yet!</h4>
                <p>Upload your first file to get started 🚀</p>
            </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - FileShare</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/minty/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-gradient bg-primary-subtle min-vh-100 d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card shadow-lg">
                    <div class="card-body p-5">
                        <div class="text-center mb-4">
                            <h1 class="display-5 fw-bold text-primary">🌐 FileShare</h1>
                            <p class="lead">Sign in to your account</p>
                        </div>

                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="mb-4">
                                <label class="form-label fw-bold">👤 Username</label>
                                <input type="text" class="form-control form-control-lg" name="username" required>
                            </div>
                            <div class="mb-4">
                                <label class="form-label fw-bold">🔒 Password</label>
                                <input type="password" class="form-control form-control-lg" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-lg w-100 mb-3">🚀 Login</button>
                        </form>

                        <div class="text-center">
                            <p class="mb-0">Don't have an account? <a href="{{ url_for('register') }}" class="text-decoration-none fw-bold">Register Now</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - FileShare</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/minty/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-gradient bg-success-subtle min-vh-100 d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card shadow-lg">
                    <div class="card-body p-5">
                        <div class="text-center mb-4">
                            <h1 class="display-5 fw-bold text-success">🌐 FileShare</h1>
                            <p class="lead">Create your account</p>
                        </div>

                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show" role="alert">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="mb-4">
                                <label class="form-label fw-bold">👤 Username</label>
                                <input type="text" class="form-control form-control-lg" name="username" required>
                            </div>
                            <div class="mb-4">
                                <label class="form-label fw-bold">🔒 Password</label>
                                <input type="password" class="form-control form-control-lg" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-success btn-lg w-100 mb-3">✅ Register</button>
                        </form>

                        <div class="text-center">
                            <p class="mb-0">Already have an account? <a href="{{ url_for('login') }}" class="text-decoration-none fw-bold">Login Now</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if
             os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return render_template_string(HOME_TEMPLATE, username=session['username'], files=files)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful! Welcome back! 🎉', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password! ❌', 'error')

    return render_template_string(LOGIN_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('Registration successful! Please login. ✅', 'success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists! Please choose another. ❌', 'error')
            conn.close()

    return render_template_string(REGISTER_TEMPLATE)


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully! 👋', 'success')
    return redirect(url_for('login'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file selected! 📎', 'error')
        return redirect(url_for('home'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected! 📎', 'error')
        return redirect(url_for('home'))

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f'✅ {filename} uploaded successfully!', 'success')

    return redirect(url_for('home'))


@app.route('/download/<filename>')
def download_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/delete/<filename>')
def delete_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'🗑️ {filename} deleted successfully!', 'success')

    return redirect(url_for('home'))


@app.errorhandler(404)
def not_found(e):
    return "404 - Page Not Found! <a href='/'>Go Home</a>", 404


if __name__ == '__main__':
    print("🚀 Starting FileShare Web App...")
    print("📱 Access at: http://localhost:5000")
    print("🌐 Network access: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
