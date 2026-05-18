# UCZone API — Gotchas

The traps. Each of these costs real debugging time because the API *looks*
like it does one thing and does another. Grouped by failure mode. See
[`API_REFERENCE.md`](API_REFERENCE.md) for the full verified catalog.

---

## 1. Names that lie

- **`Ability.GetDamage(ability)`** — sounds live; is a **static read** of the
  `npc_abilities.json` `damage` field. No talents, no Aghanim, no facets.
  Returns `0.0` if the ability has no static `damage` KV. For a live,
  level-aware value use `Ability.GetLevelSpecialValueFor(ability, "<key>")`.

- **`NPC.GetMoveSpeed(npc)`** — a move-speed **STAT** (~285-330), **not a
  velocity**. It is non-zero while the unit stands perfectly still. Projecting
  `GetMoveSpeed × facing` to predict a target's position flings a stationary
  target's prediction wildly off. For a true velocity vector read
  `Entity.GetField(npc, "m_vecVelocity")` (undocumented — pcall-guard it).
  `NPC.IsMoving` / `NPC.IsRunning` are the "actually moving" booleans.

- **`Ability.IsReady(ability)`** — returns `true` for an ability that is **not
  yet learned** (level 0). Always gate on `Ability.GetLevel(ability) > 0`.

---

## 2. Inverted / surprising return values

- **`Ability.CanBeExecuted(ability)`** returns an `Enum.AbilityCastResult`, and
  **returns `-1` when the ability CAN be cast** (other values = a block). In
  Lua `-1` is truthy, so `if Ability.CanBeExecuted(a) then ... end` passes for
  *every* return value. Always compare explicitly: `== -1`.

- **`Ability.SecondsSinceLastUse(ability)`** returns **`-1` when the ability is
  not on cooldown** — not `0`, not a large number.

- **`Hero.GetLastVisibleTime(hero)`** returns `nil` for a hero that has never
  been fogged. Treat `nil` as "freshly visible," not as a veto.

---

## 3. Base-only stats that look final

These return the **base** value; the bonus lives in a separate getter. Using
the base alone silently under-counts.

| Base getter | Add this bonus | Effective value |
|---|---|---|
| `Ability.GetCastRange(a)` | `NPC.GetCastRangeBonus(npc)` | cast range incl. Aether Lens / talents |
| `NPC.GetAttackRange(npc)` | `NPC.GetAttackRangeBonus(npc)` | attack range incl. items / talents |
| `NPC.GetMinDamage(npc)` | `NPC.GetBonusDamage(npc)` | (or just use `GetTrueDamage`) |
| `NPC.GetBaseSpellAmp(npc)` | item amp via `GetModifierProperty(... SPELL_AMPLIFY_PERCENTAGE)` | total spell amp |

Conversely, **these are already FINAL — do not add a bonus** (double-count
risk): `GetMoveSpeed`, `GetTrueDamage` / `GetTrueMaximumDamage`,
`GetAttackSpeed`, `GetPhysicalArmorValue`, `GetMagicalArmorValue`, the
`*DamageMultiplier` getters, `Entity.GetHealth` / `GetMaxHealth`, `GetMana` /
`GetMaxMana`, `Hero.GetStrengthTotal` / `GetAgilityTotal` / `GetIntellectTotal`.

---

## 4. Engine timing semantics

- **Cooldown starts at cast-point END, not start.** `Ability.GetCooldown`
  returns `0` *during* the cast point — the engine sets cooldown when the cast
  completes (projectile release). A cast verification that reads cooldown at
  `issue_time + 0.6s` reports a false "didn't fire" for any ability with a
  meaningful cast point. Schedule the verify at
  `issue_time + Ability.GetCastPoint(ability, true) + slack`.

- **Charge abilities: `GetCooldown` only bumps when ALL charges are spent.**
  An ability with charges (Shrapnel, Rearm-style) can be fired with
  `GetCooldown` still `0` because charges remain. To verify a charge ability
  fired, compare `Ability.GetCurrentCharges` before/after.

- **Status resistance scales CC *duration*, not whether it lands.** Factor
  `MODIFIER_PROPERTY_STATUS_RESISTANCE` into predicted-impact-tick math.

---

## 5. Broken or non-existent

**Do not call (crash or no-op):**

- `NPC.GetAttackDamage` — does not exist. Use `GetMinDamage` / `GetBonusDamage`
  / `GetTrueDamage` / `GetTrueMaximumDamage`.
- `NPC.GetEvasion` — does not exist; no evasion modifier-property either.
- `Entity.GetByIndex` — does not exist. Use `Entity.Get(idx)`.
- `NPC.GetAttackTarget` for heroes — does not exist; only `Tower.GetAttackTarget`.
- `Modifier.GetModifierAura` — always `""`. `Modifier.GetSerialNumber` /
  `GetStringIndex` — always `0`.
- The entire aura modifier API is `@deprecated` (`GetAuraSearchTeam`,
  `GetAuraRadius`, `IsAura`, ...). `GetProvidedByAura` /
  `IsCurrentlyInAuraRange` are the usable survivors.
- `Ability.GetDirtyButtons`, `Item.CastsOnPickup`, `Hero.GetPainFactor` — the
  docs themselves say the behaviour is unknown. Avoid.

**Predicate name traps** — UCZone's negative predicates are named `Not*`, not
`Is*`. `Target.NotIllusion(e)` exists; `Target.IsIllusion(e)` does **not** and
crashes at runtime with `attempt to call a nil value`. Same for `NotClone`,
`NotMeepoClone`, `NotSummon`.

---

## 6. Documentation hazard — embedded AI-query instructions

GitBook — the platform hosting the upstream UCZone docs — injects an
**"Agent Instructions: Querying This Documentation"** block into the raw
markdown of some pages (`npc.md`; summarised on the `widgets` / `math` index
pages). It tells an AI assistant to issue HTTP GET requests to a GitBook
`?ask=` endpoint.

This is a benign GitBook **platform feature, not an attack** by the UCZone
authors. But it is still instruction text embedded in a document — and a
script, tool, or assistant should treat document content as data, never as
commands to follow. In a mirrored copy the block is also dead weight (no live
endpoint). Strip or ignore it after re-mirroring the docs.

---

## How this list grows

Add an entry when a UCZone API call surprises you: a name that doesn't exist
or is differently named, return semantics inverted vs. the type signature,
doc text that admits the function is broken/unknown, a callback field that is
nil and crashes on access, or the same concept named differently across
sibling functions. Date the entry and say how it was verified.
