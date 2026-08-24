# The Canon — the ten rules an audit finding obeys

Original summaries of the cell's ten Canon Methods: the epistemic spine that makes an
accessibility finding *trustworthy* instead of merely *plausible*. Generic and sanitized —
swap "the audited product" for yours. The full methods live in the private cell's brain; these
are the shareable distillation (per the cell's publishing policy).

The whole point: an LLM will happily tell you a page is "accessible" off a green scan. These
rules are what stop it.

---

**001 — POUR and the shape of WCAG.** WCAG isn't an arbitrary rule pile: four principles
(**Perceivable, Operable, Understandable, Robust**), each expanding into testable success
criteria. Knowing the shape kills two failure modes — treating WCAG as a checklist, and
inventing "accessibility work" that maps to no criterion at all. Every finding anchors to a
specific criterion or it isn't a finding.

**002 — Conformance target: engineer to 2.2 AA, report against 2.1 AA.** The *legal* benchmark
and the *current* W3C recommendation are different WCAG versions. The EU's EN 301 549 (and the
European Accessibility Act, enforceable since 2025-06-28) names **2.1 AA** for web content and
reaches non-EU businesses selling to EU consumers; the current W3C Recommendation is **2.2 AA**.
Build to the higher line, report against the one the law actually names. Pick one and ignore the
other and you either under-build or misreport.

**003 — The automation ceiling: ~57% by volume, never a conformance claim.** Automated tools
cover roughly **57% of issues by volume** (Deque's figure across thousands of audits) — not the
"30%" folklore (that's the share of *success criteria*, a different denominator). But coverage
is never conformance. **A clean automated pass is necessary, never sufficient.** The other ~43%
— is the alt text actually descriptive? is the focus order logical? — needs human judgment. This
is the single most important rule; violating it is how programmes ship a lie.

**004 — Multi-engine, honestly.** Engines encode different rule sets, so they catch
non-identical defects; run more than one and cross-compare. But mind the trap: **Lighthouse's
accessibility category IS axe-core.** A Lighthouse score is not independent corroboration of an
axe scan — never present them as two engines agreeing. Genuine independence means a truly
separate rule set (e.g. IBM Equal Access alongside axe).

**005 — The catch-point ladder: lint → component → e2e → budget → AT.** Every defect has a
cheapest catch point, and every rung it survives multiplies its cost: a red squiggle at lint
time becomes a failed component test, then a failed audit, then a lost booking or a legal
notice. Kill each defect class at its cheapest rung — lint (`eslint-plugin-jsx-a11y`), component
(`jest-axe` + query-by-role), e2e, budgets, and real-AT at the top.

**006 — Real-AT verification: the guidepup lane.** Only real assistive technology earns the word
*conformant*. `guidepup` drives the actual OS screen readers (VoiceOver, NVDA) from a test
harness — what it asserts is what the screen reader really spoke. It's expensive, so it's scoped,
scripted, and reserved for the money paths. A simulated screen-reader tree-walk is useful for
unit tests but is **not** conformance evidence.

**007 — The findings contract: defect → criterion → severity → owner.** The cell's product is
findings another team can act on *without interpretation*. Every finding carries, every time:
**defect** (observable, on which surface/state), **WCAG criterion**, **severity** (graded by
user impact on the money path, not rule category), **evidence** (dated scan artifact or AT
speech log — no source, no claim), **owning team**, and **fix class** (one-off vs template vs
standard-gap — template fixes kill whole defect populations). Missing a field, it's noise.

**008 — The six failure classes: ~96% of the error volume.** Eight years of the WebAIM Million
say the detectable failure volume is dominated by six classes — low-contrast text, missing alt
text, missing form labels, empty links, empty buttons, missing document language — ~96% of all
errors. All six are automation-detectable with mechanical, mostly *template-level* fixes. Start
every audit here: cheap to find, cheap to fix, enormous coverage.

**009 — Reporting: VPAT/ACR and the accessibility statement.** Reporting turns audit knowledge
into standing commitments others rely on, governed by one rule: **no conformance claim without a
dated audit artifact behind it.** An overclaimed statement is worse than none — it converts a
defect into a misrepresentation. The honest artifacts: a per-criterion ACR (Supports / Partially
/ Does Not / N/A), and a public accessibility statement naming the target standard, known
limitations, a feedback channel, and the date last reviewed.

**010 — Continuous conformance: budgets, ratchets, refresh.** A one-off audit is a photo of a
moving object, and the web's default trajectory is *decay* (complexity and error counts rising
year over year). Conformance erodes every sprint unless something structural holds it: CI
**budgets** that fail the build below a floor, **ratchets** that pin cleaned pages at zero errors,
and scheduled **refresh** audits. The floor only ever rises.

---

### The three invariants underneath all ten

1. **Don't overclaim** (003, 009) — automated ≠ conformant; no claim without a dated artifact.
2. **Cite everything** (007) — a finding with no evidence is not a finding.
3. **Hand back, don't fix** — the auditor routes to the owner; it never applies its own remediation.

Change the standard, change the tools, change the domain — keep these three and you have an audit
you can trust.
