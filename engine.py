#Core libraries for data processing and AI detection
import os
import sys
import time
import requests  # For making HTTP requests
from requests.exceptions import ConnectionError, Timeout  # For handling request errors
#Data and text processing libraries
import pandas as pd
import joblib
import nltk
import docx
import PyPDF2
from bs4 import BeautifulSoup
import secrets
# Speech synthesis and text-to-speech libraries
import pyttsx3
# Machine learning libraries
from flask_login import LoginManager, UserMixin
import logging
from flask_sqlalchemy import SQLAlchemy



basedir = os.path.abspath(os.path.dirname(__file__))
# Set TensorFlow environment variable and logging level
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Download NLTK packages if not already installed
def download_nltk_package(package_name):
    try:
        nltk.data.find(f'tokenizers/{package_name}')
    except LookupError:
        nltk.download(package_name)

download_nltk_package('punkt')
# # df= pd.read_csv('AI_Human.csv')
# Real_images_dir = r'C:\Users\aceto\OneDrive\Desktop\ACE 2.0\Datasets\IMAGES\REAL'
# Ai_images_dir = r'C:\Users\aceto\OneDrive\Desktop\ACE 2.0\Datasets\IMAGES\AI'

# def get_random_text():
#     # Randomly select a row from the DataFrame
#     random_row = df.sample(n=1).iloc[0]
#     full_text = random_row['text']
#     label = random_row['AI_generated']  # 1 = AI, 0 = Human

#     # Use nltk's sentence tokenizer to split into full sentences
#     sentences = sent_tokenize(full_text)
    
#     # Randomly select 2-3 sentences to construct a short text snippet
#     short_text = ' '.join(random.sample(sentences, min(3, len(sentences)))) 
#     return short_text, label
# #Printing a short example I can see
# text, label = get_random_text()

# def random_image():
#     if random.choice([True, False]):
#         image_path= os.path.join(Ai_images_dir, random.choice(os.listdir(Ai_images_dir)))
#         label= "AI"

#     else:
#         image_path= os.path.join(Real_images_dir, random.choice(os.listdir(Real_images_dir)))
#         label= "Human"
#     return image_path, label

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# engine.py
# Generate a secret key (used for app config in Ace.py)
secret_key = secrets.token_hex(16)

# Initialize database and login manager (to be used in Ace.py)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_tables():
    db.create_all()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def say(text):
    engine = pyttsx3.init()
    engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')
    if not engine._inLoop:
        engine.say(text)
        engine.runAndWait()
    else:
        engine.say(text)

def async_tts(result_text):
    time.sleep(0)
    say(result_text)

model_file_path = 'pipeline_model.pkl'

if os.path.exists(model_file_path):
    grid_search = joblib.load(model_file_path)
    print("Model loaded from disk.")

# AI Detection Function with Adjustable Threshold
def detect_ai_generated(text, threshold=0.7):
    text_series = pd.Series([text])
    proba = grid_search.predict_proba(text_series)[0][1]  # Probability of being AI-generated
    proba = round(proba, 2) 
    print(f"AI Probability: {proba:.2f}")  # For debugging purposes
    is_ai_generated = proba >= threshold
    return {'is_ai': is_ai_generated, 'proba': proba}

def extract_text_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = [tag.get_text().strip() for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']) if tag.get_text().strip()]
        extracted_text = '\n'.join(content)
        return extracted_text if extracted_text else "No significant text found in the designated link."
    except ConnectionError:
        return "Failed to connect to the website. Please check your internet connection or try another link."
    except Timeout:
        return "The request timed out. The server took too long to respond."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def extract_text_from_pdf(file_stream):
    pdf_text = ''
    reader = PyPDF2.PdfReader(file_stream)
    for page_num in range(len(list(reader.pages))):
        pdf_text += reader.pages[page_num].extract_text()
    return pdf_text

def extract_text_from_docx(file_stream):
    doc = docx.Document(file_stream)
    doc_text = '\n'.join([para.text for para in doc.paragraphs])
    return doc_text

