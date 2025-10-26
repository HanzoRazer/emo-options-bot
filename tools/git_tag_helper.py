#!/usr/bin/env python
"""
Git Tag Helper — safe, gated version tagging.

Features:
  • Runs a release check first (customizable)
  • Bumps ./VERSION (semver), or use --set to force
  • Creates tag vX.Y.Z[-pre], signs when GPG is available
  • Optional CHANGELOG entry append
  • Optional push to origin (commit + tag)
  • Dry-run mode prints what would happen

Usage examples:
  python tools/git_tag_helper.py                      # default: bump patch, run release check
  python tools/git_tag_helper.py --bump minor -m "Phase 3 RC"
  python tools/git_tag_helper.py --set 3.0.0 --no-push
  python tools/git_tag_helper.py --pre rc.1 --changelog CHANGELOG.md
  python tools/git_tag_helper.py --release-cmd "python tools/release_check.py"
  python tools/git_tag_helper.py --dry-run

Exit codes:
  0  success
  1  general failure (dirty tree, bad args, etc.)
  2  release-check failed (tag NOT created)
"""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"

DEFAULT_RELEASE_CMDS = [
    "make release-check",
    "python tools/release_check.py",
    "python scripts/release_check.py",
]

def run(cmd, check=True, capture=False):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    kwargs = dict(text=True)
    if capture:
        kwargs["capture_output"] = True
    res = subprocess.run(cmd, **kwargs)
    if check and res.returncode != 0:
        raise subprocess.CalledProcessError(res.returncode, cmd, res.stdout if capture else None, res.stderr if capture else None)
    return res

def git(*args, capture=False):
    return run(["git", *args], check=True, capture=capture)

def git_is_clean():
    res = run(["git", "status", "--porcelain"], capture=True)
    return res.stdout.strip() == ""

def detect_signing():
    # If GPG key exists in git config, try signing
    res = run(["git", "config", "--get", "user.signingkey"], capture=True)
    key = res.stdout.strip()
    if not key:
        return False
    # quick check for gpg presence
    try:
        run(["gpg", "--list-secret-keys"], check=True, capture=True)
        return True
    except Exception:
        return False

def read_version():
    if VERSION_FILE.exists():
        txt = VERSION_FILE.read_text().strip()
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\.-]+))?$", txt)
        if m:
            major, minor, patch = [int(x) for x in m.group(1,2,3)]
            pre = m.group(4) or ""
            return [major, minor, patch, pre]
    return [0, 0, 1, ""]

def write_version(ver_tuple):
    major, minor, patch, pre = ver_tuple
    s = f"{major}.{minor}.{patch}"
    if pre:
        s += f"-{pre}"
    VERSION_FILE.write_text(s + "\n")
    return s

def bump(ver, part, pre=""):
    major, minor, patch, _ = ver
    if part == "major":
        return [major + 1, 0, 0, pre]
    elif part == "minor":
        return [major, minor + 1, 0, pre]
    else:
        return [major, minor, patch + 1, pre]

def coerce_version_str(s):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\.-]+))?$", s.strip())
    if not m:
        raise ValueError("Version must be semver like 1.2.3 or 1.2.3-rc.1")
    major, minor, patch = [int(x) for x in m.group(1,2,3)]
    pre = m.group(4) or ""
    return [major, minor, patch, pre]

def try_release_check(custom_cmd=None, dry_run=False):
    cmds = []
    if custom_cmd:
        cmds.append(custom_cmd)
    cmds += DEFAULT_RELEASE_CMDS
    last_err = None
    for c in cmds:
        if dry_run:
            print(f"🧪 [dry-run] Would run release-check: {c}")
            return True
        print(f"🔎 Running release-check: {c}")
        try:
            res = run(c, check=False, capture=True)
            if res.returncode == 0:
                print("✅ Release-check passed")
                return True
            else:
                print(f"⚠️ Release-check `{c}` failed with code {res.returncode}")
                if res.stdout:
                    print(res.stdout.strip())
                if res.stderr:
                    print(res.stderr.strip())
                last_err = res
        except Exception as e:
            print(f"⚠️ Release-check `{c}` errored: {e}")
            last_err = e
    print("❌ All release-check commands failed")
    return False

