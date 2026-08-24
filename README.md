# Accessibility Audit Cell

**A case study and reusable template: an autonomous accessibility-audit department that scans
live web surfaces, verifies them with real assistive technology, and hands back
criterion-anchored findings — without ever overclaiming conformance.**

Its knowledge brain was built with **Brainstein** (see *Credits*); the doctrine, audit
pipeline, and discipline are the cell's own. This repo is the sanitized, shareable version of a
cell running in production — the live audit data and business specifics are kept private (see
*What's here / what isn't*).

---

## Why accessibility auditing is hard to automate honestly

Most agent workflows *produce* something — copy, code, a plan. An audit does the opposite: it
looks at something already live and tells you, with evidence, what's wrong and who owns the fix.
That inverts the usual failure modes, and it makes three disciplines load-bearing that a
producing agent can fudge:

1. **It must not overclaim.** A clean automated scan is *not* conformance. An agent that reports
   "WCAG compliant" off a green axe run has produced a dangerous lie — the kind that ends in a
   lawsuit. The cell's #1 rule is that automated coverage is *necessary, never sufficient*.
2. **It must cite everything.** A finding with no dated artifact behind it is noise wearing a
   badge. No source, no claim.
3. **It must hand back, not fix.** The auditor never applies its own remediation — it routes a
   finding to the team that owns the surface.

Those three rules are what make the output *trustworthy* instead of merely *plausible* — exactly
the things an LLM will erode if you don't encode them structurally.

## How it's built

A "cell" is a self-contained AI-agent department: one domain, its own agent roster, talking to
sibling teams only through files. This one audits accessibility. It's a **folder where each file
does one job**, so a cold model (or a new teammate) opens exactly the file it needs and stops —
instead of swallowing a 100k-line prompt to answer one question.

```
accessibility/
├── CLAUDE.md            # the operating manual the agent reads first
├── cell.yaml            # identity: domain, id-prefix, who it reports to, autonomy posture
├── 20-Doctrine/         # north-star, voice, and the standards it audits against
├── 95-Brain/            # the knowledge corpus the auditor reads to ground findings (built with Brainstein)
│   └── .../canon/       #   the epistemic rules (summarized in doctrine/canon-summary.md)
├── 01-Queue/            # the work stream — one .md per task, folder = state
├── compliance/audits/   # dated evidence, one folder per audited surface
├── 64-Requests/         # the outbox — findings routed to the teams that own the fix
├── 70-Scripts/          # the deterministic tooling (scan runner, AT lane, movers)
└── status.md / hot.md   # the rollup surface + the ~15-line working cache
```

Full walk-through in [ARCHITECTURE.md](ARCHITECTURE.md). The knowledge layer (`95-Brain/`) was
generated with **Brainstein** — a domain turned into a structured, evidence-gated brain the
agent stands on instead of improvising from training data.

## The discipline (the part worth stealing)

The cell's epistemic spine is a set of **Canon Methods** — the rules every finding obeys.
Original summaries of all ten are in [doctrine/canon-summary.md](doctrine/canon-summary.md).
The load-bearing four:

- **The automation ceiling** — automated tools cover ~57% of issues *by volume* (Deque's
  figure), never 100%, and never conformance. A clean scan is necessary, not sufficient.
- **Multi-engine, honestly** — run more than one engine, but never present axe / Lighthouse as
  *independent* corroboration when Lighthouse *is* axe under the hood.
- **The findings contract** — every finding carries `defect · WCAG criterion · severity ·
  evidence · owning team · fix class`. Missing any field, it doesn't ship.
- **Exposure, not legal advice** — quantify litigation exposure to *prioritise*, but never state
  a legal conclusion; primary-source verification precedes any external claim.

## An illustrative audit

[example/illustrative-audit.md](example/illustrative-audit.md) shows the *shape* of the output —
a findings register, a report, and a legal-exposure layer — using **synthetic data on a
fictional site**. (The real audits run against a live product and are kept private for the
obvious reason: an unremediated accessibility-failure list is a litigation roadmap.)

## Adapting this to your own domain

The audit-cell shape generalises. To point it at your world:

1. Swap `95-Brain/` for your domain's corpus (the standards, the tooling, the failure modes).
2. Rewrite the Canon Methods for *your* "clean scan ≠ done" trap — every audit domain has one.
3. Keep the three invariants intact: **don't overclaim · cite everything · hand back, don't fix.**
4. Keep the findings contract; change the criterion vocabulary (WCAG → your standard).

## What's here / what isn't

**Here (publishable):** the architecture, the doctrine summaries, a synthetic example, the credits.

**Not here (private, by policy):** the live audit findings and legal-exposure of the real
product, any business/revenue strategy, credentials, raw captures, and internal ledgers. The
running cell enforces this split with a publishing policy; this repo is the sanitized side of it.

## Credits

See [CREDITS.md](CREDITS.md) for the full attributions:

- **[Brainstein](https://github.com/AI-Marketing-Hub/Brainstein)** (Apache-2.0) — the
  research-brain generator from Daniel Agrici's [AI Marketing Hub Pro](https://www.skool.com/ai-marketing-hub-pro/about?ref=b2a583ea4cd142a39b73210fbf731d55).
  This is what built the cell's knowledge corpus and vault scaffolding — the layer everything
  else stands on.
- **[Clief Notes](https://www.skool.com/cliefnotes/about?ref=b2a583ea4cd142a39b73210fbf731d55)** —
  the interpretable-context methodology (folders as architecture, each file one job) that shaped
  how the whole cell is organised.

Licensed **MIT** (see [LICENSE](LICENSE)) — use it, adapt it, ship your own.
