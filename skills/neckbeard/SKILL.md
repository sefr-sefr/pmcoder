---
name: neckbeard
description: Use when the user says "neckbeard this", "slap this around", "pros and cons on this", or "is this well-engineered".
---

# Neckbeard

Senior-engineer voice for reviewing Claude's output — plans, designs, diffs, implementations, or last response. PROS-first, then CONS, root-cause framing, concrete fixes. Counterweight to the sycophancy default.

## When to run

The user hands you something and asks for review. Signal words: "neckbeard this", "review this", "slap this around", "pros and cons", "run a neckbeard cto on this", "is this well-engineered".

If the input is too thin (a plan title without body, a commit message without diff), ask 2–3 questions first. Otherwise proceed.

## Output

**PROS, then CONS. Order matters** — the user tested this. PROS first stops the model from sycophancy-gravitating to "everything is great." Reversed order makes it too harsh and misses real strengths.

```
## PROS
- Specific, short. Name the file/function/decision. Don't pad — only list real strengths.

## CONS
- Specific, short, diagnostic. Lead with root-cause framing, not symptom.
  "The coupling is backwards — backend has a frontend-specific field name baked in" > "naming could be clearer"
- After each con, the fix in one line. "Fix: rename `userPayload` to `userRecord` in `handler.ts`, update the two callers."
```

When writing CONS, look hard for these recurring smells:

- **Frontend shape in backend.** Handler with frontend-specific field names, payload shaped for one consumer.
- **Duct tape without refactor.** Patch + comment → comment becomes permanent. Ask: root cause or stacked patch?
- **Flexibility for nothing.** "extensible filter framework" / `metadata` JSONB column when the concrete need is one field. Add explicitly for the field you need, not speculatively.
- **Mock data / stubs / "for now".** Not end-to-end real.
- **"Phase 2" / "known limitation" / TODO.** Future-you never does. Violates global CLAUDE.md.
- **Same pattern duplicated across files.** Copying bad patterns makes them twice as hard to fix.

Not exhaustive — look for anything off.

**Follow-up action — fix, don't hand off.** If the cons add up to "Claude needs to go fix things" and you're in the same session as the work, **just do the fixes** — don't write a "prompt to paste for Claude." The paste-prompt pattern only makes sense for cross-session handoff (e.g., the user wants to start a fresh session to do the fix). Default assumption: same session, do the work.

If you're genuinely in cross-session mode, end with a paste-ready directive prompt. Otherwise skip it.

## Voice

Terse. Specific with filenames. Diagnostic (root cause, not symptom). Don't roleplay "grumpy engineer" — just say the thing. The user's own words are fine: duct tape, vaporware, leftover, god-column.

## Example — same-session default

**The user hands you a 400-line plan in the middle of a session.**

```
## PROS
- Job is idempotent, key is `job_id + batch_ts`. Right call up front.
- Uses existing Cloud Tasks infra instead of a new queue.

## CONS
- Phase 3 is vaporware — multi-tenant routing, regional failover for features not yet scoped. Fix: cut Phase 3, revisit when a real requirement shows up.
- "Retry logic" is abstract. Fix: write "Cloud Tasks built-in retry, max 3, exponential backoff starting at 30s." Otherwise Claude invents something.
- Config table has a `metadata` JSONB column "for future flexibility." God-column graveyard. Fix: remove it. Add real columns when needed.

Going to apply these fixes to the plan now.
```

Then actually make the edits. No paste-prompt needed — you're already here.

## Example — cross-session handoff

**The user shares a plan from a different session and wants a prompt to paste into a fresh session.**

```
## PROS
[same as above]

## CONS
[same as above]

## Prompt to paste into fresh session
Rework the plan at <path>: delete Phase 3 entirely; for retries specify "Cloud Tasks built-in retry, max 3, exponential backoff starting at 30s"; remove the `metadata` JSONB column. Re-share before writing any code.
```

## When NOT to use

- The user is mid-debug and wants a specific bug fixed — don't turn "why is this crashing" into a manifesto.
- Task already tightly scoped. Pass through.
- The user explicitly says "just do it, don't review." Respect it.
- Non-technical tasks (writing, copy, design). Neckbeard opinions there are noise.
- **Brainstorming / early exploration.** Precision demands shut down divergent thinking. Wait until there's a concrete thing to slap around — don't neckbeard a half-formed idea into submission.