def maybe_append_changelog(changelog_path, tag, message, dry_run=False):
    if not changelog_path:
        return
    line = f"- {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} {tag}: {message}\n"
    if dry_run:
        print(f"🧪 [dry-run] Would append to {changelog_path}:\n{line.strip()}")
        return
    p = Path(changelog_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if p.exists() else "w"
    with open(p, mode, encoding="utf-8") as f:
        f.write(line)
    print(f"📝 Appended to {changelog_path}")

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Safe Git version tagger with release gate.")
    ap.add_argument("--bump", choices=["major","minor","patch"], default="patch", help="Semver bump (ignored if --set is used)")
    ap.add_argument("--set", help="Force a specific version like 2.0.0 or 2.0.0-rc.1")
    ap.add_argument("--pre", help="Optional pre-release suffix, e.g. rc.1")
    ap.add_argument("--message","-m", default="Phase 3 stable release", help="Tag message")
    ap.add_argument("--release-cmd", help="Custom release check command")
    ap.add_argument("--dirty-ok", action="store_true", help="Allow dirty working tree")
    ap.add_argument("--no-push", action="store_true", help="Don't push commit/tag to origin")
    ap.add_argument("--changelog", help="Append a line to this CHANGELOG file after tagging")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without changing anything")
    args = ap.parse_args()

    # 0) Release gate
    ok = try_release_check(custom_cmd=args.release_cmd, dry_run=args.dry_run)
    if not ok:
        sys.exit(2)

    # 1) Check tree cleanliness
    if not args.dirty_ok and not git_is_clean():
        print("❌ Working tree not clean. Commit your changes or pass --dirty-ok.")
        sys.exit(1)

    # 2) Compute version
    if args.set:
        new_ver = coerce_version_str(args.set)
        if args.pre:
            new_ver[3] = args.pre
    else:
        cur = read_version()
        pre = args.pre or ""
        new_ver = bump(cur, args.bump, pre=pre)
    tag = f"v{new_ver[0]}.{new_ver[1]}.{new_ver[2]}"
    if new_ver[3]:
        tag += f"-{new_ver[3]}"

    # 3) Write VERSION + commit
    if args.dry_run:
        print(f"🧪 [dry-run] Would write VERSION: {new_ver[0]}.{new_ver[1]}.{new_ver[2]}{('-'+new_ver[3]) if new_ver[3] else ''}")
        print(f"🧪 [dry-run] Would commit VERSION bump")
    else:
        ver_str = write_version(new_ver)
        run(["git","add","VERSION"])
        run(["git","commit","-m", f"Bump version to {tag}"])

    # 4) Create tag (sign if possible)
    sign = False if args.dry_run else detect_signing()
    tag_args = ["git","tag"]
    if sign:
        tag_args.append("-s")
    tag_args += [tag, "-m", args.message]

    if args.dry_run:
        print(f"🧪 [dry-run] Would create {'signed ' if sign else ''}tag: {tag} -m \"{args.message}\"")
    else:
        try:
            run(tag_args)
        except Exception:
            # if sign fails unexpectedly, fallback unsigned
            if sign:
                print("⚠️ Signing failed; creating unsigned tag")
                run(["git","tag", tag, "-m", args.message])

    # 5) Changelog append
    maybe_append_changelog(args.changelog, tag, args.message, dry_run=args.dry_run)

    # 6) Push (unless --no-push)
    if args.no_push:
        print(f"✅ Created tag {tag} (not pushed)")
        return

    if args.dry_run:
        print("🧪 [dry-run] Would push commit + tag to origin")
    else:
        run(["git","push","origin","HEAD"])
        run(["git","push","origin", tag])
        print(f"✅ Created and pushed tag {tag}")

if __name__ == "__main__":
    main()