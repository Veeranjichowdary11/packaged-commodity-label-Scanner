# 🔍 Janch (जाँच) — AI-Powered Legal Metrology Compliance & Inspection System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38BDF8.svg)](https://tailwindcss.com/)

> **Janch (जाँच)** is an intelligent end-to-end Legal Metrology Compliance & Product Inspection Platform developed for automated packaging label verification under the **Legal Metrology (Packaged Commodities) Rules, 2011 (India)**. 

---

## 🌟 Overview

Ensuring that packaged commodities comply with consumer protection guidelines and mandatory packaging rules is vital for market transparency. **Janch** automates label scanning, optical character recognition (OCR), multi-field extraction, rule compliance scoring, and formal PDF inspection report generation.

---

## ✨ Key Features

- **🔍 Multi-Engine OCR Processing**: Dual-engine text extraction combining OpenCV image preprocessing, Tesseract OCR, and Google Cloud Vision API fallback for maximum accuracy under diverse lighting and printing conditions.
- **🏷️ Mandatory Declaration Field Extraction**: Automatically parses essential mandatory fields required under Legal Metrology Rules:
  - Manufacturer / Packer / Importer Name & Address
  - Country of Origin
  - Common / Generic Name of Commodity
  - Net Quantity & Unit (grams, kg, ml, liters, units, etc.)
  - Month and Year of Manufacture / Packing / Import
  - Maximum Retail Price (MRP inclusive of all taxes)
  - Consumer Care Details (Phone, Email, Contact Address)
  - Expiry / Best Before Date & Batch / Lot / Serial Number
- **⚖️ Automated Rule Engine**: Evaluates extracted data against legal requirements to identify violations, missing mandatory declarations, formatting errors, and illegal price overcharges.
- **📄 PDF Inspection Report Generator**: Generates formatted, downloadable compliance audit certificates complete with scan metadata, extracted parameters, detected non-compliances, and official disclaimers.
- **📊 Real-time Dashboard & Analytics**: Interactive web application featuring scan statistics, compliance percentages, recent audit histories, manufacturer search, and product verification databases.
- **📷 Live Camera & Barcode Scanner**: Built-in browser camera feed with barcode & QR code scanning using Quagga and React-Webcam integration.

---

## 🏗️ System Architecture

