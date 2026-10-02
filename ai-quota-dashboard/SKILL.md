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
   - All credentials files must reside in dedicated directories with restrictive permissions (`chmod 700 ~/.config/ai-quota-dashboard` and `chmod 600 config.json`).
   - Collector scripts audit permissions and refuse execution if files are world-readable.

3. **Strict Origin Domain Pinning (`[SQP-2]`, `[E1]`):**
   - Outbound HTTP requests bearing session cookies must enforce strict HTTPS and validate that the request target matches the pinned official provider domain. Requests to mismatched hosts or unverified proxies are rejected.

4. **Selective Cookie Extraction (No Jar Dumps):**
   - Extract only the exact authentication cookie (e.g., `session_id`, `__Secure-auth`) required for the specific API. Never export the entire browser profile or full `cookies.txt` jar.

For complete specifications and audit scripts, see [references/security-cookie-guide.md](references/security-cookie-guide.md).

---

## 2. API Reverse Engineering & No-Limit Fallback Strategies

When tracking an AI provider without public usage documentation:

1. **Network Trace Isolation:**
   - Open the provider web portal, log in, and open DevTools (`F12`).
   - Switch to the **Network** tab, filter by `Fetch/XHR`, and refresh the usage or settings view.
   - Filter requests by `quota`, `usage`, `limits`, `subscription`, `billing`, or `models`.

2. **When Endpoints Lack Explicit Limit Numbers:**
   - **Unit Economics (Reverse Calculation):** When only account balance is returned (e.g. Perplexity), calculate capacity by dividing balance by request unit price (`remaining = balance / unit_price`).
   - **Rolling Window Timers:** When limits are time-bound (e.g. 50 msgs / 3 hours), track the cycle start timestamp locally and display an active countdown timer to reset.
   - **Local Log Aggregation:** When no billing endpoint exists, aggregate usage locally from runtime token usage statistics.
   - **Session Validity Heartbeat:** For flat-rate/unlimited accounts, verify session validity via lightweight ping (200 OK vs 401/403) and display an active status badge.

For full reverse-engineering patterns, see [references/api-reverse-engineering.md](references/api-reverse-engineering.md).

---

## 3. Deployment & Networking Scenarios

The dashboard supports three operational modes depending on network setup:

1. **Strictly Local LAN (Home / Office Wi-Fi):**
   - Bind server to `0.0.0.0:8885` and restrict firewall to local subnet (`sudo ufw allow from 192.168.1.0/24 to any port 8885`). Access via `http://<LAN_IP>:8885`.
2. **Remote Access Without Domain (External IP / VPN):**
   - Use encrypted WireGuard/Tailscale mesh VPN (zero router ports exposed) or router Port Forwarding with IP restrictions. Alternatively, use free Cloudflare Tunnels (`cloudflared tunnel --url http://127.0.0.1:8885`).
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
- [ ] No tokens or cookies appear in `ps aux` or shell history.
- [ ] Provider endpoints match pinned domain verification checks.
- [ ] Dashboard is accessible via LAN IP, VPN, or reverse proxy.
- [ ] PWA manifest loads cleanly and installs to mobile home screen.
