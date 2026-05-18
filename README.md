# UCZone API — Notes & Reference

This is a pile of notes on the UCZone scripting API for Dota 2, cleaned up and
organized so it's actually useful.

The official GitBook docs are okay, but a lot of the API has sharp edges —
functions that don't do what their name says, things that don't exist at all,
values that look final but secretly aren't. Every time one of those came up,
it went into a note. This repo is all of that, written down properly.

To be clear about what this is: it's **reference material and notation, not
scripts**. There's nothing here you drop into the game and run. It's a map of
how the API behaves so you can write your own stuff with fewer surprises and
fewer wasted test runs.

## What's in here

### Start here if you're new

- **[GETTING_STARTED.md](GETTING_STARTED.md)** — the quick walkthrough. Where
  scripts live, how the callback system works, how the menu works, how to
  debug. Read this first.
- **[examples/starter_script.lua](examples/starter_script.lua)** — a tiny,
  fully-commented script skeleton. Copy it, rename it, drop your own logic in.
  It already wires up the menu, the callbacks and the hero handle the right
  way, so you're not guessing at the boilerplate.

### Reference — keep these open while you work

- **[API_REFERENCE.md](API_REFERENCE.md)** — the big one. Every function worth
  knowing for reading the game state — abilities, items, units, modifiers,
  damage — and what each one *actually* returns. Includes a flat-out
  "doesn't exist / broken" list so you don't burn time on dead functions.
- **[API_GOTCHAS.md](API_GOTCHAS.md)** — the traps, in detail. Names that lie,
  return values that are backwards, stats that look final but need a bonus
  added on, weird engine timing. This is the stuff that quietly eats hours.
- **[COOKBOOK.md](COOKBOOK.md)** — copy-paste snippets for the things you do
  constantly: cast an ability safely, check how long a buff has left, predict
  where an enemy is moving, work out whether your damage actually kills.
- **[ENUMS.md](ENUMS.md)** — the enums you'll actually use (`AbilityBehavior`,
  `ModifierState`, `UnitOrder`, `DamageTypes`, and friends) with their values,
  collected in one place instead of scattered across pages.
- **[GAME_DATA.md](GAME_DATA.md)** — how Dota's static data files (heroes,
  abilities, items, units) are laid out. Useful when you want to dig into the
  raw numbers behind the game and how it's all balanced.

### Tools

- **[tools/lint_uczone_script.py](tools/lint_uczone_script.py)** — a small
  linter. Point it at your `.lua` script and it flags the known API traps —
  calling a function that doesn't exist, the backwards-return bug, base stats
  used without their bonus, and so on — before you ever load the thing in
  game. Pure Python 3, nothing to install.

## A note on accuracy

This is all hands-on stuff, checked against how the API and the game actually
behave — verified around the 7.41C patch era. Both the API and the game move
with patches, so treat specific numbers (cooldowns, ranges, costs) as "true
when written" and re-check against the current game data if something looks
off. If you spot something wrong, fixing the note is the whole point.
