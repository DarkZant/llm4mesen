import io
from abc import ABC, abstractmethod
from typing import List

from PIL import Image

from .mesen import Mesen

SCREENSHOT_PATH = "recent_frames.png"
GAMES_DATA_PATH = "data"  


def merge_pngs_horizontally(png_byte_list, separator_width=1):
    """
    png_byte_list: list of PNGs in byte form
    separator_width: width of the vertical black line (default = 1 pixel)
    """

    # Decode PNG bytes into Pillow images
    images = [Image.open(io.BytesIO(png)) for png in png_byte_list]

    # Compute new canvas size
    total_width = sum(img.width for img in images) + separator_width * (len(images) - 1)
    max_height = max(img.height for img in images)

    # Create background (RGBA black)
    result = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 255))

    # Paste frames and separators
    x = 0
    for i, img in enumerate(images):
        result.paste(img, (x, 0))
        x += img.width
        if i < len(images) - 1:  # add separator if not last
            for y in range(max_height):
                result.putpixel((x, y), (0, 0, 0, 255))
            x += separator_width

    # Convert back to PNG bytes
    output = io.BytesIO()
    result.save(output, format="PNG")
    return output.getvalue()


class Game(ABC):
    """Abstract class representing a game to be played in Mesen"""
    def __init__(self, 
                 input_length: int=30,
                 n_screenshots: int=1,
                 freq_screenshots: int=1,
                 mesen_timeout: int=180,
                 saved_screenshot_file_path: str=SCREENSHOT_PATH,
                 saved_playthrough_path: str=GAMES_DATA_PATH,
                 ):
        self.mesen = Mesen()
        self.playthrough_path = saved_playthrough_path
        self.screenshot_path = f"{saved_playthrough_path}/{self.get_acronym()}/{saved_screenshot_file_path}"
        self.input_length = input_length
        self.n_screenshots = n_screenshots
        self.freq_screenshots = freq_screenshots
        self.mesen_timeout = mesen_timeout


    def get_playthrough_filename(self, model_name: str) -> str:
        params = {
            "frame" : self.input_length,
            "scr" : self.n_screenshots,
            "freq" : self.freq_screenshots,
            "model" : model_name
        }
        return "__".join(f"{k}={params[k]}" for k in sorted(params)) + ".csv"  
    

    def save_playthrough(self, playthrough: List[str], model: str) -> str:
        playthrough_file = f"{self.get_playthrough_folder_path()}/{self.get_playthrough_filename(model)}"
        with open(playthrough_file, "a") as f:
            f.write(','.join(playthrough) + "\n")

        return playthrough_file
    

    def get_playthrough_folder_path(self) -> str:
        return f"{self.playthrough_path}/{self.get_acronym()}/playthroughs/"


    def get_recent_frames(self) -> str:
        screenshots = []
        for _ in range(self.n_screenshots):
            image_length = self.mesen.receive_int()
            image_data = self.mesen.receive_bytes(image_length)
            screenshots.append(image_data)
        with open(self.screenshot_path, "wb") as f:
            f.write(merge_pngs_horizontally(screenshots))

        return self.screenshot_path


    def get_progress(self) -> str:
        return self.mesen.receive_line()


    def get_input_timeout(self) -> int:
        return self.mesen_timeout
    

    def get_frame_window_length(self) -> int:
        return self.input_length
    

    def get_screenshot_history_length(self) -> int:
        return self.n_screenshots
    
    
    def get_screenshot_frequence(self) -> int:
        return self.freq_screenshots
    

    def set_mesen_timeout(self, timeout: int):
        self.mesen_timeout = timeout


    def set_input_length(self, n_frames: int):
        self.input_length = n_frames


    def set_screenshot_history_length(self, length: int):
        self.n_screenshots = length


    def set_screenshot_frequence(self, freq: int):
        self.freq_screenshots = freq


    def send_hyperparameters(self):
        self.mesen.send_number(self.mesen_timeout)
        self.mesen.send_number(self.input_length)
        self.mesen.send_number(self.n_screenshots)
        self.mesen.send_number(self.freq_screenshots)


    def play(self):
        self.mesen.connect()
        self.send_hyperparameters()


    def apply_inputs(self, inputs: str):
        message = inputs
        if message == None:
            message = ""

        self.mesen.send_string(message)


    def get_full_name(self) -> str:
        return self.get_game_name() + f" ({self.get_release_year()})"
    
    
    def get_inputs(self) -> str:
        return ','.join(self.get_valid_inputs())
    
    
    def get_input_hold_time(self) -> float:
        return self.input_length / self.get_fps()
    

    @abstractmethod
    def get_acronym(self) -> str:
        pass

    
    @abstractmethod
    def get_valid_inputs(self) -> str:
        pass
    
    
    @abstractmethod
    def get_game_name(self) -> str:
       pass
    

    @abstractmethod   
    def get_release_year(self) -> int:
        pass  

    @abstractmethod
    def get_inputs_description(self) -> str:
        pass
    
    @abstractmethod
    def get_game_objective(self) -> str:
        pass

    @abstractmethod
    def get_console(self) -> str:
        pass

    @abstractmethod
    def get_fps(self) -> int:
        pass



class SMB(Game):

    def get_acronym(self):
        return "smb"

    def get_valid_inputs(self):
        return ["left", "down", "right", "a", "b"]
        

    def get_game_name(self):
        return "Super Mario Bros."
    

    def get_release_year(self):
        return 1985
    

    def get_inputs_description(self):
        return '\n' + '\n'.join([
            "left : Moves Mario left.",
            "right : Moves Mario right.",
            "down : Makes Mario enter vertical pipes if they are enterable. Also allows big Mario to crouch.",
            "a : Makes Mario jump. Holding it longer makes Mario jump higher. The button needs to be released to jump again.",
            "b : Holding it makes Mario run faster when 'left' or 'right' is also held. Tapping it allows fiery Mario to shoot fireballs."
        ]) + '\n'
    

    def get_game_objective(self):
        return (
            "You must reach the flag pole at the end of each regular level and the axe at the end of each castle level, which are both always to the right. "
            "Jumping over pipes, enemies, obstacles and gaps is crucial to progress."
        )
    

    def get_console(self):
        return "NES"
    

    def get_fps(self):
        return 60
    

class TLOZ(Game):

    def get_acronym(self):
        return "tloz"

    def get_valid_inputs(self):
        return ["up", "left", "down", "right", "a", "b"]
        

    def get_game_name(self):
        return "The Legend of Zelda"
    

    def get_release_year(self):
        return 1986
    

    def get_inputs_description(self):
        return '\n' + '\n'.join([
            "left : Moves Link left.",
            "right : Moves Link right.",
            "down : Moves Link down.",
            "up : Moves Link up.",
            "Link cannot move in a diagonal, only one directional input must be chosen at a time.",
            "a : Makes Link use the equipped item.",
            "b : Makes Link attack with his sword."
        ]) + '\n'
    

    def get_game_objective(self):
        return (
            "You must beat all the dungeons and defeat Ganon while obtaining various items on the way."
        )
    

    def get_console(self):
        return "NES"
    

    def get_fps(self):
        return 60