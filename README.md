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

- **🔍 Multi-Engine OCR Processing**: High-performance offline text extraction powered by **EasyOCR** (PyTorch) with automatic dimension optimization (800px) for fast, responsive CPU inference (~6–15s), with Google Cloud Vision API fallback for maximum accuracy under diverse lighting and printing conditions.
- **🏷️ Mandatory Declaration Field Extraction**: Automatically parses essential mandatory fields required under Legal Metrology Rules:
  - Manufacturer / Packer / Importer Name & Address (with Indian 6-digit PIN code detection)
  - Country of Origin
  - Common / Generic Name of Commodity (filtered from nutritional tables)
  - Net Quantity & Unit (grams, kg, ml, liters, units, etc.)
  - Month and Year of Manufacture / Packing / Import
  - Maximum Retail Price (MRP inclusive of all taxes)
  - Consumer Care Helpline Details (Toll-Free `1800` numbers, Email, Contact Address)
  - FSSAI License Number (14 digits)
  - Expiry / Best Before Date & Batch / Lot / Serial Number
- **⚖️ Automated Rule Engine**: Evaluates extracted data against legal requirements to identify violations, missing mandatory declarations, formatting errors, and illegal price overcharges.
- **📄 PDF Inspection Report Generator**: Generates formatted, downloadable compliance audit certificates complete with scan metadata, extracted parameters, detected non-compliances, and SHA-256 hash-chained verification.
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
                     Direct REST API (127.0.0.1:8000)
                                       |
                       +---------------+---------------+
                       |       FastAPI Backend         |
                       +-------+-------+-------+-------+
                               |       |       |
            +------------------+       |       +-------------------+
            |                          |                           |
+-----------v-----------+  +-----------v-----------+  +------------v-----------+
|  OCR & Vision Service |  |   Compliance Engine   |  |   Report Generator     |
| (EasyOCR + PyTorch /  |  | (Rules Verification & |  |  (ReportLab PDF &      |
| Google Vision API)    |  |  Anomaly Detection)   |  |   SHA-256 Hash Chain)  |
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
- **Computer Vision & OCR**: EasyOCR (PyTorch), OpenCV (`opencv-python-headless`), Pillow, Google Cloud Vision API
- **Barcode & PDF Generation**: `pyzbar`, `python-barcode`, `ReportLab`

### Frontend
- **Framework**: [Next.js 14](https://nextjs.org/) (React 18, App Router)
- **Styling**: Tailwind CSS, Lucide React icons
- **Data Visualization**: Recharts
- **Media & Hardware**: React Webcam, Quagga JS Barcode Reader
- **HTTP Client**: Axios with direct CORS configuration

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

> **Important**: The application requires **BOTH** the Backend and the Frontend to run simultaneously in two separate terminal windows.

### Prerequisites

Ensure you have the following installed on your system:
- **Python**: `v3.10` or higher
- **Node.js**: `v18.0` or higher & `npm`

---

### Step 1: Start the Backend (Terminal 1)

1. Open your first terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (if not already created) and activate it:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI backend server:
   - **Windows**:
     ```powershell
     .\venv\Scripts\uvicorn.exe main:app --port 8000 --reload
     ```
   - **Linux / macOS**:
     ```bash
     uvicorn main:app --port 8000 --reload
     ```

   *The backend will be live at `http://127.0.0.1:8000`. Interactive Swagger API Docs are accessible at `http://127.0.0.1:8000/docs`.*

---

### Step 2: Start the Frontend (Terminal 2)

1. Open a second terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Open your browser and go to:
   ```
   http://localhost:3000
   ```

---

## ⚙️ Environment Variables

Create a `.env` file in the `backend/` directory:

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
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
GOOGLE_VISION_API_KEY="your_google_cloud_vision_api_key_here"  # Optional (falls back to EasyOCR)
```

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new inspector / officer account |
| `POST` | `/api/auth/login` | Authenticate user and receive JWT access token |
| `GET` | `/api/auth/me` | Fetch current authenticated profile |
| `POST` | `/api/scans` | Upload package label image for OCR & compliance audit |
| `GET` | `/api/scans` | List past scan history with pagination |
| `GET` | `/api/scans/{id}` | Retrieve scan details and extracted fields |
| `GET` | `/api/scans/{id}/report` | Download generated PDF compliance report |
| `GET` | `/api/dashboard/stats` | Fetch overall compliance statistics & metrics |
| `GET` | `/api/products` | Query product database & verify packaging details |
| `GET` | `/api/manufacturer` | Search manufacturers & compliance index |

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
