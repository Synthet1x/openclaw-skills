---
name: ai-quota-dashboard
description: "лимиты нейросетей, quota dashboard, остатки токенов, подписки и куки. Real-time multi-provider AI quota dashboard with secure cookie handling and reverse-engineering guide."
---

# AI Quotas & Subscription Limits Dashboard

Real-time telemetry, monitoring, and automated tracking for AI model quotas, subscription reset times, and API token balances across cloud and local providers (Google Antigravity/Cloud Code, ElevenLabs, OpenRouter, xAI/Grok, Anthropic, OpenAI, Perplexity, and custom platforms).

---

## 1. Zero-Leakage Credential Standard (Mandatory Security)

To pass automated security audits (`skillspector`, `llm`, `vt`) and safeguard user privacy, all credential operations must strictly follow these rules:

1. **Zero Process Argument Leakage (`[TT5]`):**
   - Never pass session cookies or API tokens via command-line arguments (`argv`). CLI arguments are visible to `ps aux`, process accounting daemons, and system audit logs.
   - Credentials must be read strictly from isolated files or environment variables.

2. **Strict Filesystem Isolation (`[PE3]`):**
   - All credentials files must reside in dedicated directories with restrictive permissions (`chmod 700 ~/.config/ai-quota-dashboard` and `chmod 600 credentials.json`).
   - Collector scripts must audit permissions and refuse execution if files are world-readable.

3. **Strict Origin Domain Pinning (`[SQP-2]`, `[E1]`):**
   - Outbound HTTP requests bearing session cookies must enforce strict HTTPS and validate that the request target matches the pinned official provider domain. Requests to mismatched hosts or unverified proxies are rejected.

4. **Selective Cookie Extraction (No Jar Dumps):**
   - Extract only the exact authentication cookie (e.g., `session_id`, `__Secure-auth`) required for the specific API. Never export the entire browser profile or full `cookies.txt` jar.

For complete specifications and audit scripts, see [references/security-cookie-guide.md](references/security-cookie-guide.md).

---

## 2. API Reverse Engineering & Quota Discovery

When tracking an AI provider without public usage documentation:

1. **Network Trace Isolation:**
   - Open the provider web portal in your browser, log in, and open DevTools (`F12`).
   - Switch to the **Network** tab, filter by `Fetch/XHR`, and refresh the usage or settings view.
2. **Key Filter Terms:**
   - Filter requests by `quota`, `usage`, `limits`, `subscription`, `billing`, or `models`.
3. **Analyze Authentication Type:**
   - **Bearer Access Token:** Check if accompanied by a `refresh_token` endpoint.
   - **Session Cookie:** Note required headers (`User-Agent`, `Origin`, CSRF tokens).
4. **Normalize Telemetry:**
   - Map response fields to: `used`, `limit`, `percent_used`, `unit`, and `resets_at` (ISO 8601 UTC).

For endpoint patterns and examples, see [references/api-reverse-engineering.md](references/api-reverse-engineering.md).

---

## 3. Setup & Deployment Procedure

### Step 1: Initialize Secure Configuration
```bash
# 1. Create directory with restricted permissions
mkdir -p ~/.config/ai-quota-dashboard
chmod 700 ~/.config/ai-quota-dashboard

# 2. Copy template and secure credentials file
cp config.example.json ~/.config/ai-quota-dashboard/config.json
chmod 600 ~/.config/ai-quota-dashboard/config.json
```

Populate `~/.config/ai-quota-dashboard/config.json` with your provider keys or extracted session cookies.

### Step 2: Run Telemetry Collection
```bash
python3 scripts/quota_collector.py
```
Verification: Confirm that `/tmp/ai_quota_cache.json` is generated with valid JSON and non-empty provider arrays.

### Step 3: Run the Dashboard Web Service
Deploy a lightweight server or systemd service to host `templates/dashboard.html` and serve `/tmp/ai_quota_cache.json` over a local port (e.g., `8885`).

Systemd unit template (`/etc/systemd/system/quota-dashboard.service`):
```ini
[Unit]
Description=AI Quotas & Limits Realtime Dashboard
After=network.target

[Service]
Type=simple
User=%I
WorkingDirectory=%h/.openclaw/workspace/orli
ExecStart=/usr/bin/python3 -m http.server 8885 --directory %h/.openclaw/agents/orli/agent/workshop-skills/ai-quota-dashboard/templates
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 4. Verification Checklist

- [ ] `config.json` has permissions `0600` (`ls -l ~/.config/ai-quota-dashboard/config.json`).
- [ ] No tokens or cookies appear in `ps aux` or shell history.
- [ ] Provider endpoints match pinned domain verification checks.
- [ ] Telemetry updates periodically and displays clean status indicators in the dashboard.
