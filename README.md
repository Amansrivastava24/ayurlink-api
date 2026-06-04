# AyurLink - Clinical Terminology & Mapping Portal

AyurLink is a FHIR-compliant terminology service and interactive portal designed to bridge traditional Indian medicine systems—**Ayurveda, Siddha, and Unani (NAMASTE)**—with modern biomedicine standards (**WHO ICD-11**). 

The portal allows clinical practitioners, researchers, and developers to search unified terminologies, resolve mapping concepts, and retrieve compliant FHIR resources dynamically.

---

## Key Features

* **Unified Terminology Search**: Live case-insensitive search across Ayurveda, Siddha, Unani traditional systems and ICD-11 codes returning standard FHIR ValueSet expansions.
* **Concept Map Translator**: Interactive translator utilizing FHIR ConceptMaps to map traditional NAMASTE codes directly to equivalent ICD-11 Biomedicine (MMS) or traditional medicine (TM-2) codes.
* **FHIR Resource Inspector**: Visual, pre-formatted JSON inspectors to inspect raw ValueSet, CodeSystem, and ConceptMap schema structures directly in the browser.
* **System Status Health Indicator**: Automatic polling check verifying the status of the local/remote backend terminology service.
* **Aesthetic Dashboard**: Custom dark-themed glassmorphism interface styled using vanilla CSS for optimal speed, layout responsiveness, and clinical clarity.

---

## Tech Stack

* **Backend**: FastAPI (Python), SQLModel (SQLAlchemy wrapper), Uvicorn, PostgreSQL (Render) / SQLite.
* **Frontend**: React.js, Vite, TypeScript, Lucide Icons, Vanilla CSS.
* **Data Layer**: Pandas & openpyxl for clean ingestion of Excel terminology definitions and `final_mappings.csv` files.

---

## Project Structure

```text
Ayurlink/
├── app/                      # Backend FastAPI Application
│   ├── core/                 # Database engines & global configuration
│   ├── data/                 # Ingestion & data seeding scripts
│   ├── models/               # SQLModel schemas (Term)
│   ├── main.py               # Main API endpoints & startup initialization
│   └── services/             # Third party integrations (WHO API client)
├── data/                     # Source traditional terminology Excel sheets
├── frontend/                 # Vite React-TS Frontend application
│   ├── src/
│   │   ├── App.tsx           # Main Dashboard component
│   │   ├── index.css         # Styling system & theme declarations
│   │   └── main.tsx          # React application mount
│   └── index.html            # Main HTML document
├── mapping-engine/           # Data matching models & engine outputs
│   └── output/
│       └── final_mappings.csv # Clean mapping CSV loaded during ingestion
├── .env.example              # Environment variables template
├── run_backend.bat           # Batch startup script for the Backend
├── run_frontend.bat          # Batch startup script for the Frontend
└── requirements.txt          # Python dependencies
```

---

## Local Installation & Setup

### 1. Database Configuration
Rename `.env.example` to `.env` in the root folder, and set your active database connection:
* **SQLite (Default / Zero-Setup)**:
  ```env
  DATABASE_URL="sqlite:///ayurlink.db"
  ```
* **PostgreSQL (Cloud / Remote)**:
  ```env
  DATABASE_URL="postgresql://[user]:[password]@[host]:[port]/[dbname]?sslmode=require"
  ```

### 2. Python Backend Setup
Initialize a Python virtual environment and install the required dependencies:
```powershell
# Create virtual environment
python -m venv .venv

# Install backend dependencies
.venv\Scripts\pip.exe install -r requirements.txt

# Install extra required libraries
.venv\Scripts\pip.exe install httpx beautifulsoup4
```

### 3. Seed the Database
Run the ingestion script to create tables and load all terminology records and mappings:
```powershell
.venv\Scripts\python.exe app/data/ingestion.py
```

### 4. React Frontend Setup
Navigate into the frontend folder and install Node.js dependencies:
```powershell
cd frontend
npm install
```

---

## Running the Application

For convenience, you can run the batch scripts in the project root:
* Run **`run_backend.bat`** (or execute `.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000`).
* Run **`run_frontend.bat`** (or run `npm run dev` inside the `frontend/` directory).

Once started:
* **Interactive Frontend**: [http://localhost:5173/](http://localhost:5173/)
* **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## FHIR Terminology Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/search` | `GET` | Unified terminology search across all systems. Returns standard ValueSet. |
| `/fhir/CodeSystem` | `GET` | Dynamically aggregates all NAMASTE terms into a single FHIR CodeSystem. |
| `/fhir/ConceptMap` | `GET` | Generates the complete FHIR ConceptMap expressing NAMASTE-to-ICD11 relationships. |
| `/fhir/ConceptMap/$translate` | `GET` | Translates a single source code (e.g. `A-1`) using FHIR ConceptMap parameters. |