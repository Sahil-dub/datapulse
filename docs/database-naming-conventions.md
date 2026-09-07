# DataPulse Database Naming Conventions

## Purpose

This document defines the naming conventions for DataPulse PostgreSQL database objects.

The goal is to keep database objects consistent, readable, predictable, and easy to work with across the raw, staging, analytics, and metadata layers.

These conventions apply to database schemas, tables, columns, keys, constraints, indexes, and migration files.

---

## 1. General Naming Rules

* Use lowercase `snake_case` for database object names.
* Use descriptive names rather than ambiguous abbreviations.
* Avoid PostgreSQL reserved words.
* Prefer consistent terminology across all layers.
* Use singular concepts for identifiers and plural names for tables.
* Do not encode data types into column names.
* Names should describe the business or technical meaning of the object.

Examples:

```text
customer_id
order_date
payment_status
created_at
is_active
```

Avoid:

```text
CustomerID
customerId
cust_id
orderDate
active_flag
```

---

## 2. Schema Naming

Schemas use lowercase `snake_case`.

Current DataPulse schemas:

```text
raw
metadata
```

Planned downstream schemas include:

```text
staging
analytics
```

Schema names should represent the responsibility of the layer rather than a specific application component.

---

## 3. Table Naming

Tables use lowercase plural `snake_case`.

Examples:

```text
customers
products
orders
payments
subscriptions
support_tickets
web_events
```

Use plural table names because each table represents a collection of records.

Avoid:

```text
Customer
customer
customer_table
tbl_customers
```

Do not add technical prefixes such as `tbl_` unless a future external system requires them.

---

## 4. Column Naming

Columns use lowercase `snake_case`.

Examples:

```text
customer_id
first_name
email
signup_date
created_at
updated_at
payment_status
```

Column names should be explicit enough to understand without relying on undocumented abbreviations.

Prefer:

```text
customer_id
```

over:

```text
cust_id
```

Prefer:

```text
transaction_amount
```

over:

```text
amt
```

---

## 5. Primary Keys

Primary-key columns use:

```text
<entity>_id
```

Examples:

```text
customer_id
product_id
order_id
payment_id
subscription_id
ticket_id
event_id
```

Primary-key constraint names use:

```text
pk_<table>
```

Examples:

```text
pk_customers
pk_orders
pk_payments
```

---

## 6. Foreign Keys

Foreign-key columns use the referenced entity's identifier:

```text
<referenced_entity>_id
```

Examples:

```text
customer_id
product_id
order_id
subscription_id
```

Foreign-key constraint names use:

```text
fk_<table>_<referenced_table>
```

Example:

```text
fk_orders_customers
```

If a table contains multiple relationships to the same entity, the column name should describe the relationship where necessary.

---

## 7. Boolean Columns

Boolean columns should use descriptive prefixes such as:

```text
is_
has_
can_
```

Examples:

```text
is_active
is_cancelled
has_discount
can_renew
```

Boolean names should make the meaning of `true` and `false` clear.

Avoid generic names such as:

```text
active
flag
status_flag
```

when a more explicit name is possible.

---

## 8. Date and Timestamp Columns

Use `_date` for calendar dates:

```text
signup_date
birth_date
order_date
```

Use `_at` for timestamps representing a specific point in time:

```text
created_at
updated_at
paid_at
cancelled_at
resolved_at
```

Standard operational timestamps should use:

```text
created_at
updated_at
```

Event-specific timestamps should describe the event represented by the timestamp.

---

## 9. Numeric, Amount, and Count Columns

Numeric columns should communicate their meaning through their names.

Monetary values should use an explicit amount-oriented suffix:

```text
total_amount
refund_amount
monthly_fee
```

Counts should use `_count`:

```text
item_count
event_count
ticket_count
```

Percentages should use `_pct`:

```text
conversion_pct
discount_pct
```

Avoid ambiguous names such as:

```text
value
amount1
num
pct
```

