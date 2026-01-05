import time

from playwright.sync_api import sync_playwright

from .gemini_models import GeminiModels, GeminiModel

from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "gemini_browser_paths.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

USER_DATA_DIR = config["user_data_dir"]
GOOGLE_CHROME_PATH = config["chrome_path"]

class ModelMode:
    def __init__(self, gemini_model: GeminiModel, button_data_test_id: str):
        self.gemini_model = gemini_model
        self.button_data_test_id = button_data_test_id


    def get_button_selector(self) -> str:
        return f"button[data-test-id='{self.button_data_test_id}']"
    

    def get_file_name(self) -> str:
        return self.gemini_model.get_file_name()
    

    def get_pretty_name(self) -> str:
        return self.gemini_model.get_pretty_name()
    

class GeminiModelModes:
    FAST = ModelMode(GeminiModels.FLASH_3, "bard-mode-option-fast")
    THINKING = ModelMode(GeminiModels.FLASH_3_THINKING, "bard-mode-option-thinking")
    PRO = ModelMode(GeminiModels.PRO_3, "bard-mode-option-pro")
    

class GeminiBrowser:

    class _ChatModes:
        EMPTY_NEW_CHAT = 0
        TEMPORARY_CHAT = 1
        FILLED_NEW_CHAT = 2
    
    def __init__(self, mode: ModelMode):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            channel="chrome",
            executable_path=GOOGLE_CHROME_PATH, 
            headless=False,
        )
        self.page = self.browser.new_page()
        self.page.goto("https://gemini.google.com/app")
        self.chat_mode = self._ChatModes.EMPTY_NEW_CHAT
        self.nb_prompts = 0
        current_model_mode = self._get_current_model_mode()
        if current_model_mode == mode:
            self.model_mode = mode 
        else: 
            self.model_mode = current_model_mode
            self.switch_model_mode(mode)

        self.current_image = None

    
    def start_new_temporary_chat(self):
        if (self.chat_mode == self._ChatModes.TEMPORARY_CHAT):
            self.start_new_chat()
        button = self.page.locator('button.temp-chat-button')
        self.chat_mode = self._ChatModes.TEMPORARY_CHAT
        self.nb_prompts = 0
        button.click()


    def start_new_chat(self):
        button = self.page.locator('button[aria-label="New chat"]')
        self.chat_mode = self._ChatModes.EMPTY_NEW_CHAT
        self.nb_prompts = 0
        button.click()


    def _get_latest_answer(self):
        # Container for all prompt+answer pairs
        container = self.page.locator('infinite-scroller[data-test-id="chat-history-container"]')
        # Most recent message, last in the history
        last_message = container.locator(":scope > *").nth(-1)  # Selects the last child of an element
        # Message contents are in <p> elements
        last_message_content_first_p = last_message.locator("p[data-path-to-node='0']")
        last_message_content = last_message_content_first_p.locator("..")

        # This div appears when the answer has finished generating. We wait for it to be
        # in the DOM before returning the answer.
        complete_div = last_message.locator('div[data-test-lottie-animation-status="completed"]')
        visible = complete_div.is_visible()
        while not visible:
            time.sleep(0.1)
            visible = complete_div.is_visible()

        # Since Gemini is supposed to answer with a simple text of structure
        # "input1,input2,..." we only need the first <p>
        latest_answer = last_message_content_first_p.inner_text()

        return latest_answer
       

    def add_image_to_prompt(self, image_file_path: str):
        # Click "Add files" (+) button
        self.page.click("button.upload-card-button.open")

        # Click "Upload files" button an save the file selector
        with self.page.expect_file_chooser() as fc_info:
            self.page.click("button[data-test-id='local-images-files-uploader-button']")

        # Set the value of the file chooser to our image
        file_chooser = fc_info.value
        file_chooser.set_files(image_file_path) 

        self.current_image = image_file_path


    def remove_oldest_image():
        """Removes the oldest image added to the prompt"""
        pass


    def _prepare_text_prompting(self):
        editor = self.page.locator('div.ql-editor')
        editor.focus()
        self.page.keyboard.press("Control+End")
        return editor


    def add_text_to_prompt(self, text: str):
        # Insert text directly into prompting textarea
        self.page.evaluate("""(text) => {
            let textarea = document.querySelector('rich-textarea.text-input-field_textarea p')
            textarea.textContent += text;
        }""", text)


    def add_newline_to_prompt(self):
        self._prepare_text_prompting()
        self.page.keyboard.press("Shift+Enter")


    def reset_text_prompt(self):
        self._prepare_text_prompting()
        self.page.keyboard.press("Control+a")
        self.page.keyboard.press("Delete")


    def send_prompt(self) -> str:
        """Sends the current prompt and returns the model's answer"""
        self.page.click("button.send-button")
        time.sleep(0.5)

        # Container for all prompt+answer pairs
        container = self.page.locator('infinite-scroller[data-test-id="chat-history-container"]')
        # Select all direct children of the container
        messages = container.locator(":scope > *")
        # Get the number of messages
        num_prompts = messages.count()

        retry_timeout = 2

        while num_prompts != self.nb_prompts + 1:
            print(f'Prompt sending failed. Trying again in {retry_timeout}s ...')
            time.sleep(retry_timeout)
            if self.current_image:
                self.add_image_to_prompt(self.current_image)
            self.page.click("button.send-button")
            time.sleep(0.5)
            num_prompts = container.locator(":scope > *").count()

        # time.sleep(self.MINIMUM_ANSWER_TIME) # Wait for the answer to be generated
        self.nb_prompts += 1
        self.current_image = None
        return self._get_latest_answer()

    
    def send_image_prompt(self, image_path: str) -> str:
        self.add_image_to_prompt(image_path)
        self.page.wait_for_timeout(1000) # Wait for image to be added to the prompt
        return self.send_prompt()

    
    def send_text_prompt(self, text: str) -> str:
        self.add_text_to_prompt(text)
        time.sleep(1) # Wait for text to be added to the prompt
        return self.send_prompt()


    def _get_model_switch_button(self):
        return self.page.locator("button.input-area-switch")


    def _get_current_model_mode(self) -> ModelMode:
        model_desc = self._get_model_switch_button()
        model_desc_label = model_desc.locator("div.input-area-switch-label")
        span = model_desc_label.locator('span')
        text = span.inner_text()
        if text == "Fast":
            return GeminiModelModes.FAST
        elif text == "Thinking":
            return GeminiModelModes.THINKING
        elif text == "Pro":
            return GeminiModelModes.PRO
        else: # To catch UI updates
            raise ValueError("Unknown Gemini model mode.")
        
    
    def get_model_file_name(self) -> str:
        return self.model_mode.get_file_name()
    
    
    def get_model_name(self) -> str:
        return self.model_mode.get_pretty_name()


    def switch_model_mode(self, model_mode: ModelMode) -> ModelMode:
        "Switches the model mode" 
        if (self.model_mode == model_mode):
            return model_mode
        
        self._get_model_switch_button().click()
        mode_button = self.page.locator(model_mode.get_button_selector())
        mode_button.click()
        self.model_mode = model_mode

        return self.model_mode
    

def test_model_modes(model: GeminiBrowser):
    for mode_name, model_mode in vars(GeminiModelModes).items():
        if isinstance(model_mode, ModelMode):
            model.switch_model_mode(model_mode)
            input(f"{mode_name} = {model_mode.get_pretty_name()} | Press <Enter> for next mode...")


def test_text_prompting(model: GeminiBrowser):
    while True:
        text = input("Text to add to prompt: ")
        if text == "":
            break
        model.add_text_to_prompt(text)

    
if __name__ == '__main__':
    gemini = GeminiBrowser(GeminiModelModes.FAST)
    gemini.start_new_temporary_chat()

    test_model_modes(gemini)

    input("Program done. Press enter to close Chrome...")