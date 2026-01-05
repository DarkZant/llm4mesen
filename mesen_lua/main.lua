local socket = require("socket.core")
local game = require("games.smb")


local client = socket.tcp()
local timeout = 10
client:settimeout(timeout)
local connected, err = client:connect("localhost", 9999)

function sendLine(line)
	client:send(line .. "\n")
end

local frameWindowLength = 10
local screenshotHistoryLength = 3
local screenshotFrequence = 3

local dropInputOnLastFrame = true

local screenshots = {}
local gameOver = false

function receiveFromPython()
	local currentFrame = emu.getState()["ppu.frameCount"]
	local frameDiff = math.fmod(currentFrame, frameWindowLength)

	if isScreenshotFrame(frameDiff) then
		saveScreenshot(emu.takeScreenshot())
	end

	local progress = game.getCurrentProgress()

	if progress == "START SCREEN" then 
		local inputFunc = function() emu.setInput({start = true}, 0) end
		if startInput == nil and math.fmod(currentFrame, 10) == 0 then
			emu.log("Start screen: Pressing Start...")
			startInput = emu.addEventCallback(inputFunc, emu.eventType.inputPolled)
		elseif startInput ~= nil and math.fmod(currentFrame, 10) == 5 then
			emu.removeEventCallback(startInput, emu.eventType.inputPolled)
		    startInput = nil
		end
		return
	elseif startInput ~= nil then
		emu.removeEventCallback(startInput, emu.eventType.inputPolled)
		startInput = nil
		emu.log("Out of start screen")
	end

	if progress == "GAME OVER" then 
		if inputForNextFrame then
			emu.removeEventCallback(inputForNextFrame, emu.eventType.inputPolled)
		end
		if not gameOver then
			gameOver = true
			sendLine(progress)
			emu.log(progress)
		end
		return
	elseif gameOver == true then 
		gameOver = false
	end

	if progress == "DEAD" and inputForNextFrame then
		emu.log("Dead, removing inputs.")
		emu.removeEventCallback(inputForNextFrame, emu.eventType.inputPolled)
	end

	if dropInputOnLastFrame and frameDiff == frameWindowLength - 1 and inputForNextFrame then 
		-- emu.log("Last frame before Python. Removing inputs. Current frame: " .. tostring(currentFrame))
		emu.removeEventCallback(inputForNextFrame, emu.eventType.inputPolled)
	end

	if frameDiff ~= 0 or not game.playerHasControl() or #screenshots < screenshotHistoryLength then
		return
	end
	
	emu.log(string.rep("-", 15) .."\nSending to Python")

	sendLine(progress)

	for i = 1, screenshotHistoryLength do
		local png = screenshots[i]
		local size = #png 
		sendLine(size)
		client:send(png)
	end

	message, err = client:receive("*l")  
	if message then
    	emu.log("Inputs received from Python: " .. message)
    	if message == "pause" then
    		emu.breakExecution()
    	end
    	local t = {}
		for token in string.gmatch(message, "[^,]+") do
		    t[token] = true
		end
		local inputFunc = function () emu.setInput(t, 0) end
		if inputForNextFrame then
			emu.removeEventCallback(inputForNextFrame, emu.eventType.inputPolled)
		end
		inputForNextFrame = emu.addEventCallback(inputFunc, emu.eventType.inputPolled)
    elseif err == "timeout" then
        emu.log("Message took too long ( > " .. timeout .. "s ). Advancing to the next frame...")
    elseif err == "closed" then
        if inputForNextFrame then
			emu.removeEventCallback(inputForNextFrame, emu.eventType.inputPolled)
		end
    	emu.removeEventCallback(listenForPython, emu.eventType.startFrame)
        emu.log("Connection closed by server: Stopping script.")  
    end

end

function setHyperparameters()
	local message, err = client:receive("*l")
	timeout = tonumber(message)
	client:settimeout(timeout)

	message, err = client:receive("*l")
	frameWindowLength = tonumber(message)

	message, err = client:receive("*l")
	screenshotHistoryLength = tonumber(message)

	message, err = client:receive("*l")
	screenshotFrequence = tonumber(message)
end

function isScreenshotFrame(frameDiff)
	if frameDiff == 0 then 
		return true 
	end 

	local mostRecentFrameDiff = frameWindowLength - screenshotFrequence
	local oldestFrameDiff = frameWindowLength - (screenshotHistoryLength - 1) * screenshotFrequence

	for targetFrame = mostRecentFrameDiff, oldestFrameDiff, -screenshotFrequence do 
		if frameDiff == targetFrame then
			return true
		end
	end

	return false
end 

function saveScreenshot(newSS)
    if #screenshots < screenshotHistoryLength then
        table.insert(screenshots, newSS)
    else
        for i = 1, screenshotHistoryLength - 1 do
            screenshots[i] = screenshots[i + 1]
        end
        screenshots[screenshotHistoryLength] = newSS
    end
end

--- Main ---

function resetEmu()
	emu.reset()
	emu.removeEventCallback(initialReset, emu.eventType.startFrame)
end

if connected then
	initialReset = emu.addEventCallback(resetEmu, emu.eventType.startFrame)
	setHyperparameters()
	listenForPython = emu.addEventCallback(receiveFromPython, emu.eventType.startFrame)
	emu.log("Successfully connected to Python")
else
	emu.log("Couldn't connect to Python: " .. err .. ". Stopping Script.")
end

--- Testing and Utility ---

function logAllTableProperties(t)
    for k, v in pairs(t) do
    	emu.log(k .. "")
    end
end

function checkInput(input)
	if emu.getInput(0)[input] then
		emu.log(input .. " is being pressed on frame: " .. tostring(emu.getState()["ppu.frameCount"]))
	end
end
