# Getting started — your first scan in ~5 minutes

New here? This is the step-by-step. It assumes you've never used an accessibility scanner
before. There's no app to install and nothing to sign up for — you run one command and get
back a report plus a list of fixes you can hand to an AI.

> **What this does:** points two accessibility engines at a web page, tells you what's wrong
> (with exact locations), and writes a fix list. It never claims a page is "compliant" — an
> automated scan is a floor, not a pass.

---

## Step 1 — check you have the two things it needs

The scanner drives a real browser, so you need two free programs. Open a terminal and check:

```bash
node --version      # need Node.js — https://nodejs.org (any recent version)
```

- **Node.js** — if `node --version` prints a number, you're set. If it says "command not
  found", install it from <https://nodejs.org> (the "LTS" button), then reopen the terminal.
- **Google Chrome** — just have it installed the normal way (<https://google.com/chrome>).
  The scanner finds it automatically on Mac, Windows, and Linux.

(You do **not** need to install `pa11y` or anything Python — the scanner handles that itself.)

## Step 2 — get the code

```bash
git clone https://github.com/alexschwager/accessibility-audit-cell
cd accessibility-audit-cell
```

## Step 3 — run your first scan

Point it at any page. Start with a deliberately-broken demo page so you can see it find things:

```bash
python3 scan.py --url https://www.w3.org/WAI/demos/bad/before/home.html
```

The first run takes a moment (it fetches the scanner in the background). You'll see it work,
then a summary of the findings in your terminal.

Now try your own page:

```bash
python3 scan.py --url https://your-site.com/the-page-you-care-about
```

> **If your site is a modern app (React, Vue, Nuxt, Angular)** and you get suspiciously few
> findings, add a wait so the page finishes loading before it's scanned:
> ```bash
> python3 scan.py --url https://your-site.com/page --wait 6000
> ```
> (A real example: a page scored 1 finding without this and 61 with it. Details in the README.)

## Step 4 — read what came back

The scan writes a dated folder (e.g. `audit-2026-08-24-your-site-com/`) containing:

- **`report.html`** — open this in your browser. It's the readable version: a summary, the
  issues grouped by type, and severity colours. **This is the one to look at and share.**
- **`fix-brief.md`** — the list of fixes (see Step 5).
- `register.json` / `report.md` — the same data for a developer or a script.

To open the report on a Mac: `open audit-*/report.html` (Windows: `start`, Linux: `xdg-open`).

## Step 5 — get the fixes done (hand it to an AI)

Open **`fix-brief.md`**. The top is a ready-made instruction; below it are the grouped findings.
**Copy the whole file and paste it into Claude, Codex, or Gemini**, pointed at your website's
code. It will propose the minimal change for each group — and the brief tells it *not* to claim
the page is now "compliant," because that would be dishonest.

That's the whole loop: **scan a page → read the report → paste the brief into an AI → it fixes.**

---

## What it does *not* do (so you don't over-trust it)

- It does **not** prove a page is accessible. Automated tools catch roughly half of issues; a
  clean scan means "nothing a machine can catch," not "a disabled person can use this."
- It does **not** test keyboard use, focus order, or screen-reader experience — those need a
  human. See [ARCHITECTURE.md](ARCHITECTURE.md) for how a full audit adds those.
- It does **not** give legal advice. It flags exposure to help you prioritise; verify the law
  before making any external claim.

## Stuck?

- **"python3: command not found"** → try `python`. On Windows, install Python from
  <https://python.org> if neither works.
- **"npx not found" / Node errors** → Node.js isn't installed or the terminal needs reopening
  after installing it (Step 1).
- **"Chrome not found"** → install Chrome, or point at it directly:
  `python3 scan.py --url … --chrome "/path/to/chrome"`.
- **Way too few findings on a modern site** → add `--wait 6000` (Step 3).

Then read the [doctrine](doctrine/canon-summary.md) — the ten rules that keep a scan honest.
