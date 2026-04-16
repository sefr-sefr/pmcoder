#!/usr/bin/env python3
"""Find Claude Code sessions most likely to have been running at crash time.

Scans ~/.claude/projects/*/*.jsonl, filters out clean-exit and trivial sessions,
and ranks the survivors by how likely they were to be alive when activity stopped.
Prints a JSON blob the SKILL.md consumer turns into paste-ready `claude -r` lines.
"""

import argparse
import glob
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path


CAVEAT_RE = re.compile(r'<local-command-caveat>.*?</local-command-caveat>', re.DOTALL)
CMD_RE = re.compile(r'<command-[^>]+>.*?</command-[^>]+>', re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')
RENAME_ARGS_RE = re.compile(r'<command-args>"?([^<]+?)"?</command-args>')


def extract_text(content):
    """Pull plain text out of a message.content value. Returns None for tool-only results."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts, has_tool_result = [], False
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_result':
                    has_tool_result = True
        if has_tool_result and not parts:
            return None
        return ' '.join(parts) if parts else None
    return None


def clean_prompt(txt):
    """Strip caveat wrappers, slash-command tags, and collapse whitespace."""
    if not txt:
        return ''
    txt = CAVEAT_RE.sub('', txt)
    txt = CMD_RE.sub('', txt)
    txt = TAG_RE.sub('', txt)
    return ' '.join(txt.split()).strip()


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
    except Exception:
        return None


def summarize_tail(tail):
    """One-line summary of the last few meaningful events in the transcript."""
    tool_calls, last_assistant, last_user = [], None, None
    for d in tail[-40:]:
        t = d.get('type')
        msg = d.get('message', {})
        if not isinstance(msg, dict):
            continue
        c = msg.get('content')
        if isinstance(c, list):
            for item in c:
                if not isinstance(item, dict):
                    continue
                if item.get('type') == 'tool_use':
                    tool_calls.append(item.get('name', ''))
                elif item.get('type') == 'text' and t == 'assistant':
                    tx = item.get('text', '').strip()
                    if tx:
                        last_assistant = tx
                elif item.get('type') == 'text' and t == 'user':
                    cleaned = clean_prompt(item.get('text', ''))
                    if cleaned and len(cleaned) > 3:
                        last_user = cleaned
        elif isinstance(c, str) and t == 'user':
            cleaned = clean_prompt(c)
            if cleaned and len(cleaned) > 3:
                last_user = cleaned
    parts = []
    if tool_calls[-5:]:
        parts.append('tools: ' + ', '.join(tool_calls[-5:]))
    if last_assistant:
        parts.append(f'asst: "{" ".join(last_assistant.split())[:120]}"')
    elif last_user:
        parts.append(f'user: "{" ".join(last_user.split())[:120]}"')
    return ' | '.join(parts)


def analyze_session(path):
    slug = custom = first_prompt = cwd = None
    first_ts = last_ts = None
    user_count = assistant_count = 0
    tail = []
    last_entry = None
    with open(path, encoding='utf-8', errors='replace') as fp:
        for line in fp:
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = parse_ts(d.get('timestamp'))
            if ts is not None:
                if first_ts is None or ts < first_ts:
                    first_ts = ts
                if last_ts is None or ts > last_ts:
                    last_ts = ts
            if not slug and d.get('slug'):
                slug = d['slug']
            if not cwd and d.get('cwd'):
                cwd = d['cwd']
            if d.get('type') == 'custom-title':
                ct = d.get('customTitle')
                if ct:
                    custom = ct
            if d.get('type') == 'system' and d.get('subtype') == 'local_command':
                c = d.get('content', '') or ''
                if '<command-name>/rename</command-name>' in c:
                    m = RENAME_ARGS_RE.search(c)
                    if m:
                        custom = m.group(1).strip().strip('"')
            t = d.get('type')
            msg = d.get('message', {})
            if t == 'user' and not d.get('isSidechain', False) and isinstance(msg, dict):
                c = msg.get('content')
                is_tool_result = False
                has_text = False
                if isinstance(c, list):
                    for item in c:
                        if isinstance(item, dict):
                            if item.get('type') == 'tool_result':
                                is_tool_result = True
                            if item.get('type') == 'text':
                                has_text = True
                elif isinstance(c, str):
                    has_text = True
                if not is_tool_result and has_text:
                    user_count += 1
                    if first_prompt is None:
                        raw = extract_text(c)
                        cleaned = clean_prompt(raw) if raw else ''
                        if cleaned and len(cleaned) > 5:
                            first_prompt = cleaned
            elif t == 'assistant' and not d.get('isSidechain', False) and isinstance(msg, dict):
                c = msg.get('content')
                has_something = False
                if isinstance(c, list):
                    for item in c:
                        if isinstance(item, dict) and item.get('type') in ('text', 'tool_use'):
                            has_something = True
                            break
                elif isinstance(c, str):
                    has_something = True
                if has_something:
                    assistant_count += 1
            if t not in ('progress', 'attachment', 'file-history-snapshot', 'permission-mode', 'queue-operation'):
                tail.append(d)
                if len(tail) > 80:
                    tail = tail[-60:]
            last_entry = d
    ending_type = last_entry.get('type', '') if last_entry else ''
    ending_subtype = last_entry.get('subtype', '') if last_entry else ''
    ending = f'{ending_type}/{ending_subtype}' if ending_subtype else ending_type
    return {
        'slug': slug,
        'custom_name': custom,
        'first_prompt': first_prompt,
        'first_ts': first_ts,
        'last_ts': last_ts,
        'cwd': cwd,
        'user_msgs': user_count,
        'assistant_msgs': assistant_count,
        'msg_count': user_count + assistant_count,
        'ending': ending,
        'last_activity': summarize_tail(tail),
    }


def current_session_id():
    """Read ~/.claude/sessions/<pid>.json to find the session we're running inside."""
    for path in glob.glob(str(Path.home() / '.claude/sessions/*.json')):
        try:
            with open(path) as fp:
                d = json.load(fp)
            sid = d.get('sessionId')
            if sid:
                return sid
        except Exception:
            continue
    return None


def rank_reason(session, latest_day_start):
    """Human-readable explanation of why this session is a likely candidate."""
    reasons = []
    if session['ending'] == 'assistant':
        reasons.append('ended mid-assistant-response')
    elif session['ending'] == 'user':
        reasons.append('ended on tool-result mid-turn')
    if session['last_ts'] and session['last_ts'] >= latest_day_start:
        reasons.append('active on latest-activity day')
    if session['msg_count'] >= 500:
        reasons.append(f"long-running ({session['msg_count']} msgs)")
    if session['first_ts'] and session['last_ts'] and (session['last_ts'] - session['first_ts']) > 7 * 86400:
        reasons.append('spans >1 week — kept open')
    return '; '.join(reasons) or 'recent activity'


def main():
    ap = argparse.ArgumentParser(description='Find Claude sessions likely running at crash time.')
    ap.add_argument('--days', type=int, default=14, help='mtime window in days (default 14)')
    ap.add_argument('--min-msgs', type=int, default=4, help='drop sessions with fewer user+assistant messages (default 4)')
    ap.add_argument('--top', type=int, default=10, help='number of candidates to return (default 10)')
    args = ap.parse_args()

    cutoff = time.time() - args.days * 86400
    current = current_session_id()
    projects_glob = str(Path.home() / '.claude/projects/*/*.jsonl')

    sessions = []
    for f in glob.glob(projects_glob):
        try:
            if os.path.getmtime(f) < cutoff:
                continue
            sid = Path(f).stem
            if current and sid == current:
                continue
            info = analyze_session(f)
            if info['ending'] == 'system/away_summary':
                continue
            if info['msg_count'] < args.min_msgs:
                continue
            info['session_id'] = sid
            info['mtime'] = os.path.getmtime(f)
            sessions.append(info)
        except Exception:
            continue

    if not sessions:
        print(json.dumps({'candidates': [], 'all_sessions_count': 0, 'latest_activity': None, 'current_session_id': current, 'note': 'No matching sessions found — try --days 30 or check ~/.claude/projects/'}, indent=2))
        return

    latest = max(s['last_ts'] for s in sessions if s['last_ts'])
    latest_day_start = datetime.fromtimestamp(latest).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    prior_day_start = latest_day_start - 86400

    def rank_key(s):
        boost = 0
        if s['ending'] == 'assistant':
            boost = 3600
        elif s['ending'] == 'user':
            boost = 1800
        return -((s['last_ts'] or 0) + boost)

    sessions.sort(key=rank_key)

    day_cands = [s for s in sessions if s['last_ts'] and s['last_ts'] >= latest_day_start]
    prior_cands = [s for s in sessions if s['last_ts'] and prior_day_start <= s['last_ts'] < latest_day_start]
    picks = (day_cands + prior_cands)[:args.top]

    for s in picks:
        s['rank_reason'] = rank_reason(s, latest_day_start)

    print(json.dumps({
        'candidates': picks,
        'all_sessions_count': len(sessions),
        'latest_activity': datetime.fromtimestamp(latest).isoformat(),
        'current_session_id': current,
    }, indent=2, default=str))


if __name__ == '__main__':
    main()
