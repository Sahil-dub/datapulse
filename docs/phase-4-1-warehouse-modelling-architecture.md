# Phase 4.1 — Warehouse Modelling Architecture

## Status

**Milestone:** 4H.1 — Warehouse Modelling Architecture  
**Status:** Design approved for implementation  
**Phase:** 4 — Warehouse Data Modelling

This document defines the architectural contract for the DataPulse warehouse layer before physical warehouse tables are implemented.

## 1. Architecture

DataPulse separates data responsibilities into five database schemas:

```text
raw
  ↓
staging
  ↓
warehouse
  ↓
analytics

metadata
```

### raw

Source-faithful ingestion layer.

Responsibilities:
- preserve source values and source structure
- retain duplicates and problematic records
- preserve invalid values for downstream diagnosis
- provide traceability back to ingestion

Raw ingestion must not prematurely apply business transformations.

### staging

Technical standardization layer.

Responsibilities:
- convert source text values into appropriate PostgreSQL types
- standardize representations
- normalize source-specific technical differences
- expose parsing/conversion failures
- prepare records for canonical warehouse modelling

Staging must preserve enough source identity to trace records back to raw.

### warehouse

Canonical business model.

Responsibilities:
- represent trusted business entities
- represent business processes at explicit grain
- provide stable relationships between facts and dimensions
- provide a consistent foundation for analytics, anomaly detection, RCA, and APIs

### analytics

Business-facing analytical layer.

Responsibilities:
- KPIs
- business metrics
- analytical marts
- cross-domain metrics
- downstream application-oriented views/models

### metadata

Platform-operational layer.

Responsibilities:
- ingestion runs
- source files
- processing status
- row counts
- pipeline execution metadata

## 2. Core Warehouse Model

The initial warehouse contains:

### Dimensions

- `dim_customer`
- `dim_product`
- `dim_date`

### Facts

- `fact_order`
- `fact_payment`
- `fact_subscription`
- `fact_support_ticket`
- `fact_web_event`

The model intentionally avoids a single denormalized customer-360 table as the primary warehouse structure.

## 3. Grain

Every fact table must have an explicit grain.

| Model | Grain |
|---|---|
| `fact_order` | One source order |
| `fact_payment` | One source payment transaction |
| `fact_subscription` | One source subscription record |
| `fact_support_ticket` | One source support ticket |
| `fact_web_event` | One source web event |

A fact model must not mix multiple grains.

## 4. Dimensions

### dim_customer

Canonical customer entity.

Expected business attributes include:
- customer_id
- first_name
- last_name
- email
- country
- signup_date
- customer_status
- acquisition_channel

The warehouse will use a surrogate `customer_key` while retaining `customer_id` as the source/business identifier.

### dim_product

Canonical product entity.

Expected attributes include:
- product_id
- product_name
- category
- unit_price
- product_status
- created_date

The warehouse will use a surrogate `product_key` while retaining `product_id` as the source/business identifier.

### dim_date

Canonical calendar dimension.

Initial attributes:
- date_key
- full_date
- year
- quarter
- month
- month_name
- week
- day_of_week
- day_name
- is_weekend

The date dimension will support consistent time-based analytics and anomaly analysis.

## 5. Fact Models

### fact_order

Grain: one order.

Expected measures/attributes:
- quantity
- unit_price
- discount_amount
- shipping_amount
- order_total
- order_status
- sales_channel

Relationships:
- customer
- product
- order date

### fact_payment

Grain: one payment transaction.

Expected measures/attributes:
- payment_amount
- payment_method
- payment_status
- transaction_reference
- currency
- source_updated_at

Relationship:
- order
- payment date

### fact_subscription

Grain: one source subscription record.

Expected attributes/measures:
- plan_type
- subscription_status
- billing_frequency
- start_date
- end_date
- monthly_fee
- auto_renew
- source_updated_at

Subscription intervals will remain explicit. We will not explode subscriptions into daily rows unless a later analytical requirement demonstrates that this is necessary.

### fact_support_ticket

Grain: one support ticket.

Expected attributes/measures:
- ticket_created_at
- ticket_updated_at
- ticket_category
- priority
- ticket_status
- resolution_channel
- assigned_team
- resolution_time_hours
- customer_satisfaction_score

Relationship:
- customer
- created/updated dates as appropriate

### fact_web_event

Grain: one web event.

Expected attributes/measures:
- event_timestamp
- source_received_at
- session_id
- event_type
- page_type
- device_type
- traffic_source
- revenue_amount

Potential relationships:
- customer
- product
- order

