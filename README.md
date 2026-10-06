# 🔍 Bug Archaeologist — Git History Intelligence

An intelligent software engineering platform that excavates and analyzes Git repository history to reconstruct how bugs were introduced, evolved, and eventually resolved.

---

## 🌟 Key Features

- **Archaeological Git Analysis**: Parses commit history, diffs, author dynamics, and file changes.
- **Automated Bug Detection & Scoring**: Identifies bug fixes, suspicious changes, code churn, and calculates risk scores.
- **AST & Code Complexity Engine**: Analyzes Python ASTs to track syntactic complexity changes across revisions.
- **Modern Interactive Dashboard**: React & TypeScript web interface to inspect repositories, commits, bug lifecycles, and code health gauges.
- **MongoDB Storage**: Fast, persistent storage for repositories, commit histories, and discovered bugs.

---

## 🏗️ Architecture

```
Bug Archaeologist/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── analyzers/        # AST, Git, Bug Detection & Scoring
│   │   ├── api/              # REST Endpoints (analysis, repos, search)
│   │   ├── database/         # MongoDB connection & Motor managers
│   │   ├── models/ & schemas/# Pydantic & database schemas
│   │   └── services/         # Repository & analysis services
│   ├── tests/                # Pytest suite
│   └── requirements.txt
├── frontend/                 # React + TypeScript + Vite UI
│   ├── src/
│   │   ├── components/       # UI elements (HealthGauge, SeverityBadge, etc.)
│   │   ├── pages/            # Dashboard, RepositoryList, BugDetail, etc.
│   │   └── services/         # API integration
│   └── package.json
├── scripts/                  # Demo seeding & utilities
└── docs/                     # Reports & presentations
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+ and `npm`
- **MongoDB** running locally (`mongodb://localhost:27017`) or via Docker

---

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn app.main:app --reload --port 8000
```
Backend API docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend UI will be running at [http://localhost:5173](http://localhost:5173).

---

### 3. Running Tests

```bash
cd backend
pytest
```

---

## 📄 License

This project is licensed under the MIT License.
