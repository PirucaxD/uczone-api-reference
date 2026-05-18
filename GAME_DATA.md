# Dota 2 Static Game Data (KV files)

Dota ships its entire balance design as plain-text **KV (key-value) data**.
UCZone mirrors it as JSON under `<cheat_dir>/assets/data/`. Reading these
files is the most direct way to study how the game's interactions and balance
are structured — every ability, item, unit and hero is a data row.

This document describes the file layout and the parsing traps. It is patch-
versioned data: numbers here move with balance patches; the *structure* is
stable.

| File | Rows | Describes |
|---|---|---|
| `npc_heroes.json` | ~155 | Heroes — ability slots, talents, facets, base stats |
| `npc_abilities.json` | ~1950 | Abilities — behavior, damage, cooldown, cast point, `AbilityValues` |
| `npc_units.json` | ~340 | Non-hero units — creeps, summons, wards, buildings, Roshan |
| `items.json` | ~540 | Items — cost, behavior, recipe graph, `AbilityValues` |
| `neutral_items.json` | 5 tiers | Which neutral items belong to which tier; craft costs |

---

## Shared structure

`npc_abilities.json` and `items.json` share one root key, `DOTAAbilities`
(items are abilities with an `ItemCost`). `npc_heroes.json` uses `DOTAHeroes`,
`npc_units.json` uses `DOTAUnits`. Every row is keyed by its internal name
(`sniper_assassinate`, `item_black_king_bar`, `npc_dota_hero_sniper`).

All values are **strings**, even numbers (`"AbilityCooldown": "20 15 10"`).

### `AbilityValues` — the per-ability tuning block

The richest field. Each entry is one tunable, and takes one of several shapes:

```jsonc
"damage": "300 400 500"                      // per-level array (space-separated)
"radius": { "value": "400 425 450 475",      // value + metadata wrapper
            "affected_by_aoe_increase": "1" }
"damage": { "value": "150 220 290 360",      // value + talent/facet bonuses
            "special_bonus_unique_pudge_7": "150",
            "special_bonus_facet_pudge_flayers_hook": "=80 =120 =160 =200" }
```

Parsing rules that actually matter:

- A **space-separated numeric string is a per-level array.** `"9 8 7"` →
  levels 1/2/3.
- A **`{ "value": ... }` wrapper** carries the base value plus metadata; read
  `value`, ignore the siblings unless you need them.
- **`special_bonus_*` keys are talent bonuses**; **`special_bonus_facet_*` are
  facet bonuses.** A `=` prefix (`"=80 =120"`) means the facet *overrides* the
  base rather than adding to it.
- Modern abilities often **nest the canonical fields** — `AbilityCooldown`,
  `AbilityCastRange`, `AbilityCastPoint`, `AbilityDamage` — *inside*
  `AbilityValues` instead of at the top level (e.g. Pudge's Meat Hook cast
  range, Lina's Laguna Blade cooldown). Check both places.

### `AbilityBehavior` — the behavior bitmask

A `|`-joined flag string (`DOTA_ABILITY_BEHAVIOR_UNIT_TARGET | ...DON'T...`).
Tells you the ability's category at a glance: `NO_TARGET` / `UNIT_TARGET` /
`POINT` / `TOGGLE` / `PASSIVE` / `CHANNELLED` / `AOE` / `IMMEDIATE`, etc.

---

## Per-file notes

### `npc_heroes.json`
Per hero: `Ability1..Ability6` (kit slots), `Ability10..Ability17` (talents),
`Facets`, base stats (`AttackDamageMin/Max`, `AttackRate`,
`AttackAnimationPoint`, `AttributePrimary`, `StatusHealth`, `StatusMana`,
`ProjectileSpeed`, vision), `Role`, `Complexity`.

> The JSON does **not reliably flag which ability slots are granted only by
> Aghanim's Shard/Scepter.** The `IsGrantedByShard` / `HasScepterUpgrade` flags
> on the *ability* KV are the truth signal — cross-check Liquipedia before
> assuming an ability is in the base kit.

### `npc_abilities.json`
Per ability: `AbilityBehavior`, `AbilityType` (basic / ultimate / attributes /
hidden), damage / cooldown / cast point / cast range / mana, `AbilityValues`,
`AbilityUnitDamageType`, `SpellImmunityType` (BKB pierce?),
`SpellDispellableType`, `HasScepterUpgrade` / `HasShardUpgrade`.

> **The KV data exposes ability *names* but NOT `modifier_*` names.** A buff or
> debuff that an ability applies has a runtime modifier name (e.g.
> `modifier_sniper_take_aim_active`) that is **not** in any KV file — only the
> `special_bonus_*` talent modifiers appear. Code that keys on modifier names
> must discover them at runtime (`OnModifierCreate`), not from the KV.

### `items.json`
Per item: `ItemCost`, `AbilityBehavior`, `AbilityCooldown`, `AbilityCastRange`,
`ItemQuality`, `ItemShopTags`, `AbilityValues`.

The **recipe graph** lives on the recipe rows: an `item_recipe_*` entry has
`ItemRecipe = "1"`, an `ItemResult` (the item it builds into) and
`ItemRequirements` — a map like `{ "01": "item_a;item_b" }` (`;`-separated
components; multiple numbered keys = alternative builds). A `*` suffix on a
component name marks the item the recipe upgrades *from*.

### `neutral_items.json`
Only the **tier assignment** — `neutral_tiers.1..5` each list their member
items, a `start_time` and a `craft_cost`. The neutral items' actual stats live
in `items.json` like any other item.

### `npc_units.json`
Per unit: health / armor / attack / move-speed / vision / bounty, `Ability1..N`
slots, and the flags `IsSummoned`, `IsAncient`, `IsNeutralUnitType`,
`ConsideredHero`, `IsRoshan`.

> Summon-vs-illusion: an **illusion is a hero copy** and is not in this file. A
> true **summon** (Furion treant, Warlock golem, necronomicon unit) carries
> `IsSummoned = "1"`. A hero-grade pet such as the Lone Druid Spirit Bear is
> flagged `ConsideredHero`, **not** `IsSummoned`.

---

## Studying game design with this data

Because the whole balance sheet is data, you can answer design questions
directly: damage-per-level curves, cooldown-vs-impact trade-offs, gold
efficiency of a build path (walk the recipe graph), which heroes share a
threat category (enumerate `AbilityBehavior` + `AbilityUnitDamageType`).

A practical pattern: write a small generator that parses each JSON once and
emits a static, pre-resolved Lua table (numbers coerced, level-arrays as Lua
arrays, `{value=...}` wrappers flattened). The script then does cheap table
lookups at runtime instead of re-parsing JSON. Keep the generator as the
single source of truth and re-run it after each patch — never hand-edit the
generated table.

> The static KV value is the *starting point*, not ground truth for runtime
> behaviour. Patches, framework quirks and undocumented interactions can
> diverge from it — when a live observation contradicts the KV, trust the
> observation and re-verify the data.
