# llm4mesen

llm4mesen is a research framework for evaluating the game-playing and reasoning abilities of large language models (LLMs) in classic 2D games using the Mesen emulator.

The project connects LLMs to an emulated game environment through a Python-based pipeline, using multimodal prompts (screenshots + text) and strictly constrained controller inputs. Gameplay is paused during inference, allowing models to act without real-time constraints, inspired by tool-assisted speedruns.

We evaluate several Gemini models on *Super Mario Bros. (1985)* and *The Legend of Zelda (1986)* using game-specific progress metrics. Results show that while LLMs outperform random play, they struggle with precise control, spatial reasoning, and long-term planning, remaining far from human-level performance.

## How to execute
1. Install the [Mesen](https://www.mesen.ca/) emulator.
2. Obtain the ROM of the game you want the LLMs to play, and open it in Mesen.
3. Clone the repository and install the Python requirements.
4. Open `main.py`.
5. Select the LLM you want to evaluate with the `llm = ...` line and make sure your API keys are properly set in your OS environment.
6. Execute `main.py` with Python.
7. In Mesen, open the Script Window: *Debug → Script Window*.
8. In the Script Window, open `mesen_lua/main.lua`.
9. Modify the `local game = require("games.smb")` import so that the imported game script, located in `mesen_lua/games/`, corresponds to the game your playing.
10. Press *Run Script*. You should see the LLM playing the game!

## Project Structure
```text
llm4mesen/
├── chatgpt/                        # ChatGPT module (API only)
├── gemini/                         # Gemini module
│   ├── gemini_api.py               # Gemini API class
│   └── gemini_browser.py           # Browser version of Gemini from gemini.google.com. Requires Google Chrome
├── mesen_lua/                      # Lua scripts executed by Mesen
│   ├── games/                      # The individual Lua scripts for each game
│   └── main.lua                    # The main script executed my Mesen
├── mesen_python/                   # Python wrapper modules for the games and Mesen
└── main.py                         # Main script to execute for the Python program
```
