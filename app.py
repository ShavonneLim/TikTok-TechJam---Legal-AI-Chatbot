from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from urllib.parse import urlparse
import re
import os
import json
import requests
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pdfplumber
import io
import fitz # PyMuPDF
import pytesseract
from PIL import Image
import threading
import datetime
#################################################
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import OllamaEmbeddings
import faiss  # For FAISS (vector search)
import numpy as np # For Data handling
import os
import datetime
import re

# Declare chosen models
query_model = OllamaLLM(model="llama3.2")
embedding_model = OllamaEmbeddings(model = "nomic-embed-text")

# Declare prompt format structure with a template
promptTemplate = """
My name is Jonathan Chew. You are my personal versatile AI companion and assistant.

Here is the conversation history: {chatlog}

Here is some context: {context}

Answer the question below.
Question: {question}

Answer:
"""
# Declare the number of nearest neighbors to retrieve
numNearestNeighbors = 1

# Connect the prompt and LLM model by "chaining" them together
prompt = ChatPromptTemplate.from_template(promptTemplate)
chain = prompt | query_model

# Generate embeddings for each document in the dataset.
def get_embeddings(documents):    
    # Generate embeddings for documents
    embeddings = embedding_model.embed_documents(documents)
    
    # Convert to numpy array
    embeddings = np.array(embeddings)
    return embeddings

# Initialize FAISS index and add embeddings to it.
def initialize_faiss_index(document_embeddings):
    embedding_dim = document_embeddings.shape[1]  # Dimension of the embeddings
    faiss_index = faiss.IndexFlatL2(embedding_dim)  # Use L2 distance for similarity
    faiss_index.add(document_embeddings)  # Add document embeddings to FAISS index
    return faiss_index

# Function to retrieve the most similar (nearest) documents using FAISS and MongoDB
def retrieve_top_k_documents(userInputEmbedding, infoDatabase, k):
    if len(infoDatabase) != 0:
        # extract all embeddings from infoDatabase into an array and convert to numpy array
        infoDatabaseEmbeddings = []
        corrospondingData = []

        # Loop over keys that have embeddings
        for key in ["Abbreviations", "data", "webscrapped_data"]:
            value_list = infoDatabase.get(key, [])

            if key == "webscrapped_data":
                # Each item is a dict containing 'content_sections' (which is a list)
                for item in value_list:
                    content_sections = item.get("content_sections", [])
                    for section in content_sections:  # iterate over list directly
                        itemTitle = section.get("title", [])
                        itemContent = section.get("content", [])
                        itemEmbedding = section.get("embeddings", [])
                        infoDatabaseEmbeddings.append(itemEmbedding)
                        corrospondingData.append({"mainPoint" : itemTitle, "elabContent" : itemContent, "contentEmbedding" : itemEmbedding})
            else:
                # Abbreviations and data
                for item in value_list:
                    itemTerm = item.get("term", [])
                    itemExplanation = item.get("explanation", [])
                    itemEmbedding = item.get("embedding", [])
                    infoDatabaseEmbeddings.append(itemEmbedding)
                    corrospondingData.append({"mainPoint" : itemTerm, "elabContent" : itemExplanation, "contentEmbedding" : itemEmbedding})

        infoDatabaseEmbeddings = np.array(infoDatabaseEmbeddings)

        # Initialize FAISS index
        faiss_index = initialize_faiss_index(infoDatabaseEmbeddings)

        # Perform similarity search using FAISS (on stored embeddings from database)
        distances, indices = faiss_index.search(userInputEmbedding, k)

        # Retrieve the actual vectors of the nearest neighbors
        nearest_vectors = np.array(infoDatabaseEmbeddings)[indices[0]]

        # Retrieve the corresponding documents
        mainPoint = [corrospondingData[i]["mainPoint"] for i in indices[0]]
        elabContent = [corrospondingData[i]["elabContent"] for i in indices[0]]

        # Combine results for easier handling
        knnResults = []
        for i in range(k):
            knnResults.append({
                "point": mainPoint[i],
                "document": elabContent[i],
                "vector": nearest_vectors[i].tolist(),  # Convert to list for JSON compatibility
                "distance": distances[0][i],
                "index": indices[0][i]
            })

        return knnResults
    
    return None

#################################################

# Global dictionary to track scraping tasks
scraping_tasks = {}

