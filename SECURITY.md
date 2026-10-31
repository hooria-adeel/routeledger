# Security policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| `main`  | Yes       |

## Reporting a vulnerability

Please do not open a public issue for a security problem. Contact the
maintainer privately (for example through the email on the GitHub profile) and
allow a few days for a reply. Include the affected endpoint, the steps to
reproduce, and the impact you believe it has.

## What is already in place

RouteLedger is a teaching project, but it treats security as part of the
design rather than an afterthought:

- **Passwords** are hashed with Argon2id. The plain password is never stored
  or logged.
- **Sessions** are signed JWTs inside an `HttpOnly`, `SameSite=Lax` cookie.
  `Secure` and HSTS are enabled when `COOKIE_SECURE=true`.
- **Authorisation** is checked on the server for every request. Hiding a
  button on the page is never the only protection.
- **SQL injection** is prevented with bound parameters and fixed sort lists.
  There are automated attacks in the test suite.
- **CSRF**: state-changing requests with an unexpected `Origin` or
  `Sec-Fetch-Site: cross-site` are refused.
- **XSS**: pages are built with DOM nodes, not HTML strings, and a strict
  Content Security Policy blocks third-party and inline scripts.
- **Clickjacking / sniffing**: `X-Frame-Options`, `nosniff`, COOP/CORP and a
  restrictive `Permissions-Policy` are sent on every response.
- **Brute force**: five wrong passwords lock the account for 15 minutes, and
  login is limited to ten attempts per minute per IP address.
- **Audit trail**: changes are recorded by database triggers in an
  append-only table. The application cannot edit or delete those rows.
- **Least privilege**: the web app connects as a role that can read, insert
  and update business data but cannot drop tables, change roles, or delete
  from the audit log.
- **Secrets** live in environment variables; `.env` is git-ignored.

## Scope

This is a portfolio/demo system. Before using it with real business data you
should add: a managed secret store, HTTPS with a real certificate, automated
backups and restore drills, centralised logging/monitoring, and a dependency
update process.
