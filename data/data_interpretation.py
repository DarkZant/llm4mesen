import os
from typing import Tuple

from mesen_python.games import SMB, TLOZ
from gemini.gemini_models import GeminiModels

smb = SMB()
playthrough_path = smb.get_playthrough_folder_path()

def get_smb_best_playthrough_progress(model_file_name: str) -> Tuple[str, str]:
    """Gets the best SMB progress achieved by a model in its playthrough data files"""
    def progress_to_float(progress_str: str) -> float:
        return float(progress_str.strip("("))

    best_world_level = ""
    best_level_progress = 0.0
    best_parameters = ""
    for data_file in os.listdir(playthrough_path):
        # Verify that the file corresponds to the model
        file_params = data_file.strip(".csv").split("__")
        wrong_model = False
        for param in file_params:
            if param.startswith("model="):
                model_in_file = param.split("=")[1]
                if model_in_file != model_file_name:
                    wrong_model = True
                    break
        if wrong_model:
            continue
        
        # Verify the playthroughs in the file
        with open(f"{playthrough_path}/{data_file}", "r") as f:
            playthroughs = f.readlines()
            
            for playthrough in playthroughs:
                steps = playthrough.split(',')
                for step in steps:
                    step = step.strip()
                    if step == "GAME OVER":
                        continue 
                    progress = step.split('|')[1]
                    progress = progress.split(' ')
                    world_level = progress[0]       

                    if world_level > best_world_level:
                        best_world_level = world_level
                        best_level_progress = progress_to_float(progress[1])
                        if best_parameters != data_file:
                            best_parameters = data_file
                    elif world_level == best_world_level:
                        level_progress = progress_to_float(progress[1])
                        if level_progress > best_level_progress:
                            best_level_progress = level_progress
                            if best_parameters != data_file:
                                best_parameters = data_file

    
    return f"{best_world_level} ({best_level_progress:.1f} %)", best_parameters


def convert_units_to_progress(units: int) -> str:
    """Converts SMB horizontal units to world-level and percentage progress"""
    level1_and_level2_units = 3161 
	
    world_level = "1-1" if units <= level1_and_level2_units else "1-2"

    if world_level == "1-1":
        level_progress = (units / level1_and_level2_units) * 100 
    elif world_level == "1-2":
        level_progress = ((units - level1_and_level2_units) / level1_and_level2_units) * 100
    if level_progress > 100.0:
        level_progress = 100.0
    level_progress_str = f"({level_progress:.1f} %)"

    return world_level + " " + level_progress_str


def get_lmgame_progress():
    """Prints the SMB progress of LMGame-Bench models in LaTeX table format"""
    lmgame_units = [
        # (model, (no harness units, harness units))
        ("claude-3-5-sonnet-20241022", (1540, 1267.7)),
        ("claude-3-7-sonnet-20250219 (thinking)", (1430.0, 1418.7)),
        ("gemini-2.5-flash-preview-04-17 (thinking)", (1540.7, 1395.0)),
        ("gemini-2.5-pro-preview-05-06 (thinking)", (1025.3, 1498.3)),
        ("llama-4-maverick-17b-128e-instruct-fp8", (786.0, 1468.7)),
        ("gpt-4.1-2025-04-14", (1991.3, 2126.3)),
        ("gpt-4o-2024-11-20", (1028.3, 2047.3)),
        ("o1-2024-12-17", (1434.0, 855.0)),
        ("o3-2025-04-16", (1955.0, 3445.0)),
        ("o4-mini-2025-04-16", (1348.3, 1448.0)),
        ("Random", (987.0, 987.0)), # No harnessing for random
    ]

    for model, (no_harness_units, harness_units) in lmgame_units:
        no_harness_progress = convert_units_to_progress(no_harness_units).replace("%", "\\%")
        harness_progress = convert_units_to_progress(harness_units).replace("%", "\\%")
        print(f"{model} & {no_harness_progress} & {harness_progress} \\\\")
        print("\\hline")



def main():    
    """Prints the best SMB progress of Gemini models in LaTeX table format"""
    models = [
        GeminiModels.PRO_3, 
        GeminiModels.FLASH_3_THINKING, 
        GeminiModels.FLASH_3,
        GeminiModels.FLASH_2_5,
        GeminiModels.FLASH_LITE_2_5,
        GeminiModels.FLASH_2_0
    ]
    for model in models:
        best_progress, file_name = get_smb_best_playthrough_progress(model.get_file_name())
        best_progress = best_progress.replace("%", "\\%")
        parameters = file_name.strip(".csv").split("__")
        params = {
            "frame": None,
            "scr": None,
            "freq": None
        }
        for param in parameters:
            key, value = param.split("=")
            if key in params:
                params[key] = value
        if params['freq'] == None:
            params['freq'] = '1'
        row = [
            model.get_model_name(),
            best_progress,
            params['frame'],
            params['scr'],
            params['freq']
        ]
        print(f"{' & '.join(row)} \\\\")
        print("\\hline")

if __name__ == "__main__":
    main()
