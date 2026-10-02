# AI Subscription API Reverse Engineering Guide

This guide details the methodology for discovering, isolating, and integrating internal quota, usage, and limit endpoints for any AI provider or web platform.

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
- **OpenRouter:** `GET https://openrouter.ai/api/v1/auth/key`
  - Returns `data.limit`, `data.usage`, `data.limit_remaining`, `data.is_free_tier`.
- **ElevenLabs:** `GET https://api.elevenlabs.io/v1/user/subscription`
  - Returns `character_count`, `character_limit`, `next_character_count_reset_unix`.
- **xAI / Grok:** `POST https://api.x.ai/v1/users/me` or OAuth refresh via `https://api.x.ai/v1/oauth2/token`.

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

## 4. Normalizing Telemetry into Universal Metrics

Map whatever JSON format the provider returns into the standard telemetry schema:

```json
{
  "provider": "Provider Name",
  "account": "user@example.com",
  "category": "subscription | api_credits | tiered_quota",
  "used": 15000,
  "limit": 100000,
  "unit": "characters | tokens | requests | percent",
  "percent_used": 15.0,
  "resets_at": "2026-10-03T00:00:00Z",
  "status": "healthy | warning | exhausted",
  "updated_at": "2026-10-02T12:00:00Z"
}
```
