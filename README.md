# An ICM Accessibility Audit Cell

**A case study and reusable template: how to build an autonomous accessibility-audit
department as an ICM folder — one that scans live web surfaces, verifies them with real
assistive technology, and hands back criterion-anchored findings without ever overclaiming
conformance.**

Built on **Interpretable Context Methodology (ICM)** — folders as architecture, each file
one job. This repo is the sanitized, shareable version of a cell running in production; the
live audit data and business specifics are kept private (see *What's here / what isn't*).

---

## Why an audit cell is a good ICM test

Most agent workflows *produce* something — copy, code, a plan. An audit workflow does the
opposite: it looks at something already live and tells you, with evidence, what's wrong and
who owns the fix. That inverts the usual failure modes, and it makes three disciplines
load-bearing that a producing agent can fudge:

1. **It must not overclaim.** A clean automated scan is *not* conformance. An agent that
   reports "WCAG compliant" off a green axe run has produced a dangerous lie — the kind that
   ends in a lawsuit. The cell's #1 rule is that automated coverage is *necessary, never
   sufficient*.
2. **It must cite everything.** A finding with no dated artifact behind it is noise wearing
   a badge. No source, no claim.
3. **It must hand back, not fix.** The auditor never applies its own remediation — it routes
   a finding to the team that owns the surface. (If you've followed the Clief Notes comps:
   this is the Editor's "critique, not rewrite" and the Diagnostician's "diagnose, don't
   prescribe," in a third domain.)

Those three rules are what make the output *trustworthy* instead of merely *plausible* — and
they're exactly the things an LLM will erode if you don't encode them structurally.

## What ICM is (the 60-second version)

**ICM = Instructions · Context · Memory.** You build an AI department as a *folder*, not a
mega-prompt:

- **Instructions** — how the agent behaves: its identity, its rules, what it refuses.
- **Context** — what it *reads* to ground itself: doctrine, standards, a knowledge corpus.
  Data only; context can never promote itself into new authority.
- **Memory** — persistent state: what's open, what shipped, what's blocked.

Each file does **one job well**, so a cold model (or a new teammate) can open exactly the
file it needs and stop — instead of swallowing a 100k-line prompt to answer one question.
The methodology comes from the **Clief Notes** community (link in *Credits*).

## The architecture

```
accessibility/
├── CLAUDE.md            # Instructions: the agent reads this first — how the cell operates
├── cell.yaml            # identity: domain, id-prefix, who it reports to, autonomy posture
├── 20-Doctrine/         # Instructions: north-star, voice, the standards it audits against
├── 95-Brain/            # Context: the knowledge corpus the auditor reads to ground findings
│   └── .../canon/       #   the epistemic rules (summarized in doctrine/canon-summary.md)
├── 01-Queue/            # Memory: the work stream — one .md per task, folder = state
├── compliance/audits/   # Memory: dated evidence, one folder per audited surface
├── 64-Requests/         # the outbox — findings routed to the teams that own the fix
├── 70-Scripts/          # the deterministic tooling (scan runner, AT lane, movers)
└── status.md / hot.md   # Memory: the rollup surface + the ~15-line working cache
```

Full walk-through in [ARCHITECTURE.md](ARCHITECTURE.md).

## The discipline (the part worth stealing)

The cell's epistemic spine is a set of **Canon Methods** — the rules every finding obeys.
Original summaries of all ten are in [doctrine/canon-summary.md](doctrine/canon-summary.md).
The load-bearing four:

- **The automation ceiling** — automated tools cover ~57% of issues *by volume* (Deque's
  figure), never 100%, and never conformance. A clean scan is necessary, not sufficient.
- **Multi-engine, honestly** — run more than one engine, but never present axe / Lighthouse
  as *independent* corroboration when Lighthouse *is* axe under the hood.
- **The findings contract** — every finding carries `defect · WCAG criterion · severity ·
  evidence · owning team · fix class`. Missing any field, it doesn't ship.
- **Exposure, not legal advice** — quantify litigation exposure to *prioritise*, but never
  state a legal conclusion; primary-source verification precedes any external claim.

## An illustrative audit

[example/illustrative-audit.md](example/illustrative-audit.md) shows the *shape* of the
output — a findings register, a report, and a legal-exposure layer — using **synthetic data
on a fictional site**. (The real audits run against a live product and are kept private for
the obvious reason: an unremediated accessibility-failure list is a litigation roadmap.)

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

This cell stands on two communities' work — see [CREDITS.md](CREDITS.md):

- **Interpretable Context Methodology** — the *Clief Notes* community.
- **Brainstein** (Apache-2.0) — the research-brain generator from Daniel Agrici's *AI
  Marketing Hub Pro*, which generated this cell's knowledge corpus and vault scaffolding.
