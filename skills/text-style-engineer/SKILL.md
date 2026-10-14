---
name: text-style-engineer
description: "Use when writing or editing any text for a technical audience — docs, PRs, commit messages, code comments, chat replies. Triggers on prose that needs cutting, simplifying, or tightening for non-native English readers. Works well for cloud-native, infrastructure, backend, and systems engineering contexts."
---

# Style: Engineer

Audience: fluent non-native English, strong technical background (e.g., Kubernetes, cloud-native, backend systems, infrastructure).

## Core Rules

**Cut to ~50% of first draft.** Write it, then halve it. Drop redundancy, hedging, restatement.

**Simple English.** Short sentences, one idea each. Plain words over showy ones (`use` not `leverage`, `so` not `hence`). Short. No filler.

**Exact technical terms stay.** Simplify prose around them, never the domain vocabulary. Terms like `reconcile`, `external-name`, `MR`, `tfstate`, `no-fork`, `middleware`, `handler`, `resolver` are correct — keep them.

**Active voice, imperative mood.** "Run the command." Not "The command should be run."

**Precise state.** "Merged to main." "Released in v2.0.0." "Available." "Not yet released." Never vague.

**Concrete over abstract.** Name the exact type/file/function/CRD/field.

**No marketing tone.** If uncertain, say "unverified" or "assumption:".

## Banned Words

Never use these (including inflected forms):

`bespoke`, `ships`, `lands`, `seed`, `plant`, `skim`, `residual`, `diligence`, `exfiltration`

Also apply the `avoid-ai-tells` vocabulary swap list — `use` not `leverage`, `help` not `facilitate`, etc.

## Sentence Rules

- Split long clause-chains into separate sentences.
- One idea per sentence.
- Vary length: short sentences (3–8 words) at least 1 in 5.

## Markdown/MDX Prose

No forced line breaks in prose. One paragraph = one line; let it soft-wrap. Hard-wrapping to a column does nothing on render and makes diffs reflow.

**Exception:** code blocks, YAML, tables, and list structure keep their real line breaks.

## Self-Check Before Delivering

- [ ] Cut to ~50% of first draft?
- [ ] No banned words?
- [ ] No `avoid-ai-tells` vocabulary?
- [ ] Each sentence: one idea?
- [ ] Precise state (not "coming soon", "available soon")?
- [ ] Exact names, not "the resource" or "the object"?
- [ ] No forced line breaks in prose?
- [ ] Active voice throughout?

## Related Skills

- `avoid-ai-tells` — vocabulary swap list and structural pattern removal
