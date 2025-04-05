import os
from datetime import timedelta
import threading
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from engine import (create_tables, db, User,  say, #get_random_text, random_image,
    async_tts, detect_ai_generated, extract_text_from_url,
    extract_text_from_pdf, extract_text_from_docx, resource_path)
from engine import  db, login_manager, create_tables, secret_key #Ai_images_dir, Real_images_dir,

my_app = Flask(
    __name__,
    template_folder=resource_path('templates'),
    static_folder=resource_path('static')
)

# Configure the app with settings
basedir = os.path.abspath(os.path.dirname(__file__))
my_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'data.db')
my_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
my_app.config['SECRET_KEY'] = secret_key
my_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

db.init_app(my_app)
login_manager.init_app(my_app)

with my_app.app_context():
    create_tables()

# @my_app.route('/get_random_text')
# def get_text_for_game():
#     text, label = get_random_text()
#     return  jsonify({'text': text, 'label': int(label)})

# @my_app.route('/get_random_content')
# def get_random_content():
#     # First I Retrieve or initialize round number and score
#     round_num = session.get('round_num', 1)
#     last_type = session.get('last_type', 'image')
    
#     # Then I Retrieve the current score from the query parameter
#     score = request.args.get('score', session.get('score', 0), type=int)
#     session['score'] = score  # Store the score in the session

#     # Then I used logic If 10 rounds are completed, end the game
#     if round_num > 10:
#         # Clear session variables for the next game
#         session.pop('round_num', None)
#         session.pop('last_type', None)
#         session.pop('score', None)
#         return jsonify({'type': 'end', 'content': 'Game Over! Well done!', 'score': score})

#     # My logic to change and rotate between text and images in game
#     if last_type == 'image':
#         # Serve text if the last content was an image
#         content, label = get_random_text()
#         session['last_type'] = 'text'
#         session['round_num'] = round_num + 1
#         threading.Thread(target=say, args=(content, label)).start()
#         return jsonify({'type': 'text', 'content': content, 'label': int(label), 'round': round_num, 'score': score})

#     else:
#         # Serve image if the last content was text
#         image_path, label = random_image()
#         session['last_type'] = 'image'
#         session['round_num'] = round_num + 1
#         return jsonify({
#             'type': 'image',
#             'content': f'/get_image/{label}/{os.path.basename(image_path)}',
#             'label': 1 if label == "AI" else 0,
#             'round': round_num,
#             'score': score
#         }) 

# @my_app.route('/get_image/<label>/<filename>')
# def get_image(label, filename):
#     folder = Ai_images_dir if label == "AI" else Real_images_dir
#     return send_from_directory(folder, filename)

@my_app.route('/')
def home():
    return redirect(url_for('login'))
@my_app.route('/login', methods=["GET", 'POST'])
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

@my_app.route('/home')
def home_page():
    session.pop('show_plagiarism_page', None)
    return redirect(url_for('plagiarism'))

# #My Route to render AI_game page
@my_app.route('/ai_game')
@login_required  #  I added this so it can it only be accessible to logged-in users
def ai_game():
    return render_template('AI_game.html')

@my_app.route('/plagiarism', methods=['GET', 'POST'])
@login_required
def plagiarism():
    extracted_text = ""
    ai_generated = None
    show_reset = False
    probability = None
    character_count = 0
    word_count = 0
    input_text = ""
    result_text = ""

    # Check if 'detect' action was triggered to display the plagiarism page
    if request.method == 'POST' and request.form.get('action') == 'detect':
        session['show_plagiarism_page'] = True
    elif request.method == 'POST' and request.form.get('action') == 'reset':
        # Clear content but stay on the plagiarism page
        session['show_plagiarism_page'] = True
        extracted_text = ""
        ai_generated = None
        probability = None
        character_count = 0
        word_count = 0
        return render_template(
            'plagiarism.html', 
            ai_generated=ai_generated, 
            extracted_text=extracted_text, 
            probability=probability, 
            show_reset=False, 
            character_count=character_count, 
            word_count=word_count,
            show_plagiarism_page=True
        )

    # Determine which section to display based on session variable
    show_plagiarism_page = session.get('show_plagiarism_page', False)

    if request.method == 'POST' and show_plagiarism_page:
        action = request.form.get('action')
        input_text = request.form.get('input_text', '')

        # Extract text from URL or file if provided, or use the input text
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

            if ai_generated:
                result_text = f"AI GENERATED! {probability * 100:.2f}% AI detected."
            else:
                result_text = f"PASSES AS HUMAN! {probability * 100:.2f}% AI detection."

       
        response = render_template(
            'plagiarism.html', 
            ai_generated=ai_generated, 
            extracted_text=input_text, 
            probability=probability, 
            show_reset=show_reset, 
            character_count=character_count, 
            word_count=word_count,
            show_plagiarism_page=True
        )

        if result_text:
            tts_thread = threading.Thread(target=async_tts, args=(result_text,))
            tts_thread.start()

        return response

    # Render initial template with intro or plagiarism page based on session state
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

# Register route
@my_app.route('/register', methods=['GET', 'POST'])
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
# Logout route
@my_app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))


app= my_app


if __name__ == '__main__':
    with app.app_context():
        app.run(host='0.0.0.0', port=80)