#!/usr/bin/env python3
"""
apply_patches_v3.py — Adds a Teacher/Parent View to the vocabulary tool.

This adds:
  - A "Teacher / Parent View" link on the name-entry screen
  - A simple access-code prompt (soft gate — see security note below)
  - A dashboard table showing every student's mastery per level,
    overall percentage, current streak, and last-active time

IMPORTANT SECURITY NOTE:
  The access code is a client-side JavaScript constant. Anyone who views
  the page source can find it. This is a light deterrent for family/
  classroom use, NOT real security. Don't rely on it to protect anything
  truly sensitive.

REQUIREMENTS BEFORE RUNNING:
  1. You must have already applied apply_patches.py (name entry + sync)
     and ideally apply_patches_v2.py (full activity sync).
  2. You must deploy the updated ProgressController.java (v3, adds
     /api/students) to your Render backend first.

Usage:
    python apply_patches_v3.py [optional-filename.html]

    If no filename is given, it looks for "index.html" in the current
    folder (since that's what you deployed to GitHub Pages). If your
    file has a different name, pass it as an argument, e.g.:
        python apply_patches_v3.py CogAT_Vocabulary_Study_Tool_updated_v2.html

Output: creates a new file with "_v3" inserted before the extension,
e.g. index_v3.html
"""

import sys
from pathlib import Path

DEFAULT_SOURCE = "index.html"

# =====================================================================
# PATCH 1: Add the Teacher View link + overlay markup in the HTML
# =====================================================================

V3_PATCH_1_HTML = (
    "V3 Patch 1: Teacher View link + overlay markup",
    """    <div id="nameEntryStatus" style="margin-top:10px;font-size:13px;color:#6b7ba0;"></div>
  </div>
</div>

<div class="layout" id="mainLayout" style="display:none;">""",
    """    <div id="nameEntryStatus" style="margin-top:10px;font-size:13px;color:#6b7ba0;"></div>
    <div style="margin-top:16px;font-size:13px;">
      <a href="#" onclick="openTeacherView();return false;" style="color:var(--teal-dark);text-decoration:underline;">👩‍🏫 Teacher / Parent View</a>
    </div>
  </div>
</div>

<div class="celebration-overlay" id="teacherViewOverlay" style="display:none;z-index:10001;">
  <div class="celebration" style="max-width:900px;text-align:left;">
    <h1 style="font-size:22px;text-align:center;">👩‍🏫 Teacher / Parent View</h1>
    <div id="teacherViewBody" style="margin-top:16px;font-size:14px;">
      <div style="text-align:center;">Loading student list...</div>
    </div>
    <div style="text-align:center;margin-top:16px;">
      <button class="close-btn" onclick="closeTeacherView()">Close</button>
    </div>
  </div>
</div>

<div class="layout" id="mainLayout" style="display:none;">""",
)

# =====================================================================
# PATCH 2: Add the Teacher View JavaScript functions
# =====================================================================

