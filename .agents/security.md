# Security guidelines for agents

This document summarizes the core security rules that must be followed during software development to prevent major vulnerabilities and to design and implement secure services.

---

## 1. Principle of Least Privilege & Access Control

* **Default Deny Policy:** By default, all resources and endpoints should be inaccessible unless explicitly allowed. Access privileges should be granted incrementally, starting with the narrowest scope.
* **Tenant & User Isolation (Preventing IDOR):** In multi-tenant environments, every query for reading, writing, or deleting data must filter by user or tenant identifiers (e.g., `user_id`, `tenant_id`, `team_id`) securely derived from the session context. Never trust tenant identifiers supplied directly by client-side inputs or query parameters.
* **Ownership & Sensitive State Protection (Preventing Mass Assignment):**
    * Fields representing critical attributes such as `created_by`, `role`, `status`, or `organization_id` must be marked as read-only.
    * Do not update these fields by directly binding client-provided objects. Instead, set them explicitly on the server-side from a trusted context.
* **Consistency in Authorization Across API Methods:** Ensure authorization logic is consistently enforced across all HTTP methods (e.g., `POST`, `PUT`, `PATCH`, `GET`, `DELETE`) and custom action endpoints. It is common to secure creation logic but neglect update or deletion logic.
* **Bulk/Batch Endpoint Validation:** When processing batch operations, validate ownership and permissions for each item individually. Do not verify only the first item and trust the rest of the batch.
* **Preserving Privilege Scopes in Background Tasks:** Asynchronous background tasks (e.g., Celery, Temporal) must inherit the authorization scope of the user who initiated the action. Do not silently escalate background executions to superuser privileges.

---

## 2. Injection Prevention

* **SQL Injection (Value Context):** Never construct SQL queries using string formatting, concatenation, or f-strings with user-controlled input. Always use **parameterized queries / prepared statements** provided by the database driver or ORM.
* **Dynamic Identifier Handling (Identifier Context):** If table or column names must be dynamic, parameterized queries cannot be used. Instead, apply one of the following approaches:
    1. Validate the user-supplied field name against a strict **allowlist**.
    2. Safely escape the input using database-specific identifier escaping utilities.
* **ORM Filter Key Injection:** Avoid allowing user-controlled inputs to dynamically define ORM filter keys (e.g., `filter(**{f"{key}__contains": value})`). Attackers can leverage relationship traversals (e.g., `user__password`) to extract sensitive fields. Always validate dynamic keys against an **allowlist**.
* **Command Injection:** When running OS commands (e.g., Python `subprocess`), disable the shell flag (e.g., `shell=False`) and pass the program name and arguments as a list. Do not interpolate user input directly into shell command strings.
* **Path Traversal:** When reading or writing files using user-supplied paths, validate that the input does not contain `..` or absolute paths, ensuring that the target path remains restricted to the designated root directory.
* **Archive Extraction (Zip Slip):** Prior to extracting files from archives (e.g., Zip, Tar), verify that the member paths do not contain relative sequences like `..` or absolute path prefixes to prevent writing files to arbitrary locations.
* **XXE (XML External Entity Resolution) Prevention:** Configure XML parsers to disable external entity resolution (`resolve_entities=False`) and network access (`no_network=True`) to prevent file exposure and Server-Side Request Forgery (SSRF).
* **Cross-Site Scripting (XSS):** Escape all user-controlled data when rendering it in browser templates. If rendering HTML or Markdown is required, run the input through a trusted HTML sanitizer library to strip out malicious scripts and tags.

---

## 3. Authentication & Session Management

* **No Hardcoded Credentials:** Never store API keys, encryption salts, JWT secrets, or DB passwords in source code or Git repositories. Use environment variables, configuration encryption, or dedicated Secret Managers.
* **Secure Password Hashing & Brute-Force Defense:**
    * Store passwords using strong, salted one-way hashing algorithms (e.g., bcrypt, Argon2, PBKDF2).
    * Use **constant-time comparison** algorithms (e.g., `constant_time_compare`, `hmac.compare_digest`) for credentials and tokens to defend against timing attacks.
* **Session Lifecycle Control:**
    * Revoke and invalidate all active sessions and tokens immediately upon security events such as password changes, email address updates, multi-factor authentication (MFA) changes, or user-initiated "log out from all devices" requests.
    * Perform **session ID rotation** upon successful login to prevent Session Fixation attacks.
    * Secure session cookies by applying the `HttpOnly`, `Secure`, and `SameSite` flags.
* **Multi-Factor Authentication (MFA) Protection:**
    * Implement strict rate limiting and lockout policies on OTP (One-Time Password) verification endpoints to prevent brute-force attacks.
    * Ensure that endpoints for disabling or modifying MFA are guarded by rigorous re-authentication checks.
* **Webhook & Request Signature Verification:** Validate incoming webhooks or signed requests using HMAC signatures compared with a constant-time comparison helper. Include timestamps and nonces to mitigate replay attacks.

---

## 4. Preventing Sensitive Data Exposure

* **Preventing Exposure in Logs and Errors:** Filter sensitive information, such as Personally Identifiable Information (PII), API tokens, password reset links, and credit card numbers, out of application logs, error-tracking systems (e.g., Sentry), and user-facing error messages.
* **Restricting Secrets in URL Query Strings:** Do not include access tokens, OAuth codes, or password reset tokens in URL query parameters. They can be exposed via browser history, proxy server logs, or HTTP Referer headers.
* **Avoiding Local Storage for Session Material:** Storing authentication tokens in `localStorage` or `sessionStorage` leaves them vulnerable to extraction via XSS. Opt for `HttpOnly` cookies to store sensitive session credentials.

