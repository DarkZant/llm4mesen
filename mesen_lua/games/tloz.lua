local Game = {}

local function getCurrentGamemode()
    -- 0 : Title | 1 : Selection Screen | 5 : Normal | 4/6/7 : Scrolling | 11 : Cave
    -- 17 : Game Over | 8 : Game Over Continue Select
	local memGamemode = emu.read(0x0012, emu.memType.nesInternalRam, false)
	-- emu.log("Gamemode: " .. memGamemode)
	return memGamemode
end

local function textIsDone()
    local textCountdown = emu.read(0x0029, emu.memType.nesInternalRam, false)
    return textCountdown == 0
end

function Game.getCurrentProgress()
    local currentGamemode = getCurrentGamemode()
	if currentGamemode <= 1 or currentGamemode == 8 then
		return "START SCREEN"
    elseif currentGamemode == 17 then 
        return "GAME OVER"
    end
    return "Alive"
end

function Game.playerHasControl()
    local currentGamemode = getCurrentGamemode()
	if currentGamemode == 5 then
		return true
    elseif currentGamemode == 11 and textIsDone() then 
        return true
    end
	return false
end

return Game