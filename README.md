# pmcoder

Claude Code skills collection.

## Skills

### reanimator

Finds Claude Code sessions that were likely running when your computer crashed, froze, or rebooted unexpectedly — and hands back paste-ready `cd … && claude -r '<id>'` commands to resume them.

Scans your `~/.claude/projects/` JSONL transcripts, filters out clean exits and trivial sessions, ranks the survivors by crash-day proximity + mid-turn signals, and prints the top candidates with a short analysis paragraph.

Triggers on phrases like "my computer crashed", "which sessions were running", "reanimate my work", etc.

## Install

```
/plugin install https://github.com/sefr-sefr/pmcoder
```

Or add this marketplace/repo in Claude Code's plugin manager.

## Layout

```
pmcoder/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        └── scripts/ (optional)
```

## License

MIT
