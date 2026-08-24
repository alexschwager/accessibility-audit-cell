# Illustrative audit — SYNTHETIC DATA

> **This is a fabricated example on a fictional site (`shop.example.com`), for showing the
> output *shape* only.** No real audit findings appear in this public repo — an unremediated
> accessibility-failure list on a real site is a litigation roadmap, so the live audits are kept
> private. Selectors, counts, and IDs below are invented.

An audit of one surface produces three artifacts in `compliance/audits/<date>-<slug>/`: a
**findings register**, a **report**, and a **legal-exposure layer**. Here's the shape of each.

---

## 1. Findings register (the machine record — `register.json`)

Each finding carries the full contract (Canon 007): defect · criterion · severity · engines ·
selector · owner · fix class.

| Severity | WCAG | Class | Engines | Selector | Owner | Fix class |
|---|---|---|---|---|---|---|
| serious | 1.4.3 Contrast (AA) | low-contrast | axe + htmlcs | `.hero__subtitle` | design | template (design token) |
| serious | 4.1.2 Name/Role/Value | missing-form-label | axe | `#search-input` | dev | component |
| moderate | 2.4.4 Link Purpose | empty-link | htmlcs | `.footer a.icon` | dev | template |
| minor | 3.1.1 Language of Page | doc-language | axe + htmlcs | `<html>` | web | one-off |

**Corroboration note (Canon 004):** the two contrast rows are the *same* finding seen by two
independent engines (axe + HTML_CS) → corroborated, route first. The label finding is
axe-only → hand-verify before routing. Lighthouse is **not** listed as a third engine because
Lighthouse's a11y category *is* axe — counting it would be a fake corroboration.

## 2. Report (the human summary — `report.md`)

```
# shop.example.com — automated a11y preview — 2026-01-15

- findings: 4 (1 corroborated by 2+ independent engines)
- scope: AUTOMATED COVERAGE ONLY — never a conformance claim (Canon Method 003).
  Lighthouse/axe rows are not independent (Canon Method 004).

By failure class (the six first — Canon 008):
  low-contrast ........ 1   (WebAIM #1 every year; token-level fix)
  missing-form-label .. 1   (transaction-blocking; serial plaintiffs test forms first)
  empty-link .......... 1
  doc-language ........ 1
```

Note what the report **refuses** to say: not "the page is 96% accessible," not "passes," not
"WCAG compliant." It reports *coverage* and *counts*, with the ceiling stated on every run.

## 3. Legal-exposure layer (`legal-exposure.md`)

Exposure indicators to **prioritise** — explicitly *not* legal advice (Canon 002/009).

```
# Legal Exposure — shop.example.com (SYNTHETIC) — 2026-01-15

Exposure indicators for prioritisation — NOT legal advice. Primary-source
verification (EUR-Lex, statutes, court records) required before any external claim.

- The missing form label sits on the search/checkout path — transaction-blocking
  failures are what serial plaintiffs test first.
- Low-contrast is the most-litigated and most-common class, trivially provable by a
  plaintiff's own scanner.
- Applicable regimes for an e-commerce site serving US + EU buyers: ADA Title III
  (US), state statutes, and the European Accessibility Act (EN 301 549 / WCAG 2.1 AA)
  for EU consumers. Cite the statute, verify the primary source, state no conclusion.
```

---

### What to notice

- **Every row is routable without interpretation** — the owning team and fix class are already on it.
- **Severity is graded by user/money impact**, not by the rule's category — a label on the checkout
  search beats a language attribute even though both are "serious" to a scanner.
- **The exposure layer quantifies risk to prioritise, and stops short of a legal conclusion** —
  that line is the difference between a useful audit and an unlicensed legal opinion.