V3_PATCH_2_SCRIPT = (
    "V3 Patch 2: Teacher View JavaScript functions",
    """function switchProfile() {
  try { localStorage.removeItem('cogat_last_name'); } catch(e) {}
  location.reload();
}

// =============== VOCABULARY DATA ===============""",
    """function switchProfile() {
  try { localStorage.removeItem('cogat_last_name'); } catch(e) {}
  location.reload();
}

// =============== TEACHER / PARENT VIEW ===============
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
}

function closeTeacherView() {
  const overlay = document.getElementById('teacherViewOverlay');
  if (overlay) overlay.style.display = 'none';
}

function computeStreakFromActivityLog(activityLog) {
  if (!activityLog || Object.keys(activityLog).length === 0) return 0;
  let streak = 0;
  const today = new Date();
  for (let i = 0; i < 365; i++) {
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
    const k = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    if (activityLog[k]) { streak++; }
    else if (i === 0) { continue; }
    else { break; }
  }
  return streak;
}

function renderTeacherTable(students) {
  const body = document.getElementById('teacherViewBody');
  if (!body) return;
  if (!students || students.length === 0) {
    body.innerHTML = '<div style="text-align:center;">No students found yet. Once someone types their name and starts practicing, they will appear here.</div>';
    return;
  }
  const levels = ['A','B','C','D','E','F','G'];
  let html = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">';
  html += '<thead><tr style="background:var(--cream);text-align:left;">' +
    '<th style="padding:8px;">Student</th>' +
    levels.map(L => '<th style="padding:8px;text-align:center;">' + L + '</th>').join('') +
    '<th style="padding:8px;text-align:center;">Overall</th>' +
    '<th style="padding:8px;text-align:center;">Streak</th>' +
    '<th style="padding:8px;">Last Active</th>' +
    '</tr></thead><tbody>';

  students.forEach(s => {
    const mastered = new Set((s.masteredWords || []));
    let totalMastered = 0, totalWords = 0;
    const perLevel = {};
    levels.forEach(L => {
      const words = (typeof WORDS !== 'undefined') ? WORDS.filter(w => w.level === L) : [];
      const count = words.filter(w => mastered.has('w:' + w.word)).length;
      perLevel[L] = { count: count, total: words.length };
      totalMastered += count;
      totalWords += words.length;
    });
    const overallPct = totalWords > 0 ? Math.round(totalMastered / totalWords * 100) : 0;
    const extra = s.extraData || {};
    const streak = computeStreakFromActivityLog(extra.activityLog);
    const lastActive = s.lastUpdated ? new Date(s.lastUpdated).toLocaleString() : '—';
    const rawName = s.studentName || '—';
    const displayName = rawName.charAt(0).toUpperCase() + rawName.slice(1);

    html += '<tr style="border-bottom:1px solid var(--rule);">' +
      '<td style="padding:8px;font-weight:600;">' + displayName + '</td>' +
      levels.map(function(L) {
        const pl = perLevel[L];
        const full = pl.total > 0 && pl.count === pl.total;
        return '<td style="padding:8px;text-align:center;">' + (full ? '⭐' : (pl.count + '/' + pl.total)) + '</td>';
      }).join('') +
      '<td style="padding:8px;text-align:center;font-weight:600;">' + overallPct + '%</td>' +
      '<td style="padding:8px;text-align:center;">' + (streak > 0 ? ('🔥 ' + streak) : '—') + '</td>' +
      '<td style="padding:8px;font-size:12px;color:#6b7ba0;">' + lastActive + '</td>' +
      '</tr>';
  });

  html += '</tbody></table></div>';
  html += '<div style="margin-top:14px;font-size:12px;opacity:0.7;text-align:center;">Showing ' + students.length + ' student' + (students.length === 1 ? '' : 's') + '.</div>';
  body.innerHTML = html;
}

// =============== VOCABULARY DATA ===============""",
)

ALL_PATCHES = [
    V3_PATCH_1_HTML,
    V3_PATCH_2_SCRIPT,
]


def main():
    source_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    src_path = Path(source_name)

    if not src_path.exists():
        print(f"ERROR: Could not find '{source_name}' in the current folder.")
        print("If your file has a different name, run this script like:")
        print("    python apply_patches_v3.py YOUR_FILE_NAME.html")
        sys.exit(1)

    text = src_path.read_text(encoding="utf-8")
    original_text = text

    print(f"Loaded {source_name} ({len(text):,} characters)\n")

    failures = []
    for name, old, new in ALL_PATCHES:
        count = text.count(old)
        if count == 0:
            failures.append((name, "target text not found — check you're running this on the right version of the file"))
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
        print("\n✅ All v3 patches applied successfully!")

    stem = src_path.stem
    suffix = src_path.suffix
    out_path = src_path.with_name(f"{stem}_v3{suffix}")
    out_path.write_text(text, encoding="utf-8")
    print(f"\nWrote patched file to: {out_path.name}")
    print(f"'{source_name}' was NOT modified.")

    if text == original_text:
        print("\n⚠️  WARNING: Output is identical to input — no patches were applied at all.")


if __name__ == "__main__":
    main()
