import google.genai as genai 
from google.genai.errors import ClientError
import os 
import time

from PIL import Image

from .gemini_models import GeminiModel

class GeminiAPI:
    def __init__(self, model: GeminiModel, api_key: str=None):
        if not api_key:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key environnement variable is not set!")
        self.client = genai.Client(api_key=api_key)
        self.model = model

        self.chat = None

        self.prompt_text = None 
        self.prompt_image = None


    def start_new_temporary_chat(self):
        """Equivalent to start_new_chat in the API"""
        self.start_new_chat()


    def start_new_chat(self):
        self.chat = self.client.chats.create(model=self.model.get_model_code())

    
    def add_text_to_prompt(self, text: str):
        if not self.prompt_text:
            self.prompt_text = text 
        else:
            self.prompt_text += text


    def _convert_image_path_to_image(self, image_path: str):
        return Image.open(image_path)


    def add_image_to_prompt(self, image_path: str):
        self.prompt_image = self._convert_image_path_to_image(image_path)


    def _extract_text_from_answer(self, answer) -> str:
        return answer.text
    
    
    def _reset_prompt(self):
        self.prompt_text = None 
        self.prompt_image = None


    def send_text_prompt(self, text: str) -> str:
        if not self.chat:
            return "Create a chat before sending a message!"
        
        self.add_text_to_prompt(text)
        return self.send_prompt()
    

    def send_image_prompt(self, image_path: str) -> str:
        if not self.chat:
            return "Create a chat before sending a message!"

        self.add_image_to_prompt(image_path)
        return self.send_prompt()
    

    def send_prompt(self) -> str:
        if not self.chat:
            return "Create a chat before sending a message!"
        
        prompt = []
        if self.prompt_text:
            prompt.append(self.prompt_text)
        if self.prompt_image:
            prompt.append(self.prompt_image)

        if len(prompt) == 0:
            return "Prompt is empty!"    
        
        prompt_has_sent = False
        while not prompt_has_sent:
            try: 
                answer = self.chat.send_message(prompt)
                prompt_has_sent = True
            except ClientError as e:
                retry_delay = get_retry_delay(e)
                waiting_time = retry_delay + 3  # Adding a 3 second margin
                print(f'Limit reached. Retry delay={retry_delay}s. Waiting', waiting_time, "seconds.")
                time.sleep(waiting_time)

        self._reset_prompt()
        return self._extract_text_from_answer(answer)
    

    def get_model(self) -> GeminiModel:
        return self.model
    

    def get_model_file_name(self) -> str:
        return self.model.get_file_name()
    

    def get_model_name(self) -> str:
        return self.model.get_pretty_name()
    
    
    def switch_model(self, model: GeminiModel):
        self.model = model 
        self.start_new_chat()


def get_retry_delay(resource_exhausted_client_error: ClientError):
    retry_seconds = None
    try:
        for detail in resource_exhausted_client_error.details.get('error').get('details'):
            if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                retry_delay = detail.get("retryDelay") # Format f'{seconds}s'
                retry_seconds = float(retry_delay.rstrip("s"))
                break 

        return retry_seconds
    except Exception as e:
        retry_seconds = 30
        print(f'Unknown retry delay. Returning {retry_seconds}s')
        return retry_seconds


def list_all_models():
    client = genai.Client()
    for model in client.models.list():
        print(model.name)
    

if __name__ == "__main__":
    list_all_models()