Customer/product/order relationships may be nullable because anonymous or non-commerce web events are valid events.

## 6. Keys

Warehouse dimensions will use surrogate keys:

```text
customer_key
product_key
date_key
```

Source/business identifiers remain available:

```text
customer_id
product_id
order_id
payment_id
subscription_id
ticket_id
event_id
```

Surrogate keys provide separation between source identity and warehouse identity and leave room for future historical dimension handling.

Full SCD Type 2 implementation is not part of 4H.1. It will only be introduced where source semantics and an analytical requirement justify it.

## 7. Data Quality and Invalid Records

The warehouse must not erase evidence of source problems.

Example:

```text
raw.orders
  quantity = "INVALID"
       ↓
staging.orders
  quantity = NULL
  parse/quality indicator = true
       ↓
DQ result
  invalid quantity detected
```

Similarly, a broken customer reference must not create a fabricated customer dimension record.

Where a fact record remains analytically usable, the fact may retain the source identifier while the warehouse dimension key is nullable and the data-quality layer records the broken relationship.

The exact inclusion/exclusion rules for individual invalid records will be defined in later staging and data-quality milestones.

## 8. Referential Relationships

The conceptual relationships are:

```text
dim_customer
    │
    ├── fact_order
    ├── fact_subscription
    ├── fact_support_ticket
    └── fact_web_event

dim_product
    │
    ├── fact_order
    └── fact_web_event

fact_order
    └── fact_payment

dim_date
    ├── fact_order
    ├── fact_payment
    ├── fact_subscription
    ├── fact_support_ticket
    └── fact_web_event
```

The physical implementation may use nullable foreign keys where source relationships are optional or invalid.

## 9. Layer Boundary Rules

### Raw → staging

Technical transformation only.

Examples:
- text → date
- text → integer
- text → numeric
- text → boolean
- timestamp normalization

### Staging → warehouse

Canonical business modelling.

Examples:
- entity deduplication rules
- canonical customer/product records
- surrogate key assignment
- fact construction
- relationship resolution

### Warehouse → analytics

Business logic and analytical derivations.

Examples:
- revenue KPIs
- customer metrics
- product performance
- subscription metrics
- support metrics
- web conversion metrics
- cross-domain analytical models

## 10. Performance Principles

Indexes will not be added indiscriminately.

They should be justified by:
- demonstrated query patterns
- primary/unique constraints
- foreign-key relationships
- time-based access patterns
- later API/analytics requirements

High-volume `fact_web_event` will receive particular attention during the physical design and performance milestone.

## 11. Constraints

The raw layer remains intentionally permissive.

Warehouse constraints should enforce canonical model integrity where the data has passed the appropriate staging and quality rules.

Expected warehouse constraints include:
- primary keys
- appropriate uniqueness constraints
- foreign keys where relationships are valid and reliable
- non-null constraints for mandatory canonical attributes
- appropriate checks for canonical values

The exact constraints belong to the physical modelling milestones rather than this architecture milestone.

## 12. dbt Compatibility

The physical warehouse design must remain compatible with the planned Phase 5 dbt implementation.

The intended progression is:

```text
raw tables
  ↓
dbt staging models
  ↓
dbt intermediate models
  ↓
warehouse dimensions/facts
  ↓
analytics models
```

Phase 4 establishes the relational model. Phase 5 will establish the dbt transformation implementation and dbt-specific testing/documentation.

## 13. Design Principles

1. Preserve raw evidence.
2. Give every fact a single explicit grain.
3. Separate technical standardization from business modelling.
4. Use dimensions for reusable business entities.
5. Use facts for business processes/events.
6. Preserve source/business identifiers.
7. Use warehouse surrogate keys for dimensions.
8. Do not fabricate relationships for invalid source references.
9. Keep anonymous web events valid where the source semantics permit them.
10. Keep analytics models separate from the canonical warehouse.
11. Avoid unnecessary complexity such as universal SCD Type 2.
12. Design for later data-quality, anomaly-detection, RCA, API, and dashboard requirements.

## 14. Out of Scope for 4H.1

The following are intentionally deferred:
- physical warehouse migrations
- staging SQL implementation
- dimension/fact SQL implementation
- indexes and query tuning
- dbt project implementation
- detailed DQ rules
- anomaly detection
- RCA
- API models

Those belong to later Phase 4/5 milestones.

## 15. Next Milestone

**4H.2 — Staging Models**

The next implementation step is to define the staging-layer contracts and physical models for the seven source domains before creating the canonical dimensions and facts.
