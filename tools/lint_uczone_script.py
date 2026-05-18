#!/usr/bin/env python
"""lint_uczone_script.py - static linter for UCZone (Dota 2) Lua scripts.

Catches the known UCZone API traps before the script ever runs - the bugs
documented in API_GOTCHAS.md. It is a regex linter, not a Lua parser, so it
is heuristic: it strips line comments, but it cannot do data-flow analysis.
Treat WARN/INFO as "look here", not "definitely wrong".

Usage:
    python tools/lint_uczone_script.py path/to/script.lua
    python tools/lint_uczone_script.py path/to/scripts_folder/

Exit codes: 0 = clean (or INFO only), 1 = ERROR or WARN found, 2 = bad usage.
Pure standard library, no dependencies.

Severity:
    ERROR - a non-existent / broken API; this will crash or misbehave.
    WARN  - very likely a bug (e.g. the CanBeExecuted -1 trap).
    INFO  - worth a look; may be correct.
"""

import os
import re
import sys

# Each rule: (id, severity, regex, message, suppress-regex-or-None).
# If `regex` matches a comment-stripped line and the suppress regex (when
# given) does NOT match the same line, the line is reported.
RULES = [
    ("no-getattackdamage", "ERROR",
     re.compile(r"\bNPC\.GetAttackDamage\b"),
     "NPC.GetAttackDamage does not exist (crashes). Use GetTrueDamage / "
     "GetTrueMaximumDamage / GetMinDamage + GetBonusDamage.", None),
    ("no-getevasion", "ERROR",
     re.compile(r"\bNPC\.GetEvasion\b"),
     "NPC.GetEvasion does not exist. Derive evasion from items / passives.",
     None),
    ("no-entity-getbyindex", "ERROR",
     re.compile(r"\bEntity\.GetByIndex\b"),
     "Entity.GetByIndex does not exist. Use Entity.Get(idx).", None),
    ("no-npc-getattacktarget", "ERROR",
     re.compile(r"\bNPC\.GetAttackTarget\b"),
     "NPC.GetAttackTarget does not exist for heroes. Only "
     "Tower.GetAttackTarget(tower) exists.", None),
    ("is-predicate-trap", "ERROR",
     re.compile(r"\bTarget\.Is(Illusion|Clone|MeepoClone|Summon)\b"),
     "UCZone's negative target predicates are named Not* (Target.NotIllusion "
     "/ NotClone / NotMeepoClone / NotSummon). The Is* form is nil and "
     "crashes at runtime.", None),
    ("broken-modifier-method", "ERROR",
     re.compile(r"\bModifier\.(GetModifierAura|GetSerialNumber|GetStringIndex)\b"),
     "This Modifier method is broken - it always returns an empty string / 0. "
     "Query game state directly instead.", None),
    ("canbeexecuted-truthy", "WARN",
     re.compile(r"\bCanBeExecuted\b"),
     "Ability.CanBeExecuted returns -1 when OK to cast; -1 is truthy in Lua, "
     "so `if CanBeExecuted(a) then` always passes. Compare `== -1`.",
     re.compile(r"-\s*1")),
    ("dirty-buttons", "WARN",
     re.compile(r"\bAbility\.GetDirtyButtons\b"),
     "Ability.GetDirtyButtons - the docs admit the return value is unknown. "
     "Do not depend on it.", None),
    ("getabsorigin-hotpath", "INFO",
     re.compile(r"\bEntity\.GetAbsOrigin\b"),
     "Entity.GetAbsOrigin allocates a Vector each call. In hot loops prefer "
     "Entity.GetAbsOriginXYZ (returns x, y, z).", None),
    ("getdamage-static", "INFO",
     re.compile(r"\bAbility\.GetDamage\b"),
     "Ability.GetDamage is a STATIC npc_abilities.json read, not a live "
     "value (no talents / Aghanim / facets). For live values use "
     "Ability.GetLevelSpecialValueFor.", None),
    ("getmovespeed-not-velocity", "INFO",
     re.compile(r"\bNPC\.GetMoveSpeed\b"),
     "NPC.GetMoveSpeed is a move-speed STAT, not a velocity (non-zero while "
     "standing still). For position prediction read "
     "Entity.GetField(npc, \"m_vecVelocity\").", None),
    ("castrange-base-only", "INFO",
     re.compile(r"\bAbility\.GetCastRange\b"),
     "Ability.GetCastRange is BASE only. Effective range = GetCastRange(a) + "
     "NPC.GetCastRangeBonus(npc).", None),
    ("attackrange-base-only", "INFO",
     re.compile(r"\bNPC\.GetAttackRange\b"),
     "NPC.GetAttackRange is BASE only. Effective range = GetAttackRange(npc) "
     "+ NPC.GetAttackRangeBonus(npc).", None),
]


