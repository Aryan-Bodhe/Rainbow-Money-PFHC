from colorama import Fore

class UserProfileNotProvidedError(Exception): 
    pass

class InvalidFinanceParameterError(Exception):
    def __init__(self, errored_parameter:str, erring_parameter:str):
        message = Fore.RED + f"[ERROR] Cannot compute '{errored_parameter}' due to invalid (possibly zero) value of '{erring_parameter}'." + Fore.RESET
        super().__init__(message)

class InvalidJsonFormatError(Exception):
    ...

class NoMarkdownFileToConvertToPDFError(Exception):
    def __init__(self):
        message = Fore.RED + "[ERROR] No valid markdown file provided to convert to PDF." + Fore.RESET
        super().__init__(message)

class LLMResponseFailedError(Exception):
    def __init__(self, provider_name):
        message = Fore.RED + f"[ERROR] Failed to get valid response from '{provider_name}'." + Fore.RESET
        super().__init__(message)

class FeedbackGenerationFailedError(Exception):...