# Celebrity Look-Alike Monorepo (Phase 1)

An original, privacy-first celebrity look-alike entertainment web application built with Next.js, FastAPI, PostgreSQL (`pgvector`), Alembic, and Docker Compose.

---

## 🌟 Architecture Overview

```
celebrity-lookalike/
├── .env.example                # Environment variable placeholders
├── docker-compose.yml          # Local Docker multi-container orchestration
├── README.md                   # Monorepo documentation
├── apps/
│   ├── api/                    # FastAPI (Python 3.12) backend service
│   │   ├── alembic/            # Alembic database migrations & pgvector setup
│   │   ├── app/
│   │   │   ├── config.py       # Pydantic Settings & environment config
│   │   │   ├── db.py           # SQLAlchemy engine & DB session dependency
│   │   │   ├── logging_config.py # Privacy-preserving log redactor
│   │   │   ├── main.py         # FastAPI application entrypoint & middleware
│   │   │   ├── models/         # SQLAlchemy models (Celebrity, CelebrityReferenceEmbedding)
│   │   │   ├── routers/        # Health & version router endpoints
│   │   │   ├── schemas/        # Pydantic schemas (Health, Version)
│   │   │   └── services/       # RecognitionProvider interface & FakeRecognitionProvider
│   │   ├── tests/              # Pytest backend test suite
│   │   └── pyproject.toml      # Python dependencies & pytest config
│   └── web/                    # Next.js 14 + React 18 + TypeScript web app
│       ├── src/
│       │   ├── app/            # App router, dark-mode glassmorphic CSS, page layout
│       │   └── components/     # Header, Footer, HealthStatus component & unit tests
│       ├── e2e/                # Playwright end-to-end smoke test
│       ├── package.json        # Frontend scripts & dependencies
│       └── vitest.config.ts    # Vitest runner configuration
```

---

## 🛡️ Core Architecture & Privacy Principles

1. **Pluggable Recognition Architecture (`RecognitionProvider`)**:
   - Decoupled interface (`RecognitionProvider`) allowing seamless ML model replacement without changing API contracts.
   - Initial `FakeRecognitionProvider` used for Phase 1 deterministic unit & integration tests.
2. **Strict Privacy & Zero Persistent Storage**:
   - User images are validated using decoded image header/pixel contents (not file extension).
   - Temporary upload deletion occurs on success and every failure path.
   - Privacy log formatter redacts base64 payload strings and vector embedding arrays from logs.
3. **Database Schema with `pgvector`**:
   - PostgreSQL table `celebrity_reference_embeddings` stores 512-dimensional vectors with an HNSW cosine index (`idx_celebrity_embeddings_hnsw`).
   - Embeddings store `model_version` tag to allow seamless recognition model upgrades.

---

## 🚀 Local Windows Setup Commands

Run all commands from the project root (`F:\Users\alish\.gemini\antigravity-ide\scratch\celebrity-lookalike`) in Windows PowerShell or Command Prompt:

### 1. Copy Environment Configuration
```powershell
Copy-Item .env.example .env
```

### 2. Launch Local Environment via Docker Compose
```powershell
docker-compose up --build -d
```

### 3. Run Alembic Database Migrations
```powershell
docker-compose exec api alembic upgrade head
```

### 4. Run Backend Pytest Suite
```powershell
docker-compose exec api pytest -v
```

### 5. Run Frontend Lint, Type-Check, and Unit Tests
```powershell
cd apps\web
npm install
npm run lint
npm run type-check
npm run test
```

### 6. Run Frontend End-to-End Smoke Test
```powershell
cd apps\web
npx playwright test
```

---

## 🔗 Active Endpoints & Verification

- **Next.js Web App**: [http://localhost:3000](http://localhost:3000)
- **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **API Version Info**: [http://localhost:8000/api/v1/version](http://localhost:8000/api/v1/version)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
