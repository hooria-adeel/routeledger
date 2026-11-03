# Software Requirements Specification (SRS)

**Project:** RouteLedger — Distribution Management System
**Version:** 1.0
**Status:** Implemented and deployed
**Live system:** <https://routeledger-omega.vercel.app>

> All brands, products, retailers, areas, employees and orders in this project
> are synthetic. The dataset is produced by
> [`database/generate_seed.py`](../database/generate_seed.py) with a fixed random
> seed. No real company, customer or personal data is included.

---

## 1. Purpose

This document specifies the requirements for RouteLedger, a web-based
distribution management system that replaces spreadsheet-based workflows for a
consumer-goods distributor. It records products, retailers, branches, areas and
multi-line sales orders in one audited database, and controls who may read or
change that data.

The intended audience is the project owner, reviewers, and anyone evaluating the
system as a portfolio piece or extending it.

## 2. Scope

### 2.1 In scope

- Authentication with hashed passwords, session cookies and account lockout.
- Role-based authorisation for four roles.
- Product and category catalogue with price history.
- Retailer, branch and area registry.
- Multi-line sales orders with per-line pricing.
- Dashboard reporting (totals, trends, mix, rankings).
- Employee administration.
- A tamper-resistant audit trail.
- Search, sort, filter and paging on every list.
- Soft delete with restore.

### 2.2 Out of scope

Deliberately excluded to keep the project focused on data integrity and access
control:

- Stock quantities, warehouse movements and replenishment.
- Invoicing, payments, receivables and tax.
- Delivery routing, tracking and proof of delivery.
- A customer-facing portal or mobile application.
- Self-service password reset by email.
- Multi-tenancy and row-level security (listed in the roadmap).

## 3. Definitions

| Term | Meaning |
|---|---|
| **Carton** | The selling unit. A product has a pack size (units per carton). |
| **Line value** | `cartons × carton_price`, stored so historical invoices never change. |
| **Soft delete** | The row stays in the table with `is_deleted = TRUE` and disappears from normal reads. |
| **Stale edit** | A save that carries an older `version` than the stored row. |
| **Audit trail** | Append-only `activity_log` rows written by database triggers. |
| **Demo account** | A read-only Viewer login published on the sign-in page of the public demo. |

## 4. Actors and roles

| Actor | Permissions (`can_edit` / `can_delete` / `can_manage`) | Typical use |
|---|---|---|
| **Viewer** | ✗ / ✗ / ✗ | Read lists and the dashboard |
| **Editor** | ✓ / ✗ / ✗ | Enter and correct orders, products, retailers |
| **Manager** | ✓ / ✓ / ✗ | Delete and restore records, read the audit log |
| **Admin** | ✓ / ✓ / ✓ | Manage employees and roles |
| **Anonymous** | – | May only load the login page and the demo hint |
| **PostgreSQL** | – | Enforces constraints, triggers and grants independently of the app |

## 5. Functional requirements

Priority: **M** = must have, **S** = should have, **C** = could have.

### 5.1 Authentication and session (FR-A)

| ID | Requirement | Priority |
|---|---|---|
| FR-A1 | An employee signs in with email and password and receives a session cookie. | M |
| FR-A2 | Passwords are stored only as Argon2id hashes; the plain value is never stored or logged. | M |
| FR-A3 | The session is a signed JWT in an `HttpOnly`, `SameSite=Lax` cookie; `Secure` and HSTS are used over HTTPS. | M |
| FR-A4 | A session expires after `TOKEN_MINUTES` (default 60) and the user is returned to the login page. | M |
| FR-A5 | Five consecutive wrong passwords lock the account for 15 minutes. | M |
| FR-A6 | Login attempts are limited to 10 per minute per IP address; the reply carries `Retry-After`. | M |
| FR-A7 | Unknown email and wrong password produce the same message and comparable timing. | M |
| FR-A8 | A deactivated employee is rejected on the next request, even with a valid cookie. | M |
| FR-A9 | Signing out clears the cookie. | M |
| FR-A10 | The login page can display a configured read-only demo account. | S |

### 5.2 Products and categories (FR-P)

| ID | Requirement | Priority |
|---|---|---|
| FR-P1 | List products with category, pack size, unit price and carton price; support search, sort and paging. | M |
| FR-P2 | Create a product with name, category, pack size and unit price. | M |
| FR-P3 | Edit a product; a changed unit price is recorded in `product_price_history` with the acting employee. | M |
| FR-P4 | Soft-delete a product and restore it. | M |
| FR-P5 | Reject a duplicate product name, a pack size ≤ 0 or a negative price. | M |
| FR-P6 | Search tolerates `%` and `_` as literal characters rather than wildcards. | S |

