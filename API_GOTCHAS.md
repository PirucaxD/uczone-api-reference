# UCZone API Gotchas

The traps. Each of these costs real debugging time because the API looks like
it does one thing and does another. Grouped by failure mode. See
[`API_REFERENCE.md`](API_REFERENCE.md) for the full catalog.

---

## 1. Names that lie

- `Ability.GetDamage(ability)` sounds live, but it's a static read of the
  `npc_abilities.json` `damage` field. No talents, no Aghanim, no facets. It
  returns `0.0` if the ability has no static `damage` KV. For a live,
  level-aware value use `Ability.GetLevelSpecialValueFor(ability, "<key>")`.

- `NPC.GetMoveSpeed(npc)` is a move-speed STAT (~285-330), not a velocity. It's
  non-zero while the unit stands perfectly still. Projecting
  `GetMoveSpeed * facing` to predict a target's position throws a stationary
  target's prediction wildly off. For a true velocity vector read
  `Entity.GetField(npc, "m_vecVelocity")` (undocumented, so pcall-guard it).
  `NPC.IsMoving` and `NPC.IsRunning` are the "actually moving" booleans.

- `Ability.IsReady(ability)` returns `true` for an ability that isn't learned
  yet (level 0). Always gate on `Ability.GetLevel(ability) > 0`.

- `Humanizer.GetOrderQueue()` is the Humanizer's own pending-order queue —
  orders your script issued through the Humanizer — not a feed of the
  player's manual orders. Scanning it for "what is the player attacking"
  misses every manual right-click and every mid-fight target switch. To
  observe the player's intent, watch the `OnPrepareUnitOrders` callback: it
  fires for every order, the player's included (`data.npc` / `data.order` /
  `data.target`). Your own orders carry the `identifier` string you passed
  to `Player.PrepareUnitOrders`, so a prefix check on `data.identifier`
  separates script orders from the player's. Verified 2026-05-18.

- `Ability.GetSpecialValueFor` does not exist. The real function is
  `Ability.GetLevelSpecialValueFor(ability, name, [lvl])`. The trap: one
  of the doc pages contains a literal "WRONG API FIX ME IT MUST BE
  GetSpecialValueFor" note that reads like a bug report on the API name.
  It is not. The LuaCATS library at `Ability.lua` defines the function
  exactly as documented under the longer name; the note is the doc
  author's editorial wish. Use the long name. Verified 2026-05-21.

- `Player.GetName(player)` returns TWO strings: `(nickname, proname|nil)`.
  Naive `local name = Player.GetName(p)` silently drops the proname.
  Bind both: `local nick, pro = Player.GetName(p)`. Verified 2026-05-19.

---

## 2. Inverted or surprising return values

- `Ability.CanBeExecuted(ability)` returns an `Enum.AbilityCastResult`, and
  returns `-1` when the ability CAN be cast (any other value is a block). In
  Lua `-1` is truthy, so `if Ability.CanBeExecuted(a) then ... end` passes for
  every return value. Always compare explicitly: `== -1`.

- `Ability.SecondsSinceLastUse(ability)` returns `-1` when the ability is not
  on cooldown. Not `0`, not a large number.

- `Hero.GetLastVisibleTime(hero)` returns `nil` for a hero that has never been
  fogged. Treat `nil` as "freshly visible", not as a veto.

- `NPC.FindRotationAngle(npc, pos)` returns the angle in RADIANS, not
  degrees. The doc only says "the rotation angle" with no unit. `math.abs`
  of the result caps at pi (~3.14), so a threshold written in degrees can
  never be true: a facing gate like `if angle > 30` or `if angle > 120`
  silently degrades to always-pass. Convert with `math.deg(angle)` before
  comparing to a degree threshold, or express the threshold in radians.
  Verified 2026-05-21 from a bot match: a gate that assumed 30 degrees
  logged angle values of 0..3 and never once crossed the threshold.

---

## 3. Base-only stats that look final

These return the base value; the bonus lives in a separate getter. Using the
base alone silently under-counts.

| Base getter | Add this bonus | Effective value |
|---|---|---|
| `Ability.GetCastRange(a)` | `NPC.GetCastRangeBonus(npc)` | cast range incl. Aether Lens / talents |
| `NPC.GetAttackRange(npc)` | `NPC.GetAttackRangeBonus(npc)` | attack range incl. items / talents |
| `NPC.GetMinDamage(npc)` | `NPC.GetBonusDamage(npc)` | (or just use `GetTrueDamage`) |
| `NPC.GetBaseSpellAmp(npc)` | item amp via `GetModifierProperty(... SPELL_AMPLIFY_PERCENTAGE)` | total spell amp |

