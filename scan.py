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
            "context": re.sub(r"\s+", " ", (i.get("context") or "")).strip()[:200],
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

    groups = group_findings(register)
    (out / "register.json").write_text(json.dumps(register, indent=2), encoding="utf-8")
    write_report(out / "report.md", a, register, corr, classes)
    write_html_report(out / "report.html", a, register, corr, classes, groups)
    write_fix_brief(out / "fix-brief.md", a, groups)

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
    print(f"\n  Visual report : {out}/report.html   (open in a browser)")
    print(f"  Fix for an AI : {out}/fix-brief.md   (paste into Claude / Codex / Gemini)")
    print(f"  Raw evidence  : {out}/register.json")
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


def group_findings(register: list) -> list:
    """Group by failure class → the unit you actually fix. Worst severity first."""
    g = {}
    for f in register:
        k = f["failure_class"]
        grp = g.setdefault(k, {"failure_class": k, "count": 0, "wcag": set(),
                               "worst": "minor", "selectors": [], "context": ""})
        grp["count"] += 1
        grp["wcag"].add(f["wcag"])
        grp["selectors"].append(f["selector"])
        if SEV_ORDER.get(f["severity"], 9) < SEV_ORDER.get(grp["worst"], 9):
            grp["worst"] = f["severity"]
        if not grp["context"] and f.get("context"):
            grp["context"] = f["context"]
    out = list(g.values())
    for grp in out:
        grp["wcag"] = ", ".join(sorted(grp["wcag"]))
        grp["cards"] = len({s.split(" > ")[0] for s in grp["selectors"]})
    out.sort(key=lambda x: (SEV_ORDER.get(x["worst"], 9), -x["count"]))
    return out


# One-instance-per-class remediation guidance (generic; the model fills the specifics).
FIX_HINT = {
    "low-contrast": "Raise the text (or background) colour until the pair clears 4.5:1 (AA). "
                    "Fix it at the design-token / component level, not per page.",
    "missing-alt-text": "Give every meaningful image an accurate `alt`; mark decorative images "
                        "`alt=\"\"`. Enforce it in the image component so it can't regress.",
    "missing-form-label": "Associate a visible `<label>` (or an accessible name) with every input. "
                          "Make the field component require a label prop.",
    "empty-link": "Give the link real text or an accessible name (icon links need `aria-label`). "
                  "The link component should reject an empty accessible name.",
    "empty-button": "Give the button an accessible name (text or `aria-label`). "
                    "The button component should require one.",
    "document-language": "Set a valid `lang` on `<html>` (e.g. `lang=\"en\"`).",
    "other": "Read the rule link in each finding; fix at the component level where possible.",
}


