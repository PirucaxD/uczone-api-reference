# UCZone API — Verified Live-Data Reference

The functions a script uses to **read the current game state**: abilities,
items, NPC/unit stats, modifiers, and damage. Every entry was verified against
real script behaviour. Signatures use `name(params) → return`.

Verified around Dota 2 **7.41C** (mid-2026). `CItem` extends `CAbility`, so
every `Ability.*` function also works on an item handle unless noted.

**Conventions**
- "FINAL" = the value already includes item/buff/talent bonuses; do **not**
  add a bonus on top (double-counting risk).
- "BASE" = level value only; you must add the matching bonus getter.
- "pcall-guard" = undocumented but present in real builds; wrap in `pcall`
  because it is build-variable.

---

## 1. Ability data

### Working functions

| Signature | Live value returned |
|---|---|
| `Ability.GetLevelSpecialValueFor(ability, name, [lvl=-1]) → number` | A KV special value at the ability's current level (`lvl=-1` auto-resolves). Live, level-aware. **The correct call for live ability values.** |
| `Ability.GetDamage(ability) → number` | The static `npc_abilities.json` `damage` field. **NOT live** — no talent/Aghanim/facet. `0.0` if absent. |
| `Ability.GetCooldown(ability) → number` | Remaining cooldown seconds. |
| `Ability.GetCooldownLength(ability) → number` | Full cooldown length for the current level. |
| `Ability.SecondsSinceLastUse(ability) → number` | Seconds since last use; **`-1` if not on cooldown.** |
| `Ability.GetCastRange(ability) → number` | Level-specific **BASE** cast range. Add `NPC.GetCastRangeBonus(npc)`. |
| `Ability.GetCastPoint(ability, [include_modifiers=true]) → number` | Cast point (cast delay), modifier-aware by default. |
| `Ability.GetCastPointModifier(ability) → number` | Cast-delay modifier component. |
| `Ability.GetOverrideCastPoint(ability) → number` | Overridden cast point (e.g. Arcane Blink). |
| `Ability.GetManaCost(ability) → number` | Current mana cost. |
| `Ability.GetHealthCost(ability) → number` | Health cost. |
| `Ability.GetLevel(ability) → integer` | Current ability level (`0` = unlearned). |
| `Ability.GetMaxLevel(ability) → integer` | Max level. |
| `Ability.GetCurrentCharges(ability) → integer` | Charges currently available. |
| `Ability.ChargeRestoreTimeRemaining(ability) → integer` | Time until the next charge restores. |
| `Ability.IsReady(ability) → boolean` | `true` if ready — **also `true` for an unlearned ability.** Gate on `GetLevel > 0`. |
| `Ability.IsCastable(ability, [mana=0.0]) → boolean` | `true` if castable at the given mana budget; checks mana/cooldown/level/slot. |
| `Ability.IsOwnersManaEnough(ability) → boolean` | `true` if the owner has enough mana. |
| `Ability.CanBeExecuted(ability) → Enum.AbilityCastResult` | Cast eligibility. **`-1` means OK.** |
| `Ability.IsActivated(ability) → boolean` | `true` if in activated state. |
| `Ability.IsChannelling(ability) → boolean` | `true` if currently channeling. |
| `Ability.IsInAbilityPhase(ability) → boolean` | `true` if in the cast (ability) phase. |
| `Ability.GetChannelStartTime(ability) → number` | Gametime channel starts. |
| `Ability.GetCastStartTime(ability) → number` | Gametime the ability will be cast. |
| `Ability.GetToggleState(ability) → boolean` | `true` if toggled on. |
| `Ability.GetAutoCastState(ability) → boolean` | Autocast on/off. |
| `Ability.GetAltCastState(ability) → boolean` | Alt-cast state (e.g. Doom Devour). |
| `Ability.GetBehavior(ability, [from_static=false]) → Enum.AbilityBehavior` | Behavior bitmask. |
| `Ability.GetDamageType(ability) → Enum.DamageTypes` | Damage type. |
| `Ability.GetImmunityType(ability, [from_static=false]) → Enum.ImmunityTypes` | BKB-pierce class. |
| `Ability.GetDispellableType(ability, [from_static=false]) → Enum.DispellableTypes` | Dispellability of the debuff applied. |
| `Ability.GetTargetTeam / GetTargetType(ability, [from_static=false])` | Target team / type. |
| `Ability.GetTargetFlags(ability) → Enum.TargetFlags` | Target flags. |
| `Ability.IsPassive(ability, [from_static=false]) → boolean` | `true` if passive. |
| `Ability.GetType(ability)` ; `IsBasic / IsUltimate / IsAttributes / IsInnate / IsHidden / IsStolen / IsGrantedByFacet → boolean` | Classification. |
| `Ability.GetName / GetBaseName(ability) → string` | Ability name. |
| `Ability.GetAbilityID(ability) → integer` ; `GetIndex(ability) → integer` | ID / slot index. |
| `Ability.CanBeUpgraded(ability) → boolean` | Upgradeable now. |
| `Ability.GetOwner(ability) → CEntity\|nil` | Ability owner. |
| `Ability.GetKeybind(ability) → string` | Bound key. |

