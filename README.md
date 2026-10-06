# DataPulse

Self-monitoring data and analytics platform.

DataPulse is a production-style portfolio project demonstrating an end-to-end data platform workflow:

**source ingestion → data modelling → ELT → data quality → analytics → anomaly detection → root-cause analysis → API → dashboard → deployment → monitoring**

The project is developed incrementally with production-oriented engineering practices, automated testing, documentation, and a realistic Git workflow.

---

## Project Goal

DataPulse demonstrates practical skills across:

- Data Engineering
- Data Analytics
- Analytics Engineering
- Applied Data Science
- Data Quality
- Backend/API Engineering
- ML/AI Engineering
- Cloud and production engineering

The platform uses realistic synthetic business data from multiple source systems and intentionally introduces data-quality problems that the platform must detect, analyze, and report.

The goal is to build one coherent data platform where each layer feeds the next rather than a collection of disconnected demonstrations.

---

## Current Status

### Completed Phases

- [x] Phase 0 — Project planning and architecture
- [x] Phase 1 — Repository and development foundation
- [x] Phase 2 — Synthetic source systems
- [x] Phase 3 — PostgreSQL and raw ingestion

### Current / Next Phase

**Phase 4 — Warehouse Data Modelling**

Phase 4 implementation begins only after the Phase 3 documentation/repository synchronization is reviewed and merged.

---

## Completed Foundation

### Phase 0 — Project Planning and Architecture

Completed:

- project definition
- business problem definition
- target users
- portfolio goals
- system scope
- technology decisions
- logical architecture
- data flow
- system boundaries
- development workflow

### Phase 1 — Repository and Development Foundation

Completed:

- Python 3.12 development environment
- project package structure
- environment configuration
- `.env.example`
- Git configuration
- feature-branch workflow
- pytest
- Ruff
- formatting and linting
- development documentation
- Docker foundation

### Phase 2 — Synthetic Source Systems

Completed:

- synthetic customer data
- synthetic product data
- synthetic order data
- synthetic payment data
- synthetic subscription data
- synthetic support-ticket data
- synthetic web-event data
- deterministic data generation
- intentional data-quality issue injection
- duplicate records
- missing values
- invalid values
- referential-integrity issues
- temporal issues
- volume anomalies
- schema-drift scenarios
- source manifests
- source materialization
- source validation
- deterministic generation validation

### Phase 3 — PostgreSQL and Raw Ingestion

Completed:

- PostgreSQL 17 local runtime
- Docker Compose PostgreSQL service
- database schemas
- raw source tables
- metadata tables
- SQL migrations
- CSV file reader
- CSV schema validation
- raw database loader
- batched loading
- transaction handling
- ingestion run tracking
- ingestion source tracking
- row-count tracking
- ingestion status tracking
- single-source ingestion orchestration
- failure handling
- PostgreSQL integration testing
- PostgreSQL rollback testing

The raw layer intentionally preserves source data and does not perform business transformations.

---

## Architecture

The target architecture is:

```text
Synthetic Source Systems
        ↓
     Ingestion
        ↓
   Raw / Bronze
        ↓
     Staging
        ↓
 Transformation / ELT
        ↓
 Analytics Warehouse
        ↓
   Data Quality
        ↓
     Analytics
        ↓
 Anomaly Detection
        ↓
 Root Cause Analysis
        ↓
      FastAPI
        ↓
 React / TypeScript Dashboard
        ↓
 AI-Assisted Explanations
        ↓
 Deployment
        ↓
 Monitoring & Observability
```

The architecture is implemented incrementally.

The current implementation reaches the PostgreSQL raw-ingestion layer.

---

## Data Sources

DataPulse currently generates seven synthetic business sources:

| Source | Approximate Volume |
|---|---:|
| Customers | 5,000 |
| Products | 250 |
| Orders | 50,000 |
| Payments | 55,000 |
| Subscriptions | 7,500 |
| Support Tickets | 15,000 |
| Web Events | 300,000+ |

Generated data covers:

```text
2025-01-01 → 2026-06-30
```

Generation is deterministic through a fixed random seed.

The source data intentionally contains realistic problems for downstream validation and analysis.

---

## Source-System Relationships

The synthetic sources represent common business systems and relationships:

```text
Customers
    │
    ├──────────────┐
    │              │
    ↓              ↓
 Orders       Subscriptions
    │              │
    ↓              ↓
Payments     Support Tickets

Products
    │
    └── referenced by Orders

Web Events
    │
    └── customer/product interaction data
```

