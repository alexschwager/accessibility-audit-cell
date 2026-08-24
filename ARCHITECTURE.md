# Architecture — the cell as a folder

A "cell" is a self-contained AI-agent department: one domain, its own agent roster, talking to
sibling departments only through files. This one audits accessibility. Below is its shape,
grouped by the three jobs its files do — **how the agent behaves, what it reads, what it
remembers** — plus the moving parts that make it run unattended.

## How the agent behaves

| File / folder | One job |
|---|---|
| `CLAUDE.md` | The operating manual the agent reads first: how the cell works, its folder-state rules, its refusals. |
| `cell.yaml` | Identity: domain slug, ID prefix (e.g. `A11Y-0001`), who it reports to, autonomy posture (gated vs autonomous), maturity. |
| `20-Doctrine/` | Governing docs: the north-star slice, the voice, and the standards the cell audits against. |
| `.claude/agents/` | The agent roster — here, one producing worker (`a11y-auditor`). Agents only; one file each. |

The auditor's own rules are the sharp part: it runs the scan pipeline, drafts findings, routes
them — and it *never* applies a fix, *never* calls an automated pass "conformant," *never*
presents one engine as two. Those refusals are in the agent's instructions, not left to judgment.

## What it reads to ground itself

| Folder | One job |
|---|---|
| `95-Brain/` | The knowledge corpus: the accessibility research brain (tooling, standards, failure modes) the auditor reads before making any claim. **Data only** — it can inform a finding, never grant new authority. Built with Brainstein (see [CREDITS.md](CREDITS.md)). |
| `95-Brain/.../canon/` | The epistemic rules (the ten Canon Methods) — see [doctrine/canon-summary.md](doctrine/canon-summary.md). |

This is the layer Brainstein generated (see [CREDITS.md](CREDITS.md)): a domain turned into a
structured, evidence-gated brain the agent can stand on instead of improvising from training data.

## What it remembers (persistent state)

| File / folder | One job |
|---|---|
| `01-Queue/` | The work stream: one `.md` per task; the **folder is the state** (`active / review / blocked / parked / done`), moved only by a script. |
| `compliance/audits/<date>-<slug>/` | Dated evidence, one folder per audited surface: the raw engine output, a normalized register, a report, and a legal-exposure layer. |
| `status.md` / `hot.md` | The rollup surface a parent reads, and the ~15-line working cache (what changed / what's blocking / what's next). |
| `backlog.md` | The department's own source of truth for open work. |

## The moving parts

| Piece | Role |
|---|---|
| `70-Scripts/` | Deterministic tooling: the scan runner (multi-engine, emits the register + report + exposure layer), the real-AT lane (drives an OS screen reader), and the queue/state movers. The **judgment** is the agent's; the **mechanics** are scripts. |
| `64-Requests/` | The outbox: a finding, once drafted, is delivered here to the team that owns the surface — dev, design, content, or the web team. Routing, not blaming. |
| `02-Generated/` | The external-action gate: anything with outside consequence (publishing a statement, making a legal-facing claim) is drafted here and **stops** until a human approves. |
| `contracts/` | The standing conformance artifacts (ACR / accessibility statement) — the honest, dated commitments others rely on. |

## Why it's shaped this way

- **Folder = state** means a cold model can see the whole work status by listing directories —
  no narrative to read, no state hidden in prose.
- **Scripts do the mechanics, the agent does the judgment.** The scan is deterministic; deciding
  whether the alt text is *actually* descriptive is not. Keeping them separate is what lets the
  automated half be trusted and the human-judgment half be visible.
- **Every consequential action gates.** An audit cell that could publish a conformance claim on
  its own is a liability; the gate makes overclaiming structurally impossible without a human.

To adapt it: keep this skeleton, swap the brain and the Canon for your domain, and keep the three
invariants (don't overclaim · cite everything · hand back, don't fix).