**Undocumented but real** (pcall-guard): `Ability.GetSpecialValue(ability, key)`
(raw KV value, NOT level-aware), `Ability.GetSpecialValueFor(ability, key)`
(works on items too).

### Does not exist / broken / misleading

- **`Ability.GetDamage`** — looks live, is a **static-KV read**. For live values use `GetLevelSpecialValueFor`.
- **`Ability.GetCastRange`** — **BASE only.** Effective = `GetCastRange(a) + NPC.GetCastRangeBonus(npc)`.
- **`Ability.GetCooldown`** — returns **`0` during the cast point** (cooldown is set on cast *completion*). For **charge abilities** it only bumps when *all* charges are spent — track `GetCurrentCharges` instead.
- **`Ability.CanBeExecuted`** — returns `-1` for OK. `-1` is truthy in Lua → `if CanBeExecuted(a) then` always passes. Compare `== -1`.
- **`Ability.GetLevelSpecialValueFor`** — the GitBook page says *"WRONG API FIX ME"*; that is an editorial wish, **the function works**. Returns `0` on a *talent* handle (talent values live in the parent ability's `AbilityValues`).
- **`Ability.IsReady`** — `true` even for an **unlearned** ability. Gate on `GetLevel > 0`.
- **`Ability.GetDirtyButtons`** — the doc itself says "Returns we don't know what." Avoid.

---

## 2. Item data

### Working functions

| Signature | Live value returned |
|---|---|
| `NPC.GetItem(npc, name, [isReal=true]) → CItem\|nil` | Item handle by name. `isReal=true` → slots 1-6 + neutral; `false` → also backpack + stash. |
| `NPC.HasItem(npc, name, [isReal=true]) → boolean` | `true` if the unit holds the item. |
| `NPC.GetItemByIndex(npc, index) → CItem\|nil` | Item handle by inventory index. |
| `NPC.HasInventorySlotFree(npc, [isReal=true]) → boolean` | `true` if a free slot exists. |
| `Item.GetCurrentCharges(item) → integer` | Current charges. |
| `Item.GetSecondaryCharges(item) → integer` | Secondary charges. |
| `Item.GetInitialCharges(item) → integer` | Charges the item ships with. |
| `Item.RequiresCharges(item) → boolean` | `true` if charge-driven. |
| `Item.IsItemEnabled(item) → boolean` | `false` if the item is on its post-stash-move cooldown. |
| `Item.GetEnableTime(item) → number` | Gametime the item becomes enabled. |
| `Item.GetPurchaseTime / GetAssembledTime(item) → number` | Purchase / assembly gametime. |
| `Item.PurchasedWhileDead(item) → boolean` | Bought while dead. |
| `Item.GetCost(item) → integer` | Item cost. |
| `Item.GetStockCount(item_id, [team]) → integer` | Shop stock — by numeric **item ID**, not a handle. |
| `Item.IsStackable / IsRecipe / IsPermanent / IsCombinable / IsDroppable / IsPurchasable / IsSellable / IsKillable / IsDisassemblable(item) → boolean` | Classification flags. |

**Item usability/cooldown** — since `CItem` extends `CAbility`, use the Ability
functions on item handles: `Ability.IsReady(item)`, `IsCastable(item, mana)`,
`GetCooldown(item)`, `GetCurrentCharges(item)`, `GetManaCost(item)`.

### Gotchas

- Item-on-cooldown after a stash move is reported by `IsItemEnabled` / `GetEnableTime`, **not** `GetCooldown`.
- `Item.GetStockCount` takes a numeric item ID (from `items.json`), unlike every other `Item.*`.
- `Item.GetPurchaseTime` on an assembled item returns the lowest-index component's purchase time.
- `Item.CastsOnPickup` / `Item.CanBeUsedOutOfInventory` — doc admits "no idea." Untrusted.

---

## 3. NPC / unit stats

### Working functions

| Signature | Live value returned |
|---|---|
| `Entity.GetHealth(entity) → integer` | Current health (FINAL). |
| `Entity.GetMaxHealth(entity) → integer` | Max health (FINAL). |
| `Entity.IsAlive(entity) → boolean` | Alive. |
| `NPC.GetMana / GetMaxMana(npc) → number` | Mana (FINAL). |
| `NPC.GetManaRegen / GetHealthRegen(npc) → number` | Regen rates. |
| `NPC.CalculateHealthRegen(npc) → number` | Health regen iterating modifiers (FINAL; slow). |
| `NPC.GetCurrentLevel(npc) → number` | Unit level. |
| `NPC.GetMinDamage(npc) → number` | **BASE** min attack damage. |
| `NPC.GetBonusDamage(npc) → number` | Item/buff bonus damage. |
| `NPC.GetTrueDamage(npc) → number` | min + bonus (FINAL min). |
| `NPC.GetTrueMaximumDamage(npc) → number` | max + bonus (FINAL max). |
| `NPC.GetPhysicalArmorValue(npc, [excludeWhite=true]) → number` | Physical armor (FINAL). |
| `NPC.GetArmorDamageMultiplier(npc) → number` | Physical damage multiplier after armor — use this for damage math. |
| `NPC.GetMagicalArmorValue(npc) → number` | Magic resist value (FINAL). |
| `NPC.GetMagicalArmorDamageMultiplier(npc) → number` | Magical damage multiplier (FINAL). |
| `NPC.GetBaseSpellAmp(npc) → number` | **Int-derived spell amp only** — no item amp. |
| `NPC.GetAttackRange(npc) → integer` | **BASE** attack range. Add `GetAttackRangeBonus`. |
| `NPC.GetAttackRangeBonus(npc) → integer` | Bonus attack range (items/talents/buffs). |
| `NPC.GetCastRangeBonus(npc) → integer` | Bonus cast range (Aether Lens, talents). |
| `NPC.GetAttackSpeed(npc) → number` | Attack speed (FINAL). |
| `NPC.GetAttacksPerSecond / GetAttackTime / GetSecondsPerAttack(npc) → number` | Attack-rate forms. |
| `NPC.GetAttackAnimPoint(npc) → number` | Attack animation point (`nil` if not found). |
| `NPC.GetAttackProjectileSpeed(npc) → integer` | Attack projectile speed (`nil` if not found). |
| `NPC.GetMoveSpeed(npc) → number` | Move-speed **STAT** (FINAL) — *not* a velocity. See gotchas. |
| `NPC.GetBaseSpeed(npc) → integer` | Base move speed. |
| `NPC.GetTurnRate(npc) → number` | Turn rate. |
| `NPC.GetDayTimeVisionRange / GetNightTimeVisionRange(npc) → integer` | Vision ranges. |
| `NPC.GetHullRadius / GetPaddedCollisionRadius / GetProjectileCollisionSize(npc) → number` | Collision/hull sizes. |
| `NPC.GetBarriers(npc) → {physical, magic, all = {current, total}}` | Live barrier (shield) HP. |
| `NPC.GetBountyXP / GetGoldBountyMin / GetGoldBountyMax(npc) → integer` | Kill rewards. |
| `NPC.GetModifierProperty(npc, Enum.ModifierFunction) → number` | Aggregated (summed) modifier-property value. |
| `NPC.GetModifierPropertyHighest(npc, property) → number` | Highest single contributor (non-stacking items). |
| `NPC.HasScepter / HasShard(npc) → boolean` | Aghanim's Scepter / Shard. |
| `NPC.IsRanged / IsMoving / IsRunning / IsAttacking / IsTurning / IsVisible / IsIllusion / IsMeepoClone / IsKillable / HasAegis / IsLinkensProtected / IsMirrorProtected / IsChannellingAbility(npc) → boolean` | Live boolean states. |
| `NPC.GetChannellingAbility(npc) → CAbility\|nil` | Ability being channeled. |
| `NPC.GetActivity(npc) → Enum.GameActivity` ; `GetAnimationInfo(npc) → table` | Current animation. |
| `Hero.GetStrengthTotal / GetAgilityTotal / GetIntellectTotal(hero) → number` | Total attributes (FINAL). |
| `Hero.GetCurrentXP(hero) → integer` ; `GetAbilityPoints(hero) → integer` | XP / unspent skill points. |
| `Hero.GetRespawnTime(hero) → number` | Respawn timing. |
| `Hero.GetRecentDamage(hero) → integer` | Damage taken in ~the last 1s. |

**Undocumented but real** (pcall-guard): `NPC.GetArmor`, `NPC.GetMagicalResist`,
`NPC.GetSpellAmplification` (total amp), `NPC.GetDamageMin / GetDamageMax`,
`NPC.GetForwardVector`, `NPC.IsFountain / IsInvulnerable / IsRooted`.

### Does not exist / broken

- **`NPC.GetAttackDamage`** — does NOT exist (crashes). Use `GetMinDamage` / `GetBonusDamage` / `GetTrueDamage` / `GetTrueMaximumDamage`.
- **`NPC.GetEvasion`** — does NOT exist; no evasion modifier-property either. Derive from items/passives.
- **`Entity.GetByIndex`** — does NOT exist. Use `Entity.Get(idx)`.
- **`NPC.GetAttackTarget`** for heroes — does NOT exist; only `Tower.GetAttackTarget(tower)` exists.

### Behavioural gotchas

- **BASE-only, must combine:** `GetAttackRange` (+ `GetAttackRangeBonus`), `GetCastRangeBonus` (added to `Ability.GetCastRange`), `GetBaseSpellAmp` (+ item amp), `GetMinDamage` (use `GetTrueDamage` for the total).
- **`GetMoveSpeed` is a STAT, not a velocity** — ~285-330, non-zero while standing still. For real velocity read `Entity.GetField(npc, "m_vecVelocity")` (pcall-guard); `IsMoving` / `IsRunning` are the "actually moving" booleans.
- **Already FINAL — never add a bonus:** `GetMoveSpeed`, `GetTrueDamage` / `GetTrueMaximumDamage`, `GetAttackSpeed`, `GetPhysicalArmorValue`, `GetMagicalArmorValue`, the `*DamageMultiplier` getters, `Entity.GetHealth` / `GetMaxHealth`, `GetMana` / `GetMaxMana`, `Hero.Get*Total`.
- `Entity.GetAbsOrigin` allocates a Vector each call — use `Entity.GetAbsOriginXYZ` in hot loops.
- `Entity.GetRoshanHealth` works only in unsafe mode.

---

## 4. Modifiers

### Working functions

| Signature | Live value returned |
|---|---|
| `NPC.HasModifier(npc, name) → boolean` | `true` if the unit has the named modifier. |
| `NPC.HasAnyModifier(npc, names) → boolean` | `true` if any of a `string[]` / hash-set (hash-set is faster). |
| `NPC.GetModifier(npc, name) → CModifier\|nil` | Modifier handle by name. |
| `NPC.GetModifiers(npc, [property_filter]) → CModifier[]` | All modifiers, optionally property-filtered. |
| `NPC.GetModifierByIndex(npc, index) → CModifier\|nil` | Modifier at a 1-based index. |
| `NPC.HasState(npc, Enum.ModifierState) → boolean` | `true` if a state is active (stunned / silenced / hexed / magic-immune / ...). |
| `NPC.GetStatesDuration(npc, states[], [only_active=true]) → table` | Remaining seconds per state. |
| `NPC.IsSilenced / IsStunned(npc) → boolean` | Convenience state checks. |
| `Modifier.GetName / GetClass(modifier) → string` | Modifier / class name. |
| `Modifier.GetDuration(modifier) → number` | Total duration. |
| `Modifier.GetDieTime(modifier) → number` | Gametime the modifier expires (remaining = `GetDieTime - GameRules.GetGameTime()`). |
| `Modifier.GetCreationTime / GetLastAppliedTime(modifier) → number` | Creation / last-(re)applied gametime. |
| `Modifier.GetStackCount(modifier) → integer` | Stack count (`0` if unstacked). |
| `Modifier.GetState(modifier) → number, number` | Enabled / disabled state bitmasks. |
| `Modifier.IsDebuff(modifier) → boolean` | `true` if a debuff. |
| `Modifier.GetAbility(modifier) → CAbility\|nil` | Source ability. |
| `Modifier.GetCaster / GetParent / GetAuraOwner(modifier) → CEntity\|nil` | Caster / parent / aura owner. |
| `Modifier.GetProvidedByAura(modifier) → boolean` | `true` if granted by an aura. |
| `Modifier.IsCurrentlyInAuraRange(modifier) → boolean` | In aura range. |

### Broken / deprecated

- **`Modifier.GetModifierAura`** — always returns `""`. **`GetSerialNumber` / `GetStringIndex`** — always `0`.
- The **entire aura modifier API is `@deprecated`** (`GetAuraSearchTeam`, `GetAuraRadius`, `IsAura`, ...). `GetProvidedByAura` and `IsCurrentlyInAuraRange` are the survivors. Query game state directly instead.
- The docs mention `Modifier.GetRemainingTime` but the page does not define it — compute remaining time from `GetDieTime`.

---

## 5. Damage prediction / effective-HP

There is **no single `GetEffectiveHP` / `GetTrueDamageVs` engine call** —
effective-HP must be composed.

### Engine primitives

| Signature | Use |
|---|---|
| `NPC.GetTrueDamage / GetTrueMaximumDamage(npc)` | Final min / max attack damage. |
| `NPC.GetArmorDamageMultiplier(npc)` | Physical damage multiplier after armor. |
| `NPC.GetMagicalArmorDamageMultiplier(npc)` | Magical damage multiplier after resist. |
| `NPC.GetPhysicalDamageReduction(npc)` | Physical reduction value. |
| `NPC.GetBarriers(npc)` | Live shield HP to add before subtracting damage. |
| `NPC.GetModifierProperty(npc, property)` | Incoming/outgoing damage %, flat block (`AVOID_DAMAGE`), spell amp, status resist. |
| `NPC.IsKillable(npc) → boolean` | `false` if currently unkillable (e.g. under Eul). |
| `NPC.HasAegis(npc) → boolean` | Aegis = an effective second life. |

### Recommended damage-calc order

```
raw damage
  × outgoing-damage modifiers   (attacker's GetModifierProperty)
  × incoming-damage modifiers   (target's GetModifierProperty)
  × armor / resist multiplier   (GetArmorDamageMultiplier / GetMagicalArmorDamageMultiplier)
  − flat block                  (MODIFIER_PROPERTY_AVOID_DAMAGE)
```

Effective HP = `Entity.GetHealth` + barriers, then divide by the relevant
multiplier. Status resistance scales CC **duration**, not whether CC lands.

---

## Quick reference — what to query live vs. look up statically

- **Always query live:** ability cooldown / charges / mana / level / readiness;
  item presence + charges + enable-time; unit health / mana / armor / attack
  speed; modifier presence / duration / stacks; states; barriers.
- **Live but compose:** cast range (`GetCastRange + GetCastRangeBonus`), attack
  range (`GetAttackRange + GetAttackRangeBonus`), spell amp, effective-HP.
- **Static look-up** (no live getter, or the getter is static): ability
  damage tables, talent magnitudes, item geometry — read from the KV files
  (see [`GAME_DATA.md`](GAME_DATA.md)).
- **Never call:** `NPC.GetAttackDamage`, `NPC.GetEvasion`, `Entity.GetByIndex`,
  `NPC.GetAttackTarget` (heroes).
