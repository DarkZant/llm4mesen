class ChatGPTModel:
    """Wrapper for the available ChatGPT models"""
    def __init__(self, model_code: str, mode: str=None):
        self.model_code = model_code
        self.mode = mode


    def get_model_code(self) -> str:
        return self.model_code
    

    def _drop_release_date(self) -> str:
        split = self.model_code.split("-")
        return split[:-3]
    

    def get_pretty_name(self) -> str:
        split = self._drop_release_date()
        for i in range(len(split)):
            split[i] = split[i].capitalize()
        if self.mode:
            split.append(self.mode.capitalize())
        return " ".join(split)
    
    
    def get_file_name(self) -> str:
        split = self._drop_release_date()
        split[1] = split[1].replace('.', '+')
        if self.mode:
            split.append(self.mode)
        return '-'.join(split)
    
        
# Models are in the docs:
# https://platform.openai.com/docs/models

class ChatGPTModels:
    """Contains all usable ChatGPT models as attributes"""
    GPT_5_2 = ChatGPTModel("gpt-5.2-2025-12-11")
    MINI_5 = ChatGPTModel("gpt-5-mini-2025-08-07")
    NANO_5 = ChatGPTModel("gpt-5-nano-2025-08-07")
    GPT_5 = ChatGPTModel("gpt-5-2025-08-07")
    GPT_4_1 = ChatGPTModel("gpt-4.1-2025-04-14")
    GPT_5_2_PRO = ChatGPTModel("gpt-5.2-pro-2025-12-11")
   