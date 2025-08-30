Sure 🙂 Here's the full content of your **README.md** file:

---

# 🧑‍⚖️ AI-Powered Legal/Regulatory Chat Assistant

A secure, extensible Flask-based conversational AI platform powered by **LangChain**, **FAISS**, and **Ollama LLMs**, with **MongoDB-backed user/authentication** support and a **Retrieval-Augmented Generation (RAG)** pipeline for contextual responses.

This project demonstrates how to combine secure web applications, vector-based retrieval, and AI-driven document processing into a locally runnable demo.

---

## 🚀 Features

### **Authentication & User Management**

* Registration, login, and logout flows using Flask-Login.
* Password hashing with `werkzeug.security`.
* Session security hardened with CSRF protection, CSP, and secure cookies.

### **Conversational AI**

* Powered by **Ollama LLMs** (`llama3` / `llama3.2`).
* Retrieval-Augmented Generation (RAG) with **FAISS + MongoDB**.
* Contextual memory across sessions for improved conversational flow.

### **Data Handling**

* Support for **text, PDF, and image ingestion**.
* Web scraping of **generic HTML**, **Wikipedia pages**, and **PDFs** with fallback OCR (**PyMuPDF + Tesseract**).
* Background scraping with task tracking.

### **Security & Resilience**

* Rate limiting (**Flask-Limiter**).
* Strong Content Security Policy via **Flask-Talisman**.
* Sanitized uploads with file validation and per-user storage isolation.

### **Developer Utilities**

* CLI tool to generate a demo user.
* Modular scraping pipeline with automatic scraper-type detection.

---

## 📂 Project Structure

```
├── app.py              # Main Flask application
├── templates/          # Jinja2 templates (index, login, chat, etc.)
├── static/             # CSS/JS assets
├── uploads/            # User-uploaded files (auto-created at runtime)
└── requirements.txt    # Python dependencies
```

---

## 🛠️ Requirements

### **Core Dependencies**

* Python ≥ 3.9
* MongoDB ≥ 6.0 (local or remote instance)
* Ollama (must be running locally on `http://localhost:11434`)

### **Python Libraries**

Key packages (non-exhaustive):

* `Flask`, `Flask-Login`, `Flask-WTF`, `Flask-Limiter`, `Flask-Talisman`
* `pymongo`, `bson`
* `faiss-cpu`
* `langchain`, `langchain_ollama`, `langchain_community`
* `pdfplumber`, `PyMuPDF` (`fitz`), `pytesseract`, `Pillow`
* `requests`, `beautifulsoup4`

📌 See `requirements.txt` for a full list.

---

## ⚙️ Installation

### **Clone the Repository**

```bash
git clone https://github.com/your-username/legal-ai-chat.git
cd legal-ai-chat
```

### **Set up Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### **Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Start MongoDB**

```bash
mongod --dbpath ./data/db
```

### **Run Ollama**

Ensure Ollama is installed and running:

```bash
ollama run llama3
ollama run llama3.2
```

### **Set Environment Variables** *(optional for production)*

```bash
export SECRET_KEY="change-this"
export MONGO_URI="mongodb://localhost:27017/flask_chat_app"
export SESSION_COOKIE_SECURE=0   # set to 1 in production
```

### **Initialize Upload Directory**

```bash
mkdir -p uploads
```

### **Start Flask App**

```bash
flask run
```

---

## 🧪 Running the Demo

1. Open your browser at **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.
2. Register a new account, or create a demo user:

   ```bash
   flask create-demo-user
   ```

   **Demo credentials:**

   ```
   login: demo@example.com
   password: password
   ```
3. Start chatting with the AI, upload documents, or add web sources to be scraped.

---

## 🔍 Key Endpoints

| Route                   | Method(s) | Description                    |
| ----------------------- | --------- | ------------------------------ |
| `/`                     | GET       | Landing page                   |
| `/register`             | GET/POST  | User registration              |
| `/login`                | GET/POST  | User login                     |
| `/logout`               | GET       | Logout                         |
| `/chat`                 | GET       | Chat interface                 |
| `/chat/send`            | POST      | Send a message + files         |
| `/chat/history`         | GET       | Retrieve chat history          |
| `/sources`              | GET/POST  | Manage regulatory sources      |
| `/scrape_all`           | GET       | Bulk re-scrape sources         |
| `/scraping_status/<id>` | GET       | Poll background scraping tasks |

---

## 🧱 Architecture Overview

### **Frontend**

* Jinja2 templates with Bootstrap.
* AJAX/JSON endpoints for live chat updates.

### **Backend**

* Flask routes with layered middlewares (**CSRF**, **limiter**, **Talisman**).
* Authentication via **Flask-Login**.

### **AI / RAG Pipeline**

```
Input → Embedding (OllamaEmbeddings)
       → Similarity search (FAISS + MongoDB embeddings)
       → Context assembly + chat history
       → Prompting (ChatPromptTemplate)
       → Response generation (OllamaLLM)
```

### **Scraping Pipeline**

* URL classification → PDF / HTML / Wikipedia.
* Text extraction → Cleaning → Sectioning (via Ollama JSON prompt).
* Storage in MongoDB (`TikTok_TechJam.webscrapped_data`).

---

## 🔐 Security Considerations

* CSRF protection enabled across all forms.
* CSP headers block unauthorized scripts.
* Rate limiting prevents brute force/DOS attacks.
* Uploads restricted to **png, jpg, jpeg, gif, txt, pdf**.
* Passwords hashed with **PBKDF2**.

⚠️ **In production:**

* Set `SESSION_COOKIE_SECURE=1` behind HTTPS.
* Change `SECRET_KEY`.
* Run Flask behind a reverse proxy (e.g., **Nginx + Gunicorn**).

---

## 📈 Future Enhancements

* Add async task queue (**Celery/RQ**) instead of threads.
* Expand embedding coverage for uploaded documents.
* Add **Docker** support for reproducible deployment.
* Improve frontend chat UX with WebSockets.

---

## 🧑‍💻 Contributing

Pull requests welcome. Please ensure:

* Code passes **flake8** linting.
* Features include tests.
* Security is not compromised.

---

## 📜 License

**MIT License © 2025 Your Name**

---

Do you also want me to create a **cleaner, more visually structured README** with badges, images, and sections so it looks more professional on GitHub? It’ll make your project page stand out.
Should I?
