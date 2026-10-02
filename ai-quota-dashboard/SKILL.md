---
name: ai-quota-dashboard
description: "лимиты нейросетей, quota dashboard, остатки токенов, подписки и куки. Real-time multi-provider AI quota dashboard with secure token management and telemetry guide."
---

# AI Quotas & Subscription Limits Dashboard

Real-time telemetry, monitoring, and automated tracking for AI model quotas, subscription reset times, and API token balances across cloud and self-hosted providers (Google Antigravity, ElevenLabs, OpenRouter, xAI/Grok, Anthropic, OpenAI, Perplexity, LiteLLM, Ollama, and custom gateways).

---

## 1. Zero-Leakage Credential Standard (Mandatory Security)

To pass automated security audits (`skillspector`, `llm`, `vt`) and safeguard user privacy, all credential operations must strictly follow these rules:

1. **Zero Process Argument Leakage (`[TT5]`):**
   - Never pass API keys, tokens, or headers via command-line arguments (`argv`). CLI arguments are visible to `ps aux`, process accounting daemons, and system audit logs.
   - Credentials must be read strictly from isolated configuration files or environment variables.

2. **Strict Filesystem Isolation (`[PE3]`):**
   - All credentials files must reside in dedicated directories with restrictive permissions (`chmod 700 ~/.config/ai-quota-dashboard` and `chmod 600 config.json`).
   - Collector scripts must audit permissions and refuse execution if files are world-readable.

3. **Strict Origin Domain Pinning (`[SQP-2]`, `[E1]`):**
   - Outbound HTTP requests bearing authorization headers must enforce strict HTTPS and validate that the request target matches the pinned official provider domain. Requests to mismatched hosts or unverified proxies are rejected.

4. **Official Developer Credentials & Service Tokens:**
   - Always prioritize official developer API keys or read-only service tokens configured in your provider/gateway dashboard.
   - Do not scrape or extract third-party browser session cookies.

For complete specifications and audit scripts, see [references/security-cookie-guide.md](references/security-cookie-guide.md).

---

## 2. Telemetry Ingestion & No-Limit Fallback Strategies

When integrating an AI provider without public quota countdown documentation:

1. **Standard Telemetry Ingestion:**
   - Query documented developer endpoints (e.g., OpenRouter `/api/v1/credits`, ElevenLabs `/v1/user/subscription`, Ollama `/api/tags`).
   - Map response fields to standard telemetry: `used`, `limit`, `percent_used`, `unit`, and `resets_at` (ISO 8601 UTC).

2. **When Endpoints Lack Explicit Limit Numbers:**
   - **Unit Economics (Reverse Calculation):** When only account balance is returned (e.g. pay-as-you-go APIs), calculate remaining capacity by dividing balance by unit request price (`remaining = balance / unit_price`).
   - **Rolling Window Timers:** When limits operate on rolling intervals (e.g. 50 requests per 3 hours), track the cycle start timestamp locally and display an active countdown timer to reset.
   - **Local Usage Telemetry:** For self-hosted gateways without billing endpoints, aggregate runtime token usage statistics locally.
   - **Session Validity Heartbeat:** For flat-rate or unlimited tiers, verify endpoint availability via lightweight status ping (200 OK) and display an active pulse badge.

For full architecture details, see [references/api-reverse-engineering.md](references/api-reverse-engineering.md).

---

## 3. Deployment & Networking Scenarios

The dashboard supports three operational modes:

1. **Strictly Local LAN (Home / Office Wi-Fi):**
   - Bind server to `0.0.0.0:8885` and restrict firewall to local subnet. Access via `http://<LAN_IP>:8885`.
2. **Remote Access Without Domain (External IP / VPN):**
   - Use encrypted WireGuard/Tailscale mesh VPN (zero router ports exposed) or router Port Forwarding with IP restrictions. Alternatively, use secure Cloudflare Tunnels.
3. **Custom Domain with HTTPS & Password Protection:**
   - Nginx reverse proxy with Certbot Let's Encrypt SSL. Enforce Basic Auth (`htpasswd`) so public bots cannot scrape private quota telemetry.

For complete Nginx blocks, firewall rules, and VPN instructions, see [references/networking-deployment.md](references/networking-deployment.md).

---

## 4. Mobile Standalone App (PWA Shortcut)

The dashboard includes full Progressive Web App support to run as a standalone fullscreen app on iOS and Android:
- **iPhone / iPad (Safari):** Tap the **Share** button (box with upward arrow) -> select **"Add to Home Screen"** -> Tap **"Add"**.
- **Android (Chrome):** Tap **Menu** (three dots) -> select **"Install app"** or **"Add to Home screen"**.

Launches in fullscreen mode with an app icon and dark theme status bar.

---

## 5. Verification Checklist

- [ ] `config.json` has permissions `0600` (`ls -l ~/.config/ai-quota-dashboard/config.json`).
- [ ] No tokens or keys appear in `ps aux` or shell history.
- [ ] Provider endpoints match pinned domain verification checks.
- [ ] Dashboard is accessible via LAN IP, VPN, or reverse proxy.
- [ ] PWA manifest loads cleanly and installs to mobile home screen.
