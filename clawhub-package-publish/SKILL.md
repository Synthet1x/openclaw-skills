---
name: clawhub-package-publish
description: "залей на clawhub, publish plugin, обнови пакет в каталоге. Publishes an OpenClaw code plugin from this host and verifies ClawHub latest."
---

# ClawHub package publish

Use when the user asks to publish or bump an OpenClaw **plugin/package** on ClawHub. Skills use `clawhub-skill-publish`; this procedure is only for `openclaw.plugin.json` packages.

## 1. See what ClawHub already has

```
export https_proxy=http://127.0.0.1:10808 HTTP_PROXY=http://127.0.0.1:10808
clawhub whoami
clawhub package inspect @owner/name --versions --json --limit 20
```

Do not use `clawhub inspect` or `clawhub search` for plugins. Those query the skill registry and return `Skill not found`.

Done when `latestVersion` / `tags.latest` are recorded and compared with local `package.json`, `openclaw.plugin.json`, and `git rev-parse HEAD`.

## 2. Dry-run from the plugin folder

`--workdir` and the source path must be the plugin directory (the folder with `package.json` and `openclaw.plugin.json`). Do not use the OpenClaw workspace as workdir — clawhub then walks workspace files and fails with `EACCES` on `~/.openclaw/workspace/secrets/.htpasswd`.

```
clawhub --workdir /path/to/plugin package publish /path/to/plugin --dry-run --json \
  --version X.Y.Z --name @owner/name --family code-plugin \
  --source-repo Owner/repo --source-commit FULLSHA --source-ref main \
  --changelog "short release note"
```

Done when JSON `version` and `commit` match the local release and the version is ahead of ClawHub latest.

## 3. Publish once

Same command without `--dry-run`, with `--no-input`.

Done when the result includes `releaseId`. That is the success signal.

## 4. Verify; do not republish on catalog lag

Right after publish, `package inspect --versions` can still show the previous `latestVersion`.

- If `releaseId` was returned: wait, then inspect again. Do not publish a second time.
- A second publish while Convex is still processing the first can fail with Node action OOM (512 MB) even though the first release later appears.
- Publish again only when no `releaseId` came back.

Done when `latestVersion` and `tags.latest` equal the new version, `verification.sourceCommit` matches the git SHA, and (if the same tarball is on npm) `version.artifact.npmShasum` matches npm.

`scanStatus: suspicious` from LLM analysis is not a publish failure when latest already points at the new version.
