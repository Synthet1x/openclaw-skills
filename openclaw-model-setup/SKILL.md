---
name: openclaw-model-setup
description: "добавь модель, модель не подключается, нет режимов размышления. Adds a provider model to OpenClaw with all three required entries and unlocks selectable thinking levels on OpenCode Go."
---

# OpenClaw Model Setup

Use when adding a new model from an existing provider to OpenClaw, when `session_status` or `/model` rejects the id with `not allowed`, or when a fresh OpenCode Go model exposes only `off` as its thinking level.

For Grok/xAI where the plugin short-circuits thinking levels to `off` and ignores `compat`, use `grok-thinking-levels` instead — that procedure patches `dist` and does not apply to other providers.

## 1. Three config entries in `~/.openclaw/openclaw.json`

All three are required. Missing any one leaves the model unusable.

a) **`models.providers.<provider>.models[]`** — the model definition. Match `contextWindow` and `maxTokens` to the provider's published limits. Set `input: ["text", "image"]` when the model accepts images.

b) **`agents.defaults.modelPolicy.allow[]`** — append `"<provider>/<model-id>"` (e.g. `opencode-go/mimo-v2.6-pro`). Missing this entry yields `Model "<id>" is not allowed` from `session_status(model=...)` and the model picker. This is the most commonly missed step — the first error message points at the model, not at the allowlist.

c) **`agents.defaults.models."<provider>/<model-id>".alias`** — the short alias the user will type:

```json
"opencode-go/mimo-v2.6-pro": { "alias": "m26p" }
```

Done when `session_status model=<alias>` returns the model row instead of an "is not allowed" error.

## 2. OpenCode Go thinking levels

The opencode-go plugin hardcodes a fixed thinking profile for `deepseek-v4-flash`, `deepseek-v4-pro`, `kimi-k3`, `kimi-k2.5`, `kimi-k2.6`, `kimi-k2.7-code`, `minimax-m3`, `minimax-m2.5`, `minimax-m2.7`. Those ids ignore `compat.supportedReasoningEfforts`; changing their levels requires editing the plugin `dist`.

For any other OpenCode Go id (new releases like `mimo-v2.6-pro`), set `compat.supportedReasoningEfforts` on the model entry from step 1a:

```json
{
  "id": "mimo-v2.6-pro",
  "name": "MiMo-V2.6 Pro",
  "contextWindow": 1000000,
  "maxTokens": 32768,
  "input": ["text", "image"],
  "compat": { "supportedReasoningEfforts": ["low", "medium", "high", "max"] }
}
```

Valid level ids: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`. The default picks `medium` if present, else `high`, else `low`, else `off`. `compat.supportedReasoningEfforts` takes precedence over the fallback path.

Pitfall: without `compat.supportedReasoningEfforts`, a model entry with `reasoning: true` and `api: "openai-completions"` falls back to a fixed `off`-only profile (`FIXED_REASONING_PROFILE` in `provider-policy-api-Cnka8Jkw.mjs`). Prefer `compat.supportedReasoningEfforts` because it exposes selectable levels.

## 3. Reload

Ask the OpenClaw system tool to restart this Gateway, or instruct the operator to restart via the Control UI or terminal. Do not `systemctl` or otherwise restart the gateway service from the shell.

Done when `session_status` for a session on the new model shows `Modes: think <level>` matching the selected level, not `off` unless `off` was selected.

## 4. Discover ids on OpenCode Go

To see what ids the provider exposes before writing config, query its models endpoint. Plain `Authorization: Bearer` alone returns 403 — the `x-opencode-session` header is required:

```bash
curl -sS "https://opencode.ai/zen/go/v1/models" \
  -H "Authorization: Bearer $OPENCODE_API_KEY" \
  -H "x-opencode-session: openclaw-main-session"
```
