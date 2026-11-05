#!/usr/bin/env python3
"""Read-only security audit for an OpenClaw host.

Checks the box and the gateway, prints a markdown report (or JSON).
Never modifies anything and never prints secret values.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
OW = HOME / ".openclaw"
FINDINGS: list[dict] = []


def add(level: str, area: str, message: str, detail: str = "") -> None:
    FINDINGS.append({"level": level, "area": area, "message": message, "detail": detail})


def run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except Exception as exc:  # noqa: BLE001
        return 1, str(exc)


def mode_str(path: Path) -> str:
    try:
        return oct(path.stat().st_mode & 0o777)
    except OSError:
        return "?"


# ── checks ───────────────────────────────────────────────────────────────────

def check_host() -> None:
    rc, out = run(["uname", "-srm"])
    if rc == 0:
        add("INFO", "host", "Система", out.strip())
    up = Path("/proc/uptime")
    if up.exists():
        secs = float(up.read_text().split()[0])
        add("INFO", "host", "Аптайм", f"{secs / 86400:.1f} дн.")


def check_gateway() -> None:
    cfg_path = OW / "openclaw.json"
    if not cfg_path.exists():
        add("HIGH", "gateway", "Не найден openclaw.json")
        return
    try:
        cfg = json.loads(cfg_path.read_text())
    except Exception as exc:  # noqa: BLE001
        add("HIGH", "gateway", "Конфиг не парсится", str(exc)[:120])
        return
    gw = cfg.get("gateway", {}) or {}
    bind = gw.get("bind") or gw.get("host") or "?"
    port = gw.get("port", 18789)
    if bind in ("0.0.0.0", "::", "*"):
        add("HIGH", "gateway", f"Шлюз слушает {bind}:{port} — доступен из сети", "Проверь firewall/reverse proxy")
    else:
        add("INFO", "gateway", f"Bind {bind}:{port}")
    auth = gw.get("auth") or {}
    if isinstance(auth, dict) and not auth.get("mode") and not auth.get("password") and not auth.get("token"):
        add("HIGH", "gateway", "Аутентификация шлюза не выглядит включённой")
    tp = gw.get("trustedProxies")
    if tp:
        add("INFO", "gateway", "trustedProxies", json.dumps(tp))
    if (OW / "openclaw.json").stat().st_mode & 0o077:
        add("HIGH", "gateway", "openclaw.json доступен группе/другим", mode_str(OW / "openclaw.json"))


def check_ports() -> None:
    rc, out = run(["ss", "-H", "-tuln"])
    if rc != 0:
        add("INFO", "ports", "ss недоступен, пропускаю")
        return
    exposed = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local = parts[4]
        if local.startswith("127.") or local.startswith("[::1]") or local.startswith("::1"):
            continue
        exposed.append(local)
    if exposed:
        add("MEDIUM", "ports", f"Слушают вне loopback: {len(exposed)}", ", ".join(sorted(set(exposed))[:12]))
    else:
        add("INFO", "ports", "Все слушающие сокеты только на loopback")


def check_ssh() -> None:
    rc, out = run(["sshd", "-T"], timeout=10)
    cfg = {}
    if rc == 0:
        for line in out.splitlines():
            k, _, v = line.partition(" ")
            cfg[k.strip().lower()] = v.strip()
    else:
        files = [Path("/etc/ssh/sshd_config")] + sorted(Path("/etc/ssh/sshd_config.d").glob("*.conf")) if Path("/etc/ssh/sshd_config.d").is_dir() else [Path("/etc/ssh/sshd_config")]
        for f in files:
            if not f.exists():
                continue
            for line in f.read_text(errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                k, _, v = line.partition(" ")
                cfg.setdefault(k.lower(), v.strip())
    if not cfg:
        add("INFO", "ssh", "Конфиг SSH не прочитан без root")
        return
    if cfg.get("permitrootlogin", "").lower() == "yes":
        add("HIGH", "ssh", "PermitRootLogin yes — root по SSH разрешён")
    if cfg.get("passwordauthentication", "").lower() == "yes":
        add("MEDIUM", "ssh", "PasswordAuthentication yes — пароли разрешены")
    add("INFO", "ssh", f"Port {cfg.get('port', '22')}, root={cfg.get('permitrootlogin', '?')}, password={cfg.get('passwordauthentication', '?')}")


def check_firewall() -> None:
    rc, out = run(["ufw", "status"], timeout=10)
    if rc == 0 and "Status:" in out:
        state = "active" if "active" in out else "inactive"
        add("INFO" if state == "active" else "HIGH", "firewall", f"UFW {state}")
        return
    rc, out = run(["nft", "list", "ruleset"], timeout=10)
    if rc == 0 and out.strip():
        add("INFO", "firewall", "nftables: правила есть", f"{len(out.splitlines())} строк")
        return
    rc, out = run(["iptables", "-S"], timeout=10)
    if rc == 0 and len(out.splitlines()) > 3:
        add("INFO", "firewall", "iptables: правила есть", f"{len(out.splitlines())} строк")
    else:
        add("MEDIUM", "firewall", "Firewall не обнаружен или требует sudo")


def check_permissions() -> None:
    for p in (OW, OW / "agents", OW / "credentials"):
        if p.exists():
            m = p.stat().st_mode & 0o777
            if m & 0o077:
                add("HIGH", "permissions", f"{p} доступен не только владельцу", mode_str(p))
    leaked = []
    for pattern in ("**/*.token", "**/*secret*", "**/*credential*", "**/*.pem", "**/*.key"):
        for f in OW.glob(pattern):
            try:
                if f.is_file() and f.stat().st_mode & 0o004:
                    leaked.append(str(f))
            except OSError:
                pass
    if leaked:
        add("HIGH", "permissions", f"World-readable секретные файлы: {len(leaked)}", ", ".join(leaked[:5]))
    else:
        add("INFO", "permissions", "Секретные файлы не world-readable")


SECRET_PATTERNS = [
    ("api_key", re.compile(r"(?i)\b(?:api[_-]?key|apikey)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}")),
    ("bearer", re.compile(r"(?i)\bauthorization\b\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]


def check_secrets(limit_files: int = 4000) -> None:
    roots = [HOME / ".openclaw" / "workspace"]
    hits = []
    seen = 0
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", "media", "inbound", "dist", "__pycache__"}]
            for name in filenames:
                if not name.endswith((".md", ".txt", ".json", ".yaml", ".yml", ".env", ".sh", ".py", ".js", ".ts")):
                    continue
                seen += 1
                if seen > limit_files:
                    break
                f = Path(dirpath) / name
                try:
                    if f.stat().st_size > 512 * 1024:
                        continue
                    text = f.read_text(errors="ignore")
                except OSError:
                    continue
                for label, rx in SECRET_PATTERNS:
                    if rx.search(text):
                        hits.append(f"{f} ({label})")
                        break
            if seen > limit_files:
                break
    if hits:
        add("HIGH", "secrets", f"Похоже на секреты в открытом виде: {len(hits)}", "; ".join(hits[:6]))
    else:
        add("INFO", "secrets", "Открытых секретов в workspace не найдено")


def check_updates(quick: bool) -> None:
    if quick:
        return
    rc, out = run(["apt", "list", "--upgradable"], timeout=40)
    if rc != 0:
        add("INFO", "updates", "apt недоступен")
        return
    pkgs = [l.split("/")[0] for l in out.splitlines() if "/" in l and not l.startswith("Listing")]
    if pkgs:
        add("MEDIUM" if len(pkgs) > 20 else "LOW", "updates", f"Ждут обновления: {len(pkgs)} пакетов", ", ".join(pkgs[:8]))
    else:
        add("INFO", "updates", "Обновлений нет")


def check_backups() -> None:
    bdir = OW / "backups"
    if not bdir.exists():
        add("MEDIUM", "backups", "Каталог бэкапов не найден")
        return
    files = sorted((p for p in bdir.rglob("*") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        add("MEDIUM", "backups", "Бэкапов нет")
        return
    age_days = (datetime.now().timestamp() - files[0].stat().st_mtime) / 86400
    level = "INFO" if age_days < 14 else ("MEDIUM" if age_days < 30 else "HIGH")
    add(level, "backups", f"Последний бэкап {age_days:.0f} дн. назад", files[0].name)


def check_disk_encryption() -> None:
    rc, out = run(["lsblk", "-f"])
    if rc != 0:
        add("INFO", "disk", "lsblk недоступен")
        return
    if "crypto_LUKS" in out:
        add("INFO", "disk", "Шифрование диска (LUKS) найдено")
    else:
        add("LOW", "disk", "LUKS-шифрование не обнаружено")


def check_docker() -> None:
    if not shutil.which("docker"):
        return
    rc, out = run(["docker", "ps", "--format", "{{.Names}}|{{.Ports}}"], timeout=15)
    if rc != 0:
        add("INFO", "docker", "Docker не отвечает (нет прав?)")
        return
    names = []
    public = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        name, ports = line.split("|", 1)
        names.append(name)
        if "0.0.0.0:" in ports:
            public.append(name)
    add("INFO", "docker", f"Контейнеров запущено: {len(names)}")
    if public:
        add("MEDIUM", "docker", f"Порты на 0.0.0.0: {', '.join(public[:8])}")


def check_fail2ban() -> None:
    rc, out = run(["systemctl", "is-active", "fail2ban"], timeout=8)
    state = out.strip()
    add("INFO" if state == "active" else "LOW", "fail2ban", f"fail2ban: {state}")


# ── output ───────────────────────────────────────────────────────────────────

ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
ICON = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}


def report_markdown() -> str:
    findings = sorted(FINDINGS, key=lambda f: ORDER.get(f["level"], 9))
    counts = {k: sum(1 for f in findings if f["level"] == k) for k in ORDER}
    lines = [
        "# Security audit",
        "",
        f"_{datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M %Z')} · {os.uname().nodename}_",
        "",
        f"🔴 {counts['CRITICAL']} · 🟠 {counts['HIGH']} · 🟡 {counts['MEDIUM']} · 🔵 {counts['LOW']} · ⚪ {counts['INFO']}",
        "",
    ]
    for f in findings:
        if f["level"] == "INFO":
            continue
        lines.append(f"- {ICON[f['level']]} **{f['level']}** · {f['area']}: {f['message']}")
        if f["detail"]:
            lines.append(f"  - `{f['detail']}`")
    info = [f for f in findings if f["level"] == "INFO"]
    if info:
        lines += ["", "## Что в порядке", ""]
        for f in info:
            lines.append(f"- {f['area']}: {f['message']}" + (f" — `{f['detail']}`" if f["detail"] else ""))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    check_host()
    check_gateway()
    check_ports()
    check_ssh()
    check_firewall()
    check_permissions()
    check_secrets()
    check_updates(args.quick)
    check_backups()
    check_disk_encryption()
    check_docker()
    check_fail2ban()

    if args.json:
        print(json.dumps({"host": os.uname().nodename, "findings": FINDINGS}, ensure_ascii=False, indent=2))
    else:
        print(report_markdown())
    critical = sum(1 for f in FINDINGS if f["level"] in ("CRITICAL", "HIGH"))
    return 2 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
