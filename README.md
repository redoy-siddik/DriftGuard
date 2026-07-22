# DriftGuard — Predictive GPU Health Monitoring

<div align="center">

**Production-ready Django ML system for detecting behavioral drift in GPU telemetry using a two-layer AI detection pipeline.**

`Django 4.2 LTS` · `scikit-learn Isolation Forest` · `Rolling Z-Score` · `REST API` · `Docker` · `PostgreSQL`

</div>

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DriftGuard Architecture                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   GPU Nodes (Simulated DCGM / Real Prometheus)                              │
│         │                                                                   │
│         ▼  5-minute intervals                                               │
│   ┌───────────────┐                                                         │
│   │  Telemetry DB │  ← TelemetrySnapshot (SQLite dev / PostgreSQL prod)     │
│   └───────┬───────┘                                                         │
│           │                                                                 │
│           ▼  DriftDetectionEngine.run()                                     │
│   ┌────────────────────────────────────────────────────┐                   │
│   │           Two-Layer AI Detection Pipeline           │                   │
│   │                                                    │                   │
│   │  Layer 1: ZScoreDriftDetector                      │                   │
│   │  ├── Baseline window: 144 samples (12 hours)       │                   │
│   │  ├── Current window:   12 samples  (1 hour)        │                   │
│   │  ├── Per-metric z-scores (temp, power, ecc, etc.)  │                   │
│   │  └── Weighted composite score (z_composite)        │                   │
│   │                                                    │                   │
│   │  Layer 2: IsolationForestDetector                  │                   │
│   │  ├── Pipeline(StandardScaler + IsolationForest)    │                   │
│   │  ├── Trained on 7-day baseline (2016 samples)      │                   │
│   │  ├── contamination=0.05                            │                   │
│   │  └── Stored as pickle in DB BinaryField            │                   │
│   │                                                    │                   │
│   │  Score Fusion:                                     │                   │
│   │  fused = 0.7 × z_composite + 0.3 × if_penalty     │                   │
│   │  if_penalty = 2.5 (anomaly) | 0.0 (normal)        │                   │
│   └────────────────────────────────────────────────────┘                   │
│           │                                                                 │
│           ▼                                                                 │
│   ┌───────────────┐     ┌───────────────┐    ┌──────────────────────────┐  │
│   │  DriftScore   │────▶│     Alert     │    │   GPUNode.current_status │  │
│   │  (composite)  │     │ warning/crit  │    │   normal/warning/critical │  │
│   └───────────────┘     └───────────────┘    └──────────────────────────┘  │
│           │                                                                 │
│           ▼                                                                 │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │            REST API (DRF) + Live Dashboard (Chart.js)    │             │
│   │   /api/v1/dashboard/summary/   /api/v1/nodes/            │             │
│   │   /api/v1/alerts/              /nodes/<id>/              │             │
│   └──────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.11+
- pip
- (Optional) Docker + Docker Compose

---

## Development Quickstart (SQLite, no Docker)

```bash
# 1. Clone repository
git clone <repo-url>
cd driftguard

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set DJANGO_SETTINGS_MODULE=config.settings.development

# 5. Apply migrations
python manage.py migrate

# 6. Generate synthetic GPU telemetry (7 days, 10 nodes, 20% with drift)
python manage.py generate_telemetry --days 7 --nodes 10 --drift-pct 0.2

# 7. Train Isolation Forest models for all nodes
python manage.py train_models

# 8. Run the drift detection pipeline
python manage.py run_detection

# 9. Launch development server
python manage.py runserver

# 10. Create an admin user (optional)
python manage.py createsuperuser
```

Access the dashboard at: **http://localhost:8000/**
REST API at: **http://localhost:8000/api/v1/**
Django Admin at: **http://localhost:8000/admin/**

---

## Docker Development Quickstart

```bash
# Start web + PostgreSQL containers
docker-compose up --build

# Apply migrations (first run)
docker-compose exec web python manage.py migrate

# Generate telemetry
docker-compose exec web python manage.py generate_telemetry --days 7 --nodes 10

# Train models
docker-compose exec web python manage.py train_models

# Run detection
docker-compose exec web python manage.py run_detection
```

---

## Production Deployment (Docker Compose + Nginx)

```bash
# 1. Copy and configure environment
cp .env.example .env
# Set all required variables (SECRET_KEY, POSTGRES_*, etc.)

# 2. Build and launch all services
docker-compose -f docker-compose.prod.yml up --build -d

# 3. Run initial setup
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker-compose -f docker-compose.prod.yml exec web python manage.py generate_telemetry --days 7 --nodes 10
docker-compose -f docker-compose.prod.yml exec web python manage.py train_models
docker-compose -f docker-compose.prod.yml exec web python manage.py run_detection
```

Services running:
- **web** — Django + Gunicorn (4 workers) on port 8000
- **db** — PostgreSQL 15 on port 5432
- **nginx** — Reverse proxy on port 80

---

## Management Commands Reference

| Command | Arguments | Description |
|---------|-----------|-------------|
| `generate_telemetry` | `--days 7 --nodes 10 --interval 5 --drift-pct 0.2 --clear --gpu-model STR` | Generate synthetic GPU telemetry data |
| `train_models` | `--node gpu-node-01` | Train Isolation Forest for all/single node |
| `run_detection` | `--node gpu-node-01` | Execute full two-layer detection pipeline |

