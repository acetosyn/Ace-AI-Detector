import os
from datetime import timedelta
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from engine import (
    create_tables,
    db,
    User,
    detect_ai_generated,
    extract_text_from_url,
    extract_text_from_pdf,
    extract_text_from_docx,
    resource_path,
    login_manager,
    secret_key
)

app = Flask(
    __name__,
    template_folder=resource_path('templates'),
    static_folder=resource_path('static')
)

# Configure the app with settings
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

db.init_app(app)
login_manager.init_app(app)

with app.app_context():
    create_tables()


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session.permanent = True 
            session.pop('show_plagiarism_page', None)
            flash('Login successful', 'success')
            return redirect(url_for('plagiarism'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/home')
def home_page():
    session.pop('show_plagiarism_page', None)
    return redirect(url_for('plagiarism'))


@app.route('/ai_game')
@login_required
def ai_game():
    return render_template('AI_game.html')


@app.route('/plagiarism', methods=['GET', 'POST'])
@login_required
def plagiarism():
    extracted_text = ""
    ai_generated = None
    show_reset = False
    probability = None
    character_count = 0
    word_count = 0
    input_text = ""

    if request.method == 'POST' and request.form.get('action') == 'detect':
        session['show_plagiarism_page'] = True
    elif request.method == 'POST' and request.form.get('action') == 'reset':
        session['show_plagiarism_page'] = True
        return render_template(
            'plagiarism.html', 
            ai_generated=None, 
            extracted_text="", 
            probability=None, 
            show_reset=False, 
            character_count=0, 
            word_count=0,
            show_plagiarism_page=True
        )

    show_plagiarism_page = session.get('show_plagiarism_page', False)

    if request.method == 'POST' and show_plagiarism_page:
        action = request.form.get('action')
        input_text = request.form.get('input_text', '')

        if input_text.startswith('http://') or input_text.startswith('https://'):
            extracted_text = extract_text_from_url(input_text)
            if not extracted_text.strip():
                flash('No text found in the designated link', 'error')
            input_text = extracted_text

        uploaded_file = request.files.get('file_upload')
        if uploaded_file:
            file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
            if file_ext == '.pdf':
                extracted_text = extract_text_from_pdf(uploaded_file)
            elif file_ext == '.docx':
                extracted_text = extract_text_from_docx(uploaded_file)
            input_text = extracted_text

        if action == 'detect-ai' and input_text:
            detection_result = detect_ai_generated(input_text)
            ai_generated = detection_result['is_ai']
            probability = detection_result['proba']
            show_reset = True
            character_count = len(input_text)
            word_count = len(input_text.split())

         # Always calculate counts if input_text exists
        if input_text:
            character_count = len(input_text)
            word_count = len(input_text.split())

        return render_template(
            'plagiarism.html', 
            ai_generated=ai_generated, 
            extracted_text=input_text, 
            probability=probability, 
            show_reset=show_reset, 
            character_count=character_count, 
            word_count=word_count,
            show_plagiarism_page=True
        )

    return render_template(
        'plagiarism.html', 
        show_plagiarism_page=show_plagiarism_page,
        ai_generated=ai_generated, 
        extracted_text=extracted_text, 
        probability=probability, 
        show_reset=show_reset, 
        character_count=character_count, 
        word_count=word_count
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Username already in use. Please use a different username", 'error')
        elif existing_email:
            flash('Email address already in use. Please use a different email', 'error')
        else:
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        app.run(host='0.0.0.0', port=80)