# ---------------------- Configuration ----------------------
app = Flask(__name__)
# Secrets & cookies
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')  # override in prod
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    # Set SECURE=True when you serve over HTTPS:
    SESSION_COOKIE_SECURE=bool(os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'),
)

# CSRF (protects all POST/PUT/DELETE by default)
CSRFProtect(app)

# Basic security headers (CSP tuned for Bootstrap CDN)
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://cdn.jsdelivr.net","'sha256-W5+htbxtKeL5CoScW0XRg99l36pqNOhRaVAgJntqhnQ='","'sha256-yOlt6R4B4mKeVB2CkudZc3zXsQA1gL+8TDLKrCSE45k='"],
    'style-src': ["'self'", "https://cdn.jsdelivr.net", "'unsafe-inline'"],  # inline needed by Bootstrap
    'img-src': ["'self'", "data:"],
    'connect-src': ["'self'", "https://nominatim.openstreetmap.org"]
}

Talisman(
    app,
    content_security_policy=csp,
    frame_options='DENY',
    referrer_policy='no-referrer',
    force_https=False,  # set True behind HTTPS
)

# Rate limiting (global + per-endpoint)
limiter = Limiter(get_remote_address, app=app, default_limits=["500 per day", "100 per hour"])

app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/flask_chat_app')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf'])

    
# ---------------------- MongoDB ----------------------------
client = MongoClient(app.config['MONGO_URI'])
db = client.get_database()
db_rag = client['RAG']
users_col = db['users']
msgs_col = db['messages']
sources_col = db['sources']  # new collection for entries (title, url, type)

# Ensure indexes
users_col.create_index('email', unique=True, name='uniq_email')
sources_col.create_index([('created_at', -1)], name='created_at_desc')

#################################################
# Retrieve data (& embeddings) from information database
def getInformationDB():
    all_data = {}

    # Loop through each collection and extract all data from RAG database (on stored embeddings from database)
    for collection_name in db_rag.list_collection_names():
        collection = db_rag[collection_name]
        documents = list(collection.find({}))  # fetch all docs
        all_data[collection_name] = documents  # append to master dict

    return all_data

#################################################

# ---------------------- Login Manager ----------------------
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, doc):
        self.id = str(doc['_id'])
        self.email = doc.get('email')
        self.name = doc.get('name') or self.email

    @staticmethod
    def get(user_id):
        try:
            doc = users_col.find_one({'_id': ObjectId(user_id)})
        except Exception:
            doc = None
        return User(doc) if doc else None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ---------------------- Helpers ----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_files(file_list):
    saved = []
    for f in file_list:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            ts = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            name, ext = os.path.splitext(filename)
            safe_name = f"{name}_{ts}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            f.save(filepath)
            saved.append(safe_name)
    return saved

