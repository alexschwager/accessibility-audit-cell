#!/usr/bin/env python3
"""scan.py — the front door: audit ONE web page and print the findings.

    python3 scan.py --url https://example.com

Runs pa11y against the URL with TWO independent engines (HTML_CodeSniffer + axe-core,
per Canon Method 004), normalizes both into one findings register (the contract from
Canon Method 007: defect · WCAG criterion · severity · engine · selector · class), and
writes dated evidence you can hand to whoever owns the fix.

It reports AUTOMATED COVERAGE ONLY — never a conformance claim (Canon Method 003). A
clean run means "no automatically-detectable failures found," not "accessible." The
~43% of issues that need human + real-assistive-tech judgment are a separate lane.

Requirements (the tool shells out to pa11y; nothing to pip-install):
  - Node.js + npx      (pa11y is fetched on first run via `npx --yes pa11y`)
  - Google Chrome      (used headless; no Chromium download)
  - Python 3.8+        (stdlib only)

MIT-licensed; original work. This is the automated-scan slice of a larger audit cell —
see README. It does not do real-AT verification, routing, or conformance reporting.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Chrome locations tried in order; override with --chrome.
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    "/usr/bin/google-chrome",                                        # Linux
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",         # Windows
]

# pa11y HTML_CS gives no impact; map its type. axe gives an impact — used directly.
HTMLCS_SEVERITY = {"error": "serious", "warning": "moderate", "notice": "minor"}
AXE_SEVERITY = {"critical": "blocker", "serious": "serious",
                "moderate": "moderate", "minor": "minor"}

# Canon Method 008 — the six failure classes that carry ~96% of error volume.
def failure_class(text: str) -> str:
    t = text.lower()
    if "contrast" in t:
        return "low-contrast"
    if "alt" in t or ("image" in t and "text" in t):
        return "missing-alt-text"
    if "label" in t or ("form" in t and "field" in t):
        return "missing-form-label"
    if "link" in t and ("name" in t or "empty" in t or "content" in t):
        return "empty-link"
    if "button" in t and ("name" in t or "empty" in t):
        return "empty-button"
    if "lang" in t:
        return "document-language"
    return "other"


def find_chrome(override: str | None) -> str:
    if override:
        if not Path(override).exists():
            sys.exit(f"error: --chrome path does not exist: {override}")
        return override
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    sys.exit("error: Google Chrome not found. Install Chrome, or pass --chrome <path>.")


def wcag_from_htmlcs(code: str) -> str:
    """'WCAG2AA.Principle4.Guideline4_1.4_1_1.F77' -> '4.1.1' (the success criterion)."""
    m = re.search(r"\b(\d+)_(\d+)_(\d+)\b", code)
    return f"{m.group(1)}.{m.group(2)}.{m.group(3)}" if m else "—"


def run_pa11y(url: str, runner: str, raw_out: Path, chrome: str,
              timeout_s: int, wait_ms: int) -> list:
    """Run pa11y with one runner; write raw JSON; return the parsed issue list."""
    config = raw_out.parent / f".pa11y-config-{runner}.json"
    config.write_text(json.dumps({
        "chromeLaunchConfig": {"executablePath": chrome},
        "timeout": timeout_s * 1000,
        # Single-page apps (React/Vue/Nuxt) render AFTER load — audit too early and you
        # scan an empty shell (a false green). `wait` holds before testing so the app
        # hydrates. Raise it for content that streams in from an API.
        "wait": wait_ms,
    }), encoding="utf-8")
    env = dict(os.environ, PUPPETEER_SKIP_DOWNLOAD="true",
               PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true")
    cmd = ["npx", "--yes", "pa11y", "--reporter", "json",
           "--config", str(config), "--runner", runner, url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_s + 120, env=env)
    except FileNotFoundError:
        sys.exit("error: `npx` not found. Install Node.js (which provides npx).")
    except subprocess.TimeoutExpired:
        sys.exit(f"error: pa11y timed out on the {runner} engine after {timeout_s}s.")
    # pa11y exits 2 when it FINDS issues — that is a successful audit, not an error.
    if proc.returncode not in (0, 2) or not proc.stdout.strip():
        sys.exit(f"error: pa11y ({runner}) failed (exit {proc.returncode}):\n{proc.stderr.strip()}")
    raw_out.write_text(proc.stdout, encoding="utf-8")
    return json.loads(proc.stdout)


def normalize(issues: list, engine: str) -> list:
    out = []
    for i in issues:
        code = i.get("code", "")
        msg = i.get("message", "")
        if engine == "htmlcs":
            wcag = wcag_from_htmlcs(code)
            severity = HTMLCS_SEVERITY.get(i.get("type", ""), "moderate")
        else:  # axe
            wcag = code  # the axe rule id; the message carries a dequeuniversity link
            impact = (i.get("runnerExtras") or {}).get("impact", i.get("type", ""))
            severity = AXE_SEVERITY.get(impact, "moderate")
        out.append({
            "engine": f"pa11y/{engine}",
            "wcag": wcag,
            "severity": severity,
            "selector": i.get("selector", ""),
            "failure_class": failure_class(f"{code} {msg}"),
            "summary": msg[:200],
        })
    return out


SEV_ORDER = {"blocker": 0, "serious": 1, "moderate": 2, "minor": 3}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", required=True, help="the page to audit")
    p.add_argument("--out", default=None, help="output dir (default: ./audit-<date>-<host>)")
    p.add_argument("--title", default=None, help="human label for the surface")
    p.add_argument("--chrome", default=None, help="path to Chrome (auto-detected otherwise)")
    p.add_argument("--timeout", type=int, default=180, help="per-engine timeout, seconds")
    p.add_argument("--wait", type=int, default=1500,
                   help="ms to wait before auditing so single-page apps hydrate "
                        "(raise to 4000+ for content that streams from an API)")
    a = p.parse_args(argv)

    chrome = find_chrome(a.chrome)
    host = re.sub(r"[^a-z0-9]+", "-", a.url.split("//")[-1].lower()).strip("-")[:40]
    out = Path(a.out or f"audit-{date.today().isoformat()}-{host}")
    out.mkdir(parents=True, exist_ok=True)

    register = []
    print(f"Auditing {a.url}\n  Chrome: {chrome}\n  Wait:   {a.wait}ms "
          f"(raise with --wait if this is an API-driven single-page app)\n"
          f"  Output: {out}/\n")
    for runner in ("htmlcs", "axe"):
        print(f"  running pa11y ({runner}) …", flush=True)
        issues = run_pa11y(a.url, runner, out / f"pa11y-{runner}.json",
                           chrome, a.timeout, a.wait)
        register.extend(normalize(issues, runner))

    # Corroboration: same (wcag, selector) seen by both engines (Canon 004).
    keys = {}
    for f in register:
        keys.setdefault((f["wcag"], f["selector"]), set()).add(f["engine"])
    for f in register:
        f["corroborated"] = len(keys[(f["wcag"], f["selector"])]) > 1
    register.sort(key=lambda f: (not f["corroborated"], SEV_ORDER.get(f["severity"], 9)))

    corr = sum(1 for f in register if f["corroborated"])
    classes = {}
    for f in register:
        classes[f["failure_class"]] = classes.get(f["failure_class"], 0) + 1

    (out / "register.json").write_text(json.dumps(register, indent=2), encoding="utf-8")
    write_report(out / "report.md", a, register, corr, classes)

    # ---- stdout summary ----
    print(f"\n{'='*70}\nFINDINGS: {len(register)}  "
          f"({corr} corroborated by both engines)\n{'='*70}")
    print("\nBy failure class (the six that carry ~96% of error volume first):")
    for cls, n in sorted(classes.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {cls}")
    print("\nTop findings (corroborated first, then by severity):")
    for f in register[:15]:
        flag = "✓both" if f["corroborated"] else f["engine"].split("/")[1]
        print(f"  [{f['severity']:<8}] {f['wcag']:<10} {flag:<6} {f['selector'][:44]}")
    if len(register) > 15:
        print(f"  … and {len(register) - 15} more — full list in {out}/register.json")

    print(f"\n{'-'*70}")
    print("AUTOMATED COVERAGE ONLY — this is NOT a conformance claim (Canon 003).")
    print("A clean run means 'no auto-detectable failures', not 'accessible'. The")
    print("~43% needing human + real screen-reader judgment is a separate lane.")
    print("Fix owners & recommendations: open report.md.")
    print(f"{'-'*70}")
    return 0


def write_report(path: Path, a, register, corr, classes) -> None:
    lines = [
        f"# {a.title or a.url} — automated a11y scan — {date.today().isoformat()}",
        "",
        f"- generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- url: {a.url}",
        f"- findings: **{len(register)}** ({corr} corroborated by 2 independent engines)",
        "- scope: **AUTOMATED COVERAGE ONLY — never a conformance claim** (Canon Method 003).",
        "  HTML_CS and axe are two independent engines; a Lighthouse score would NOT be a",
        "  third (Lighthouse *is* axe) — Canon Method 004.",
        "",
        "## By failure class (Canon Method 008)",
        "",
        "| Failure class | Count |",
        "|---|---|",
    ]
    for cls, n in sorted(classes.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {cls} | {n} |")
    lines += [
        "",
        "## Register (corroborated first, then by severity — Canon Method 007)",
        "",
        "| Corrob. | Severity | WCAG / rule | Class | Engine | Selector | Summary |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in register:
        lines.append(
            f"| {'yes' if f['corroborated'] else '—'} | {f['severity']} | {f['wcag']} | "
            f"{f['failure_class']} | {f['engine']} | `{f['selector'][:60]}` | "
            f"{f['summary'][:80].replace('|', '/')} |")
    lines += [
        "",
        "## What to do with this",
        "",
        "1. **Corroborated + blocker/serious rows first** — two engines agreeing on a",
        "   transaction-path failure is the highest-confidence, highest-stakes fix.",
        "2. **Route by fix class, not page** — a low-contrast token or an unlabeled input",
        "   *component* fixes every instance at once; chase templates, not pages.",
        "3. **Single-engine rows need a human check** before routing — axe and HTML_CS each",
        "   have false positives the other doesn't.",
        "4. **This is the floor, not the ceiling.** Verify the money path with a real screen",
        "   reader before any 'accessible' claim reaches a customer.",
        "",
        "_Exposure, not legal advice: prioritise by user impact; verify primary sources",
        "(statutes, EUR-Lex, case law) before any external legal claim (Canon 002/009)._",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