The opposite case: these are already FINAL, so don't add a bonus or you
double-count. `GetMoveSpeed`, `GetTrueDamage`, `GetTrueMaximumDamage`,
`GetAttackSpeed`, `GetPhysicalArmorValue`, `GetMagicalArmorValue`, the
`*DamageMultiplier` getters, `Entity.GetHealth`, `GetMaxHealth`, `GetMana`,
`GetMaxMana`, `Hero.GetStrengthTotal / GetAgilityTotal / GetIntellectTotal`.

---

## 4. Engine timing semantics

- Cooldown starts at the END of the cast point, not the start.
  `Ability.GetCooldown` returns `0` during the cast point; the engine sets
  cooldown when the cast completes (projectile release). A cast verification
  that reads cooldown at `issue_time + 0.6s` reports a false "didn't fire" for
  any ability with a meaningful cast point. Schedule the verify at
  `issue_time + Ability.GetCastPoint(ability, true) + slack`.

- Charge abilities: `GetCooldown` only bumps when ALL charges are spent. An
  ability with charges (Shrapnel, Rearm-style) can be fired with `GetCooldown`
  still `0` because charges remain. To verify a charge ability fired, compare
  `Ability.GetCurrentCharges` before and after.

- Status resistance scales CC duration, not whether it lands. Factor
  `MODIFIER_PROPERTY_STATUS_RESISTANCE` into predicted-impact-tick math.

- Same-tick CAST orders REPLACE each other unless `queue=true`. Issuing
  E + R + Q in the same frame with `queue=false` (the default) — each new
  non-queued order replaces the unit's current intent, so one or more
  casts get dropped before completing. The engine's shift-queue mechanic
  is exposed via the `queue` flag on `Player.PrepareUnitOrders`. Pattern
  for a multi-step combo: first step `queue=false` (interrupts the
  baseline orbwalk), subsequent same-tick steps `queue=true`. Verified
  2026-05-22.

---

## 5. Broken or non-existent

Do not call these, they crash or no-op:

- `NPC.GetAttackDamage` does not exist. Use `GetMinDamage`, `GetBonusDamage`,
  `GetTrueDamage`, `GetTrueMaximumDamage`.
- `NPC.GetEvasion` does not exist, and there's no evasion modifier-property
  either.
- `Entity.GetByIndex` does not exist. Use `Entity.Get(idx)`.
- `NPC.GetAttackTarget` for heroes does not exist. Only
  `Tower.GetAttackTarget` does.
- `Modifier.GetModifierAura` always returns `""`. `Modifier.GetSerialNumber`
  and `GetStringIndex` always return `0`.
- The entire aura modifier API is `@deprecated` (`GetAuraSearchTeam`,
  `GetAuraRadius`, `IsAura`, and so on). `GetProvidedByAura` and
  `IsCurrentlyInAuraRange` are the usable survivors.
- `Ability.GetDirtyButtons`, `Item.CastsOnPickup`, `Hero.GetPainFactor`: the
  docs themselves say the behaviour is unknown. Avoid.

Predicate name traps: UCZone's negative predicates are named `Not*`, not
`Is*`. `Target.NotIllusion(e)` exists; `Target.IsIllusion(e)` does not, and
calling it crashes at runtime with `attempt to call a nil value`. Same for
`NotClone`, `NotMeepoClone`, `NotSummon`.

- `NPC.GetAngleDiff(npc, ...)` returns garbage values for non-hero NPCs.
  Heroes only. For creeps / summons / wards / illusions use a manual
  facing calculation from `GetAnglesAsVector` or `FindRotationAngle`
  instead.

- `Ability.GetName(ab)` throws when `ab` is a real entity that is NOT an
  ability. Common shape: resolving a native order-queue entry's
  `abilityIndex` with `Entity.Get` — that index can point at an ITEM
  (ward dispenser, neutral item, consumable), not an ability.
  `Entity.IsEntity` is not enough of a guard. Wrap in `pcall`, or gate on
  an is-ability check. Verified 2026-05-22 in a ranked match: the call
  threw four times and aborted the diagnostic tick each time.

  Re-confirmed live in the upstream UCZone framework in multiple ranked
  matches. The framework's `1_heroes_data_system.lua:9155` walks the
  hero's inventory at various ticks and calls `Ability.GetName` on each
  entry; items throw. See section 9 below for the cross-reference and
  the full crashing-item list.

