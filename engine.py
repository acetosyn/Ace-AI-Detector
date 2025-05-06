# Core libraries for data processing and AI detection
import os
import sys
import time
import secrets
import logging
import requests
from requests.exceptions import ConnectionError, Timeout

# Data and text processing libraries
import pandas as pd
import joblib
import docx
import PyPDF2
from bs4 import BeautifulSoup

# Flask components
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

# Set up base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Get absolute path for resources (useful for PyInstaller packaging)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Generate a secret key for app configuration
secret_key = secrets.token_hex(16)

# Initialize database and login manager
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_tables():
    """Create database tables."""
    db.create_all()

# Define User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load trained AI detection model
model_file_path = 'pipeline_model.pkl'
if os.path.exists(model_file_path):
    grid_search = joblib.load(model_file_path)
    print("Model loaded from disk.")

# Detect AI-generated text
def detect_ai_generated(text, threshold=0.7):
    """
    Predict if the given text is AI-generated.
    Returns a dict with probability and classification.
    """
    text_series = pd.Series([text])
    proba = round(grid_search.predict_proba(text_series)[0][1], 2)
    print(f"AI Probability: {proba:.2f}")
    return {'is_ai': proba >= threshold, 'proba': proba}

# Extract text from a given URL
def extract_text_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

# Extract text from a PDF file
def extract_text_from_pdf(file_stream):
    pdf_text = ''
    reader = PyPDF2.PdfReader(file_stream)
    for page in reader.pages:
        pdf_text += page.extract_text() or ''
    return pdf_text

# Extract text from a DOCX file
def extract_text_from_docx(file_stream):
    doc = docx.Document(file_stream)
    return '\n'.join([para.text for para in doc.paragraphs])
