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

## How this list grows

Add an entry when a UCZone API call surprises you: a name that doesn't exist
or is named differently, return semantics inverted vs. the type signature,
doc text that admits the function is broken or unknown, a callback field that
is nil and crashes on access, or the same concept named differently across
sibling functions. Date the entry and say how it was verified.