---

## 6. Documentation quirk: embedded AI-query instructions

GitBook, the platform hosting the upstream UCZone docs, injects an "Agent
Instructions: Querying This Documentation" block into the raw markdown of some
pages (`npc.md`, and summarised on the `widgets` and `math` index pages). It
tells an AI assistant to issue HTTP GET requests to a GitBook `?ask=`
endpoint.

That's a GitBook platform feature, not anything the UCZone authors wrote. It's
still instruction text sitting inside a document, though, and any tool or
assistant should treat document content as data, not as commands to follow. In
a local mirror the block is dead weight anyway (no live endpoint), so strip or
ignore it after re-mirroring the docs.

---

## 7. Nilable returns that crash on access

- `Entity.GetAbsOrigin(e)` is NILABLE. It returns `nil` for a dead,
  mid-respawn, or just-destroyed entity — even one that passed
  `Entity.IsEntity(e)` a line earlier (the handle is valid; the unit just
  has no world position). Any `pos.x` / arithmetic / `:Distance2D(pos)`
  immediately after `GetAbsOrigin` needs an `if pos then` guard. Common
  crash shapes: a target dying mid-tick between an `IsAlive` check and the
  pos read; the local hero mid-respawn; a particle / field-thinker entity
  destroyed between `IsEntity` and `GetAbsOrigin`.

- `OnProjectile` data: `data.target` is nilable. When the projectile has
  no tracked entity target (line projectile, world-position cast),
  `data.target` is `nil` and `data.target_loc: Vector` is the actual
  impact point. Useful non-obvious fields beyond the basics:
  `expireTime`, `maxImpactTime`, `launch_tick`, `moveSpeed`,
  `original_move_speed` — enough for full lead / dodge math without
  polling.

- `OnLinearProjectileCreate` data: `data.velocity` is a `Vector`, not a
  scalar speed. For direction use `velocity:Normalized()`, for speed use
  `velocity:Length()`. The event has no `target` field (it is linear by
  definition — use `origin + velocity * t` for prediction). Other useful
  fields: `acceleration: Vector`, `maxSpeed: number`, `distance: number`.

- `OnParticleCreate` data: both `data.entity` and `data.entityForModifiers`
  are nilable (marked `[?]`). World particles and pre-cast warning
  particles often have no owner. The `entity_id: integer` /
  `entity_for_modifiers_id: integer` companions are non-nil and useful
  for raw integer matching. `particleNameIndex: integer` is the hashed
  particle name for fast comparison; build the lookup key with
  `Utils.ResourceIdFromName`.

## 8. KV data limits, and the APIs that route around them

- `npc_abilities.json` exposes ability names, `AbilityBehavior`,
  `AbilityType`, damage, cooldown, cast range and `AbilityValues` — but
  NOT the names of the `modifier_*` modifiers an ability applies (only
  `SpecialBonusIntrinsic` talent modifiers appear). A threat / debuff
  catalog keyed on modifier names therefore cannot be data-derived;
  `modifier_<ability>` is a convention guess that has to be harvested from
  an in-game "unrecognized modifier" log. Anything keyed on ability names,
  behaviors, or cast-activity slots IS fully KV-derivable — prefer
  ability-keyed designs.

- `NPC.GetChannellingAbility(npc)` returns the `CAbility` the unit is
  currently channelling (nil otherwise) — a modifier-name-free channel
  detector. Use it instead of a hand-maintained channel-modifier list,
  which rots (see above). Fall back to a modifier check only where a
  SPECIFIC modifier matters (e.g. `modifier_teleporting` to single out a
  Teleport among channels).

- Cast-activity slots are derivable, but not by raw index.
  `ACT_DOTA_CAST_ABILITY_N` is the unit's spell-bar slot — Q=1, W=2, E=3,
  R=4 — NOT the index in the hero's KV `Ability1..N` array (which is padded
  with `generic_hidden`, innate, and hidden entries). Derive the slot: walk
  the ability list, skip `generic_hidden` / `Innate=1` / `HIDDEN` or
  `NOT_LEARNABLE` behavior / pure-passive / `ABILITY_TYPE_ATTRIBUTES`; the
  `ABILITY_TYPE_ULTIMATE` ability is AB4, the first three remaining
  castables are AB1/AB2/AB3.