def write_fix_brief(path: Path, a, groups: list) -> None:
    """A paste-ready remediation brief for a coding agent (Claude / Codex / Gemini)."""
    L = [
        f"# Accessibility fix brief — {a.title or a.url}",
        "",
        f"Source: automated scan of {a.url} ({date.today().isoformat()}), engines "
        "axe-core + HTML_CodeSniffer.",
        "",
        "## Paste this to your coding agent",
        "",
        "> You are fixing accessibility issues found by an automated scan. Each group below is a",
        "> real, grounded defect: a real WCAG criterion, a real failing element, real selectors.",
        "> For each group, propose the **minimal** code change, and prefer a single component or",
        "> design-token fix over editing many pages. Show me the diff before applying it, and ask",
        "> before touching shared tokens. **Do not** claim the page is \"accessible\" or \"WCAG",
        "> compliant\" afterward — an automated scan covers ~57% of issues by volume; fixing these",
        "> raises the floor, it is not conformance. Keyboard, focus order, and screen-reader",
        "> behaviour still need a human check.",
        "",
        "## The findings (highest leverage first)",
        "",
    ]
    for i, grp in enumerate(groups, 1):
        scope = f"{grp['count']} instance{'s' if grp['count'] != 1 else ''}"
        if grp["cards"] > 1:
            scope += f" across {grp['cards']} components/blocks — likely ONE fix"
        L += [
            f"### {i}. {grp['failure_class']} — {scope}",
            f"- **WCAG / rule:** {grp['wcag']}  ·  **severity:** {grp['worst']}",
            f"- **Failing element (representative):** `{grp['context'] or 'see register.json'}`",
            f"- **Example selector:** `{grp['selectors'][0]}`"
            + (f"  (+{len(grp['selectors'])-1} more in register.json)" if len(grp['selectors']) > 1 else ""),
            f"- **How to fix:** {FIX_HINT.get(grp['failure_class'], FIX_HINT['other'])}",
            "",
        ]
    L += ["---", "_Generated by scan.py. Automated coverage only — never a conformance claim._"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


REPORT_CSS = """
:root{
  --bg:#f4f6fa; --surface:#ffffff; --surface-2:#eef1f7; --ink:#1a1d26;
  --muted:#5a6172; --border:#dfe3ec; --accent:#4b56c8; --accent-ink:#3a44a8;
  --blocker:#c0392b; --serious:#cf5b23; --moderate:#b8860b; --minor:#6b7280; --good:#2e9e6b;
}
:root:not([data-theme="light"]){ }
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#101219; --surface:#191c25; --surface-2:#20242f; --ink:#e9ebf2;
  --muted:#9aa2b4; --border:#2b2f3b; --accent:#8b93f0; --accent-ink:#aab0f5;
  --blocker:#e2604f; --serious:#e6884f; --moderate:#d9ad3f; --minor:#8b91a3; --good:#4cc389;
}}
:root[data-theme="dark"]{
  --bg:#101219; --surface:#191c25; --surface-2:#20242f; --ink:#e9ebf2;
  --muted:#9aa2b4; --border:#2b2f3b; --accent:#8b93f0; --accent-ink:#aab0f5;
  --blocker:#e2604f; --serious:#e6884f; --moderate:#d9ad3f; --minor:#8b91a3; --good:#4cc389;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif;line-height:1.55;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:40px 24px 80px}
h1{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:2.1rem;line-height:1.1;
  margin:0 0 6px;text-wrap:balance}
h2{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:1.35rem;margin:44px 0 14px}
.sub{color:var(--muted);font-size:.95rem;margin:0}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
a{color:var(--accent-ink);text-underline-offset:2px}
.banner{margin:22px 0 8px;padding:14px 18px;border-radius:10px;
  background:var(--surface-2);border:1px solid var(--border);border-left:4px solid var(--accent);
  font-size:.92rem;color:var(--ink)}
.banner b{color:var(--accent-ink)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:20px 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px}
.tile .n{font-size:2rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1}
.tile .l{color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;margin-top:6px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 0}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border-radius:999px;
  background:var(--surface);border:1px solid var(--border);font-size:.82rem;font-variant-numeric:tabular-nums}
.dot{width:9px;height:9px;border-radius:50%}
.sev-blocker{background:var(--blocker)}.sev-serious{background:var(--serious)}
.sev-moderate{background:var(--moderate)}.sev-minor{background:var(--minor)}
.group{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:0;margin:14px 0;overflow:hidden}
.group-h{display:flex;align-items:center;gap:12px;padding:15px 18px;border-bottom:1px solid var(--border)}
.group-h .stripe{width:5px;align-self:stretch;border-radius:3px;min-height:36px}
.group-h .t{font-weight:600;font-size:1.05rem}
.group-h .meta{color:var(--muted);font-size:.85rem;margin-left:auto;text-align:right}
.group-b{padding:14px 18px;font-size:.9rem}
.kv{color:var(--muted)}
.el{display:block;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;
  padding:10px 12px;margin:8px 0;font-size:.82rem;overflow-x:auto;white-space:pre}
.fix{margin-top:8px}
.fix b{color:var(--good)}
.tablewrap{overflow-x:auto;border:1px solid var(--border);border-radius:12px;margin-top:12px}
table{border-collapse:collapse;width:100%;font-size:.83rem}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--border);white-space:nowrap}
th{background:var(--surface-2);font-weight:600;color:var(--muted);text-transform:uppercase;
  letter-spacing:.05em;font-size:.72rem}
td.sel{max-width:340px;overflow:hidden;text-overflow:ellipsis}
tr:last-child td{border-bottom:none}
.foot{margin-top:40px;padding-top:18px;border-top:1px solid var(--border);color:var(--muted);font-size:.85rem}
"""


def write_html_report(path, a, register, corr, classes, groups):
    sev_counts = {}
    for f in register:
        sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
    chips = "".join(
        f'<span class="chip"><span class="dot sev-{s}"></span>{n} {s}</span>'
        for s in ("blocker", "serious", "moderate", "minor") if (n := sev_counts.get(s)))
    class_chips = "".join(
        f'<span class="chip">{n} {_esc(c)}</span>'
        for c, n in sorted(classes.items(), key=lambda kv: -kv[1]))

    group_html = []
    for grp in groups:
        scope = f"{grp['count']} instance" + ("s" if grp["count"] != 1 else "")
        if grp["cards"] > 1:
            scope += f" · {grp['cards']} blocks · likely one fix"
        group_html.append(f"""
      <div class="group">
        <div class="group-h">
          <span class="stripe sev-{grp['worst']}"></span>
          <span class="t">{_esc(grp['failure_class'])}</span>
          <span class="meta">{scope}<br>{_esc(grp['wcag'])} · {grp['worst']}</span>
        </div>
        <div class="group-b">
          <span class="kv">Representative failing element</span>
          <code class="el mono">{_esc(grp['context'] or 'see register.json')}</code>
          <div class="fix"><b>Fix →</b> {_esc(FIX_HINT.get(grp['failure_class'], FIX_HINT['other']))}</div>
        </div>
      </div>""")

    rows = "".join(
        f"<tr><td>{'✓ both' if f['corroborated'] else _esc(f['engine'].split('/')[1])}</td>"
        f'<td><span class="chip"><span class="dot sev-{f["severity"]}"></span>{f["severity"]}</span></td>'
        f'<td class="mono">{_esc(f["wcag"])}</td><td>{_esc(f["failure_class"])}</td>'
        f'<td class="sel mono">{_esc(f["selector"])}</td></tr>'
        for f in register[:200])

    title = _esc(a.title or a.url)
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accessibility scan — {title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{REPORT_CSS}</style></head><body><div class="wrap">
  <p class="sub mono">ACCESSIBILITY SCAN · {date.today().isoformat()}</p>
  <h1>{title}</h1>
  <p class="sub"><a href="{_esc(a.url)}">{_esc(a.url)}</a></p>
  <div class="banner"><b>Automated coverage only — this is NOT a conformance claim.</b>
    Two engines (axe-core + HTML_CodeSniffer) found what software can find — about 57% of
    issues by volume. A clean run means “no auto-detectable failures,” not “accessible”:
    keyboard operation, focus order, and real screen-reader behaviour are not tested here.</div>
  <div class="tiles">
    <div class="tile"><div class="n">{len(register)}</div><div class="l">Findings</div></div>
    <div class="tile"><div class="n">{corr}</div><div class="l">Corroborated (2 engines)</div></div>
    <div class="tile"><div class="n">{len(groups)}</div><div class="l">Fix groups</div></div>
  </div>
  <div class="chips">{chips}</div>
  <h2>What to fix (highest leverage first)</h2>
  <p class="sub">Grouped by defect type — the unit you actually fix. One component or token
    change usually clears a whole group. Hand these to a coding agent via <code
    class="mono">fix-brief.md</code>.</p>
  {''.join(group_html)}
  <h2>By failure class</h2>
  <div class="chips">{class_chips}</div>
  <h2>Full register</h2>
  <p class="sub">Corroborated first, then by severity. {('First 200 of %d shown; ' % len(register)) if len(register) > 200 else ''}complete data in <code class="mono">register.json</code>.</p>
  <div class="tablewrap"><table><thead><tr><th>Engine</th><th>Severity</th><th>WCAG / rule</th>
    <th>Class</th><th>Selector</th></tr></thead><tbody>{rows}</tbody></table></div>
  <p class="foot">Generated by <b>scan.py</b> · axe-core + HTML_CodeSniffer via pa11y ·
    Exposure is not legal advice; verify primary sources before any external claim.</p>
</div></body></html>"""
    path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
