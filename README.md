# llm4mesen

llm4mesen is a research framework for evaluating the game-playing and reasoning abilities of large language models (LLMs) in classic 2D NES games using the Mesen emulator.

The project connects LLMs to an emulated game environment through a Python-based pipeline, using multimodal prompts (screenshots + text) and strictly constrained controller inputs. Gameplay is paused during inference, allowing models to act without real-time constraints, inspired by tool-assisted speedruns.

We evaluate several Gemini models on *Super Mario Bros.* and *The Legend of Zelda* using game-specific progress metrics. Results show that while LLMs outperform random play, they struggle with precise control, spatial reasoning, and long-term planning, remaining far from human-level performance.
