# Production Deployment & Infrastructure Guide

This guide outlines container definitions, infrastructure architecture, environment variables, security hardening, and staging-first rollout procedures for deploying the **Celebrity Look-Alike Application** to production.

---

## 1. Production Architecture Overview

```
                          [ NGINX Reverse Proxy / Cloudflare Edge ]
                                     | (client_max_body_size 10M)
                                     v
                   +-----------------------------------+
                   |         Web Service (Next.js)     |
                   |      User: nextjs (UID 1001)      |
                   +-----------------------------------+
                                     |
                                     v
                   +-----------------------------------+
                   |        API Service (FastAPI)      |
                   |      User: appuser (UID 10001)    |
                   |   Mount: /models (Read-Only)      |
                   +-----------------------------------+
                        /            |            \
                       /             |             \
                      v              v              v
        +-------------------+ +-------------+ +-----------------------+
        | External Managed  | | External    | | Private S3 Object     |
        | Postgres DB       | | Managed     | | Storage               |
        | (pgvector ext)    | | Redis       | | (Celebrity Images)    |
        +-------------------+ +-------------+ +-----------------------+
                                     ^
                                     |
                   +-----------------------------------+
                   |      Worker Service (Python)      |
                   |      User: appuser (UID 10001)    |
                   |   Mount: /models (Read-Only)      |
                   +-----------------------------------+
```

---

## 2. Container Hardening & Security Policies

1. **Non-Root Container Enforcement**:
   - `api` & `worker`: Runs under `appuser` (UID `10001`, GID `10001`).
   - `web`: Runs under `nextjs` (UID `1001`, GID `1001`).
2. **Read-Only Model Mount (`/models:ro`)**:
   - Model weights (`w600k_mbf.onnx`) and license metadata are mounted as read-only volumes (`:ro`).
3. **Resource Limits & Reservations**:
   - `api`: Max 2.0 CPUs, 2048M Memory (Reservation: 0.5 CPUs, 512M Memory).
   - `worker`: Max 2.0 CPUs, 2048M Memory (Reservation: 0.5 CPUs, 512M Memory).
   - `web`: Max 1.0 CPU, 1024M Memory (Reservation: 0.25 CPUs, 256M Memory).
4. **Health & Liveness Probes**:
   - `api`: `curl -f http://localhost:8000/api/v1/health` (Interval: 10s, Timeout: 3s, Retries: 3).
   - `web`: `wget --spider http://localhost:3000/` (Interval: 15s, Timeout: 5s, Retries: 3).

---

## 3. External Managed Services Integration

### Managed PostgreSQL + pgvector
- **Engine**: PostgreSQL 16+ with `pgvector` extension enabled.
- **Connection**: SSL Mode `verify-full`.
- **Database Migrations**: Executed via Alembic before container launch (`alembic upgrade head`).

### Managed Redis
- **Engine**: Redis 7+ with TLS (`rediss://`).
- **Data Persistence**: Eviction policy `noeviction` (job queue state & TTL keys).

### Private S3-Compatible Object Storage
- **Access**: Private bucket containing licensed celebrity reference images. No user image uploads stored.

---

## 4. Staging-First Rollout Protocol

### Step 1: Pre-Flight Verification & Environment Provisioning
1. Copy `.env.production.example` to `.env.staging`.
2. Provision managed Postgres database and apply extension: `CREATE EXTENSION IF NOT EXISTS vector;`.
3. Provision managed Redis cluster and S3 reference bucket.

### Step 2: Database Migration & Model Self-Test
1. Run Alembic database migrations on staging database:
   ```bash
   alembic upgrade head
   ```
2. Verify active recognition model weights and self-test:
   ```bash
   python -c "from app.services.recognition import get_recognition_provider; print(get_recognition_provider().self_test())"
   ```

### Step 3: Staging Container Deployment & Integration Testing
1. Launch staging containers:
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.staging up -d
   ```
2. Execute full Pytest integration suite:
   ```bash
   python -m pytest -v
   ```

### Step 4: Production Blue/Green Cutover
1. Once staging health checks verify `healthy` status (`GET /api/v1/health`), deploy production environment.
2. Switch NGINX / Cloudflare edge router traffic to production containers.
3. Monitor queue metrics (`GET /api/v1/matches/queue/metrics`) and error rates.