def strip_line_comment(line):
    """Drop a Lua -- line comment. Naive: ignores -- inside string literals,
    which is acceptable for a heuristic linter (false negatives, not
    positives)."""
    idx = line.find("--")
    return line[:idx] if idx != -1 else line


def lint_file(path):
    """Return a list of (lineno, rule_id, severity, message) findings."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.readlines()
    except OSError as exc:
        print("  ! could not read %s: %s" % (path, exc), file=sys.stderr)
        return []

    findings = []
    in_block_comment = False
    uses_isready, uses_getlevel = False, False

    for lineno, raw_line in enumerate(raw, 1):
        line = raw_line
        # crude --[[ ]] block-comment tracking
        if in_block_comment:
            end = line.find("]]")
            if end == -1:
                continue
            line = line[end + 2:]
            in_block_comment = False
        start = line.find("--[[")
        if start != -1:
            after = line.find("]]", start)
            if after == -1:
                in_block_comment = True
                line = line[:start]
            else:
                line = line[:start] + line[after + 2:]
        line = strip_line_comment(line)
        if not line.strip():
            continue

        if "IsReady" in line:
            uses_isready = True
        if "GetLevel" in line:
            uses_getlevel = True

        for rule_id, sev, rx, msg, suppress in RULES:
            if rx.search(line) and not (suppress and suppress.search(line)):
                findings.append((lineno, rule_id, sev, msg))

    # file-level heuristic: IsReady used but GetLevel never -> ungated.
    if uses_isready and not uses_getlevel:
        findings.append((0, "isready-ungated", "INFO",
                         "Script calls IsReady but never GetLevel. "
                         "Ability.IsReady returns true for an UNLEARNED "
                         "ability - gate casts on GetLevel(ability) > 0."))
    findings.sort(key=lambda f: f[0])
    return findings


def collect(path):
    if os.path.isfile(path):
        return [path]
    out = []
    for dirpath, _dirs, files in os.walk(path):
        for name in sorted(files):
            if name.lower().endswith(".lua"):
                out.append(os.path.join(dirpath, name))
    return out


def main(argv):
    if len(argv) != 2:
        print("usage: lint_uczone_script.py <script.lua | folder>",
              file=sys.stderr)
        return 2
    target = argv[1]
    if not os.path.exists(target):
        print("no such path: %s" % target, file=sys.stderr)
        return 2

    files = collect(target)
    if not files:
        print("no .lua files found under %s" % target)
        return 0

    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for path in files:
        findings = lint_file(path)
        if not findings:
            continue
        print(path)
        for lineno, rule_id, sev, msg in findings:
            counts[sev] += 1
            where = ("L%d" % lineno) if lineno else "file"
            print("  %-5s %-7s [%s] %s" % (sev, where, rule_id, msg))
        print("")

    print("-" * 64)
    print("%d file(s) scanned - %d ERROR, %d WARN, %d INFO"
          % (len(files), counts["ERROR"], counts["WARN"], counts["INFO"]))
    if counts["ERROR"] or counts["WARN"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
