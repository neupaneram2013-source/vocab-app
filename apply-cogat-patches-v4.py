#!/usr/bin/env python3
"""
apply_patches_v4.py — Removes the client-side teacher access code and
switches to proper server-side authentication (added in the backend's
v4 ProgressController.java).

The frontend no longer stores or checks any password itself — it just
sends whatever the user types to the server, and the server decides
whether it's correct. Nothing secret lives in this file anymore.

REQUIREMENTS BEFORE RUNNING:
  1. You must have already applied apply_patches_v3.py (adds the
     Teacher View feature).
  2. You must deploy the v4 ProgressController.java and the updated
     application.properties to your Render backend, and set the
     TEACHER_ACCESS_CODE environment variable there.

Usage:
    python apply_patches_v4.py [optional-filename.html]

    Defaults to looking for "index.html" in the current folder.

Output: creates a new file with "_v4" inserted before the extension,
e.g. index_v4.html
"""

import sys
from pathlib import Path

DEFAULT_SOURCE = "index.html"

V4_PATCH_1_TEACHER_AUTH = (
    "V4 Patch 1: Server-side teacher authentication",
    """// =============== TEACHER / PARENT VIEW ===============
// NOTE: this access code lives in plain JavaScript and is visible to
// anyone who views the page source. It's a light deterrent for family
// or small-classroom use, not real security. Change it to whatever you
// like below.
const TEACHER_ACCESS_CODE = 'letmein';

async function openTeacherView() {
  const entered = prompt('Enter teacher/parent access code:');
  if (entered === null) return;
  if (entered !== TEACHER_ACCESS_CODE) {
    alert('Incorrect code.');
    return;
  }
  const overlay = document.getElementById('teacherViewOverlay');
  const body = document.getElementById('teacherViewBody');
  if (overlay) overlay.style.display = 'flex';
  if (body) body.innerHTML = '<div style="text-align:center;">Loading student list...</div>';
  try {
    const res = await fetch(API_BASE + '/students');
    if (!res.ok) throw new Error('bad response');
    const students = await res.json();
    renderTeacherTable(students);
  } catch(e) {
    if (body) body.innerHTML = '<div style="text-align:center;color:var(--red);">Could not load student list. Make sure the backend is reachable (it may be waking up from sleep — try again in a minute).</div>';
  }
}""",
    """// =============== TEACHER / PARENT VIEW ===============
// The access code is checked on the SERVER now (see ProgressController's
// /api/students endpoint). Nothing secret lives in this file — the
// browser just forwards whatever the user typed and the server decides.

async function openTeacherView() {
  const entered = prompt('Enter teacher/parent access code:');
  if (entered === null) return;
  const overlay = document.getElementById('teacherViewOverlay');
  const body = document.getElementById('teacherViewBody');
  if (overlay) overlay.style.display = 'flex';
  if (body) body.innerHTML = '<div style="text-align:center;">Loading student list...</div>';
  try {
    const res = await fetch(API_BASE + '/students', {
      headers: { 'X-Teacher-Code': entered }
    });
    if (res.status === 401) {
      if (body) body.innerHTML = '<div style="text-align:center;color:var(--red);">Incorrect access code.</div>';
      return;
    }
    if (!res.ok) throw new Error('bad response');
    const students = await res.json();
    renderTeacherTable(students);
  } catch(e) {
    if (body) body.innerHTML = '<div style="text-align:center;color:var(--red);">Could not load student list. Make sure the backend is reachable (it may be waking up from sleep — try again in a minute).</div>';
  }
}""",
)

ALL_PATCHES = [
    V4_PATCH_1_TEACHER_AUTH,
]


def main():
    source_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    src_path = Path(source_name)

    if not src_path.exists():
        print(f"ERROR: Could not find '{source_name}' in the current folder.")
        print("If your file has a different name, run this script like:")
        print("    python apply_patches_v4.py YOUR_FILE_NAME.html")
        sys.exit(1)

    text = src_path.read_text(encoding="utf-8")
    original_text = text

    print(f"Loaded {source_name} ({len(text):,} characters)\n")

    failures = []
    for name, old, new in ALL_PATCHES:
        count = text.count(old)
        if count == 0:
            failures.append((name, "target text not found — check you're running this on the v3-patched file"))
            continue
        if count > 1:
            failures.append((name, f"target text found {count} times (expected exactly once) — skipping"))
            continue
        text = text.replace(old, new, 1)
        print(f"✓ Applied: {name}")

    if failures:
        print("\n⚠️  Some patches could NOT be applied safely:")
        for name, reason in failures:
            print(f"   - {name}: {reason}")
    else:
        print("\n✅ All v4 patches applied successfully!")

    stem = src_path.stem
    suffix = src_path.suffix
    out_path = src_path.with_name(f"{stem}_v4{suffix}")
    out_path.write_text(text, encoding="utf-8")
    print(f"\nWrote patched file to: {out_path.name}")
    print(f"'{source_name}' was NOT modified.")

    if text == original_text:
        print("\n⚠️  WARNING: Output is identical to input — no patches were applied at all.")


if __name__ == "__main__":
    main()
