# Getting Started with UCZone Scripting

A first-time walkthrough of writing a UCZone (Dota 2) Lua script. Read it
once, copy [`examples/starter_script.lua`](examples/starter_script.lua), and
keep [`API_REFERENCE.md`](API_REFERENCE.md) and [`API_GOTCHAS.md`](API_GOTCHAS.md)
open while you work.

## 1. Where scripts live

Scripts are Lua 5.4 files. Drop a `.lua` file into `%cheat_dir%/scripts/` and
the framework loads it. Editing and saving reloads it.

## 2. The callback model

A script does almost nothing on its own. It returns a table of callback
handlers, and the framework calls a handler when its event fires:

```lua
local script = {}

function script.OnUpdate()      -- runs once per frame
    -- your per-frame logic
end

return script
```

Common callbacks (full list and `data` shapes are in the GitBook
`callbacks.md`):

| Callback | Fires when |
|---|---|
| `OnUpdate` | every frame, the main loop |
| `OnUpdateEx` | every frame, with extra timing data |
| `OnGameEnd` | the match ends |
| `OnModifierCreate` / `OnModifierDestroy` | a buff/debuff lands or expires |
| `OnEntityHurt` / `OnEntityKilled` | damage, or a kill |
| `OnUnitAnimation` | a unit plays an animation (cast tells) |
| `OnPrepareUnitOrders` | an order is about to be issued (you can inspect it) |
| `OnNpcSpawned` / `OnEntityCreate` / `OnEntityDestroy` | entity lifecycle |

## 3. Reading the game state

Inside a callback you query the live game. Your own hero:

```lua
local me = Heroes.GetLocal()      -- nil until a game is running
```

From there the `Entity.*`, `NPC.*`, `Hero.*`, `Ability.*`, `Item.*` and
`Modifier.*` functions read everything: health, mana, abilities, items,
modifiers, positions. The verified catalog is [`API_REFERENCE.md`](API_REFERENCE.md).
It lists what each function returns and, more importantly, which ones lie.

Bulk lookups: `Heroes.GetAll()`, `NPCs.GetAll()`, `Towers.GetAll()`.

## 4. The menu

Player-facing options go in the in-game menu. Don't auto-do something the
player should control without a toggle.

```lua
local tab   = Menu.Create("General", "Main", "My Script")
local group = tab:Create("Main")
local enabled = group:Switch("Enable", false)   -- :Get() reads it
```

Widgets: `Switch`, `Slider`, `ColorPicker`, `ComboBox`, `Button`, `Label`,
`Bind` (key bind). Each returns a handle; read it with `:Get()`.

## 5. Issuing orders

`Ability.CastNoTarget(ab)`, `Ability.CastTarget(ab, target)`,
`Ability.CastPosition(ab, pos)`, `NPC.MoveTo`, `NPC.AttackTarget`, and so on.
Items are abilities, so call the `Ability.*` cast functions on an item handle.

Before casting, check `Ability.IsCastable(ab, mana)`. It checks cooldown, mana,
level and slot together.

## 6. Avoid the traps: read API_GOTCHAS first

The UCZone API has a set of well-known traps that look correct and compile
fine but misbehave at runtime. A non-existent `NPC.GetAttackDamage`,
`Ability.CanBeExecuted` returning `-1` for "OK" (which is truthy in Lua),
`Ability.IsReady` being `true` for unlearned abilities, base-vs-final stats,
`NPC.GetMoveSpeed` being a stat rather than a velocity, and more. They are all
catalogued in [`API_GOTCHAS.md`](API_GOTCHAS.md).

Lint your script before running it:

```
python tools/lint_uczone_script.py path/to/your_script.lua
```

It flags every known trap with a file/line and an explanation, and exits
non-zero on an ERROR or WARN, so it works as a pre-run check.

## 7. Debugging

`print(...)` and `log(...)` write to the console and to
`%cheat_dir%/debug.log`, and they auto-stringify tables. That log is the main
debugging tool: sprinkle prints, play a demo, read the log afterwards.

Avoid heavy work in `OnDraw` (on-screen rendering); it can tank FPS. Prefer
logging, or a menu `Label`, for diagnostics.

## 8. Where to go next

- [`examples/starter_script.lua`](examples/starter_script.lua): copy this skeleton.
- [`COOKBOOK.md`](COOKBOOK.md): worked snippets for common tasks.
- [`API_REFERENCE.md`](API_REFERENCE.md): the verified function catalog.
- [`API_GOTCHAS.md`](API_GOTCHAS.md): the traps, in detail.
- [`ENUMS.md`](ENUMS.md): the enums you'll actually use.
- [`GAME_DATA.md`](GAME_DATA.md): Dota's static data files.
- Official docs: <https://uczone.gitbook.io/api-v2.0>, and the
  [Lua 5.4 manual](https://www.lua.org/manual/5.4/).
- The `ILKA.umbrella-vscode` VS Code extension ships ~10k lines of LuaCATS
  type definitions. Install it for autocomplete and inline type checks.