### 5.3 Retailers, branches and areas (FR-R)

| ID | Requirement | Priority |
|---|---|---|
| FR-R1 | Maintain retailers and their branches, with each branch assigned to an area. | M |
| FR-R2 | A branch name is unique within its retailer, but may repeat across retailers. | M |
| FR-R3 | Area names are unique and may carry an optional district. | M |
| FR-R4 | Soft-delete and restore retailers, branches and areas. | M |
| FR-R5 | Soft-deleting a parent hides it from normal reads; dependent rows are preserved and foreign keys refuse a hard delete. | M |

### 5.4 Orders (FR-O)

| ID | Requirement | Priority |
|---|---|---|
| FR-O1 | Create an order for one retailer with an order date and one or more lines. | M |
| FR-O2 | Each line holds a product, a carton quantity > 0 and the carton price at the time of sale. | M |
| FR-O3 | `line_value` is calculated on the server and stored with the line. | M |
| FR-O4 | An order and all its lines are saved in one transaction: either everything is written or nothing is. | M |
| FR-O5 | A product may appear only once per order. | M |
| FR-O6 | The branch, when given, must belong to the order's retailer. | M |
| FR-O7 | The order date cannot be in the future or before 2000-01-01. | M |
| FR-O8 | Edit an order header, add/change/remove lines, soft-delete and restore the order. | M |
| FR-O9 | An order lists its retailer, branch, total value and line count. | S |

### 5.5 Dashboard (FR-D)

| ID | Requirement | Priority |
|---|---|---|
| FR-D1 | Show totals for products, retailers, branches, orders, sales value and cartons. | M |
| FR-D2 | Show sales by month, by category, by area, and top retailers/products. | M |
| FR-D3 | Clicking a month narrows the KPI cards and every breakdown to that month; the trend keeps every month for context. | S |
| FR-D4 | Totals must reconcile exactly with the underlying order lines. | M |

### 5.6 Employees and roles (FR-E)

| ID | Requirement | Priority |
|---|---|---|
| FR-E1 | An Admin lists employees with their role and status. | M |
| FR-E2 | An Admin creates an employee, choosing one of the four roles. | M |
| FR-E3 | An Admin edits an employee, resets a password, deactivates or reactivates the account. | M |
| FR-E4 | Password changes follow the password policy; the hash is replaced atomically. | M |
| FR-E5 | Only roles with `can_manage` may call these operations, on both UI and API. | M |

### 5.7 Audit trail (FR-L)

| ID | Requirement | Priority |
|---|---|---|
| FR-L1 | Every insert, update and delete on the seven business tables is recorded with actor, timestamp and full before/after snapshots. | M |
| FR-L2 | The log is readable by Managers and Admins, filterable by table and record. | S |
| FR-L3 | The application role cannot update or delete log rows. | M |
| FR-L4 | Logging happens in the same transaction as the change it describes. | M |

### 5.8 Non-functional linkage

