# pmcoder

A small collection of Claude Code skills I've ended up writing for myself. I'm a somewhat tech-savvy product person — not an engineer — and most of this came out of the same frustration: Claude will happily ship code that *works* but isn't the code an engineer would actually write. Duct tape, over-engineering, half-done features, unnecessary abstractions, or the other way — too literal an interpretation of the request that leaves the real structural problems untouched.

These skills are the scaffolding I've accumulated trying to close that gap. They're opinionated and reflect how I personally like to work, but if any of them are useful to you, help yourself.

## Skills

### reanimator

For when your Mac panics, freezes, or reboots and you lose your terminal sessions. It scans your `~/.claude/projects/` transcripts, figures out which Claude Code sessions were most likely alive at the moment everything died, and hands you back paste-ready `cd … && claude -r '<id>'` one-liners for each. Cuts the "which session was that?" detective work down to zero.

**Triggers on:** "my computer crashed", "which sessions were running", "reanimate my work", and similar.

### shape-review

A quality gate I run before presenting any design or implementation plan. Dispatches a sub-agent that critically reviews the shape for over-engineering, duct-taping, missed refactoring, and CLAUDE.md rule violations — then iterates up to six times until the design either passes or you have to step in. Catches a lot of "technically right but structurally wrong" proposals before they hit the editor.

**Triggers on:** designing features, writing specs, writing implementation plans.

### ios-test

Boots an iOS Simulator, connects `idb`, navigates Safari to a URL, and takes a first screenshot — all the boilerplate out of the way so Claude can get straight to actually testing your mobile UI. Auto-discovers `idb` regardless of where it was installed. I use it for the things Chrome DevTools' phone emulation can't cover (virtual keyboard behaviour, safe areas, iOS Safari quirks).

**Triggers on:** `/ios-test <url>`. Requires Xcode command line tools, `idb` (`pip3 install fb-idb`), and `idb-companion` (`brew tap facebook/fb && brew install idb-companion`).

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