---

## 5. Business Logic & DoS Protection

* **Mitigating Race Conditions:** Ensure that "read-then-write" transactions (e.g., inventory deduction, balance updates, coupon usage) are protected against concurrent access using database locks (`SELECT FOR UPDATE`), optimistic locking (versioning), or unique constraints.
* **Pagination Bypass Prevention:** Force a maximum limit (Max Limit) and a reasonable default limit on all list endpoints. Accepting arbitrary pagination sizes (e.g., `?limit=9999999`) can exhaust database memory and CPU resources, causing Denial of Service (DoS).
* **Resource Exhaustion Defense (Decompression Bombs, etc.):**
    * Enforce size limits when decompressing user-uploaded archives to protect disk and memory.
    * Avoid performing high-cost operations (e.g., image resizing, complex regex matches, external API calls) synchronously before user authentication is completed, as they present low-cost vectors for Denial of Service amplification.

---

## 6. Web Boundary & Client Security

* **Open Redirect Prevention:** Validate redirect targets (e.g., `next` or `redirect_uri` parameters) against an allowlist of permitted domains or enforce relative path redirects (starting with `/`) to prevent phishing redirects.
* **Secure CORS Configuration:**
    * Do not configure `Access-Control-Allow-Origin: *` in combination with `Access-Control-Allow-Credentials: true`.
    * Use an allowlist to dynamically validate the `Origin` header instead of reflecting the requested origin unchecked.
* **Host Header Injection Mitigation:** Do not construct absolute URLs (e.g., for password reset links in emails) using the HTTP Request Host header directly (e.g., `request.get_host()`). Build them using validated hostnames configured in server environment settings.
* **CORS iframe & postMessage Verification:** When using cross-window messaging (`postMessage`), strictly validate `event.origin` against an allowlist and verify the message structure. Avoid weak pattern checks like `indexOf` or unanchored regular expressions.

---

## 7. AI & LLM Integration Security

* **Indirect Prompt Injection:** When feeding external data (e.g., web scraping outputs, email bodies, file contents) into an LLM context, isolate this untrusted content to ensure the model does not interpret it as system instructions.
* **Server-Side Validation of Model Actions (Tool Call validation):** Do not trust parameters or resource IDs (e.g., `project_id`, `user_id`) provided by the LLM during tool/function calls. Re-validate ownership and access permissions on the server side based on the active user session.
* **User Confirmation for Destructive Actions:** Actions with external side effects or destructive outcomes (e.g., deleting data, sending emails, initiating payments) must not be executed automatically by the model. Always prompt for explicit user confirmation in the UI before execution.
* **Secure Output Rendering:**
    * Sanitize model outputs to prevent Cross-Site Scripting (XSS). Filter out `<iframe>`, `<script>`, and tracking images (`<img>` tags attempting CSRF/data leakage).
    * Strip malicious schemes such as `javascript:` or `data:` from model-generated links.

---

## 8. Hardening Django Production Environment Settings

Django offers high development convenience, but failing to change settings during deployment exposes source code and environment variables.
* **Enforcing DEBUG = False and Error Page Isolation:** If `DEBUG = True` is left active in production, database passwords, API keys, and source code paths will be exposed on the browser when a 500 error occurs. It must be set to `False` in production, and custom error pages should be rendered instead.
* **Changing Admin Page Address:** The default `/admin/` path is the primary target for brute-force attacks. The admin URL must be changed to a randomized string (e.g., `/secret-zone-drf-99/`) in `urls.py`.
* **Enforcing Security Middleware and Cookie Encryption:** Assuming HTTPS (SSL) is applied, settings such as `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, and `CSRF_COOKIE_SECURE = True` must be configured to prevent network sniffing.

---

## 9. Preventing Redis Unauthorized Access and Remote Code Execution (RCE)

Redis is designed assuming a trusted network environment (No Auth by default). Improper configurations in Docker can lead to full host server compromise.
* **Setting Password via requirepass:** A strong authentication password must be set in the Redis configuration file (`redis.conf`) or the Docker execution command.
* **Restricting Port Exposure (Critical):** Redis ports must not be forwarded externally in `docker-compose.yml` (e.g., avoid `ports: - "6379:6379"`). Exposing Redis to the internet makes the system vulnerable to ransomware and malware infections.

---

## 10. Docker Container Network Isolation and Privilege Restriction

If containerization is used, infrastructure-level security boundaries must be explicitly defined.
* **Network Isolation:** Only the Django (or Nginx) container that interacts with external users should expose external ports (e.g., 80, 443). MySQL and Redis must close external ports and be isolated to communicate with Django only within an internal virtual network (`networks`).
* **Non-Root User Execution:** The `Dockerfile` must define a non-root user (e.g., `USER django_user`) at the end of the file. Running applications as `root` by default allows attackers to potentially compromise the entire host server if a container escape vulnerability occurs.

---

## 11. Database (MySQL) Connection Transmission Encryption

* **Enforcing TLS/SSL Connection:** If the Django container and the MySQL container reside on different physical servers or in a cloud environment (e.g., AWS RDS), query data transmitted between them may be exposed in plain text. SSL settings must be added to the Django DB settings (`OPTIONS`) to encrypt all query data in transit.