Each functional area above is covered by automated tests; the mapping is in
§8 and in [`security.md`](security.md#automated-evidence).

## 6. Business rules

| ID | Rule | Enforced by |
|---|---|---|
| BR-1 | A product appears at most once per order. | `UNIQUE (order_id, product_id)` |
| BR-2 | `cartons > 0`, `carton_price ≥ 0`, `line_value ≥ 0`. | `CHECK` constraints |
| BR-3 | `line_value = cartons × carton_price`. | API calculation + `CHECK` |
| BR-4 | A branch belongs to exactly one retailer and one area. | Foreign keys |
| BR-5 | An order's branch must match its retailer. | API validation + FK |
| BR-6 | Names of products, retailers, areas and roles are unique. | `UNIQUE` |
| BR-7 | Concurrent edits never overwrite each other. | `version` trigger → `409` |
| BR-8 | Deletes are soft; history is preserved. | `is_deleted` + filtered reads |
| BR-9 | The audit log is append-only. | Trigger + revoked grants |
| BR-10 | A deactivated employee cannot act. | `is_active` checked per request |
| BR-11 | Only Managers and Admins may delete, restore or read the audit log. | Server-side permission dependency |

## 7. Non-functional requirements

### 7.1 Security

| ID | Requirement |
|---|---|
| NFR-S1 | All traffic is HTTPS; HSTS is sent when `COOKIE_SECURE=true`. |
| NFR-S2 | Every state-changing request with a foreign `Origin` or `Sec-Fetch-Site: cross-site` is refused. |
| NFR-S3 | SQL is executed with bound parameters only; sort columns come from a fixed allow-list. |
| NFR-S4 | Pages are built with DOM nodes, not HTML strings, under a strict Content Security Policy. |
| NFR-S5 | Security headers (`nosniff`, `X-Frame-Options: DENY`, COOP, CORP, `Referrer-Policy`, `Permissions-Policy`) are sent on every response. |
| NFR-S6 | `TrustedHostMiddleware` rejects unknown `Host` values. |
| NFR-S7 | The application connects with a role that cannot run DDL or rewrite the audit log. |
| NFR-S8 | Secrets come from environment variables; `.env` is git-ignored. |

### 7.2 Performance and capacity

| ID | Requirement |
|---|---|
| NFR-P1 | List endpoints page server-side with a maximum of 100 rows per request. |
| NFR-P2 | Name searches use GIN trigram indexes and stay usable at catalogue sizes in the tens of thousands. |
| NFR-P3 | Dashboard queries run against pre-defined views, not repeated ad-hoc SQL. |
| NFR-P4 | Typical API responses on the free serverless tier complete well under 2 s after a cold start. |

### 7.3 Usability and accessibility

| ID | Requirement |
|---|---|
| NFR-U1 | Light and dark themes, and three text sizes, persist across sessions. |
| NFR-U2 | Every interactive control is reachable by keyboard with a visible focus ring. |
| NFR-U3 | The layout works from 390 px mobile width upwards. |
| NFR-U4 | Errors are shown in plain language, not stack traces. |
| NFR-U5 | Destructive actions require explicit confirmation. |

### 7.4 Reliability and integrity

| ID | Requirement |
|---|---|
| NFR-R1 | A failed order write leaves no partial rows. |
| NFR-R2 | Stale writes return `409` with a message telling the user to reload. |
| NFR-R3 | The system starts even when the database is temporarily unreachable, and reconnects. |
| NFR-R4 | Backups and a documented restore procedure exist. |

### 7.5 Maintainability and portability

| ID | Requirement |
|---|---|
| NFR-M1 | Dependencies are pinned; automated tests run in CI on Python 3.12 and 3.13. |
| NFR-M2 | The same code runs locally, in Docker and on a serverless host without source changes. |
| NFR-M3 | Database rules live in SQL files that can be applied to any PostgreSQL 16+ instance. |
| NFR-M4 | Configuration is environment-driven with documented variables. |

### 7.6 Data

| ID | Requirement |
|---|---|
| NFR-D1 | Data is normalised to third normal form, with one documented exception (`line_value`). |
| NFR-D2 | Synthetic data is reproducible from a fixed seed. |
| NFR-D3 | No real personal data is stored in the repository or the demo database. |

## 8. Verification

| Requirement group | Evidence |
|---|---|
| Authentication (FR-A) | `backend/tests/test_security.py` — hashing, lockout, rate limit, forged/expired tokens |
| Authorisation | role-by-role tests against write, delete and manage endpoints |
| Data rules (BR-1 … BR-9) | `backend/tests/test_database.py` — constraints, triggers, views, rollback |
| CSRF, hosts, headers | dedicated tests and live checks on the deployment |
| Reconciliation (FR-D4) | view totals compared with raw order lines |

Current suite: **98 tests** (80 security + 18 database), all passing.

## 9. Constraints and assumptions

- PostgreSQL 16 or newer is required (`ON CONFLICT`, `jsonb`, trigram indexes, `GENERATED` columns).
- The browser must accept cookies; some corporate proxies strip them.
- One application instance is assumed for the in-process rate limiter; multiple
  instances would need a shared store such as Redis.
- The public demo publishes a read-only account by design; it must be removed
  before using the system with real data.

## 10. Acceptance criteria (sample)

1. Logging in with a valid account returns the employee and sets an `HttpOnly` cookie.
2. Five wrong passwords lock the account; the correct password then returns `423`.
3. A Viewer calling `POST /products` receives `403`, and no row is created.
4. Saving an order whose second line has `cartons = 0` creates no order at all.
5. Two users editing the same product: the second save returns `409`.
6. `UPDATE activity_log` is refused for the application role.
7. `/health` reports the product count and returns `200` without a login.
