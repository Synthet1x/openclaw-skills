# Zero-Leakage Credential Standard (Cookies & Tokens)

This document establishes the security protocol for capturing, storing, and utilizing browser session cookies and API tokens within AI monitoring workflows. Adherence to these practices ensures protection against credential exposure and satisfies ClawHub security scanners (`skillspector`, `llm`, `vt`).

---

## 1. Threat Model & Vulnerability Vectors

When automating quota checks against subscription portals, credentials face four primary exposure vectors:

1. **Process Argument Leakage (`[TT5]`):**
   Passing cookies or tokens via command-line arguments (e.g., `curl -H "Cookie: ..."` or `python script.py --token ...`) exposes secrets in plaintext to `ps aux`, process monitoring daemons, system logs, and shell history (`~/.bash_history`).
   *Mitigation:* Never pass secrets via CLI arguments. Secrets must be read strictly from environment variables or dedicated restricted configuration files.

2. **Insecure Storage & Permissive Permissions (`[PE3]`):**
   Saving credentials in world-readable files or shared directories allows local privilege escalation and credential harvesting by unauthorized local processes.
   *Mitigation:* All credential stores must reside under `~/.config/<service>/` with mandatory file permissions `chmod 600` (read/write by owner only) and directory permissions `chmod 700`.

3. **Indiscriminate Cookie Jar Dumping:**
   Exporting entire browser profiles or full `cookies.txt` files bundles unrelated sensitive cookies (banking, Google session, primary email, SSO tokens) together with the target service cookie.
   *Mitigation:* Selective extraction. Extract ONLY the exact cookie required for the target API session (e.g., `session_id`, `__Secure-` auth token), discarding all other cookies.

4. **Credential Egress & Unpinned Forwarding (`[SQP-2]`, `[E1]`):**
   Forwarding authorization headers through unverified intermediaries, logging proxies, or third-party webhooks causes credential theft.
   *Mitigation:* Hardcoded origin domain pinning. HTTPS requests containing session credentials must strictly validate and target only official, pinned provider hostnames.

---

## 2. Safe Cookie Extraction from Browser

When an AI subscription lacks a public developer API and requires a web session cookie:

### Step-by-Step Selective Extraction (Chrome / Edge / Firefox)
1. Open the target AI portal in your browser and log in.
2. Press `F12` to open Developer Tools, then navigate to the **Application** (Chrome/Edge) or **Storage** (Firefox) tab.
3. In the left sidebar, expand **Cookies** and select the target domain (e.g., `https://chat.example.com`).
4. Locate the specific authentication cookie key (commonly `__Secure-auth`, `session`, `jwt`, `token`, or `auth_token`).
5. Double-click the **Value** cell and copy *only* that single string.
6. Immediately close Developer Tools.

*Prohibition:* Never use third-party "Cookie Exporter" extensions that dump all domain cookies to disk.

---

## 3. Secure Local Storage (`chmod 600`)

Store the extracted token or cookie in a dedicated, isolated JSON or text file.

### Safe Initialization
```bash
# 1. Create isolated configuration directory
mkdir -p ~/.config/ai-quota-dashboard
chmod 700 ~/.config/ai-quota-dashboard

# 2. Write configuration with dummy or restricted content
touch ~/.config/ai-quota-dashboard/credentials.json
chmod 600 ~/.config/ai-quota-dashboard/credentials.json
```

### Credentials Schema (`~/.config/ai-quota-dashboard/credentials.json`)
```json
{
  "providers": {
    "custom_service": {
      "cookie_name": "session_id",
      "cookie_value": "PASTE_TOKEN_HERE",
      "pinned_domain": "api.service.com"
    }
  }
}
```

---

## 4. Safe Ingestion in Python / Scripts

Always load credentials via direct file I/O or environment variables. Enforce permission audits inside scripts before reading:

```python
import os
import stat
import json

def load_secure_credentials(config_path: str) -> dict:
    expanded = os.path.expanduser(config_path)
    if not os.path.exists(expanded):
        raise FileNotFoundError(f"Config {expanded} not found.")

    # Audit file permissions (must be 0600 or 0400)
    file_stat = os.stat(expanded)
    mode = stat.S_IMODE(file_stat.st_mode)
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise PermissionError(
            f"Security Violation: {expanded} has insecure permissions {oct(mode)}. "
            f"Run `chmod 600 {expanded}` before proceeding."
        )

    with open(expanded, "r", encoding="utf-8") as f:
        return json.load(f)
```

---

## 5. Network Egress Security & Domain Pinning

All HTTP clients communicating with provider endpoints must enforce strict TLS and domain verification:

```python
import urllib.parse
import urllib.request

def safe_request(url: str, headers: dict, pinned_domain: str):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Insecure scheme: {parsed.scheme}. HTTPS is mandatory.")
    if parsed.netloc != pinned_domain:
        raise ValueError(
            f"Domain Mismatch: Attempted to send credentials to {parsed.netloc}, "
            f"expected strictly pinned domain {pinned_domain}."
        )

    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=10)
```