## 9. Upstream framework crashes verified live

These are bugs in the upstream UCZone framework, not in your script.
They are noted here because the `[Lua error]` and `[hero_lib]` tags in
the log can read like your own code crashing when they are not. If
the file path in the error starts with `scripts_data\dota_production`,
it is the framework. Listed here with verification context so you can
match the pattern fast.

- `scripts_data\dota_production\1_heroes_data_system.lua:9155` --
  `bad argument #1 to 'GetName' (arg is not an Ability)`. The
  framework walks the hero's inventory at various ticks and calls
  `Ability.GetName` on each entry. When the entry resolves to an item
  (wards, consumables, recipes, components, shard) the call throws --
  same root cause as the `Ability.GetName` gotcha in section 5. Items
  observed triggering it: `item_ward_sentry`, `item_ward_observer`,
  `item_ward_dispenser`, `item_dust`, `item_clarity`, `item_famango`,
  `item_greater_famango`, `item_splintmail`, `item_recipe_aether_lens`,
  `item_energy_booster`, `item_void_stone`, `item_aghanims_shard`,
  `item_vitality_booster`, `item_tpscroll`, `item_smoke_of_deceit`,
  `item_ring_of_basilius`, `item_boots`. Roughly 20-30 crashes per
  match on a hero that buys often. Re-confirmed 2026-05-25 and again
  2026-05-26.

- `scripts_data\dota_production\2_dodger.lua:5469` --
  `bad argument #1 to 'GetNetOrigin' (arg is not an Entity: <handle>)`.
  The dodger holds an entity reference somewhere that survives the
  underlying entity's destruction (the `<handle>` is a stale memory
  address). Every frame the dodger tries
  `Entity.GetNetOrigin(<stale handle>)` and throws. Observed firing
  roughly 38 times per second of game time across a full match
  (2278 throws in one match). The crash spam is loud but the
  framework keeps running; user-script callbacks still execute
  normally. Verified 2026-05-26.

- `scripts_data\dota_production\2_dodger.lua:4104` --
  `attempt to perform arithmetic on a nil value (field 'time')`.
  Inner stack trace:
  `forward_offset` -> `aoe_is_danger` -> `resolve_target` ->
  `need_to_dodge` -> `try_to_dodge` -> `insert_animation` -> callback.
  The dodger's `forward_offset` reads a `time` field from an AoE
  threat record that is nil for some inputs. Fires only occasionally
  (twice in 141k log lines), so the trigger condition is narrow. The
  callback chain keeps running, but the dodger drops the current
  resolve. Verified 2026-05-26.

## 10. Behaviors that surprise in bot matches

- `NPC.IsAttacking(ally)` is unreliable for ALLIED bots. A heuristic that
  counts allies attacking a given enemy by polling `NPC.IsAttacking` on
  each ally can read `false` for an ally that is visibly attacking, across
  whole matches in some ally-mixes (it reports correctly in others). Treat
  any allied-bot `IsAttacking` heuristic as best-effort; instrument it and
  keep a fallback that does not depend on it.

- The engine silently drops the FIRST cast of a freshly-acquired item. The
  order is well-formed and reaches the engine intact (it appears in
  `ExecuteOrder`), the item handle resolves from an active slot, the ability
  reads ready, the target is valid and in range, mana is fine, the caster is
  not disabled. The cast still does nothing: no cooldown, no effect. The
  SECOND and every later cast of that same item work normally. One cast
  "breaks the item in"; most likely the engine has not resolved the item's
  slot or cast state until it is commanded once. Verified by tracing a
  failed Hurricane Pike cast against a later successful one: the two were
  byte-identical in the log (same order type, ability and target handles,
  flags). A freshly-bought active item cannot be relied on for its first
  use. Work around it by priming the item with one throwaway cast when it
  is safe to, and by re-issuing a missed first cast one frame later so the
  second, landing cast covers the action.

## 11. Allocation and resource traps