# ---------------------- Routes: Auth -----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('register'))
        if users_col.find_one({'email': email}):
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))
        hashed = generate_password_hash(password)
        res = users_col.insert_one({'name': name, 'email': email, 'password': hashed, 'created_at': datetime.datetime.utcnow()})
        user = User(users_col.find_one({'_id': res.inserted_id}))
        login_user(user)
        flash('Registration successful. Welcome!', 'success')
        return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        doc = users_col.find_one({'email': email})
        if doc and check_password_hash(doc.get('password', ''), password):
            login_user(User(doc))
            flash('Logged in successfully.', 'success')
            return redirect(url_for('chat'))
        flash('Invalid credentials.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ---------------------- Routes: Pages ----------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

# ---------------------- Chat APIs --------------------------
@app.route('/chat/history')
@login_required
def chat_history():
    msgs = list(msgs_col.find({'user_id': ObjectId(current_user.id)}).sort('created_at', 1).limit(200))
    def to_dict(m):
        return {
            'role': m.get('role'),
            'text': m.get('text'),
            'files': m.get('files', []),
            'created_at': m.get('created_at', datetime.datetime.utcnow()).isoformat() + 'Z'
        }
    return jsonify([to_dict(m) for m in msgs])

@app.route('/chat/send', methods=['POST'])
@login_required
def chat_send():
    text = request.form.get('message', '').strip()
    files = request.files.getlist('files')
    saved_files = save_files(files)
    lat = request.form.get('lat', 0)
    lon = request.form.get('lon', 0)
    acc = request.form.get('accuracy', 0)
    country = request.form.get('country', 'nil')
    country_code = request.form.get('country_code', 'nil')


    user_msg = {
        'user_id': ObjectId(current_user.id),
        'role': 'user',
        'text': text,
        'files': saved_files,
        'created_at': datetime.datetime.utcnow(),
    }

    location_data = {'lat': lat, 'lon': lon, 'acc': acc, 'country': country, 'country_code': country_code}

    print(location_data)
    if text or saved_files:
        msgs_col.insert_one(user_msg)

    # reply_lines = []
    # if text:
    #     reply_lines.append(f'You said: "{text}"')
    # if saved_files:
    #     reply_lines.append("I see you uploaded: " + ", ".join(saved_files))
    # if not reply_lines:
    #     reply_lines.append("Send a message or upload a file to get started!")

    #################################################
    # Generate an embedding for the user's query.
    userInputEmbedding = get_embeddings([user_msg])

    # Get chat data - zh's code
    texts = [doc["text"] for doc in msgs_col.find({}, {"_id": 0, "text": 1}) if "text" in doc]
    chatHistory = "\n".join(texts)
    
    # ------- Information Database Retrieval (RAG) -------
    # Get information database data
    infoDatabase = getInformationDB()

    # Retrieve the most relevant documents using the MongoDB database and FAISS for similarity
    knnResults = retrieve_top_k_documents(userInputEmbedding, infoDatabase, numNearestNeighbors)
    
    # Combine the retrieved RAG information into a single context string.
    RAGcontext = "Here are some relevant context information, use where applicable:"
    if knnResults != None:
        for cd in knnResults:
            if cd["document"] != []:
                RAGcontext += "\n" + cd["document"]

    # print(RAGcontext)
    # ------- Generation of AI Output -------
    # Provide input to give the chain (prompt + model), and store output in the "AIoutput" variable
    AIoutput = chain.invoke({"question" : user_msg['text'], "context" : RAGcontext, "chatlog" : chatHistory})
    #################################################

    bot_msg = {
        'user_id': ObjectId(current_user.id),
        'role': 'bot',
        # 'text': "  \n".join(reply_lines) + AIoutput,
        'text': AIoutput,
        'files': [],
        'created_at': datetime.datetime.utcnow(),
    }
    msgs_col.insert_one(bot_msg)

    return jsonify({'ok': True, 'messages': [
        {'role': 'user', 'text': user_msg['text'], 'files': user_msg['files']},
        {'role': 'bot', 'text': bot_msg['text'], 'files': []},
    ]})


@app.route('/sources', methods=['GET', 'POST'])
@login_required
def sources():
    message = ""
    websites_collection = db_rag["regulatory_websites"]
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        if not name or not url:
            message = "Error: All fields are required!"
        else:
            try:
                if websites_collection.find_one({"url": url}):
                    message = "Error: This URL is already in the database."
                else:
                    scraper_type = auto_detect_scraper_type(url)
                    new_website = {
                        "name": name,
                        "url": url,
                        "scraper_type": scraper_type,
                        "date_added": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    websites_collection.insert_one(new_website)
                    task_id = f"scrape_{int(time.time())}"
                    thread = threading.Thread(target=background_scraper, args=(new_website, task_id))
                    thread.daemon = True
                    thread.start()
                    message = f"Success: Website added to database! Scraping started in background (Task ID: {task_id})"
                    return redirect(url_for('sources'))
            except Exception as e:
                message = f"An error occurred: {e}"
    existing_websites = list(websites_collection.find({}).sort("date_added", -1))
    return render_template('sources.html', message=message, websites=existing_websites)

@app.route('/scrape_all')
def scrape_all():
    websites_collection = db_rag["regulatory_websites"]
    websites = list(websites_collection.find({}))
    if not websites:
        return jsonify({"message": "No websites to scrape"})
    task_ids = []
    for website in websites:
        task_id = f"scrape_all_{website['_id']}_{int(time.time())}"
        thread = threading.Thread(target=background_scraper, args=(website, task_id))
        thread.daemon = True
        thread.start()
        task_ids.append(task_id)
    return jsonify({
        "message": f"Started scraping {len(websites)} websites",
        "task_ids": task_ids
    })

# ---------------------- File serving (dev only) ------------
@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------------------- CLI Helper -------------------------
@app.cli.command('create-demo-user')
def create_demo_user():
    """flask create-demo-user"""
    email = 'demo@example.com'
    if not users_col.find_one({'email': email}):
        users_col.insert_one({
            'name': 'Demo User',
            'email': email,
            'password': generate_password_hash('password'),
            'created_at': datetime.datetime.utcnow(),
        })
        print("Created demo user: demo@example.com / password")
    else:
        print("Demo user already exists.")


def auto_detect_scraper_type(url: str) -> str:
    url_lower = url.lower()
    if re.search(r"(\.pdf|/pdf)$", url, re.IGNORECASE):
        return "pdf"
    try:
        head_response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = head_response.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type:
            return "pdf"
    except requests.RequestException:
        pass
    if "flsenate.gov" in url_lower and "pdf" in url_lower:
        return "pdf"
    try:
        get_response = requests.get(url, timeout=5)
        if "application/pdf" in get_response.headers.get("Content-Type", "").lower():
            return "pdf"
        soup = BeautifulSoup(get_response.text, 'html.parser')
        embed_tag = soup.find('embed', src=lambda src: src and '.pdf' in src.lower())
        iframe_tag = soup.find('iframe', src=lambda src: src and '.pdf' in src.lower())
        object_tag = soup.find('object', data=lambda data: data and '.pdf' in data.lower())
        if embed_tag or iframe_tag or object_tag:
            return "pdf"
    except requests.RequestException:
        pass
    if "wikipedia.org" in url_lower:
        return "wikipedia_generic"
    return "generic_html"

def scrape_generic_html(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Cornell Law: prioritize main statute text only
        if "law.cornell.edu/uscode/text" in url.lower():
            main_content = soup.select_one("div#text")
        else:
            main_content = None

        # Fallback if not Cornell or if div#text not found
        if not main_content:
            content_selectors = [
                'main', 'div[role="main"]', 'div.main-content', 'div.content', 'article',
                'div#content', 'div.body-content', 'div.bill-text', 'div.legal-text', 'div.statute-text'
            ]
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

        if not main_content:
            main_content = soup.find('body')
        if not main_content:
            return ""

        all_text = []
        seen_text = set()
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre']):
            text = element.get_text(separator=" ", strip=True)
            text_key = re.sub(r'\s+', ' ', text).lower()
            if len(text_key) > 50 and text_key not in seen_text:
                all_text.append(text)
                seen_text.add(text_key)

        combined_text = "\n".join(all_text)
        final_text = re.sub(r'\n{2,}', '\n\n', combined_text.strip())
        return final_text

    except requests.exceptions.RequestException as e:
        print(f"❌ Error scraping {url}: {e}")
        return ""
    
def scrape_wikipedia(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find("div", {"class": "mw-parser-output"})
        if not content_div:
            print(f"⚠️ Could not find content for {url}")
            return ""

        # Remove unwanted elements that commonly appear in Wikipedia
        unwanted_selectors = [
            '.navbox',           # Navigation boxes
            '.infobox',          # Info boxes
            '.ambox',            # Article message boxes
            '.hatnote',          # Hat notes
            '.dablink',          # Disambiguation links
            '.sistersitebox',    # Sister site boxes
            '.vertical-navbox',  # Vertical navigation
            '.toc',              # Table of contents
            '.thumbcaption',     # Image captions (often repetitive)
            '.reflist',          # Reference lists
            '.catlinks',         # Category links
            '.printfooter',      # Print footer
            '.mw-editsection',   # Edit section links
            'table.wikitable',   # Most wiki tables (often metadata/navigation)
            '.sidebar',          # Sidebar content
            '.quotebox',         # Quote boxes (often duplicative)
        ]
        
        for selector in unwanted_selectors:
            for element in content_div.select(selector):
                element.decompose()

        # Also remove elements by class patterns
        unwanted_class_patterns = [
            'navbox', 'infobox', 'ambox', 'hatnote', 'dablink', 
            'vertical-navbox', 'reflist', 'catlinks', 'printfooter'
        ]
        
        for pattern in unwanted_class_patterns:
            for element in content_div.find_all(class_=lambda x: x and any(pattern in cls.lower() for cls in x)):
                element.decompose()

        # Focus on main content elements, but be more selective
        all_text = []
        seen_text = set()  # Add deduplication like in generic HTML scraper
        
        # Prioritize paragraphs and headers for main content
        for element in content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(separator=" ", strip=True)
            if text:
                # Create a normalized version for duplicate detection
                text_key = re.sub(r'\s+', ' ', text).lower()
                # Only include substantial content (more than 30 chars) and avoid duplicates
                if len(text_key) > 30 and text_key not in seen_text:
                    all_text.append(text)
                    seen_text.add(text_key)
        
        # Only include lists if they contain substantial content
        for element in content_div.find_all(['ul', 'ol']):
            # Skip if this list is inside an already-removed element's parent
            if element.find_parent(class_=lambda x: x and any(pattern in ' '.join(x).lower() for pattern in unwanted_class_patterns)):
                continue
                
            text = element.get_text(separator=" ", strip=True)
            if text and len(text) > 50:  # Only include substantial lists
                text_key = re.sub(r'\s+', ' ', text).lower()
                if text_key not in seen_text:
                    all_text.append(text)
                    seen_text.add(text_key)
        
        # Join with double newlines for better paragraph separation
        final_text = "\n\n".join(all_text)
        
        # Additional cleanup to remove common Wikipedia artifacts
        final_text = re.sub(r'\[\d+\]', '', final_text)  # Remove citation numbers
        final_text = re.sub(r'\n{3,}', '\n\n', final_text)  # Normalize whitespace
        
        return final_text.strip()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error scraping {url}: {e}")
        return ""

def scrape_pdf(url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"📄 Trying pdfplumber on {url}...")
        try:
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                all_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        cleaned = re.sub(r'\s+', ' ', text).strip()
                        all_text.append(cleaned)
                combined_text = "\n".join(all_text)
                if combined_text and is_text_repeated(combined_text):
                    print("⚠️ pdfplumber extracted repeated content. Falling back to OCR.")
                elif all_text:
                    print("✅ pdfplumber successfully extracted text.")
                    return combined_text
        except Exception as e:
            print(f"⚠️ pdfplumber failed. Reason: {e}")
            pass
        print(f"🤖 Falling back to OCR for {url}...")
        try:
            pdf_document = fitz.open(stream=response.content, filetype="pdf")
            ocr_text = []
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("ppm")
                text = pytesseract.image_to_string(Image.open(io.BytesIO(img_bytes)))
                if text:
                    cleaned_text = re.sub(r'\s+', ' ', text).strip()
                    ocr_text.append(cleaned_text)
            if ocr_text:
                print("✅ OCR successfully extracted text.")
                return "\n".join(ocr_text)
            else:
                print("❌ OCR also failed to extract any text.")
                return ""
        except Exception as e:
            print(f"❌ OCR fallback failed. Reason: {e}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading PDF from {url}: {e}")
        return ""

def is_text_repeated(text: str) -> bool:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 3:
        return False
    unique_paragraphs = set(paragraphs)
    repetition_ratio = len(unique_paragraphs) / len(paragraphs)
    return repetition_ratio < 0.5

def scrape_website(url, scraper_type):
    print(f"Scraping URL: {url} with type: {scraper_type}")
    if scraper_type == "wikipedia_generic":
        return scrape_wikipedia(url)
    elif scraper_type == "pdf":
        return scrape_pdf(url)
    else:
        return scrape_generic_html(url)

def clean_extracted_text(text: str) -> str:
    junk_patterns = [
        r"skip to (main )?content.*",
        r"home\s+accessibility\s+FAQ.*",
        r"contact\s+us.*",
        r"privacy\s+policy.*",
        r"terms\s+of\s+use.*",
        r"©.*\d{4}.*",
        r"all rights reserved.*",
        r"back to top.*"
    ]
    for pattern in junk_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    seen = set()
    cleaned_paragraphs = []
    for paragraph in re.split(r"\n+", text):
        stripped = paragraph.strip()
        if stripped and stripped.lower() not in seen:
            seen.add(stripped.lower())
            cleaned_paragraphs.append(stripped)
    return "\n\n".join(cleaned_paragraphs)

def is_ollama_running():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def process_law_content_with_ollama(content, task_id=None):
    """
    Sends cleaned content to Ollama, but with a more robust JSON parsing mechanism.
    """
    ollama_url = "http://localhost:11434/api/generate"
    model_name = "llama3"
    cleaned_content = clean_extracted_text(content)

    if not is_ollama_running():
        msg = "❌ Ollama server is NOT running on http://localhost:11434"
        print(msg)
        if task_id:
            scraping_tasks[task_id]["ollama_status"] = msg
        paragraphs = [p.strip() for p in cleaned_content.split("\n\n") if p.strip()]
        return [{"title": f"Section {i+1}", "content": p} for i, p in enumerate(paragraphs)]

    if task_id:
        scraping_tasks[task_id]["ollama_status"] = "Sending content to Ollama..."

    prompt = f"""
    You are a legal document processor. Your task is to structure the provided legal or regulatory text.

    **Your instructions:**
    1.  **DO NOT PARAPHRASE, SUMMARIZE, OR ALTER THE ORIGINAL TEXT.**
    2.  Your sole purpose is to split the document into logical, coherent sections.
    3.  Assign a concise, descriptive title for each section. If a section already has a clear title (e.g., a heading), use that. Otherwise, create one.
    4.  The 'content' of each section must contain the original text, exactly as it appeared in the document, without any changes.
    5.  Return **only valid JSON** in the following format:

    [
    {{
        "title": "A Concise Section Title",
        "content": "The full, exact text of the section, with no changes whatsoever."
    }},
    {{
        "title": "Another Section Title",
        "content": "The original text of the next section."
    }}
    ]

    Document:
    ---
    {cleaned_content}
    ---
    """
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True # Use streaming to handle potentially large responses
    }

    try:
        print("📤 Sending request to Ollama...")
        response = requests.post(ollama_url, json=payload, stream=True, timeout=600)
        response.raise_for_status()

        ollama_output_lines = []
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        ollama_output_lines.append(data["response"])
                except json.JSONDecodeError:
                    continue

        ollama_output = "".join(ollama_output_lines)
        print("📥 Received response from Ollama.")
        if task_id:
            scraping_tasks[task_id]["ollama_status"] = "Processing complete ✅"

        # Find all potential JSON blocks and pick the longest one
        json_matches = re.findall(r"(\[.*\])", ollama_output, re.DOTALL)
        if not json_matches:
            raise ValueError("No valid JSON returned from Ollama")

        # Pick the longest match as it's most likely to be the full JSON object
        json_text = max(json_matches, key=len)

        sections = json.loads(json_text)

        final_sections = []
        for i, sec in enumerate(sections):
            title = sec.get("title", f"Section {i+1}").strip()
            content = sec.get("content", "").strip()
            if content:
                final_sections.append({"title": title, "content": content})

        if not final_sections:
            raise ValueError("Empty sections after parsing Ollama output")

        return final_sections

    except Exception as e:
        msg = f"⚠️ Ollama failed, using paragraph fallback. Reason: {e}"
        print(msg)
        if task_id:
            scraping_tasks[task_id]["ollama_status"] = msg
        paragraphs = [p.strip() for p in cleaned_content.split("\n\n") if p.strip()]
        return [{"title": f"Section {i+1}", "content": p} for i, p in enumerate(paragraphs)]

# --- Background Scraper (Modified) ---

def background_scraper(website_data, task_id):
    try:
        scraping_tasks[task_id] = {"status": "running", "message": "Scraping in progress..."}

        db = client["TikTok_TechJam"]
        scraped_data_collection = db["webscrapped_data"]

        raw_content = scrape_website(website_data['url'], website_data['scraper_type'])
        if not raw_content or len(raw_content.strip()) == 0:
            scraping_tasks[task_id] = {
                "status": "error",
                "message": "No content could be extracted from the website"
            }
            return

        processed_sections = process_law_content_with_ollama(raw_content, task_id)

        # Add embeddings field as empty for now
        if processed_sections:
            for section in processed_sections:
                section["embeddings"] = None  # Placeholder for future embeddings

        scraped_law = {
            "law_name": website_data['name'],
            "source_url": website_data['url'],
            "full_text": raw_content,
            "content_sections": processed_sections if processed_sections else [],
            "scrape_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        result = scraped_data_collection.insert_one(scraped_law)

        scraping_tasks[task_id] = {
            "status": "completed",
            "message": f"Successfully scraped and processed {website_data['name']}",
            "mongo_id": str(result.inserted_id),
            "sections_count": len(processed_sections) if processed_sections else 0
        }
        print(f"✅ Successfully stored structured data for {website_data['name']}")
        print(f"📝 Sections extracted: {len(processed_sections) if processed_sections else 0}")

    except Exception as e:
        scraping_tasks[task_id] = {
            "status": "error",
            "message": f"Error during scraping or processing: {str(e)}"
        }
        print(f"❌ Background scraping/processing error: {e}")

@app.route('/scraping_status/<task_id>')
def scraping_status(task_id):
    if task_id in scraping_tasks:
        return jsonify(scraping_tasks[task_id])
    else:
        return jsonify({"status": "not_found", "message": "Task not found"})


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
