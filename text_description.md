# Team TIDO

**GitHub Link:** [https://github.com/ShavonneLim/TikTok-TechJam---Legal-AI-Chatbot](https://github.com/ShavonneLim/TikTok-TechJam---Legal-AI-Chatbot)  
**YouTube Link:** [https://youtu.be/WK71iQTOsR4](https://youtu.be/WK71iQTOsR4)

---

## Introduction
Our team, **TIDO**, has developed a prototype system for the track **"From Guesswork to Governance: Automating Geo-Regulation with LLM."**  
The proposed solution directly addresses the problem of identifying and managing **geo-specific compliance requirements** for new features at TikTok. By leveraging **advanced AI** and a **comprehensive data pipeline**, our system turns this **reactive, manual process** into a **proactive, auditable** one.

---

## How it Addresses Requirements
The system meets all specified task requirements and deliverables:

- **Reduce Compliance Governance Costs**  
  Our automated solution drastically lowers the manual effort required. Product teams can simply input feature descriptions into the system's chat interface and receive an **instant analysis**, rather than spending hours on manual research and consultation.

- **Mitigate Regulatory Exposure**  
  By **proactively flagging features** that require geo-specific logic **before** they are launched, our system helps prevent legal and financial risks from **undetected compliance gaps**. The AI-driven analysis provides **early warnings** and **actionable insights**.

- **Enable Audit-Ready Transparency**  
  The system generates a clear output that includes a **required flag**, **detailed reasoning**, and the **related regulations**. This automated evidence trail is **auditable**, allowing the company to confidently respond to regulatory inquiries and demonstrate that features have been **screened for regional compliance needs**.

---

## Features & Functionalities
Our solution is a **full-stack web application** with distinct features and functionalities:

### 1. Frontend Interface & User Experience
- **Secure Login**  
  - Built with **HTML**, **CSS**, and **JavaScript**
  - Managed by **Flask-Login** for user authentication and session management
  - Uses **Werkzeug** for secure password hashing  
  - Implements **CSRFProtect** to prevent cross-site request forgery

- **AI Chat Interface**  
  - Conversational interface where users can input **feature artifacts** and **legal queries**
  - Responses are **tailored to the user's geolocation** using the browser's built-in **`navigator.geolocation` API**

- **Source Management Page**  
  - Dedicated page for uploading **new legal resources** (e.g., websites, PDFs)
  - Automatically enriches the **system’s knowledge base**

---

### 2. Data Handling & Web Scraping
- **URL Classification** → Automatically detects content type (HTML, PDF, etc.)
- **Web Scraping & Extraction**
  - **HTML pages:** Parsed using **BeautifulSoup4**
  - **PDFs:** Extracted using **pdfplumber**
  - **Fallback:** **PyMuPDF** converts PDFs into high-resolution images → processed via **Pytesseract** + **PIL** for **OCR**
- **Data Processing** → Cleaned, normalized, deduplicated, and stored efficiently

---

### 3. AI & Backend Logic
- **Classification**  
  Uses **Ollama model** for **section classification** and fallback **paragraph splitting**.
  
- **Retrieval-Augmented Generation (RAG)**  
  Core of the solution → Generates **human-like**, **well-reasoned responses**.

- **Vector Database**  
  - Classified texts stored in **MongoDB**
  - Optimized for **efficient retrieval**

- **Intelligent Retrieval**  
  Uses **k-nearest neighbors (KNN)** to fetch **relevant legal data**.

- **LLM Integration**  
  Combines retrieved documents with **LLaMA 3.2** to generate:
  - Required compliance flags
  - Explanations
  - Related regulations

---

## Development Tools

| **Tool**              | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Python**            | Primary backend language for Flask server, AI integration, data processing   |
| **Flask**             | Web framework to build backend server and APIs                              |
| **HTML / CSS / JS / Bootstrap** | Frontend development and UI interactivity                           |
| **Visual Studio Code** | IDE for coding, debugging, and project management                           |
| **MongoDB**           | Stores users, URLs, scraped data, AI outputs                                 |
| **BeautifulSoup4**    | Web scraping and HTML parsing                                               |
| **Requests**          | Fetches website data and APIs                                               |
| **pdfplumber**        | Extracts text and tables from PDFs                                          |
| **PyMuPDF (fitz)**    | Converts PDFs to high-res images for OCR                                    |
| **Pytesseract**       | Optical Character Recognition (OCR)                                         |
| **Pillow (PIL)**      | Image preprocessing for OCR                                                 |
| **Regex (re)**        | Text cleaning and pattern matching                                          |
| **Flask-Login**       | User sessions and authentication                                            |
| **Werkzeug**          | Secure password hashing and file uploads                                   |
| **Flask-WTF / CSRFProtect** | Protects against CSRF attacks                                        |
| **Flask-Talisman**    | Enforces HTTPS and adds security headers                                    |
| **Flask-Limiter**     | Implements rate limiting                                                    |
| **LLaMA 3.2**         | Large language model for classification and generation                      |
| **RAG**               | Combines retrieval and generative AI for better answers                     |

---

## Libraries

### Web Framework & Security
- Flask, Flask-Login, Werkzeug, Flask-WTF (CSRFProtect), Flask-Talisman, Flask-Limiter

### Database / Data Handling
- **pymongo**, **bson**, **json**, **os**, **io**

### Web Scraping & Parsing
- **requests**, **BeautifulSoup4**, **re**

### PDF / OCR Handling
- **pdfplumber**, **PyMuPDF (fitz)**, **PIL (Pillow)**, **pytesseract**

### Utilities
- **threading**, **time**, **datetime**, **urllib.parse**

### AI / NLP
- **llama3.2**
- **RAG (Retrieval-Augmented Generation)**

---

## Assets
- **Frontend UI files** → HTML, CSS, JS  
- **User-uploaded PDFs / images** → For OCR and text extraction  
- **Static assets** → Icons, fonts, images  
- **MongoDB collections** → Store users, documents, and AI outputs  

---

## APIs
- **Geolocation API** → `navigator.geolocation`  
- **Reverse Geolocation API** → [Nominatim OpenStreetMap](https://nominatim.openstreetmap.org)  
- **Web scraping targets** → Accessed via `requests`  
- **Optional AI APIs** → LLaMA or RAG can be hosted externally

---

## Additional Datasets
- [Florida Senate Bill Text Filed PDF](https://www.flsenate.gov/Session/Bill/2024/3/BillText/Filed/PDF)  
- [Florida Senate Bill Text C1 PDF](https://www.flsenate.gov/Session/Bill/2024/3/BillText/c1/PDF)  
- [Florida Senate Bill Text C2 PDF](https://www.flsenate.gov/Session/Bill/2024/3/BillText/c2/PDF)
