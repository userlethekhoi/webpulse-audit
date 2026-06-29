# SECURITY_GUIDELINES.md — Security Engineering Handbook for AI Coding Agents

> **Classification:** Security Engineering Standard  
> **Version:** 1.0  
> **Sensitivity:** Internal — Engineering Use Only  
> **Applicability:** All source code, infrastructure, and configuration  
> **Companion Documents:**  
> - [AI_CODING_SYSTEM_PROMPT.md](./AI_CODING_SYSTEM_PROMPT.md) — Agent behavioral rules  
> - [CODING_STANDARDS.md](./CODING_STANDARDS.md) — Coding standards  
> - [REVIEW_CHECKLIST.md](./REVIEW_CHECKLIST.md) — Pull request review checklist

---

## How to Use This Document

This handbook defines **mandatory security controls** for AI coding agents producing production code. Every section follows a consistent format designed for rapid lookup during code generation and review.

**For AI agents:** Before writing any code that handles user input, network communication, authentication, or data storage, consult the relevant section. Security controls are non-negotiable — they cannot be deferred to "later" or marked as TODO.

**Severity ratings:**

| Rating | Meaning |
|---|---|
| 🔴 **Critical** | Exploitation leads to full compromise, data breach, or RCE |
| 🟠 **High** | Exploitation leads to unauthorized access or significant data exposure |
| 🟡 **Medium** | Exploitation leads to limited data exposure or degraded security |
| 🟢 **Low** | Informational finding or defense-in-depth improvement |

---

## Table of Contents

