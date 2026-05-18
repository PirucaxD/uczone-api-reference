# UCZone API Reference (verified)

A **corrected, hands-on reference** for the UCZone v2.0 Lua scripting API for
Dota 2, plus a structured description of Dota's static game-data files. It
exists to make the API easier to study and to spare the next developer the
demo cycles it takes to discover which functions behave as their names imply.

This is **original analysis**, not a copy of the official docs. Every entry
here was checked against real script behaviour or the engine, and the notes
call out where the official GitBook documentation is wrong, misleading, or
incomplete. Where this reference and the GitBook disagree, this reference
states *why*.

## Contents

**Start here** if you are new:

| File | What it is |
|---|---|
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | First-time walkthrough — scripts folder, the callback model, the menu, debugging, where to go next. |
| [`examples/starter_script.lua`](examples/starter_script.lua) | A minimal, correct, fully-commented script skeleton. Copy it and edit. |

**Reference:**

| File | What it is |
|---|---|
| [`API_REFERENCE.md`](API_REFERENCE.md) | Verified catalog of the **live game-state query API** — abilities, items, NPC/unit stats, modifiers, damage. Each function: signature, what live value it returns, and any gotcha. Includes a "does not exist / broken" list. |
| [`API_GOTCHAS.md`](API_GOTCHAS.md) | The traps — functions whose name lies, inverted return values, base-vs-final stats, engine timing surprises, and a note on GitBook's embedded AI-query instructions. |
| [`COOKBOOK.md`](COOKBOOK.md) | Worked snippets for common tasks — cast safely, read a modifier's remaining time, predict a position, effective-HP / kill math. |
| [`ENUMS.md`](ENUMS.md) | The enums you actually use — `AbilityBehavior`, `ModifierState`, `UnitOrder`, `DamageTypes`, `AbilityCastResult`, … with values. |
| [`GAME_DATA.md`](GAME_DATA.md) | How Dota's static KV data files (`npc_heroes`, `npc_abilities`, `npc_units`, `items`, `neutral_items`) are structured — for studying game interactions and balance design. |

**Tools** (`tools/`, pure Python 3, no dependencies):

| Tool | What it does |
|---|---|
| [`lint_uczone_script.py`](tools/lint_uczone_script.py) | Static linter for UCZone Lua scripts — flags the known API traps from `API_GOTCHAS.md` with a file/line. Exit non-zero on ERROR/WARN; usable as a pre-run check. |

## Scope

This reference focuses on the **live-data query surface** — the functions a
script uses to read the current game state and make decisions. That is the
part where naming traps cost the most debugging time. It is deliberately *not*
a full mirror of every UCZone GitBook page (menu widgets, rendering, callback
signatures, math classes — ~105 pages). For those, consult the official docs:
<https://uczone.gitbook.io/api-v2.0>.

## Note — GitBook's embedded AI-query instructions

GitBook — the platform hosting the upstream UCZone docs — injects an
**"Agent Instructions: Querying This Documentation"** block into the raw
markdown of some pages (here: `npc.md`, and summarised on the `widgets` and
`math` index pages). It tells an AI assistant to issue HTTP GET requests to a
GitBook `?ask=` endpoint to query the docs.

This is a **GitBook platform feature — not something the UCZone authors wrote,
and not an attack.** But it is still instruction text sitting inside a
document, and a script, tool, or assistant should treat document content as
data, not as commands to obey. In a local mirror it is also dead weight —
there is no live endpoint to query — so the right move is simply to strip or
ignore it after re-mirroring the docs.

## Provenance & accuracy

- Derived from the UCZone API v2.0 GitBook plus hands-on use of the API in
  real Lua scripts. Verified around the Dota 2 **7.41C** era (mid-2026).
- The API and the game data both change with patches. Treat per-version
  numbers (cooldowns, ranges, costs) as point-in-time and re-verify against
  the current `assets/data/*.json` after an update.
- Corrections are dated; the verification date is in each note.
