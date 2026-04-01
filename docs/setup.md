# Setup Guide

[Back to README](../README.md)

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| npm | 10+ | Frontend package manager |
| Git | 2.40+ | Version control |

## Setup Flow

```
  ┌─────────┐
  │  Start  │
  └────┬────┘
       │
       v
  ┌──────────────────┐
  │ Clone / open     │
  │ project          │
  └────┬─────────┬───┘
       │         │
       v         v
  ┌─────────┐  ┌─────────────┐
  │ Backend │  │  Frontend   │
  │  Setup  │  │  Setup      │
  └────┬────┘  └──────┬──────┘
       │              │
       v              v
  Create venv     npm install
       │              │
       v              v
  Activate venv   npm run dev
       │          (localhost:3000)
       v              │
  pip install         │
       │              │
       v              │
  uvicorn --reload    │
  (localhost:8000)    │
       │              │
       v              v
  ┌──────────────────────┐
  │ Both services running│
  └──────────────────────┘
```

## Backend Setup

### 1. Create a virtual environment

```bash
cd backend
python -m venv venv
```

### 2. Activate the virtual environment

**Windows (Git Bash)**:
```bash
source venv/Scripts/activate
```

**Windows (PowerShell)**:
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**:
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Current dependencies:
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.13.0
python-dotenv==1.0.1
```

### 4. Environment variables

The backend reads from `backend/.env`. Current variables:

```env
DEBUG=true
```

### 5. Run the backend

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**.

- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Frontend Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Run the development server

```bash
npm run dev
```

The frontend will be available at **http://localhost:3000**.

### 3. Build for production

```bash
npm run build
npm start
```

## Service Communication

```
  ┌──────────────────┐     HTTP      ┌──────────────────┐
  │     Browser      │──────────────>│  Next.js Frontend │
  │  localhost:3000  │               │  localhost:3000   │
  └──────────────────┘               └────────┬─────────┘
                                              │
                                     fetch('/api/...')
                                              │
                                              v
                                     ┌──────────────────┐
                                     │  FastAPI Backend  │
                                     │  localhost:8000   │
                                     │  (CORS enabled)   │
                                     └──────────────────┘
```

The frontend at `localhost:3000` connects to the backend at `localhost:8000`. CORS is pre-configured in `backend/app/main.py`.

## Running Tests

```
  python -m unittest discover -s tests -v
       │
       ├──> test_input_acquisition.py  (101 tests)
       │
       └──> test_dummy_data.py         ( 42 tests)
                                       ─────────
                                       143 tests OK
```

All tests use Python's built-in `unittest` — no external test runner needed.

```bash
cd backend
source venv/Scripts/activate

# Run all tests
python -m unittest discover -s tests -v

# Run only the input acquisition tests
python -m unittest tests.test_input_acquisition -v

# Run only the dummy data / integration tests
python -m unittest tests.test_dummy_data -v
```

See [Testing Guide](testing.md) for full details.

## Project Structure After Setup

```
AURA/
├── backend/
│   ├── venv/                  # Python virtual environment (git-ignored)
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── core/
│   │   │   └── config.py      # Pydantic settings
│   │   ├── input_acquisition/ # Phase 1 module
│   │   ├── models/            # Domain models (future phases)
│   │   ├── routers/           # API endpoints
│   │   └── schemas/           # Request/response schemas (future)
│   ├── tests/
│   │   ├── dummy_data.py      # Deterministic test data generator
│   │   ├── test_input_acquisition.py
│   │   └── test_dummy_data.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── node_modules/          # npm packages (git-ignored)
│   ├── src/app/
│   │   ├── layout.tsx
│   │   ├── page.tsx           # Home page with API health check
│   │   └── globals.css
│   ├── package.json
│   └── tsconfig.json
└── docs/
```

## Troubleshooting

### Python not found

If `python` is not recognized, try `python3` or install via:
```bash
winget install Python.Python.3.12 --source winget
```
After installation, restart your terminal for PATH changes to take effect.

### Port already in use

If port 8000 or 3000 is occupied:
```bash
# Backend on a different port
uvicorn app.main:app --reload --port 8001

# Frontend on a different port
npx next dev --port 3001
```

Update the CORS origin in `backend/app/main.py` if you change the frontend port.

### Virtual environment activation issues on Windows

If PowerShell blocks script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
