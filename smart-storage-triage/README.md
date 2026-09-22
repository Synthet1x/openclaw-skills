# Smart Storage Triage & Search (v1.2.3)

Fast, zero-bloat local search and storage triage for AI agents with strict privacy & security guards.

## Why this exists

When AI agents need to answer questions about a codebase, documents, or large drives, the default behavior is running blind shell commands (`grep`, `find`, `ls -R`) or dumping multi-megabyte files into conversation history. This frequently burns **50,000–100,000+ tokens per question**, degrades model reasoning, and risks context overflow.

**Smart Storage Triage** provides a dynamic two-layer solution:
1. **Full-Text BM25 Index (SQLite FTS5):** indexes code repositories, markdown, configuration, and office documents with exact line numbers and page/sheet tracking. Queries return only the exact 3-5 line snippet needed, reducing token usage by **95-98%**.
2. **Compressed Path Tree (`tree.json.gz`):** indexes massive nested directory structures and multi-year archives. Searches across 100,000+ files in **~0.03 seconds** without disk thrashing.

---

## Security & Privacy (Safety First in v1.2.3)

- **Zero-Secret Tree & Content Exclusion:** strictly excludes `.env*`, private keys (`*.pem`, `*.key`, `id_rsa*`, `id_ed25519*`), cloud tokens, and sensitive credential stores (`credentials.json`, `token.json`, `auth.json`, `*.kdbx`) from **both** full-text indexing and the `tree.json.gz` snapshot.
- **Symlink Boundary Protection:** directory symlinks are pruned to prevent directory traversal loops; file symlinks resolving outside the target directory boundary are ignored and never followed.
- **Broad Scope Safety Guard:** indexing system root (`/`), `/home`, `/root`, or the entire user home directory (`~`) is blocked in code to prevent accidental broad data exposure. Requires the explicit confirmation flag `--allow-broad`.
- **Sensitive Directory Exclusion:** `.ssh`, `.aws`, `.gnupg`, `.azure`, `.kube`, `.secrets`, and `secrets` folders are never scanned or indexed.
- **100% Local & Zero Telemetry:** runs entirely on local Python and embedded SQLite FTS5. Zero external network calls, zero tracking.
- **No Hardcoded Paths:** safe for any machine or team. Custom paths resolve via CLI arguments, environment variables (`STORAGE_RAG_DB`, `STORAGE_RAG_TREE`), or `~/.config/smart-storage-triage/config.json`.

---

## Dynamic Age-Based Triage (What is an "Archive"?)

Files are categorized automatically by **modification age (`mtime`)** without requiring manual tagging:
- **Active Files (< 1 year untouched by default):** indexed deeply into full-text SQLite FTS5 (BM25) for immediate semantic retrieval.
- **Archived Files (>= 1 year untouched, or folders named `archive`/`backup`):** automatically excluded from heavy full-text indexing to save memory and avoid search pollution, but preserved in the lightweight `tree.json.gz` snapshot for instant path & filename lookups.
- **Working Directory Override (`--full` / `--workdir`):** when indexing an active codebase or project, tells the indexer to index every file deeply regardless of age.
- **Custom Time Windows (`--active-days <N>`):** easily adjust the active window (e.g. `--active-days 730` for 2 years).

---

## Quick Start

### 1. Build or update an index
```bash
# Default triage: files <1 year -> full text; files >=1 year -> tree snapshot
python3 scripts/triage_index.py /path/to/storage

# Working project (index everything fully)
python3 scripts/triage_index.py /path/to/project --full

# Custom active window (e.g., 2 years)
python3 scripts/triage_index.py /path/to/storage --active-days 730
```

### 2. Search content (active code & documents)
```bash
python3 scripts/storage_find.py "function_name or search query"
```

### 3. Search file paths and archives
```bash
python3 scripts/archive_find.py "config*.yaml" --limit 20
```

---

## License

MIT-0
