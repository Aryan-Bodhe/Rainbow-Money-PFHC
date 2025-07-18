class UserProfileNotProvidedError(Exception): 
    pass

class InvalidFinanceParameterError(Exception):
    def __init__(self, errored_parameter:str, erring_parameter:str):
        message = f"Cannot compute '{errored_parameter}' due to invalid (possibly zero) value of '{erring_parameter}'."
        super().__init__(message)

class InvalidJsonFormatError(Exception):
    ...

class NoMarkdownFileToConvertToPDFError(Exception):
    def __init__(self):
        message = "No valid markdown file provided to convert to PDF."
        super().__init__(message)

class LLMResponseFailedError(Exception):
    def __init__(self, provider_name):
        message = f"Failed to get valid response from '{provider_name}'."
        super().__init__(message)

class FeedbackGenerationFailedError(Exception):...

class CriticalInternalFailure(Exception):
    def __init__(self):
        message = "We're sorry, something went wrong while processing your data. Please try again later or contact support if the issue persists."
        super().__init__(message)