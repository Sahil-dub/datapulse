# Phase 4.2.1 — Staging Architecture & Contract

## Status
**Milestone:** 4H.2.1 — Staging Architecture & Contract
**Status:** Design approved for implementation
**Phase:** 4 — Warehouse Data Modelling

This document defines the staging-layer contract between the source-faithful raw layer and the canonical warehouse model.

## 1. Staging Responsibilities

Staging performs technical standardization, not business analytics.

Staging must:
- read from the corresponding raw table
- preserve raw_record_id
- convert source text values to appropriate PostgreSQL types
- normalize technical representations
- expose parsing/conversion failures
- retain source/business identifiers
- preserve raw-to-staging traceability
- avoid silently deleting source records

Staging must not:
- calculate business KPIs
- assign warehouse surrogate dimension keys
- fabricate missing relationships
- hide invalid source values
- perform broad business aggregation
- replace the raw layer

## 2. Staging Tables

| Raw source | Staging model |
|---|---|
| raw.customers | staging.customers |
| raw.products | staging.products |
| raw.orders | staging.orders |
| raw.payments | staging.payments |
| raw.subscriptions | staging.subscriptions |
| raw.support_tickets | staging.support_tickets |
| raw.web_events | staging.web_events |

The initial staging layer remains one-to-one with raw records.

## 3. Traceability

Every staging record must retain raw_record_id.

source file → raw_record_id → staging record → warehouse record → analytics result

Where a warehouse record is derived from multiple staging records, the warehouse implementation must preserve an appropriate source relationship.

## 4. Type Conversion Contract

Raw business fields are currently stored as TEXT. Staging converts them into semantic PostgreSQL types.

### Identifiers
Business identifiers remain TEXT. Examples: customer_id, product_id, order_id, payment_id, subscription_id, ticket_id, event_id, session_id, transaction_reference.

Identifiers must not be converted to integers merely because they contain digits.

### Dates
Date-only fields become DATE: signup_date, created_date, order_date, payment_date, start_date, end_date.

### Timestamps
Timestamp-bearing fields become TIMESTAMPTZ where the source represents an instant: source_updated_at, ticket_created_at, ticket_updated_at, event_timestamp, source_received_at.

### Integers
Count/quantity fields with integral semantics become INTEGER. Initial candidate: quantity.

### Numeric
Financial and measured decimal values become NUMERIC. Initial candidates: unit_price, discount_amount, shipping_amount, order_total, payment_amount, monthly_fee, resolution_time_hours, customer_satisfaction_score, revenue_amount.

Precision and scale will be selected during physical implementation.

### Boolean
Boolean-like values become BOOLEAN. Initial candidate: auto_renew. Accepted source representations must be explicitly defined rather than relying on implicit casts.

## 5. Invalid Value Handling

Invalid source values must not cause silent data loss.

Example:

raw.orders.quantity = INVALID
→ staging.orders.quantity = NULL
→ staging quality indicator = false/invalid
→ DQ layer reports the problem

The implementation must distinguish:
1. valid value
2. missing/null source value
3. non-null value that failed conversion

This distinction is required for later data-quality reporting.

## 6. Quality Indicators

Where a source column requires parsing, the staging model should expose a corresponding quality indicator when conversion can fail.

Examples: quantity_parse_valid, order_date_parse_valid, payment_amount_parse_valid.

A valid source NULL is not automatically a parse error. Indicators should be added where they materially improve diagnosis rather than for every column indiscriminately.

## 7. String Standardization

Staging performs technical normalization only.

Allowed examples include trimming accidental surrounding whitespace and converting empty strings to NULL where the source semantics treat empty as missing.

Staging must not silently perform business-specific category mapping. Business semantics belong in later modelling or DQ logic.

## 8. Duplicate Strategy

Duplicates are intentionally present in DataPulse source data.

The staging layer must not use DISTINCT as a generic cleanup mechanism.

Instead:
- every raw record remains traceable into staging
- duplicate business identifiers remain observable
- duplicate detection is a data-quality concern
- canonical deduplication belongs at the staging-to-warehouse boundary when the business model requires one canonical entity

This preserves evidence needed for Phase 6.

## 9. Referential Integrity

Staging does not fabricate missing parent records.

For example, an order may retain a customer_id that does not exist in the customer source. The staging record remains representable, while referential integrity is evaluated as a separate quality/model concern.

## 10. Schema Drift

The source pipeline supports intentional schema-drift scenarios.

Staging must fail clearly when a raw source structure is incompatible with the expected staging contract. It must not silently reinterpret a renamed or missing column.

Schema-drift handling must remain observable and tested.

## 11. Source-Specific Contract

### customers
- signup_date → DATE
- all other fields remain TEXT/business identifiers or attributes

### products
- unit_price → NUMERIC
- created_date → DATE
- identifiers and descriptive attributes remain TEXT

### orders
- order_date → DATE
- quantity → INTEGER
- unit_price → NUMERIC
- discount_amount → NUMERIC
- shipping_amount → NUMERIC
- order_total → NUMERIC
- identifiers/status/channel remain TEXT

### payments
- payment_date → DATE
- payment_amount → NUMERIC
- source_updated_at → TIMESTAMPTZ
- identifiers/status/method/currency/reference remain TEXT

### subscriptions
- start_date → DATE
- end_date → DATE
- monthly_fee → NUMERIC
- auto_renew → BOOLEAN
- source_updated_at → TIMESTAMPTZ
- identifiers/status/plan/frequency remain TEXT

### support_tickets
- ticket_created_at → TIMESTAMPTZ
- ticket_updated_at → TIMESTAMPTZ
- resolution_time_hours → NUMERIC
- customer_satisfaction_score → NUMERIC
- identifiers/category/priority/status/channel/team remain TEXT

### web_events
- event_timestamp → TIMESTAMPTZ
- source_received_at → TIMESTAMPTZ
- revenue_amount → NUMERIC
- identifiers/session/category fields remain TEXT

## 12. Staging-to-Warehouse Boundary

Staging answers: Can this source value be technically represented in a reliable PostgreSQL type?

Warehouse modelling answers: What canonical business entity or event should this record represent?

raw → staging: technical typing, normalization, parsing visibility
staging → warehouse: business identity, deduplication, surrogate keys, relationships, canonical grain

This boundary must remain explicit.

## 13. Testing Contract

Each staging model must eventually test:
- expected columns
- expected PostgreSQL data types
- valid conversion
- missing/null values
- invalid conversion
- preservation of raw_record_id
- duplicate preservation
- source identifier preservation
- representative schema-drift failure
- representative referential-integrity problem

Tests must prove that bad source data remains observable rather than silently disappearing.

## 14. Implementation Order

1. customers
2. products
3. orders
4. payments
5. subscriptions
6. support_tickets
7. web_events

This order follows the major source relationships while keeping each staging model independently testable.

## 15. Out of Scope

- physical staging migrations
- warehouse dimensions
- warehouse facts
- surrogate key assignment
- final deduplication
- business KPI calculations
- dbt implementation
- comprehensive DQ framework
- anomaly detection
- RCA

## 16. Next Milestone

**4H.2.2 — Customer Staging**

The next implementation will create the physical staging.customers model and its tests, validate type conversion and invalid-value handling, and preserve raw-to-staging traceability.