These relationships provide the foundation for later:

- warehouse modelling
- primary and foreign-key validation
- dimensional modelling
- cross-domain analytics
- anomaly detection
- root-cause analysis

---

## Database Architecture

DataPulse separates database responsibilities into layers:

```text
raw
    ↓
staging
    ↓
analytics

metadata
```

### Raw

The `raw` layer represents source data as received.

Responsibilities:

- preserve source values
- preserve problematic records
- retain duplicates
- retain invalid values
- retain missing values
- support traceability back to source data

The raw layer does not perform business transformations.

### Staging

The `staging` layer will standardize source data.

Planned responsibilities:

- data-type conversion
- normalization
- source-specific cleanup
- standardization
- preparation for downstream models

### Analytics

The `analytics` layer will contain business-oriented models.

Planned responsibilities:

- business metrics
- reporting datasets
- facts and dimensions
- anomaly-detection inputs
- root-cause-analysis inputs
- API-facing datasets

### Metadata

The `metadata` layer contains operational platform information.

Examples:

- ingestion runs
- source files
- processing status
- row counts
- execution metadata

---

## Raw Ingestion Architecture

The current single-source ingestion workflow is:

```text
Source CSV
    ↓
Ingestion Run
    ↓
Ingestion Source
    ↓
CSV Reader
    ↓
Schema Validation
    ↓
Raw Database Loader
    ↓
Transactional Commit
    ↓
Metadata SUCCESS
```

Failure paths are recorded explicitly:

```text
Failure
   ↓
Source FAILED
   ↓
Run FAILED
```

The orchestration layer coordinates ingestion but does not perform business transformations.

---

## Ingestion Metadata

Each ingestion operation records operational metadata.

Run lifecycle:

```text
RUNNING
   ├──→ SUCCESS
   └──→ FAILED
```

Source lifecycle:

```text
PENDING
   ├──→ SUCCESS
   └──→ FAILED
```

Metadata records include information such as:

- ingestion run identifier
- ingestion source identifier
- source name
- source file
- source file path
- start time
- finish time
- status
- rows read
- rows loaded
- error information

This allows the platform to determine what happened during ingestion rather than only whether data exists.

---

## Transaction Handling

Raw database loading is transactional.

For batched ingestion:

```text
Batch 1
   ↓
Batch 2
   ↓
Batch 3
   ↓
Commit
```

If a later batch fails:

```text
Batch 1
   ↓
Batch 2
   ↓
Batch 3 FAILED
   ↓
ROLLBACK
```

Previously inserted batches from that raw-load operation are rolled back.

This prevents partially committed raw ingestion.

The rollback behavior was validated against the real PostgreSQL Docker environment.

---

## Data Quality Philosophy

DataPulse intentionally does not treat raw source data as clean.

The platform follows:

```text
Capture first
     ↓
Validate
     ↓
Transform
     ↓
Measure quality
     ↓
Analyze
```

The generated sources intentionally contain problems such as:

- missing values
- duplicate records
- invalid categorical values
- invalid dates
- invalid numeric values
- broken references
- temporal inconsistencies
- schema drift
- unexpected record volumes
- freshness problems

The raw layer preserves these problems so downstream layers can detect and explain them.

---

## Technology Stack

### Implemented

Currently implemented and validated:

- Python 3.12
- PostgreSQL 17
- SQL
- SQLAlchemy
- psycopg
- Pandas
- pytest
- Ruff
- Docker
- Docker Compose
- Git
- GitHub

### Planned

Planned for later phases:

- dbt
- data-quality framework
- business analytics models
- statistical anomaly detection
- root-cause analysis
- FastAPI
- React
- TypeScript
- AI/LLM-assisted explanations
- advanced ML models
- CI/CD
- cloud deployment
- monitoring and observability

Technologies will only be introduced when they solve a genuine project requirement.

The project intentionally avoids unnecessary Kafka, Spark, Kubernetes, Terraform, or microservices unless a real requirement emerges.

---

## Planned Analytics

The analytics layer will cover multiple business domains.

### Revenue

- revenue trends
- payment amounts
- refunds
- revenue by product
- revenue by customer
- revenue by acquisition channel

### Customer

- customer acquisition
- customer activity
- customer status
- customer segmentation
- customer behaviour

### Product

- product performance
- product sales
- product activity
- product-level anomalies

### Subscription

- subscription lifecycle
- active subscriptions
- cancellations
- renewals
- subscription revenue