1. [OWASP Top 10 Overview](#1-owasp-top-10-overview)
2. [SQL Injection](#2-sql-injection)
3. [Cross-Site Scripting (XSS)](#3-cross-site-scripting-xss)
4. [Cross-Site Request Forgery (CSRF)](#4-cross-site-request-forgery-csrf)
5. [Server-Side Request Forgery (SSRF)](#5-server-side-request-forgery-ssrf)
6. [XML External Entities (XXE)](#6-xml-external-entities-xxe)
7. [Open Redirect](#7-open-redirect)
8. [File Upload Security](#8-file-upload-security)
9. [Authentication](#9-authentication)
10. [Authorization](#10-authorization)
11. [JWT Security](#11-jwt-security)
12. [OAuth Security](#12-oauth-security)
13. [Cookie Security](#13-cookie-security)
14. [Session Management](#14-session-management)
15. [Secrets Management](#15-secrets-management)
16. [Environment Variables](#16-environment-variables)
17. [TLS / Transport Security](#17-tls--transport-security)
18. [CORS Configuration](#18-cors-configuration)
19. [Rate Limiting](#19-rate-limiting)
20. [Input Validation](#20-input-validation)
21. [Output Encoding](#21-output-encoding)
22. [Dependency Scanning](#22-dependency-scanning)
23. [Least Privilege](#23-least-privilege)
24. [Logging Security](#24-logging-security)
25. [Secure Defaults](#25-secure-defaults)

---

## 1. OWASP Top 10 Overview

The OWASP Top 10 represents the most critical web application security risks. Every AI agent producing web-facing code must understand and defend against these categories.

| Rank | Category | Relevant Section |
|---|---|---|
| A01:2021 | Broken Access Control | §10 Authorization, §7 Open Redirect |
| A02:2021 | Cryptographic Failures | §17 TLS, §11 JWT, §15 Secrets |
| A03:2021 | Injection | §2 SQL Injection, §3 XSS, §6 XXE |
| A04:2021 | Insecure Design | §25 Secure Defaults, §23 Least Privilege |
| A05:2021 | Security Misconfiguration | §18 CORS, §16 Environment Variables |
| A06:2021 | Vulnerable Components | §22 Dependency Scanning |
| A07:2021 | Authentication Failures | §9 Authentication, §14 Sessions |
| A08:2021 | Data Integrity Failures | §11 JWT, §12 OAuth |
| A09:2021 | Logging Failures | §24 Logging Security |
| A10:2021 | SSRF | §5 SSRF |

**AI Implementation Note:** When generating code for any web-facing feature, mentally map the feature to applicable OWASP categories and apply the corresponding controls from the referenced sections.

---

## 2. SQL Injection

**Severity:** 🔴 Critical

### Description

SQL injection occurs when user-controlled input is concatenated into SQL queries without sanitization. An attacker can modify the query logic to read, modify, or delete data, execute administrative operations, or in some cases achieve remote code execution.

### How to Detect

- Search for string formatting in SQL: `f"SELECT`, `"SELECT ... %s" %`, `"SELECT ... " +`, `.format(`
- Search for raw SQL execution: `cursor.execute(query)` where `query` contains user input
- Search for ORM bypass: `.raw(`, `.extra(`, `RawSQL(`
- Static analysis: `bandit -t B608` (hardcoded SQL expressions)

### How to Prevent

```python
# ✅ SECURE — Parameterized query
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# ✅ SECURE — ORM query
user = await User.objects.filter(email=email).first()

# ✅ SECURE — SQLAlchemy with bound parameters
stmt = select(User).where(User.email == email)
result = await session.execute(stmt)

# ❌ VULNERABLE — String concatenation
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ❌ VULNERABLE — String formatting
cursor.execute("SELECT * FROM users WHERE email = '%s'" % email)
```

### Code Review Checklist

- [ ] All SQL queries use parameterized statements or ORM methods
- [ ] No string concatenation, f-strings, `.format()`, or `%` operator in SQL
- [ ] ORM `.raw()` and `.extra()` use parameter binding
- [ ] Table and column names are never user-controlled (use allowlist if dynamic)
- [ ] Stored procedures use parameterized inputs
- [ ] `LIKE` clauses escape `%` and `_` metacharacters in user input

### Common Mistakes

1. Using parameterized queries for values but concatenating table/column names
2. Using ORM `.raw()` with formatted strings instead of bound parameters
3. Assuming integer inputs don't need parameterization (they do)
4. Escaping quotes manually instead of using parameterized queries
5. Using `LIKE '%' + user_input + '%'` without escaping LIKE metacharacters

### Secure Coding Recommendations

- **Always** use parameterized queries — no exceptions
- Use ORM methods for all standard operations
- If dynamic table/column names are needed, validate against an explicit allowlist
- Enable SQL query logging in development to audit generated queries
- Use `sqlalchemy.text()` with `:param` syntax for raw SQL when ORM is insufficient

---

## 3. Cross-Site Scripting (XSS)

**Severity:** 🔴 Critical

### Description

XSS occurs when an application includes untrusted data in HTML output without proper encoding. Attackers inject JavaScript that executes in victims' browsers, stealing session tokens, credentials, or performing actions on behalf of users.

**Types:**
- **Reflected:** Payload in URL/request, reflected in response
- **Stored:** Payload saved in database, rendered to other users
- **DOM-based:** Client-side JavaScript processes untrusted data into the DOM

### How to Detect

- Search for raw HTML rendering: `|safe`, `{% autoescape off %}`, `markupsafe.Markup(user_input)`, `innerHTML =`
- Search for template rendering with unescaped variables
- Search for `dangerouslySetInnerHTML` in React
- Search for `document.write()`, `.innerHTML`, `.outerHTML` with user data

### How to Prevent

```python
# ✅ SECURE — Template engine auto-escaping (Jinja2)
# {{ user_name }} — auto-escaped by default

# ✅ SECURE — Explicit escaping
from markupsafe import escape
safe_name = escape(user_name)

# ✅ SECURE — Content Security Policy header
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; script-src 'self'; style-src 'self'"
)

# ❌ VULNERABLE — Bypassing auto-escape
{{ user_input | safe }}

# ❌ VULNERABLE — Raw HTML insertion
document.getElementById("output").innerHTML = userInput;
```

### Code Review Checklist

- [ ] Template engine auto-escaping is enabled globally
- [ ] No use of `|safe`, `{% autoescape off %}`, or `Markup()` on user input
- [ ] CSP headers are set on all HTML responses
- [ ] JavaScript does not use `.innerHTML` with user-controlled data
- [ ] URLs in `href` and `src` attributes validate scheme (no `javascript:`)
- [ ] JSON embedded in HTML uses `json.dumps()` with proper escaping

### Common Mistakes

1. Trusting "internal" data that originally came from user input
2. Encoding for HTML context but not for JavaScript or URL context
3. Using CSP with `unsafe-inline` or `unsafe-eval` (defeats the purpose)
4. Sanitizing input instead of encoding output (sanitizers can be bypassed)
5. Forgetting that attribute values, URLs, and CSS contexts need different encoding

### Secure Coding Recommendations

- Enable auto-escaping in all template engines (Jinja2: `autoescape=True`)
- Implement Content Security Policy headers on every HTML response
- Use `json.dumps()` with `ensure_ascii=True` when embedding JSON in HTML
- Never construct HTML with string concatenation — use template engines
- For rich text, use an allowlist-based sanitizer (e.g., `bleach`) with a strict tag set

---

## 4. Cross-Site Request Forgery (CSRF)

**Severity:** 🟠 High

### Description

CSRF tricks authenticated users into submitting unintended requests. An attacker hosts a page that submits a form or triggers a request to the target application, using the victim's session cookies to authenticate the malicious request.

### How to Detect

- Search for state-changing endpoints (POST, PUT, DELETE) without CSRF token validation
- Check if `SameSite` cookie attribute is set
- Verify CSRF middleware is enabled in web frameworks
- Check for CORS misconfiguration that allows cross-origin POST

### How to Prevent

```python
# ✅ SECURE — Django CSRF middleware (enabled by default)
MIDDLEWARE = [
    "django.middleware.csrf.CsrfViewMiddleware",
    ...
]

# ✅ SECURE — SameSite cookies
response.set_cookie(
    "session_id",
    value=session_id,
    samesite="Lax",      # or "Strict"
    secure=True,
    httponly=True,
)

# ✅ SECURE — Custom header check for API
# Require X-Requested-With header on all state-changing API calls
if request.headers.get("X-Requested-With") != "XMLHttpRequest":
    raise Forbidden("Missing CSRF header")

# ❌ VULNERABLE — No CSRF protection on state-changing endpoint
@app.post("/transfer")
async def transfer_funds(request):
    # No token validation — any cross-origin form can trigger this
    ...
```

### Code Review Checklist

- [ ] CSRF middleware enabled for all state-changing endpoints
- [ ] Session cookies have `SameSite=Lax` or `SameSite=Strict`
- [ ] API endpoints use token-based auth (not cookies) or validate Origin header
- [ ] CSRF tokens are unique per session and cryptographically random
- [ ] GET requests do not modify state

### Common Mistakes

1. Disabling CSRF middleware "because the frontend is separate"
2. Using `SameSite=None` without understanding cross-origin implications
3. Accepting GET requests for state changes (login, purchase, delete)
4. Using predictable or reusable CSRF tokens
5. Not validating the `Origin` or `Referer` header on API endpoints

### Secure Coding Recommendations

- Enable framework CSRF protection (Django, Flask-WTF, FastAPI middleware)
- Set `SameSite=Lax` on all session cookies (minimum)
- For SPAs, use token-based authentication (Bearer tokens) instead of cookies
- Validate `Origin` header on all cross-origin-capable endpoints
- Never perform state changes on GET requests

---

## 5. Server-Side Request Forgery (SSRF)

**Severity:** 🔴 Critical

### Description

SSRF occurs when an application makes HTTP requests to user-controlled URLs. Attackers can access internal services, cloud metadata endpoints (169.254.169.254), private networks, and local files via `file://` scheme.

### How to Detect

- Search for user input flowing to HTTP client calls: `httpx.get(user_url)`, `requests.get(url)`
- Search for URL parameters: `?url=`, `?redirect=`, `?callback=`, `?next=`
- Check for URL validation that only checks scheme but not host
- Look for DNS rebinding vulnerabilities (validate after resolution)

### How to Prevent

```python
import ipaddress
from urllib.parse import urlparse
import socket

BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # Cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

def validate_url_for_ssrf(url: str) -> str:
    """Validate URL is safe for server-side fetching."""
    parsed = urlparse(url)

    # ✅ Scheme validation
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"Unsupported scheme: {parsed.scheme}")

    # ✅ Resolve hostname to IP BEFORE making the request
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
    except (socket.gaierror, ValueError) as exc:
        raise ValidationError(f"Cannot resolve: {parsed.hostname}") from exc

    # ✅ Block private/internal IPs
    for network in BLOCKED_NETWORKS:
        if ip in network:
            raise ValidationError(f"Blocked: internal network {network}")

    return url
```

### Code Review Checklist

- [ ] All outbound HTTP requests with user-controlled URLs validate the URL
- [ ] Private IP ranges (10/8, 172.16/12, 192.168/16, 127/8) are blocked
- [ ] Cloud metadata IP (169.254.169.254) is blocked
- [ ] Only `http://` and `https://` schemes are allowed
- [ ] DNS resolution is performed before validation (not just hostname check)
- [ ] Redirects are limited and validated (attacker can redirect to internal IP)
- [ ] `file://`, `ftp://`, `gopher://`, `dict://` schemes are rejected

### Common Mistakes

1. Validating the hostname string but not the resolved IP (DNS rebinding)
2. Blocking `127.0.0.1` but not `0177.0.0.1` (octal), `2130706433` (decimal), or `0x7f000001` (hex)
3. Allowing redirects that land on internal IPs
4. Blocking known internal IPs but not IPv6 equivalents
5. Only checking the initial URL, not redirect targets

### Secure Coding Recommendations

- Resolve DNS and validate the IP address before making the request
- Use an allowlist of permitted domains when possible
- Disable or limit redirects: `httpx.AsyncClient(follow_redirects=False)`
- If redirects are needed, validate each redirect target against the same rules
- Run outbound-request services in network-isolated environments

---

## 6. XML External Entities (XXE)

**Severity:** 🔴 Critical

### Description

XXE attacks exploit XML parsers that process external entity declarations. Attackers can read local files, access internal systems, perform SSRF, or cause denial of service through entity expansion ("Billion Laughs").

### How to Detect

- Search for XML parsing: `xml.etree`, `lxml.etree`, `xml.sax`, `xml.dom`
- Check if external entity processing is disabled
- Search for `DOCTYPE` handling in user-submitted XML
- Look for XML-accepting endpoints without content type validation

### How to Prevent

```python
# ✅ SECURE — defusedxml (drop-in replacement)
import defusedxml.ElementTree as ET
tree = ET.parse(user_xml_file)  # External entities disabled

# ✅ SECURE — lxml with safe settings
from lxml import etree
parser = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    dtd_validation=False,
    load_dtd=False,
)
tree = etree.parse(user_xml_file, parser)

# ❌ VULNERABLE — stdlib XML parser with no protection
import xml.etree.ElementTree as ET
tree = ET.parse(user_xml_file)  # External entities processed!
```

### Code Review Checklist

- [ ] All XML parsing uses `defusedxml` or equivalent safe parser
- [ ] External entity resolution is disabled
- [ ] DTD processing is disabled
- [ ] Network access during parsing is disabled
- [ ] Entity expansion limits are set (Billion Laughs protection)
- [ ] If XML is not needed, use JSON instead

### Common Mistakes

1. Using `xml.etree.ElementTree` from stdlib (no XXE protection)
2. Disabling entity resolution but not DTD loading
3. Accepting XML when JSON would suffice
4. Trusting XML from "internal" sources that may be user-influenced
5. Not setting entity expansion limits (denial of service)

### Secure Coding Recommendations

- **Prefer JSON over XML** whenever possible
- Use `defusedxml` as a drop-in replacement for all stdlib XML modules
- If using `lxml`, configure parser with `resolve_entities=False, no_network=True`
- Set entity expansion limits to prevent denial of service
- Validate Content-Type headers — reject unexpected XML content

---

## 7. Open Redirect

**Severity:** 🟡 Medium

### Description

Open redirects occur when an application redirects users to a URL specified in user input without validation. Attackers use these for phishing — the victim sees a legitimate domain in the link but is redirected to a malicious site.

### How to Detect

- Search for redirect functions with user-controlled URLs: `redirect(request.args.get("next"))`
- Search for URL parameters: `?next=`, `?redirect=`, `?return_to=`, `?url=`, `?continue=`
- Check if redirect targets are validated against an allowlist

### How to Prevent

```python
from urllib.parse import urlparse

ALLOWED_HOSTS: set[str] = {"example.com", "app.example.com"}

def safe_redirect(target_url: str, default: str = "/") -> str:
    """Validate redirect target is internal or on allowlist."""
    parsed = urlparse(target_url)

    # ✅ Allow relative URLs (internal redirects)
    if not parsed.netloc:
        # Reject protocol-relative URLs (//evil.com)
        if target_url.startswith("//"):
            return default
        return target_url

    # ✅ Allow only explicitly permitted hosts
    if parsed.hostname in ALLOWED_HOSTS and parsed.scheme in ("http", "https"):
        return target_url

    return default

# ❌ VULNERABLE — Unvalidated redirect
@app.get("/login")
async def login(next_url: str = "/"):
    return RedirectResponse(next_url)  # Attacker: /login?next=https://evil.com
```

### Code Review Checklist

- [ ] All redirect targets are validated against an allowlist of hosts
- [ ] Relative URLs are allowed, protocol-relative URLs (`//evil.com`) are rejected
- [ ] Default redirect target is used when validation fails
- [ ] `javascript:` scheme is rejected in redirect targets
- [ ] Redirect parameters are not reflected in error messages (prevents XSS)

### Common Mistakes

1. Only checking if the URL starts with `/` (fails for `//evil.com`)
2. Checking domain with `in` instead of exact match (`evil.com` contains `com`)
3. Allowing arbitrary subdomains (`attacker.example.com`)
4. Not rejecting `javascript:` and `data:` scheme URLs
5. Trusting `Referer` header for redirect targets

### Secure Coding Recommendations

- Use an allowlist of permitted redirect hosts — never a blocklist
- For login flows, store the return URL in the session (not in URL parameters)
- Validate the full parsed URL (scheme, host, port), not just the string
- If only internal redirects are needed, require the URL to be path-only (no scheme/host)

---

## 8. File Upload Security

**Severity:** 🟠 High

### Description

Insecure file upload handling can lead to remote code execution (uploading web shells), path traversal (overwriting system files), stored XSS (uploading HTML), and denial of service (uploading very large files).

### How to Detect

- Search for file upload endpoints: `request.files`, `UploadFile`, `multipart/form-data`
- Check if file extensions are validated against an allowlist
- Check if uploaded files are stored with original filenames
- Verify file content type is validated (not just the extension)

### How to Prevent

```python
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".pdf"}
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

async def handle_upload(upload: UploadFile) -> Path:
    """Securely handle file upload."""
    # ✅ Validate file size
    content = await upload.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError(f"File exceeds {MAX_FILE_SIZE} bytes")

    # ✅ Validate extension against allowlist
    original = Path(upload.filename) if upload.filename else Path("unnamed")
    if original.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Extension not allowed: {original.suffix}")

    # ✅ Validate content type matches extension (magic bytes)
    detected_type = detect_mime_type(content)
    if not is_type_allowed(detected_type, original.suffix):
        raise ValidationError("Content type mismatch")

    # ✅ Generate random filename — never use original
    safe_name = f"{uuid.uuid4().hex}{original.suffix.lower()}"
    dest = UPLOAD_DIR / safe_name

    # ✅ Verify destination is within upload directory
    dest = dest.resolve()
    if not str(dest).startswith(str(UPLOAD_DIR.resolve())):
        raise ValidationError("Path traversal detected")

    dest.write_bytes(content)
    return dest
```

### Code Review Checklist

- [ ] File extension validated against an allowlist (not blocklist)
- [ ] File content type validated via magic bytes, not just `Content-Type` header
- [ ] Original filename is NEVER used for storage — generate a random name
- [ ] File size is limited and enforced before writing to disk
- [ ] Upload directory is outside the web root
- [ ] Uploaded files are not executable (no `.py`, `.php`, `.jsp`, `.sh`)
- [ ] Path traversal is prevented (resolve and verify base directory)
- [ ] Antivirus scan is performed on uploads in high-security contexts

### Common Mistakes

1. Validating extension with a blocklist (misses `.phtml`, `.php5`, etc.)
2. Trusting the `Content-Type` header (set by the client, easily spoofed)
3. Using the original filename (enables path traversal via `../../etc/passwd`)
4. Storing uploads in a web-accessible directory (enables direct execution)
5. No file size limit (denial of service via huge uploads)

### Secure Coding Recommendations

- Generate random filenames using `uuid.uuid4()` for all stored files
- Store uploads outside the web root in a dedicated, non-executable directory
- Validate both extension (allowlist) and content (magic bytes)
- Set strict file size limits at both application and web server levels
- Serve uploaded files via a separate domain or with `Content-Disposition: attachment`

---

## 9. Authentication

**Severity:** 🔴 Critical

### Description

Authentication verifies that a user is who they claim to be. Broken authentication enables attackers to assume other users' identities, access unauthorized accounts, and compromise the entire system.

### How to Detect

- Search for custom authentication logic (instead of established libraries)
- Check password storage: `md5(`, `sha1(`, `hashlib.sha256(password` (no salt)
- Check for timing-safe comparison on tokens and passwords
- Verify brute-force protections (rate limiting, lockout)

### How to Prevent

```python
# ✅ SECURE — Password hashing with bcrypt
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ✅ SECURE — Timing-safe token comparison
import hmac

def verify_token(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided.encode(), expected.encode())

# ❌ VULNERABLE — Plain text password storage
user.password = request.form["password"]

# ❌ VULNERABLE — MD5/SHA hashing (no salt, fast = brute-forceable)
user.password = hashlib.md5(password.encode()).hexdigest()

# ❌ VULNERABLE — String comparison (timing attack)
if provided_token == expected_token:
    ...
```

### Code Review Checklist

- [ ] Passwords hashed with bcrypt, Argon2, or scrypt (not MD5/SHA)
- [ ] Password hash includes unique salt per user
- [ ] Token comparison uses `hmac.compare_digest()` (constant-time)
- [ ] Account lockout or rate limiting after N failed attempts
- [ ] Password complexity requirements enforced
- [ ] Password reset tokens are single-use and time-limited
- [ ] Multi-factor authentication supported for sensitive operations
- [ ] Authentication errors do not reveal whether username or password is wrong

### Common Mistakes

1. Rolling custom authentication instead of using established libraries
2. Using fast hashes (MD5, SHA-256) for passwords — these are brute-forceable
3. Using `==` for token comparison (timing side-channel attack)
4. Revealing "user not found" vs "wrong password" in error messages
5. Not invalidating sessions after password change

### Secure Coding Recommendations

- Use `bcrypt` (cost factor ≥12) or `argon2-cffi` for password hashing
- Use `hmac.compare_digest()` for ALL security-sensitive comparisons
- Implement progressive delays or account lockout after failed attempts
- Invalidate all existing sessions when password is changed
- Return identical error messages for "user not found" and "wrong password"

---

## 10. Authorization

**Severity:** 🔴 Critical

### Description

Authorization determines what an authenticated user is allowed to do. Broken authorization lets users access other users' data, perform privileged operations, or escalate their role to administrator.

### How to Detect

- Search for direct object references: `/api/users/{id}` where `id` is user-controlled
- Check if ownership is verified before data access or modification
- Search for role checks that are missing or client-side only
- Verify horizontal access controls (user A can't access user B's data)

### How to Prevent

```python
# ✅ SECURE — Always verify ownership
async def get_document(document_id: int, current_user: User) -> Document:
    document = await Document.objects.get(id=document_id)
    if document.owner_id != current_user.id:
        raise PermissionDenied("Access denied")
    return document

# ✅ SECURE — Role-based authorization decorator
def require_role(required_role: Role):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            if request.user.role != required_role:
                raise PermissionDenied("Insufficient privileges")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

@require_role(Role.ADMIN)
async def delete_user(request, user_id: int):
    ...

# ❌ VULNERABLE — No ownership check (IDOR)
async def get_document(document_id: int) -> Document:
    return await Document.objects.get(id=document_id)
    # Any authenticated user can access ANY document!
```

### Code Review Checklist

- [ ] Every data access verifies the requesting user's ownership or role
- [ ] Authorization checks are server-side (never client-side only)
- [ ] Direct object references (IDs in URLs) are protected against IDOR
- [ ] Role escalation is prevented (users cannot set their own role)
- [ ] Admin endpoints require admin role
- [ ] Bulk operations enforce per-item authorization

### Common Mistakes

1. Checking authentication but not authorization (any logged-in user can do anything)
2. Trusting client-side role checks (hidden buttons but accessible API)
3. Using sequential integer IDs without ownership verification (IDOR)
4. Checking role on the "list" endpoint but not the "detail" endpoint
5. Allowing users to modify their own role field in profile updates

### Secure Coding Recommendations

- Filter all database queries by the current user's scope
- Use UUIDs instead of sequential IDs for public-facing identifiers
- Implement authorization as middleware or decorators (centralized, not per-endpoint)
- Log all authorization failures for security monitoring
- Apply the Principle of Least Privilege — deny by default, grant explicitly

---

## 11. JWT Security

**Severity:** 🟠 High

### Description

JSON Web Tokens (JWTs) are used for stateless authentication. Misconfigured JWTs can be forged, tampered with, or replayed. Common vulnerabilities include algorithm confusion (`none` algorithm), weak secrets, and missing validation.

### How to Detect

- Search for JWT library usage: `jwt.encode`, `jwt.decode`, `jose.jwt`
- Check if algorithm is explicitly specified in decode (not inferred from token)
- Check if `exp`, `iss`, `aud` claims are validated
- Check if the signing secret is strong and properly managed

### How to Prevent

```python
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = settings.jwt_secret_key  # From env, ≥256 bits

def create_token(user_id: str) -> str:
    """Create a signed JWT with expiration."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        "iss": "myapp",
        "aud": "myapp-api",
    }
    # ✅ Explicit algorithm
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    """Verify and decode JWT with strict validation."""
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],   # ✅ Explicit — prevents algorithm confusion
            issuer="myapp",          # ✅ Validate issuer
            audience="myapp-api",    # ✅ Validate audience
            options={
                "require": ["exp", "iss", "aud", "sub"],  # ✅ Require claims
            },
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid token: {exc}") from exc

# ❌ VULNERABLE — No algorithm specified (accepts 'none')
payload = jwt.decode(token, SECRET_KEY)

# ❌ VULNERABLE — Weak secret
SECRET_KEY = "secret"
```

### Code Review Checklist

- [ ] `algorithms` parameter explicitly set in `jwt.decode()` — never inferred
- [ ] `"none"` algorithm is never accepted
- [ ] Signing secret is ≥256 bits and loaded from environment
- [ ] `exp` (expiration) claim is always set and validated
- [ ] `iss` (issuer) and `aud` (audience) claims are validated
- [ ] Token refresh mechanism exists with shorter access token lifetimes
- [ ] Revocation mechanism exists (blacklist or short-lived + refresh)

### Common Mistakes

1. Not specifying `algorithms=` in decode (allows algorithm switching to `none`)
2. Using a weak signing secret (dictionary-attackable)
3. Setting very long expiration (days/months instead of minutes/hours)
4. Storing sensitive data in JWT payload (it's base64, not encrypted)
5. No token revocation mechanism (compromised token valid until expiry)

### Secure Coding Recommendations

- Use `HS256` with ≥256-bit secret or `RS256` with RSA key pair
- Set access token expiration to 15–60 minutes
- Implement refresh tokens for session extension
- Never store sensitive data in JWT payload — it is readable by anyone
- Consider `PyJWT` or `python-jose` — both enforce algorithm specification

---

## 12. OAuth Security

**Severity:** 🟠 High

### Description

OAuth 2.0 is a delegation protocol for authorization. Misconfigured OAuth flows enable token theft, authorization code interception, and privilege escalation.

### How to Detect

- Check if `state` parameter is validated (prevents CSRF)
- Check if PKCE is used for public clients
- Verify redirect URI is validated against exact-match allowlist
- Check token storage (localStorage vs httpOnly cookie)

### How to Prevent

```python
import secrets

# ✅ SECURE — Generate and validate state parameter
def initiate_oauth_flow(session: dict) -> str:
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    return f"https://provider.com/authorize?state={state}&..."

def handle_callback(request, session: dict) -> Token:
    # ✅ Validate state to prevent CSRF
    if request.args.get("state") != session.pop("oauth_state", None):
        raise SecurityError("Invalid OAuth state — possible CSRF")

    code = request.args.get("code")
    # ✅ Exchange code for token server-side
    token = exchange_code(code, client_secret=settings.oauth_client_secret)
    return token

# ❌ VULNERABLE — No state validation
def handle_callback(request):
    code = request.args.get("code")
    token = exchange_code(code)  # CSRF: attacker can inject their code
```

### Code Review Checklist

- [ ] `state` parameter generated with `secrets.token_urlsafe()` and validated
- [ ] PKCE (`code_verifier` / `code_challenge`) used for mobile and SPA clients
- [ ] Redirect URIs validated by exact match (no wildcards, no subdomain matching)
- [ ] Authorization codes are single-use and short-lived
- [ ] Client secrets stored in environment variables, never in client-side code
- [ ] Token exchange happens server-side, not in the browser

### Common Mistakes

1. Not validating the `state` parameter (CSRF on OAuth callback)
2. Using implicit flow (tokens in URL fragments — deprecated)
3. Allowing wildcard redirect URIs (`https://*.example.com/callback`)
4. Storing client secrets in frontend JavaScript
5. Not implementing PKCE for public clients (mobile, SPA)

### Secure Coding Recommendations

- Always use Authorization Code flow with PKCE
- Validate `state` on every callback — generate with `secrets.token_urlsafe(32)`
- Register exact redirect URIs — no patterns or wildcards
- Store tokens in httpOnly, Secure, SameSite cookies (not localStorage)
- Implement token rotation on refresh

---

## 13. Cookie Security

**Severity:** 🟠 High

### Description

Cookies store session identifiers and authentication state. Without proper attributes, cookies can be stolen via XSS, sent over unencrypted connections, or included in cross-site requests.

### How to Detect

- Search for `set_cookie()`, `response.cookies`, `Set-Cookie` header
- Check for missing `Secure`, `HttpOnly`, `SameSite` attributes
- Check cookie expiration and scope (domain, path)

### How to Prevent

```python
# ✅ SECURE — All security attributes set
response.set_cookie(
    key="session_id",
    value=session_token,
    httponly=True,       # Not accessible via JavaScript
    secure=True,         # Only sent over HTTPS
    samesite="Lax",      # Not sent on cross-site POST
    max_age=3600,        # 1 hour expiration
    path="/",            # Scoped to root path
    domain=".example.com",
)

# ❌ VULNERABLE — No security attributes
response.set_cookie("session_id", session_token)
# Defaults: HttpOnly=False, Secure=False, SameSite=None
```

### Code Review Checklist

- [ ] All cookies set `HttpOnly=True` (prevents JavaScript access)
- [ ] All cookies set `Secure=True` (HTTPS only)
- [ ] All cookies set `SameSite=Lax` or `SameSite=Strict`
- [ ] Cookie values are cryptographically random (not guessable)
- [ ] Cookie expiration is set and reasonable
- [ ] Cookie scope (domain, path) is as narrow as possible
- [ ] No sensitive data stored in cookie value (use session ID only)

### Common Mistakes

1. Setting cookies without `HttpOnly` — stolen by XSS
2. Setting cookies without `Secure` — sent over HTTP (man-in-the-middle)
3. Using `SameSite=None` without understanding cross-site implications
4. Storing user data in cookie value instead of server-side session
5. Not setting expiration — cookie persists indefinitely

### Secure Coding Recommendations

- Always set all three: `HttpOnly=True`, `Secure=True`, `SameSite=Lax`
- Use `SameSite=Strict` for highly sensitive cookies (breaks some legitimate flows)
- Generate session tokens with `secrets.token_urlsafe(32)` — minimum 128 bits of entropy
- Set `max_age` to the shortest acceptable session duration
- Implement session regeneration after authentication state changes

---

## 14. Session Management

**Severity:** 🟠 High

### Description

Sessions maintain user state across requests. Poor session management enables session fixation, session hijacking, and session replay attacks.

### How to Detect

- Check if session IDs are regenerated after login
- Check session timeout configuration
- Verify session storage is server-side (not client-side)
- Check if concurrent sessions are limited

### How to Prevent

```python
# ✅ SECURE — Session regeneration after authentication
async def login(request, credentials: LoginCredentials) -> Response:
    user = await authenticate(credentials)

    # ✅ Regenerate session ID to prevent fixation
    request.session.regenerate()

    request.session["user_id"] = user.id
    request.session["login_time"] = datetime.now(tz=timezone.utc).isoformat()
    request.session["ip_address"] = request.client.host

    return Response(status_code=200)

# ✅ SECURE — Session validation
async def validate_session(request) -> User:
    if "user_id" not in request.session:
        raise AuthenticationError("No session")

    # ✅ Check session age
    login_time = datetime.fromisoformat(request.session["login_time"])
    if datetime.now(tz=timezone.utc) - login_time > timedelta(hours=8):
        request.session.clear()
        raise AuthenticationError("Session expired")

    return await User.objects.get(id=request.session["user_id"])
```

### Code Review Checklist

- [ ] Session ID regenerated after successful authentication
- [ ] Session ID regenerated after privilege escalation
- [ ] Session timeout configured (idle timeout and absolute timeout)
- [ ] Session data stored server-side (not in cookie)
- [ ] Session invalidated on logout (server-side destruction)
- [ ] Concurrent session limits enforced (optional, high security)
- [ ] Session ID has sufficient entropy (≥128 bits)

### Common Mistakes

1. Not regenerating session ID after login (session fixation)
2. No idle timeout — abandoned sessions remain valid indefinitely
3. Storing sensitive data in client-side session cookies
4. Not invalidating session on logout (server-side reference remains)
5. Allowing unlimited concurrent sessions per user

### Secure Coding Recommendations

- Regenerate session ID on every authentication state change
- Set idle timeout (30 minutes) and absolute timeout (8 hours)
- Store sessions server-side (Redis, database) — cookies store only the session ID
- Clear session completely on logout — both client and server-side
- Bind sessions to client fingerprint (IP, User-Agent) for anomaly detection

---

## 15. Secrets Management

**Severity:** 🔴 Critical

### Description

Secrets include API keys, database passwords, encryption keys, certificates, and tokens. Hardcoded secrets are the most common critical vulnerability — they end up in version control, CI logs, error messages, and public repositories.

### How to Detect

- Search for hardcoded strings: `password=`, `api_key=`, `secret=`, `token=`
- Use `trufflehog`, `gitleaks`, or `detect-secrets` on the repository
- Check `.env` files in version control
- Search for base64-encoded strings that might be encoded credentials

### How to Prevent

```python
# ✅ SECURE — Secrets from environment
import os

DATABASE_URL = os.environ["DATABASE_URL"]            # Required — crashes if missing
API_KEY = os.environ["API_KEY"]                      # Required — crashes if missing
OPTIONAL_TOKEN = os.environ.get("OPTIONAL_TOKEN")    # Optional — returns None

# ✅ SECURE — Pydantic settings with secret fields
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: SecretStr
    api_key: SecretStr
    jwt_secret: SecretStr

    model_config = SettingsConfigDict(env_prefix="MYAPP_")

# SecretStr prevents accidental logging:
# str(settings.api_key) → "**********"
# settings.api_key.get_secret_value() → actual value

# ❌ VULNERABLE — Hardcoded secrets
DATABASE_URL = "postgresql://admin:p@ssw0rd@localhost/mydb"
API_KEY = "sk-1234567890abcdef"
```

### Code Review Checklist

- [ ] No secrets hardcoded in source code
- [ ] No secrets in version control (check history with `gitleaks`)
- [ ] `.env` is in `.gitignore` — `.env.example` is committed with placeholders
- [ ] Secrets loaded from environment variables or secret manager
- [ ] `SecretStr` or equivalent used to prevent accidental logging
- [ ] Secrets have rotation mechanism and expiration
- [ ] Default values are NEVER provided for secret parameters

### Common Mistakes

1. Committing `.env` files to version control
2. Hardcoding secrets "temporarily" and forgetting to remove them
3. Providing default values for secrets (`API_KEY = os.getenv("API_KEY", "test-key")`)
4. Logging secret values at DEBUG level
5. Storing secrets in client-side code (JavaScript, mobile apps)

### Secure Coding Recommendations

- Use `pydantic.SecretStr` for all secret configuration fields
- Never provide default values for secrets — force explicit configuration
- Run `gitleaks` or `detect-secrets` in CI pipeline
- Use dedicated secret management (Vault, AWS Secrets Manager, Azure Key Vault) in production
- Rotate secrets regularly and after any potential exposure

---

## 16. Environment Variables

**Severity:** 🟡 Medium

### Description

Environment variables configure runtime behavior and inject secrets. Mismanaged environment variables lead to configuration drift, secret exposure, and insecure defaults.

### How to Detect

- Check for `os.getenv()` calls without validation
- Verify `.env.example` exists and is current
- Check for environment-specific logic in code (not configuration)
- Verify secret environment variables are not logged

### How to Prevent

```python
# ✅ SECURE — Typed, validated configuration
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MYAPP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Non-secrets with defaults
    debug: bool = False
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)

    # Secrets without defaults (required)
    database_url: SecretStr
    api_key: SecretStr

# ❌ VULNERABLE — Unvalidated, untyped
debug = os.getenv("DEBUG")          # Returns string "true", not bool
timeout = os.getenv("TIMEOUT")      # Returns string, not float
api_key = os.getenv("API_KEY", "")  # Default empty string hides missing config
```

### Code Review Checklist

- [ ] All env vars parsed through typed configuration (Pydantic, dynaconf)
- [ ] Consistent naming prefix used (`MYAPP_*`)
- [ ] `.env.example` committed with all variables and placeholder values
- [ ] `.env` is in `.gitignore`
- [ ] No default values for secret variables
- [ ] Validation at startup — fail fast on misconfiguration
- [ ] Secure defaults for security-related variables (`DEBUG=False`, `VERIFY_SSL=True`)

### Common Mistakes

1. Using `os.getenv()` without type conversion (everything is a string)
2. Providing empty-string defaults for required variables (masks misconfiguration)
3. Different env var names across environments (no naming convention)
4. Not validating value ranges (negative timeout, port > 65535)
5. Committing `.env` to version control

### Secure Coding Recommendations

- Use a settings class with validation as the single source of configuration
- Prefix all variables with the project name to avoid collision
- Crash at startup if required variables are missing — do not silently continue
- Document every variable in `.env.example` with comments
- Use `SecretStr` for all sensitive values to prevent logging

---

## 17. TLS / Transport Security

**Severity:** 🔴 Critical

### Description

TLS protects data in transit from eavesdropping and tampering. Disabled TLS verification, weak protocols, and misconfigured certificates expose all communication to interception.

### How to Detect

- Search for `verify=False`, `ssl=False`, `CERT_NONE`, `check_hostname=False`
- Check minimum TLS version configuration
- Search for self-signed certificate acceptance
- Verify HSTS headers on HTTPS responses

### How to Prevent

```python
# ✅ SECURE — Default behavior (verification enabled)
async with httpx.AsyncClient() as client:
    response = await client.get("https://example.com")
    # TLS verification is ON by default — do not change this

# ✅ SECURE — Custom CA bundle
import ssl
ssl_context = ssl.create_default_context(cafile="/path/to/ca-bundle.crt")
async with httpx.AsyncClient(verify=ssl_context) as client:
    ...

# ✅ SECURE — HSTS header
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

# ❌ VULNERABLE — TLS verification disabled
async with httpx.AsyncClient(verify=False) as client:
    response = await client.get("https://example.com")

# ❌ VULNERABLE — SSL context with no verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
```

### Code Review Checklist

- [ ] TLS verification enabled on all HTTP clients (no `verify=False`)
- [ ] Minimum TLS version is 1.2 (no SSLv3, TLSv1.0, TLSv1.1)
- [ ] HSTS header set on all HTTPS responses
- [ ] No self-signed certificates in production
- [ ] Certificate pinning implemented for critical connections (optional)
- [ ] If `verify=False` exists, it requires explicit user opt-in and produces a warning log

### Common Mistakes

1. Disabling verification globally during development and forgetting to re-enable
2. Accepting self-signed certificates in production
3. Using TLS 1.0/1.1 (deprecated and vulnerable)
4. Not setting HSTS headers (allows protocol downgrade)
5. Catching SSL errors and continuing silently

### Secure Coding Recommendations

- Never set `verify=False` in library or core code — only in CLI with explicit user flag
- If `verify=False` is user-configurable, log a WARNING every time it's used
- Set HSTS header with `max-age=31536000` (1 year) and `includeSubDomains`
- Use system CA bundle by default — custom CA only when explicitly needed
- Pin certificates for connections to critical internal services

---

## 18. CORS Configuration

**Severity:** 🟡 Medium

### Description

Cross-Origin Resource Sharing controls which domains can make requests to your API. Misconfigured CORS can expose API endpoints to any website, enabling data theft through cross-origin requests.

### How to Prevent

```python
# ✅ SECURE — Specific origins
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com", "https://admin.example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)

# ❌ VULNERABLE — Wildcard origin with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # This combination is actually blocked by browsers,
                              # but the intent reveals a misunderstanding
)
```

### Code Review Checklist

- [ ] `allow_origins` uses explicit list — no wildcard `*` in production
- [ ] `allow_credentials=True` is only used with explicit origins
- [ ] `allow_methods` is restricted to actually needed methods
- [ ] `allow_headers` lists only required headers
- [ ] `Origin` header is not reflected back dynamically without validation
- [ ] Preflight responses are cached appropriately (`max_age`)

### Common Mistakes

1. Setting `allow_origins=["*"]` in production
2. Dynamically reflecting the `Origin` header as `Access-Control-Allow-Origin`
3. Allowing all methods and headers "for convenience"
4. Not setting `max_age` (excessive preflight requests)
5. Confusing CORS with authentication — CORS is not access control

### Secure Coding Recommendations

- Maintain an explicit allowlist of permitted origins
- Use environment-specific CORS configuration (dev: localhost, prod: specific domains)
- Test CORS configuration with `curl -H "Origin: https://evil.com"`
- Never dynamically reflect the Origin header without validation

---

## 19. Rate Limiting

**Severity:** 🟡 Medium

### Description

Rate limiting prevents abuse by restricting the number of requests a client can make in a time window. Without it, attackers can brute-force authentication, scrape data, or cause denial of service.

### How to Prevent

```python
# ✅ SECURE — Rate limiting implementation
from collections import defaultdict
from time import monotonic
from dataclasses import dataclass, field

@dataclass
class RateLimiter:
    max_requests: int
    window_seconds: float
    _buckets: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def is_allowed(self, client_id: str) -> bool:
        now = monotonic()
        bucket = self._buckets[client_id]

        # Remove expired entries
        self._buckets[client_id] = [t for t in bucket if now - t < self.window_seconds]

        if len(self._buckets[client_id]) >= self.max_requests:
            return False

        self._buckets[client_id].append(now)
        return True

# ✅ SECURE — Applied to authentication endpoint
limiter = RateLimiter(max_requests=5, window_seconds=60.0)

async def login(request):
    client_ip = request.client.host
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests")
    ...
```

### Code Review Checklist

- [ ] Authentication endpoints have rate limiting
- [ ] Rate limit uses appropriate identifier (IP, user ID, API key)
- [ ] `429 Too Many Requests` response includes `Retry-After` header
- [ ] Rate limiting is server-side (not client-side)
- [ ] Different limits for different endpoint tiers (auth stricter than read)
- [ ] Rate limit state is shared across instances (Redis for distributed)

### Common Mistakes

1. No rate limiting on authentication endpoints (brute-force possible)
2. Rate limiting by IP only (shared IPs affect innocent users)
3. Rate limit in memory only (resets on restart, not shared across instances)
4. Not returning `Retry-After` header (clients can't back off intelligently)
5. Applying identical limits to all endpoints

### Secure Coding Recommendations

- Use sliding window or token bucket algorithms
- Apply strictest limits to authentication and password reset endpoints
- Use Redis or equivalent for distributed rate limit state
- Return `Retry-After` header with the 429 response
- Consider tiered limits: unauthenticated < authenticated < admin

---

## 20. Input Validation

**Severity:** 🔴 Critical

### Description

Input validation is the first line of defense. Every data entry point — CLI arguments, HTTP parameters, file content, environment variables, database results — must be validated for type, length, range, format, and encoding.

### How to Prevent

```python
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse
import re

class ScanRequest(BaseModel):
    """Validated scan request."""
    url: str = Field(..., min_length=10, max_length=2048)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    concurrency: int = Field(default=10, ge=1, le=100)
    format: str = Field(default="json", pattern=r"^(json|text|html)$")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"URL must use http or https scheme, got: {parsed.scheme!r}")
        if not parsed.netloc:
            raise ValueError("URL must include a hostname")
        if re.search(r'[<>"{}|\\^`]', v):
            raise ValueError("URL contains invalid characters")
        return v

# ✅ SECURE — Validation at the boundary
request = ScanRequest(url=user_input_url, timeout=user_input_timeout)
# Pydantic raises ValidationError with details if invalid

# ❌ VULNERABLE — No validation
url = request.args.get("url")
timeout = float(request.args.get("timeout"))  # Crashes on non-numeric
response = await client.get(url, timeout=timeout)
```

### Code Review Checklist

- [ ] All user input validated at the entry point (API boundary)
- [ ] Type validation: correct data type enforced
- [ ] Length validation: min/max length for strings, min/max value for numbers
- [ ] Format validation: regex or parser for structured data (email, URL, date)
- [ ] Allowlist validation: fixed-set values checked against enum or set
- [ ] Encoding validation: UTF-8 enforced, invalid bytes rejected
- [ ] Validation errors return clear messages without leaking internals
- [ ] Validation happens before any processing or storage

### Common Mistakes

1. Validating in the frontend only (bypassed by API calls)
2. Using blocklists instead of allowlists (always incomplete)
3. Validating format but not length (long strings cause buffer/memory issues)
4. Validation at the wrong layer (deep inside business logic instead of boundary)
5. Trusting data from "internal" sources that originally came from user input

### Secure Coding Recommendations

- Use Pydantic models for all request validation
- Validate at the outermost boundary — before any processing
- Prefer allowlists over blocklists for format validation
- Set maximum lengths on ALL string inputs (defense against DoS)
- Return descriptive validation errors to help legitimate users fix their input

---

## 21. Output Encoding

**Severity:** 🟠 High

### Description

Output encoding transforms data to be safe for the destination context (HTML, JavaScript, URL, SQL, JSON, shell). The same data needs different encoding depending on where it will be rendered.

### How to Prevent

```python
# ✅ HTML context — auto-escape in templates
# Jinja2 with autoescape=True (default in Flask, FastAPI)
# {{ user_name }} → automatically escaped

# ✅ JSON context — json.dumps handles encoding
import json
safe_json = json.dumps({"name": user_input}, ensure_ascii=True)

# ✅ URL context — quote user input in URLs
from urllib.parse import quote
safe_url = f"https://example.com/search?q={quote(user_query)}"

# ✅ Shell context — avoid entirely, but if needed:
import shlex
safe_arg = shlex.quote(user_input)

# ❌ VULNERABLE — Unencoded output
html = f"<p>Hello, {user_name}</p>"  # XSS if user_name contains <script>

# ❌ VULNERABLE — Unquoted URL parameter
url = f"https://example.com/search?q={user_query}"  # Injection if query has &
```

### Code Review Checklist

- [ ] HTML output uses template engine with auto-escaping
- [ ] JSON output uses `json.dumps()` (not string concatenation)
- [ ] URL parameters are encoded with `urllib.parse.quote()`
- [ ] Shell arguments use `shlex.quote()` or argument lists (never `shell=True`)
- [ ] XML output uses proper XML serializer (not string building)
- [ ] SQL output uses parameterized queries (see §2)
- [ ] No manual encoding/escaping — use library functions

### Common Mistakes

1. Encoding for the wrong context (HTML encoding in JavaScript context)
2. Double-encoding (encoding already-encoded data)
3. Building output with string concatenation instead of serializers
4. Assuming encoding in one layer covers all layers
5. Forgetting to encode attribute values (different rules than element content)

### Secure Coding Recommendations

- Use context-appropriate encoding functions — never manual escaping
- Enable auto-escaping globally in template engines
- Build JSON with `json.dumps()`, URLs with `urllib.parse`, HTML with templates
- If building shell commands, use `subprocess.run()` with argument lists

---

## 22. Dependency Scanning

**Severity:** 🟠 High

### Description

Third-party dependencies introduce supply chain risk. Vulnerable, abandoned, or malicious packages can compromise the entire application. Regular scanning and version management is essential.

### How to Detect

- Run `pip-audit` or `safety check` on requirements
- Check CVE databases (NVD, GitHub Advisory, Snyk) for known vulnerabilities
- Monitor dependency age and maintenance status
- Verify package integrity (hashes in requirements)

### How to Prevent

```toml
# ✅ SECURE — Pinned versions in pyproject.toml
[project]
dependencies = [
    "httpx==0.27.0",
    "pydantic==2.7.0",
    "pydantic-settings==2.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest==8.2.0",
    "ruff==0.4.0",
    "mypy==1.10.0",
    "pip-audit==2.7.0",
    "bandit==1.7.0",
]
```

```yaml
# ✅ SECURE — CI pipeline scanning
# .github/workflows/security.yml
- name: Dependency audit
  run: pip-audit --strict --require-hashes

- name: Security linting
  run: bandit -r src/ -c pyproject.toml

- name: Check for known vulnerabilities
  run: safety check --full-report
```

### Code Review Checklist

- [ ] All dependency versions are pinned to exact versions
- [ ] No known critical or high CVEs in any dependency
- [ ] License compatibility verified for all dependencies
- [ ] `pip-audit` or equivalent runs in CI pipeline
- [ ] Lock file (`requirements.txt` with hashes) is committed
- [ ] New dependencies justified against evaluation criteria
- [ ] Transitive dependencies audited (not just direct)

### Common Mistakes

1. Using version ranges (`>=1.0`) in applications (unpredictable builds)
2. Never updating dependencies (accumulating known vulnerabilities)
3. Only scanning direct dependencies (transitive deps also have CVEs)
4. Adding dependencies without evaluating maintenance status
5. Not running security scans in CI (only running locally)

### Secure Coding Recommendations

- Pin exact versions in applications. Use ranges only in libraries.
- Run `pip-audit` in CI on every push
- Review dependency updates monthly — apply security patches within 48 hours
- Prefer dependencies with: active maintenance, permissive license, minimal transitive deps
- Use `pip install --require-hashes` in production for integrity verification

---

## 23. Least Privilege

**Severity:** 🟡 Medium

### Description

The Principle of Least Privilege states that every component, user, and process should have only the minimum permissions needed to perform its function. Over-privileged systems increase the blast radius of any compromise.

### How to Prevent

```python
# ✅ SECURE — Minimal database permissions
# Application user has SELECT, INSERT, UPDATE — not DROP, ALTER, GRANT
# CREATE USER app_user WITH PASSWORD '...';
# GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;

# ✅ SECURE — Minimal file permissions
from pathlib import Path
output_path = Path("reports/")
output_path.mkdir(mode=0o755, parents=True, exist_ok=True)
report_file = output_path / "report.json"
report_file.write_text(content)
report_file.chmod(0o644)  # Owner read/write, others read-only

# ✅ SECURE — Minimal API scope
REQUIRED_SCOPES = ["read:findings", "write:reports"]  # Not "admin:*"

# ✅ SECURE — Run as non-root in Docker
# Dockerfile
# USER appuser  (not root)

# ❌ VULNERABLE — Running as root
# Dockerfile: USER root
# App has access to entire filesystem and all OS capabilities
```

### Code Review Checklist

- [ ] Application does not require root/admin privileges
- [ ] Database connections use least-privilege accounts
- [ ] API tokens/keys have minimal scopes
- [ ] File permissions are restrictive (no world-writable files)
- [ ] Docker containers run as non-root user
- [ ] Network access is restricted to required hosts/ports
- [ ] Temporary privilege escalation is logged and time-limited

### Common Mistakes

1. Running applications as root "because it's easier"
2. Using database admin credentials for application connections
3. Requesting wildcard API scopes (`*:*`) instead of specific permissions
4. Creating world-writable temporary directories
5. Granting broad IAM policies in cloud environments

### Secure Coding Recommendations

- Create dedicated service accounts with minimal permissions
- Request only the API scopes you actually need
- Use read-only filesystem mounts where possible
- Drop capabilities in Docker: `--cap-drop=ALL --cap-add=NET_BIND_SERVICE`
- Audit permissions regularly — remove unused grants

---

## 24. Logging Security

**Severity:** 🟠 High

### Description

Logging is critical for security monitoring and incident response, but logs themselves are an attack surface. Sensitive data in logs is a data breach. Insufficient logging makes incident response impossible.

### How to Prevent

```python
import logging

logger = logging.getLogger(__name__)

# ✅ SECURE — Log security events with context
logger.warning(
    "Authentication failed: user=%s ip=%s attempts=%d",
    username,
    client_ip,
    failed_attempts,
)

# ✅ SECURE — Log authorization failures
logger.warning(
    "Authorization denied: user=%s resource=%s action=%s",
    user_id,
    resource_id,
    requested_action,
)

# ✅ SECURE — Redact sensitive fields
def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    sensitive = {"authorization", "cookie", "x-api-key", "proxy-authorization"}
    return {
        k: "***REDACTED***" if k.lower() in sensitive else v
        for k, v in headers.items()
    }

logger.debug("Response headers: %s", redact_headers(response.headers))

# ❌ VULNERABLE — Logging secrets
logger.debug("Auth header: %s", request.headers["Authorization"])
logger.info("Connecting with password: %s", db_password)
logger.error("Request failed. Full request: %s", request.body)
```

### Code Review Checklist

- [ ] Authentication successes and failures are logged
- [ ] Authorization failures are logged with user, resource, and action
- [ ] No passwords, tokens, API keys, or session IDs in logs
- [ ] No PII (email, SSN, phone) in logs without consent
- [ ] Request/response bodies are not logged (may contain sensitive data)
- [ ] Log injection is prevented (newlines stripped from user input in logs)
- [ ] Logs include timestamps, severity, source module, and correlation ID
- [ ] Security-relevant events are logged at WARNING or higher

### Common Mistakes

1. Logging full HTTP headers (contains `Authorization`, `Cookie`)
2. Logging request bodies (may contain passwords, PII)
3. Not logging authentication failures (can't detect brute force)
4. Including user input directly in log messages (log injection)
5. Logging at DEBUG level in production (performance impact, data exposure)

### Secure Coding Recommendations

- Build a redaction utility that strips known sensitive fields before logging
- Log all authentication and authorization events
- Sanitize user input before including in log messages (strip newlines)
- Use structured logging (JSON) for machine-parseable security events
- Set production log level to INFO or WARNING — never DEBUG

---

## 25. Secure Defaults

**Severity:** 🟡 Medium

### Description

Secure defaults ensure that the application is safe out of the box — without requiring the deployer to configure security. If a configuration is not explicitly set, the default must be the secure option, not the convenient one.

### How to Prevent

```python
# ✅ SECURE — Defaults are restrictive
class Settings(BaseSettings):
    debug: bool = False                      # Debug OFF by default
    verify_ssl: bool = True                  # TLS verification ON by default
    cors_origins: list[str] = []             # No CORS origins by default
    session_cookie_secure: bool = True       # Secure cookies by default
    session_cookie_httponly: bool = True      # HttpOnly by default
    session_cookie_samesite: str = "Lax"     # SameSite by default
    max_upload_size_bytes: int = 10_485_760  # 10 MB limit by default
    rate_limit_requests: int = 100           # Rate limiting ON by default
    rate_limit_window_seconds: int = 60
    allowed_hosts: list[str] = []            # No hosts allowed by default
    log_level: str = "INFO"                  # Not DEBUG by default

# ❌ INSECURE — Defaults are permissive
class Settings(BaseSettings):
    debug: bool = True                       # Debug ON — exposes internals
    verify_ssl: bool = False                 # TLS OFF — MITM possible
    cors_origins: list[str] = ["*"]          # All origins — no protection
    max_upload_size_bytes: int = 0           # No limit — DoS possible
    allowed_hosts: list[str] = ["*"]         # All hosts — host header injection
```

### Code Review Checklist

- [ ] `DEBUG=False` by default
- [ ] `VERIFY_SSL=True` by default
- [ ] `CORS_ORIGINS=[]` by default (empty, not wildcard)
- [ ] `ALLOWED_HOSTS=[]` by default (empty, not wildcard)
- [ ] Session cookies have `Secure=True`, `HttpOnly=True`, `SameSite=Lax` by default
- [ ] File upload limits are set by default
- [ ] Rate limiting is enabled by default
- [ ] Authentication is required by default (endpoints are protected, not open)
- [ ] Verbose error messages disabled by default (no stack traces to users)
- [ ] Logging level is INFO by default (not DEBUG)

### Common Mistakes

1. Setting `DEBUG=True` as default for "developer convenience"
2. Allowing all CORS origins by default
3. Disabling TLS verification by default
4. No upload size limit by default
5. Detailed error messages in production by default

### Secure Coding Recommendations

- Apply the principle: "secure by default, relaxed by explicit configuration"
- If a security setting is weakened, produce a WARNING log on every startup
- Make insecure options require deliberate action (flag, env var, config file)
- Document the security implications of every configurable security setting
- Test with default configuration — it should be production-safe

---

## Appendix A — Security Scanning Tools

| Tool | Purpose | Usage |
|---|---|---|
| `bandit` | Python security linter (SAST) | `bandit -r src/ -c pyproject.toml` |
| `pip-audit` | Dependency vulnerability scanning | `pip-audit --strict` |
| `safety` | Dependency CVE checking | `safety check --full-report` |
| `gitleaks` | Secret detection in git history | `gitleaks detect --source .` |
| `detect-secrets` | Secret detection in files | `detect-secrets scan` |
| `semgrep` | Pattern-based code scanning | `semgrep --config auto src/` |
| `mypy --strict` | Type safety (prevents type confusion) | `mypy --strict src/` |
| `trivy` | Container image scanning | `trivy image myapp:latest` |

---

## Appendix B — Incident Response Checklist

If a security vulnerability is discovered in code produced by an AI agent:

1. **STOP** all development work on affected components
2. **ASSESS** severity using the CVSS or internal severity scale
3. **CONTAIN** — if deployed, determine if the vulnerability is exploitable
4. **FIX** — apply the minimum targeted fix
5. **VERIFY** — confirm fix resolves the vulnerability and passes all tests
6. **SCAN** — run full security scan to check for similar patterns
7. **REVIEW** — audit recent AI-generated code for the same vulnerability class
8. **DOCUMENT** — record the vulnerability, root cause, and fix in security log
9. **UPDATE** — if the vulnerability represents a pattern, update this handbook

---

*End of document. Security controls are non-negotiable. No feature deadline justifies shipping a known vulnerability.*
