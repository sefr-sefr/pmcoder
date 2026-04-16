# pmcoder

Claude Code skills collection.

## Skills

### reanimator

Finds Claude Code sessions that were likely running when your computer crashed, froze, or rebooted unexpectedly — and hands back paste-ready `cd … && claude -r '<id>'` commands to resume them.

Scans `~/.claude/projects/` JSONL transcripts, filters out clean exits and trivial sessions, ranks the survivors by crash-day proximity + mid-turn signals, and prints the top candidates with a short analysis paragraph.

Triggers on: "my computer crashed", "which sessions were running", "reanimate my work", etc.

### shape-review

Shape Review quality gate for designs and plans. Invoke **before** presenting any design section, spec, or implementation plan. Dispatches a sub-agent that critically evaluates the shape for over-engineering, duct-taping, refactoring gaps, and CLAUDE.md rule violations. Iterates until the design passes or 6 passes run out.

Triggers on: designing features, writing specs, or writing implementation plans.

### ios-test

Boots an iOS Simulator, connects `idb`, navigates Safari to a URL, and takes an initial screenshot. Auto-discovers `idb` wherever it's installed (PATH, `~/Library/Python/*/bin/idb`, etc.). Useful for mobile-specific testing that Chrome DevTools emulation can't cover.

Takes a URL as argument: `/ios-test https://local.dev`

Requires: Xcode command line tools, `idb` (`pip3 install fb-idb`), `idb-companion` (`brew tap facebook/fb && brew install idb-companion`).

## Install

```
/plugin install https://github.com/sefr-sefr/pmcoder
```

Or add this repo as a marketplace in Claude Code's plugin manager.

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