when the underlying meaning can be stated explicitly.

---

## 10. Unique Constraints

Unique constraint names use:

```text
uq_<table>_<column(s)>
```

Examples:

```text
uq_customers_email
uq_products_sku
```

---

## 11. Check Constraints

Check constraint names use:

```text
ck_<table>_<description>
```

Examples:

```text
ck_orders_quantity_positive
ck_products_price_non_negative
```

Constraint descriptions should identify the rule being enforced.

---

## 12. Indexes

Index names use:

```text
ix_<table>_<column(s)>
```

Examples:

```text
ix_orders_customer_id
ix_orders_order_date
ix_payments_order_id
```

For multi-column indexes, list the columns in index order:

```text
ix_orders_customer_id_order_date
```

Indexes should be created for a demonstrated query, uniqueness requirement, or relationship requirement rather than added indiscriminately.

---

## 13. Migration Naming

Migration files use a zero-padded numeric sequence followed by a short description:

```text
001_create_raw_schema.sql
002_create_metadata_schema.sql
003_<description>.sql
```

The numeric prefix establishes migration order.

Migration descriptions should:

* use lowercase `snake_case`
* describe the database change
* remain concise
* avoid implementation-specific details

Example:

```text
003_create_raw_customers_table.sql
```

---

## 14. Layer Responsibilities

DataPulse separates database layers by responsibility.

```text
raw       → source-faithful
staging   → standardized
analytics → business-oriented
metadata  → operational
```

### Raw

The `raw` layer represents data as received from source systems.

Raw tables should preserve source semantics and should not prematurely apply business transformations.

Because DataPulse intentionally generates realistic data-quality issues, the raw layer must be able to capture problematic source records for downstream validation and analysis.

### Staging

The `staging` layer standardizes source data.

Typical responsibilities include:

* consistent data types
* standardized column naming
* basic normalization
* source-specific cleanup
* preparation for downstream transformations

### Analytics

The `analytics` layer represents business-oriented models used for reporting, analytics, anomaly detection, and downstream applications.

Business logic and derived metrics belong here rather than in the raw layer.

### Metadata

The `metadata` layer contains operational information about the data platform itself.

Examples include:

* ingestion runs
* source files
* processing status
* row counts
* pipeline execution metadata

Metadata should describe the operation of the platform rather than represent business-domain source data.

---

## 15. Raw-Layer Principle

The raw layer follows a **capture first, validate downstream** approach.

Raw ingestion should preserve the source data sufficiently to allow DataPulse to identify and analyze:

* missing values
* duplicate records
* invalid values
* broken references
* temporal inconsistencies
* schema drift
* unexpected record volumes

Business transformations and data-quality remediation should not be embedded prematurely into raw ingestion.

This separation allows the project to demonstrate realistic data-engineering workflows and makes downstream data-quality results traceable to the original source data.

---

## 16. Naming Consistency

When introducing a new database object, existing terminology should be reused wherever the same concept already exists.

For example, if the platform consistently uses:

```text
customer_id
order_id
created_at
updated_at
```

new tables should not introduce alternatives such as:

```text
client_id
purchase_id
creation_timestamp
last_modified
```

unless the source system genuinely uses a different concept that must be preserved in the raw layer.

Consistency is more important than creating a new naming pattern for each individual source.

---

## 17. Summary

DataPulse database naming follows these core principles:

1. Use lowercase `snake_case`.
2. Use plural names for tables.
3. Use `<entity>_id` for identifiers.
4. Use descriptive foreign-key names.
5. Use `is_`, `has_`, or `can_` for booleans.
6. Use `_date` for dates and `_at` for timestamps.
7. Use explicit names for amounts, counts, and percentages.
8. Use predictable prefixes for constraints and indexes.
9. Use ordered, descriptive migration filenames.
10. Keep the raw layer source-faithful.
11. Apply standardization in staging.
12. Keep business-oriented logic in analytics.
13. Keep platform-operational information in metadata.
