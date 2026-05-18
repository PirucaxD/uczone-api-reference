-- starter_script.lua
--
-- A minimal, correct UCZone (Dota 2) script skeleton. Copy it into
-- %cheat_dir%/scripts/, rename it, and replace the example action with your
-- own logic. Every line is commented for a first-time reader.
--
-- Walkthrough: ../GETTING_STARTED.md   Snippets: ../COOKBOOK.md
-- Run the linter on your edited copy:  python ../tools/lint_uczone_script.py
--
---@diagnostic disable: undefined-global

-- A script returns a table of callback handlers. The framework calls a
-- handler whenever its event fires. `OnUpdate` runs once per frame.
local script = {}

----------------------------------------------------------------------------
-- MENU
--
-- Menu.Create(category, tab, section) returns a tab object; tab:Create(name)
-- returns a group you add widgets to. Keep a handle to every widget.
----------------------------------------------------------------------------
local tab   = Menu.Create("General", "Main", "Starter Script")
local group = tab:Create("Main")

local ui = {}
-- Switch(label, default_value) -> a boolean widget. Read it with :Get().
ui.enabled = group:Switch("Enable", false)

----------------------------------------------------------------------------
-- STATE
--
-- Heroes.GetLocal() returns YOUR hero, but only once a game is running -
-- it is nil in menus / hero-select / right after a reconnect. Cache it and
-- re-acquire when nil, rather than calling it every frame.
----------------------------------------------------------------------------
local my_hero = nil

----------------------------------------------------------------------------
-- LOGIC
----------------------------------------------------------------------------

-- Example action: use Phase Boots while running. Safe, and it shows the
-- standard shape - find the item, check it is castable, then cast.
-- Replace this whole function with your own behaviour.
local function example_use_phase_boots()
    -- NPC.GetItem returns the item handle or nil.
    local item = NPC.GetItem(my_hero, "item_phase_boots")
    if not item then return end

    -- IsCastable checks cooldown / mana / level / slot in one call.
    -- Pass the mana you actually have as the budget.
    if not Ability.IsCastable(item, NPC.GetMana(my_hero)) then return end

    -- Only worth it while moving.
    if not NPC.IsRunning(my_hero) then return end

    -- CastNoTarget issues the order. (item handles use the Ability.* API.)
    Ability.CastNoTarget(item)
end

-- Called once per frame while a game is live and the menu switch is on.
local function tick()
    example_use_phase_boots()
    -- ... your per-frame decisions go here. See ../COOKBOOK.md.
end

----------------------------------------------------------------------------
-- CALLBACKS
----------------------------------------------------------------------------

function script.OnUpdate()
    -- (Re)acquire the hero handle. Bail this frame if there is no game yet.
    if not my_hero then
        my_hero = Heroes.GetLocal()
        return
    end

    -- Cheap guards first: respect the menu, and only act while alive.
    if not ui.enabled:Get() then return end
    if not Entity.IsAlive(my_hero) then return end

    tick()
end

-- `print` / `log` write to the console and %cheat_dir%/debug.log, and
-- auto-stringify tables - the main debugging tool. Avoid heavy OnDraw
-- rendering; it can tank FPS.
function script.OnGameEnd()
    print("[starter_script] game ended")
end

return script
