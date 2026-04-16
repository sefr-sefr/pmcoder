---
name: shape-review
description: Shape Review quality gate for designs and plans. Invoke BEFORE presenting any design section, spec, or implementation plan to the user. Catches over-engineering, duct-taping, wrong shape, and CLAUDE.md violations. Required during brainstorming, before specs, and during planning.
---

# Shape Review

You have formed a design or plan internally. **Do NOT present it to the user yet.** First, run this review.

Each review pass is a **separate sub-agent invocation** — not internal reasoning. This ensures genuine re-evaluation with fresh eyes on each pass.

## Step 1: Prepare the content

1. Determine context: **existing code** or **greenfield**?
2. **Read the relevant existing code** if you haven't already — reviewers cannot assess shape for code they can't see
3. **Read the project CLAUDE.md and global CLAUDE.md** — reviewers need these for the rules check
4. Compose the **design text** (the design/plan to review) — hold it in your context
5. Compose the **context text** containing:
   - Whether this is existing code or greenfield
   - Summary of relevant existing code structure (if applicable)
   - All CLAUDE.md rules that apply (from both project and global)

## Step 2: Dispatch Pass 1

Dispatch a sub-agent (Agent tool, subagent_type: "general-purpose"). **Inline the design and context directly in the prompt** — do NOT write to temp files. Sub-agents start fresh with no parent context and cannot reliably find files.

Build the prompt by concatenating these sections verbatim, with the design and context text substituted inline:

---

**You are a shape reviewer. Your job is to critically evaluate a design or plan for structural problems.**

## Design/Plan to Review

{PASTE THE FULL DESIGN TEXT HERE}

## Context

{PASTE THE FULL CONTEXT TEXT HERE}

## Review Questions

Answer EVERY question below. For each question, write 2-3 sentences of genuine analysis — not just "looks fine." If you cannot find a problem, explain specifically what you checked and why it passes.

### If this is existing code work:
1. **Should we refactor more?** Is the design adding to existing structure when the structure itself should change shape?
2. **Is anything slapped on** where the full shape should have been altered?
3. **Is this over-complicated?** Will unnecessary code be created?
4. **Will this duct-tape around existing problems?** Should more existing code change instead?
5. **Is there crud or over-complicated code** that this design works around rather than fixes — risking a monster?
6. **Is the execution path sound?** The design may be right, but is the plan to get there right?
7. **Does this violate any CLAUDE.md rules?** Check the rules in the context file against every aspect of the design.

### If this is greenfield work:
1. **Is anything slapped on** where the full shape should have been altered?
2. **Is this over-complicated?** Will unnecessary code be created?
3. **Is the shape right**, or are there pieces without a coherent whole?
4. **Does this violate any CLAUDE.md rules?** Check the rules in the context file against every aspect of the design.

## Your output format

Return your findings in this exact format (do NOT write to files — return as your response):

```
# Shape Review — Pass 1

## Findings

### Question 1: [question name]
[your analysis]
**Verdict:** PASS / FAIL

### Question 2: [question name]
[your analysis]
**Verdict:** PASS / FAIL

[...repeat for all questions...]

## Issues requiring revision
- [specific issue and what should change]
- [specific issue and what should change]

## Overall verdict
**PASS** or **FAIL** (fail if ANY question failed)
```

Be genuinely critical. If everything passes on your first look, you are probably not looking hard enough. Check again.

**IMPORTANT: Do NOT read files, explore codebases, or search for context. Everything you need is provided above. Base your review ONLY on the design and context given in this prompt.**

---

## Step 3: Read the results and decide

The sub-agent's return value contains the review findings.

- **If PASS:** Proceed to Step 5
- **If FAIL:** Revise the design/plan based on the issues found. Go to Step 4.

## Step 4: Dispatch subsequent passes

For each subsequent pass (up to max 6 total), dispatch a **new** sub-agent with the same prompt structure as Step 2, modified as follows:

- Change the pass number (Pass 2, Pass 3, etc.)
- Inline the **revised** design text
- Add a section: "## Previous Pass Findings\n{PASTE PREVIOUS FINDINGS HERE}\nThe design has been revised since then. Evaluate the CURRENT design fresh — do not assume previous issues are fixed just because they were identified. Verify each one."

After each pass:
- **If PASS:** Proceed to Step 5
- **If FAIL:** Revise again, dispatch next pass
- **If 6 passes exhausted without PASS:** Present the design to the user with all findings attached and flag that the shape review did not converge — the user needs to weigh in

## Step 5: Compile the summary

Present this summary alongside the design/plan:

```
### Shape Review Results
- **Passes run:** [number]
- **Key revisions made:**
  - [Pass N: what changed and why]
- **Final verdict:** PASS — all questions clean as of Pass [N]
```

## Step 6: What comes next

- **If this is a design/spec:** Present it to the user with the shape review summary
- **If this is an implementation plan:** After presenting, also invoke `/scrutinize-plan` (agent review for implementation-level gaps)

## Reminders

- Each pass MUST be a separate sub-agent invocation — not internal reasoning
- This skill and `/scrutinize-plan` check **different things** — both are required for plans
- Other skill review processes (e.g., writing-plans' plan-document-reviewer) check completeness and correctness, NOT shape — they do not replace this
