# DataPulse

Self-monitoring data and analytics platform.

DataPulse is a production-style portfolio project demonstrating an end-to-end data platform workflow:

**source ingestion → data modelling → ELT → data quality → analytics → anomaly detection → root-cause analysis → API → dashboard → deployment**

The project is being developed incrementally with production-oriented engineering practices, automated testing, documentation, and a realistic Git workflow.

---

## Project Goal

DataPulse is designed to demonstrate practical skills across:

* Data Engineering
* Data Analytics and BI
* Analytics Engineering
* Applied Data Science
* AI/Data Applications
* Data Quality and Data Platforms

The platform will use realistic synthetic business data from multiple source systems and intentionally introduce data-quality problems that the platform must detect and report.

---

## Current Status

**Phase 1 — Repository & Development Environment: Complete**

**Current phase: Phase 2 — Synthetic Source Systems**

### Completed

* Python 3.12 development environment
* Project package structure
* Environment configuration
* `.env.example`
* Git configuration and repository structure
* Docker and Docker Compose foundation
* Initial application health check
* Unit testing with pytest
* Code quality checks with Ruff
* Initial project documentation
* Git feature-branch workflow

### Validation

The Phase 1 foundation currently passes:

* `pytest`
* `ruff check .`
* `ruff format --check .`
* `git diff --cached --check`

Docker has been prepared in the project configuration but has not yet been validated locally because Docker is not currently installed in the development environment.

---

## Planned Architecture

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
 Deployment & Monitoring
```

The architecture will be implemented incrementally rather than built all at once.

---

## Technology Stack

### Core

* Python 3.12
* PostgreSQL
* SQL
* dbt
* Pandas where appropriate
* scikit-learn

### Application

* FastAPI
* React
* TypeScript

### Engineering

* pytest
* Ruff
* Docker
* Git
* GitHub
* GitHub Actions

### Cloud

* AWS, using free-tier resources where practical

Additional technologies will only be introduced when they solve a genuine project requirement.

---

## Repository Structure

```text
datapulse/
├── config/
├── data/
│   ├── generated/
│   └── sample/
├── docs/
│   ├── architecture/
│   └── decisions/
├── scripts/
├── src/
│   └── datapulse/
├── tests/
│   ├── data/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

The repository structure will evolve as new platform components are implemented.

---

## Development Approach

DataPulse is being developed as a real software project rather than as a single large implementation.

Each meaningful milestone follows this general workflow:

1. Define the problem and design.
2. Implement a focused feature.
3. Add appropriate tests.
4. Run validation and inspect the results.
5. Update documentation.
6. Commit the work with a meaningful commit message.
7. Push the feature branch.
8. Review the changes before moving to the next milestone.

The README is maintained as **living documentation** and will be updated as the project progresses.

---

## Roadmap

* [x] Phase 0 — Project planning and architecture
* [x] Phase 1 — Repository and development environment
* [ ] Phase 2 — Synthetic source systems
* [ ] Phase 3 — PostgreSQL and raw ingestion
* [ ] Phase 4 — Warehouse data modelling
* [ ] Phase 5 — ELT and dbt transformations
* [ ] Phase 6 — Data quality framework
* [ ] Phase 7 — Automated testing
* [ ] Phase 8 — Business analytics
* [ ] Phase 9 — Anomaly detection
* [ ] Phase 10 — Root cause analysis
* [ ] Phase 11 — FastAPI analytics API
* [ ] Phase 12 — React/TypeScript dashboard
* [ ] Phase 13 — AI-assisted explanations
* [ ] Phase 14 — ML engineering improvements
* [ ] Phase 15 — Docker and production hardening
* [ ] Phase 16 — CI/CD
* [ ] Phase 17 — Cloud deployment
* [ ] Phase 18 — Monitoring and observability
* [ ] Phase 19 — Documentation and portfolio
* [ ] Phase 20 — Interview and CV preparation

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
ruff check .
```

Check formatting:

```powershell
ruff format --check .
```

---

## Git Workflow

The project uses a feature-branch workflow.

Examples:

```text
feature/synthetic-source-systems
feature/data-ingestion
feature/warehouse-model
feature/data-quality-engine
feature/anomaly-detection
feature/root-cause-analysis
feature/analytics-api
feature/frontend-dashboard
feature/ci-cd
```

Bug fixes, refactoring, and documentation use appropriate branch prefixes such as:

```text
fix/
refactor/
docs/
```

Commit history will remain chronological and will represent actual development work.

---

## License

License and data-usage details will be finalized as the project and its data sources are established.