```
                       +-------------------------------+
                       |      Next.js Frontend UI      |
                       |  (Dashboard, Live Camera,     |
                       |   Report Viewer, Analytics)   |
                       +---------------+---------------+
                                       |
                                HTTP / REST API
                                       |
                       +---------------+---------------+
                       |       FastAPI Backend         |
                       +-------+-------+-------+-------+
                               |       |       |
            +------------------+       |       +-------------------+
            |                          |                           |
+-----------v-----------+  +-----------v-----------+  +------------v-----------+
|  OCR & Vision Service |  |   Compliance Engine   |  |   Report Generator     |
| (OpenCV + Tesseract / |  | (Rules Verification & |  |  (ReportLab PDF &      |
| Google Vision API)    |  |  Anomaly Detection)   |  |   Barcode Encoding)    |
+-----------------------+  +-----------------------+  +------------------------+
            |                          |                           |
            +------------------+       |       +-------------------+
                               |       |       |
                       +-------v-------v-------v-------+
                       |    SQLite Async Database      |
                       |         (SQLAlchemy)          |
                       +-------------------------------+
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database & ORM**: SQLAlchemy (Async Engine), SQLite (`aiosqlite`)
- **Security & Authentication**: OAuth2 with Password Hashing (`bcrypt`), JWT (`python-jose`)
- **Computer Vision & OCR**: OpenCV (`opencv-python-headless`), Tesseract OCR (`pytesseract`), Pillow, Google Cloud Vision API
- **Barcode & PDF Generation**: `pyzbar`, `python-barcode`, `ReportLab`

### Frontend
- **Framework**: [Next.js 14](https://nextjs.org/) (React 18, App Router)
- **Styling**: Tailwind CSS, Lucide React icons
- **Data Visualization**: Recharts
- **Media & Hardware**: React Webcam, Quagga JS Barcode Reader

---

## 📁 Repository Structure

```
SIH/
├── backend/                  # FastAPI Backend Application
│   ├── app/
│   │   ├── api/routes/       # API Routers (auth, scans, dashboard, products, manufacturer)
│   │   ├── core/             # Configuration & DB connection
│   │   ├── models/           # SQLAlchemy Data Models
│   │   ├── schemas/          # Pydantic Request/Response Schemas
│   │   ├── services/         # OCR Service, Compliance Engine, Field Extractor, PDF Report Generator
│   │   └── utils/            # Helper utilities
│   ├── main.py               # Application Entry Point
│   ├── requirements.txt      # Backend Python Dependencies
│   └── .env.example          # Environment Variables Template
├── frontend/                 # Next.js Frontend Application
│   ├── src/                  # Components, Pages, & API Client
│   ├── package.json          # Node.js Dependencies & Scripts
│   ├── tailwind.config.js    # Tailwind CSS Configuration
│   └── tsconfig.json         # TypeScript Configuration
├── server/                   # Socket / Microservice Extension directory
├── .env.example              # Root Environment Template
├── .gitignore                # Root Git Ignore Configuration
├── LICENSE                   # Open Source MIT License
└── requirements.txt          # Root Python Dependencies
```

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed on your system:
- **Python**: `v3.10` or higher
- **Node.js**: `v18.0` or higher & `npm`
- **Tesseract OCR**: Installed on your system path (optional for Google Vision fallback)
  - *Windows*: Download installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
  - *Linux*: `sudo apt-get install tesseract-ocr`
  - *macOS*: `brew install tesseract`

---

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   - **Windows**:
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

5. Run database seed (optional for sample products & manufacturers):
   ```bash
   python seed.py
   ```

6. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be live at `http://localhost:8000`. Interactive API Docs are available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Access the web dashboard at `http://localhost:3000`.

---

## ⚙️ Environment Variables

Create a `.env` file in the `backend/` directory (or use root `.env`):

```env
APP_NAME="Janch - Legal Metrology Compliance Checker"
VERSION="1.0.0"
DEBUG=True
DATABASE_URL="sqlite+aiosqlite:///./janch.db"
SECRET_KEY="your-random-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=480
UPLOAD_DIR="uploads"
REPORTS_DIR="reports"
MAX_UPLOAD_SIZE=10485760
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
GOOGLE_VISION_API_KEY="your_google_cloud_vision_api_key_here"
```

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new inspector / officer account |
| `POST` | `/api/auth/login` | Authenticate user and receive JWT access token |
| `GET` | `/api/auth/me` | Fetch current authenticated profile |
| `POST` | `/api/scans/` | Upload package label image for OCR & compliance audit |
| `GET` | `/api/scans/` | List past scan history with pagination |
| `GET` | `/api/scans/{id}` | Retrieve scan details and extracted fields |
| `GET` | `/api/scans/{id}/report` | Download generated PDF compliance report |
| `GET` | `/api/dashboard/stats` | Fetch overall compliance statistics & metrics |
| `GET` | `/api/products/` | Query product database & verify packaging details |
| `GET` | `/api/manufacturer/` | Search manufacturers & compliance index |

---

## 📤 Pushing to GitHub

To push this repository to GitHub for the first time:

1. Initialize Git in the root folder:
   ```bash
   git init
   ```

2. Stage all files:
   ```bash
   git add .
   ```

3. Commit changes:
   ```bash
   git commit -m "feat: initial commit for Janch Legal Metrology Compliance System"
   ```

4. Link remote GitHub repository and push:
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.NAME.git
   git push -u origin main
   ```

---

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for full details.