```bash
# Full pipeline one-liner (dev)
python manage.py generate_telemetry --days 7 --nodes 10 --drift-pct 0.3 --clear && \
python manage.py train_models && \
python manage.py run_detection
```

---

## REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/nodes/` | List all GPU nodes |
| `GET` | `/api/v1/nodes/<node_id>/` | Node detail (with IF model status) |
| `PUT` | `/api/v1/nodes/<node_id>/toggle-active/` | Enable/disable node monitoring |
| `GET` | `/api/v1/nodes/<node_id>/telemetry/?hours=24` | Last N telemetry snapshots |
| `GET` | `/api/v1/nodes/<node_id>/drift-scores/?hours=48` | Drift score history |
| `GET` | `/api/v1/nodes/<node_id>/baseline/` | Per-metric baseline statistics |
| `POST` | `/api/v1/detection/run/` | Trigger full detection pipeline |
| `POST` | `/api/v1/detection/train/` | Train/retrain Isolation Forest models |
| `GET` | `/api/v1/alerts/?status=open&severity=critical&node=gpu-node-01` | Alert list with filters |
| `POST` | `/api/v1/alerts/<id>/acknowledge/` | Acknowledge an alert |
| `POST` | `/api/v1/alerts/<id>/resolve/` | Resolve an alert |
| `GET` | `/api/v1/dashboard/summary/` | Aggregate cluster health stats |
| `GET` | `/api/v1/dashboard/cluster-health/` | Per-node status matrix |
| `POST` | `/api/v1/telemetry/generate/` | Generate synthetic telemetry via API |

---

## Two-Layer Detection Pipeline

### Layer 1 — Rolling Z-Score Drift (`apps/detection/zscore.py`)

Fast, per-metric statistical comparison:

```
baseline_window = 144 samples (12 hours of data)
current_window  =  12 samples  (1 hour of data)

z_score = (current_window_mean - baseline_mean) / baseline_std

composite = Σ(|z_metric| × weight[metric])

Weights:
  temperature_c  : 0.30
  power_draw_w   : 0.25
  ecc_errors     : 0.25
  memory_used_gb : 0.10
  utilization_pct: 0.10

Thresholds:
  composite < 2.0  → normal
  2.0 ≤ x < 3.5   → warning
  x ≥ 3.5         → critical
```

### Layer 2 — Isolation Forest (`apps/detection/isolation_forest.py`)

Unsupervised multivariate anomaly detection:

```python
Pipeline([
    ('scaler', StandardScaler()),
    ('model', IsolationForest(contamination=0.05, n_estimators=100))
])
```

- **Training**: 7-day rolling baseline window (2016 samples per node)
- **Features**: all 7 telemetry metrics
- **Storage**: pickled Pipeline in `IsolationForestModel.model_blob` (BinaryField)
- **Inference**: predicts anomaly (-1) or normal (1); returns raw decision score

### Score Fusion

```python
if if_model_available:
    if_penalty = 2.5 if is_anomaly else 0.0
    fused_score = 0.7 * zscore_composite + 0.3 * if_penalty
else:
    fused_score = zscore_composite
```

---

## Real DCGM / Prometheus Integration Guide

To replace the synthetic generator with real GPU telemetry:

1. **DCGM Exporter** — Mount a custom ingestion view:

```python
# apps/telemetry/ingest.py
from apps.telemetry.models import TelemetrySnapshot
from django.utils import timezone

def ingest_dcgm_metrics(node, dcgm_payload: dict):
    """Called from your DCGM polling loop or webhook."""
    TelemetrySnapshot.objects.create(
        node=node,
        timestamp=timezone.now(),
        utilization_pct=dcgm_payload['DCGM_FI_DEV_GPU_UTIL'],
        memory_used_gb=dcgm_payload['DCGM_FI_DEV_FB_USED'] / 1024,
        temperature_c=dcgm_payload['DCGM_FI_DEV_GPU_TEMP'],
        power_draw_w=dcgm_payload['DCGM_FI_DEV_POWER_USAGE'],
        ecc_errors=dcgm_payload.get('DCGM_FI_DEV_ECC_SBE_VOL_TOTAL', 0),
        fan_speed_pct=dcgm_payload.get('DCGM_FI_DEV_FAN_SPEED', 0),
        sm_clock_mhz=dcgm_payload.get('DCGM_FI_DEV_SM_CLOCK', 0),
    )
```

2. **Prometheus** — Use `prometheus_client` or query the HTTP API endpoint, map metric names to `TelemetrySnapshot` fields, then call `ingest_dcgm_metrics()`.

3. Once real data flows into `TelemetrySnapshot`, the **detection pipeline runs identically** — no other changes needed.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | Django secret key (required in production) |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | Active settings module |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `POSTGRES_DB` | `driftguard` | PostgreSQL database name |
| `POSTGRES_USER` | `driftguard` | PostgreSQL user |
| `POSTGRES_PASSWORD` | — | PostgreSQL password |
| `POSTGRES_HOST` | `db` | PostgreSQL host (use `db` in Docker) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_SSLMODE` | `prefer` | PostgreSQL SSL mode |
| `CORS_ORIGINS` | `http://localhost:8000` | Comma-separated allowed CORS origins |
| `SECURE_SSL_REDIRECT` | `False` | Enable HTTPS redirect in production |
