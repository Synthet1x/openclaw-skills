# OpenClaw Skills

Agent skills for [OpenClaw](https://github.com/openclaw/openclaw) — published on [ClawHub](https://clawhub.ai) and mirrored here.

Each top-level folder is a self-contained skill: drop it into your OpenClaw `skills/` directory (or agent workspace) and the agent picks it up.

## Skills

| Skill | What it does | ClawHub |
|---|---|---|
| [`sber-business`](./sber-business) | СберБизнес API: onboarding, Zero-Knowledge Vault (AES-256-GCM + mTLS), notification channels (Telegram/MAX/Discord/Slack/Webhook), balances, payment orders, signing links, bank-stamped PDF statements | [`sber-business@1.0.3`](https://clawhub.ai/skills/sber-business) ✅ |
| [`smart-storage-triage`](./smart-storage-triage) | Fast local search & storage triage for huge drives and archives: SQLite FTS5 (BM25) full-text index + compressed path-tree snapshots. Returns 3–5 line snippets instead of dumping files — ~95–98 % token savings, with privacy guards and user confirmation before broad indexing | [`smart-storage-triage@1.3.0`](https://clawhub.ai/skills/smart-storage-triage) ✅ |
| [`a4-text-sheet`](./a4-text-sheet) | Renders school homework and reading sheets as decorated A4 2480×3508 images (plus chat JPEG) and prints them on demand | original |
| [`academic-doc-formatting`](./academic-doc-formatting) | Formats academic DOCX documents: verified title page layout, branch-specific structure (full papers vs. routine tasks), strict pagination | original |
| [`clawhub-skill-publish`](./clawhub-skill-publish) | Publishes skills to ClawHub, reads security-scan reports via API and fixes scanner findings (skillspector / llm / vt) | original |
| [`clawhub-package-publish`](./clawhub-package-publish) | Publishes OpenClaw code plugins to the ClawHub catalog and verifies the released version | original |
| [`grok-thinking-levels`](./grok-thinking-levels) | Exposes high thinking levels for Grok model ids the xAI plugin still treats as non-thinking | original |
| [`openclaw-model-setup`](./openclaw-model-setup) | Adds a provider model to OpenClaw with all required entries and unlocks selectable thinking levels | original |

✅ = published on ClawHub (security moderation: **CLEAN**). Install published skills with:

```bash
clawhub install sber-business
clawhub install smart-storage-triage
```

For the original skills — copy the folder into your `skills/` directory.

## Security notes

- `sber-business` keeps all secrets (client certificates, keys, tokens) in AES-256-GCM encrypted vault files; private-key material is passed via `stdin` only, never via CLI arguments. Webhook notification of financial data is HTTPS-only and can mask account numbers/tax IDs.
- `smart-storage-triage` is strictly local: no network egress, deny-lists for secrets (`.env`, keys), and explicit user confirmation before indexing broad directory trees.

## License

[MIT-0](./LICENSE) (no attribution required) — same as on ClawHub.

---

*По-русски:* набор скиллов для ИИ-агента OpenClaw. Два из них опубликованы в каталоге ClawHub (`sber-business`, `smart-storage-triage`), остальные — авторские оригиналы. Установка опубликованных: `clawhub install <имя>`, остальные — копированием папки в `skills/`. Лицензия MIT-0.