- `Entity.GetAbsOrigin(e)` allocates a fresh `Vector` object on every
  call. In a hot loop (per-frame distance checks across N units) the
  garbage adds up. `Entity.GetAbsOriginXYZ(e)` returns the same data as
  three numbers `(x, y, z)` with zero allocation; use it inside tight
  loops and reserve `GetAbsOrigin` for one-shot reads where the Vector
  object is actually used.

- `GridNav.CreateNpcMap()` allocates a map handle that MUST be released
  with `GridNav.ReleaseNpcMap(map)` or it leaks. Pair them in the same
  code block, even on the error path. Verified by reading the doc note
  at `gridnav.md`.

## 12. API design quirks worth knowing

- `Ability.CastTarget` / `Ability.CastNoTarget` / `Ability.CastPosition`
  are NOT a faster or more direct cast pipeline. They are convenience
  wrappers over `Player.PrepareUnitOrders` and end up on the same
  humanizer / native-order list. They take the identical optional
  parameters, just renamed: `push` (the `Ability.Cast*` flag) is
  `callback` (the `PrepareUnitOrders` flag) under a different name with
  the same semantics. Switching a cast off `PrepareUnitOrders` onto
  `Ability.Cast*` buys nothing against a native-order flood;
  `execute_fast=true` (front of the order list) is the only real lever.
  Verified 2026-05-23.

- `Ability.IsCastable(ability, mana)` takes a `mana` parameter — you
  pass the mana budget you have and the function returns whether the
  ability is castable AT that mana. Not `IsCastable(ability)` as the name
  might suggest. Useful for "can I afford a combo at the current mana"
  branches without manually subtracting per ability.

- `Ability.GetLevelSpecialValueFor` returns `0` when called on a TALENT
  handle. Talent magnitudes live in the parent ability's `AbilityValues`
  (or on a sibling KV field), not on the talent's own `AbilityValues`.
  Read the talent value from the parent ability, or hardcode with a
  comment if the parent reference is awkward.

- `Humanizer.GetOrderQueue()` exposes `triggerCallBack` per entry. Your
  own orders, issued via `Player.PrepareUnitOrders(..., callback=true)`,
  carry `triggerCallBack=true` on their queue entry; baseline and
  framework subsystems issue with `callback=false`. A diff snapshot of
  the queue across frames cleanly attributes each new order to "script"
  vs "native or other". Pairs with your own `issued` log to prove the
  order pipeline reaches the queue.

- `CMenuBind:Get(idx)` returns `0` unreliably for keys that are actually
  bound. `:Buttons()` returns the real key codes. A bind widget with `L`
  bound was observed reporting `:Get(1)=0, :Get(2)=0, :Buttons()=22/0`
  (22 is `L`). `:IsDown()` works regardless and is what you want for
  dispatch decisions; only a readout-for-display path needs `:Buttons()`.

- The framework loads EVERY `.lua` file in `%cheat_dir%/scripts/` for
  every match, regardless of which hero the player picks. There is no
  per-hero auto-load (no folder convention like
  `scripts/heroes/<x>/`, no `script.hero` metadata, no `OnHeroPick`
  callback). A hero-specific script MUST self-gate. The canonical
  pattern across observed hero scripts (Windranger, Keeper of the
  Light, MeepoV2, custom Sniper brain) is:
  ```lua
  local me = Heroes.GetLocal()  -- or Player.GetAssignedHero(Players.GetLocal())
  if not me or NPC.GetUnitName(me) ~= "npc_dota_hero_<x>" then return end
  ```
  inside each callback body (or once as an outermost wrap of the
  returned callbacks table if the script chains additional handlers
  via lib `.Wire` patterns — the wrap also gates the chained
  observers cleanly). Without this gate, a script's callbacks AND any
  `.Wire`-chained lib handlers fire on every hero the player picks,
  with no warning. The framework's `starter_script.lua` example does
  not gate either and silently relies on the user adding one.
  Verified 2026-05-26 against a Sniper-specific brain that fired
  Sniper's `item_hurricane_pike` on a Drow match's enemy PA before the
  gate was added; the brain self-acquired as
  `npc_dota_hero_drow_ranger` and ran full save/combo logic on Drow's
  inventory.

## How this list grows

Add an entry when a UCZone API call surprises you: a name that doesn't exist
or is named differently, return semantics inverted vs. the type signature,
doc text that admits the function is broken or unknown, a callback field that
is nil and crashes on access, or the same concept named differently across
sibling functions. Date the entry and say how it was verified.