### Payments

- payment success/failure
- payment trends
- payment anomalies
- payment relationships with orders

### Support

- ticket volume
- ticket status
- resolution times
- support trends
- customer-support relationships

### Web Events

- event volume
- customer activity
- product interactions
- traffic patterns
- behavioural anomalies

---

## Planned Anomaly Detection

Anomaly detection will initially use transparent statistical methods before advanced machine-learning approaches.

Planned progression:

```text
Historical data
      ↓
Statistical baseline
      ↓
Rolling metrics
      ↓
Thresholds / z-scores
      ↓
Severity
      ↓
Anomaly results
```

The initial objective is reliability and explainability.

Advanced ML approaches will only be introduced after deterministic anomaly detection has been validated.

---

## Planned Root Cause Analysis

Anomaly detection answers:

> What looks unusual?

Root-cause analysis will investigate:

> What dimensions or upstream factors appear to explain the anomaly?

Planned workflow:

```text
Detected anomaly
      ↓
Break down by dimensions
      ↓
Compare segments
      ↓
Inspect upstream data
      ↓
Correlate related metrics
      ↓
Rank likely contributors
      ↓
Produce explanation
```

The RCA layer will distinguish correlation from confirmed causation.

---

## Planned API

The backend API will use FastAPI.

Planned areas include:

```text
/health
/analytics
/data-quality
/anomalies
/root-cause
```

The API will expose trusted outputs from the analytics and monitoring layers.

Core business transformations will remain in the data platform rather than being hidden inside API handlers.

---

## Planned Dashboard

The frontend will use:

- React
- TypeScript

Planned dashboard areas:

- overall platform health
- business KPIs
- data-quality status
- anomaly monitoring
- root-cause analysis
- ingestion status

The frontend will consume backend APIs rather than directly accessing PostgreSQL.

---

## Planned AI-Assisted Explanations

AI will be introduced only after the deterministic data-quality, analytics, anomaly-detection, and RCA layers are trusted.

The intended flow is:

```text
Trusted deterministic facts
        ↓
Structured context
        ↓
LLM
        ↓
Human-readable explanation
```

The LLM will not calculate the underlying metrics.

The model will receive verified facts and will be constrained to those facts.

The objective is practical AI engineering rather than using an LLM where SQL or Python is more reliable.

---

## Planned ML Engineering

Later ML work may include:

- advanced anomaly detection
- feature engineering
- model evaluation
- model comparison
- model management
- model monitoring
- drift detection

Statistical baselines will remain important even after advanced models are introduced because they provide interpretable reference points.

---

## Repository Structure

The current repository structure is:

```text
datapulse/
├── docs/
│   ├── database-naming-conventions.md
│   ├── ingestion-orchestration-contract.md
│   ├── phase-2-completion.md
│   ├── phase-3-1-postgresql-foundation.md
│   └── phase-3-completion.md
├── scripts/
├── sql/
│   └── migrations/
├── src/
│   └── datapulse/
│       ├── data_generation/
│       │   ├── config.py
│       │   ├── manifest.py
│       │   ├── materialization.py
│       │   ├── pipeline.py
│       │   ├── schema_drift.py
│       │   ├── schema_drift_config.py
│       │   └── ...
│       ├── csv_validation.py
│       ├── database.py
│       ├── db_loader.py
│       ├── file_reader.py
│       ├── ingestion_contract.py
│       ├── ingestion_metadata.py
│       ├── ingestion_orchestrator.py
│       ├── settings.py
│       └── ...
├── tests/
│   ├── fixtures/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

The repository structure will evolve as new platform layers are implemented.

---

## Database Migrations

Database changes are managed through ordered SQL migrations.

Current migrations include:

```text
sql/migrations/
├── 001_create_raw_schema.sql
├── 002_create_metadata_schema.sql
├── 003_create_raw_customers_table.sql
├── 004_create_raw_products_table.sql
├── 005_create_raw_orders_table.sql
├── 006_create_raw_payments_table.sql
├── 007_create_raw_subscriptions_table.sql
├── 008_create_raw_support_tickets_table.sql
├── 009_create_raw_web_events_table.sql
├── 010_create_ingestion_runs_table.sql
├── 011_create_ingestion_sources_table.sql
└── 012_add_ingestion_source_row_counts.sql
```

Migration naming follows the project's database naming conventions.

---

## Database Naming Conventions

DataPulse uses consistent PostgreSQL naming conventions.

Core principles:

- lowercase `snake_case`
- plural table names
- `<entity>_id` identifiers
- descriptive foreign keys
- `is_`, `has_`, or `can_` prefixes for boolean columns
- `_date` for calendar dates
- `_at` for timestamps
- explicit names for amounts and counts
- predictable constraint names
- predictable index names
- ordered migration filenames

Layer responsibilities:

```text
raw
    ↓
