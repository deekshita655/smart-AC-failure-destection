# Run Instructions — Smart AC Failure Intelligence & Predictive Maintenance

This project has three parts:

```
smart-ac-platform/
├── backend/     FastAPI application (this is what everyone integrates against)
├── ml/          Placeholder KMeans clustering script (plan B for the ML team)
└── frontend/    Minimal React (Vite) app with role-based dashboards
```

Everything below has been tested end-to-end (backend boot, auth, RBAC, ticket
creation, sensor → predictive-ticket pipeline, KMeans script) except the parts
that depend on external credentials you don't have yet (Azure OpenAI, Gemini) —
those fail *gracefully* with a `CONFIGURATION_PENDING` error until you supply keys.

---

## 1. Prerequisites

- Python 3.11+ (3.12 used in testing)
- Node.js 18+ and npm
- PostgreSQL 14+ (or just use SQLite for local dev — see note below)

## 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2.1 Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

- **DATABASE_URL** — point at your Postgres instance, e.g.
  `postgresql+psycopg2://ac_user:ac_password@localhost:5432/smart_ac_db`

  **No Postgres handy?** For quick local testing you can use SQLite instead —
  just set `DATABASE_URL=sqlite:///./smart_ac.db`. All SQLAlchemy models work
  unchanged. Switch back to Postgres before anything resembling production use.

- **SECRET_KEY** — set to any long random string (used to sign JWTs).
- **AZURE_OPENAI_*** / **AZURE_OPENAI_EMBEDDING_*** / **GEMINI_API_KEY** — leave
  as `CONFIGURATION_PENDING` until the Azure/Gemini owners hand you real values.
  The app boots fine without them; only `/service-tickets/{id}/analyze`,
  `/service-tickets/{id}/embed`, and `/chat/message` will return a
  `503 CONFIGURATION_PENDING` error until they're set.

### 2.2 Create the database (if using Postgres)

```sql
CREATE DATABASE smart_ac_db;
CREATE USER ac_user WITH PASSWORD 'ac_password';
GRANT ALL PRIVILEGES ON DATABASE smart_ac_db TO ac_user;
```

### 2.3 Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on startup (`Base.metadata.create_all`) — no
Alembic migration step is required for this MVP.

Interactive API docs: **http://localhost:8000/docs**

### 2.4 Seed demo data

In a second terminal (venv still active):

```bash
python seed.py
```

This creates one user per role and 3 demo devices:

| username  | password       | role               |
|-----------|----------------|--------------------|
| tech1     | Password123!   | TECHNICIAN         |
| mgmt1     | Password123!   | OVERALL_MANAGEMENT |
| quality1  | Password123!   | QUALITY            |
| design1   | Password123!   | DESIGN             |
| admin1    | Password123!   | ADMIN              |

Demo devices: `DEV-90612`, `DEV-90613`, `DEV-90700`.

### 2.5 Quick sanity check

```bash
curl http://localhost:8000/api/v1/health
# {"success":true,"data":{"status":"ok"},"request_id":"..."}

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"tech1","password":"Password123!"}'
```

---

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open **http://localhost:5173**. Sign in with `tech1` / `Password123!` (or any
seeded account). The Vite dev server proxies `/api` to `http://localhost:8000`
by default (see `vite.config.js`) — adjust `VITE_API_BASE_URL` in `.env` if
your backend runs elsewhere.

---

## 4. ML placeholder (KMeans plan-B script)

This is **not** the primary ML pipeline — it's a fallback so the platform has
something to plug in if the real pipeline isn't ready.

```bash
cd ml
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python kmeans_placeholder_training.py --input /path/to/FINALDATASET.csv --output ./artifacts --k 6
```

Outputs in `./artifacts/`:
- `kmeans_model.joblib` — fitted sklearn pipeline
- `cluster_assignments.csv` — `record` → `cluster_id`
- `metrics.json` — silhouette score, k, sample count

To push a real (or placeholder) ML prediction into a ticket, call:

```bash
curl -X POST http://localhost:8000/api/v1/service-tickets/TCK-1/ml-result \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"model_name":"kmeans-placeholder","model_version":"0.1","failure_mode":"Refrigerant Failure","component":"Compressor","department":"Refrigeration","confidence":0.7,"suggested_action":"Inspect refrigerant lines"}'
```

## 5. Simulating sensor data (predictive maintenance)

There's no separate simulator script shipped in this MVP handoff, but any
process (a cron job, a notebook, a simple loop) can POST directly:

```bash
curl -X POST http://localhost:8000/api/v1/sensors/readings \
  -H "Authorization: Bearer <technician_or_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEV-90612", "timestamp": "2026-08-12T10:00:00Z",
    "temperature": 30, "compressor_current": 12, "vibration": 5.0,
    "fan_speed": 1500, "power_consumption": 2000,
    "refrigerant_pressure": 200, "humidity": 70
  }'
```

If the values are far enough from baseline, this automatically creates a
`DeviceHealth` row, an `Anomaly` row, a `PredictiveEvent`, and a `PENDING`
`PreventiveTicket` — visible via `GET /api/v1/preventive-tickets`.

---

## 6. Power BI

Point Power BI's **Web / REST connector** at (with an `OVERALL_MANAGEMENT` or
`ADMIN` bearer token in the request header):

- `GET /api/v1/powerbi/dataset/service-tickets`
- `GET /api/v1/powerbi/dataset/ai-predictions`
- `GET /api/v1/powerbi/dataset/predictive-maintenance`

These are flattened, PII-free, read-only JSON datasets. See `architecture.md`
Part 10 for field definitions.

---

## 7. Running tests / verifying your setup works

There's no test suite bundled (out of scope per the brief), but you can
smoke-test manually via `/docs` (Swagger UI) — try, in order:
`POST /auth/login` → copy `access_token` → click **Authorize** in Swagger →
`POST /devices/lookup` → `POST /service-tickets` → `POST /service-tickets/{id}/analyze`.

---

## 8. Known limitations / things you must still supply

See `architecture.md` → **OPEN CONTRACTS** for the full list. In short:
Azure OpenAI credentials, Gemini API key, the frozen ML JSON schema, the OCR
JSON schema, and a production CORS origin list are all currently placeholders.
