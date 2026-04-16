---
name: ios-test
description: Boot iOS Simulator, navigate Safari to a URL, and take an initial screenshot for mobile testing
argument-hint: "<url>"
---

# iOS Simulator Quick Launch

This skill boots an iOS Simulator, navigates to a URL in Safari, connects `idb`, and takes an initial screenshot. It handles all boilerplate so you can jump straight into testing.

**All shell commands in this skill require `dangerouslyDisableSandbox: true`.**

## Locating `idb`

`idb` is typically installed via `pip3 install fb-idb` and ends up on `PATH` — but when installed with `--user` or under a specific Python version, it may not be on PATH. Every bash block in this skill starts by resolving `$IDB` so the skill works regardless of where idb lives:

```bash
IDB=$(command -v idb 2>/dev/null || ls ~/Library/Python/*/bin/idb 2>/dev/null | head -1 || echo "")
[ -z "$IDB" ] && { echo "ERROR: idb not found. Install with: pip3 install fb-idb && brew tap facebook/fb && brew install idb-companion"; exit 1; }
```

Use `"$IDB"` everywhere an idb invocation is needed.

## Step 1: Pre-flight

Run these checks in a single bash call and stop if anything is missing:

```bash
IDB=$(command -v idb 2>/dev/null || ls ~/Library/Python/*/bin/idb 2>/dev/null | head -1 || echo "")
xcrun simctl help >/dev/null 2>&1 && echo "simctl: OK" || echo "simctl: MISSING"
[ -n "$IDB" ] && "$IDB" --help >/dev/null 2>&1 && echo "idb: OK ($IDB)" || echo "idb: MISSING (pip3 install fb-idb)"
which idb_companion >/dev/null 2>&1 && echo "idb_companion: OK" || echo "idb_companion: MISSING (brew tap facebook/fb && brew install idb-companion)"
```

## Step 2: Boot or reuse simulator

```bash
# Check if one is already booted
BOOTED=$(xcrun simctl list devices booted | grep -i iphone | head -1)
if [ -n "$BOOTED" ]; then
    echo "Reusing already-booted device: $BOOTED"
else
    # Find preferred device: iPhone 16 Pro > iPhone 15 Pro > first available iPhone
    UDID=$(xcrun simctl list devices available -j | python3 -c "
import json, sys
data = json.load(sys.stdin)
preferred = ['iPhone 16 Pro', 'iPhone 15 Pro', 'iPhone 16', 'iPhone 15']
found = None
for runtime, devices in data.get('devices', {}).items():
    if 'iOS' not in runtime:
        continue
    for d in devices:
        if d.get('isAvailable') and 'iPhone' in d.get('name', ''):
            for p in preferred:
                if d['name'] == p:
                    if found is None or preferred.index(p) < preferred.index(found[0]):
                        found = (p, d['udid'])
            if found is None:
                found = (d['name'], d['udid'])
if found:
    print(found[1])
else:
    print('NONE')
")
    if [ "$UDID" = "NONE" ]; then
        echo "ERROR: No available iPhone simulators found. Create one in Xcode > Window > Devices and Simulators"
        exit 1
    fi
    echo "Booting $UDID..."
    xcrun simctl boot "$UDID" 2>/dev/null || true  # Ignore "already booted" error
    open -a Simulator
    echo "Waiting for boot to complete..."
    xcrun simctl bootstatus "$UDID" -b 2>/dev/null || sleep 10
fi
```

## Step 3: Connect idb

```bash
IDB=$(command -v idb 2>/dev/null || ls ~/Library/Python/*/bin/idb 2>/dev/null | head -1 || echo "")
# Get the booted device UDID
UDID=$(xcrun simctl list devices booted -j | python3 -c "
import json, sys
data = json.load(sys.stdin)
for runtime, devices in data.get('devices', {}).items():
    for d in devices:
        if d.get('state') == 'Booted' and 'iPhone' in d.get('name', ''):
            print(d['udid'])
            sys.exit(0)
")
echo "Connecting idb to $UDID..."
"$IDB" connect "$UDID"
```

## Step 4: Navigate to URL

The URL comes from `$ARGUMENTS`. If no URL is provided, ask the user for one.

```bash
xcrun simctl openurl booted '$ARGUMENTS'
sleep 2  # Brief settle time — if screenshot shows loading/blank, retry after 2s more
```

## Step 5: Take initial screenshot

```bash
IDB=$(command -v idb 2>/dev/null || ls ~/Library/Python/*/bin/idb 2>/dev/null | head -1 || echo "")
mkdir -p /tmp/claude/ios-test
SCREENSHOT="/tmp/claude/ios-test/initial_$(date +%s).png"
"$IDB" screenshot "$SCREENSHOT"
echo "Screenshot saved: $SCREENSHOT"
```

Get screenshot dimensions using `sips` (fast, no Python startup):
```bash
sips -g pixelWidth -g pixelHeight "$SCREENSHOT" 2>/dev/null | awk '/pixel/{print $2}'
```

Read the screenshot image and report to the user:

1. The device model and iOS version (from `xcrun simctl list devices booted`)
2. The screenshot dimensions and derived scale factor (pixel width / device pt width)
3. What you see on the page (describe the layout, any obvious issues)
4. Suggest what to test next based on what's visible

## Step 6: Get accessibility info (optional but recommended)

```bash
IDB=$(command -v idb 2>/dev/null || ls ~/Library/Python/*/bin/idb 2>/dev/null | head -1 || echo "")
"$IDB" ui describe-all
```

This returns the full accessibility hierarchy with element labels and frame coordinates in device points. Useful for identifying tap targets without pixel estimation.

## What to tell the user

After setup completes, tell the user:
- Which device is running and idb is connected
- The URL that was loaded
- What the initial screenshot shows
- That interactions use **device-point coordinates** (screenshot pixels / 3 for 3x devices) — no calibration needed
- Quick reference: `idb ui tap <x> <y>`, `idb ui swipe <x1> <y1> <x2> <y2>`, `idb ui text "..."`, `idb ui describe-all`

## If something fails

- **simctl not found**: "Xcode command line tools not installed. Run `xcode-select --install`"
- **idb not found**: `pip3 install fb-idb` and `brew tap facebook/fb && brew install idb-companion`
- **No devices**: "No iPhone simulators available. Open Xcode > Window > Devices and Simulators to create one"
- **Boot fails**: Try `xcrun simctl shutdown all` then retry
- **"No Companion Connected"**: Run `idb connect <UDID>` with the device UDID
- **URL doesn't load**: Check the URL is valid and the page is publicly accessible
- **Screenshot fails**: Device may not be fully booted yet — wait a few more seconds and retry
