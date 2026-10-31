# Security design

RouteLedger is a demo system, but its security controls are real and tested.
The threat model assumes a hostile internet user who can create an account only
through an Administrator, and who may try to read or change data they should
not.

## Controls

| Area | Control | Where |
|---|---|---|
| Passwords | Argon2id hashing, strength policy (10+ chars, upper, lower, digit) | `app/security.py`, `scripts/create_admin.py` |
| Sessions | signed JWT, 60-minute expiry, `HttpOnly`, `SameSite=Lax`, `Secure` in production | `app/security.py`, `app/routers/auth.py` |
| Brute force | 5 failures → 15-minute lock; 10 login attempts/minute/IP | `auth.py`, `middleware.py` |
| Enumeration | identical message and timing for wrong email and wrong password | `auth.py` |
| Authorisation | server-side `require("can_edit" / "can_delete" / "can_manage")` on every write | `app/dependencies.py` |
| SQL injection | bound parameters everywhere; sort columns from a fixed dictionary | routers, `app/utils.py` |
| CSRF | state-changing requests with a foreign `Origin` or `Sec-Fetch-Site: cross-site` are rejected | `app/middleware.py` |
| XSS | DOM construction instead of HTML strings; strict CSP with no inline script | `frontend/js`, `middleware.py` |
| Clickjacking | `X-Frame-Options: DENY` + `frame-ancestors 'none'` | `middleware.py` |
| Sniffing | `X-Content-Type-Options: nosniff`, explicit MIME types | `middleware.py`, `main.py` |
| Host header | `TrustedHostMiddleware` with an allow-list | `main.py` |
| Privacy | `Referrer-Policy: no-referrer`, restrictive `Permissions-Policy`, COOP/CORP | `middleware.py` |
| Transport | HSTS when `COOKIE_SECURE=true`; deploy behind the platform's TLS | `middleware.py` |
| Caching | `Cache-Control: no-store` on API responses | `middleware.py` |
| Audit | database triggers write an append-only `activity_log` | `database/schema.sql` |
| Least privilege | the app role cannot drop tables, alter roles, or change the log | `database/create_app_user.sql`, `scripts/bootstrap_db.py` |
| Secrets | environment variables only; `.env` is git-ignored | `.gitignore`, `.env.example` |

## STRIDE summary

| Threat | Example | Mitigation |
|---|---|---|
| **S**poofing | stolen or forged session cookie | signed JWT, `HttpOnly` cookie, expiry, `Secure` + HSTS in production |
| **T**ampering | editing a product without permission | server-side role checks, database constraints |
| **R**epudiation | "I did not change that price" | trigger-based audit log with employee id, old/new values |
| **I**nformation disclosure | reading another user's data | authentication on every data route, no public listings |
| **D**enial of service | password guessing, expensive searches | login rate limit, lockout, paging capped at 100 rows |
| **E**levation of privilege | Viewer calling an Editor endpoint | permission dependency on every write, least-privilege DB role |

## OWASP Top 10 (2021) mapping

| Risk | Coverage |
|---|---|
| A01 Broken Access Control | role dependency on every write; deactivated users rejected on every request |
| A02 Cryptographic Failures | Argon2id, signed sessions, HTTPS/HSTS in production |
| A03 Injection | bound parameters, fixed sort allow-list, DOM-based UI |
| A04 Insecure Design | threat model, least privilege, append-only audit |
| A05 Security Misconfiguration | security headers, trusted hosts, CORS allow-list, debug off |
| A06 Vulnerable Components | pinned dependencies, Dependabot, `pip-audit` in CI |
| A07 Auth Failures | lockout, rate limiting, generic errors, session expiry |
| A08 Data Integrity Failures | constraints, triggers, transactional order creation |
| A09 Logging Failures | tamper-resistant audit log with before/after values |
| A10 SSRF | no outbound requests from user input |

## Automated evidence

The test suite (`backend/tests/`) proves the controls instead of only claiming
them:

- Argon2 hashes in the database, never plain text
- identical response for unknown email and wrong password
- lockout after five failures, even with the correct password
- rate limiting returns `429`
- forged, expired and `alg=none` tokens are rejected
- SQL-injection payloads in search and login find nothing and drop nothing
- every protected route returns `401` without a session
- each role is tested against write/delete/manage endpoints
- stale edits return `409`; a failed order saves no rows
- the audit log records the actor and cannot be updated or deleted
- security headers and CSP are present; pages contain no inline handlers
- the application database role cannot perform DDL or alter the log

## Known limits

- The rate limiter is in-process memory; multiple instances need Redis.
- JWT sessions cannot be revoked before expiry except by deactivating the user
  (which is checked on every request).
- Email-based password reset is intentionally out of scope; an Administrator
  resets passwords.
- This is not a substitute for a professional penetration test.
