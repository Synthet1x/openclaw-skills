# AI Subscription API Reverse Engineering Guide

This guide details the methodology for discovering, isolating, and integrating internal quota, usage, and limit endpoints for any AI provider or web platform — including strategies for platforms that omit explicit limit figures.

---

## 1. The Discovery Methodology

Modern web dashboards for AI services display usage, quota meters, and model limits in real time. Because these web UIs fetch data via client-side JavaScript, the underlying telemetry endpoints are discoverable via browser network inspection.

### Step 1: Network Trace Isolation
1. Open your browser to the provider's dashboard or chat interface (e.g., Claude, ChatGPT, Grok, Perplexity, OpenRouter).
2. Open Developer Tools (`F12` or `Ctrl+Shift+I` / `Cmd+Option+I`).
3. Switch to the **Network** tab and activate the **Fetch/XHR** filter.
4. Ensure the recording indicator is red (active).
5. Refresh the page or trigger a quota-related action (open the account settings modal, model picker, or usage breakdown).

### Step 2: High-Yield Query Filtering
Use the search/filter bar in the Network tab with target keywords:
- `usage`
- `quota`
- `subscription`
- `limits`
- `billing`
- `credits`
- `models`
- `me` or `user`
- `session`

---

## 2. Common Endpoint Architectures & Patterns

### Pattern A: Internal RPC Endpoints
Often seen in complex cloud interfaces (e.g., Google Cloud Code / Antigravity):
- **Request:** `POST https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** JSON payload containing model IDs, tier entitlements, hourly/weekly request quotas, and UTC reset timestamps (`resetTime`).

### Pattern B: REST Usage / Entitlement Endpoints
Standard for modern API providers:
- **OpenRouter:** `GET https://openrouter.ai/api/v1/auth/key` or `/api/v1/credits`
  - Returns `data.total_credits`, `data.total_usage`, `data.limit_remaining`.
- **ElevenLabs:** `GET https://api.elevenlabs.io/v1/user/subscription`
  - Returns `character_count`, `character_limit`, `next_character_count_reset_unix`.
- **xAI / Grok:** `POST https://cli-chat-proxy.grok.com/v1/billing?format=credits` or OAuth usage.

### Pattern C: Web Dashboard Internal Endpoints
When an official developer endpoint does not expose subscription limits (e.g., consumer web interfaces):
- The web application queries private internal endpoints (e.g., `https://chat.example.com/backend-api/me` or `/api/subscription/usage`).
- These rely on a session cookie or ephemeral JWT extracted during login.

---

## 3. Dissecting Authentication & Lifecycles

Before automating any endpoint, identify how credentials refresh:

1. **Bearer Access Token (Short-lived):**
   - Typically expires in 1 hour.
   - Look for a companion `refresh_token` or an OAuth refresh request (e.g., to `oauth2/token` or `/auth/refresh`).
   - The collector script should implement an auto-refresh loop storing updated tokens with `chmod 600`.

2. **Session Cookie (Long-lived):**
   - Often lasts weeks or months until logout.
   - Pinned to the host domain.
   - May require accompanying headers:
     - `User-Agent`: Mimic standard browser user agent to avoid bot blocks.
     - `Origin` or `Referer`: Set to the provider's web root.
     - `x-csrf-token` or similar anti-forgery header (extracted from the initial page HTML or companion cookie).

---

## 4. When Endpoints Lack Explicit Limit Data (Inferred & Fallback Strategies)

Many platforms (Pay-as-you-go APIs, Flat-rate subscriptions, or Search APIs) do not return a clean `"remaining": 42` counter. To maintain full visibility on the dashboard, use these four proven estimation patterns:

### Strategy 1: Unit Economics / Reverse Balance Calculation
When the API returns only account balance in USD (e.g., Perplexity, custom search APIs):
- Query the account balance (e.g., `$9.34`).
- Divide by the fixed cost per standard request (e.g., `$0.005` per search).
- Calculate estimated capacity: `remaining_requests = int(balance_usd / unit_price)`.
- Render a dynamic progress bar calibrated against the last top-up tier.

### Strategy 2: Rolling Window & Fixed Quota Timers
When the subscription has a strict cadence limit (e.g., "50 messages per 3 hours" in Claude Pro / ChatGPT Plus) but the endpoint only returns tier status:
- Maintain a local state timestamp of the first outbound request in the cycle (`cycle_started_at`).
- Increment a local request counter per session turn.
- Calculate and render the remaining countdown to window reset (`cycle_started_at + 3 hours`).

### Strategy 3: Local Log Aggregation (Zero-API Fallback)
When a provider provides zero telemetry endpoints or strictly forbids automated status polling:
- Aggregate usage directly from local runtime session logs (e.g., OpenClaw session transcripts or local proxy SQLite stores).
- Tally input/output tokens, active turns, and estimated cost locally.
- Map this usage onto the dashboard card with a "Locally Calculated" badge.

### Strategy 4: Session Validity Heartbeat (Flat-Rate / Unlimited)
For unlimited enterprise tiers or fixed flat-rate keys where limits are unbounded:
- Execute a lightweight status check (e.g., `GET /v1/models` or `GET /user`).
- Verify HTTP 200 OK vs 401/403.
- Render the provider card with a live green pulse badge (`status: active`, `tier: unlimited / flat-rate`).

---

## 5. Normalizing Telemetry into Universal Metrics

Map whatever JSON or calculated telemetry you collect into the standard dashboard schema:

```json
{
  "provider": "Provider Name",
  "account": "user@example.com",
  "category": "subscription | api_credits | tiered_quota | inferred",
  "used": 15000,
  "limit": 100000,
  "unit": "characters | tokens | requests | usd | percent",
  "percent_used": 15.0,
  "resets_at": "2026-10-03T00:00:00Z",
  "status": "healthy | warning | exhausted | active",
  "inference_mode": "api_exact | unit_calculated | local_log_tracked",
  "updated_at": "2026-10-02T12:00:00Z"
}
```
