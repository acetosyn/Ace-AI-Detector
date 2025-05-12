import os
import sys
import secrets
import requests
import pandas as pd
import joblib
import docx
import PyPDF2
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, Timeout
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sklearn.exceptions import NotFittedError

# Setup base directory and model path
basedir = os.path.abspath(os.path.dirname(__file__))
model_file_name = 'pipeline_model.pkl'
model_file_path = os.path.join(basedir, model_file_name)

# Resource path utility (for PyInstaller or server deployment)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# App secret key
secret_key = secrets.token_hex(16)

# Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

# DB model for user authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create DB tables
def create_tables():
    db.create_all()

# Load AI detection model
grid_search = None
try:
    grid_search = joblib.load(resource_path(model_file_name))
    print("[INFO] pipeline_model.pkl loaded successfully.")
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")

# Detect AI-generated text
def detect_ai_generated(text, threshold=0.7):
    if not grid_search:
        return {'is_ai': False, 'proba': 0.0, 'error': 'Model not loaded.'}
    
    try:
        text_series = pd.Series([text])
        proba = round(grid_search.predict_proba(text_series)[0][1], 2)
        print(f"[DEBUG] AI Probability: {proba:.2f}")
        return {'is_ai': proba >= threshold, 'proba': proba}
    except NotFittedError:
        return {'is_ai': False, 'proba': 0.0, 'error': 'Model not fitted properly. Re-train or fix model.'}
    except Exception as e:
        return {'is_ai': False, 'proba': 0.0, 'error': str(e)}

# Extract readable text from a webpage
def extract_text_from_url(url):
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = [tag.get_text().strip() for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']) if tag.get_text().strip()]
        return '\n'.join(content) if content else "No significant text found in the designated link."
    except ConnectionError:
        return "Failed to connect to the website. Please check your internet connection or try another link."
    except Timeout:
        return "The request timed out. The server took too long to respond."
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Extract text from a PDF
def extract_text_from_pdf(file_stream):
    pdf_text = ''
    try:
        reader = PyPDF2.PdfReader(file_stream)
        for page in reader.pages:
            pdf_text += page.extract_text() or ''
    except Exception as e:
        return f"Failed to extract text from PDF: {str(e)}"
    return pdf_text

# Extract text from a DOCX
def extract_text_from_docx(file_stream):
    try:
        doc = docx.Document(file_stream)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Failed to extract text from DOCX: {str(e)}"
