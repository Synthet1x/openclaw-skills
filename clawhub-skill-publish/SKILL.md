---
name: clawhub-skill-publish
description: "опубликуй скилл на clawhub, clawhub security, замечания аудиторов. Publishes OpenClaw skills to ClawHub, audits security reports via API, and fixes scanner findings."
---

# ClawHub Skill Publish & Security Audit

Use when publishing, updating, or reviewing the security status of an OpenClaw **skill** on ClawHub. For code plugins (`openclaw.plugin.json`), use `clawhub-package-publish`.

## 1. Inspect ClawHub Security Audit via API

ClawHub runs automated scanners (`skillspector`, `llm`, `vt`) on every published skill version. External requests must route through the local proxy.

```bash
curl -sS -x http://127.0.0.1:10808 "https://clawhub.ai/api/v1/skills/<slug>/versions/<version>" | python3 -c '
import sys, json
data = json.load(sys.stdin)
ver = data.get("version", {})
sec = ver.get("security", {})
print("Status:", sec.get("status"), "| Warnings:", sec.get("hasWarnings"))
scanners = sec.get("scanners", {})
llm = scanners.get("llm") or {}
if llm:
    print("LLM Verdict:", llm.get("verdict"))
    print("LLM Findings:", llm.get("findings"))
    print("LLM Summary:", llm.get("summary"))
skillspector = scanners.get("skillspector") or {}
if skillspector:
    print("Skillspector:", skillspector.get("status"), "| Issues:", skillspector.get("issueCount"))
'
```

Done when current `security.status` (`clean`, `suspicious`, etc.) and specific findings are identified.

## 2. Fix Common Security Scanner Findings

To achieve `clean` status and `llm.verdict == "benign"`:

1. **Process Arguments Leakage (`[TT5]`):**
   - Never pass secrets, passwords, or tokens in CLI flags (e.g. `openssl pkcs12 -passin pass:...` or `curl -u user:pass`). These are visible in `/proc/$PID/cmdline` to other local processes.
   - Pass secrets via `stdin`:
     ```python
     cmd = ["openssl", "pkcs12", "-in", str(p12_path), ..., "-passin", "stdin"]
     res = subprocess.run(cmd, input=password.encode("utf-8"), capture_output=True)
     ```

2. **Insecure Storage / Plaintext Fallback (`[PE3]`):**
   - If advertising encrypted storage (Vault/AES-GCM), do not provide an automated fallback to unencrypted plaintext `.env` files. Remove unencrypted fallbacks so encryption is mandatory.

3. **Sensitive Financial / PII Data Egress (`[SQP-2]`, `[E1]`):**
   - Enforce HTTPS for any custom webhook URLs:
     ```python
     if not url.lower().startswith("https://"):
         log("SECURITY REJECT: Webhook URL must use HTTPS for financial data.")
         return False
     ```
   - Provide a privacy masking option (`maskPrivacy: true`) that redacts bank account numbers (`40702...0000`) and tax IDs (`7707****93`).
   - Include an explicit Privacy & Compliance notice in `SKILL.md` and user guides warning against broadcasting sensitive financial data to unauthenticated channels.

4. **Frontmatter Schema Validation (`[LP1]`):**
   - `quick_validate.py` permits only standard top-level keys in `SKILL.md` frontmatter: `name`, `description`, `allowed-tools`, `metadata`, `license`, `homepage`, `user-invocable`, `disable-model-invocation`, `command-tool`, `command-arg-mode`, `command-dispatch`.
   - Custom permission disclosures (e.g. `network-destinations`, `filesystem-access`) must be placed inside `metadata:`, not at the root level:
     ```yaml
     ---
     name: my-skill
     description: "..."
     allowed-tools: [exec, read, write]
     metadata:
       network-destinations:
         - https://api.example.com
       filesystem-access:
         - ~/.openclaw/secrets/
     ---
     ```

## 3. Pre-Publish Package Validation

Run the local validator before every publish attempt:

```bash
python3 ~/.npm-global/lib/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py /path/to/skill
```

Done when output is `Skill is valid!`.

## 4. Publish to ClawHub

Publish the skill folder using `--no-input` through the proxy:

```bash
export https_proxy=http://127.0.0.1:10808 HTTP_PROXY=http://127.0.0.1:10808
clawhub --no-input skill publish /path/to/skill --version <X.Y.Z> --changelog "<release notes>"
```

Done when the CLI outputs `✔ OK. Published <slug>@<version> (<releaseId>)`. The `releaseId` is the definitive success signal.

**Catalog Lag Guard:** Never republish if a `releaseId` was returned. Right after publishing, Convex backend indexing and security scanners take 30–60 seconds to process. During this window, the version API endpoint may return HTTP 404 or the previous `latestVersion`. Wait before inspecting.

## 5. Verify Clean Audit Result

Wait 30–60 seconds for ClawHub's backend scanners (`skillspector`, `llm`, `vt`) to finish, then inspect the version endpoint. Use safe JSON parsing to handle temporary 404 responses gracefully:

```bash
curl -sS -x http://127.0.0.1:10808 "https://clawhub.ai/api/v1/skills/<slug>/versions/<version>" | python3 -c '
import sys, json
raw = sys.stdin.read().strip()
try:
    data = json.loads(raw)
    sec = data.get("version", {}).get("security", {})
    print("Status:", sec.get("status"), "| Warnings:", sec.get("hasWarnings"))
    scanners = sec.get("scanners", {})
    llm = scanners.get("llm") or {}
    if llm:
        print("LLM Verdict:", llm.get("verdict"))
        print("LLM Summary:", llm.get("summary"))
    skillspector = scanners.get("skillspector") or {}
    if skillspector:
        print("Skillspector:", skillspector.get("status"), "| Issues:", skillspector.get("issueCount"))
except json.JSONDecodeError:
    print("Pending indexing (non-JSON response):", raw[:120])
'
```

Alternatively, check skill metadata via CLI:
```bash
export https_proxy=http://127.0.0.1:10808 HTTP_PROXY=http://127.0.0.1:10808
clawhub inspect <slug>
```

Done when `Status: clean` (or `Moderation: CLEAN`) and `Warnings: False` / `LLM Verdict: benign`.
