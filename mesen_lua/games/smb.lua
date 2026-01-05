local Game = {}

local function getMariosCurrentPosition()
	local currentScreen = emu.read(0x006D, emu.memType.nesInternalRam, false) * 256
	local marioXPos = emu.read(0x0086, emu.memType.nesInternalRam, false)
	local pos = currentScreen + marioXPos
	-- emu.log("Mario's Position: " .. tostring(pos))
	return pos
end

local function getMariosState()
	-- 8 : Playing | 6 : Game Over | Dying : 11
	local marioState = emu.read(0x000E, emu.memType.nesInternalRam, false)
	-- emu.log("Mario's State: " .. tostring(marioState))
	return marioState
end

local function getMariosVerticalScreenPosition()
	-- 0 : Above Viewport | 1 : Viewport | > 1 : Below Viewport
	local marioVertical = emu.read(0x00B5, emu.memType.nesInternalRam, false)
	-- emu.log("Mario Vertical Screen Position: " .. tostring(marioVertical))
	return marioVertical
end

local function marioIsDead() return end

local function getCurrentGamemode()
	-- 0 : Start Screen & Demo | 1 : Playing | 2 : Toad/Peach Castle Cutscene | 3 : Game Over 
	local memGamemode = emu.read(0x0770, emu.memType.nesInternalRam, false)
	-- emu.log("Gamemode: " .. memGamemode)
	return memGamemode
end

local function getCurrentLevel()
	local currentWorld = emu.read(0x075F, emu.memType.nesInternalRam, false) + 1
	local currentLevel = emu.read(0x0760, emu.memType.nesInternalRam, false) + 1
	if (currentWorld <= 2 or currentWorld == 4 or currentWorld == 7) and currentLevel > 2 then
		currentLevel = currentLevel - 1
	end
	local currentWorldLevel = tostring(currentWorld) .. '-' .. tostring(currentLevel)
	--emu.log("Current Level: " .. currentWorldLevel)
	return currentWorldLevel
end

local maxProgressLevelMap = {
	["1-1"] = 3161,
	["1-2"] = 3161,
	["1-3"] = 2425,
	["1-4"] = 2261,
	["2-1"] = 3193,
	["2-2"] = 3161,
	["2-3"] = 3593,
	["2-4"] = 2261
}

function Game.getCurrentProgress()
	local currentGamemode = getCurrentGamemode()
	if currentGamemode == 3 then
		return "GAME OVER"
	elseif currentGamemode == 0 then
		return "START SCREEN"
	end
	local marioState = getMariosState()
	if marioState == 11 then 
		return "DEAD"
	end
	
	local currentLevel = getCurrentLevel()
	local marioPos = getMariosCurrentPosition()
	local progress = (marioPos / maxProgressLevelMap[currentLevel]) * 100
	local progressPercentage = math.floor(progress * 10 + 0.5) / 10
	if progressPercentage > 100 then
		progressPercentage = 100
	end
	local currentProgress = currentLevel .. " (" .. tostring(progressPercentage) .. " %)"
	--emu.log(currentProgress)
	return currentProgress
end

function Game.playerHasControl()
	local marioState = getMariosState()
	local currentGamemode = getCurrentGamemode()
	local marioVertical = getMariosVerticalScreenPosition()
	local marioIsControllable = marioState == 8 and currentGamemode ~= 2 and marioVertical < 2
	-- emu.log("Is Mario controllable? " .. tostring(marioIsControllable))
	return marioIsControllable
end

return Game