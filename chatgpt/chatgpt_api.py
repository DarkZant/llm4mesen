from openai import OpenAI, RateLimitError, APIError
import os
import time
from PIL import Image
import base64
from io import BytesIO

from .chatgpt_models import ChatGPTModel


class ChatGPTAPI:
    def __init__(self, model: ChatGPTModel, api_key: str = None):
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key environment variable is not set!")

        self.client = OpenAI(api_key=api_key)
        self.model = model

        self.messages = None

        self.prompt_text = None
        self.prompt_image = None

    def start_new_temporary_chat(self):
        self.start_new_chat()

    def start_new_chat(self):
        self.messages = []

    def add_text_to_prompt(self, text):
        if not self.prompt_text:
            self.prompt_text = text
        else:
            self.prompt_text += text

    def _convert_image_path_to_base64(self, image_path):
        image = Image.open(image_path)
        buffer = BytesIO()
        image.save(buffer, format=image.format or "PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def add_image_to_prompt(self, image_path):
        self.image_url = image_path
        self.prompt_image = self._convert_image_path_to_base64(image_path)

    def _reset_prompt(self):
        self.prompt_text = None
        self.prompt_image = None

    def send_text_prompt(self, text):
        if self.messages is None:
            return "Create a chat before sending a message!"

        self.add_text_to_prompt(text)
        return self.send_prompt()

    def send_image_prompt(self, image_path):
        if self.messages is None:
            return "Create a chat before sending a message!"

        self.add_image_to_prompt(image_path)
        return self.send_prompt()

    def send_prompt(self):
        if self.messages is None:
            return "Create a chat before sending a message!"

        if not self.prompt_text and not self.prompt_image:
            return "Prompt is empty!"

        content = []

        if self.prompt_text:
            content.append({"type": "input_text", "text": self.prompt_text})

        if self.prompt_image:
            content.append({
                "type": "input_image",
                "image_url": self.image_url
            })

        self.messages.append({
            "role": "user",
            "content": content
        })

        prompt_has_sent = False
        while not prompt_has_sent:
            try:
                response = self.client.responses.create(
                    model=self.model.get_model_code(),
                    input=self.messages
                )
                prompt_has_sent = True

            except RateLimitError as e:
                print(e)
                retry_delay = 30
                waiting_time = retry_delay + 3
                print(f"Rate limit reached. Waiting {waiting_time}s.")
                time.sleep(waiting_time)

            except APIError as e:
                print("OpenAI API error:", e)
                time.sleep(5)

        assistant_text = response.output_text

        self.messages.append({
            "role": "assistant",
            "content": assistant_text
        })

        self._reset_prompt()
        return assistant_text

    def get_model(self):
        return self.model

    def get_model_file_name(self):
        return self.model.get_file_name()

    def get_model_name(self):
        return self.model.get_pretty_name()

    def switch_model(self, model):
        self.model = model
        self.start_new_chat()