source-faithful

staging
    ↓
standardized

analytics
    ↓
business-oriented

metadata
    ↓
operational
```

Detailed conventions are documented in:

```text
docs/database-naming-conventions.md
```

---

## Testing Strategy

Testing is performed throughout development rather than postponed until the end.

The project uses:

- pytest
- unit tests
- integration tests
- database integration tests
- ingestion tests
- rollback tests
- regression tests
- data-generation validation
- source-schema validation

The testing strategy will expand as new platform layers are introduced.

---

## Current Validation Status

The completed Phase 3 implementation was validated with:

```text
242 passed in 5.52s
```

Formatting:

```text
ruff format --check src tests
60 files already formatted
```

Linting:

```text
ruff check src tests
All checks passed!
```

Additional validation included:

- Docker Compose PostgreSQL health
- PostgreSQL connectivity
- PostgreSQL version validation
- database creation
- application connectivity
- real PostgreSQL ingestion
- successful ingestion path
- source-schema failure path
- database failure path
- transaction rollback
- ingestion metadata validation
- row-count validation
- error-message validation
- `git diff --check`

GitHub Actions CI checks are not currently configured, so no CI result is claimed.

---

## Development Workflow

DataPulse is developed as a real software project rather than as one large implementation.

Each meaningful milestone follows:

1. Define the problem.
2. Design the solution.
3. Implement a focused feature.
4. Add appropriate tests.
5. Run validation.
6. Inspect the results.
7. Update documentation.
8. Commit the work.
9. Push the feature branch.
10. Review the repository state.
11. Only then move to the next milestone.

---

## Phase Completion Governance

A phase is not considered complete simply because work on the next phase has started.

The required completion gate is:

```text
Implementation
      ↓
Tests
      ↓
Validation
      ↓
Formatting / Linting
      ↓
Integration Validation
      ↓
Documentation
      ↓
Clean Working Tree
      ↓
Completion Commit
      ↓
