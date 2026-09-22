# OpenClaw Skills

Agent skills for [OpenClaw](https://github.com/openclaw/openclaw) — published on [ClawHub](https://clawhub.ai) and mirrored here.

Each top-level folder is a self-contained skill: drop it into your OpenClaw `skills/` directory (or agent workspace) and the agent picks it up.

## Skills

| Skill | What it does | ClawHub |
|---|---|---|
| [`sber-business`](./sber-business) | СберБизнес API: onboarding, Zero-Knowledge Vault (AES-256-GCM + mTLS), notification channels (Telegram/MAX/Discord/Slack/Webhook), balances, payment orders, signing links, bank-stamped PDF statements | [`sber-business@1.0.3`](https://clawhub.ai/skills/sber-business) ✅ |
| [`smart-storage-triage`](./smart-storage-triage) | Fast local search & storage triage for huge drives and archives: SQLite FTS5 (BM25) full-text index + compressed path-tree snapshots. Returns 3–5 line snippets instead of dumping files — ~95–98 % token savings, with privacy guards and user confirmation before broad indexing | [`smart-storage-triage@1.3.0`](https://clawhub.ai/skills/smart-storage-triage) ✅ |

✅ = published on ClawHub and passed its security moderation (**CLEAN**). Install with:

```bash
clawhub install sber-business
clawhub install smart-storage-triage
```

Only skills that have passed the ClawHub security audit are mirrored to this repository. New skills join after they clear the same review.

## Security notes

- `sber-business` keeps all secrets (client certificates, keys, tokens) in AES-256-GCM encrypted vault files; private-key material is passed via `stdin` only, never via CLI arguments. Webhook notification of financial data is HTTPS-only and can mask account numbers/tax IDs.
- `smart-storage-triage` is strictly local: no network egress, deny-lists for secrets (`.env`, keys), and explicit user confirmation before indexing broad directory trees.

## License

[MIT-0](./LICENSE) (no attribution required) — same as on ClawHub.

---

*По-русски:* зеркало скиллов для ИИ-агента OpenClaw с каталога ClawHub — сюда попадают только скиллы, прошедшие секьюрити-аудит ClawHub. Сейчас это `sber-business` и `smart-storage-triage`. Установка: `clawhub install <имя>`. Лицензия MIT-0.
