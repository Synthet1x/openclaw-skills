---
name: grok-thinking-levels
description: "нет режимов размышления, ползунок не тянется, новая grok. Exposes high thinking for a Grok id the xAI plugin still treats as off."
---

# Grok thinking levels

Use when a Grok model answers, but `/think` and the effort slider have no `high` (often only `off`) after that id was added to config.

Scope: Grok / xAI only. Other providers handle this via config — see `openclaw-model-setup` for the `compat.supportedReasoningEfforts` route (opencode-go and friends).

For Grok, config cannot fix this. `compat.supportedReasoningEfforts` is ignored: the xAI plugin profile returns off-only for unknown ids and short-circuits catalog levels. Runtime compat then nulls `thinkingLevelMap` unless the id is frontier.

## Patch the installed plugin

1. Search the installed OpenClaw `dist` for `function isXaiFrontierModelId` and `function isXaiGrok46ModelId`. Hashed filenames change on update; do not reuse an old hash.
2. Add the new id (and a `grok-X.Y-` prefix if dated builds exist) to the frontier check and to the xhigh predicate. The xhigh function is still named for 4.6; that is the check that maps `xhigh` to `xhigh` instead of `high`.
3. Add the same id prefix to `XAI_MODERN_MODEL_PREFIXES` in the provider-models module that defines `isModernXaiModel`.
4. In a fresh `node --input-type=module` process, import `resolveThinkingProfile` and `applyXaiRuntimeModelCompat`. Done for the patch when levels include `low`, `medium`, `high`, and `xhigh`, default is `high`, and `thinkingLevelMap.high` is `"high"`.

## Reload

5. Ask the OpenClaw system tool to restart this Gateway if available, or instruct the operator to restart via the Control UI or terminal. Do not `systemctl` or otherwise restart the gateway service from the shell. A fresh node import does not reload the running process.
6. If that tool fails on another provider's auth, say the patch is on disk and the live picker is unchecked. Do not claim `high` is selectable.
7. Done when a gateway session row for that model lists `high` in `thinkingLevels`, or the user can select `high`.

The dist patch is wiped by the next OpenClaw update. After an update, repeat the search; do not assume the old file still exists.
