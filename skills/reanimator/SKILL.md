---
name: reanimator
description: Use when the user's computer crashed, froze, rebooted unexpectedly, or they otherwise lost their Claude Code sessions and need to find which ones were running so they can resume them. Also trigger on phrases like "which sessions were running", "my computer died/crashed", "rebooted earlier", "what was I working on before", "help me find my sessions", "reanimate my work", or any variant of "my Claude sessions got killed". Scans the JSONL transcripts under ~/.claude/projects/ and produces a ranked list of likely-active sessions with paste-ready `cd … && claude -r '<id>'` commands plus a short analysis paragraph.
---

# Reanimator

When the user's computer crashes, reboots unexpectedly, or they otherwise lose open Claude Code sessions, this skill finds the sessions most likely to have been active at the moment of failure and hands back paste-ready commands to resume them.

## When to run

Fire on any of: "my computer crashed", "I just rebooted", "which sessions were running", "I lost my Claude windows", "reanimate my sessions", "what was I working on before", "help me pick up where I left off after the crash", and similar. The user wants a list, not a long explanation.

## What you produce

A list of 8–12 lines like this:

```
cd /Users/peterblom/_CODE_/Yesper/mcps && claude -r '2e23b2ab-3648-49e0-b633-b42d246efc54'  # <-- mcp-trafikverket: staging 4 files for commit (ended mid-response)
```

The `#` makes the description a shell comment — the user can double-click the whole row to select it and paste without the description breaking the command. Use **two spaces** before the `#` for readability. Do not quote the description (no surrounding single or double quotes) since the terminal will happily ignore anything after `#`, and unquoted text keeps the line cleaner.

Followed by a 2–4 sentence paragraph explaining the pattern you see (e.g. "you had a parallel NRC pipeline cluster open"), calling out the single strongest "died mid-turn" signal, and noting anything that looks like an always-open workspace vs a transient chat.

Do **not** write a separate report file. Print the list and paragraph into the conversation.

## How it works

Claude Code stores each session's full event log at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. One JSONL line per event: user messages, assistant messages, tool calls, tool results, system events, file-history snapshots. The file is append-only, so file `mtime` equals the time of the last event. Clean-closed sessions end with a `system/away_summary` entry — that's the only reliable "exit" marker. Everything else (turn_duration, stop_hook_summary, mid-assistant, mid-tool-result) means the process was still alive when the transcript stopped growing.

Key facts about the data (do not re-derive these):

- **There is no descriptive auto-title.** Each session has a `slug` field (3-word id like `fluffy-sauteeing-kay`) — non-descriptive. The `claude --resume` picker displays the first user prompt, not a summary.
- Custom titles come from two sources, both captured by the script: `/rename` commands (stored as `system/local_command` with `<command-args>"name"</command-args>`) and `custom-title` entries (stored as `{"type":"custom-title","customTitle":"..."}`).
- `type:"user"` entries include both real user prompts AND tool results. Real prompts are the ones whose content has a `text` block and no `tool_result` block. The script already handles this.
- User prompts in resumed sessions start with `<local-command-caveat>...</local-command-caveat>` wrappers; slash commands are stored as `<command-name>...</command-name>` etc. The script strips all of these before extracting the first real prompt.
- The current session's id is in `~/.claude/sessions/<pid>.json` — the script excludes it automatically.

## Workflow

Run the script:

```bash
python3 <skill-path>/scripts/reanimate.py
```

Optional flags: `--days N` (mtime window, default 14), `--min-msgs N` (drop trivial sessions, default 4), `--top N` (default 10).

The script prints JSON to stdout: `{candidates: [...], all_sessions_count, latest_activity, current_session_id}`. Each candidate has `session_id`, `cwd`, `custom_name`, `slug`, `first_prompt`, `last_activity`, `first_ts`, `last_ts`, `msg_count`, `ending`, `rank_reason`.

Then format the output for the user:

1. For each candidate, emit one line in this exact format:

   ```
   cd <cwd> && claude -r '<session_id>'  # <-- <label>
   ```

   Note: two spaces before `#`, no quotes around `<label>`. This way the user can double-click the row to select it all and paste cleanly — the shell treats everything after `#` as a comment.

2. `<label>` is:
   - The `custom_name` if set, shown verbatim (don't prettify, don't quote).
   - Otherwise a terse human-readable description synthesized from `first_prompt` + `last_activity`. Aim for `<topic>: <what was happening>` in under 70 chars. Examples: `bessy frontend: finished plan, committed through review gates`, `larsa: d3-phase2 intent-protocol plan just saved`. Use your judgment — the slug is not useful here; pick something the user will recognize.
3. After the lines, write a short paragraph covering:
   - What cluster/pattern of work the candidates represent (look for shared project roots, naming themes).
   - Which single session is the strongest died-mid-turn signal (ending = `assistant` or `user`, with recent `last_ts`).
   - Anything else worth flagging (unusually long-running workspaces, orphans, etc.).

## Why the defaults are what they are

- **14 days**: Lost sessions are usually within a working fortnight. Anything older is almost certainly closed.
- **≥4 messages**: Filters out one-liner sessions like `"See ya!"` / `"Goodbye!"` which appear to come from a hook or wind-down pattern and are never the ones the user wants resumed.
- **Exclude `system/away_summary`**: Clean exit — definitely not running at crash time.
- **Exclude current session**: It can't have been crashed; it's the one doing the asking.
- **Rank by crash-day clustering + mid-turn boost**: The sessions most likely to have been open when things died are those whose last event is closest in time to the latest non-current activity, with extra weight for "assistant" or "user tool-result" endings (those mean the process was in the middle of a turn when it went away).

## If the script returns zero candidates

That means either:
- The user's `~/.claude/projects/` is empty or uses a non-standard path (unlikely).
- Everything in the last 14 days exited cleanly (everything ends in `away_summary`) — tell the user nothing looked crashed.
- The user lost sessions further back. Re-run with `--days 30` or `--days 60`.