Phase Closed
```

A phase must satisfy all applicable completion requirements before the next phase officially becomes active.

---

## Roadmap

### Phase 0 — Planning

- [x] Project definition
- [x] System scope
- [x] Technology decisions
- [x] Architecture

### Phase 1 — Repository & Development Foundation

- [x] Repository foundation
- [x] Python environment
- [x] Code quality
- [x] Testing foundation
- [x] Documentation foundation

### Phase 2 — Synthetic Source Systems

- [x] Source-system design
- [x] Synthetic data generators
- [x] Data-quality issue injection
- [x] Source materialization
- [x] Source manifests
- [x] Schema drift
- [x] Source validation
- [x] Phase completion validation

### Phase 3 — PostgreSQL & Raw Ingestion

- [x] PostgreSQL foundation
- [x] Database schemas
- [x] Raw source tables
- [x] Ingestion framework
- [x] Ingestion metadata
- [x] Ingestion orchestration
- [x] PostgreSQL integration tests
- [x] Rollback validation
- [x] Phase completion validation

### Phase 4 — Warehouse Data Modelling

- [ ] Warehouse architecture
- [ ] Staging models
- [ ] Dimension models
- [ ] Fact models
- [ ] Keys and relationships
- [ ] Model validation
- [ ] Performance considerations

### Phase 5 — ELT & dbt Transformations

- [ ] dbt foundation
- [ ] Staging transformations
- [ ] Intermediate transformations
- [ ] Analytics models
- [ ] dbt tests
- [ ] dbt documentation

### Phase 6 — Data Quality Framework

- [ ] Data-quality architecture
- [ ] Completeness checks
- [ ] Uniqueness checks
- [ ] Validity checks
- [ ] Referential-integrity checks
- [ ] Consistency checks
- [ ] Freshness checks
- [ ] Volume checks
- [ ] Data-quality result storage
- [ ] Data-quality reporting

### Phase 7 — Automated Testing

- [ ] Unit testing expansion
- [ ] Integration testing expansion
- [ ] Data testing
- [ ] Regression testing
- [ ] Infrastructure testing
- [ ] Test reporting

### Phase 8 — Business Analytics

- [ ] Revenue analytics
- [ ] Customer analytics
- [ ] Product analytics
- [ ] Subscription analytics
- [ ] Payment analytics
- [ ] Support analytics
- [ ] Web analytics
- [ ] Cross-domain analytics

### Phase 9 — Anomaly Detection

- [ ] Anomaly-detection architecture
- [ ] Statistical baselines
- [ ] Rolling metrics
- [ ] Z-score detection
- [ ] Threshold detection
- [ ] Severity classification
- [ ] Anomaly result storage
- [ ] Validation

### Phase 10 — Root Cause Analysis

- [ ] RCA foundation
- [ ] Dimension analysis
- [ ] Upstream analysis
- [ ] Business correlation
- [ ] Contributor ranking
- [ ] Explainability

### Phase 11 — FastAPI Analytics API

- [ ] API foundation
- [ ] Health endpoint
- [ ] Analytics endpoints
- [ ] Data-quality API
- [ ] Anomaly API
- [ ] RCA API
- [ ] API testing
- [ ] API quality controls

### Phase 12 — React/TypeScript Dashboard

- [ ] Frontend foundation
- [ ] Main dashboard
- [ ] Analytics views
- [ ] Data-quality UI
- [ ] Anomaly UI
- [ ] RCA UI
- [ ] UX improvements

### Phase 13 — AI-Assisted Explanations

- [ ] AI architecture
- [ ] Context construction
- [ ] LLM explanation
- [ ] Guardrails
- [ ] API/dashboard integration

### Phase 14 — ML Engineering Improvements

- [ ] Evaluation framework
- [ ] Advanced anomaly models
- [ ] Feature engineering
- [ ] Model management
- [ ] ML monitoring

### Phase 15 — Docker & Production Hardening

- [ ] Containerization improvements
- [ ] Docker Compose production configuration
- [ ] Production configuration
- [ ] Performance improvements
- [ ] Security hardening

### Phase 16 — CI/CD

- [ ] CI foundation
- [ ] Quality checks in CI
- [ ] Automated tests in CI
- [ ] Build pipeline
- [ ] Deployment pipeline
- [ ] Git workflow automation

GitHub Actions is intentionally not being introduced before this phase.

### Phase 17 — Cloud Deployment

- [ ] Cloud architecture
- [ ] Cloud PostgreSQL
- [ ] Backend deployment
- [ ] Frontend deployment
- [ ] Deployment pipeline
- [ ] Cost controls

### Phase 18 — Monitoring & Observability

- [ ] Application logging
- [ ] Pipeline monitoring
- [ ] Data monitoring
- [ ] API monitoring
- [ ] Anomaly monitoring
- [ ] Alerting

### Phase 19 — Documentation & Portfolio

- [ ] Technical documentation
- [ ] Architecture diagrams
- [ ] Developer documentation
- [ ] Portfolio presentation
- [ ] Engineering decision records

### Phase 20 — Interview & CV Preparation

- [ ] Project story
- [ ] Data Engineering preparation
- [ ] Data Science preparation
- [ ] Software Engineering preparation
- [ ] Cloud preparation
- [ ] AI preparation
- [ ] Resume updates
- [ ] Portfolio updates
- [ ] Mock interviews

---

## Development Requirements

Python 3.12 is required.

Create and activate the virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project and development dependencies:

```powershell
pip install -e ".[dev]"
```

Run tests:

```powershell
pytest
```

Run linting:

```powershell
ruff check src tests
```

Check formatting:

```powershell
ruff format --check src tests
```

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Check the PostgreSQL service:

```powershell
docker compose ps
```

---

## Git Workflow

The project uses a feature-branch workflow.

Examples:

```text
feature/data-ingestion
feature/warehouse-model
feature/elt-dbt
feature/data-quality
feature/anomaly-detection
feature/root-cause-analysis
feature/analytics-api
feature/frontend-dashboard
feature/ci-cd
```

Bug fixes, refactoring, and documentation use appropriate prefixes:

```text
fix/
refactor/
docs/
```

Commit history should remain chronological and represent actual development work.

---

## Documentation

Important project documentation includes:

- `docs/database-naming-conventions.md`
- `docs/ingestion-orchestration-contract.md`
- `docs/phase-2-completion.md`
- `docs/phase-3-1-postgresql-foundation.md`
- `docs/phase-3-completion.md`

Historical phase-completion records are retained as project evidence and should not be rewritten merely because later phases have started.

---

## License

License and data-usage details will be finalized as the project and its data sources are established.
