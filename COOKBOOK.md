# UCZone Scripting Cookbook

Worked snippets for the tasks every script needs. They use only verified API
(see [`API_REFERENCE.md`](API_REFERENCE.md)) and avoid the traps in
[`API_GOTCHAS.md`](API_GOTCHAS.md). Assume `local me = Heroes.GetLocal()`
inside a callback, with `me` confirmed non-nil.

---

## Your hero and nearby enemies

```lua
local me = Heroes.GetLocal()                 -- nil until the game starts
if not me or not Entity.IsAlive(me) then return end

-- Heroes.InRadius(pos, radius, teamNum, teamType, [omitIllusions], [omitDormant])
local enemies = Heroes.InRadius(
    Entity.GetAbsOrigin(me),
    1200,
    Entity.GetTeamNum(me),                   -- relative to MY team
    Enum.TeamType.TEAM_ENEMY,                -- ... give me the enemies
    true                                     -- omit illusions
)
for _, enemy in ipairs(enemies) do
    -- enemy is a CHero handle
end
```

---

## Cast an ability safely

The full guard: the ability exists, is learned, and is castable now.
`IsReady` alone is not enough, since it's `true` for unlearned abilities.

```lua
local ab = NPC.GetAbility(me, "sniper_assassinate")
if ab
   and Ability.GetLevel(ab) > 0                       -- learned?
   and Ability.IsCastable(ab, NPC.GetMana(me))        -- cooldown + mana + slot
then
    Ability.CastTarget(ab, target)        -- unit-target ability
    -- Ability.CastNoTarget(ab)           -- no-target ability
    -- Ability.CastPosition(ab, pos)      -- point-target ability
end
```

Items are abilities, so the same works on an `NPC.GetItem(me, "item_x")`
handle.

---

## Read a modifier's remaining time

There is no `GetRemainingTime`, so compute it from the die time.

```lua
local mod = NPC.GetModifier(enemy, "modifier_sniper_shrapnel_slow")
if mod then
    local remaining = Modifier.GetDieTime(mod) - GameRules.GetGameTime()
    local stacks    = Modifier.GetStackCount(mod)   -- 0 if unstacked
end
```

---

## Check unit states (stunned, magic-immune, ...)

`HasState` is the right tool. It covers stun, silence, hex, BKB, root.

```lua
local MS = Enum.ModifierState
if NPC.HasState(enemy, MS.MODIFIER_STATE_MAGIC_IMMUNE) then
    -- a single-target magic spell will not land
end
if NPC.HasState(enemy, MS.MODIFIER_STATE_STUNNED) then
    -- enemy cannot act
end

-- remaining seconds of several states at once:
local dur = NPC.GetStatesDuration(enemy,
    { [MS.MODIFIER_STATE_STUNNED] = true, [MS.MODIFIER_STATE_HEXED] = true })
```

---

## Predict a target's position

`NPC.GetMoveSpeed` is a STAT, not a velocity, so it never tells you motion.
Use the networked velocity vector instead, and pcall-guard it (undocumented).

```lua
local function velocity_of(unit)
    local ok, v = pcall(Entity.GetField, unit, "m_vecVelocity")
    if ok and v then return v end
    return Vector(0, 0, 0)
end

-- intercept point for a fixed-delay ground ability:
local lead   = 0.5                                   -- seconds of total delay
local future = Entity.GetAbsOrigin(target) + velocity_of(target) * lead
```

`NPC.IsMoving(unit)` and `NPC.IsRunning(unit)` are the "is it actually moving"
booleans if you only need yes/no.

---

## Effective HP and a simple kill check

There is no single effective-HP call, so compose it. Barriers (shields) sit
on top of HP; armor and resist scale the damage.

```lua
-- can `magical_damage` of magic damage kill `enemy` right now?
local function magic_kills(enemy, magical_damage)
    local bars   = NPC.GetBarriers(enemy)
    local shield = bars and bars.all and bars.all.current or 0
    local hp     = Entity.GetHealth(enemy) + shield
    local mult   = NPC.GetMagicalArmorDamageMultiplier(enemy)   -- e.g. 0.75
    return magical_damage * mult >= hp
end
```

For physical damage use `NPC.GetArmorDamageMultiplier`. `NPC.HasAegis(enemy)`
is effectively a second life, so fold it in before committing a kill combo.

---

## Distance between two units

```lua
local function dist(a, b)
    local pa, pb = Entity.GetAbsOrigin(a), Entity.GetAbsOrigin(b)
    return (pa - pb):Length2D()          -- 2D, ignores the z axis
end

-- range check without building Vectors yourself:
if NPC.IsEntityInRange(me, target, 600) then
    -- target is within 600 units
end
```

---

## Effective cast / attack range (base + bonus)

`Ability.GetCastRange` and `NPC.GetAttackRange` are BASE values.

```lua
local cast_range   = Ability.GetCastRange(ab) + NPC.GetCastRangeBonus(me)
local attack_range = NPC.GetAttackRange(me)   + NPC.GetAttackRangeBonus(me)
```

---

## Iterate your own abilities and items

```lua
for i = 0, 25 do
    local ab = NPC.GetAbilityByIndex(me, i)
    if ab then print(i, Ability.GetName(ab)) end
end
for i = 0, 20 do
    local item = NPC.GetItemByIndex(me, i)
    if item then print(i, Ability.GetName(item)) end
end
```

---

## Logging for debugging

```lua
print("value is", some_table)        -- console + debug.log, auto-stringifies
```

`print` and `log` write to `%cheat_dir%/debug.log`. Play a demo, then read the
log. That round-trip is the core debugging loop. Keep heavy work out of
`OnDraw` (FPS cost); log instead.
