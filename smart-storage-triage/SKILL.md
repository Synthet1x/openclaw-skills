---
name: smart-storage-triage
description: "Universal smart search and storage triage for codebases, local files, documents, and archives. Uses SQLite FTS5 (BM25) and fast gzip tree snapshots. Requires user confirmation before broad directory indexing."
allowed-tools: [exec, read]
---

# Smart Storage Triage & Search (v1.3.0)

Fast, zero-bloat search across code repositories, local folders, documentation, and deep archives. Avoids burning tens of thousands of tokens by querying indexed SQLite FTS5 and compressed directory tree snapshots instead of performing blind shell walks (`find` / `grep`).

### What's New in v1.3.0:
- **Full Directory Tree Tracking:** Snapshots now capture both directories (`dirs`) and files (`files`), allowing instant folder discovery even for newly created or empty paths.
- **Dual Folder & File Search:** Query either folders (`--dirs`), files (`--files`), or both with visual tags (`📁 [ПАПКА]`, `📄 [ФАЙЛ]`).
- **Unicode Surrogate Resilience:** Hardened string sanitizer prevents UTF-8 encoding crashes from corrupted PDF/binary documents.

## Security & Privacy (Safety First)

1. **Automatic Secret & Credential Exclusion:**
   - Files matching `.env*`, `credentials.json`, `token.json`, `auth.json`, `secrets.json`, `id_rsa*`, `id_ed25519*`, `*.pem`, `*.key`, `*.kdbx`, `*.pfx`, `*.p12` are strictly excluded from **both** full-text indexing and directory tree snapshots (`tree.json.gz`).
   - Sensitive directories (`.ssh`, `.aws`, `.gnupg`, `.azure`, `.kube`, `.secrets`, `secrets`) are completely skipped.
2. **Symlink Boundary Protection:**
   - Directory symlinks are pruned to prevent directory traversal loops.
   - File symlinks that resolve outside the target directory boundary are strictly ignored and never followed.
3. **Broad Scope Safety Guard:**
   - Direct indexing of the root filesystem (`/`), `/home`, or the user home directory (`~`) is restricted in code to prevent accidental broad data exposure. Indexing broad system targets requires the explicit `--allow-broad` flag.
4. **100% Local & Zero Telemetry:**
   - Runs entirely using standard Python and embedded SQLite FTS5. Zero external network calls, zero tracking.
5. **No Hardcoded Paths:**
   - Works in any directory. Custom paths can be configured via environment variables (`STORAGE_RAG_DB`, `STORAGE_RAG_TREE`), CLI arguments, or `~/.config/smart-storage-triage/config.json`.

## Mandatory User Confirmation (Approval Step)

**CRITICAL:** Before building or rebuilding an index (`triage_index.py`) on a new directory or external storage:
- The agent **MUST ask for explicit user confirmation**, specifying the target directory path and expected scope.
- **NEVER** automatically index the entire home directory (`~`), filesystem root (`/`), or parent mount points without clear user authorization.

## Dynamic Age-Based Triage (What is an "Archive"?)

Storage is split automatically without manual tagging:
1. **Active Files (< 1 year untouched by default):**
   - Files modified within the active period (`--active-days 365`) are indexed with **full-text BM25 search** (code with exact line numbers, documents with page/sheet numbers).
2. **Archived Files (>= 1 year untouched, or inside `archive/backup` folders):**
   - Files not modified for 1 year or more automatically graduate into the **Archive Layer**.
   - They do **not** bloat the heavy full-text index, saving 95%+ of disk space and memory.
   - Instead, they are captured in the compressed **`tree.json.gz` snapshot** for instant path, filename, and date searches (100,000+ files in 0.03s).
3. **Working Directory Override (`--full` / `--workdir`):**
   - When indexing an active workspace or project repository, pass `--full` to index every file deeply, regardless of modification age.

## Search Workflow

### 1. Content Search (Active Code, Text, and Documents)

Query full-text content with BM25 ranking:
```bash
python3 <skill_dir>/scripts/storage_find.py "<query>" [--limit 10]
```
- Returns matching files, exact line numbers (for code/text) or page/sheet numbers (for documents), and concise snippets.
- Reads only the relevant snippet into context, saving up to 98% of prompt tokens.

### 2. File Path & Archive Search (Deep Trees & Inactive Files)

Query the compressed tree snapshot (`tree.json.gz`) for instant filename, folder, or regex matches:
```bash
python3 <skill_dir>/scripts/archive_find.py "<pattern_or_name>" [--dirs] [--files] [--ext .py|.pdf] [--limit 20]
```
- Searches across 100,000+ files and directories in ~0.03 seconds without triggering disk I/O thrashing.
- Supports substring, regex patterns, and type filtering (`--dirs` for folders only, `--files` for files only).

### 3. Creating or Updating an Index

Ask the user for approval first, then build or refresh the index:
```bash
# Default triage: active (<1y) -> full text, archived (>=1y) -> tree snapshot
python3 <skill_dir>/scripts/triage_index.py <directory_path>

# Custom active window (e.g. 2 years)
python3 <skill_dir>/scripts/triage_index.py <directory_path> --active-days 730

# Working repository / full indexing (index all files regardless of age)
python3 <skill_dir>/scripts/triage_index.py <directory_path> --full
```

## Resolution Order

`storage_find.py` and `archive_find.py` auto-resolve indexes in the following priority:
1. Explicit `--db` or `--tree` argument.
2. Environment variables `STORAGE_RAG_DB` and `STORAGE_RAG_TREE`.
3. User configuration file `~/.config/smart-storage-triage/config.json`.
4. Current working directory (`./storage_rag.db`, `./tree.json.gz`).
