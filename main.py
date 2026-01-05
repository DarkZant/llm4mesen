import time
from collections import deque

from gemini import *
from chatgpt import *
from mesen_python import *


INPUT_LENGTH = 30  # Number of frames the inputs will be applied for
N_SCREENSHOTS = 3  # Number of screenshots to provide to the LLM (all in one file)
FREQ_SCREENSHOTS = 1 if N_SCREENSHOTS > 1 else 1 # Frequency of screenshots (in frames)

game = SMB(
    input_length=INPUT_LENGTH,
    n_screenshots=N_SCREENSHOTS,
    freq_screenshots=FREQ_SCREENSHOTS
)
valid_inputs = set(game.get_valid_inputs())


LLM_INPUT = True
if LLM_INPUT:
    # llm = ChatGPTAPI(ChatGPTModels.NANO_5)
    # llm = GeminiAPI(GeminiModels.FLASH_LITE_2_5)
    llm = GeminiBrowser(GeminiModelModes.FAST)
n_same_progress_equals_stuck = 3
ADD_STUCK_PROMPT = True if LLM_INPUT else False
ADD_PROGRESS_PROMPT = True
STOP_ON_GAME_OVER = True


def get_initial_context_prompt():
    return (
        f"You are a video game player. You are currently playing the game {game.get_full_name()} "
        f"for the {game.get_console()}. The goal of the game is: {game.get_game_objective()}\n"

        "Your answers will be limited. The only thing you can answer is a combination of these inputs, "
        f"separated by commas (,): {game.get_inputs_description()}"
        f"The inputs you answer will be applied for {game.get_frame_window_length()} frames, which is equivalent to {game.get_input_hold_time()} seconds, "
        "after which you will receive a new image to repeat the process."
        "The inputs you answer must respect the format and they must contribute to reaching the game's goal. Only one of each input must be in the answer. "
        f"If you see that the inputs have no effects on the game, try different ones, don't try the same inputs more than {n_same_progress_equals_stuck} times if you don't see any changes.\n"

        f"To decide which inputs to choose, you will be given images of the last {game.get_screenshot_history_length()} "
        "frames that the game has rendered, where the leftmost frame is the oldest and the rightmost frame is the most recent. "
        "With these images, you will also receive your current game progress.\n"

        'Answer "Understood." if you understood these instructions.'
    )


INPUT_SHORTCUTS = {
    "l" : "left", 
    "d" : "down", 
    "r" : "right",
    "u" : "up"
}

def get_user_input() -> str:
    inputs = input(f"Enter an input sequence: ")
    inputs_split = inputs.split(",")
    for i in range(len(inputs_split)):
        if inputs_split[i] in INPUT_SHORTCUTS.keys():
            inputs_split[i] = INPUT_SHORTCUTS[inputs_split[i]]

    return ','.join(inputs_split)


def get_llm_input(progress: str, frames_image: str) -> str:
    if ADD_PROGRESS_PROMPT:
        llm.add_text_to_prompt("Progress: " + progress)
        
    answer = llm.send_image_prompt(frames_image) 
    # Allowing the LLM to add spaces after the commas 
    no_space_answer = answer.replace(" ", "").strip()
    if inputs_are_valid(no_space_answer):
        return no_space_answer
    
    return answer


def inputs_are_valid(inputs: str) -> bool:
    if inputs == "":
        return True
    
    inputs_set = set(input for input in inputs.split(","))
    return inputs_set.issubset(valid_inputs)  


def main():
    """Main execution loop"""
    if LLM_INPUT:
        print("Playing LLM:", llm.get_model_name())

        initial_context_prompt = get_initial_context_prompt()

        print("-" * 30 + "\n" + initial_context_prompt + "\n" + "-" * 30)

        llm.start_new_temporary_chat()
        response = llm.send_text_prompt(initial_context_prompt)
        print("Model's response to initial prompt:", response)

    game.play()

    input_time = 0
    playthrough = []

    def add_to_playthrough(inputs: str, progress: str):
        playthrough.append(inputs.replace(",", ";") + '|' + progress)

    progress_queue = deque(maxlen=n_same_progress_equals_stuck)

    print('\nStarting playing sequence\n' + "-" * 30)

    while True:
        input_timeout = game.get_input_timeout()

        progress = game.get_progress()    
        print("Progress:", progress)

        progress_queue.append(progress)
        # If the LLM is stuck, we tell it to try something else
        if ADD_STUCK_PROMPT and len(progress_queue) == n_same_progress_equals_stuck and len(set(progress_queue)) == 1:
            print("LLM is stuck. Adding help to prompt.")
            llm.add_text_to_prompt("No progress is being made, try different inputs.\n")

        if progress == "GAME OVER":
            playthrough.append(progress)
            if LLM_INPUT:
                playthrough_file = game.save_playthrough(playthrough, llm.get_model_file_name())
                print(f"Saved playthrough to {playthrough_file}\n" + "-" * 15)
                if STOP_ON_GAME_OVER:
                    break
                llm.start_new_temporary_chat()
                llm.send_text_prompt(get_initial_context_prompt())
            playthrough = []

        elif progress == "DEAD":
            # Tell the model that it has died
            playthrough.append(progress)
            llm.add_text_to_prompt("You died and you've respawned!\n")
            continue

        recent_frames = game.get_recent_frames()

        if input_time > input_timeout:
            print("Skipping input because Python is late...\n" + "-" * 15)
            input_time -= input_timeout
            add_to_playthrough("Skipped", progress)
            continue

        time_before_input = time.time()
        inputs = get_llm_input(progress, recent_frames) if LLM_INPUT else get_user_input()
        input_time = time.time() - time_before_input

        if input_time > input_timeout:
            print(f"Input took longer than {input_timeout}s. Moving to next window...")
            input_time -= input_timeout
            add_to_playthrough("Skipped", progress)
            
        elif not inputs_are_valid(inputs):
            print(f"Invalid inputs: {inputs}. Moving to next window...")
            game.apply_inputs(None)
            add_to_playthrough("Invalid", progress)
            if LLM_INPUT:
                llm.add_text_to_prompt("The previous answer's format was invalid. Please provide only inputs separated by commas (,).\n")

        else:
            print('Applying inputs:', inputs)
            game.apply_inputs(inputs)
            playthrough_input = "None" if inputs == "" else inputs
            add_to_playthrough(playthrough_input, progress)

        print("-" * 15)



if __name__ == "__main__":
    main()