class GeminiModel:
    """Wrapper for the available Gemini models"""
    def __init__(self, model_code: str, mode: str=None):
        self.model_code = model_code
        self.mode = mode


    def get_model_code(self) -> str:
        return self.model_code
    

    def get_model_name(self) -> str:
        if self.mode:
            return f"{self.model_code} ({self.mode})"
        return self.model_code
    

    def get_pretty_name(self) -> str:
        split = self.model_code.split("-")
        for i in range(len(split)):
            split[i] = split[i].capitalize()
        if self.mode:
            split.append(self.mode.capitalize())
        return " ".join(split)
    
    
    def get_file_name(self) -> str:
        split = self.model_code.split("-")
        model = split[0]
        if model == "gemini":
            split[0] = "gemi"
        elif model == "gemma":
            split[0] = "gema"
            split = split[:-1]
        split[1] = split[1].replace('.', '+')
        if self.mode:
            split.append(self.mode)
        return '-'.join(split)
    
        
# Models are in the docs:
# https://ai.google.dev/gemini-api/docs/models

class GeminiModels:
    """Contains all usable Gemini models as attributes"""
    PRO_3 = GeminiModel("gemini-3-pro-preview")
    PRO_2_5 = GeminiModel("gemini-2.5-pro")
    FLASH_3_THINKING = GeminiModel("gemini-3-flash-preview", "thinking")
    FLASH_3 = GeminiModel("gemini-3-flash-preview")
    FLASH_2_5 = GeminiModel("gemini-2.5-flash")
    FLASH_2_0 = GeminiModel("gemini-2.0-flash")
    FLASH_LITE_2_5 = GeminiModel("gemini-2.5-flash-lite")
    FLASH_LITE_2_0 = GeminiModel("gemini-2.0-flash-lite")
    GEMMA_3_27b = GeminiModel("gemma-3-27b-it")